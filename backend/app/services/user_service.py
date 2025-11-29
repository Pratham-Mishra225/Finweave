"""User service for MongoDB operations."""
from typing import Optional, Dict, Any
from datetime import datetime
import re
import logging
from app.config.mongodb import get_database
from app.config.firebase import get_firestore_db
from app.models.user import UserCreate, UserUpdate, UserPreferences, UserStats

logger = logging.getLogger(__name__)


class UserService:
    """Service for user-related MongoDB operations."""
    
    def __init__(self):
        """Initialize user service with MongoDB collection."""
        self.collection = "users"
    
    def _get_collection(self):
        """Get MongoDB users collection."""
        db = get_database()
        return db[self.collection]
    
    async def create_user(self, user_data: UserCreate) -> Dict[str, Any]:
        """
        Create a new user in MongoDB and Firestore.
        
        Args:
            user_data: User creation data
            
        Returns:
            Created user document
        """
        user_dict = {
            "uid": user_data.firebase_uid,
            "email": user_data.email,
            "name": user_data.name,
            "phone": user_data.phone,
            "avatar_url": user_data.avatar_url,
            "balance": 0.0,
            "assets": None,
            "liabilities": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "preferences": user_data.preferences.model_dump() if user_data.preferences else UserPreferences().model_dump(),
            "stats": UserStats().model_dump()
        }
        
        # Create in MongoDB
        collection = self._get_collection()
        await collection.insert_one(user_dict)
        
        # Create in Firestore
        try:
            firestore_db = get_firestore_db()
            firestore_user = {
                "email": user_data.email,
                "name": user_data.name,
                "phone": user_data.phone,
                "balance": 0.0,
                "created_at": datetime.utcnow(),
                "preferences": user_data.preferences.model_dump() if user_data.preferences else UserPreferences().model_dump()
            }
            firestore_db.collection("users").document(user_data.firebase_uid).set(firestore_user)
            logger.info(f"User created in Firestore: {user_data.firebase_uid}")
        except Exception as e:
            logger.error(f"Failed to create user in Firestore: {e}")
        
        # Fetch the created document
        return await self.get_user(user_data.firebase_uid)
    
    async def get_user(self, uid: str) -> Optional[Dict[str, Any]]:
        """
        Get user by UID.
        
        Args:
            uid: Firebase user ID
            
        Returns:
            User document or None if not found
        """
        collection = self._get_collection()
        user = await collection.find_one({"uid": uid})
        if user:
            user["_id"] = str(user["_id"])  # Convert ObjectId to string
        return user
    
    async def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """
        Get user by email address.
        
        Args:
            email: User email
            
        Returns:
            User document or None if not found
        """
        collection = self._get_collection()
        user = await collection.find_one({"email": email})
        if user:
            user["_id"] = str(user["_id"])
        return user
    
    async def update_user(self, uid: str, user_data: UserUpdate) -> Optional[Dict[str, Any]]:
        """
        Update user information.
        
        Args:
            uid: Firebase user ID
            user_data: Updated user data
            
        Returns:
            Updated user document or None if not found
        """
        # Only update fields that are provided
        update_dict = {
            k: v for k, v in user_data.model_dump(exclude_unset=True).items()
            if v is not None
        }
        
        if not update_dict:
            return await self.get_user(uid)
        
        # Validate email format if provided
        if 'email' in update_dict and update_dict['email']:
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, update_dict['email']):
                raise ValueError("Invalid email format")
        
        # Validate phone number format if provided
        if 'phone' in update_dict and update_dict['phone']:
            # Basic phone validation (10+ digits)
            phone_digits = ''.join(filter(str.isdigit, update_dict['phone']))
            if len(phone_digits) < 10:
                raise ValueError("Invalid phone number format")
        
        update_dict["updated_at"] = datetime.utcnow()
        
        collection = self._get_collection()
        result = await collection.update_one(
            {"uid": uid},
            {"$set": update_dict}
        )
        
        if result.matched_count == 0:
            return None
        
        return await self.get_user(uid)
    
    async def delete_user(self, uid: str) -> bool:
        """
        Delete user from MongoDB.
        
        Args:
            uid: Firebase user ID
            
        Returns:
            True if deleted, False if not found
        """
        collection = self._get_collection()
        result = await collection.delete_one({"uid": uid})
        return result.deleted_count > 0
    
    async def upsert_user(self, uid: str, email: str, name: str) -> Dict[str, Any]:
        """
        Create or update user (upsert operation).
        Used for Google sign-in where user might not exist.
        
        Args:
            uid: Firebase user ID
            email: User email
            name: User display name
            
        Returns:
            User document
        """
        user = await self.get_user(uid)
        
        if user:
            return user
        
        # Create new user
        user_data = UserCreate(
            firebase_uid=uid,
            email=email,
            name=name,
            preferences=UserPreferences()
        )
        
        return await self.create_user(user_data)
    
    async def user_exists(self, uid: str) -> bool:
        """
        Check if user exists.
        
        Args:
            uid: Firebase user ID
            
        Returns:
            True if user exists, False otherwise
        """
        collection = self._get_collection()
        user = await collection.find_one({"uid": uid})
        return user is not None
    
    async def update_user_stats(self, uid: str, stats: UserStats) -> Optional[Dict[str, Any]]:
        """
        Update user statistics.
        
        Args:
            uid: Firebase user ID
            stats: Updated statistics
            
        Returns:
            Updated user document or None if not found
        """
        collection = self._get_collection()
        result = await collection.update_one(
            {"uid": uid},
            {
                "$set": {
                    "stats": stats.model_dump(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            return None
        
        return await self.get_user(uid)
    
    async def update_user_preferences(
        self,
        uid: str,
        preferences: UserPreferences
    ) -> Optional[Dict[str, Any]]:
        """
        Update user preferences.
        
        Args:
            uid: Firebase user ID
            preferences: Updated preferences
            
        Returns:
            Updated user document or None if not found
        """
        collection = self._get_collection()
        result = await collection.update_one(
            {"uid": uid},
            {
                "$set": {
                    "preferences": preferences.model_dump(),
                    "updated_at": datetime.utcnow()
                }
            }
        )
        
        if result.matched_count == 0:
            return None
        
        return await self.get_user(uid)
    
    async def upsert_user(self, uid: str, email: str, name: str) -> Dict[str, Any]:
        """
        Atomically create or get user (for handling race conditions).
        
        Args:
            uid: Firebase user ID
            email: User email
            name: User name
            
        Returns:
            User document
        """
        collection = self._get_collection()
        await collection.update_one(
            {"uid": uid},
            {
                "$setOnInsert": {
                    "uid": uid,
                    "email": email,
                    "name": name,
                    "phone": None,
                    "avatar_url": None,
                    "balance": 0.0,
                    "assets": None,
                    "liabilities": None,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow(),
                    "preferences": UserPreferences().model_dump(),
                    "stats": UserStats().model_dump()
                }
            },
            upsert=True
        )
        return await self.get_user(uid)


# Global user service instance
user_service = UserService()
