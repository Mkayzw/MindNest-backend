from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import crud, models
from app.api.deps import get_db, get_current_active_user

router = APIRouter()

@router.get("/mood-trend")
def get_mood_trend(
    period: str = Query("week", regex="^(day|week|month)$"),
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    Get mood trends over time (daily, weekly, monthly)
    
    - **period**: Aggregation period ('day', 'week', or 'month')
    - **days**: Number of days to look back (1-365)
    """
    return crud.mental_health.get_mood_trend(db, current_user.id, period, days)

@router.get("/stress-patterns")
def get_stress_patterns(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
) -> List[Dict[str, Any]]:
    """
    Get patterns in stress triggers
    
    - **days**: Number of days to look back (1-365)
    """
    return crud.mental_health.get_stress_patterns(db, current_user.id, days)

@router.get("/journaling-streak")
def get_journaling_streak(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get the current and longest journaling streak
    """
    return crud.mental_health.get_journaling_streak(db, current_user.id)

@router.get("/recommendations")
def get_self_care_recommendations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Get personalized self-care recommendations based on mood and stress patterns
    """
    # Get recent mood data (last 7 days)
    recent_moods = crud.mental_health.get_mood_logs_by_user(
        db, current_user.id, limit=7
    )
    
    # Calculate average mood
    if recent_moods:
        avg_mood = sum(m.mood_level for m in recent_moods) / len(recent_moods)
    else:
        avg_mood = 3  # Neutral if no data
    
    # Get incomplete self-care activities
    incomplete_activities = crud.mental_health.get_self_care_activities_by_user(
        db, current_user.id, completed=False, limit=5
    )
    
    # Basic recommendations based on mood
    recommendations = []
    
    if avg_mood < 2.5:
        recommendations.append("Your mood has been low lately. Consider scheduling time for activities you enjoy.")
        recommendations.append("Try to get some physical activity today, even a short walk can help.")
        recommendations.append("Consider reaching out to a friend or loved one for support.")
    elif avg_mood < 3.5:
        recommendations.append("Your mood has been moderate. Remember to take breaks during your day.")
        recommendations.append("Stay hydrated and maintain regular meals.")
    
    # Add recommendations to complete existing self-care activities
    if incomplete_activities:
        recommendations.append(f"You have {len(incomplete_activities)} incomplete self-care tasks. Try to complete at least one today.")
        recommendations.append(f"Consider scheduling time for: {incomplete_activities[0].name}")
    
    return {
        "avg_mood_level": avg_mood,
        "recommendations": recommendations,
        "suggested_activities": [
            {
                "id": a.id,
                "name": a.name,
                "description": a.description
            } for a in incomplete_activities[:3]
        ]
    } 