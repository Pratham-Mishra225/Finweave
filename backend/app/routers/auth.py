"""Authentication routes for user signup, login, and token verification."""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
from firebase_admin import auth as firebase_auth
from app.utils.auth import verify_firebase_token, get_current_user
from app.services.user_service import user_service
from app.models.user import UserCreate, UserPreferences
import logging

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/auth", tags=["authentication"])


class SignupRequest(BaseModel):
    """Request model for user signup."""
    email: EmailStr
    password: str
    name: str
    phone: Optional[str] = None


class LoginResponse(BaseModel):
    """Response model for login."""
    message: str
    user: dict


class TokenVerifyResponse(BaseModel):
    """Response model for token verification."""
    valid: bool
    user: Optional[dict] = None


class UserProfileResponse(BaseModel):
    """Response model for user profile."""
    uid: str
    email: str
    name: str
    phone: Optional[str]
    avatar_url: Optional[str]
    balance: float
    created_at: str
    preferences: dict


@router.post("/signup", response_model=LoginResponse)
async def signup(request: SignupRequest):
    """
    Create a new user account with email and password.
    
    This endpoint:
    1. Creates Firebase Authentication user
    2. Creates corresponding user document in MongoDB
    
    Args:
        request: Signup request with email, password, and profile info
        
    Returns:
        User information and success message
        
    Raises:
        HTTPException: If user already exists or creation fails
    """
    try:
        # Check if user already exists in MongoDB by email
        existing_user = await user_service.get_user_by_email(request.email)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="User with this email already exists"
            )
        
        # Create Firebase Authentication user
        user_record = firebase_auth.create_user(
            email=request.email,
            password=request.password,
            display_name=request.name,
            email_verified=False
        )
        
        # Create user document in MongoDB
        user_data = UserCreate(
            firebase_uid=user_record.uid,
            email=request.email,
            name=request.name,
            phone=request.phone,
            preferences=UserPreferences()
        )
        
        firestore_user = await user_service.create_user(user_data)
        
        return LoginResponse(
            message="User created successfully. Please verify your email.",
            user={
                "uid": user_record.uid,
                "email": user_record.email,
                "name": user_record.display_name,
                "email_verified": user_record.email_verified
            }
        )
        
    except firebase_auth.EmailAlreadyExistsError:
        raise HTTPException(
            status_code=400,
            detail="User with this email already exists in Firebase Auth"
        )
    except Exception as e:
        # Clean up Firebase user if MongoDB creation fails
        try:
            if 'user_record' in locals():
                firebase_auth.delete_user(user_record.uid)
        except Exception as cleanup_error:
            logger.warning(f"Failed to cleanup Firebase user: {cleanup_error}")
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create user: {str(e)}"
        )


@router.post("/login/verify-token", response_model=TokenVerifyResponse)
async def verify_token(token_data: dict = Depends(verify_firebase_token)):
    """
    Verify Firebase ID token and sync user data.
    
    This endpoint:
    1. Verifies the Firebase token
    2. Creates MongoDB user if doesn't exist (for Google sign-in)
    3. Returns user information
    
    Args:
        token_data: Decoded Firebase token from dependency
        
    Returns:
        Token validity and user information
    """
    try:
        uid = token_data.get("uid")
        email = token_data.get("email")
        name = token_data.get("name", email.split("@")[0])
        
        logger.info(f"Token verification request for uid: {uid}, email: {email}")
        
        # Check if user exists in MongoDB
        user = await user_service.get_user(uid)
        
        logger.info(f"User exists in MongoDB: {user is not None}")
        
        # Create user if doesn't exist (happens with Google sign-in)
        # Use upsert to handle race conditions atomically
        if not user:
            logger.info(f"Creating new user in MongoDB for uid: {uid}")
            user = await user_service.upsert_user(uid, email, name)
            logger.info(f"User created successfully: {user}")
        
        return TokenVerifyResponse(
            valid=True,
            user={
                "uid": uid,
                "email": email,
                "name": name,
                "email_verified": token_data.get("email_verified", False)
            }
        )
        
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Token verification failed: {str(e)}"
        )


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """
    Get current user's profile from MongoDB.
    
    Args:
        current_user: Authenticated user from token
        
    Returns:
        User profile information
        
    Raises:
        HTTPException: If user not found
    """
    try:
        uid = current_user["uid"]
        user = await user_service.get_user(uid)
        
        if not user:
            raise HTTPException(
                status_code=404,
                detail="User profile not found"
            )
        
        return UserProfileResponse(
            uid=user["uid"],
            email=user["email"],
            name=user["name"],
            phone=user.get("phone"),
            avatar_url=user.get("avatar_url"),
            balance=user.get("balance", 0.0),
            created_at=user.get("created_at", ""),
            preferences=user.get("preferences", {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch profile: {str(e)}"
        )


@router.delete("/delete-account")
async def delete_account(current_user: dict = Depends(get_current_user)):
    """
    Delete user account from both Firebase Auth and MongoDB.
    
    Args:
        current_user: Authenticated user from token
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If deletion fails
    """
    try:
        uid = current_user["uid"]
        
        # Delete from MongoDB
        await user_service.delete_user(uid)
        
        # Delete from Firebase Auth
        firebase_auth.delete_user(uid)
        
        return {"message": "Account deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete account: {str(e)}"
        )


@router.post("/send-verification-email")
async def send_verification_email(current_user: dict = Depends(get_current_user)):
    """
    Send email verification link to user.
    
    Note: This generates a verification link that should be sent via your email service.
    Firebase Admin SDK doesn't send emails directly.
    
    Args:
        current_user: Authenticated user from token
        
    Returns:
        Verification link
    """
    try:
        link = firebase_auth.generate_email_verification_link(current_user["email"])
        
        return {
            "message": "Verification link generated",
            "link": link,
            "note": "Send this link to user via your email service"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate verification link: {str(e)}"
        )
