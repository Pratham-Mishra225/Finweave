"""Insights router for financial analytics endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
import logging

from app.utils.auth import get_current_user
from app.services.insights_service import get_insights_service, InsightsService
from app.models.insight import (
    InsightCard,
    CategoryBreakdown,
    CategorySummary,
    MonthlyComparison,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("/cards", response_model=List[InsightCard])
async def get_insight_cards(
    current_user: dict = Depends(get_current_user),
    insights_service: InsightsService = Depends(get_insights_service)
):
    """
    Get 4 AI-generated insight cards based on user's financial data.
    
    Returns insights like overspending forecasts, savings trends,
    subscription alerts, and category trends.
    """
    try:
        user_id = current_user["uid"]
        cards = await insights_service.get_insight_cards(user_id)
        return cards
    except Exception as e:
        logger.error(f"Error getting insight cards: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate insight cards"
        )


@router.get("/category-breakdown", response_model=List[CategoryBreakdown])
async def get_category_breakdown(
    limit: int = 5,
    current_user: dict = Depends(get_current_user),
    insights_service: InsightsService = Depends(get_insights_service)
):
    """
    Get category breakdown for bar chart visualization.
    
    Returns spending by category for the current month with
    amounts, percentages, transaction counts, and trends.
    
    Args:
        limit: Number of categories to return (default 5)
    """
    try:
        user_id = current_user["uid"]
        breakdown = await insights_service.get_category_breakdown(user_id, limit)
        return breakdown
    except Exception as e:
        logger.error(f"Error getting category breakdown: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get category breakdown"
        )


@router.get("/category-summary", response_model=List[CategorySummary])
async def get_category_summary(
    limit: int = 3,
    current_user: dict = Depends(get_current_user),
    insights_service: InsightsService = Depends(get_insights_service)
):
    """
    Get category summary cards with month-over-month comparison.
    
    Returns top spending categories with current/previous month
    amounts, change percentages, and trends.
    
    Args:
        limit: Number of categories to return (default 3)
    """
    try:
        user_id = current_user["uid"]
        summary = await insights_service.get_category_summary(user_id, limit)
        return summary
    except Exception as e:
        logger.error(f"Error getting category summary: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get category summary"
        )


@router.get("/monthly-comparison", response_model=MonthlyComparison)
async def get_monthly_comparison(
    current_user: dict = Depends(get_current_user),
    insights_service: InsightsService = Depends(get_insights_service)
):
    """
    Get month-over-month expense comparison.
    
    Compares current month's expenses with the previous month
    and calculates the change amount and percentage.
    """
    try:
        user_id = current_user["uid"]
        comparison = await insights_service.get_monthly_comparison(user_id)
        return comparison
    except Exception as e:
        logger.error(f"Error getting monthly comparison: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get monthly comparison"
        )


@router.get("/dashboard", response_model=Dict[str, Any])
async def get_insights_dashboard(
    current_user: dict = Depends(get_current_user),
    insights_service: InsightsService = Depends(get_insights_service)
):
    """
    Get complete insights dashboard data in a single request.
    
    Returns all insight cards, category breakdown, category summary,
    and monthly comparison in one response for efficient loading.
    """
    try:
        user_id = current_user["uid"]
        
        # Check cache first
        cached = await insights_service.get_cached_insights(user_id)
        if cached:
            logger.info(f"Returning cached insights for user {user_id}")
            return {
                "insight_cards": cached.get("insight_cards", []),
                "category_breakdown": cached.get("category_breakdown", []),
                "category_summary": cached.get("category_summary", []),
                "monthly_comparison": cached.get("monthly_comparison", {}),
                "from_cache": True
            }
        
        # Generate fresh insights
        insight_cards = await insights_service.get_insight_cards(user_id)
        category_breakdown = await insights_service.get_category_breakdown(user_id)
        category_summary = await insights_service.get_category_summary(user_id)
        monthly_comparison = await insights_service.get_monthly_comparison(user_id)
        
        # Convert to serializable format
        dashboard_data = {
            "insight_cards": [card.model_dump() for card in insight_cards],
            "category_breakdown": [cb.model_dump() for cb in category_breakdown],
            "category_summary": [cs.model_dump() for cs in category_summary],
            "monthly_comparison": monthly_comparison.model_dump(),
            "from_cache": False
        }
        
        # Cache the results
        await insights_service.cache_insights(user_id, dashboard_data)
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error getting insights dashboard: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get insights dashboard"
        )


@router.get("/ai", response_model=Dict[str, Any])
async def get_ai_insights(
    refresh: bool = False,
    current_user: dict = Depends(get_current_user),
    insights_service: InsightsService = Depends(get_insights_service)
):
    """
    Get AI-powered financial insights using Gemini.
    
    Returns personalized insight cards and trend analysis generated
    by analyzing the user's transactions, goals, and financial patterns.
    This endpoint provides deeper, more contextual insights compared
    to the regular insights endpoint.
    """
    try:
        user_id = current_user["uid"]
        return await insights_service.get_ai_insights(user_id)
    except Exception as e:
        logger.error(f"Error getting AI insights: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate AI insights"
        )


@router.get("/ai/dashboard", response_model=Dict[str, Any])
async def get_ai_enhanced_dashboard(
    current_user: dict = Depends(get_current_user),
    insights_service: InsightsService = Depends(get_insights_service)
):
    """Return the latest cached AI dashboard without regenerating it."""
    try:
        user_id = current_user["uid"]
        return await insights_service.get_ai_dashboard(user_id)
    except Exception as e:
        logger.error(f"Error getting AI-enhanced dashboard: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to get AI-enhanced dashboard"
        )


@router.post("/ai/dashboard/regenerate", response_model=Dict[str, Any])
async def regenerate_ai_dashboard(
    current_user: dict = Depends(get_current_user),
    insights_service: InsightsService = Depends(get_insights_service)
):
    """Force regeneration of AI dashboard and persist the snapshot."""
    try:
        user_id = current_user["uid"]
        return await insights_service.get_ai_dashboard(user_id, force_refresh=True)
    except Exception as e:
        logger.error(f"Error regenerating AI dashboard: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to regenerate AI dashboard"
        )
