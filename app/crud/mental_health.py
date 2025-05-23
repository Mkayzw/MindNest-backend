from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import func, extract

from app.models.mental_health import MoodLog, StressEvent, SelfCareActivity
from app.schemas.mental_health import (
    MoodLogCreate, 
    StressEventCreate, 
    SelfCareActivityCreate,
    SelfCareActivityUpdate
)

# Mood Log CRUD operations
def create_mood_log(db: Session, mood_log: MoodLogCreate, user_id: int) -> MoodLog:
    db_mood_log = MoodLog(**mood_log.model_dump(), user_id=user_id)
    db.add(db_mood_log)
    db.commit()
    db.refresh(db_mood_log)
    return db_mood_log

def get_mood_log(db: Session, mood_log_id: int, user_id: int) -> Optional[MoodLog]:
    return db.query(MoodLog).filter(MoodLog.id == mood_log_id, MoodLog.user_id == user_id).first()

def get_mood_logs_by_user(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100, 
    start_date: Optional[datetime] = None, 
    end_date: Optional[datetime] = None
) -> List[MoodLog]:
    query = db.query(MoodLog).filter(MoodLog.user_id == user_id)
    
    if start_date:
        query = query.filter(MoodLog.logged_at >= start_date)
    if end_date:
        query = query.filter(MoodLog.logged_at <= end_date)
        
    return query.order_by(MoodLog.logged_at.desc()).offset(skip).limit(limit).all()

def delete_mood_log(db: Session, mood_log_id: int, user_id: int) -> Optional[MoodLog]:
    db_mood_log = get_mood_log(db, mood_log_id, user_id)
    if db_mood_log:
        db.delete(db_mood_log)
        db.commit()
    return db_mood_log

# Stress Event CRUD operations
def create_stress_event(db: Session, stress_event: StressEventCreate, user_id: int) -> StressEvent:
    db_stress_event = StressEvent(**stress_event.model_dump(), user_id=user_id)
    db.add(db_stress_event)
    db.commit()
    db.refresh(db_stress_event)
    return db_stress_event

def get_stress_event(db: Session, stress_event_id: int, user_id: int) -> Optional[StressEvent]:
    return db.query(StressEvent).filter(
        StressEvent.id == stress_event_id, 
        StressEvent.user_id == user_id
    ).first()

def get_stress_events_by_user(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100, 
    trigger_tag: Optional[str] = None, 
    start_date: Optional[datetime] = None, 
    end_date: Optional[datetime] = None
) -> List[StressEvent]:
    query = db.query(StressEvent).filter(StressEvent.user_id == user_id)
    
    if trigger_tag:
        query = query.filter(StressEvent.trigger_tag == trigger_tag)
    if start_date:
        query = query.filter(StressEvent.timestamp >= start_date)
    if end_date:
        query = query.filter(StressEvent.timestamp <= end_date)
        
    return query.order_by(StressEvent.timestamp.desc()).offset(skip).limit(limit).all()

def delete_stress_event(db: Session, stress_event_id: int, user_id: int) -> Optional[StressEvent]:
    db_stress_event = get_stress_event(db, stress_event_id, user_id)
    if db_stress_event:
        db.delete(db_stress_event)
        db.commit()
    return db_stress_event

# Self-Care Activity CRUD operations
def create_self_care_activity(db: Session, activity: SelfCareActivityCreate, user_id: int) -> SelfCareActivity:
    db_activity = SelfCareActivity(**activity.model_dump(), user_id=user_id)
    db.add(db_activity)
    db.commit()
    db.refresh(db_activity)
    return db_activity

def get_self_care_activity(db: Session, activity_id: int, user_id: int) -> Optional[SelfCareActivity]:
    return db.query(SelfCareActivity).filter(
        SelfCareActivity.id == activity_id, 
        SelfCareActivity.user_id == user_id
    ).first()

def get_self_care_activities_by_user(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100, 
    completed: Optional[bool] = None, 
    scheduled_after: Optional[datetime] = None
) -> List[SelfCareActivity]:
    query = db.query(SelfCareActivity).filter(SelfCareActivity.user_id == user_id)
    
    if completed is not None:
        query = query.filter(SelfCareActivity.is_completed == completed)
    if scheduled_after:
        query = query.filter(SelfCareActivity.scheduled_for >= scheduled_after)
        
    return query.order_by(SelfCareActivity.created_at.desc()).offset(skip).limit(limit).all()

def update_self_care_activity(
    db: Session, 
    activity_id: int, 
    activity_update: SelfCareActivityUpdate, 
    user_id: int
) -> Optional[SelfCareActivity]:
    db_activity = get_self_care_activity(db, activity_id, user_id)
    if db_activity:
        update_data = activity_update.model_dump(exclude_unset=True)
        
        # If marking as completed, set the completed_at timestamp
        if update_data.get("is_completed") and not db_activity.is_completed:
            update_data["completed_at"] = datetime.utcnow()
        # If marking as not completed, clear the completed_at timestamp
        elif update_data.get("is_completed") is False:
            update_data["completed_at"] = None
            
        for key, value in update_data.items():
            setattr(db_activity, key, value)
            
        db.commit()
        db.refresh(db_activity)
    return db_activity

def delete_self_care_activity(db: Session, activity_id: int, user_id: int) -> Optional[SelfCareActivity]:
    db_activity = get_self_care_activity(db, activity_id, user_id)
    if db_activity:
        db.delete(db_activity)
        db.commit()
    return db_activity

# Analytics Functions
def get_mood_trend(
    db: Session, 
    user_id: int, 
    period: str = "week", 
    days: int = 30
) -> List[Dict[str, Any]]:
    """
    Get mood trends over time (daily, weekly, monthly)
    
    period: 'day', 'week', or 'month'
    days: number of days to look back
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    if period == "day":
        # Daily average
        result = db.query(
            func.date(MoodLog.logged_at).label("date"),
            func.avg(MoodLog.mood_level).label("average_mood")
        ).filter(
            MoodLog.user_id == user_id,
            MoodLog.logged_at >= start_date
        ).group_by(
            func.date(MoodLog.logged_at)
        ).order_by(
            func.date(MoodLog.logged_at)
        ).all()
        
        return [{"date": str(r.date), "average_mood": float(r.average_mood)} for r in result]
        
    elif period == "week":
        # Weekly average
        result = db.query(
            extract('year', MoodLog.logged_at).label('year'),
            extract('week', MoodLog.logged_at).label('week'),
            func.avg(MoodLog.mood_level).label("average_mood")
        ).filter(
            MoodLog.user_id == user_id,
            MoodLog.logged_at >= start_date
        ).group_by(
            'year', 'week'
        ).order_by(
            'year', 'week'
        ).all()
        
        return [{"year_week": f"{int(r.year)}-W{int(r.week)}", "average_mood": float(r.average_mood)} for r in result]
        
    elif period == "month":
        # Monthly average
        result = db.query(
            extract('year', MoodLog.logged_at).label('year'),
            extract('month', MoodLog.logged_at).label('month'),
            func.avg(MoodLog.mood_level).label("average_mood")
        ).filter(
            MoodLog.user_id == user_id,
            MoodLog.logged_at >= start_date
        ).group_by(
            'year', 'month'
        ).order_by(
            'year', 'month'
        ).all()
        
        return [{"year_month": f"{int(r.year)}-{int(r.month)}", "average_mood": float(r.average_mood)} for r in result]
    
    return []

def get_stress_patterns(
    db: Session, 
    user_id: int, 
    days: int = 30
) -> List[Dict[str, Any]]:
    """Get patterns in stress triggers"""
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get frequencies of stress trigger tags
    result = db.query(
        StressEvent.trigger_tag,
        func.count(StressEvent.id).label("frequency"),
        func.avg(StressEvent.intensity).label("average_intensity")
    ).filter(
        StressEvent.user_id == user_id,
        StressEvent.timestamp >= start_date,
        StressEvent.trigger_tag != None
    ).group_by(
        StressEvent.trigger_tag
    ).order_by(
        func.count(StressEvent.id).desc()
    ).all()
    
    return [
        {
            "trigger_tag": r.trigger_tag, 
            "frequency": r.frequency, 
            "average_intensity": float(r.average_intensity)
        } 
        for r in result
    ]

def get_journaling_streak(db: Session, user_id: int) -> Dict[str, Any]:
    """Calculate the current journaling streak"""
    from app.models.journal import JournalEntry
    
    # Get dates of journal entries in descending order
    journal_dates = db.query(
        func.date(JournalEntry.created_at).label("entry_date")
    ).filter(
            JournalEntry.user_id == user_id
    ).distinct().order_by(
        func.date(JournalEntry.created_at).desc()
    ).all()
    
    if not journal_dates:
        return {"current_streak": 0, "longest_streak": 0}
    
    # Convert to list of date objects
    dates = [entry.entry_date for entry in journal_dates]
    
    # Calculate current streak
    current_streak = 1
    today = datetime.utcnow().date()
    
    # Check if there's an entry for today
    if dates[0] != today:
        yesterday = today - timedelta(days=1)
        # If no entry for today and yesterday, streak is 0
        if dates[0] != yesterday:
            return {"current_streak": 0, "longest_streak": 0}
    
    # Calculate streak by checking for consecutive days
    for i in range(len(dates) - 1):
        if dates[i] - dates[i+1] == timedelta(days=1):
            current_streak += 1
        else:
            break
    
    # For longest streak, we'd need to check all date ranges
    # This is a simplified version that just returns the current streak
    return {"current_streak": current_streak, "longest_streak": current_streak} 