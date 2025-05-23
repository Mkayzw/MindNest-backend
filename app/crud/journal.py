# app/crud/journal.py
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.journal import JournalEntry
from app.schemas.journal import JournalCreate, Journal

def create_journal_entry(db: Session, journal: JournalCreate, user_id: int) -> JournalEntry:
    db_journal = JournalEntry(**journal.model_dump(), user_id=user_id)
    db.add(db_journal)
    db.commit()
    db.refresh(db_journal)
    return db_journal

def get_journal_entry(db: Session, journal_id: int, user_id: int) -> Optional[JournalEntry]:
    return db.query(JournalEntry).filter(JournalEntry.id == journal_id, JournalEntry.user_id == user_id).first()

def get_journal_entries_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[JournalEntry]:
    return db.query(JournalEntry).filter(JournalEntry.user_id == user_id).offset(skip).limit(limit).all()

def update_journal_entry(db: Session, journal_id: int, journal_update: JournalCreate, user_id: int) -> Optional[JournalEntry]:
    db_journal = db.query(JournalEntry).filter(JournalEntry.id == journal_id, JournalEntry.user_id == user_id).first()
    if db_journal:
        update_data = journal_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_journal, key, value)
        db.commit()
        db.refresh(db_journal)
    return db_journal

def delete_journal_entry(db: Session, journal_id: int, user_id: int) -> Optional[JournalEntry]:
    db_journal = db.query(JournalEntry).filter(JournalEntry.id == journal_id, JournalEntry.user_id == user_id).first()
    if db_journal:
        db.delete(db_journal)
        db.commit()
    return db_journal