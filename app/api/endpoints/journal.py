# app/api/endpoints/journal.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app import crud, schemas, models
from app.database import get_db
from app.api import deps # Assuming a deps.py for dependencies like get_current_active_user

router = APIRouter()

@router.post("/", response_model=schemas.JournalRead, status_code=status.HTTP_201_CREATED)
def create_journal(
    *, 
    db: Session = Depends(get_db),
    journal_in: schemas.JournalCreate,
    current_user: models.User = Depends(deps.get_current_active_user) # Placeholder for actual auth dependency
):
    """
    Create new journal entry.
    """
    journal = crud.journal.create_journal_entry(db=db, journal=journal_in, user_id=current_user.id)
    return journal

@router.get("/", response_model=List[schemas.JournalRead])
def read_journals(
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    Retrieve journal entries for the current user.
    """
    journals = crud.journal.get_journal_entries_by_user(db=db, user_id=current_user.id, skip=skip, limit=limit)
    return journals

@router.get("/{journal_id}", response_model=schemas.JournalRead)
def read_journal(
    *, 
    db: Session = Depends(get_db),
    journal_id: int,
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    Get a specific journal entry by ID.
    """
    journal = crud.journal.get_journal_entry(db=db, journal_id=journal_id, user_id=current_user.id)
    if not journal:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    return journal

@router.put("/{journal_id}", response_model=schemas.JournalRead)
def update_journal(
    *, 
    db: Session = Depends(get_db),
    journal_id: int,
    journal_in: schemas.JournalCreate, # Using JournalCreate for update, can be a specific JournalUpdate schema
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    Update a journal entry.
    """
    journal = crud.journal.get_journal_entry(db=db, journal_id=journal_id, user_id=current_user.id)
    if not journal:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    journal = crud.journal.update_journal_entry(db=db, journal_id=journal_id, journal_update=journal_in, user_id=current_user.id)
    return journal

@router.delete("/{journal_id}", response_model=schemas.JournalRead)
def delete_journal(
    *, 
    db: Session = Depends(get_db),
    journal_id: int,
    current_user: models.User = Depends(deps.get_current_active_user)
):
    """
    Delete a journal entry.
    """
    journal = crud.journal.get_journal_entry(db=db, journal_id=journal_id, user_id=current_user.id)
    if not journal:
        raise HTTPException(status_code=404, detail="Journal entry not found")
    deleted_journal = crud.journal.delete_journal_entry(db=db, journal_id=journal_id, user_id=current_user.id)
    return deleted_journal