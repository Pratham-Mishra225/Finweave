"""Notification service for managing user notifications in Firestore."""
import logging
from datetime import datetime
from typing import Optional, Dict, Any

from app.config.firebase import get_firestore_db
from app.models.notification import (
    NotificationResponse,
    NotificationStats,
    NotificationType,
    NotificationPriority
)

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for managing notifications stored in Firestore."""

    def __init__(self):
        self.firestore_db = None

    def _get_firestore_db(self):
        """Lazily fetch Firestore client to avoid requiring init at import time."""
        if self.firestore_db is None:
            self.firestore_db = get_firestore_db()
        return self.firestore_db

    def _get_notifications_collection(self, user_id: str):
        """Get the notifications subcollection for a user."""
        return self._get_firestore_db().collection("users").document(user_id).collection("notifications")

    def _serialize_notification_data(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Serialize notification data for Firestore storage."""
        data = notification_data.copy()
        
        # Convert type enum to string
        if 'type' in data and hasattr(data['type'], 'value'):
            data['type'] = data['type'].value
            
        # Convert priority enum to string
        if 'priority' in data and hasattr(data['priority'], 'value'):
            data['priority'] = data['priority'].value
            
        return data

    def _deserialize_notification_data(
        self, doc_id: str, doc_data: Dict[str, Any], user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Deserialize notification data from Firestore."""
        data = doc_data.copy()
        data['id'] = doc_id
        if 'user_id' not in data and user_id:
            data['user_id'] = user_id
        
        # Convert timestamps
        if 'created_at' in data and hasattr(data['created_at'], 'isoformat'):
            pass  # Keep as datetime
        
        return data

    async def create_notification(
        self,
        user_id: str,
        notification_type: NotificationType,
        title: str,
        message: str,
        priority: NotificationPriority = NotificationPriority.MEDIUM,
        metadata: Optional[Dict[str, Any]] = None
    ) -> NotificationResponse:
        """
        Create a new notification for a user.
        
        Args:
            user_id: User's Firebase UID
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            priority: Notification priority level
            metadata: Additional metadata
            
        Returns:
            NotificationResponse with created notification
        """
        try:
            notification_dict = {
                "type": notification_type.value,
                "title": title,
                "message": message,
                "priority": priority.value,
                "read": False,
                "created_at": datetime.utcnow(),
                "read_at": None,
                "metadata": metadata or {},
                "user_id": user_id
            }
            
            # Add to Firestore
            notifications_ref = self._get_notifications_collection(user_id)
            doc_ref = notifications_ref.add(notification_dict)
            
            # Get the document ID
            notification_id = doc_ref[1].id
            
            # Prepare response data
            response_data = self._deserialize_notification_data(notification_id, notification_dict, user_id)
            
            logger.info(f"Notification created for user {user_id}: {notification_id}")
            return NotificationResponse(**response_data)
            
        except Exception as e:
            logger.error(f"Error creating notification for user {user_id}: {e}")
            raise

    async def get_notifications(
        self,
        user_id: str,
        filter_type: Optional[str] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """
        Get paginated notifications for a user.
        
        Args:
            user_id: User's Firebase UID
            filter_type: Filter by notification type (all, transactions, goals, insights, alerts)
            page: Page number (1-indexed)
            limit: Number of notifications per page
            
        Returns:
            Dict with notifications list and pagination info
        """
        try:
            notifications_ref = self._get_notifications_collection(user_id)
            
            # Always order by created_at to avoid composite index requirement for filters
            query = notifications_ref.order_by("created_at", direction="DESCENDING")

            # Fetch all documents (limited by Firestore to 1MB per request)
            all_docs = list(query.stream())

            # Apply optional type filter in memory to avoid composite index requirement
            type_mapping = {
                "transactions": NotificationType.TRANSACTION.value,
                "goals": NotificationType.GOAL.value,
                "insights": NotificationType.INSIGHT.value,
                "alerts": NotificationType.ALERT.value
            }
            active_filter_value = None
            if filter_type and filter_type != "all":
                active_filter_value = type_mapping.get(filter_type)

            filtered_docs = []
            for doc in all_docs:
                doc_dict = doc.to_dict()
                if active_filter_value and doc_dict.get("type") != active_filter_value:
                    continue
                filtered_docs.append(doc)

            total_count = len(filtered_docs)

            # Calculate pagination
            offset = (page - 1) * limit
            paginated_docs = filtered_docs[offset:offset + limit]
            
            # Convert to response models
            notifications = []
            for doc in paginated_docs:
                data = self._deserialize_notification_data(doc.id, doc.to_dict(), user_id)
                notifications.append(NotificationResponse(**data))
            
            return {
                "notifications": notifications,
                "total_count": total_count,
                "page": page,
                "limit": limit,
                "total_pages": (total_count + limit - 1) // limit if total_count > 0 else 1,
                "has_next": offset + limit < total_count,
                "has_previous": page > 1
            }
            
        except Exception as e:
            logger.error(f"Error getting notifications for user {user_id}: {e}")
            raise

    async def get_notification_by_id(
        self, user_id: str, notification_id: str
    ) -> Optional[NotificationResponse]:
        """
        Get a single notification by ID.
        
        Args:
            user_id: User's Firebase UID
            notification_id: Notification ID
            
        Returns:
            NotificationResponse if found, None otherwise
        """
        try:
            notifications_ref = self._get_notifications_collection(user_id)
            doc_ref = notifications_ref.document(notification_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
            
            data = self._deserialize_notification_data(doc.id, doc.to_dict(), user_id)
            return NotificationResponse(**data)
            
        except Exception as e:
            logger.error(f"Error getting notification {notification_id} for user {user_id}: {e}")
            raise

    async def mark_as_read(
        self, user_id: str, notification_id: str
    ) -> Optional[NotificationResponse]:
        """
        Mark a notification as read.
        
        Args:
            user_id: User's Firebase UID
            notification_id: Notification ID
            
        Returns:
            Updated NotificationResponse if found, None otherwise
        """
        try:
            notifications_ref = self._get_notifications_collection(user_id)
            doc_ref = notifications_ref.document(notification_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return None
            
            # Update read status
            update_data = {
                "read": True,
                "read_at": datetime.utcnow()
            }
            doc_ref.update(update_data)
            
            # Get updated document
            updated_doc = doc_ref.get()
            data = self._deserialize_notification_data(updated_doc.id, updated_doc.to_dict(), user_id)
            
            logger.info(f"Notification {notification_id} marked as read for user {user_id}")
            return NotificationResponse(**data)
            
        except Exception as e:
            logger.error(f"Error marking notification {notification_id} as read: {e}")
            raise

    async def mark_all_as_read(self, user_id: str) -> int:
        """
        Mark all notifications as read for a user.
        
        Args:
            user_id: User's Firebase UID
            
        Returns:
            Number of notifications marked as read
        """
        try:
            notifications_ref = self._get_notifications_collection(user_id)
            
            # Get all unread notifications
            unread_query = notifications_ref.where("read", "==", False)
            unread_docs = list(unread_query.stream())
            
            # Batch update all unread notifications
            # Firestore batch operations have a limit of 500 operations
            read_at = datetime.utcnow()
            updated_count = 0
            BATCH_SIZE = 500

            db = self._get_firestore_db()
            
            # Process in chunks of 500 to handle large numbers of notifications
            for i in range(0, len(unread_docs), BATCH_SIZE):
                batch = db.batch()
                chunk = unread_docs[i:i + BATCH_SIZE]
                for doc in chunk:
                    batch.update(doc.reference, {
                        "read": True,
                        "read_at": read_at
                    })
                    updated_count += 1
                if chunk:
                    batch.commit()
            
            logger.info(f"Marked {updated_count} notifications as read for user {user_id}")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error marking all notifications as read for user {user_id}: {e}")
            raise

    async def delete_notification(
        self, user_id: str, notification_id: str
    ) -> bool:
        """
        Delete a notification.
        
        Args:
            user_id: User's Firebase UID
            notification_id: Notification ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            notifications_ref = self._get_notifications_collection(user_id)
            doc_ref = notifications_ref.document(notification_id)
            doc = doc_ref.get()
            
            if not doc.exists:
                return False
            
            doc_ref.delete()
            
            logger.info(f"Notification {notification_id} deleted for user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting notification {notification_id}: {e}")
            raise

    async def get_notification_stats(self, user_id: str) -> NotificationStats:
        """
        Get notification statistics for a user.
        
        Args:
            user_id: User's Firebase UID
            
        Returns:
            NotificationStats with counts
        """
        try:
            notifications_ref = self._get_notifications_collection(user_id)
            all_docs = list(notifications_ref.stream())
            
            total_count = len(all_docs)
            unread_count = 0
            by_type: Dict[str, int] = {}
            by_priority: Dict[str, int] = {}
            
            for doc in all_docs:
                data = doc.to_dict()
                
                # Count unread
                if not data.get("read", False):
                    unread_count += 1
                
                # Count by type
                notif_type = data.get("type", "unknown")
                by_type[notif_type] = by_type.get(notif_type, 0) + 1
                
                # Count by priority
                priority = data.get("priority", "medium")
                by_priority[priority] = by_priority.get(priority, 0) + 1
            
            return NotificationStats(
                total_count=total_count,
                unread_count=unread_count,
                by_type=by_type,
                by_priority=by_priority
            )
            
        except Exception as e:
            logger.error(f"Error getting notification stats for user {user_id}: {e}")
            raise

    async def get_unread_count(self, user_id: str) -> int:
        """
        Get count of unread notifications for a user.
        
        Args:
            user_id: User's Firebase UID
            
        Returns:
            Number of unread notifications
        """
        try:
            notifications_ref = self._get_notifications_collection(user_id)
            unread_query = notifications_ref.where("read", "==", False)
            unread_docs = list(unread_query.stream())
            return len(unread_docs)
            
        except Exception as e:
            logger.error(f"Error getting unread count for user {user_id}: {e}")
            raise


# Event trigger functions
class NotificationEventTrigger:
    """Handles notification triggers for various events."""

    def __init__(self, notification_service: "NotificationService"):
        self.notification_service = notification_service

    async def trigger_on_transaction_added(
        self,
        user_id: str,
        transaction_name: str,
        amount: float,
        category: str,
        transaction_id: str
    ) -> NotificationResponse:
        """
        Trigger notification when a new transaction is added.
        Shows AI-powered goal impact analysis.
        
        Args:
            user_id: User's Firebase UID
            transaction_name: Name of the transaction
            amount: Transaction amount
            category: Transaction category
            transaction_id: Transaction ID
            
        Returns:
            Created notification
        """
        # Try to get AI-powered goal impact
        try:
            from app.services.ai.gemini_service import get_gemini_service
            gemini = get_gemini_service()
            transaction = {
                "amount": amount,
                "category": category,
                "description": transaction_name
            }
            goals = []  # Will be fetched in gemini service if needed
            monthly_stats = {}  # Could be populated if available
            impact = await gemini.get_transaction_impact(
                transaction,
                goals,
                monthly_stats
            )
            title = impact.get("title", "Transaction Added")
            message = impact.get("message", f"₹{abs(amount):.0f} {category}")
            
        except Exception as e:
            # Fallback to simple notification
            title = "Transaction Added"
            message = f"'{transaction_name}' for ₹{abs(amount):.0f} in {category} has been recorded."
        
        return await self.notification_service.create_notification(
            user_id=user_id,
            notification_type=NotificationType.TRANSACTION,
            title=title,
            message=message,
            priority=NotificationPriority.LOW,
            metadata={
                "transaction_id": transaction_id,
                "transaction_name": transaction_name,
                "amount": amount,
                "category": category
            }
        )

    async def trigger_on_goal_milestone(
        self,
        user_id: str,
        goal_id: str,
        goal_title: str,
        milestone: int,
        saved_amount: float,
        target_amount: float
    ) -> NotificationResponse:
        """
        Trigger notification when a goal milestone is reached.
        
        Args:
            user_id: User's Firebase UID
            goal_id: Goal ID
            goal_title: Goal title
            milestone: Milestone percentage (25, 50, 75, 100)
            saved_amount: Current saved amount
            target_amount: Target amount
            
        Returns:
            Created notification
        """
        messages = {
            25: f"Great start! You're 25% of the way to '{goal_title}'! 🎯",
            50: f"Halfway there! You've reached 50% of '{goal_title}'! 🌟",
            75: f"Almost there! You're 75% to '{goal_title}'! 🔥",
            100: f"Congratulations! You've achieved '{goal_title}'! 🎉"
        }
        
        title = f"Goal Milestone: {milestone}%"
        message = messages.get(milestone, f"You've reached {milestone}% of your goal '{goal_title}'!")
        priority = NotificationPriority.HIGH if milestone == 100 else NotificationPriority.MEDIUM
        
        return await self.notification_service.create_notification(
            user_id=user_id,
            notification_type=NotificationType.GOAL,
            title=title,
            message=message,
            priority=priority,
            metadata={
                "goal_id": goal_id,
                "goal_title": goal_title,
                "milestone": milestone,
                "saved_amount": saved_amount,
                "target_amount": target_amount
            }
        )

    async def trigger_on_budget_alert(
        self,
        user_id: str,
        category: str,
        spent_amount: float,
        budget_amount: float,
        percentage: float
    ) -> NotificationResponse:
        """
        Trigger notification when budget threshold is reached.
        
        Args:
            user_id: User's Firebase UID
            category: Budget category
            spent_amount: Amount spent
            budget_amount: Budget limit
            percentage: Percentage of budget used
            
        Returns:
            Created notification
        """
        if percentage >= 100:
            title = "Budget Exceeded!"
            message = f"You've exceeded your {category} budget! Spent ₹{spent_amount:.2f} of ₹{budget_amount:.2f}."
            priority = NotificationPriority.HIGH
        elif percentage >= 90:
            title = "Budget Warning"
            message = f"You've used {percentage:.0f}% of your {category} budget (₹{spent_amount:.2f}/₹{budget_amount:.2f})."
            priority = NotificationPriority.HIGH
        else:
            title = "Budget Alert"
            message = f"You've used {percentage:.0f}% of your {category} budget."
            priority = NotificationPriority.MEDIUM
        
        return await self.notification_service.create_notification(
            user_id=user_id,
            notification_type=NotificationType.ALERT,
            title=title,
            message=message,
            priority=priority,
            metadata={
                "category": category,
                "spent_amount": spent_amount,
                "budget_amount": budget_amount,
                "percentage": percentage
            }
        )

    async def trigger_on_bill_reminder(
        self,
        user_id: str,
        bill_name: str,
        amount: float,
        due_date: str,
        days_until_due: int
    ) -> NotificationResponse:
        """
        Trigger notification for upcoming bill reminder.
        
        Args:
            user_id: User's Firebase UID
            bill_name: Name of the bill
            amount: Bill amount
            due_date: Due date string
            days_until_due: Days until bill is due
            
        Returns:
            Created notification
        """
        if days_until_due == 0:
            title = "Bill Due Today!"
            message = f"Your {bill_name} payment of ₹{amount:.2f} is due today."
            priority = NotificationPriority.HIGH
        elif days_until_due == 1:
            title = "Bill Due Tomorrow"
            message = f"Your {bill_name} payment of ₹{amount:.2f} is due tomorrow."
            priority = NotificationPriority.HIGH
        elif days_until_due <= 3:
            title = "Upcoming Bill"
            message = f"Your {bill_name} payment of ₹{amount:.2f} is due in {days_until_due} days."
            priority = NotificationPriority.MEDIUM
        else:
            title = "Bill Reminder"
            message = f"Your {bill_name} payment of ₹{amount:.2f} is due on {due_date}."
            priority = NotificationPriority.LOW
        
        return await self.notification_service.create_notification(
            user_id=user_id,
            notification_type=NotificationType.BILL,
            title=title,
            message=message,
            priority=priority,
            metadata={
                "bill_name": bill_name,
                "amount": amount,
                "due_date": due_date,
                "days_until_due": days_until_due
            }
        )

    async def trigger_on_insight(
        self,
        user_id: str,
        insight_title: str,
        insight_message: str,
        insight_type: str = "general"
    ) -> NotificationResponse:
        """
        Trigger notification for a new AI insight.
        
        Args:
            user_id: User's Firebase UID
            insight_title: Insight title
            insight_message: Insight message
            insight_type: Type of insight
            
        Returns:
            Created notification
        """
        return await self.notification_service.create_notification(
            user_id=user_id,
            notification_type=NotificationType.INSIGHT,
            title=insight_title,
            message=insight_message,
            priority=NotificationPriority.MEDIUM,
            metadata={
                "insight_type": insight_type
            }
        )

    async def trigger_on_achievement(
        self,
        user_id: str,
        achievement_name: str,
        achievement_description: str
    ) -> NotificationResponse:
        """
        Trigger notification for an achievement unlock.
        
        Args:
            user_id: User's Firebase UID
            achievement_name: Name of the achievement
            achievement_description: Achievement description
            
        Returns:
            Created notification
        """
        return await self.notification_service.create_notification(
            user_id=user_id,
            notification_type=NotificationType.ACHIEVEMENT,
            title=f"Achievement Unlocked: {achievement_name}!",
            message=achievement_description,
            priority=NotificationPriority.HIGH,
            metadata={
                "achievement_name": achievement_name
            }
        )


# Create singleton instances
notification_service = NotificationService()
notification_trigger = NotificationEventTrigger(notification_service)


def get_notification_service() -> NotificationService:
    """Get notification service instance."""
    return notification_service


def get_notification_trigger() -> NotificationEventTrigger:
    """Get notification event trigger instance."""
    return notification_trigger
