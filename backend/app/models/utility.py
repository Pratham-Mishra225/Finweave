"""Utility-related Pydantic models."""
from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime, date
from enum import Enum

from app.models.common import RecurringFrequency


class DebtType(str, Enum):
    """Debt type enum."""
    OWED = "owed"  # Money you owe to someone
    LENT = "lent"  # Money someone owes to you


class DebtStatus(str, Enum):
    """Debt status enum."""
    PENDING = "pending"
    PAID = "paid"
    PARTIAL = "partial"


class DebtEntry(BaseModel):
    """Debt entry model."""
    person_name: str = Field(..., min_length=1, max_length=100)
    amount: float = Field(..., gt=0)
    type: DebtType
    status: DebtStatus = DebtStatus.PENDING
    description: Optional[str] = None
    due_date: Optional[date] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now())


class DebtResponse(DebtEntry):
    """Debt response model."""
    id: str
    user_id: str
    paid_amount: float = 0.0
    remaining_amount: float = 0.0
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class DebtUpdate(BaseModel):
    """Debt update model."""
    person_name: Optional[str] = Field(None, min_length=1, max_length=100)
    amount: Optional[float] = Field(None, gt=0)
    status: Optional[DebtStatus] = None
    description: Optional[str] = None
    due_date: Optional[date] = None
    paid_amount: Optional[float] = Field(None, ge=0)


class NetWorthData(BaseModel):
    """Net worth calculation data."""
    assets: float = 0.0
    liabilities: float = 0.0
    net_worth: float = 0.0
    asset_breakdown: Dict[str, float] = {}
    liability_breakdown: Dict[str, float] = {}
    calculated_at: datetime = Field(default_factory=lambda: datetime.now())


class ReportType(str, Enum):
    """Report type enum."""
    MONTHLY = "monthly"
    ANNUAL = "annual"
    CUSTOM = "custom"


class ReportFormat(str, Enum):
    """Report format enum."""
    PDF = "pdf"
    CSV = "csv"


class ReportRequest(BaseModel):
    """Request model for generating reports."""
    type: ReportType
    format: ReportFormat
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    month: Optional[int] = Field(None, ge=1, le=12)
    year: Optional[int] = Field(None, ge=2000, le=2100)
    include_charts: bool = True
    include_categories: bool = True
    include_goals: bool = False


class ReportResponse(BaseModel):
    """Response model for generated reports."""
    report_id: str
    filename: str
    file_url: str
    file_size: int
    format: ReportFormat
    generated_at: datetime
    expires_at: Optional[datetime] = None


class ReceiptScanResponse(BaseModel):
    """Response model for receipt scanning."""
    merchant_name: Optional[str] = None
    amount: Optional[float] = None
    date: Optional[date] = None
    items: List[Dict[str, Any]] = []
    category: Optional[str] = None
    raw_text: Optional[str] = None
    confidence: float = 0.0
    success: bool = False
    error_message: Optional[str] = None


class ExportRequest(BaseModel):
    """Request model for exporting transactions."""
    format: ReportFormat
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    categories: Optional[List[str]] = None
    include_metadata: bool = True


class BillReminder(BaseModel):
    """Bill reminder model."""
    title: str = Field(..., min_length=1, max_length=200)
    amount: float = Field(..., gt=0)
    due_date: date
    recurring: bool = False
    recurring_frequency: Optional[RecurringFrequency] = None
    category: str = "Bills"
    description: Optional[str] = None
    reminder_days_before: int = Field(default=3, ge=1, le=30)


class BillReminderResponse(BillReminder):
    """Bill reminder response model."""
    id: str
    user_id: str
    paid: bool = False
    paid_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
