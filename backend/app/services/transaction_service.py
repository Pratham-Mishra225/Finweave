"""Transaction service for handling dual-write logic and balance calculations."""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from bson import ObjectId  # type: ignore[import]

from app.config.mongodb import get_database
from app.config.firebase import get_firestore_db
from app.models.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionFilter,
    TransactionSummary,
    TransactionUpdate,
    PaginatedTransactions,
    TransactionType
)
from app.services.home_service import HomeService
from app.services.notification_service import (
    get_notification_trigger,
    NotificationEventTrigger
)

logger = logging.getLogger(__name__)


class TransactionService:
    """Service for managing transactions with dual-write to MongoDB and Firestore."""

    def __init__(self):
        self.mongodb = get_database()
        self.firestore_db = get_firestore_db()
        self.transactions_collection = self.mongodb["transactions"]
        self.notification_trigger: Optional[NotificationEventTrigger] = None
        self._init_notification_trigger()

    def _init_notification_trigger(self) -> None:
        """Lazily initialize notification trigger to avoid import-time side effects."""
        try:
            self.notification_trigger = get_notification_trigger()
        except Exception as e:
            logger.warning(f"Notification trigger initialization failed: {e}")
            self.notification_trigger = None

    async def create_transaction(
        self, user_id: str, transaction_data: TransactionCreate
    ) -> TransactionResponse:
        """
        Create a new transaction in MongoDB and update Firestore cache.
        
        Args:
            user_id: The user's Firebase UID
            transaction_data: Transaction creation data
            
        Returns:
            TransactionResponse with created transaction
        """
        try:
            # Prepare transaction document for MongoDB
            transaction_dict = transaction_data.model_dump()
            transaction_dict["user_id"] = user_id
            transaction_dict["created_at"] = datetime.utcnow()
            transaction_dict["updated_at"] = datetime.utcnow()

            # Insert into MongoDB (primary source of truth)
            result = await self.transactions_collection.insert_one(transaction_dict)
            transaction_dict["_id"] = result.inserted_id

            # Recalculate user balance
            await self._recalculate_and_update_balance(user_id)

            # Update Firestore cache (last 50 transactions)
            await self._sync_firestore_cache(user_id)

            # Invalidate spending overview cache so graphs refresh
            await self._invalidate_spending_cache(user_id)

            # Convert to response model
            response = self._to_transaction_response(transaction_dict)

            # Trigger transaction notification (best-effort)
            await self._trigger_transaction_notification(user_id, transaction_dict)

            return response

        except Exception as e:
            logger.error(f"Error creating transaction for user {user_id}: {e}")
            raise

    async def _trigger_transaction_notification(self, user_id: str, transaction_data: Dict[str, Any]) -> None:
        """Send a notification when a transaction is added (best effort)."""
        if not self.notification_trigger:
            return

        try:
            await self.notification_trigger.trigger_on_transaction_added(
                user_id=user_id,
                transaction_name=transaction_data.get("name", "Transaction"),
                amount=transaction_data.get("amount", 0.0),
                category=str(transaction_data.get("category", "General")),
                transaction_id=str(transaction_data.get("_id"))
            )
        except Exception as e:
            logger.warning(
                "Failed to trigger transaction notification for user %s: %s",
                user_id,
                e
            )

    async def get_transactions_paginated(
        self, user_id: str, page: int = 1, limit: int = 20
    ) -> PaginatedTransactions:
        """
        Get paginated transactions from MongoDB.
        
        Args:
            user_id: The user's Firebase UID
            page: Page number (1-indexed)
            limit: Number of transactions per page
            
        Returns:
            PaginatedTransactions with transaction list and pagination info
        """
        try:
            skip = (page - 1) * limit

            # Get total count
            total = await self.transactions_collection.count_documents({"user_id": user_id})

            # Get paginated transactions
            cursor = self.transactions_collection.find({"user_id": user_id}).sort(
                "date", -1
            ).skip(skip).limit(limit)

            transactions = []
            async for doc in cursor:
                transactions.append(self._to_transaction_response(doc))

            pages = (total + limit - 1) // limit  # Ceiling division

            return PaginatedTransactions(
                transactions=transactions,
                total=total,
                page=page,
                limit=limit,
                pages=pages
            )

        except Exception as e:
            logger.error(f"Error fetching transactions for user {user_id}: {e}")
            raise

    async def search_transactions(
        self, user_id: str, query: str, page: int = 1, limit: int = 20
    ) -> PaginatedTransactions:
        """
        Search transactions by name or category.
        
        Args:
            user_id: The user's Firebase UID
            query: Search query string
            page: Page number
            limit: Results per page
            
        Returns:
            PaginatedTransactions matching the search query
        """
        try:
            skip = (page - 1) * limit

            # Build search filter (case-insensitive regex on name and description)
            search_filter = {
                "user_id": user_id,
                "$or": [
                    {"name": {"$regex": query, "$options": "i"}},
                    {"description": {"$regex": query, "$options": "i"}},
                    {"category": {"$regex": query, "$options": "i"}}
                ]
            }

            # Get total count
            total = await self.transactions_collection.count_documents(search_filter)

            # Get paginated results
            cursor = self.transactions_collection.find(search_filter).sort(
                "date", -1
            ).skip(skip).limit(limit)

            transactions = []
            async for doc in cursor:
                transactions.append(self._to_transaction_response(doc))

            pages = (total + limit - 1) // limit

            return PaginatedTransactions(
                transactions=transactions,
                total=total,
                page=page,
                limit=limit,
                pages=pages
            )

        except Exception as e:
            logger.error(f"Error searching transactions for user {user_id}: {e}")
            raise

    async def filter_transactions(
        self, user_id: str, filters: TransactionFilter
    ) -> PaginatedTransactions:
        """
        Filter transactions based on multiple criteria.
        
        Args:
            user_id: The user's Firebase UID
            filters: TransactionFilter with filter criteria
            
        Returns:
            PaginatedTransactions matching the filters
        """
        try:
            # Build MongoDB filter
            mongo_filter: Dict[str, Any] = {"user_id": user_id}

            if filters.category:
                mongo_filter["category"] = filters.category.value

            if filters.type:
                mongo_filter["type"] = filters.type.value

            if filters.start_date or filters.end_date:
                date_filter = {}
                if filters.start_date:
                    date_filter["$gte"] = datetime.combine(filters.start_date, datetime.min.time())
                if filters.end_date:
                    date_filter["$lte"] = datetime.combine(filters.end_date, datetime.max.time())
                mongo_filter["date"] = date_filter

            if filters.min_amount is not None or filters.max_amount is not None:
                amount_filter = {}
                if filters.min_amount is not None:
                    amount_filter["$gte"] = filters.min_amount
                if filters.max_amount is not None:
                    amount_filter["$lte"] = filters.max_amount
                mongo_filter["amount"] = amount_filter

            if filters.search_query:
                mongo_filter["$or"] = [
                    {"name": {"$regex": filters.search_query, "$options": "i"}},
                    {"description": {"$regex": filters.search_query, "$options": "i"}}
                ]

            # Pagination
            skip = (filters.page - 1) * filters.limit

            # Get total count
            total = await self.transactions_collection.count_documents(mongo_filter)

            # Get filtered transactions
            cursor = self.transactions_collection.find(mongo_filter).sort(
                "date", -1
            ).skip(skip).limit(filters.limit)

            transactions = []
            async for doc in cursor:
                transactions.append(self._to_transaction_response(doc))

            pages = (total + filters.limit - 1) // filters.limit

            return PaginatedTransactions(
                transactions=transactions,
                total=total,
                page=filters.page,
                limit=filters.limit,
                pages=pages
            )

        except Exception as e:
            logger.error(f"Error filtering transactions for user {user_id}: {e}")
            raise

    async def get_transaction_by_id(
        self, user_id: str, transaction_id: str
    ) -> Optional[TransactionResponse]:
        """
        Get a single transaction by ID.
        
        Args:
            user_id: The user's Firebase UID
            transaction_id: Transaction ObjectId as string
            
        Returns:
            TransactionResponse or None if not found
        """
        try:
            doc = await self.transactions_collection.find_one({
                "_id": ObjectId(transaction_id),
                "user_id": user_id
            })

            if doc:
                return self._to_transaction_response(doc)
            return None

        except Exception as e:
            logger.error(f"Error fetching transaction {transaction_id}: {e}")
            raise

    async def update_transaction(
        self, user_id: str, transaction_id: str, update_data: TransactionUpdate
    ) -> Optional[TransactionResponse]:
        """
        Update a transaction.
        
        Args:
            user_id: The user's Firebase UID
            transaction_id: Transaction ObjectId as string
            update_data: Fields to update
            
        Returns:
            Updated TransactionResponse or None if not found
        """
        try:
            # Get only non-None fields
            update_dict = update_data.model_dump(exclude_none=True)
            if not update_dict:
                # No fields to update
                return await self.get_transaction_by_id(user_id, transaction_id)

            update_dict["updated_at"] = datetime.utcnow()

            # Update in MongoDB
            result = await self.transactions_collection.find_one_and_update(
                {"_id": ObjectId(transaction_id), "user_id": user_id},
                {"$set": update_dict},
                return_document=True
            )

            if result:
                # Recalculate balance if amount or type changed
                if "amount" in update_dict or "type" in update_dict:
                    await self._recalculate_and_update_balance(user_id)
                    await self._sync_firestore_cache(user_id)
                # Even if other fields changed, invalidate spending cache to keep chart fresh
                await self._invalidate_spending_cache(user_id)

                return self._to_transaction_response(result)
            return None

        except Exception as e:
            logger.error(f"Error updating transaction {transaction_id}: {e}")
            raise

    async def delete_transaction(
        self, user_id: str, transaction_id: str
    ) -> bool:
        """
        Delete a transaction.
        
        Args:
            user_id: The user's Firebase UID
            transaction_id: Transaction ObjectId as string
            
        Returns:
            True if deleted, False if not found
        """
        try:
            result = await self.transactions_collection.delete_one({
                "_id": ObjectId(transaction_id),
                "user_id": user_id
            })

            if result.deleted_count > 0:
                # Recalculate balance
                await self._recalculate_and_update_balance(user_id)
                await self._sync_firestore_cache(user_id)
                await self._invalidate_spending_cache(user_id)
                return True
            return False

        except Exception as e:
            logger.error(f"Error deleting transaction {transaction_id}: {e}")
            raise

    async def get_transaction_summary(self, user_id: str) -> TransactionSummary:
        """
        Get summary statistics for user's transactions.
        
        Args:
            user_id: The user's Firebase UID
            
        Returns:
            TransactionSummary with aggregated statistics
        """
        try:
            # Aggregate income and expenses
            pipeline = [
                {"$match": {"user_id": user_id}},
                {
                    "$group": {
                        "_id": "$type",
                        "total": {"$sum": "$amount"},
                        "count": {"$sum": 1}
                    }
                }
            ]

            results = await self.transactions_collection.aggregate(pipeline).to_list(None)

            total_income = 0.0
            total_expenses = 0.0
            transaction_count = 0

            for result in results:
                if result["_id"] == TransactionType.INCOME.value:
                    total_income = result["total"]
                    transaction_count += result["count"]
                elif result["_id"] == TransactionType.EXPENSE.value:
                    total_expenses = result["total"]
                    transaction_count += result["count"]

            net_balance = total_income - total_expenses
            average_transaction = (total_income + total_expenses) / transaction_count if transaction_count > 0 else 0.0

            # Get top category by spending
            top_category_pipeline = [
                {"$match": {"user_id": user_id, "type": TransactionType.EXPENSE.value}},
                {
                    "$group": {
                        "_id": "$category",
                        "total": {"$sum": "$amount"}
                    }
                },
                {"$sort": {"total": -1}},
                {"$limit": 1}
            ]

            top_category_result = await self.transactions_collection.aggregate(
                top_category_pipeline
            ).to_list(1)

            top_category = None
            top_category_amount = None
            if top_category_result:
                top_category = top_category_result[0]["_id"]
                top_category_amount = top_category_result[0]["total"]

            return TransactionSummary(
                total_income=total_income,
                total_expenses=total_expenses,
                net_balance=net_balance,
                transaction_count=transaction_count,
                average_transaction=average_transaction,
                top_category=top_category,
                top_category_amount=top_category_amount
            )

        except Exception as e:
            logger.error(f"Error getting transaction summary for user {user_id}: {e}")
            raise

    async def _recalculate_and_update_balance(self, user_id: str):
        """
        Recalculate total balance from all transactions and update Firestore user doc.
        
        Args:
            user_id: The user's Firebase UID
        """
        try:
            # Aggregate total balance (income - expenses)
            pipeline = [
                {"$match": {"user_id": user_id}},
                {
                    "$group": {
                        "_id": "$type",
                        "total": {"$sum": "$amount"}
                    }
                }
            ]

            results = await self.transactions_collection.aggregate(pipeline).to_list(None)

            total_income = 0.0
            total_expenses = 0.0

            for result in results:
                if result["_id"] == TransactionType.INCOME.value:
                    total_income = result["total"]
                elif result["_id"] == TransactionType.EXPENSE.value:
                    total_expenses = result["total"]

            balance = total_income - total_expenses

            # Update Firestore user document (create if doesn't exist)
            try:
                user_ref = self.firestore_db.collection("users").document(user_id)
                user_ref.set({
                    "balance": balance,
                    "updated_at": datetime.utcnow()
                }, merge=True)
                logger.info(f"Updated balance for user {user_id}: {balance}")
            except Exception as firestore_error:
                logger.warning(f"Firestore balance sync failed (non-critical): {firestore_error}")
                # Don't raise - balance calculation succeeded, just Firestore sync failed

        except Exception as e:
            logger.error(f"Error recalculating balance for user {user_id}: {e}")
            raise

    async def _sync_firestore_cache(self, user_id: str):
        """
        Sync last 50 transactions to Firestore cache for quick access.
        Non-blocking - fails silently if Firestore is unavailable.
        
        Args:
            user_id: The user's Firebase UID
        """
        try:
            # Get last 50 transactions from MongoDB
            cursor = self.transactions_collection.find({"user_id": user_id}).sort(
                "date", -1
            ).limit(50)

            transactions = []
            async for doc in cursor:
                # Convert to dict for Firestore
                transaction_dict = {
                    "id": str(doc["_id"]),
                    "name": doc["name"],
                    "amount": doc["amount"],
                    "type": doc["type"],
                    "category": doc["category"],
                    "description": doc.get("description"),
                    "date": doc["date"],
                    "recurring": doc.get("recurring", False),
                    "recurring_frequency": doc.get("recurring_frequency"),
                    "created_at": doc["created_at"]
                }
                transactions.append(transaction_dict)

            # Update Firestore cache collection
            cache_ref = self.firestore_db.collection("users").document(user_id).collection("transactions_cache")
            
            # Clear existing cache (Firestore operations are synchronous in firebase-admin)
            try:
                batch = self.firestore_db.batch()
                docs = cache_ref.limit(100).stream()
                for doc in docs:
                    batch.delete(doc.reference)
                batch.commit()
            except Exception as clear_error:
                logger.warning(f"Error clearing cache for user {user_id}: {clear_error}")

            # Write new cache
            try:
                batch = self.firestore_db.batch()
                for idx, transaction in enumerate(transactions):
                    doc_ref = cache_ref.document(f"tx_{idx}")
                    batch.set(doc_ref, transaction)
                batch.commit()
                logger.info(f"Synced {len(transactions)} transactions to Firestore cache for user {user_id}")
            except Exception as write_error:
                logger.warning(f"Error writing cache for user {user_id}: {write_error}")

        except Exception as e:
            logger.error(f"Error syncing Firestore cache for user {user_id}: {e}")
            # Don't raise - cache sync failure shouldn't break the operation

    async def _invalidate_spending_cache(self, user_id: str):
        """Invalidate cached spending overview data so charts recompute."""
        try:
            HomeService.invalidate_spending_overview_cache(user_id)
        except Exception as e:
            logger.warning(f"Failed to invalidate spending cache for user {user_id}: {e}")

    def _to_transaction_response(self, doc: Dict[str, Any]) -> TransactionResponse:
        """
        Convert MongoDB document to TransactionResponse model.
        
        Args:
            doc: MongoDB document dictionary
            
        Returns:
            TransactionResponse model
        """
        return TransactionResponse(
            id=str(doc["_id"]),
            user_id=doc["user_id"],
            name=doc["name"],
            amount=doc["amount"],
            type=doc["type"],
            category=doc["category"],
            description=doc.get("description"),
            date=doc["date"],
            recurring=doc.get("recurring", False),
            recurring_frequency=doc.get("recurring_frequency"),
            created_at=doc["created_at"],
            updated_at=doc.get("updated_at")
        )


# Singleton instance
_transaction_service: Optional[TransactionService] = None


def get_transaction_service() -> TransactionService:
    """Get or create TransactionService singleton instance."""
    global _transaction_service
    if _transaction_service is None:
        _transaction_service = TransactionService()
    return _transaction_service
