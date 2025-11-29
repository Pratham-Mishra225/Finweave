"""Home page service for dashboard data aggregation."""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from google.cloud import firestore

from app.config.firebase import get_firestore_db
from app.config.mongodb import get_database
from app.models.transaction import TransactionResponse, TransactionType
from app.models.insight import InsightCard

logger = logging.getLogger(__name__)


class HomeService:
    """Service for home dashboard data management."""
    
    @staticmethod
    async def get_user_balance(user_id: str) -> float:
        """Get user's current balance - tries Firestore first, falls back to MongoDB.
        
        Args:
            user_id: Firebase user ID
            
        Returns:
            Current balance
        """
        # Try Firestore first
        try:
            db = get_firestore_db()
            user_ref = db.collection("users").document(user_id)
            user_doc = user_ref.get()
            
            if user_doc.exists:
                user_data = user_doc.to_dict()
                balance = user_data.get("balance")
                if balance is not None:
                    return balance
        except Exception as e:
            logger.warning(f"Firestore balance fetch failed, falling back to MongoDB: {e}")
        
        # Fallback: Calculate from MongoDB
        try:
            mongodb = get_database()
            pipeline = [
                {"$match": {"user_id": user_id}},
                {
                    "$group": {
                        "_id": "$type",
                        "total": {"$sum": "$amount"}
                    }
                }
            ]
            
            results = await mongodb.transactions.aggregate(pipeline).to_list(None)
            
            total_income = 0.0
            total_expenses = 0.0
            
            for result in results:
                if result["_id"] == TransactionType.INCOME.value:
                    total_income = result["total"]
                elif result["_id"] == TransactionType.EXPENSE.value:
                    total_expenses = result["total"]
            
            return total_income - total_expenses
        except Exception as e:
            logger.error(f"Error calculating balance from MongoDB: {e}")
            return 0.0
    
    @staticmethod
    async def get_recent_transactions(user_id: str, limit: int = 4) -> List[Dict[str, Any]]:
        """Get recent transactions - tries Firestore cache first, falls back to MongoDB.
        
        Args:
            user_id: Firebase user ID
            limit: Number of transactions to return (default: 4)
            
        Returns:
            List of recent transaction dictionaries
        """
        # Try Firestore cache first
        try:
            db = get_firestore_db()
            
            # First try with ordering by date
            try:
                transactions_ref = (
                    db.collection("users")
                    .document(user_id)
                    .collection("transactions_cache")
                    .order_by("date", direction=firestore.Query.DESCENDING)
                    .limit(limit)
                )
                
                transactions = []
                for doc in transactions_ref.stream():
                    transaction_data = doc.to_dict()
                    transaction_data["id"] = doc.id
                    transactions.append(transaction_data)
                
                if transactions:
                    return transactions
            except Exception as order_error:
                logger.warning(f"Ordered Firestore query failed: {order_error}")
            
            # Try simple fetch without ordering
            try:
                transactions_ref = (
                    db.collection("users")
                    .document(user_id)
                    .collection("transactions_cache")
                    .limit(limit)
                )
                
                transactions = []
                for doc in transactions_ref.stream():
                    transaction_data = doc.to_dict()
                    transaction_data["id"] = doc.id
                    transactions.append(transaction_data)
                
                if transactions:
                    return transactions
            except Exception as simple_error:
                logger.warning(f"Simple Firestore query failed: {simple_error}")
                
        except Exception as e:
            logger.warning(f"Firestore cache unavailable, falling back to MongoDB: {e}")
        
        # Fallback: Get from MongoDB directly
        try:
            mongodb = get_database()
            cursor = mongodb.transactions.find({"user_id": user_id}).sort("date", -1).limit(limit)
            
            transactions = []
            async for doc in cursor:
                transaction_data = {
                    "id": str(doc["_id"]),
                    "name": doc["name"],
                    "amount": doc["amount"],
                    "type": doc["type"],
                    "category": doc["category"],
                    "description": doc.get("description"),
                    "date": doc["date"].isoformat() if hasattr(doc["date"], 'isoformat') else doc["date"],
                    "recurring": doc.get("recurring", False),
                    "created_at": doc["created_at"].isoformat() if hasattr(doc.get("created_at"), 'isoformat') else doc.get("created_at")
                }
                transactions.append(transaction_data)
            
            return transactions
        except Exception as e:
            logger.error(f"Error fetching recent transactions from MongoDB: {e}")
            return []
    
    @staticmethod
    async def get_spending_overview(user_id: str, days: int = 30) -> Dict[str, Any]:
        """Get spending overview chart data for the last N days.
        
        Aggregates transactions by week for the specified period.
        Caches result in Firestore for 1 hour.
        
        Args:
            user_id: Firebase user ID
            days: Number of days to analyze (default: 30)
            
        Returns:
            Dictionary with labels and spending data
        """
        try:
            # Check cache first
            cached_data = await HomeService._get_cached_spending_overview(user_id)
            if cached_data:
                logger.info(f"Using cached spending overview for user {user_id}")
                return cached_data
            
            # Calculate spending from MongoDB
            start_date = datetime.now() - timedelta(days=days)
            
            db = get_database()
            
            # Aggregate by week
            pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "date": {"$gte": start_date},
                        "type": "expense"
                    }
                },
                {
                    "$group": {
                        "_id": {
                            "$week": "$date"
                        },
                        "total": {"$sum": "$amount"},
                        "week_start": {"$min": "$date"}
                    }
                },
                {
                    "$sort": {"week_start": -1}
                },
                {
                    "$limit": 4
                }
            ]
            
            cursor = db.transactions.aggregate(pipeline)
            results = await cursor.to_list(length=10)
            # Ensure results are in chronological order for charting
            results = list(reversed(results))
            
            # Format data for chart
            labels = []
            data = []
            total_spend = 0.0
            
            for week_data in results:
                week_start = week_data.get("week_start")
                if isinstance(week_start, datetime):
                    label = week_start.strftime("Week of %b %d")
                else:
                    label = f"Week {len(labels) + 1}"
                labels.append(label)
                amount = week_data.get("total", 0)
                data.append(amount)
                total_spend += amount
            
            # If less than 4 weeks, pad with zeros
            while len(labels) < 4:
                labels.append(f"Week {len(labels) + 1}")
                data.append(0.0)
            
            overview_data = {
                "labels": labels,
                "data": data,
                "total": total_spend,
                "period": "month"
            }
            
            # Cache the result
            await HomeService._cache_spending_overview(user_id, overview_data)
            
            return overview_data
            
        except Exception as e:
            logger.error(f"Error calculating spending overview: {e}")
            # Return default data
            return {
                "labels": ["Week 1", "Week 2", "Week 3", "Week 4"],
                "data": [0, 0, 0, 0],
                "total": 0.0,
                "period": "month"
            }
    
    @staticmethod
    async def _get_cached_spending_overview(user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached spending overview from Firestore.
        
        Args:
            user_id: Firebase user ID
            
        Returns:
            Cached data if exists and not expired, None otherwise
        """
        try:
            db = get_firestore_db()
            cache_ref = db.collection("spending_cache").document(user_id)
            cache_doc = cache_ref.get()
            
            if not cache_doc.exists:
                return None
            
            cache_data = cache_doc.to_dict()
            cached_at = cache_data.get("cached_at")
            
            # Ensure cached_at is a Python datetime and handle timezone awareness
            if cached_at:
                # If cached_at is a Firestore Timestamp, convert to datetime
                if hasattr(cached_at, "to_datetime"):
                    cached_at = cached_at.to_datetime()
                # If cached_at is a string, try to parse it (optional, if needed)
                # if isinstance(cached_at, str):
                #     cached_at = datetime.fromisoformat(cached_at)
                # If cached_at is aware, make it naive
                if isinstance(cached_at, datetime):
                    if cached_at.tzinfo is not None:
                        cached_at = cached_at.replace(tzinfo=None)
                    # Now check cache validity
                    if (datetime.now() - cached_at).total_seconds() < 3600:
                        return cache_data.get("overview_data")
            
            return None
        except Exception as e:
            logger.warning(f"Firestore cache unavailable (will calculate fresh): {e}")
            return None
    
    @staticmethod
    async def _cache_spending_overview(user_id: str, overview_data: Dict[str, Any]) -> None:
        """Cache spending overview in Firestore (non-blocking, fails silently).
        
        Args:
            user_id: Firebase user ID
            overview_data: Data to cache
        """
        try:
            db = get_firestore_db()
            cache_ref = db.collection("spending_cache").document(user_id)
            cache_ref.set({
                "overview_data": overview_data,
                "cached_at": datetime.now()
            })
        except Exception as e:
            # Non-critical - just log and continue
            logger.warning(f"Could not cache spending overview (Firestore may be unavailable): {e}")

    @staticmethod
    def invalidate_spending_overview_cache(user_id: str) -> None:
        """Remove cached spending overview so next fetch recomputes data."""
        try:
            db = get_firestore_db()
            cache_ref = db.collection("spending_cache").document(user_id)
            cache_ref.delete()
            logger.info(f"Invalidated spending cache for user {user_id}")
        except Exception as e:
            logger.warning(f"Could not invalidate spending cache for user {user_id}: {e}")
    
    @staticmethod
    async def get_ai_insight_alert(user_id: str) -> Optional[Dict[str, Any]]:
        """Get AI-generated insight alert for the dashboard.
        
        Fetches the most recent urgent or warning insight from Firestore.
        Falls back to a default insight if Firestore is unavailable.
        
        Args:
            user_id: Firebase user ID
            
        Returns:
            Insight alert dictionary
        """
        default_insight = {
            "id": "default",
            "type": "forecast",
            "title": "AI Financial Insight — Forecast",
            "message": "Track your spending to get personalized insights and forecasts!",
            "severity": "info",
            "icon": "checkmark-circle-outline"
        }
        
        try:
            db = get_firestore_db()
            
            # Try to get insights - use simpler query to avoid index requirement
            try:
                insights_ref = (
                    db.collection("users")
                    .document(user_id)
                    .collection("insights")
                    .order_by("created_at", direction=firestore.Query.DESCENDING)
                    .limit(10)
                )
                
                insights = list(insights_ref.stream())
                
                # Filter for urgent/warning insights from last 7 days
                seven_days_ago = datetime.now() - timedelta(days=7)
                for insight_doc in insights:
                    insight_data = insight_doc.to_dict()
                    created_at = insight_data.get("created_at")
                    # Handle Firestore timestamp
                    if hasattr(created_at, 'replace'):
                        created_at = created_at.replace(tzinfo=None)
                    if created_at and created_at < seven_days_ago:
                        continue
                    if insight_data.get("severity") in ["urgent", "warning"]:
                        insight_data["id"] = insight_doc.id
                        return insight_data
                        
                # No urgent/warning insights found - return positive default
                return default_insight
            except Exception as query_error:
                logger.warning(f"Insights query failed (Firestore may be unavailable): {query_error}")
                return default_insight
            
        except Exception as e:
            logger.warning(f"Could not fetch AI insight (Firestore may be unavailable): {e}")
            return default_insight
    
    @staticmethod
    async def get_dashboard_data(user_id: str) -> Dict[str, Any]:
        """Get complete dashboard data for home page.
        
        Aggregates:
        - Current balance
        - Recent 4 transactions
        - AI insight alert
        - 30-day spending overview
        
        Args:
            user_id: Firebase user ID
            
        Returns:
            Complete dashboard data dictionary
        """
        try:
            # Fetch all data in parallel
            balance = await HomeService.get_user_balance(user_id)
            recent_transactions = await HomeService.get_recent_transactions(user_id, limit=4)
            spending_overview = await HomeService.get_spending_overview(user_id, days=30)
            ai_insight = await HomeService.get_ai_insight_alert(user_id)
            
            return {
                "balance": balance,
                "recent_transactions": recent_transactions,
                "spending_overview": spending_overview,
                "ai_insight": ai_insight
            }
        except Exception as e:
            logger.error(f"Error fetching dashboard data: {e}")
            raise


# Create singleton instance
home_service = HomeService()
