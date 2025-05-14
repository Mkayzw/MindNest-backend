# mental_health.py
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

# Mood Log Schemas
class MoodLogBase(BaseModel):
    mood_level: int  # Scale 1-5
    note: Optional[str] = None

class MoodLogCreate(MoodLogBase):
    pass

class MoodLog(MoodLogBase):
    id: int
    user_id: int
    logged_at: datetime

    class Config:
        orm_mode = True

# Stress Event Schemas
class StressEventBase(BaseModel):
    description: str
    trigger_tag: Optional[str] = None
    intensity: int  # Scale 1-5

class StressEventCreate(StressEventBase):
    pass

class StressEvent(StressEventBase):
    id: int
    user_id: int
    timestamp: datetime

    class Config:
        orm_mode = True

# Self-Care Activity Schemas
class SelfCareActivityBase(BaseModel):
    name: str
    description: Optional[str] = None
    scheduled_for: Optional[datetime] = None

class SelfCareActivityCreate(SelfCareActivityBase):
    pass

class SelfCareActivityUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_completed: Optional[bool] = None
    scheduled_for: Optional[datetime] = None

class SelfCareActivity(SelfCareActivityBase):
    id: int
    user_id: int
    is_completed: bool
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        orm_mode = True
