"""Insights service for analytics and AI-powered financial insights."""
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

from app.config.mongodb import get_database
from app.config.firebase import get_firestore_db
from app.models.insight import (
    InsightCard,
    CategoryBreakdown,
    CategorySummary,
    MonthlyComparison,
    InsightType,
    TrendDirection,
)
from app.models.transaction import TransactionType
from app.services.ai.gemini_service import get_gemini_service

logger = logging.getLogger(__name__)

# Category colors for charts
CATEGORY_COLORS = {
    "Food": "#FF6B6B",
    "Bills": "#4ECDC4",
    "Shopping": "#45B7D1",
    "Travel": "#96CEB4",
    "Subscriptions": "#FFEAA7",
    "Salary": "#74B9FF",
    "Freelance": "#A29BFE",
    "Investment": "#00B894",
    "Others": "#636E72",
}


class InsightsService:
    """Service for generating financial insights and analytics."""

    def __init__(self):
        self.mongodb = get_database()
        self.firestore_db = get_firestore_db()
        self.transactions_collection = self.mongodb["transactions"]
        self.insights_cache_collection = self.mongodb["insights_cache"]
        self.ai_insights_cache_collection = self.mongodb["ai_insights_cache"]

    async def get_insight_cards(self, user_id: str) -> List[InsightCard]:
        """
        Generate AI insight cards based on user's financial data.
        
        Args:
            user_id: Firebase user ID
            
        Returns:
            List of 4 insight cards
        """
        try:
            now = datetime.utcnow()
            start_of_month = datetime(now.year, now.month, 1)
            
            # Previous month range
            if now.month == 1:
                prev_month_start = datetime(now.year - 1, 12, 1)
                prev_month_end = datetime(now.year, 1, 1)
            else:
                prev_month_start = datetime(now.year, now.month - 1, 1)
                prev_month_end = start_of_month

            # Get current month data
            current_data = await self._get_month_spending_by_category(
                user_id, start_of_month, now
            )
            
            # Get previous month data
            previous_data = await self._get_month_spending_by_category(
                user_id, prev_month_start, prev_month_end
            )

            # Get savings comparison
            savings_comparison = await self._calculate_savings_comparison(
                user_id, start_of_month, prev_month_start, prev_month_end
            )

            # Generate insight cards
            cards = []
            
            # Card 1: Overspending forecast
            overspending_card = await self._generate_overspending_insight(
                user_id, current_data, previous_data
            )
            if overspending_card:
                cards.append(overspending_card)
            
            # Card 2: Savings trend
            savings_card = self._generate_savings_insight(savings_comparison)
            if savings_card:
                cards.append(savings_card)
            
            # Card 3: Subscription alert
            subscriptions_card = await self._generate_subscriptions_insight(
                user_id, current_data
            )
            if subscriptions_card:
                cards.append(subscriptions_card)
            
            # Card 4: Top category trend
            category_card = self._generate_category_trend_insight(
                current_data, previous_data
            )
            if category_card:
                cards.append(category_card)

            # Fill with default cards if less than 4
            while len(cards) < 4:
                cards.append(self._create_default_insight_card(len(cards) + 1))

            return cards[:4]

        except Exception as e:
            logger.error(f"Error generating insight cards for user {user_id}: {e}")
            return self._create_default_insight_cards()

    async def get_category_breakdown(
        self, user_id: str, limit: int = 5
    ) -> List[CategoryBreakdown]:
        """
        Get category breakdown for bar chart visualization.
        
        Args:
            user_id: Firebase user ID
            limit: Number of categories to return (default 5)
            
        Returns:
            List of CategoryBreakdown items
        """
        try:
            now = datetime.utcnow()
            start_of_month = datetime(now.year, now.month, 1)
            
            # Previous month for trend comparison
            if now.month == 1:
                prev_month_start = datetime(now.year - 1, 12, 1)
                prev_month_end = datetime(now.year, 1, 1)
            else:
                prev_month_start = datetime(now.year, now.month - 1, 1)
                prev_month_end = start_of_month

            # Current month aggregation
            current_pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "type": TransactionType.EXPENSE.value,
                        "date": {"$gte": start_of_month, "$lte": now}
                    }
                },
                {
                    "$group": {
                        "_id": "$category",
                        "amount": {"$sum": "$amount"},
                        "count": {"$sum": 1}
                    }
                },
                {"$sort": {"amount": -1}},
                {"$limit": limit}
            ]
            
            current_results = await self.transactions_collection.aggregate(
                current_pipeline
            ).to_list(None)

            # Previous month aggregation for trend
            prev_pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "type": TransactionType.EXPENSE.value,
                        "date": {"$gte": prev_month_start, "$lt": prev_month_end}
                    }
                },
                {
                    "$group": {
                        "_id": "$category",
                        "amount": {"$sum": "$amount"}
                    }
                }
            ]
            
            prev_results = await self.transactions_collection.aggregate(
                prev_pipeline
            ).to_list(None)
            
            prev_amounts = {r["_id"]: r["amount"] for r in prev_results}

            # Calculate total for percentages
            total_amount = sum(r["amount"] for r in current_results) or 1

            breakdown = []
            for result in current_results:
                category = result["_id"]
                current_amount = result["amount"]
                prev_amount = prev_amounts.get(category, 0)
                
                # Determine trend
                if prev_amount == 0:
                    trend = TrendDirection.UP if current_amount > 0 else TrendDirection.STABLE
                elif current_amount > prev_amount:
                    trend = TrendDirection.UP
                elif current_amount < prev_amount:
                    trend = TrendDirection.DOWN
                else:
                    trend = TrendDirection.STABLE

                breakdown.append(CategoryBreakdown(
                    category=category,
                    amount=round(current_amount, 2),
                    percentage=round((current_amount / total_amount) * 100, 1),
                    transaction_count=result["count"],
                    trend=trend,
                    color=CATEGORY_COLORS.get(category, "#636E72")
                ))

            return breakdown

        except Exception as e:
            logger.error(f"Error getting category breakdown for user {user_id}: {e}")
            return []

    async def get_category_summary(
        self, user_id: str, limit: int = 3
    ) -> List[CategorySummary]:
        """
        Get category summary cards with trends.
        
        Args:
            user_id: Firebase user ID
            limit: Number of categories to return (default 3)
            
        Returns:
            List of CategorySummary items
        """
        try:
            now = datetime.utcnow()
            start_of_month = datetime(now.year, now.month, 1)
            
            # Previous month range
            if now.month == 1:
                prev_month_start = datetime(now.year - 1, 12, 1)
                prev_month_end = datetime(now.year, 1, 1)
            else:
                prev_month_start = datetime(now.year, now.month - 1, 1)
                prev_month_end = start_of_month

            # Aggregation pipeline for current month with top transaction
            current_pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "type": TransactionType.EXPENSE.value,
                        "date": {"$gte": start_of_month, "$lte": now}
                    }
                },
                {"$sort": {"amount": -1}},
                {
                    "$group": {
                        "_id": "$category",
                        "amount": {"$sum": "$amount"},
                        "count": {"$sum": 1},
                        "top_transaction": {"$first": "$name"}
                    }
                },
                {"$sort": {"amount": -1}},
                {"$limit": limit}
            ]

            current_results = await self.transactions_collection.aggregate(
                current_pipeline
            ).to_list(None)

            # Previous month aggregation
            prev_pipeline = [
                {
                    "$match": {
                        "user_id": user_id,
                        "type": TransactionType.EXPENSE.value,
                        "date": {"$gte": prev_month_start, "$lt": prev_month_end}
                    }
                },
                {
                    "$group": {
                        "_id": "$category",
                        "amount": {"$sum": "$amount"}
                    }
                }
            ]

            prev_results = await self.transactions_collection.aggregate(
                prev_pipeline
            ).to_list(None)
            
            prev_amounts = {r["_id"]: r["amount"] for r in prev_results}

            summaries = []
            for result in current_results:
                category = result["_id"]
                current_amount = result["amount"]
                prev_amount = prev_amounts.get(category, 0)
                
                # Calculate change percentage
                if prev_amount == 0:
                    change_percentage = 100.0 if current_amount > 0 else 0.0
                else:
                    change_percentage = ((current_amount - prev_amount) / prev_amount) * 100

                # Determine trend
                if change_percentage > 5:
                    trend = TrendDirection.UP
                elif change_percentage < -5:
                    trend = TrendDirection.DOWN
                else:
                    trend = TrendDirection.STABLE

                summaries.append(CategorySummary(
                    category=category,
                    current_month_amount=round(current_amount, 2),
                    previous_month_amount=round(prev_amount, 2),
                    change_percentage=round(change_percentage, 1),
                    trend=trend,
                    top_transaction=result.get("top_transaction"),
                    transaction_count=result["count"]
                ))

            return summaries

        except Exception as e:
            logger.error(f"Error getting category summary for user {user_id}: {e}")
            return []

    async def get_monthly_comparison(self, user_id: str) -> MonthlyComparison:
        """
        Get month-over-month expense comparison.
        
        Args:
            user_id: Firebase user ID
            
        Returns:
            MonthlyComparison data
        """
        try:
            now = datetime.utcnow()
            start_of_month = datetime(now.year, now.month, 1)
            
            # Previous month range
            if now.month == 1:
                prev_month_start = datetime(now.year - 1, 12, 1)
                prev_month_end = datetime(now.year, 1, 1)
                prev_month_name = "December"
            else:
                prev_month_start = datetime(now.year, now.month - 1, 1)
                prev_month_end = start_of_month
                prev_month_name = prev_month_start.strftime("%B")

            current_month_name = now.strftime("%B")

            # Get current month expenses
            current_expenses = await self._get_total_expenses(
                user_id, start_of_month, now
            )
            
            # Get previous month expenses
            previous_expenses = await self._get_total_expenses(
                user_id, prev_month_start, prev_month_end
            )

            # Calculate change
            change_amount = current_expenses - previous_expenses
            if previous_expenses == 0:
                change_percentage = 100.0 if current_expenses > 0 else 0.0
            else:
                change_percentage = (change_amount / previous_expenses) * 100

            # Determine trend
            if change_percentage > 5:
                trend = TrendDirection.UP
            elif change_percentage < -5:
                trend = TrendDirection.DOWN
            else:
                trend = TrendDirection.STABLE

            return MonthlyComparison(
                current_month=current_month_name,
                previous_month=prev_month_name,
                current_expenses=round(current_expenses, 2),
                previous_expenses=round(previous_expenses, 2),
                change_amount=round(change_amount, 2),
                change_percentage=round(change_percentage, 1),
                trend=trend
            )

        except Exception as e:
            logger.error(f"Error getting monthly comparison for user {user_id}: {e}")
            return MonthlyComparison(
                current_month=datetime.utcnow().strftime("%B"),
                previous_month="Previous",
                current_expenses=0.0,
                previous_expenses=0.0,
                change_amount=0.0,
                change_percentage=0.0,
                trend=TrendDirection.STABLE
            )

    async def cache_insights(
        self, user_id: str, insights_data: Dict[str, Any]
    ) -> None:
        """
        Cache insights data in MongoDB with TTL.
        
        Args:
            user_id: Firebase user ID
            insights_data: Insights data to cache
        """
        from app.config.constants import INSIGHTS_CACHE_TTL_HOURS
        
        try:
            now = datetime.utcnow()
            month_key = now.strftime("%Y-%m")
            
            cache_doc = {
                "user_id": user_id,
                "month": month_key,
                "category_breakdown": insights_data.get("category_breakdown", []),
                "trends": insights_data.get("trends", {}),
                "spending_patterns": insights_data.get("spending_patterns", {}),
                "generated_at": now,
                "expires_at": now + timedelta(hours=INSIGHTS_CACHE_TTL_HOURS)
            }

            await self.insights_cache_collection.update_one(
                {"user_id": user_id, "month": month_key},
                {"$set": cache_doc},
                upsert=True
            )

        except Exception as e:
            logger.error(f"Error caching insights for user {user_id}: {e}")

    async def get_cached_insights(
        self, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached insights if still valid.
        
        Args:
            user_id: Firebase user ID
            
        Returns:
            Cached insights data or None if expired/not found
        """
        try:
            now = datetime.utcnow()
            month_key = now.strftime("%Y-%m")
            
            cache = await self.insights_cache_collection.find_one({
                "user_id": user_id,
                "month": month_key,
                "expires_at": {"$gt": now}
            })

            return cache

        except Exception as e:
            logger.error(f"Error getting cached insights for user {user_id}: {e}")
            return None

    async def cache_ai_dashboard(
        self, user_id: str, dashboard_data: Dict[str, Any]
    ) -> None:
        """Persist the latest AI-generated dashboard snapshot."""
        try:
            doc = {**dashboard_data}
            doc.pop("from_cache", None)
            doc["user_id"] = user_id
            doc.setdefault("generated_at", datetime.utcnow())

            await self.ai_insights_cache_collection.update_one(
                {"user_id": user_id},
                {"$set": doc},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error caching AI insights for user {user_id}: {e}")

    async def get_cached_ai_dashboard(
        self, user_id: str
    ) -> Optional[Dict[str, Any]]:
        """Return the cached AI dashboard snapshot if available."""
        try:
            cached = await self.ai_insights_cache_collection.find_one({
                "user_id": user_id
            })
            if cached:
                cached.pop("_id", None)
                cached["from_cache"] = True
            return cached
        except Exception as e:
            logger.error(f"Error getting cached AI insights for user {user_id}: {e}")
            return None

    # Private helper methods
    
    async def _get_month_spending_by_category(
        self, user_id: str, start_date: datetime, end_date: datetime
    ) -> Dict[str, float]:
        """Get spending by category for a date range."""
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "type": TransactionType.EXPENSE.value,
                    "date": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": "$category",
                    "total": {"$sum": "$amount"}
                }
            }
        ]
        
        results = await self.transactions_collection.aggregate(pipeline).to_list(None)
        return {r["_id"]: r["total"] for r in results}

    async def _get_total_expenses(
        self, user_id: str, start_date: datetime, end_date: datetime
    ) -> float:
        """Get total expenses for a date range."""
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "type": TransactionType.EXPENSE.value,
                    "date": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": "$amount"}
                }
            }
        ]
        
        results = await self.transactions_collection.aggregate(pipeline).to_list(None)
        return results[0]["total"] if results else 0.0

    async def _calculate_savings_comparison(
        self,
        user_id: str,
        current_start: datetime,
        prev_start: datetime,
        prev_end: datetime
    ) -> Dict[str, Any]:
        """Calculate savings comparison between months."""
        now = datetime.utcnow()
        
        # Current month: income - expenses
        current_income = await self._get_total_income(user_id, current_start, now)
        current_expenses = await self._get_total_expenses(user_id, current_start, now)
        current_savings = current_income - current_expenses

        # Previous month
        prev_income = await self._get_total_income(user_id, prev_start, prev_end)
        prev_expenses = await self._get_total_expenses(user_id, prev_start, prev_end)
        prev_savings = prev_income - prev_expenses

        # Calculate change
        if prev_savings == 0:
            change_percentage = 100.0 if current_savings > 0 else 0.0
        else:
            change_percentage = ((current_savings - prev_savings) / abs(prev_savings)) * 100

        return {
            "current_savings": current_savings,
            "previous_savings": prev_savings,
            "change_percentage": change_percentage,
            "improved": current_savings > prev_savings
        }

    async def _get_total_income(
        self, user_id: str, start_date: datetime, end_date: datetime
    ) -> float:
        """Get total income for a date range."""
        pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "type": TransactionType.INCOME.value,
                    "date": {"$gte": start_date, "$lte": end_date}
                }
            },
            {
                "$group": {
                    "_id": None,
                    "total": {"$sum": "$amount"}
                }
            }
        ]
        
        results = await self.transactions_collection.aggregate(pipeline).to_list(None)
        return results[0]["total"] if results else 0.0

    async def _generate_overspending_insight(
        self,
        user_id: str,
        current_data: Dict[str, float],
        previous_data: Dict[str, float]
    ) -> Optional[InsightCard]:
        """Generate overspending forecast insight."""
        for category, current_amount in current_data.items():
            prev_amount = previous_data.get(category, 0)
            if prev_amount > 0 and current_amount > prev_amount:
                increase_pct = ((current_amount - prev_amount) / prev_amount) * 100
                if increase_pct >= 15:
                    return InsightCard(
                        id=f"overspend_{category.lower()}",
                        type=InsightType.BUDGET_WARNING,
                        title="Overspending Forecast",
                        description=f"You're projected to exceed your {category} budget this month by {int(increase_pct)}%.",
                        icon="warning",
                        severity="warning",
                        actionable=True,
                        action_text="Review Spending",
                        created_at=datetime.utcnow()
                    )
        return None

    def _generate_savings_insight(
        self, savings_data: Dict[str, Any]
    ) -> Optional[InsightCard]:
        """Generate savings trend insight."""
        change_pct = savings_data["change_percentage"]
        improved = savings_data["improved"]
        
        if improved and change_pct > 0:
            return InsightCard(
                id="savings_trend",
                type=InsightType.SAVINGS_TIP,
                title="Savings Trend",
                description=f"You saved {abs(int(change_pct))}% more compared to last month.",
                icon="trending-up",
                severity="success",
                actionable=False,
                created_at=datetime.utcnow()
            )
        elif not improved and change_pct < -10:
            return InsightCard(
                id="savings_trend",
                type=InsightType.SAVINGS_TIP,
                title="Savings Alert",
                description=f"Your savings decreased by {abs(int(change_pct))}% this month.",
                icon="trending-down",
                severity="warning",
                actionable=True,
                action_text="Review Expenses",
                created_at=datetime.utcnow()
            )
        return None

    async def _generate_subscriptions_insight(
        self, user_id: str, current_data: Dict[str, float]
    ) -> Optional[InsightCard]:
        """Generate subscription alert insight."""
        now = datetime.utcnow()
        start_of_month = datetime(now.year, now.month, 1)
        
        # Count recurring transactions
        recurring_count = await self.transactions_collection.count_documents({
            "user_id": user_id,
            "recurring": True,
            "date": {"$gte": start_of_month}
        })
        
        subscriptions_amount = current_data.get("Subscriptions", 0)
        
        if recurring_count >= 2 or subscriptions_amount > 0:
            return InsightCard(
                id="subscriptions_alert",
                type=InsightType.SPENDING_ALERT,
                title="Subscription Alert",
                description=f"{max(recurring_count, 1)} recurring payments detected. Review your subscriptions.",
                icon="refresh",
                severity="info",
                actionable=True,
                action_text="View Subscriptions",
                created_at=datetime.utcnow()
            )
        return None

    def _generate_category_trend_insight(
        self,
        current_data: Dict[str, float],
        previous_data: Dict[str, float]
    ) -> Optional[InsightCard]:
        """Generate top category trend insight."""
        # Find category with biggest decrease
        biggest_decrease = None
        biggest_decrease_pct = 0
        
        for category, prev_amount in previous_data.items():
            if prev_amount > 0:
                current_amount = current_data.get(category, 0)
                if current_amount < prev_amount:
                    decrease_pct = ((prev_amount - current_amount) / prev_amount) * 100
                    if decrease_pct > biggest_decrease_pct:
                        biggest_decrease_pct = decrease_pct
                        biggest_decrease = category
        
        if biggest_decrease and biggest_decrease_pct >= 20:
            # Map categories to icons
            category_icons = {
                "Food": "restaurant",
                "Bills": "document-text",
                "Shopping": "cart",
                "Travel": "airplane",
                "Subscriptions": "refresh",
                "Others": "ellipsis-horizontal"
            }
            
            return InsightCard(
                id=f"trend_{biggest_decrease.lower()}",
                type=InsightType.TREND_ANALYSIS,
                title=f"{biggest_decrease} Spending",
                description=f"{biggest_decrease} expenses decreased by {int(biggest_decrease_pct)}% this month.",
                icon=category_icons.get(biggest_decrease, "analytics"),
                severity="success",
                actionable=False,
                created_at=datetime.utcnow()
            )
        return None

    def _create_default_insight_card(self, index: int) -> InsightCard:
        """Create a default insight card when no specific insight available."""
        defaults = [
            {
                "id": "welcome",
                "type": InsightType.FINANCIAL_HEALTH,
                "title": "Track Your Spending",
                "description": "Add more transactions to get personalized insights.",
                "icon": "analytics",
                "severity": "info"
            },
            {
                "id": "tip_1",
                "type": InsightType.SAVINGS_TIP,
                "title": "Set a Goal",
                "description": "Create savings goals to track your progress.",
                "icon": "flag",
                "severity": "info"
            },
            {
                "id": "tip_2",
                "type": InsightType.FINANCIAL_HEALTH,
                "title": "Review Regularly",
                "description": "Check your finances weekly for better control.",
                "icon": "calendar",
                "severity": "info"
            },
            {
                "id": "tip_3",
                "type": InsightType.SAVINGS_TIP,
                "title": "Budget Wisely",
                "description": "Use the 50/30/20 rule for better budgeting.",
                "icon": "pie-chart",
                "severity": "info"
            }
        ]
        
        default = defaults[(index - 1) % len(defaults)]
        return InsightCard(
            id=default["id"],
            type=default["type"],
            title=default["title"],
            description=default["description"],
            icon=default["icon"],
            severity=default["severity"],
            actionable=False,
            created_at=datetime.utcnow()
        )

    def _create_default_insight_cards(self) -> List[InsightCard]:
        """Create default insight cards for new users or errors."""
        return [self._create_default_insight_card(i) for i in range(1, 5)]

    async def get_ai_insights(self, user_id: str) -> Dict[str, Any]:
        """
        Generate AI-powered insights using Gemini.
        Returns the new segregated format with all AI-generated content.
        """
        try:
            gemini_service = get_gemini_service()
            
            # Get recent transactions (last 60 days)
            now = datetime.utcnow()
            sixty_days_ago = now - timedelta(days=60)
            
            cursor = self.transactions_collection.find({
                "user_id": user_id,
                "date": {"$gte": sixty_days_ago}
            }).sort("date", -1).limit(100)
            
            transactions = []
            async for doc in cursor:
                transactions.append({
                    "name": doc.get("name"),
                    "amount": doc.get("amount"),
                    "type": doc.get("type"),
                    "category": doc.get("category"),
                    "date": str(doc.get("date"))
                })
            
            # Get user goals from Firestore
            goals = []
            try:
                goals_ref = self.firestore_db.collection("users").document(user_id).collection("goals")
                goals_docs = goals_ref.stream()
                for doc in goals_docs:
                    goal_data = doc.to_dict()
                    goal_data["id"] = doc.id
                    goals.append(goal_data)
            except Exception as e:
                logger.warning(f"Could not fetch goals: {e}")
            
            # Get user stats (balance)
            user_stats = {"balance": 0}
            try:
                user_doc = self.firestore_db.collection("users").document(user_id).get()
                if user_doc.exists:
                    user_stats["balance"] = user_doc.to_dict().get("balance", 0)
            except Exception as e:
                logger.warning(f"Could not fetch user stats: {e}")
            
            # Get trend data
            current_spending, previous_spending = await self._get_trend_data(user_id)
            
            # Generate full AI insights using new method
            ai_insights = await gemini_service.generate_full_ai_insights(
                transactions, goals, user_stats, current_spending, previous_spending
            )
            
            return ai_insights
            
        except Exception as e:
            logger.error(f"Error generating AI insights: {e}")
            return {
                "quick_stats": {"items": []},
                "spending": {"title": "Kahan Gaya Paisa?", "categories": [], "total": "₹0"},
                "goals": {"title": "Goals", "items": [], "empty": "Koi goal nahi? Banao!"},
                "alerts": [],
                "ai_summary": {"emoji": "💡", "text": "Track karte raho!", "ai": False},
                "ai_insights": [],
                "trend_analysis": {"emoji": "➡️", "title": "No data", "text": "Add transactions", "direction": "stable"},
                "ai_generated": False,
                "generated_at": datetime.utcnow().isoformat()
            }

    async def get_ai_dashboard(
        self, user_id: str, force_refresh: bool = False
    ) -> Dict[str, Any]:
        """Return cached AI dashboard or regenerate it when requested."""
        if not force_refresh:
            cached = await self.get_cached_ai_dashboard(user_id)
            if cached:
                return cached

        # Get AI insights (new format)
        ai_data = await self.get_ai_insights(user_id)
        
        # Get category breakdown for charts
        category_breakdown = await self.get_category_breakdown(user_id)

        dashboard = {
            **ai_data,
            "category_breakdown": [breakdown_item.model_dump() for breakdown_item in category_breakdown],
            "from_cache": False
        }

        await self.cache_ai_dashboard(user_id, dashboard)
        return dashboard
    
    async def _get_trend_data(self, user_id: str) -> Tuple[Dict[str, float], Dict[str, float]]:
        """Get spending data for trend comparison."""
        now = datetime.utcnow()
        start_of_month = datetime(now.year, now.month, 1)
        
        if now.month == 1:
            prev_month_start = datetime(now.year - 1, 12, 1)
            prev_month_end = datetime(now.year, 1, 1)
        else:
            prev_month_start = datetime(now.year, now.month - 1, 1)
            prev_month_end = start_of_month
        
        # Current month aggregation
        current_pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "type": TransactionType.EXPENSE.value,
                    "date": {"$gte": start_of_month, "$lte": now}
                }
            },
            {
                "$group": {
                    "_id": "$category",
                    "amount": {"$sum": "$amount"}
                }
            }
        ]
        
        current_results = await self.transactions_collection.aggregate(current_pipeline).to_list(None)
        current_data = {r["_id"]: r["amount"] for r in current_results}
        
        # Previous month aggregation
        prev_pipeline = [
            {
                "$match": {
                    "user_id": user_id,
                    "type": TransactionType.EXPENSE.value,
                    "date": {"$gte": prev_month_start, "$lt": prev_month_end}
                }
            },
            {
                "$group": {
                    "_id": "$category",
                    "amount": {"$sum": "$amount"}
                }
            }
        ]
        
        prev_results = await self.transactions_collection.aggregate(prev_pipeline).to_list(None)
        previous_data = {r["_id"]: r["amount"] for r in prev_results}
        
        return current_data, previous_data


# Singleton instance
_insights_service: Optional[InsightsService] = None


def get_insights_service() -> InsightsService:
    """Get or create the insights service singleton."""
    global _insights_service
    if _insights_service is None:
        _insights_service = InsightsService()
    return _insights_service
