"""Profile and account management routes."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from app.utils.auth import get_current_user
from app.services.profile_service import profile_service
from app.models.user import UserUpdate, UserPreferencesUpdate
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("")
async def get_profile(current_user: dict = Depends(get_current_user)):
    """
    Get current user's profile with stats.
    
    Args:
        current_user: Authenticated user from token
        
    Returns:
        User profile with statistics
        
    Raises:
        HTTPException: If profile fetch fails
    """
    try:
        uid = current_user["uid"]
        profile = await profile_service.get_profile_with_stats(uid)
        
        if not profile:
            raise HTTPException(
                status_code=404,
                detail="Profile not found"
            )
        
        return profile
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch profile: {str(e)}"
        )


@router.put("")
async def update_profile(
    user_data: UserUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update user profile information.
    
    Args:
        user_data: Updated user data
        current_user: Authenticated user from token
        
    Returns:
        Updated user profile
        
    Raises:
        HTTPException: If update fails
    """
    try:
        uid = current_user["uid"]
        updated_user = await profile_service.update_profile(uid, user_data)
        
        if not updated_user:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        
        return {
            "message": "Profile updated successfully",
            "user": updated_user
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating profile: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update profile: {str(e)}"
        )


@router.put("/preferences")
async def update_preferences(
    preferences: UserPreferencesUpdate,
    current_user: dict = Depends(get_current_user)
):
    """
    Update user preferences.
    
    Args:
        preferences: Updated preferences
        current_user: Authenticated user from token
        
    Returns:
        Updated preferences
        
    Raises:
        HTTPException: If update fails
    """
    try:
        uid = current_user["uid"]
        updated_prefs = await profile_service.update_preferences(uid, preferences)
        
        if not updated_prefs:
            raise HTTPException(
                status_code=404,
                detail="User not found"
            )
        
        return {
            "message": "Preferences updated successfully",
            "preferences": updated_prefs
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating preferences: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update preferences: {str(e)}"
        )


@router.get("/stats")
async def get_stats(current_user: dict = Depends(get_current_user)):
    """
    Get user statistics (balance, goals count, transactions count).
    
    Args:
        current_user: Authenticated user from token
        
    Returns:
        User statistics
        
    Raises:
        HTTPException: If stats fetch fails
    """
    try:
        uid = current_user["uid"]
        stats = await profile_service.calculate_user_stats(uid)
        
        return {
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error fetching stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch stats: {str(e)}"
        )
