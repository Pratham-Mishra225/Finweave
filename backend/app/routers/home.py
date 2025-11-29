"""Home page router for dashboard endpoints."""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any

from app.services.home_service import home_service
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/home",
    tags=["Home Dashboard"]
)


@router.get(
    "/dashboard",
    response_model=Dict[str, Any],
    summary="Get dashboard data",
    description="""
    Get complete home dashboard data including:
    - Current balance
    - Recent 4 transactions
    - AI insight alert (forecast/warning)
    - 30-day spending overview (weekly breakdown)
    """
)
async def get_dashboard(
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get complete dashboard data for the home page.
    
    Returns:
        - balance: Current account balance
        - recent_transactions: List of last 4 transactions
        - spending_overview: 30-day spending chart data (4 weeks)
        - ai_insight: AI-generated insight alert
    """
    try:
        user_id = current_user["uid"]
        dashboard_data = await home_service.get_dashboard_data(user_id)
        
        logger.info(f"Dashboard data fetched for user {user_id}")
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error fetching dashboard data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch dashboard data"
        )


@router.get(
    "/balance",
    response_model=Dict[str, float],
    summary="Get user balance",
    description="Get current user balance from Firestore"
)
async def get_balance(
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, float]:
    """Get current user balance."""
    try:
        user_id = current_user["uid"]
        balance = await home_service.get_user_balance(user_id)
        
        return {"balance": balance}
        
    except Exception as e:
        logger.error(f"Error fetching balance: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch balance"
        )


@router.get(
    "/spending-overview",
    response_model=Dict[str, Any],
    summary="Get spending overview",
    description="Get 30-day spending overview with weekly breakdown"
)
async def get_spending_overview(
    days: int = 30,
    current_user: Dict = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Get spending overview chart data.
    
    Args:
        days: Number of days to analyze (default: 30)
    
    Returns:
        Dictionary with labels, data, and total spending
    """
    try:
        user_id = current_user["uid"]
        overview = await home_service.get_spending_overview(user_id, days)
        
        return overview
        
    except Exception as e:
        logger.error(f"Error fetching spending overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch spending overview"
        )


@router.get(
    "/recent-transactions",
    summary="Get recent transactions",
    description="Get the most recent transactions (default: 4)"
)
async def get_recent_transactions(
    limit: int = 4,
    current_user: Dict = Depends(get_current_user)
):
    """
    Get recent transactions from Firestore cache.
    
    Args:
        limit: Number of transactions to return (default: 4)
    
    Returns:
        List of recent transactions
    """
    try:
        user_id = current_user["uid"]
        transactions = await home_service.get_recent_transactions(user_id, limit)
        
        return {"transactions": transactions}
        
    except Exception as e:
        logger.error(f"Error fetching recent transactions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch recent transactions"
        )


@router.get(
    "/ai-insight",
    summary="Get AI insight alert",
    description="Get the most recent AI-generated insight alert"
)
async def get_ai_insight(
    current_user: Dict = Depends(get_current_user)
):
    """
    Get AI-generated insight alert for dashboard.
    
    Returns:
        Latest urgent/warning insight or default forecast
    """
    try:
        user_id = current_user["uid"]
        insight = await home_service.get_ai_insight_alert(user_id)
        
        return insight
        
    except Exception as e:
        logger.error(f"Error fetching AI insight: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch AI insight"
        )
