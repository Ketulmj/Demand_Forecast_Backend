from typing import Optional
from db import get_db
from security import get_password_hash
import secrets
import asyncio

USERS = 'users'
UPLOADS = 'uploads'

# Utility to create a MongoDB user programmatically
async def create_mongo_user(db, username: str, password: str, dbname: str):
    """
    Create a MongoDB user with readWrite role for the specified database.
    Usage:
        await create_mongo_user(db, "mongo", "example", "forecast_mongo")
    """
    try:
        result = await db.command(
            "createUser",
            username,
            pwd=password,
            roles=[{"role": "readWrite", "db": dbname}]
        )
        return result
    except Exception as e:
        return {"error": str(e)}

async def get_user(db, user_id: int) -> Optional[dict]:
    return await db[USERS].find_one({"_id": user_id})

async def get_user_by_email(db, email: str) -> Optional[dict]:
    print("Fetching user by email:", email)
    collections = await db.list_collection_names()
    print("Collections:", collections)
    return await db[USERS].find_one({"email": email})

async def create_user(db, user) -> dict:
    # hashed_password = get_password_hash(user.password)
    verification_token = secrets.token_urlsafe(32)
    doc = {
        "username": user.username,
        "email": user.email,
        "password": user.password,
        "is_email_verified": False,
        "email_verification_token": verification_token,
    }
    print("Doc : ",doc)
    result = await db[USERS].insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc

async def get_user_by_email_verification_token(db, token: str) -> Optional[dict]:
    return await db[USERS].find_one({"email_verification_token": token})

async def verify_user_email(db, user: dict) -> dict:
    await db[USERS].update_one({"_id": user["_id"]}, {"$set": {"is_email_verified": True, "email_verification_token": None}})
    return await get_user_by_email(db, user.get("email"))

async def create_upload(db, upload) -> dict:
    doc = {
        "user_id": upload.user_id,
        "filename": upload.filename,
        "key": upload.key,
        "bucket": upload.bucket,
        "size_bytes": upload.size_bytes,
        "content_type": upload.content_type,
    }
    result = await db[UPLOADS].insert_one(doc)
    doc["_id"] = result.inserted_id
    return doc