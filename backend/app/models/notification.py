"""Notification-related Pydantic models."""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class NotificationType(str, Enum):
    """Notification type enum."""
    TRANSACTION = "transaction"
    GOAL = "goal"
    INSIGHT = "insight"
    ALERT = "alert"
    BILL = "bill"
    ACHIEVEMENT = "achievement"
    SYSTEM = "system"


class NotificationPriority(str, Enum):
    """Notification priority enum."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class NotificationBase(BaseModel):
    """Base notification model."""
    type: NotificationType
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=500)
    priority: NotificationPriority = NotificationPriority.MEDIUM
    metadata: Optional[Dict[str, Any]] = None


class NotificationCreate(NotificationBase):
    """Model for creating a new notification."""
    user_id: str


class NotificationResponse(NotificationBase):
    """Model for notification API responses."""
    id: str
    user_id: str
    read: bool = False
    created_at: datetime
    read_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class NotificationFilter(BaseModel):
    """Model for filtering notifications."""
    type: Optional[NotificationType] = None
    read: Optional[bool] = None
    priority: Optional[NotificationPriority] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)


class NotificationUpdate(BaseModel):
    """Model for updating a notification."""
    read: Optional[bool] = None


class NotificationStats(BaseModel):
    """Notification statistics."""
    total_count: int = 0
    unread_count: int = 0
    by_type: Dict[str, int] = {}
    by_priority: Dict[str, int] = {}


class BulkNotificationUpdate(BaseModel):
    """Model for bulk notification updates."""
    notification_ids: List[str]
    read: bool
