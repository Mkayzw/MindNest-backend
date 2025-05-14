# app/api/endpoints/self_care.py
from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import schemas, crud, models
from app.api.deps import get_db, get_current_active_user

router = APIRouter()

@router.post("/", response_model=schemas.SelfCareActivity)
def create_self_care_activity(
    activity: schemas.SelfCareActivityCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Create a new self-care activity
    """
    return crud.mental_health.create_self_care_activity(db, activity, current_user.id)

@router.get("/", response_model=List[schemas.SelfCareActivity])
def read_self_care_activities(
    skip: int = 0,
    limit: int = 100,
    completed: Optional[bool] = None,
    scheduled_after: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Retrieve self-care activities for the current user
    """
    # Convert date to datetime if provided
    scheduled_after_datetime = datetime.combine(scheduled_after, datetime.min.time()) if scheduled_after else None
    
    return crud.mental_health.get_self_care_activities_by_user(
        db, 
        user_id=current_user.id, 
        skip=skip, 
        limit=limit, 
        completed=completed,
        scheduled_after=scheduled_after_datetime
    )

@router.get("/{activity_id}", response_model=schemas.SelfCareActivity)
def read_self_care_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get a specific self-care activity by ID
    """
    activity = crud.mental_health.get_self_care_activity(db, activity_id, current_user.id)
    if not activity:
        raise HTTPException(status_code=404, detail="Self-care activity not found")
    return activity

@router.patch("/{activity_id}", response_model=schemas.SelfCareActivity)
def update_self_care_activity(
    activity_id: int,
    activity_update: schemas.SelfCareActivityUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Update a self-care activity
    """
    updated_activity = crud.mental_health.update_self_care_activity(
        db, activity_id, activity_update, current_user.id
    )
    if not updated_activity:
        raise HTTPException(status_code=404, detail="Self-care activity not found")
    return updated_activity

@router.delete("/{activity_id}", response_model=schemas.SelfCareActivity)
def delete_self_care_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Delete a self-care activity
    """
    activity = crud.mental_health.delete_self_care_activity(db, activity_id, current_user.id)
    if not activity:
        raise HTTPException(status_code=404, detail="Self-care activity not found")
    return activity 