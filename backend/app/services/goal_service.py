"""Goal service for managing user financial goals in Firestore."""
import logging
from datetime import datetime, date
from typing import List, Optional, Dict, Any

from app.config.firebase import get_firestore_db
from app.models.goal import (
    GoalCreate,
    GoalUpdate,
    GoalResponse,
    GoalStatus,
    GoalMilestone
)
from app.models.notification import (
    NotificationCreate,
    NotificationType,
    NotificationPriority
)

logger = logging.getLogger(__name__)


class GoalService:
    """Service for managing goals stored in Firestore."""

    MILESTONE_PERCENTAGES = [25, 50, 75, 100]

    def __init__(self):
        self.firestore_db = None

    def _get_firestore_db(self):
        """Lazily fetch Firestore client to avoid requiring init at import time."""
        if self.firestore_db is None:
            self.firestore_db = get_firestore_db()
        return self.firestore_db

    def _get_goals_collection(self, user_id: str):
        """Get the goals subcollection for a user."""
        return self._get_firestore_db().collection("users").document(user_id).collection("goals")

    def _get_notifications_collection(self, user_id: str):
        """Get the notifications subcollection for a user."""
        return self._get_firestore_db().collection("users").document(user_id).collection("notifications")

    @staticmethod
    def calculate_progress(saved_amount: float, target_amount: float) -> float:
        """
        Calculate goal progress percentage.
        
        Args:
            saved_amount: Amount saved so far
            target_amount: Target goal amount
            
        Returns:
            Progress percentage (0-100)
        """
        if target_amount <= 0:
            return 0.0
        progress = (saved_amount / target_amount) * 100
        return min(round(progress, 2), 100.0)

    @staticmethod
    def check_deadline_status(deadline: Optional[date]) -> Dict[str, Any]:
        """
        Check the deadline status of a goal.
        
        Args:
            deadline: Goal deadline date
            
        Returns:
            Dict with days_remaining and is_overdue
        """
        if deadline is None:
            return {"days_remaining": None, "is_overdue": False}
        
        today = date.today()
        delta = deadline - today
        days_remaining = delta.days
        is_overdue = days_remaining < 0
        
        return {"days_remaining": days_remaining, "is_overdue": is_overdue}

    def _check_milestone_reached(
        self, old_progress: float, new_progress: float
    ) -> Optional[int]:
        """
        Check if a milestone has been reached.
        
        Args:
            old_progress: Previous progress percentage
            new_progress: New progress percentage
            
        Returns:
            Milestone percentage if reached, None otherwise
        """
        for milestone in self.MILESTONE_PERCENTAGES:
            if old_progress < milestone <= new_progress:
                return milestone
        return None

    async def _trigger_milestone_notification(
        self, user_id: str, goal_id: str, goal_title: str, milestone: int
    ) -> None:
        """
        Create a notification when a milestone is reached.
        
        Args:
            user_id: User's Firebase UID
            goal_id: Goal ID
            goal_title: Goal title
            milestone: Milestone percentage reached
        """
        try:
            messages = {
                25: f"Great start! You're 25% of the way to your goal '{goal_title}'! 🎯",
                50: f"Halfway there! You've reached 50% of your goal '{goal_title}'! 🌟",
                75: f"Almost there! You're 75% to your goal '{goal_title}'! 🔥",
                100: f"Congratulations! You've achieved your goal '{goal_title}'! 🎉"
            }
            
            notification_data = {
                "type": NotificationType.GOAL.value,
                "title": f"Goal Milestone: {milestone}%",
                "message": messages.get(milestone, f"You've reached {milestone}% of your goal!"),
                "priority": NotificationPriority.HIGH.value if milestone == 100 else NotificationPriority.MEDIUM.value,
                "read": False,
                "created_at": datetime.utcnow(),
                "metadata": {
                    "goal_id": goal_id,
                    "goal_title": goal_title,
                    "milestone": milestone
                }
            }
            
            notifications_ref = self._get_notifications_collection(user_id)
            notifications_ref.add(notification_data)
            
            logger.info(f"Milestone notification created for user {user_id}, goal {goal_id}, milestone {milestone}%")
            
        except Exception as e:
            logger.error(f"Error creating milestone notification: {e}")
            # Don't raise - notification failure shouldn't fail the goal update

    def _serialize_goal_data(self, goal_data: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize goal data for Firestore storage."""
        data = goal_data.copy()
        
        # Convert date to string for storage
        if 'deadline' in data and data['deadline'] is not None:
            if isinstance(data['deadline'], date):
                data['deadline'] = data['deadline'].isoformat()
        
        # Convert category enum to string
        if 'category' in data and hasattr(data['category'], 'value'):
            data['category'] = data['category'].value
            
        # Convert status enum to string
        if 'status' in data and hasattr(data['status'], 'value'):
            data['status'] = data['status'].value
            
        return data

    def _deserialize_goal_data(self, doc_id: str, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Deserialize goal data from Firestore."""
        data = doc_data.copy()
        data['id'] = doc_id
        
        # Convert deadline string to date if needed
        if 'deadline' in data and data['deadline'] is not None:
            if isinstance(data['deadline'], str):
                data['deadline'] = date.fromisoformat(data['deadline'])
        
        # Convert timestamps
        if 'created_at' in data and hasattr(data['created_at'], 'isoformat'):
            pass  # Keep as datetime
        
        return data

    async def create_goal(self, user_id: str, goal_data: GoalCreate) -> GoalResponse:
        """
        Create a new goal in Firestore.
        
        Args:
            user_id: User's Firebase UID
            goal_data: Goal creation data
            
        Returns:
            GoalResponse with created goal
        """
        try:
            # Prepare goal document
            goal_dict = goal_data.model_dump()
            goal_dict["user_id"] = user_id
            goal_dict["status"] = GoalStatus.ACTIVE.value
            goal_dict["created_at"] = datetime.utcnow()
            goal_dict["updated_at"] = datetime.utcnow()
            
            # Serialize for Firestore
            goal_dict = self._serialize_goal_data(goal_dict)
            
            # Add to Firestore
            goals_ref = self._get_goals_collection(user_id)
            doc_ref = goals_ref.add(goal_dict)
            
            # Get the document ID
            goal_id = doc_ref[1].id
            
            # Prepare response data
            response_data = self._deserialize_goal_data(goal_id, goal_dict)
            
            # Check for milestone (in case saved_amount > 0 on creation)
            if goal_data.saved_amount > 0:
                progress = self.calculate_progress(goal_data.saved_amount, goal_data.target_amount)
                milestone = self._check_milestone_reached(0, progress)
                if milestone:
                    await self._trigger_milestone_notification(
                        user_id, goal_id, goal_data.title, milestone
                    )
            
            logger.info(f"Goal created for user {user_id}: {goal_id}")
            return GoalResponse.from_goal_data(response_data)
            
        except Exception as e:
            logger.error(f"Error creating goal for user {user_id}: {e}")
            raise

    async def get_goals(
        self, user_id: str, status: Optional[GoalStatus] = None
    ) -> List[GoalResponse]:
        """
        Get all goals for a user.
        
        Args:
            user_id: User's Firebase UID
            status: Optional status filter
            
        Returns:
            List of GoalResponse
        """
        try:
            goals_ref = self._get_goals_collection(user_id)
            
            # Apply status filter if provided
            if status:
                query = goals_ref.where("status", "==", status.value)
            else:
                query = goals_ref
            
            # Order by created_at descending
            query = query.order_by("created_at", direction="DESCENDING")
            
            docs = query.stream()
            
            goals = []
            for doc in docs:
                goal_data = self._deserialize_goal_data(doc.id, doc.to_dict())
                goals.append(GoalResponse.from_goal_data(goal_data))
            
            return goals
            
        except Exception as e:
            logger.error(f"Error fetching goals for user {user_id}: {e}")
            raise

    async def get_goal_by_id(self, user_id: str, goal_id: str) -> Optional[GoalResponse]:
        """
        Get a specific goal by ID.
        
        Args:
            user_id: User's Firebase UID
            goal_id: Goal document ID
            
        Returns:
            GoalResponse if found, None otherwise
        """
        try:
            goals_ref = self._get_goals_collection(user_id)
            doc_ref = goals_ref.document(goal_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
            
            goal_data = self._deserialize_goal_data(doc.id, doc.to_dict())
            return GoalResponse.from_goal_data(goal_data)
            
        except Exception as e:
            logger.error(f"Error fetching goal {goal_id} for user {user_id}: {e}")
            raise

    async def update_goal(
        self, user_id: str, goal_id: str, update_data: GoalUpdate
    ) -> Optional[GoalResponse]:
        """
        Update a goal.
        
        Args:
            user_id: User's Firebase UID
            goal_id: Goal document ID
            update_data: Fields to update
            
        Returns:
            Updated GoalResponse if found, None otherwise
        """
        try:
            goals_ref = self._get_goals_collection(user_id)
            doc_ref = goals_ref.document(goal_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
            
            # Get current goal data
            current_data = doc.to_dict()
            old_saved = current_data.get("saved_amount", 0)
            old_target = current_data.get("target_amount", 0)
            old_progress = self.calculate_progress(old_saved, old_target)
            
            # Prepare update dict (only non-None values)
            update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
            
            if not update_dict:
                # No updates provided
                goal_data = self._deserialize_goal_data(doc.id, current_data)
                return GoalResponse.from_goal_data(goal_data)
            
            # Validate saved_amount doesn't exceed target_amount
            new_saved = update_dict.get("saved_amount", old_saved)
            new_target = update_dict.get("target_amount", old_target)
            
            if new_saved > new_target:
                raise ValueError("Saved amount cannot exceed target amount")
            
            # Add updated_at timestamp
            update_dict["updated_at"] = datetime.utcnow()
            
            # Serialize for Firestore
            update_dict = self._serialize_goal_data(update_dict)
            
            # Check if goal should be marked as completed
            new_progress = self.calculate_progress(new_saved, new_target)
            if new_progress >= 100 and current_data.get("status") != GoalStatus.COMPLETED.value:
                update_dict["status"] = GoalStatus.COMPLETED.value
            
            # Update document
            doc_ref.update(update_dict)
            
            # Get updated document
            updated_doc = doc_ref.get()
            goal_data = self._deserialize_goal_data(updated_doc.id, updated_doc.to_dict())
            
            # Check for milestone notification
            milestone = self._check_milestone_reached(old_progress, new_progress)
            if milestone:
                await self._trigger_milestone_notification(
                    user_id, goal_id, goal_data.get("title", "Goal"), milestone
                )
            
            logger.info(f"Goal {goal_id} updated for user {user_id}")
            return GoalResponse.from_goal_data(goal_data)
            
        except ValueError as e:
            raise e
        except Exception as e:
            logger.error(f"Error updating goal {goal_id} for user {user_id}: {e}")
            raise

    async def delete_goal(self, user_id: str, goal_id: str) -> bool:
        """
        Delete a goal.
        
        Args:
            user_id: User's Firebase UID
            goal_id: Goal document ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            goals_ref = self._get_goals_collection(user_id)
            doc_ref = goals_ref.document(goal_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            doc_ref.delete()
            logger.info(f"Goal {goal_id} deleted for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting goal {goal_id} for user {user_id}: {e}")
            raise

    async def get_goals_summary(self, user_id: str) -> Dict[str, Any]:
        """
        Get summary statistics of user's goals.
        
        Args:
            user_id: User's Firebase UID
            
        Returns:
            Dict with goals summary stats
        """
        try:
            goals = await self.get_goals(user_id)
            
            total_goals = len(goals)
            active_goals = len([g for g in goals if g.status == GoalStatus.ACTIVE])
            completed_goals = len([g for g in goals if g.status == GoalStatus.COMPLETED])
            
            total_target = sum(g.target_amount for g in goals if g.status == GoalStatus.ACTIVE)
            total_saved = sum(g.saved_amount for g in goals if g.status == GoalStatus.ACTIVE)
            overall_progress = self.calculate_progress(total_saved, total_target) if total_target > 0 else 0
            
            # Goals at risk (overdue or nearing deadline with low progress)
            at_risk = [
                g for g in goals 
                if g.status == GoalStatus.ACTIVE and (
                    g.is_overdue or 
                    (g.days_remaining is not None and g.days_remaining <= 7 and g.progress_percentage < 75)
                )
            ]
            
            return {
                "total_goals": total_goals,
                "active_goals": active_goals,
                "completed_goals": completed_goals,
                "total_target_amount": total_target,
                "total_saved_amount": total_saved,
                "overall_progress": overall_progress,
                "at_risk_count": len(at_risk),
                "at_risk_goals": [{"id": g.id, "title": g.title} for g in at_risk]
            }
            
        except Exception as e:
            logger.error(f"Error fetching goals summary for user {user_id}: {e}")
            raise

    async def add_to_goal(
        self, user_id: str, goal_id: str, amount: float
    ) -> Optional[GoalResponse]:
        """
        Add an amount to a goal's saved_amount.
        
        Args:
            user_id: User's Firebase UID
            goal_id: Goal document ID
            amount: Amount to add (positive) or subtract (negative)
            
        Returns:
            Updated GoalResponse if found, None otherwise
        """
        try:
            goals_ref = self._get_goals_collection(user_id)
            doc_ref = goals_ref.document(goal_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
            
            current_data = doc.to_dict()
            current_saved = current_data.get("saved_amount", 0)
            if current_saved + amount < 0:
                raise ValueError(
                    f"Cannot subtract {abs(amount)} from goal '{goal_id}': only {current_saved} available."
                )
            new_saved = current_saved + amount
            
            # Create update with new saved amount
            update_data = GoalUpdate(saved_amount=new_saved)  # type: ignore
            return await self.update_goal(user_id, goal_id, update_data)
            
        except Exception as e:
            logger.error(f"Error adding to goal {goal_id} for user {user_id}: {e}")
            raise


# Create singleton instance
goal_service = GoalService()


def get_goal_service() -> GoalService:
    """Get goal service instance."""
    return goal_service
