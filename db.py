from motor.motor_asyncio import AsyncIOMotorClient
from settings import settings

_client: AsyncIOMotorClient | None = None

def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        mongo_uri = settings.DATABASE_URL
        _client = AsyncIOMotorClient(mongo_uri)
    print("MongoDB client initialized")
    return _client

def get_db():
    """Return the default database object from the Mongo client."""
    client = get_client()
    print("Client : ",client)
    # if DATABASE_NAME is included in URL, motor will select it; otherwise use 'forecast_db'
    db = client.get_default_database()
    print("DB : ",db)
    print("Forecasting DB : ",client['forecast_db'])
    return db if db is not None else client['forecast_db']