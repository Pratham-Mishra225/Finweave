"""Transaction-related Pydantic models."""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime, date
from enum import Enum

from app.models.common import RecurringFrequency


class TransactionType(str, Enum):
    """Transaction type enum."""
    INCOME = "income"
    EXPENSE = "expense"


class TransactionCategory(str, Enum):
    """Transaction category enum."""
    FOOD = "Food"
    BILLS = "Bills"
    SHOPPING = "Shopping"
    TRAVEL = "Travel"
    SUBSCRIPTIONS = "Subscriptions"
    SALARY = "Salary"
    FREELANCE = "Freelance"
    INVESTMENT = "Investment"
    OTHERS = "Others"


class TransactionBase(BaseModel):
    """Base transaction model."""
    name: str = Field(..., min_length=1, max_length=200)
    amount: float = Field(..., gt=0)
    type: TransactionType
    category: TransactionCategory
    description: Optional[str] = None
    date: datetime
    recurring: bool = False
    recurring_frequency: Optional[RecurringFrequency] = None


class TransactionCreate(TransactionBase):
    """Model for creating a new transaction."""
    pass


class TransactionResponse(TransactionBase):
    """Model for transaction API responses."""
    id: str
    user_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TransactionFilter(BaseModel):
    """Model for filtering transactions."""
    category: Optional[TransactionCategory] = None
    type: Optional[TransactionType] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    search_query: Optional[str] = None
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)


class TransactionSummary(BaseModel):
    """Summary statistics for transactions."""
    total_income: float = 0.0
    total_expenses: float = 0.0
    net_balance: float = 0.0
    transaction_count: int = 0
    average_transaction: float = 0.0
    top_category: Optional[str] = None
    top_category_amount: Optional[float] = None


class TransactionUpdate(BaseModel):
    """Model for updating a transaction."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    amount: Optional[float] = Field(None, gt=0)
    type: Optional[TransactionType] = None
    category: Optional[TransactionCategory] = None
    description: Optional[str] = None
    date: Optional[datetime] = None
    recurring: Optional[bool] = None
    recurring_frequency: Optional[RecurringFrequency] = None


class PaginatedTransactions(BaseModel):
    """Paginated transaction response."""
    transactions: List[TransactionResponse]
    total: int
    page: int
    limit: int
    pages: int
