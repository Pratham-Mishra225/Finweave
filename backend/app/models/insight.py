"""Insight-related Pydantic models."""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Literal
from datetime import datetime
from enum import Enum


class InsightType(str, Enum):
    """Insight type enum."""
    SPENDING_ALERT = "spending_alert"
    SAVINGS_TIP = "savings_tip"
    GOAL_PROGRESS = "goal_progress"
    BUDGET_WARNING = "budget_warning"
    TREND_ANALYSIS = "trend_analysis"
    FINANCIAL_HEALTH = "financial_health"


class TrendDirection(str, Enum):
    """Trend direction enum."""
    UP = "up"
    DOWN = "down"
    STABLE = "stable"


class InsightCard(BaseModel):
    """AI-generated insight card."""
    id: str
    type: InsightType
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=500)
    icon: str  # Icon name or emoji
    severity: Literal["info", "warning", "success", "error"] = "info"
    actionable: bool = False
    action_text: Optional[str] = None
    action_url: Optional[str] = None
    created_at: datetime
    metadata: Optional[Dict] = None


class CategoryBreakdown(BaseModel):
    """Category breakdown for bar chart."""
    category: str
    amount: float
    percentage: float
    transaction_count: int
    trend: TrendDirection
    color: str  # Hex color code


class CategorySummary(BaseModel):
    """Summary card for a spending category."""
    category: str
    current_month_amount: float
    previous_month_amount: float
    change_percentage: float
    trend: TrendDirection
    top_transaction: Optional[str] = None
    transaction_count: int


class SpendingOverview(BaseModel):
    """Spending overview chart data."""
    period: str  # "week", "month", "year"
    labels: List[str]  # Date labels
    income_data: List[float]
    expense_data: List[float]
    net_data: List[float]
    total_income: float
    total_expenses: float
    net_balance: float


class MonthlyComparison(BaseModel):
    """Month-over-month comparison."""
    current_month: str
    previous_month: str
    current_expenses: float
    previous_expenses: float
    change_amount: float
    change_percentage: float
    trend: TrendDirection


class InsightsDashboard(BaseModel):
    """Complete insights dashboard data."""
    insight_cards: List[InsightCard]
    category_breakdown: List[CategoryBreakdown]
    category_summaries: List[CategorySummary]
    spending_overview: SpendingOverview
    monthly_comparison: MonthlyComparison
    generated_at: datetime


class InsightCache(BaseModel):
    """Cached insights data stored in MongoDB."""
    user_id: str
    month: str  # Format: "YYYY-MM"
    category_breakdown: List[Dict]
    trends: Dict
    spending_patterns: Dict
    generated_at: datetime
    expires_at: datetime


class AIInsightCard(BaseModel):
    """AI-generated insight card with enhanced metadata."""
    id: str
    type: InsightType
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=500)
    icon: str
    severity: Literal["info", "warning", "success", "error"] = "info"
    actionable: bool = False
    action_text: Optional[str] = None
    action_url: Optional[str] = None
    created_at: datetime
    metadata: Optional[Dict] = None
    ai_generated: bool = True


class TrendAnalysis(BaseModel):
    """AI-generated trend analysis."""
    overall_trend: TrendDirection
    trend_percentage: float
    biggest_increase_category: Optional[str] = None
    biggest_decrease_category: Optional[str] = None
    analysis: str
    warning: Optional[str] = None
    positive: Optional[str] = None
    tip: str


class FinancialReportSummary(BaseModel):
    """AI-generated financial report summary."""
    summary: str
    highlights: List[str]
    concerns: List[str]
    recommendations: List[str]
    score: int = Field(ge=0, le=100)
    score_label: Literal["Excellent", "Good", "Fair", "Needs Attention"]
    generated_by_ai: bool = False
    generated_at: datetime


class AIInsightsResponse(BaseModel):
    """Response model for AI-generated insights endpoint."""
    insight_cards: List[AIInsightCard]
    trend_analysis: Optional[TrendAnalysis] = None
    generated_at: datetime
    ai_powered: bool = True
