"""Gemini AI service for transaction categorization, insights generation, and receipt scanning."""
import json
import logging
from datetime import datetime, date
from typing import List, Dict, Any, Optional
from io import BytesIO

from app.config.gemini import get_gemini_model, get_gemini_vision_model
from app.models.transaction import TransactionCategory

logger = logging.getLogger(__name__)

# Valid transaction categories
VALID_CATEGORIES = [cat.value for cat in TransactionCategory]

# Mumbai-specific merchant mappings for faster categorization
MERCHANT_CATEGORY_MAP = {
    # Food
    "swiggy": "Food", "zomato": "Food", "dominos": "Food", "mcdonalds": "Food",
    "starbucks": "Food", "chai": "Food", "vadapav": "Food", "udipi": "Food",
    "burger king": "Food", "pizza hut": "Food", "kfc": "Food", "subway": "Food",
    # Travel
    "uber": "Travel", "ola": "Travel", "rapido": "Travel", "metro": "Travel",
    "irctc": "Travel", "local": "Travel", "best": "Travel", "petrol": "Travel",
    "hp": "Travel", "indian oil": "Travel", "bharat petroleum": "Travel",
    # Bills
    "adani": "Bills", "tata power": "Bills", "jio": "Bills", "airtel": "Bills",
    "vodafone": "Bills", "mahanagar gas": "Bills", "bmc": "Bills", "mtnl": "Bills",
    # Shopping
    "amazon": "Shopping", "flipkart": "Shopping", "myntra": "Shopping",
    "dmart": "Shopping", "reliance": "Shopping", "big bazaar": "Shopping",
    "ajio": "Shopping", "nykaa": "Shopping", "meesho": "Shopping",
    # Subscriptions
    "netflix": "Subscriptions", "spotify": "Subscriptions", "hotstar": "Subscriptions",
    "prime": "Subscriptions", "gym": "Subscriptions", "youtube": "Subscriptions",
}


class GeminiService:
    """AI-powered financial analysis using Google Gemini."""

    def __init__(self):
        self._model = None
        self._vision_model = None

    @property
    def model(self):
        """Lazy load text model."""
        if self._model is None:
            self._model = get_gemini_model()
        return self._model

    @property
    def vision_model(self):
        """Lazy load vision model."""
        if self._vision_model is None:
            self._vision_model = get_gemini_vision_model()
        return self._vision_model

    # ==================== HELPER METHODS ====================

    def _parse_ai_response(self, response_text: str) -> Any:
        """Parse AI response, handling markdown code blocks."""
        text = response_text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.debug(f"Raw response: {text[:500]}")
            raise ValueError(f"AI returned invalid JSON: {e}")

    def _quick_categorize(self, name: str) -> Optional[str]:
        """Quick local categorization without AI."""
        name_lower = name.lower()
        for keyword, category in MERCHANT_CATEGORY_MAP.items():
            if keyword in name_lower:
                return category
        return None

    def _format_inr(self, amount: float) -> str:
        """Format amount in Indian Rupee."""
        return f"₹{amount:,.0f}"

    def _calculate_stats(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate transaction statistics."""
        category_totals = {}
        total_income = 0
        total_expenses = 0

        for txn in transactions:
            amount = txn.get("amount", 0)
            if txn.get("type") == "income":
                total_income += amount
            else:
                total_expenses += amount
                cat = txn.get("category", "Others")
                category_totals[cat] = category_totals.get(cat, 0) + amount

        sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)

        return {
            "income": total_income,
            "expenses": total_expenses,
            "savings": total_income - total_expenses,
            "savings_rate": ((total_income - total_expenses) / total_income * 100) if total_income > 0 else 0,
            "category_totals": dict(sorted_categories),
            "top_category": sorted_categories[0] if sorted_categories else ("None", 0),
            "txn_count": len(transactions)
        }

    def _get_health_status(self, savings_rate: float) -> Dict[str, str]:
        """Get health status based on savings rate."""
        if savings_rate >= 20:
            return {"emoji": "🟢", "label": "Ek Number!", "level": "excellent"}
        elif savings_rate >= 10:
            return {"emoji": "🟡", "label": "Thik Hai", "level": "good"}
        elif savings_rate >= 0:
            return {"emoji": "🟠", "label": "Dhyan Do", "level": "fair"}
        else:
            return {"emoji": "🔴", "label": "Alert!", "level": "poor"}

    # ==================== TRANSACTION CATEGORIZATION ====================

    async def categorize_transaction(
        self, name: str, amount: float, description: Optional[str] = None
    ) -> str:
        """Categorize transaction using local rules first, then AI."""
        # Try quick local categorization
        quick_cat = self._quick_categorize(name)
        if quick_cat:
            logger.info(f"Quick categorized '{name}' as '{quick_cat}'")
            return quick_cat

        # Fall back to AI
        if not self.model:
            return TransactionCategory.OTHERS.value

        try:
            prompt = f"""Categorize this Mumbai transaction. Reply with ONE word only.

Transaction: {name}
Amount: ₹{amount}
Note: {description or 'None'}

Categories: Food, Bills, Shopping, Travel, Subscriptions, Salary, Freelance, Investment, Others

Reply with category name only."""

            response = await self.model.generate_content_async(prompt)
            category = response.text.strip()

            if category in VALID_CATEGORIES:
                return category

            for valid_cat in VALID_CATEGORIES:
                if valid_cat.lower() in category.lower():
                    return valid_cat

            return TransactionCategory.OTHERS.value

        except Exception as e:
            logger.error(f"Categorization error: {e}")
            return TransactionCategory.OTHERS.value

    # ==================== TRANSACTION IMPACT NOTIFICATION ====================

    async def get_transaction_impact(
        self,
        transaction: Dict[str, Any],
        goals: List[Dict[str, Any]],
        monthly_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate instant notification about transaction's impact on goals.
        Called immediately after adding a transaction.
        """
        txn_amount = transaction.get("amount", 0)
        txn_type = transaction.get("type", "expense")
        txn_category = transaction.get("category", "Others")

        # Calculate impact
        monthly_budget = monthly_stats.get("budget", 0)
        monthly_spent = monthly_stats.get("spent", 0)
        remaining_budget = monthly_budget - monthly_spent if monthly_budget > 0 else 0

        # Find affected goals
        goal_alerts = []
        for goal in goals:
            saved = goal.get("saved_amount", 0)
            target = goal.get("target_amount", 1)
            progress = (saved / target * 100) if target > 0 else 0

            if progress >= 100:
                goal_alerts.append({"emoji": "🎯", "text": f"{goal.get('title', 'Goal')[:15]} done!"})
            elif progress >= 75:
                goal_alerts.append({"emoji": "🔥", "text": f"{goal.get('title', 'Goal')[:15]}: {progress:.0f}%"})

        # Generate notification based on transaction type
        if txn_type == "income":
            return {
                "show": True,
                "emoji": "💰",
                "title": f"+{self._format_inr(txn_amount)}",
                "subtitle": "Aamdani aa gayi!",
                "type": "success",
                "goal_alerts": goal_alerts[:2]
            }

        # Expense notifications
        budget_percent = (txn_amount / monthly_budget * 100) if monthly_budget > 0 else 0

        if remaining_budget < 0:
            return {
                "show": True,
                "emoji": "🚨",
                "title": "Budget Cross!",
                "subtitle": f"Extra: {self._format_inr(abs(remaining_budget))}",
                "type": "error",
                "goal_alerts": goal_alerts[:2]
            }
        elif budget_percent > 15:
            return {
                "show": True,
                "emoji": "⚠️",
                "title": "Bada Kharcha",
                "subtitle": f"{self._format_inr(txn_amount)} - {txn_category}",
                "type": "warning",
                "goal_alerts": goal_alerts[:2]
            }
        else:
            return {
                "show": True,
                "emoji": "✅",
                "title": f"{txn_category}",
                "subtitle": f"{self._format_inr(txn_amount)} | Bacha: {self._format_inr(max(0, remaining_budget))}",
                "type": "info",
                "goal_alerts": goal_alerts[:2]
            }

    # ==================== INSIGHTS GENERATION (SEGREGATED) ====================

    async def generate_insights(
        self,
        transactions: List[Dict[str, Any]],
        goals: List[Dict[str, Any]],
        user_stats: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate segregated, short insights for the insights page.
        Returns categorized sections instead of generic cards.
        """
        stats = self._calculate_stats(transactions)

        return {
            "quick_stats": self._build_quick_stats(stats, user_stats),
            "spending": self._build_spending_section(stats),
            "goals": self._build_goals_section(goals),
            "alerts": self._build_alerts(stats, goals),
            "tip": await self._generate_ai_tip(stats, goals),
            "generated_at": datetime.utcnow().isoformat()
        }

    def _build_quick_stats(self, stats: Dict, user_stats: Dict) -> Dict[str, Any]:
        """Build quick stats section - 4 key numbers."""
        health = self._get_health_status(stats["savings_rate"])

        return {
            "items": [
                {"label": "Aamdani", "value": self._format_inr(stats["income"]), "icon": "arrow-up", "color": "green"},
                {"label": "Kharcha", "value": self._format_inr(stats["expenses"]), "icon": "arrow-down", "color": "red"},
                {"label": "Bachat", "value": self._format_inr(stats["savings"]), "icon": "piggy-bank", "color": "blue"},
                {"label": "Health", "value": health["label"], "emoji": health["emoji"], "level": health["level"]}
            ]
        }

    def _build_spending_section(self, stats: Dict) -> Dict[str, Any]:
        """Build spending breakdown by category."""
        total = stats["expenses"]
        categories = []

        for cat, amount in list(stats["category_totals"].items())[:5]:
            percent = (amount / total * 100) if total > 0 else 0
            categories.append({
                "name": cat,
                "amount": self._format_inr(amount),
                "percent": round(percent)
            })

        return {
            "title": "Kahan Gaya Paisa?",
            "total": self._format_inr(total),
            "categories": categories
        }

    def _build_goals_section(self, goals: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build goal progress tracker."""
        items = []

        for goal in goals[:4]:
            saved = goal.get("saved_amount", 0)
            target = goal.get("target_amount", 0)
            
            # Guard against division by zero
            if target <= 0:
                progress = 100.0 if saved > 0 else 0.0
                remaining = 0
            else:
                progress = (saved / target * 100)
                remaining = target - saved

            if progress >= 100:
                status = {"emoji": "🎯", "text": "Done!"}
            elif progress >= 75:
                status = {"emoji": "🔥", "text": "Almost!"}
            elif progress >= 50:
                status = {"emoji": "💪", "text": "Halfway"}
            else:
                status = {"emoji": "🎯", "text": f"{self._format_inr(remaining)} baaki"}

            items.append({
                "title": goal.get("title", "Goal")[:20],
                "progress": round(progress),
                "emoji": status["emoji"],
                "status": status["text"]
            })

        return {
            "title": "Goals",
            "items": items,
            "empty": "Koi goal nahi? Banao!" if not items else None
        }

    def _build_alerts(self, stats: Dict, goals: List[Dict]) -> List[Dict[str, Any]]:
        """Build smart alerts - max 2 most important."""
        alerts = []

        # Deficit alert
        if stats["savings"] < 0:
            alerts.append({
                "type": "error",
                "emoji": "🚨",
                "text": f"Deficit: {self._format_inr(abs(stats['savings']))}"
            })

        # High spending category (40% of income threshold indicates disproportionate spending)
        HIGH_SPENDING_THRESHOLD = 0.4
        top_cat, top_amount = stats["top_category"]
        if top_amount > stats["income"] * HIGH_SPENDING_THRESHOLD and stats["income"] > 0:
            alerts.append({
                "type": "warning",
                "emoji": "⚠️",
                "text": f"{top_cat} pe zyada kharcha"
            })

        # Goal deadline alerts
        for goal in goals[:3]:
            deadline = goal.get("deadline")
            if deadline:
                try:
                    deadline_str = str(deadline).replace("Z", "+00:00")
                    if "T" in deadline_str:
                        deadline_date = datetime.fromisoformat(deadline_str)
                    else:
                        deadline_date = datetime.strptime(deadline_str, "%Y-%m-%d")
                    days_left = (deadline_date - datetime.utcnow()).days
                    progress = (goal.get("saved_amount", 0) / goal.get("target_amount", 1)) * 100

                    if 0 < days_left <= 7 and progress < 90:
                        alerts.append({
                            "type": "warning",
                            "emoji": "⏰",
                            "text": f"{goal.get('title', 'Goal')[:12]}: {days_left} din baaki"
                        })
                except Exception as e:
                    # Ignore deadline parsing errors; invalid or missing dates are expected for some goals.
                    logger.warning(f"Failed to parse goal deadline '{deadline}': {e}")

        return alerts[:2]

    async def _generate_ai_tip(self, stats: Dict, goals: List[Dict]) -> Dict[str, Any]:
        """Generate one short AI tip."""
        if not self.model:
            return self._get_default_tip(stats)

        try:
            prompt = f"""Mumbai financial buddy. Give ONE tip (max 12 words) in Hinglish.

Income: ₹{stats['income']:,.0f} | Expenses: ₹{stats['expenses']:,.0f}
Top: {stats['top_category'][0]} (₹{stats['top_category'][1]:,.0f})

Reply tip only. Use 'boss/bhai'. Be specific."""

            response = await self.model.generate_content_async(prompt)
            tip_text = response.text.strip()[:80]

            return {"emoji": "💡", "text": tip_text, "ai": True}

        except Exception as e:
            logger.error(f"AI tip error: {e}")
            return self._get_default_tip(stats)

    def _get_default_tip(self, stats: Dict) -> Dict[str, Any]:
        """Get default tip based on stats."""
        rate = stats["savings_rate"]
        if rate < 0:
            text = "Boss, kharcha kam karo!"
        elif rate < 10:
            text = "20% bachao, future set!"
        elif rate >= 30:
            text = "Zabardast bachat!"
        else:
            text = "Sahi track pe ho!"

        return {"emoji": "💡", "text": text, "ai": False}

    # ==================== FULL AI INSIGHTS GENERATION ====================

    async def generate_full_ai_insights(
        self,
        transactions: List[Dict[str, Any]],
        goals: List[Dict[str, Any]],
        user_stats: Dict[str, Any],
        current_month_spending: Dict[str, float],
        previous_month_spending: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Generate complete AI-powered insights for the insights page.
        All content is AI-generated with Hinglish responses.
        """
        stats = self._calculate_stats(transactions)
        
        # Build base structure
        result = {
            "quick_stats": self._build_quick_stats(stats, user_stats),
            "spending": self._build_spending_section(stats),
            "goals": self._build_goals_section(goals),
            "alerts": self._build_alerts(stats, goals),
            "ai_generated": False,
            "generated_at": datetime.utcnow().isoformat()
        }

        # Generate AI content if model available
        if self.model:
            try:
                ai_content = await self._generate_ai_content(stats, goals, current_month_spending, previous_month_spending)
                result.update(ai_content)
                result["ai_generated"] = True
            except Exception as e:
                logger.error(f"AI content generation failed: {e}")
                result["ai_summary"] = self._get_default_tip(stats)
                result["ai_insights"] = []
                result["trend_analysis"] = self._get_default_trend(current_month_spending, previous_month_spending)
        else:
            result["ai_summary"] = self._get_default_tip(stats)
            result["ai_insights"] = []
            result["trend_analysis"] = self._get_default_trend(current_month_spending, previous_month_spending)

        return result

    async def _generate_ai_content(
        self,
        stats: Dict,
        goals: List[Dict],
        current_spending: Dict[str, float],
        previous_spending: Dict[str, float]
    ) -> Dict[str, Any]:
        """Generate all AI content in a single prompt for efficiency."""
        
        # Prepare goals summary
        goals_text = ""
        for g in goals[:3]:
            target = g.get("target_amount", 0)
            saved = g.get("saved_amount", 0)
            progress = (saved / target * 100) if target > 0 else (100.0 if saved > 0 else 0.0)
            goals_text += f"- {g.get('title', 'Goal')}: {progress:.0f}% done\n"

        # Calculate trend
        curr_total = sum(current_spending.values())
        prev_total = sum(previous_spending.values())
        trend_change = ((curr_total - prev_total) / prev_total * 100) if prev_total > 0 else 0

        prompt = f"""You are a Mumbai financial buddy. Analyze this data and respond in Hinglish (Hindi-English mix).
Use simple words, Mumbai slang (boss, bhai, kharcha, bachat). Keep everything SHORT.

DATA:
Income: ₹{stats['income']:,.0f}
Expenses: ₹{stats['expenses']:,.0f}
Savings: ₹{stats['savings']:,.0f} ({stats['savings_rate']:.0f}%)
Top spending: {stats['top_category'][0]} - ₹{stats['top_category'][1]:,.0f}
Month trend: {trend_change:+.0f}% vs last month

Goals:
{goals_text or 'No goals set'}

Spending by category:
{json.dumps(dict(list(stats['category_totals'].items())[:5]), indent=2)}

Generate JSON response:
{{
  "summary": "1 line summary (max 15 words) - encouraging, specific with numbers",
  "insights": [
    {{"emoji": "emoji", "title": "5 words max", "text": "15 words max actionable tip"}},
    {{"emoji": "emoji", "title": "5 words max", "text": "15 words max actionable tip"}},
    {{"emoji": "emoji", "title": "5 words max", "text": "15 words max actionable tip"}}
  ],
  "trend": {{
    "emoji": "📈 or 📉 or ➡️",
    "title": "3 words",
    "text": "10 words trend analysis",
    "direction": "up|down|stable"
  }},
  "top_tip": "One main tip in 10 words"
}}

Be specific with ₹ amounts. Reply JSON only."""

        if not self.model:
            raise RuntimeError("Gemini model not initialized")

        response = await self.model.generate_content_async(prompt)
        ai_data = self._parse_ai_response(response.text)

        return {
            "ai_summary": {"emoji": "✨", "text": ai_data.get("summary", ""), "ai": True},
            "ai_insights": ai_data.get("insights", []),
            "trend_analysis": ai_data.get("trend", {}),
            "top_tip": ai_data.get("top_tip", "")
        }

    def _get_default_trend(self, current: Dict[str, float], previous: Dict[str, float]) -> Dict[str, Any]:
        """Get default trend when AI unavailable."""
        curr_total = sum(current.values())
        prev_total = sum(previous.values())
        
        if prev_total > 0:
            change = ((curr_total - prev_total) / prev_total) * 100
        else:
            change = 0

        if change > 10:
            return {"emoji": "📈", "title": "Badh gaya", "text": f"Kharcha {change:.0f}% zyada", "direction": "up"}
        elif change < -10:
            return {"emoji": "📉", "title": "Kam hua", "text": f"Kharcha {abs(change):.0f}% kam", "direction": "down"}
        else:
            return {"emoji": "➡️", "title": "Same hai", "text": "Pichle mahine jaisa", "direction": "stable"}

    # ==================== RECEIPT SCANNING ====================

    async def scan_receipt(self, image_bytes: bytes) -> Dict[str, Any]:
        """Extract transaction data from receipt image."""
        if not self.vision_model:
            return {"success": False, "error": "Vision unavailable"}

        try:
            import PIL.Image
            image = PIL.Image.open(BytesIO(image_bytes))

            prompt = """Extract from this Indian receipt. JSON only:
{"merchant": "name", "amount": number, "date": "YYYY-MM-DD", "category": "Food|Shopping|Bills|Travel|Others", "items": [{"name": "x", "price": 0}]}"""

            response = await self.vision_model.generate_content_async([prompt, image])
            result = self._parse_ai_response(response.text)
            result["success"] = True

            if result.get("category") not in VALID_CATEGORIES:
                result["category"] = "Others"

            return result

        except Exception as e:
            logger.error(f"Receipt scan error: {e}")
            return {"success": False, "error": str(e)}

    # ==================== TREND ANALYSIS ====================

    async def analyze_spending_trends(
        self,
        current_month_data: Dict[str, float],
        previous_month_data: Dict[str, float],
        goals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze spending trends between months."""
        current_total = sum(current_month_data.values())
        previous_total = sum(previous_month_data.values())

        if previous_total > 0:
            change = ((current_total - previous_total) / previous_total) * 100
        else:
            change = 100 if current_total > 0 else 0

        # Determine trend
        if change > 10:
            trend, emoji, text = "up", "📈", f"{abs(change):.0f}% badha"
        elif change < -10:
            trend, emoji, text = "down", "📉", f"{abs(change):.0f}% kam"
        else:
            trend, emoji, text = "stable", "➡️", "Same hai"

        # Find changes
        all_cats = set(current_month_data.keys()) | set(previous_month_data.keys())
        changes = []
        for cat in all_cats:
            curr = current_month_data.get(cat, 0)
            prev = previous_month_data.get(cat, 0)
            if prev > 0:
                changes.append((cat, ((curr - prev) / prev) * 100, curr - prev))

        changes.sort(key=lambda x: x[1], reverse=True)

        return {
            "overall_trend": trend,
            "trend_emoji": emoji,
            "trend_text": text,
            "trend_percentage": round(change, 1),
            "current_total": self._format_inr(current_total),
            "previous_total": self._format_inr(previous_total),
            "biggest_increase_category": changes[0][0] if changes and changes[0][1] > 0 else None,
            "biggest_decrease_category": changes[-1][0] if changes and changes[-1][1] < 0 else None,
            "analysis": f"Kharcha {text.lower()}",
            "warning": "Kharcha badh raha hai" if trend == "up" else None,
            "positive": "Sahi! Kam kharcha" if trend == "down" else None,
            "tip": "Track karte raho!"
        }

    # ==================== REPORT SUMMARY ====================

    async def generate_financial_report_summary(
        self,
        transactions: List[Dict[str, Any]],
        goals: List[Dict[str, Any]],
        period: str,
        start_date: date,
        end_date: date
    ) -> Dict[str, Any]:
        """Generate financial report summary."""
        stats = self._calculate_stats(transactions)
        health = self._get_health_status(stats["savings_rate"])

        summary = {
            "period": f"{start_date} to {end_date}",
            "period_type": period,
            "income": self._format_inr(stats["income"]),
            "expenses": self._format_inr(stats["expenses"]),
            "savings": self._format_inr(stats["savings"]),
            "savings_rate": f"{stats['savings_rate']:.1f}%",
            "score": min(100, max(0, int(50 + stats["savings_rate"]))),
            "score_label": health["label"],
            "top_categories": [
                {"name": cat, "amount": self._format_inr(amt)}
                for cat, amt in list(stats["category_totals"].items())[:3]
            ],
            "highlights": [
                f"Aamdani: {self._format_inr(stats['income'])}",
                f"Kharcha: {self._format_inr(stats['expenses'])}",
                f"Bachat: {stats['savings_rate']:.0f}%"
            ],
            "concerns": [] if stats["savings"] >= 0 else ["Kharcha zyada ho gaya"],
            "recommendations": ["Track karo", "Budget banao"],
            "generated_by_ai": False,
            "generated_at": datetime.utcnow().isoformat()
        }

        # Add AI summary if available
        if self.model:
            try:
                prompt = f"""1-line Hinglish summary (max 15 words):
Income ₹{stats['income']:,.0f}, Expenses ₹{stats['expenses']:,.0f}, Savings {stats['savings_rate']:.0f}%
Be encouraging, Mumbai style."""

                response = await self.model.generate_content_async(prompt)
                summary["summary"] = response.text.strip()[:100]
                summary["generated_by_ai"] = True
            except Exception:
                summary["summary"] = f"Is {period} mein {self._format_inr(stats['savings'])} bachaye!"

        return summary


# Singleton
_gemini_service: Optional[GeminiService] = None


def get_gemini_service() -> GeminiService:
    """Get GeminiService singleton."""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
