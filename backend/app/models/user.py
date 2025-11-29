"""User-related Pydantic models."""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Dict, Any
from datetime import datetime


class UserPreferences(BaseModel):
    """User preferences and settings."""
    dark_mode: bool = False
    notifications_enabled: bool = True
    email_notifications: bool = True
    push_notifications: bool = True
    currency: str = "USD"
    language: str = "en"


class UserStats(BaseModel):
    """User statistics."""
    balance: float = 0.0
    total_transactions: int = 0
    total_goals: int = 0
    active_goals: int = 0
    completed_goals: int = 0
    total_income: float = 0.0
    total_expenses: float = 0.0
    this_month_expenses: float = 0.0


class UserBase(BaseModel):
    """Base user model with common fields."""
    email: EmailStr
    name: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    """Model for creating a new user."""
    firebase_uid: str
    preferences: Optional[UserPreferences] = UserPreferences()


class UserResponse(UserBase):
    """Model for user API responses."""
    uid: str
    balance: float = 0.0
    created_at: datetime
    updated_at: Optional[datetime] = None
    preferences: UserPreferences
    stats: Optional[UserStats] = None
    
    # Financial profile fields
    assets: Optional[float] = None
    liabilities: Optional[float] = None
    
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """Model for updating user information."""
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    assets: Optional[float] = None
    liabilities: Optional[float] = None


class UserPreferencesUpdate(BaseModel):
    """Model for updating user preferences."""
    dark_mode: Optional[bool] = None
    notifications_enabled: Optional[bool] = None
    email_notifications: Optional[bool] = None
    push_notifications: Optional[bool] = None
    currency: Optional[str] = None
    language: Optional[str] = None
