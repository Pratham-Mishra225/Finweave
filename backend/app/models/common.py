"""Common Pydantic models and enums shared across modules."""
from enum import Enum


class RecurringFrequency(str, Enum):
    """Recurring frequency enum for transactions, bills, and reminders."""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
