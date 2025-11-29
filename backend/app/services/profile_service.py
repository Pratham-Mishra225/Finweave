"""Profile service for user profile and preferences management."""
from typing import Dict, Any, Optional
from datetime import datetime
import logging
from app.config.mongodb import get_database
from app.config.firebase import get_firestore_db
from app.services.user_service import user_service
from app.models.user import UserUpdate, UserPreferencesUpdate, UserStats, UserPreferences

logger = logging.getLogger(__name__)


class ProfileService:
    """Service for profile-related operations."""
    
    async def get_profile_with_stats(self, uid: str) -> Optional[Dict[str, Any]]:
        """
        Get user profile with calculated statistics.
        
        Args:
            uid: Firebase user ID
            
        Returns:
            User profile with stats or None if not found
        """
        # Get user from MongoDB
        user = await user_service.get_user(uid)
        
        if not user:
            return None
        
        # Calculate current stats
        stats = await self.calculate_user_stats(uid)
        
        # Update stats in the response
        user["stats"] = stats
        
        return user
    
    async def update_profile(
        self,
        uid: str,
        user_data: UserUpdate
    ) -> Optional[Dict[str, Any]]:
        """
        Update user profile information.
        
        Args:
            uid: Firebase user ID
            user_data: Updated user data
            
        Returns:
            Updated user profile or None if not found
        """
        # Update in MongoDB
        updated_user = await user_service.update_user(uid, user_data)
        
        if not updated_user:
            return None
        
        # Update in Firestore if applicable
        try:
            firestore_db = get_firestore_db()
            update_dict = {
                k: v for k, v in user_data.model_dump(exclude_unset=True).items()
                if v is not None
            }
            
            if update_dict:
                update_dict["updated_at"] = datetime.utcnow()
                firestore_db.collection("users").document(uid).update(update_dict)
                logger.info(f"User profile updated in Firestore: {uid}")
        except Exception as e:
            logger.error(f"Failed to update user in Firestore: {e}")
        
        return updated_user
    
    async def update_preferences(
        self,
        uid: str,
        preferences_update: UserPreferencesUpdate
    ) -> Optional[Dict[str, Any]]:
        """
        Update user preferences.
        
        Args:
            uid: Firebase user ID
            preferences_update: Updated preferences
            
        Returns:
            Updated preferences or None if not found
        """
        # Get current user
        user = await user_service.get_user(uid)
        
        if not user:
            return None
        
        # Get current preferences
        current_prefs = user.get("preferences", {})
        
        # Update only provided fields
        update_dict = preferences_update.model_dump(exclude_unset=True)
        current_prefs.update({k: v for k, v in update_dict.items() if v is not None})
        
        # Create UserPreferences object
        updated_preferences = UserPreferences(**current_prefs)
        
        # Update in MongoDB
        updated_user = await user_service.update_user_preferences(uid, updated_preferences)
        
        if not updated_user:
            return None
        
        # Update in Firestore
        try:
            firestore_db = get_firestore_db()
            firestore_db.collection("users").document(uid).update({
                "preferences": updated_preferences.model_dump(),
                "updated_at": datetime.utcnow()
            })
            logger.info(f"User preferences updated in Firestore: {uid}")
        except Exception as e:
            logger.error(f"Failed to update preferences in Firestore: {e}")
        
        return updated_preferences.model_dump()
    
    async def calculate_user_stats(self, uid: str) -> Dict[str, Any]:
        """
        Calculate user statistics from transactions and goals.
        
        Args:
            uid: Firebase user ID
            
        Returns:
            User statistics dictionary
        """
        db = get_database()
        
        # Get user for balance
        user = await user_service.get_user(uid)
        balance = user.get("balance", 0.0) if user else 0.0
        
        # Count total transactions
        transactions_collection = db["transactions"]
        total_transactions = await transactions_collection.count_documents({"user_id": uid})
        
        # Calculate income and expenses
        pipeline = [
            {"$match": {"user_id": uid}},
            {
                "$group": {
                    "_id": "$type",
                    "total": {"$sum": "$amount"}
                }
            }
        ]
        
        totals_cursor = transactions_collection.aggregate(pipeline)
        total_income = 0.0
        total_expenses = 0.0
        
        async for item in totals_cursor:
            if item["_id"] == "income":
                total_income = item["total"]
            elif item["_id"] == "expense":
                total_expenses = item["total"]
        
        # Calculate this month's expenses
        from datetime import datetime
        start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        month_pipeline = [
            {
                "$match": {
                    "user_id": uid,
                    "type": "expense",
                    "date": {"$gte": start_of_month}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": "$amount"}
                }
            }
        ]
        
        month_cursor = transactions_collection.aggregate(month_pipeline)
        month_result = [doc async for doc in month_cursor]
        this_month_expenses = month_result[0]["total"] if month_result else 0.0
        
        # Count goals from Firestore
        try:
            firestore_db = get_firestore_db()
            goals_ref = firestore_db.collection("users").document(uid).collection("goals")
            goals = goals_ref.stream()
            
            total_goals = 0
            active_goals = 0
            completed_goals = 0
            
            for goal in goals:
                total_goals += 1
                goal_data = goal.to_dict()
                
                # Check if goal is completed
                progress = goal_data.get("progress", 0)
                if progress >= 100:
                    completed_goals += 1
                else:
                    active_goals += 1
            
        except Exception as e:
            logger.error(f"Failed to count goals from Firestore: {e}")
            total_goals = 0
            active_goals = 0
            completed_goals = 0
        
        stats = {
            "balance": balance,
            "total_transactions": total_transactions,
            "total_goals": total_goals,
            "active_goals": active_goals,
            "completed_goals": completed_goals,
            "total_income": total_income,
            "total_expenses": total_expenses,
            "this_month_expenses": this_month_expenses
        }
        
        # Update stats in MongoDB
        await user_service.update_user_stats(uid, UserStats(**stats))
        
        return stats


# Global profile service instance
profile_service = ProfileService()
