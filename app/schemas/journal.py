# app/schemas/journal.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class JournalBase(BaseModel):
    title: str
    content: str
    mood: Optional[str] = None

class JournalCreate(JournalBase):
    pass

class Journal(JournalBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class JournalRead(Journal):
    pass