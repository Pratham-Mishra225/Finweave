"""Application constants."""

# File upload limits
MAX_RECEIPT_FILE_SIZE_MB = 10
MAX_RECEIPT_FILE_SIZE_BYTES = MAX_RECEIPT_FILE_SIZE_MB * 1024 * 1024

# Allowed MIME types for receipt upload
ALLOWED_RECEIPT_MIME_TYPES = frozenset(["image/jpeg", "image/png", "image/jpg"])

# Cache TTL
INSIGHTS_CACHE_TTL_HOURS = 6

# API limits
MAX_TRANSACTIONS_PER_QUERY = 100
MAX_GOALS_PER_USER_DISPLAY = 4
MAX_CATEGORIES_DISPLAY = 5

# PDF export limits
MAX_TRANSACTIONS_IN_PDF = 100
