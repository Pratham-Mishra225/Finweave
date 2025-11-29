"""Notifications router for managing user notifications."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional

from app.models.notification import (
    NotificationResponse,
    NotificationStats
)
from app.services.notification_service import (
    get_notification_service,
    NotificationService
)
from app.utils.auth import get_current_user

router = APIRouter(
    prefix="/notifications",
    tags=["notifications"],
    responses={401: {"description": "Unauthorized"}}
)


@router.get("", response_model=None)
async def get_notifications(
    filter: Optional[str] = Query(
        "all",
        description="Filter by notification type: all, transactions, goals, insights, alerts"
    ),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Get paginated notifications for the authenticated user.
    
    - **filter**: Filter notifications by type (all, transactions, goals, insights, alerts)
    - **page**: Page number for pagination (default: 1)
    - **limit**: Number of notifications per page (default: 20, max: 100)
    
    Returns:
    - List of notifications
    - Pagination metadata (total_count, page, limit, total_pages, has_next, has_previous)
    """
    try:
        result = await notification_service.get_notifications(
            user_id=current_user["uid"],
            filter_type=filter,
            page=page,
            limit=limit
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats", response_model=NotificationStats)
async def get_notification_stats(
    current_user: dict = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Get notification statistics for the authenticated user.
    
    Returns:
    - total_count: Total number of notifications
    - unread_count: Number of unread notifications
    - by_type: Count breakdown by notification type
    - by_priority: Count breakdown by priority level
    """
    try:
        stats = await notification_service.get_notification_stats(
            user_id=current_user["uid"]
        )
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unread-count")
async def get_unread_count(
    current_user: dict = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Get count of unread notifications for the authenticated user.
    
    Returns:
    - unread_count: Number of unread notifications
    """
    try:
        count = await notification_service.get_unread_count(
            user_id=current_user["uid"]
        )
        return {"unread_count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{notification_id}", response_model=NotificationResponse)
async def get_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Get a specific notification by ID.
    
    Returns notification details including:
    - type, title, message
    - read status
    - created_at timestamp
    - metadata
    """
    try:
        notification = await notification_service.get_notification_by_id(
            user_id=current_user["uid"],
            notification_id=notification_id
        )
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        return notification
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{notification_id}/mark-read", response_model=NotificationResponse)
async def mark_notification_read(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Mark a specific notification as read.
    
    Updates:
    - read: True
    - read_at: Current timestamp
    
    Returns the updated notification.
    """
    try:
        notification = await notification_service.mark_as_read(
            user_id=current_user["uid"],
            notification_id=notification_id
        )
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        return notification
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/mark-all-read")
async def mark_all_notifications_read(
    current_user: dict = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Mark all notifications as read for the authenticated user.
    
    Returns:
    - updated_count: Number of notifications marked as read
    - message: Confirmation message
    """
    try:
        updated_count = await notification_service.mark_all_as_read(
            user_id=current_user["uid"]
        )
        return {
            "updated_count": updated_count,
            "message": f"Successfully marked {updated_count} notifications as read"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{notification_id}", status_code=204)
async def delete_notification(
    notification_id: str,
    current_user: dict = Depends(get_current_user),
    notification_service: NotificationService = Depends(get_notification_service)
):
    """
    Delete a specific notification.
    
    This permanently removes the notification and cannot be undone.
    """
    try:
        deleted = await notification_service.delete_notification(
            user_id=current_user["uid"],
            notification_id=notification_id
        )
        if not deleted:
            raise HTTPException(status_code=404, detail="Notification not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
