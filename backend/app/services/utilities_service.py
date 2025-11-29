"""Utilities service for reports, exports, debts, and receipt scanning."""
import logging
import csv
import io
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from bson import ObjectId  # type: ignore[import]

from reportlab.lib.pagesizes import A4  # type: ignore[import]
from reportlab.lib import colors  # type: ignore[import]
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle  # type: ignore[import]
from reportlab.lib.units import inch  # type: ignore[import]
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle  # type: ignore[import]
from reportlab.lib.enums import TA_CENTER  # type: ignore[import]

from app.config.mongodb import get_database
from app.config.firebase import get_firestore_db
from app.models.utility import (
    DebtEntry,
    DebtResponse,
    DebtUpdate,
    DebtStatus,
    DebtType,
    NetWorthData,
    ReportType,
    ReportFormat,
    ReportRequest,
    ReceiptScanResponse,
)
from app.services.ai.gemini_service import get_gemini_service

logger = logging.getLogger(__name__)


class UtilitiesService:
    """Service for utilities: reports, exports, debts, and receipt scanning."""

    def __init__(self):
        self.mongodb = get_database()
        self.firestore_db = get_firestore_db()
        self.transactions_collection = self.mongodb["transactions"]
        self.debts_collection = self.mongodb["debts"]
        self.reports_collection = self.mongodb["reports"]

    # ==================== DEBT MANAGEMENT ====================

    async def create_debt(self, user_id: str, debt_data: DebtEntry) -> DebtResponse:
        """
        Create a new debt entry.
        
        Args:
            user_id: Firebase user ID
            debt_data: Debt entry data
            
        Returns:
            Created debt response
        """
        try:
            debt_dict = debt_data.model_dump()
            debt_dict["user_id"] = user_id
            debt_dict["paid_amount"] = 0.0
            debt_dict["remaining_amount"] = debt_data.amount
            debt_dict["created_at"] = datetime.utcnow()
            debt_dict["updated_at"] = datetime.utcnow()
            
            result = await self.debts_collection.insert_one(debt_dict)
            debt_dict["_id"] = result.inserted_id
            
            return self._to_debt_response(debt_dict)
            
        except Exception as e:
            logger.error(f"Error creating debt for user {user_id}: {e}")
            raise

    async def get_debts(
        self, user_id: str, debt_type: Optional[DebtType] = None
    ) -> List[DebtResponse]:
        """
        Get all debts for a user.
        
        Args:
            user_id: Firebase user ID
            debt_type: Optional filter by debt type
            
        Returns:
            List of debt responses
        """
        try:
            filter_dict: Dict[str, Any] = {"user_id": user_id}
            if debt_type:
                filter_dict["type"] = debt_type.value
            
            cursor = self.debts_collection.find(filter_dict).sort("created_at", -1)
            
            debts = []
            async for doc in cursor:
                debts.append(self._to_debt_response(doc))
            
            return debts
            
        except Exception as e:
            logger.error(f"Error getting debts for user {user_id}: {e}")
            raise

    async def update_debt(
        self, user_id: str, debt_id: str, update_data: DebtUpdate
    ) -> Optional[DebtResponse]:
        """
        Update a debt entry.
        
        Args:
            user_id: Firebase user ID
            debt_id: Debt ID
            update_data: Update data
            
        Returns:
            Updated debt response or None if not found
        """
        try:
            # Get current debt
            debt = await self.debts_collection.find_one({
                "_id": ObjectId(debt_id),
                "user_id": user_id
            })
            
            if not debt:
                return None
            
            # Prepare update
            update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
            update_dict["updated_at"] = datetime.utcnow()
            
            # Handle paid_amount update
            if "paid_amount" in update_dict:
                total_amount = update_dict.get("amount", debt["amount"])
                update_dict["remaining_amount"] = total_amount - update_dict["paid_amount"]
                
                # Auto-mark as paid if fully paid
                if update_dict["remaining_amount"] <= 0:
                    update_dict["status"] = DebtStatus.PAID.value
                    update_dict["remaining_amount"] = 0
                elif update_dict["paid_amount"] > 0:
                    update_dict["status"] = DebtStatus.PARTIAL.value
            
            await self.debts_collection.update_one(
                {"_id": ObjectId(debt_id)},
                {"$set": update_dict}
            )
            
            # Fetch updated document
            updated_debt = await self.debts_collection.find_one({"_id": ObjectId(debt_id)})
            return self._to_debt_response(updated_debt)
            
        except Exception as e:
            logger.error(f"Error updating debt {debt_id}: {e}")
            raise

    async def mark_debt_paid(self, user_id: str, debt_id: str) -> Optional[DebtResponse]:
        """Mark a debt as fully paid."""
        try:
            debt = await self.debts_collection.find_one({
                "_id": ObjectId(debt_id),
                "user_id": user_id
            })
            
            if not debt:
                return None
            
            await self.debts_collection.update_one(
                {"_id": ObjectId(debt_id)},
                {
                    "$set": {
                        "status": DebtStatus.PAID.value,
                        "paid_amount": debt["amount"],
                        "remaining_amount": 0,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            updated_debt = await self.debts_collection.find_one({"_id": ObjectId(debt_id)})
            return self._to_debt_response(updated_debt)
            
        except Exception as e:
            logger.error(f"Error marking debt {debt_id} as paid: {e}")
            raise

    async def delete_debt(self, user_id: str, debt_id: str) -> bool:
        """Delete a debt entry."""
        try:
            result = await self.debts_collection.delete_one({
                "_id": ObjectId(debt_id),
                "user_id": user_id
            })
            return result.deleted_count > 0
        except Exception as e:
            logger.error(f"Error deleting debt {debt_id}: {e}")
            raise

    # ==================== NET WORTH ====================

    async def calculate_net_worth(self, user_id: str) -> NetWorthData:
        """
        Calculate user's net worth from balance and debts.
        
        Args:
            user_id: Firebase user ID
            
        Returns:
            NetWorthData with assets, liabilities, and breakdown
        """
        try:
            # Get user balance from Firestore
            balance = 0.0
            try:
                user_doc = self.firestore_db.collection("users").document(user_id).get()
                if user_doc.exists:
                    balance = user_doc.to_dict().get("balance", 0)
            except Exception as e:
                logger.warning(f"Could not fetch user balance: {e}")
            
            # Get debts
            debts_cursor = self.debts_collection.find({
                "user_id": user_id,
                "status": {"$ne": DebtStatus.PAID.value}
            })
            
            owed_to_others = 0.0  # Money you owe (liability)
            owed_by_others = 0.0  # Money owed to you (asset)
            
            async for debt in debts_cursor:
                remaining = debt.get("remaining_amount", 0)
                if debt.get("type") == DebtType.OWED.value:
                    owed_to_others += remaining
                else:  # LENT
                    owed_by_others += remaining
            
            # Calculate net worth
            assets = balance + owed_by_others
            liabilities = owed_to_others
            net_worth = assets - liabilities
            
            return NetWorthData(
                assets=round(assets, 2),
                liabilities=round(liabilities, 2),
                net_worth=round(net_worth, 2),
                asset_breakdown={
                    "cash_balance": round(balance, 2),
                    "receivables": round(owed_by_others, 2)
                },
                liability_breakdown={
                    "payables": round(owed_to_others, 2)
                },
                calculated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error calculating net worth for user {user_id}: {e}")
            raise

    # ==================== REPORTS ====================

    async def generate_report(
        self,
        user_id: str,
        report_request: ReportRequest
    ) -> Tuple[bytes, str]:
        """
        Generate a financial report.
        
        Args:
            user_id: Firebase user ID
            report_request: Report parameters
            
        Returns:
            Tuple of (file_bytes, filename)
        """
        try:
            # Determine date range
            start_date, end_date = self._get_report_date_range(report_request)
            
            # Fetch transactions
            transactions = await self._get_transactions_for_report(
                user_id, start_date, end_date
            )
            
            # Fetch goals if requested
            goals = []
            if report_request.include_goals:
                goals = await self._get_goals_for_report(user_id)
            
            # Generate AI summary
            gemini_service = get_gemini_service()
            ai_summary = await gemini_service.generate_financial_report_summary(
                transactions, goals, report_request.type.value, start_date, end_date
            )
            
            # Generate report based on format
            if report_request.format == ReportFormat.PDF:
                file_bytes = self._generate_pdf_report(
                    transactions, goals, ai_summary, report_request, start_date, end_date
                )
                filename = f"financial_report_{start_date}_{end_date}.pdf"
            else:  # CSV
                file_bytes = self._generate_csv_report(transactions, start_date, end_date)
                filename = f"transactions_{start_date}_{end_date}.csv"
            
            return file_bytes, filename
            
        except Exception as e:
            logger.error(f"Error generating report for user {user_id}: {e}")
            raise

    async def export_transactions(
        self,
        user_id: str,
        format: ReportFormat,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        categories: Optional[List[str]] = None
    ) -> Tuple[bytes, str]:
        """
        Export transactions to CSV or PDF.
        
        Args:
            user_id: Firebase user ID
            format: Export format (csv/pdf)
            start_date: Optional start date filter
            end_date: Optional end date filter
            categories: Optional category filter
            
        Returns:
            Tuple of (file_bytes, filename)
        """
        try:
            # Build filter
            filter_dict: Dict[str, Any] = {"user_id": user_id}
            
            if start_date or end_date:
                date_filter = {}
                if start_date:
                    date_filter["$gte"] = datetime.combine(start_date, datetime.min.time())
                if end_date:
                    date_filter["$lte"] = datetime.combine(end_date, datetime.max.time())
                filter_dict["date"] = date_filter
            
            if categories:
                filter_dict["category"] = {"$in": categories}
            
            # Fetch transactions
            cursor = self.transactions_collection.find(filter_dict).sort("date", -1)
            transactions = await cursor.to_list(None)
            
            # Generate export
            date_str = datetime.now().strftime("%Y%m%d")
            if format == ReportFormat.CSV:
                file_bytes = self._generate_csv_export(transactions)
                filename = f"transactions_export_{date_str}.csv"
            else:
                file_bytes = self._generate_pdf_export(transactions)
                filename = f"transactions_export_{date_str}.pdf"
            
            return file_bytes, filename
            
        except Exception as e:
            logger.error(f"Error exporting transactions for user {user_id}: {e}")
            raise

    # ==================== RECEIPT SCANNING ====================

    async def scan_receipt(self, user_id: str, image_bytes: bytes) -> ReceiptScanResponse:
        """
        Scan a receipt image and extract transaction data.
        
        Args:
            user_id: Firebase user ID
            image_bytes: Receipt image bytes
            
        Returns:
            ReceiptScanResponse with extracted data
        """
        try:
            gemini_service = get_gemini_service()
            result = await gemini_service.scan_receipt(image_bytes)
            
            # Convert to response model
            return ReceiptScanResponse(
                merchant_name=result.get("merchant_name"),
                amount=result.get("amount"),
                date=self._parse_date(result.get("date")),
                items=result.get("items", []),
                category=result.get("category"),
                raw_text=result.get("raw_text"),
                confidence=result.get("confidence", 0.0),
                success=result.get("success", False),
                error_message=result.get("error_message")
            )
            
        except Exception as e:
            logger.error(f"Error scanning receipt for user {user_id}: {e}")
            return ReceiptScanResponse(
                success=False,
                error_message=str(e),
                confidence=0.0
            )

    # ==================== HELPER METHODS ====================

    def _to_debt_response(self, doc: Dict[str, Any]) -> DebtResponse:
        """Convert MongoDB document to DebtResponse."""
        return DebtResponse(
            id=str(doc["_id"]),
            user_id=doc["user_id"],
            person_name=doc["person_name"],
            amount=doc["amount"],
            type=DebtType(doc["type"]),
            status=DebtStatus(doc.get("status", "pending")),
            description=doc.get("description"),
            due_date=doc.get("due_date"),
            paid_amount=doc.get("paid_amount", 0.0),
            remaining_amount=doc.get("remaining_amount", doc["amount"]),
            created_at=doc.get("created_at", datetime.utcnow()),
            updated_at=doc.get("updated_at")
        )

    def _get_report_date_range(
        self, request: ReportRequest
    ) -> Tuple[date, date]:
        """Get date range for report based on request parameters."""
        today = date.today()
        
        if request.start_date and request.end_date:
            return request.start_date, request.end_date
        
        if request.type == ReportType.MONTHLY:
            month = request.month or today.month
            year = request.year or today.year
            start = date(year, month, 1)
            if month == 12:
                end = date(year + 1, 1, 1) - timedelta(days=1)
            else:
                end = date(year, month + 1, 1) - timedelta(days=1)
            return start, end
        
        elif request.type == ReportType.ANNUAL:
            year = request.year or today.year
            return date(year, 1, 1), date(year, 12, 31)
        
        else:  # CUSTOM - default to last 30 days
            return today - timedelta(days=30), today

    async def _get_transactions_for_report(
        self, user_id: str, start_date: date, end_date: date
    ) -> List[Dict[str, Any]]:
        """Fetch transactions for report date range."""
        cursor = self.transactions_collection.find({
            "user_id": user_id,
            "date": {
                "$gte": datetime.combine(start_date, datetime.min.time()),
                "$lte": datetime.combine(end_date, datetime.max.time())
            }
        }).sort("date", -1)
        
        return await cursor.to_list(None)

    async def _get_goals_for_report(self, user_id: str) -> List[Dict[str, Any]]:
        """Fetch user goals for report."""
        goals = []
        try:
            goals_ref = self.firestore_db.collection("users").document(user_id).collection("goals")
            for doc in goals_ref.stream():
                goal_data = doc.to_dict()
                goal_data["id"] = doc.id
                goals.append(goal_data)
        except Exception as e:
            logger.warning(f"Could not fetch goals for report: {e}")
        return goals

    def _generate_pdf_report(
        self,
        transactions: List[Dict[str, Any]],
        goals: List[Dict[str, Any]],
        ai_summary: Dict[str, Any],
        request: ReportRequest,
        start_date: date,
        end_date: date
    ) -> bytes:
        """Generate PDF financial report."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.5*inch, bottomMargin=0.5*inch)
        styles = getSampleStyleSheet()
        elements = []
        
        # Title
        title_style = ParagraphStyle(
            'Title',
            parent=styles['Heading1'],
            fontSize=24,
            alignment=TA_CENTER,
            spaceAfter=20
        )
        elements.append(Paragraph("Financial Report", title_style))
        elements.append(Paragraph(
            f"{start_date.strftime('%B %d, %Y')} - {end_date.strftime('%B %d, %Y')}",
            ParagraphStyle('Subtitle', parent=styles['Normal'], alignment=TA_CENTER, fontSize=12)
        ))
        elements.append(Spacer(1, 20))
        
        # AI Summary
        if ai_summary:
            elements.append(Paragraph("AI Analysis", styles['Heading2']))
            elements.append(Paragraph(ai_summary.get("summary", ""), styles['Normal']))
            elements.append(Spacer(1, 10))
            
            # Highlights
            if ai_summary.get("highlights"):
                elements.append(Paragraph("Highlights:", styles['Heading3']))
                for highlight in ai_summary["highlights"]:
                    elements.append(Paragraph(f"• {highlight}", styles['Normal']))
                elements.append(Spacer(1, 10))
            
            # Score
            score = ai_summary.get("score", 0)
            score_label = ai_summary.get("score_label", "N/A")
            elements.append(Paragraph(
                f"Financial Health Score: {score}/100 ({score_label})",
                styles['Heading3']
            ))
            elements.append(Spacer(1, 20))
        
        # Summary Statistics
        income = sum(t.get("amount", 0) for t in transactions if t.get("type") == "income")
        expenses = sum(t.get("amount", 0) for t in transactions if t.get("type") == "expense")
        
        elements.append(Paragraph("Summary", styles['Heading2']))
        summary_data = [
            ["Total Income", f"₹{income:,.2f}"],
            ["Total Expenses", f"₹{expenses:,.2f}"],
            ["Net Savings", f"₹{income - expenses:,.2f}"],
            ["Transactions", str(len(transactions))]
        ]
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # Category Breakdown
        if request.include_categories:
            elements.append(Paragraph("Spending by Category", styles['Heading2']))
            category_totals = {}
            for t in transactions:
                if t.get("type") == "expense":
                    cat = t.get("category", "Others")
                    category_totals[cat] = category_totals.get(cat, 0) + t.get("amount", 0)
            
            if category_totals:
                category_data = [["Category", "Amount", "%"]]
                total_expenses = sum(category_totals.values()) or 1
                for cat, amount in sorted(category_totals.items(), key=lambda x: x[1], reverse=True):
                    pct = (amount / total_expenses) * 100
                    category_data.append([cat, f"₹{amount:,.2f}", f"{pct:.1f}%"])
                
                category_table = Table(category_data, colWidths=[2*inch, 2*inch, 1*inch])
                category_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#001F3F')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ]))
                elements.append(category_table)
        
        elements.append(Spacer(1, 20))
        
        # Recommendations
        if ai_summary and ai_summary.get("recommendations"):
            elements.append(Paragraph("Recommendations", styles['Heading2']))
            for rec in ai_summary["recommendations"]:
                elements.append(Paragraph(f"→ {rec}", styles['Normal']))
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    def _generate_csv_report(
        self,
        transactions: List[Dict[str, Any]],
        start_date: date,
        end_date: date
    ) -> bytes:
        """Generate CSV transaction report."""
        return self._generate_csv_export(transactions)

    def _generate_csv_export(self, transactions: List[Dict[str, Any]]) -> bytes:
        """Generate CSV export of transactions."""
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        
        # Header
        writer.writerow([
            "Date", "Name", "Amount", "Type", "Category", "Description"
        ])
        
        # Data rows
        for t in transactions:
            trans_date = t.get("date")
            if isinstance(trans_date, datetime):
                date_str = trans_date.strftime("%Y-%m-%d")
            else:
                date_str = str(trans_date)
            
            writer.writerow([
                date_str,
                t.get("name", ""),
                t.get("amount", 0),
                t.get("type", ""),
                t.get("category", ""),
                t.get("description", "")
            ])
        
        return buffer.getvalue().encode('utf-8')

    def _generate_pdf_export(self, transactions: List[Dict[str, Any]]) -> bytes:
        """Generate PDF export of transactions."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []
        
        # Title
        elements.append(Paragraph("Transaction Export", styles['Heading1']))
        elements.append(Paragraph(
            f"Generated on {datetime.now().strftime('%B %d, %Y')}",
            styles['Normal']
        ))
        elements.append(Spacer(1, 20))
        
        # Table
        if transactions:
            from app.config.constants import MAX_TRANSACTIONS_IN_PDF
            
            table_data = [["Date", "Name", "Amount", "Type", "Category"]]
            for t in transactions[:MAX_TRANSACTIONS_IN_PDF]:
                trans_date = t.get("date")
                if isinstance(trans_date, datetime):
                    date_str = trans_date.strftime("%Y-%m-%d")
                else:
                    date_str = str(trans_date)[:10]
                
                amount = t.get("amount", 0)
                t_type = t.get("type", "expense")
                amount_str = f"₹{amount:,.2f}" if t_type == "income" else f"-₹{amount:,.2f}"
                
                table_data.append([
                    date_str,
                    t.get("name", "")[:30],
                    amount_str,
                    t_type.capitalize(),
                    t.get("category", "")
                ])
            
            table = Table(table_data, colWidths=[1.2*inch, 2*inch, 1.2*inch, 1*inch, 1.2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#001F3F')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ]))
            elements.append(table)
        else:
            elements.append(Paragraph("No transactions found.", styles['Normal']))
        
        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()

    def _parse_date(self, date_str: Optional[str]) -> Optional[date]:
        """Parse date string to date object."""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            try:
                return datetime.strptime(date_str, "%d/%m/%Y").date()
            except ValueError:
                return None


# Singleton instance
_utilities_service: Optional[UtilitiesService] = None


def get_utilities_service() -> UtilitiesService:
    """Get the UtilitiesService singleton instance."""
    global _utilities_service
    if _utilities_service is None:
        _utilities_service = UtilitiesService()
    return _utilities_service
