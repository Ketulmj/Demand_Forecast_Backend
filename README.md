# Demand Forecasting – Backend (FastAPI)

This is the backend for a Demand Forecasting application built with FastAPI, SQLAlchemy, and PostgreSQL. It handles user authentication with email verification, CSV ingestion via AWS S3, background model training, forecasting endpoints, and business insights extraction.


## Key Features
- User signup with email verification and secure JWT-based login.
- CSV upload through presigned AWS S3 URLs.
- Background training pipeline (XGBoost) with feature engineering.
- Forecast endpoint that predicts future `quantity_sold` for product/category/city.
- Business insights (KPIs and charts) extracted from your latest dataset.
- PostgreSQL persistence for users, uploads, training runs, forecasts, and insights.


## Tech Stack
- Backend: `FastAPI`
- ORM: `SQLAlchemy`
- DB: `PostgreSQL` (via `docker-compose` or local)
- Auth: JWT, `passlib` for password hashing
- Email: `fastapi-mail` (SMTP-based) with HTML templates
- Storage & ML Artifacts: AWS S3 (`boto3`) and local cache (`cache/models`)
- ML: `xgboost`, `scikit-learn`, `pandas`, `numpy`

---

## Project Structure
```
Demand_Forecast_Backend/
├── main.py                      # FastAPI app, CORS, router mounts
├── docker-compose.yml           # PostgreSQL service for local db setup
├── requirements.txt             # Python dependencies
│── .env                        # Environment variables
│
├── core/
│   ├── __init__.py
│   ├── config.py                # Env settings (DB, JWT, email, AWS)
│   └── security.py              # Password hashing/verification (passlib)
│
├── db/
│   ├── __init__.py
│   └── db.py                    # SQLAlchemy engine
│
├── models/
│   ├── __init__.py
│   └── models.py                # SQLAlchemy models (User, Upload,. etc)
│
├── routers/
│   ├── __init__.py
│   ├── auth.py                  # Signup, verify-email, login
│   ├── upload.py                # uploads and triggers start model training
│   ├── predict.py               # Predict forecasts
│   ├── insights.py              # Business insights (KPIs/charts)
│   ├── feature.py               # Distinct features for UI filters
│   └── user.py                  # user-related routes
│
├── schemas/
│   ├── __init__.py
│   └── schemas.py               # Pydantic models for auth, uploads, training, prediction, insights
│
├── services/
│   ├── __init__.py
│   └── crud.py                  # DB operations
│
├── utils/
│   ├── __init__.py
│   ├── auth.py                  # JWT tokens, current user dependencies
│   ├── helpers.py               # CSV loading, preprocessing, feature engineering, future features, sequential prediction
│   ├── train.py                 # Training pipeline, model/meta saving, S3 upload, email notification
│   └── email.py                 # Email sending via fastapi-mail
│
├── templates/
│   ├── verification_email.html  # Verification email template
│   ├── verification_success.html# Verification success page
│   ├── verification_error.html  # Verification error page
│   └── training_completion_email.html # Training completion email template
│
└── public/
    ├── home.png                 # Frontend screenshot: Home
    ├── upload-csv.jpg           # Frontend screenshot: Upload CSV
    ├── forecast.png             # Frontend screenshot: Forecast view
    └── bussiness-insights.png   # Frontend screenshot: Business insights
```

---
**Frontend**
- GitHub repo: https://github.com/Ketulmj/demand_forecast_client.git
- Local dev: set `VITE_API_URL=http://127.0.0.1:8000` in the frontend `.env`, run the backend here, and start the frontend with `npm run dev`. Ensure CORS in `main.py` allows your frontend origin.

```
core/        # env-driven settings (pydantic-settings)
db/          # SQLAlchemy engine/session setup
models/      # SQLAlchemy models
routers/     # FastAPI routers (auth, upload, predict, insights, feature)
schemas/     # Pydantic request/response models
services/    # CRUD helpers
utils/       # auth helpers, training pipeline, emails, helpers
templates/   # email HTML templates
public/      # frontend screenshots (referenced in README)
main.py      # FastAPI app init, CORS, and router mounting
```

## Prerequisites
- Python 3.10+
- PostgreSQL (or run via Docker using `docker-compose.yml`)
- An AWS S3 bucket and credentials (or run training purely local; S3 is recommended)
- SMTP credentials for sending verification and training-completion emails

## Env Setup
This backend uses environment variables defined via `.env` (loaded by `pydantic-settings`). Create a `.env` file in the project root with values like:

```
# Database
DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/fastapi_db

# JWT / Security
SECRET_KEY=your-strong-secret
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Email (FastAPI-Mail)
MAIL_USERNAME=your_smtp_username
MAIL_PASSWORD=your_smtp_password
MAIL_FROM=you@example.com
MAIL_PORT=587
MAIL_SERVER=smtp.example.com
MAIL_STARTTLS=true
MAIL_SSL_TLS=false

# AWS / S3
AWS_ACCESS_KEY_ID=YOUR_AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY=YOUR_AWS_SECRET_ACCESS_KEY
AWS_REGION=ap-south-1
S3_BUCKET_NAME=your-bucket-name
```

Notes:
- The provided `docker-compose.yml` maps PostgreSQL on host `localhost:5432` to container `5432` with default creds `postgres/password`. Adjust as needed.
- Ensure the S3 bucket exists and credentials have `s3:GetObject`, `s3:PutObject`, and `s3:ListBucket` permissions.

---

## Install & Run (Windows PowerShell)
1) Create virtual env and install dependencies:
```
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2) Start PostgreSQL with Docker (optional):
```
docker compose up -d
```

3) Run the backend:
```
uvicorn main:app --reload --port 8000
```

- API root: `http://localhost:8000/`
- FastAPI docs: `http://localhost:8000/docs`

---

## Data Format (CSV)
Your dataset should at minimum include these columns:
- `date` (parseable date)
- `product_category`
- `product`
- `city`
- `quantity_sold`
- `release_date`
- `price`
- `discount`
- `final_price`
- `marketing_spend`
- `last_month_sales`

The training pipeline performs:
- Date parsing and sorting
- Label encoding for categorical columns
- Lag and rolling statistics on `quantity_sold`
- Holiday and season features
- Train/test split and model training (XGBoost)

---

## Typical Usage Flow
1) Signup and verify email:
   - `POST /auth/signup` with `{ username, email, password }`
   - Check your inbox and click the verification link (`GET /auth/verify-email?token=...`).

2) Login to obtain a JWT:
   - `POST /auth/login` → `{ access_token, token_type }`
   - Use header `Authorization: Bearer <token>` for protected routes.

3) Upload CSV via S3 presigned URL:
   - `GET /upload/generate-upload-url?filename=mydata.csv`
   - Use the returned `upload_url` to `PUT` your CSV directly to S3.
   - `POST /upload/upload-complete` with `{ upload_id }` to confirm and trigger background training.

4) Fetch business insights:
   - `GET /insights/` (requires auth) → returns KPIs and charts derived from latest upload.

5) Predict demand:
   - `POST /predict/` with body:
     ```json
     {
       "product_category": "Electronics",
       "product": "iPhone 14",
       "city": "Mumbai",
       "num_days": 30
     }
     ```
   - Returns list of `{ date, predicted_quantity_sold }` and a `forecast_id` if persisted.

6) List forecasts for current user:
   - `GET /predict/get_forecasts`

7) Distinct features for UI filters:
   - `GET /feature/features`

## Important Endpoints
- Auth
  - `POST /auth/signup`
  - `GET  /auth/verify-email?token=...`
  - `POST /auth/login`
  - `GET  /auth/me`

- Upload & Training
  - `GET  /upload/generate-upload-url?filename=...`
  - `POST /upload/upload-complete` (triggers training)
  - `GET  /upload/download/{upload_id}` (presigned GET)

- Insights & Features
  - `GET  /insights/` (latest business insight)
  - `GET  /feature/features` (distinct columns/products/categories/cities)

- Forecasting
  - `POST /predict/` (generate forecast)
  - `GET  /predict/get_forecasts` (list user forecasts)


## Screenshots (Frontend)
The following images provide a visual overview of the UI:

![Home](public/home.png)

![Upload CSV](public/upload-csv.jpg)

![Forecast](public/forecast.png)

![Business Insights](public/bussiness-insights.png)

---

## CORS & Frontend Dev
CORS is configured to allow:
- `http://localhost:5173` (React + Vite app)

Update `main.py` if your frontend runs on a different origin.

## Notes & Tips
- Email templates live in `templates/` (verification and training completion).
- Trained models and metadata are saved under `cache/models/` and uploaded to S3 if configured.
- Swagger UI at `/docs` and ReDoc at `/redoc` help you explore endpoints.
- If you change DB credentials/ports, update `DATABASE_URL` in `.env` accordingly.


## License
This project is intended for internal/demo use. Please add a license if you plan to distribute it.