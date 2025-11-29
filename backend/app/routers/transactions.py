"""Transactions API router."""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional

from app.models.transaction import (
    TransactionCreate,
    TransactionResponse,
    TransactionFilter,
    TransactionSummary,
    TransactionUpdate,
    PaginatedTransactions,
    TransactionCategory,
    TransactionType
)
from app.services.transaction_service import get_transaction_service, TransactionService
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    transaction: TransactionCreate,
    current_user: dict = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service)
):
    """
    Create a new transaction.
    
    Creates transaction in MongoDB (source of truth), updates Firestore cache,
    and recalculates user balance.
    """
    try:
        user_id = current_user["uid"]
        result = await service.create_transaction(user_id, transaction)
        return result
    except Exception as e:
        logger.error(f"Error creating transaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create transaction"
        )


@router.get("", response_model=PaginatedTransactions)
async def get_transactions(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: dict = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service)
):
    """
    Get paginated list of transactions.
    
    Returns transactions sorted by date (newest first) with pagination.
    """
    try:
        user_id = current_user["uid"]
        result = await service.get_transactions_paginated(user_id, page, limit)
        return result
    except Exception as e:
        logger.error(f"Error fetching transactions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch transactions"
        )


@router.get("/search", response_model=PaginatedTransactions)
async def search_transactions(
    q: str = Query(..., min_length=1, description="Search query"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service)
):
    """
    Search transactions by name, description, or category.
    
    Performs case-insensitive regex search across name, description, and category fields.
    """
    try:
        user_id = current_user["uid"]
        result = await service.search_transactions(user_id, q, page, limit)
        return result
    except Exception as e:
        logger.error(f"Error searching transactions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search transactions"
        )


@router.get("/filter", response_model=PaginatedTransactions)
async def filter_transactions(
    category: Optional[TransactionCategory] = Query(None, description="Filter by category"),
    type: Optional[TransactionType] = Query(None, description="Filter by type (income/expense)"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    min_amount: Optional[float] = Query(None, ge=0, description="Minimum amount"),
    max_amount: Optional[float] = Query(None, ge=0, description="Maximum amount"),
    search_query: Optional[str] = Query(None, description="Search in name/description"),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service)
):
    """
    Filter transactions by multiple criteria.
    
    Supports filtering by category, type, date range, amount range, and search query.
    All filters can be combined.
    """
    try:
        from datetime import datetime
        
        # Parse date strings if provided
        parsed_start_date = None
        parsed_end_date = None
        
        if start_date:
            try:
                parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid start_date format. Use YYYY-MM-DD"
                )
        
        if end_date:
            try:
                parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid end_date format. Use YYYY-MM-DD"
                )
        
        user_id = current_user["uid"]
        
        filters = TransactionFilter(
            category=category,
            type=type,
            start_date=parsed_start_date,
            end_date=parsed_end_date,
            min_amount=min_amount,
            max_amount=max_amount,
            search_query=search_query,
            page=page,
            limit=limit
        )
        
        result = await service.filter_transactions(user_id, filters)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error filtering transactions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to filter transactions"
        )


@router.get("/summary", response_model=TransactionSummary)
async def get_transaction_summary(
    current_user: dict = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service)
):
    """
    Get transaction summary statistics.
    
    Returns aggregated data including total income, expenses, net balance,
    transaction count, average transaction, and top spending category.
    """
    try:
        user_id = current_user["uid"]
        result = await service.get_transaction_summary(user_id)
        return result
    except Exception as e:
        logger.error(f"Error getting transaction summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get transaction summary"
        )


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: str,
    current_user: dict = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service)
):
    """
    Get a single transaction by ID.
    
    Returns 404 if transaction not found or doesn't belong to the user.
    """
    try:
        user_id = current_user["uid"]
        result = await service.get_transaction_by_id(user_id, transaction_id)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching transaction {transaction_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch transaction"
        )


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: str,
    update_data: TransactionUpdate,
    current_user: dict = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service)
):
    """
    Update a transaction.
    
    Only updates fields that are provided (non-null).
    Recalculates balance if amount or type is changed.
    """
    try:
        user_id = current_user["uid"]
        result = await service.update_transaction(user_id, transaction_id, update_data)
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating transaction {transaction_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update transaction"
        )


@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transaction(
    transaction_id: str,
    current_user: dict = Depends(get_current_user),
    service: TransactionService = Depends(get_transaction_service)
):
    """
    Delete a transaction.
    
    Recalculates user balance after deletion.
    Returns 404 if transaction not found.
    """
    try:
        user_id = current_user["uid"]
        success = await service.delete_transaction(user_id, transaction_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting transaction {transaction_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete transaction"
        )
