import uuid
import boto3
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from botocore.exceptions import ClientError
from bson.objectid import ObjectId

from db import get_db
from settings import settings
from schemas import UploadCompleteRequest, User
from auth import get_current_active_user

router = APIRouter()

s3 = boto3.client(
    "s3",
    region_name=settings.AWS_REGION,
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
)

UPLOADS_COLLECTION = 'uploads'

def make_s3_key(user_id: str, filename: str) -> str:
    ext = filename.split(".")[-1].lower() if "." in filename else "csv"
    return f"uploads/{user_id}/{uuid.uuid4().hex}.{ext}"

@router.post("/csv-for-training")
async def upload_file(
    file: UploadFile = File(...), 
    db = Depends(get_db), 
    current_user: User = Depends(get_current_active_user)
):
    user_id = str(current_user.get('_id'))
    key = make_s3_key(user_id, file.filename)
    bucket_name = settings.S3_BUCKET_NAME

    try:
        s3.upload_fileobj(
            Fileobj=file.file,
            Bucket=bucket_name,
            Key=key,
            ExtraArgs={"ContentType": file.content_type or "application/octet-stream"},
        )
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"S3 upload failed: {e}")

    head = s3.head_object(Bucket=bucket_name, Key=key)
    size = head.get("ContentLength")

    upload_doc = {
        "user_id": user_id,
        "filename": file.filename,
        "key": key,
        "bucket": bucket_name,
        "size_bytes": size,
        "content_type": file.content_type or "application/octet-stream",
    }
    result = await db[UPLOADS_COLLECTION].insert_one(upload_doc)
    inserted_id = result.inserted_id

    return {
        "id": str(inserted_id),
        "filename": upload_doc["filename"],
        "s3_key": upload_doc["key"],
        "bucket": upload_doc["bucket"],
        "size_bytes": upload_doc["size_bytes"],
        "content_type": upload_doc["content_type"],
    }

@router.get("/generate-upload-url")
async def generate_presigned_upload_url(
    filename: str = Query(...),
    content_type: str = Query("text/csv"),
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    user_id = str(current_user.get('_id'))
    bucket_name = settings.S3_BUCKET_NAME
    key = make_s3_key(user_id, filename)

    try:
        presigned_url = s3.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": bucket_name,
                "Key": key,
                "ContentType": content_type
            },
            ExpiresIn=300  # 5 minutes
        )
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate presigned URL: {e}")

    upload_doc = {
        "user_id": user_id,
        "filename": filename,
        "key": key,
        "bucket": bucket_name,
        "size_bytes": 0, # Will be updated on completion
        "content_type": content_type,
    }
    result = await db[UPLOADS_COLLECTION].insert_one(upload_doc)
    inserted_id = result.inserted_id

    return {
        "upload_url": presigned_url,
        "key": key,
        "upload_id": str(inserted_id)
    }

@router.post("/upload-complete")
async def confirm_upload(
    request: UploadCompleteRequest, 
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    user_id = str(current_user.get('_id'))
    try:
        upload_id = ObjectId(request.upload_id)
    except Exception:
        raise HTTPException(400, "Invalid upload_id format")

    upload = await db[UPLOADS_COLLECTION].find_one({"_id": upload_id, "user_id": user_id})
    if not upload:
        raise HTTPException(404, "Upload record not found or you don't have permission")

    if upload.get('key') != request.s3_key:
        raise HTTPException(400, "S3 key mismatch")

    head = s3.head_object(Bucket=upload["bucket"], Key=upload["key"])
    size = head.get("ContentLength")
    
    await db[UPLOADS_COLLECTION].update_one(
        {"_id": upload_id},
        {"$set": {"size_bytes": size}}
    )
    
    return {"status": "ok"}

@router.get("/download/{upload_id}")
async def get_download_url(
    upload_id: str, 
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    user_id = str(current_user.get('_id'))
    try:
        obj_id = ObjectId(upload_id)
    except Exception:
        raise HTTPException(400, "Invalid upload_id format")

    row = await db[UPLOADS_COLLECTION].find_one({"_id": obj_id, "user_id": user_id})
    if not row:
        raise HTTPException(404, "Not found or you don't have permission")
        
    url = s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={"Bucket": row["bucket"], "Key": row["key"]},
        ExpiresIn=300,  # 5 minutes
    )
    return {"url": url}