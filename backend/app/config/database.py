"""MongoDB database configuration and connection."""
from motor.motor_asyncio import AsyncIOMotorClient
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)


class Database:
    """MongoDB database manager."""
    
    client: AsyncIOMotorClient = None
    db = None


database = Database()


async def connect_to_mongo():
    """Create database connection."""
    try:
        database.client = AsyncIOMotorClient(settings.mongodb_uri)
        database.db = database.client[settings.mongodb_db_name]
        
        # Test connection
        await database.client.admin.command('ping')
        logger.info(f"Connected to MongoDB database: {settings.mongodb_db_name}")
    except Exception as e:
        logger.error(f"Error connecting to MongoDB: {e}")
        raise


async def close_mongo_connection():
    """Close database connection."""
    if database.client:
        database.client.close()
        logger.info("MongoDB connection closed")


def get_database():
    """Get database instance."""
    return database.db
