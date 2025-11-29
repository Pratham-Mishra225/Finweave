"""Models package initialization."""
from app.models.common import RecurringFrequency
from app.models.user import (
    UserBase,
    UserCreate,
    UserResponse,
    UserUpdate,
    UserPreferences,
    UserPreferencesUpdate,
    UserStats
)
from app.models.transaction import (
    TransactionBase,
    TransactionCreate,
    TransactionResponse,
    TransactionUpdate,
    TransactionFilter,
    TransactionSummary,
    PaginatedTransactions,
    TransactionType,
    TransactionCategory
)
from app.models.goal import (
    GoalBase,
    GoalCreate,
    GoalUpdate,
    GoalResponse,
    GoalMilestone,
    GoalCategory,
    GoalStatus
)
from app.models.notification import (
    NotificationBase,
    NotificationCreate,
    NotificationResponse,
    NotificationUpdate,
    NotificationFilter,
    NotificationStats,
    BulkNotificationUpdate,
    NotificationType,
    NotificationPriority
)
from app.models.insight import (
    InsightCard,
    CategoryBreakdown,
    CategorySummary,
    SpendingOverview,
    MonthlyComparison,
    InsightsDashboard,
    InsightCache,
    InsightType,
    TrendDirection
)
from app.models.utility import (
    DebtEntry,
    DebtResponse,
    DebtUpdate,
    NetWorthData,
    ReportRequest,
    ReportResponse,
    ReceiptScanResponse,
    ExportRequest,
    BillReminder,
    BillReminderResponse,
    DebtType,
    DebtStatus,
    ReportType,
    ReportFormat
)

__all__ = [
    # Common models
    "RecurringFrequency",
    # User models
    "UserBase",
    "UserCreate",
    "UserResponse",
    "UserUpdate",
    "UserPreferences",
    "UserPreferencesUpdate",
    "UserStats",
    # Transaction models
    "TransactionBase",
    "TransactionCreate",
    "TransactionResponse",
    "TransactionUpdate",
    "TransactionFilter",
    "TransactionSummary",
    "PaginatedTransactions",
    "TransactionType",
    "TransactionCategory",
    # Goal models
    "GoalBase",
    "GoalCreate",
    "GoalUpdate",
    "GoalResponse",
    "GoalMilestone",
    "GoalCategory",
    "GoalStatus",
    # Notification models
    "NotificationBase",
    "NotificationCreate",
    "NotificationResponse",
    "NotificationUpdate",
    "NotificationFilter",
    "NotificationStats",
    "BulkNotificationUpdate",
    "NotificationType",
    "NotificationPriority",
    # Insight models
    "InsightCard",
    "CategoryBreakdown",
    "CategorySummary",
    "SpendingOverview",
    "MonthlyComparison",
    "InsightsDashboard",
    "InsightCache",
    "InsightType",
    "TrendDirection",
    # Utility models
    "DebtEntry",
    "DebtResponse",
    "DebtUpdate",
    "NetWorthData",
    "ReportRequest",
    "ReportResponse",
    "ReceiptScanResponse",
    "ExportRequest",
    "BillReminder",
    "BillReminderResponse",
    "DebtType",
    "DebtStatus",
    "ReportType",
    "ReportFormat",
]
