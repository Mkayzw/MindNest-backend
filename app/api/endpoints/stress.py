# app/api/endpoints/stress.py
from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import schemas, crud, models
from app.api.deps import get_db, get_current_active_user

router = APIRouter()

@router.post("/", response_model=schemas.StressEvent)
def create_stress_event(
    stress_event: schemas.StressEventCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Create a new stress event entry
    """
    return crud.mental_health.create_stress_event(db, stress_event, current_user.id)

@router.get("/", response_model=List[schemas.StressEvent])
def read_stress_events(
    skip: int = 0,
    limit: int = 100,
    trigger_tag: Optional[str] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Retrieve stress events for the current user
    """
    # Convert date to datetime if provided
    start_datetime = datetime.combine(start_date, datetime.min.time()) if start_date else None
    end_datetime = datetime.combine(end_date, datetime.max.time()) if end_date else None
    
    return crud.mental_health.get_stress_events_by_user(
        db, 
        user_id=current_user.id, 
        skip=skip, 
        limit=limit, 
        trigger_tag=trigger_tag,
        start_date=start_datetime, 
        end_date=end_datetime
    )

@router.get("/{stress_event_id}", response_model=schemas.StressEvent)
def read_stress_event(
    stress_event_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get a specific stress event by ID
    """
    stress_event = crud.mental_health.get_stress_event(db, stress_event_id, current_user.id)
    if not stress_event:
        raise HTTPException(status_code=404, detail="Stress event not found")
    return stress_event

@router.delete("/{stress_event_id}", response_model=schemas.StressEvent)
def delete_stress_event(
    stress_event_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Delete a stress event
    """
    stress_event = crud.mental_health.delete_stress_event(db, stress_event_id, current_user.id)
    if not stress_event:
        raise HTTPException(status_code=404, detail="Stress event not found")
    return stress_event 