"""Firebase Admin SDK and Firestore initialization."""
import logging
import firebase_admin
from firebase_admin import credentials, firestore
from app.config.settings import settings

logger = logging.getLogger(__name__)


# Initialize Firebase Admin SDK
def initialize_firebase():
    """Initialize Firebase Admin SDK with service account credentials."""
    try:
        cred = credentials.Certificate(settings.firebase_credentials_path)
        firebase_admin.initialize_app(cred)
        logger.info("Firebase Admin SDK initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing Firebase: {e}")
        raise


# Get Firestore client
def get_firestore_client():
    """Get Firestore database client."""
    return firestore.client()


# Global Firestore client instance
db = None


def get_firestore_db():
    """Return the initialized Firestore client.

    Raises:
        RuntimeError: If Firestore client has not been initialized.
    """
    if db is None:
        raise RuntimeError("Firestore client has not been initialized. Call init_firestore() first.")
    return db


def init_firestore():
    """Initialize Firestore client (call after Firebase initialization).
    
    Must be called before using the global Firestore client via get_firestore_db().
    """
    global db
    db = get_firestore_client()
    return db
