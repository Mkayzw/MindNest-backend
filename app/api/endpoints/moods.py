# app/api/endpoints/moods.py
from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import schemas, crud, models
from app.api.deps import get_db, get_current_active_user

router = APIRouter()

@router.post("/", response_model=schemas.MoodLog)
def create_mood_log(
    mood_log: schemas.MoodLogCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Create a new mood log entry
    """
    return crud.mental_health.create_mood_log(db, mood_log, current_user.id)

@router.get("/", response_model=List[schemas.MoodLog])
def read_mood_logs(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Retrieve mood logs for the current user
    """
    # Convert date to datetime if provided
    start_datetime = datetime.combine(start_date, datetime.min.time()) if start_date else None
    end_datetime = datetime.combine(end_date, datetime.max.time()) if end_date else None
    
    return crud.mental_health.get_mood_logs_by_user(
        db, 
        user_id=current_user.id, 
        skip=skip, 
        limit=limit, 
        start_date=start_datetime, 
        end_date=end_datetime
    )

@router.get("/{mood_log_id}", response_model=schemas.MoodLog)
def read_mood_log(
    mood_log_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Get a specific mood log by ID
    """
    mood_log = crud.mental_health.get_mood_log(db, mood_log_id, current_user.id)
    if not mood_log:
        raise HTTPException(status_code=404, detail="Mood log not found")
    return mood_log

@router.delete("/{mood_log_id}", response_model=schemas.MoodLog)
def delete_mood_log(
    mood_log_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Delete a mood log
    """
    mood_log = crud.mental_health.delete_mood_log(db, mood_log_id, current_user.id)
    if not mood_log:
        raise HTTPException(status_code=404, detail="Mood log not found")
    return mood_log 