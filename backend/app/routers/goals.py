"""Goals router for managing user financial goals."""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List

from app.models.goal import (
    GoalCreate,
    GoalUpdate,
    GoalResponse,
    GoalStatus
)
from app.services.goal_service import get_goal_service, GoalService
from app.utils.auth import get_current_user

router = APIRouter(
    prefix="/goals",
    tags=["goals"],
    responses={401: {"description": "Unauthorized"}}
)


@router.post("", response_model=GoalResponse, status_code=201)
async def create_goal(
    goal_data: GoalCreate,
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends(get_goal_service)
):
    """
    Create a new financial goal.
    
    - **title**: Goal title (required)
    - **target_amount**: Target amount to save (required, must be > 0)
    - **saved_amount**: Initial saved amount (optional, defaults to 0)
    - **deadline**: Target completion date (optional)
    - **category**: Goal category (Savings, Investment, Purchase, etc.)
    - **description**: Additional description (optional)
    """
    try:
        goal = await goal_service.create_goal(
            user_id=current_user["uid"],
            goal_data=goal_data
        )
        return goal
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[GoalResponse])
async def get_goals(
    status: Optional[GoalStatus] = Query(
        None,
        description="Filter by goal status (active, completed, cancelled)"
    ),
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends(get_goal_service)
):
    """
    Get all goals for the authenticated user.
    
    Optionally filter by status:
    - **active**: Goals in progress
    - **completed**: Achieved goals
    - **cancelled**: Cancelled goals
    """
    try:
        goals = await goal_service.get_goals(
            user_id=current_user["uid"],
            status=status
        )
        return goals
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_goals_summary(
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends(get_goal_service)
):
    """
    Get summary statistics of user's goals.
    
    Returns:
    - Total goals count
    - Active/completed counts
    - Total target and saved amounts
    - Overall progress percentage
    - Goals at risk (overdue or nearing deadline)
    """
    try:
        summary = await goal_service.get_goals_summary(user_id=current_user["uid"])
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{goal_id}", response_model=GoalResponse)
async def get_goal(
    goal_id: str,
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends(get_goal_service)
):
    """
    Get a specific goal by ID.
    
    Returns goal details including:
    - Progress percentage
    - Remaining amount
    - Days remaining until deadline
    - Overdue status
    """
    try:
        goal = await goal_service.get_goal_by_id(
            user_id=current_user["uid"],
            goal_id=goal_id
        )
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        return goal
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{goal_id}", response_model=GoalResponse)
async def update_goal(
    goal_id: str,
    update_data: GoalUpdate,
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends(get_goal_service)
):
    """
    Update a goal.
    
    All fields are optional. Only provided fields will be updated.
    
    - **title**: New goal title
    - **target_amount**: New target amount
    - **saved_amount**: Update saved amount (triggers milestone notifications)
    - **deadline**: New deadline
    - **category**: New category
    - **description**: New description
    - **status**: Change status (active, completed, cancelled)
    
    When saved_amount is updated, milestone notifications are triggered at 25%, 50%, 75%, and 100%.
    Goal is automatically marked as completed when 100% progress is reached.
    """
    try:
        goal = await goal_service.update_goal(
            user_id=current_user["uid"],
            goal_id=goal_id,
            update_data=update_data
        )
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        return goal
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{goal_id}", status_code=204)
async def delete_goal(
    goal_id: str,
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends(get_goal_service)
):
    """
    Delete a goal.
    
    This permanently removes the goal and cannot be undone.
    Consider updating status to 'cancelled' instead for record keeping.
    """
    try:
        deleted = await goal_service.delete_goal(
            user_id=current_user["uid"],
            goal_id=goal_id
        )
        if not deleted:
            raise HTTPException(status_code=404, detail="Goal not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{goal_id}/add", response_model=GoalResponse)
async def add_to_goal(
    goal_id: str,
    amount: float = Query(..., description="Amount to add (positive) or subtract (negative)"),
    current_user: dict = Depends(get_current_user),
    goal_service: GoalService = Depends(get_goal_service)
):
    """
    Add or subtract an amount from a goal's saved amount.
    
    - Positive amount: Add to savings
    - Negative amount: Subtract from savings (won't go below 0)
    
    Triggers milestone notifications at 25%, 50%, 75%, and 100%.
    """
    try:
        goal = await goal_service.add_to_goal(
            user_id=current_user["uid"],
            goal_id=goal_id,
            amount=amount
        )
        if not goal:
            raise HTTPException(status_code=404, detail="Goal not found")
        return goal
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
