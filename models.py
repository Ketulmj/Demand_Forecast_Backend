"""
MongoDB is used for persistence. Collections used by the application:
- users
- uploads

Index creation can be performed on startup if required.
This module intentionally does not declare SQLAlchemy models anymore.
"""

USERS_COLLECTION = 'users'
UPLOADS_COLLECTION = 'uploads'
