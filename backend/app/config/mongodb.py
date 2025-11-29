"""MongoDB connection using Motor (async driver)."""
import logging
import certifi
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.config.settings import settings

logger = logging.getLogger(__name__)


# Async MongoDB client for FastAPI
class MongoDB:
    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None


mongodb = MongoDB()


async def connect_to_mongodb():
    """Connect to MongoDB using Motor async client."""
    try:
        client: AsyncIOMotorClient = AsyncIOMotorClient(
            settings.mongodb_uri,
            tlsCAFile=certifi.where()
        )
        mongodb.client = client
        mongodb.db = client[settings.mongodb_db_name]
        
        # Verify connection
        await client.admin.command('ping')
        logger.info(f"Connected to MongoDB database: {settings.mongodb_db_name}")
        
        # Create indexes
        await create_indexes()
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        raise


async def close_mongodb_connection():
    """Close MongoDB connection."""
    if mongodb.client:
        mongodb.client.close()
        logger.info("MongoDB connection closed")


async def create_indexes():
    """Create MongoDB indexes for optimized queries."""
    if mongodb.db is None:
        raise RuntimeError("MongoDB database is not initialized")

    transactions = mongodb.db["transactions"]
    insights_cache = mongodb.db["insights_cache"]
    debts = mongodb.db["debts"]
    user_memory = mongodb.db["user_memory"]

    # Transaction indexes
    await transactions.create_index([("user_id", 1), ("date", -1)])
    await transactions.create_index([("user_id", 1), ("category", 1)])
    await transactions.create_index([("user_id", 1), ("amount", 1)])
    
    # Insights cache TTL index (expires after 6 hours)
    # Note: TTL index may delete documents while being read. Application logic
    # should handle missing documents gracefully and validate cache age before use.
    await insights_cache.create_index("generated_at", expireAfterSeconds=21600)
    
    # Debt collection index
    await debts.create_index([("user_id", 1), ("status", 1)])
    
    # User memory index
    await user_memory.create_index("user_id", unique=True)
    
    logger.info("MongoDB indexes created successfully")


def get_database():
    """Get MongoDB database instance.
    
    Raises:
        RuntimeError: If MongoDB database has not been initialized.
    """
    if mongodb.db is None:
        raise RuntimeError("MongoDB database is not initialized. Call connect_to_mongodb() before accessing the database.")
    return mongodb.db
