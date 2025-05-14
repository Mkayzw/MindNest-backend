# mental_health.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Boolean, Float
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base

class MoodLog(Base):
    __tablename__ = "mood_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    mood_level = Column(Integer, nullable=False)  # Scale 1-5
    note = Column(Text, nullable=True)
    logged_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="mood_logs")

class StressEvent(Base):
    __tablename__ = "stress_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    description = Column(Text, nullable=False)
    trigger_tag = Column(String, nullable=True)
    intensity = Column(Integer, nullable=False)  # Scale 1-5
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="stress_events")

class SelfCareActivity(Base):
    __tablename__ = "self_care_activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    is_completed = Column(Boolean, default=False)
    scheduled_for = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="self_care_activities")
