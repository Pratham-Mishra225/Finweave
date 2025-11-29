"""Goal-related Pydantic models."""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime, date
from enum import Enum


class GoalCategory(str, Enum):
    """Goal category enum."""
    SAVINGS = "Savings"
    INVESTMENT = "Investment"
    PURCHASE = "Purchase"
    TRAVEL = "Travel"
    EDUCATION = "Education"
    EMERGENCY = "Emergency"
    DEBT = "Debt"
    OTHER = "Other"


class GoalStatus(str, Enum):
    """Goal status enum."""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class GoalBase(BaseModel):
    """Base goal model."""
    title: str = Field(..., min_length=1, max_length=200)
    target_amount: float = Field(..., gt=0)
    saved_amount: float = Field(default=0.0, ge=0)
    deadline: Optional[date] = None
    category: GoalCategory
    description: Optional[str] = None
    
    @field_validator('saved_amount')
    @classmethod
    def saved_must_not_exceed_target(cls, v, info):
        """Validate that saved amount does not exceed target.
        
        Note: For GoalUpdate, this validator may not have access to existing values
        from the database. Additional validation should be performed in the service
        layer when processing updates to ensure saved_amount doesn't exceed target_amount.
        """
        if 'target_amount' in info.data and v > info.data['target_amount']:
            raise ValueError('Saved amount cannot exceed target amount')
        return v


class GoalCreate(GoalBase):
    """Model for creating a new goal."""
    pass


class GoalUpdate(BaseModel):
    """Model for updating a goal."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    target_amount: Optional[float] = Field(None, gt=0)
    saved_amount: Optional[float] = Field(None, ge=0)
    deadline: Optional[date] = None
    category: Optional[GoalCategory] = None
    description: Optional[str] = None
    status: Optional[GoalStatus] = None


class GoalResponse(GoalBase):
    """Model for goal API responses with calculated fields."""
    id: str
    user_id: str
    status: GoalStatus = GoalStatus.ACTIVE
    progress_percentage: float = 0.0
    remaining_amount: float = 0.0
    days_remaining: Optional[int] = None
    is_overdue: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    @classmethod
    def from_goal_data(cls, goal_data: dict) -> "GoalResponse":
        """Create GoalResponse with calculated fields."""
        target = goal_data.get('target_amount', 0)
        saved = goal_data.get('saved_amount', 0)
        deadline = goal_data.get('deadline')
        
        # Calculate progress percentage
        progress = (saved / target * 100) if target > 0 else 0
        progress = min(progress, 100)  # Cap at 100%
        
        # Calculate remaining amount
        remaining = max(target - saved, 0)
        
        # Calculate days remaining
        days_remaining = None
        is_overdue = False
        if deadline:
            if isinstance(deadline, str):
                deadline = datetime.fromisoformat(deadline).date()
            delta = deadline - date.today()
            days_remaining = delta.days
            is_overdue = days_remaining < 0
        
        return cls(
            **goal_data,
            progress_percentage=round(progress, 2),
            remaining_amount=remaining,
            days_remaining=days_remaining,
            is_overdue=is_overdue
        )
    
    class Config:
        from_attributes = True


class GoalMilestone(BaseModel):
    """Model for goal milestone notifications."""
    goal_id: str
    milestone_percentage: int  # 25, 50, 75, 100
    message: str
    achieved_at: datetime
