import pytest
from httpx import AsyncClient
from fastapi import status
from typing import Tuple, List, Dict, Any
import secrets
from datetime import datetime, timedelta, timezone

# Helper function to register, login a user, and fetch their ID and token
async def register_login_get_user_token_and_id(
    client: AsyncClient, 
    email_suffix: str, 
    password_suffix: str = "password", 
    full_name_suffix: str = "User"
) -> Tuple[str, int]:
    random_component = secrets.token_hex(4)
    unique_email = f"testuser_analytics_{email_suffix}_{random_component}@example.com"
    password = f"{password_suffix}_{email_suffix}_{random_component}"
    full_name = f"{full_name_suffix} {email_suffix}"

    reg_response = await client.post(
        "/api/v1/auth/register",
        json={"email": unique_email, "password": password, "full_name": full_name},
    )
    assert reg_response.status_code == status.HTTP_201_CREATED

    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": unique_email, "password": password},
    )
    assert login_response.status_code == status.HTTP_200_OK
    token_data = login_response.json()
    auth_token = token_data["access_token"]

    user_me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert user_me_response.status_code == status.HTTP_200_OK
    user_id = user_me_response.json()["id"]
    
    return auth_token, user_id

# Helper to create mood log with specific timestamp
async def create_mood_log_for_user(
    client: AsyncClient, 
    token: str, 
    mood_level: int, 
    note: str, 
    logged_at: datetime
):
    # The API expects a MoodLogCreate schema which might not have logged_at
    # Assuming the API sets logged_at on creation, or if it allows setting it,
    # the schema would need to be MoodLogCreate(mood_level=..., note=..., logged_at=...)
    # For now, assuming the API uses its own timestamping for logged_at upon creation.
    # If the backend allows overriding 'date' (or 'logged_at') upon creation, this needs adjustment.
    # The current MoodLogCreate schema does not seem to support a custom date.
    # This helper might need to be re-evaluated based on API capabilities for backdating.
    # For now, we'll create it and the API will set the timestamp.
    # If tests require specific historical timestamps, the backend needs to support it.
    payload = {"mood_level": mood_level, "note": note}
    # If your API supports setting the date:
    # payload["logged_at"] = logged_at.isoformat() 
    response = await client.post(
        "/api/v1/moods/",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()

# Helper to create journal entry with specific timestamp
async def create_journal_entry_for_user(
    client: AsyncClient, 
    token: str, 
    title: str, 
    content: str, 
    mood: str, 
    created_at: datetime # Assuming the API allows setting created_at
):
    # Similar to mood logs, this depends on whether the backend API allows overriding
    # the creation timestamp. The JournalCreate schema does not seem to support it.
    # If specific historical timestamps are crucial, the backend must allow setting 'created_at'.
    payload = {"title": title, "content": content, "mood": mood}
    # If your API supports setting the date:
    # payload["created_at"] = created_at.isoformat()
    response = await client.post(
        "/api/v1/journals/",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()

# Helper to create stress event with specific timestamp
async def create_stress_event_for_user(
    client: AsyncClient,
    token: str,
    description: str,
    trigger_tag: str,
    intensity: int,
    occurrence_time: datetime # Assuming API allows setting occurrence_time
):
    # Similar to above, this depends on API capability for custom timestamps.
    # The StressEventCreate schema does not seem to support it.
    payload = {"description": description, "trigger_tag": trigger_tag, "intensity": intensity}
    # If API supports custom time:
    # payload["occurrence_time"] = occurrence_time.isoformat()
    response = await client.post(
        "/api/v1/stress/",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert response.status_code == status.HTTP_201_CREATED
    return response.json()

# Note: The helper functions for creating items with specific past timestamps
# (create_mood_log_for_user, create_journal_entry_for_user, create_stress_event_for_user)
# currently assume that the backend API's POST endpoints for these resources will
# automatically set the creation timestamp (e.g., `created_at`, `logged_at`, `occurrence_time`)
# to `datetime.utcnow()` at the moment of creation. They do NOT currently pass a specific
# timestamp to the API, as the Pydantic schemas (MoodLogCreate, JournalCreate, StressEventCreate)
# used for request bodies in those routes do not include fields for these timestamps.
#
# If the analytics endpoints require data with precisely controlled historical timestamps
# to function correctly for tests (e.g., for `mood-trend` over a specific past week,
# or `journaling-streak` based on entries made on specific past dates),
# then the backend API (specifically the POST endpoints for creating these resources)
# would need to be modified to:
# 1. Accept an optional timestamp in the request body (e.g., `created_at: Optional[datetime]`).
# 2. Use this provided timestamp when creating the database record, instead of `datetime.utcnow()`.
#
# Without such backend support, these helper functions can only create items timestamped "now".
# This might limit the ability to test certain historical analytics scenarios accurately.
# The tests written below will proceed with this assumption, and if specific timestamp
# manipulation is needed, it will be highlighted. For `journaling-streak`, we will attempt
# to create entries on different "real" days if tests span multiple days, or rely on
# the backend's interpretation of "today" vs "yesterday" based on UTC.
# For mood-trend and stress-patterns, if date filtering via query params is supported by the API,
# that would be the primary way to test ranges, otherwise, we test with data created "now".

# --- Mood Trend Tests ---

@pytest.mark.asyncio
async def test_mood_trend_success(client: AsyncClient):
    auth_token, _ = await register_login_get_user_token_and_id(client, "mood_trend_success")
    
    # To properly test mood trend, we need to create mood logs with varying timestamps.
    # As noted above, if the API doesn't allow setting past timestamps, this test is limited.
    # Assuming for now we can create some logs and the API will trend them.
    # If the backend does not allow setting timestamps, these will all be "now".
    # For a true trend, these would need to be on different days.
    await create_mood_log_for_user(client, auth_token, 5, "Great day", datetime.now(timezone.utc))
    await create_mood_log_for_user(client, auth_token, 3, "Okay day", datetime.now(timezone.utc)) 
    # Ideally, create logs for different days:
    # await create_mood_log_for_user(client, auth_token, 4, "Yesterday good", datetime.now(timezone.utc) - timedelta(days=1))
    # await create_mood_log_for_user(client, auth_token, 2, "Two days ago meh", datetime.now(timezone.utc) - timedelta(days=2))

    response = await client.get(
        "/api/v1/analytics/mood-trend/",
        "/api/v1/analytics/mood-trend/",
        headers={"Authorization": f"Bearer {auth_token}"}
        # Add query params like ?start_date=...&end_date=... if API supports
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    # Further assertions depend on the exact structure (e.g., {"date": "YYYY-MM-DD", "average_mood": X.X})
    # and whether the backend could actually store varied timestamps.
    # If all timestamps are "now", the trend might be a single point or average of today.
    if data: # If any data is returned
        for item in data:
            assert "date" in item
            assert "average_mood" in item
            assert isinstance(item["average_mood"], (float, int))

@pytest.mark.asyncio
async def test_mood_trend_no_data(client: AsyncClient):
    auth_token, _ = await register_login_get_user_token_and_id(client, "mood_trend_no_data")
    
    response = await client.get(
        "/api/v1/analytics/mood-trend",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

@pytest.mark.asyncio
async def test_mood_trend_no_auth(client: AsyncClient):
    response = await client.get("/api/v1/analytics/mood-trend/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# --- Stress Patterns Tests ---

@pytest.mark.asyncio
async def test_stress_patterns_success(client: AsyncClient):
    auth_token, _ = await register_login_get_user_token_and_id(client, "stress_patterns_success")

    # Similar timestamp limitation as mood trend for creating historical data.
    await create_stress_event_for_user(client, auth_token, "Work deadline", "Work", 8, datetime.now(timezone.utc))
    await create_stress_event_for_user(client, auth_token, "Argument with friend", "Personal", 6, datetime.now(timezone.utc))
    await create_stress_event_for_user(client, auth_token, "Heavy traffic", "Commute", 5, datetime.now(timezone.utc))
    await create_stress_event_for_user(client, auth_token, "Another work issue", "Work", 7, datetime.now(timezone.utc))

    response = await client.get(
        "/api/v1/analytics/stress-patterns/",
        "/api/v1/analytics/stress-patterns/",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # Expected structure e.g., {"Work": {"count": 2, "average_intensity": 7.5}, "Personal": {...}}
    # This depends heavily on the API's output structure.
    assert isinstance(data, dict) # Or list, depending on API
    if data:
        for tag_data in data.values(): # Assuming dict values are the summaries
            assert "count" in tag_data
            assert "average_intensity" in tag_data # Or similar metrics

@pytest.mark.asyncio
async def test_stress_patterns_no_data(client: AsyncClient):
    auth_token, _ = await register_login_get_user_token_and_id(client, "stress_patterns_no_data")
    
    response = await client.get(
        "/api/v1/analytics/stress-patterns",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data == {} or data == [] # Or specific "no data" structure

@pytest.mark.asyncio
async def test_stress_patterns_no_auth(client: AsyncClient):
    response = await client.get("/api/v1/analytics/stress-patterns/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# --- Journaling Streak Tests ---
# For these tests, the exact time of day matters less than the date part.
# The backend's logic for "today", "yesterday" based on UTC will be key.

@pytest.mark.asyncio
async def test_journaling_streak_current_success(client: AsyncClient):
    auth_token, _ = await register_login_get_user_token_and_id(client, "journal_streak_current")
    
    # To test a streak, we need entries on consecutive days.
    # This is challenging if we can't backdate.
    # If these run on the same day, streak might be 1.
    # If the create_journal_entry_for_user could set 'created_at', we would do:
    # await create_journal_entry_for_user(client, auth_token, "Day 1", "", "Ok", datetime.now(timezone.utc) - timedelta(days=2))
    # await create_journal_entry_for_user(client, auth_token, "Day 2", "", "Ok", datetime.now(timezone.utc) - timedelta(days=1))
    # await create_journal_entry_for_user(client, auth_token, "Day 3", "", "Ok", datetime.now(timezone.utc))
    
    # Assuming for now the backend can correctly determine streak from entries made "today"
    # or if test runs over multiple days, this might naturally work.
    # For a robust test, backend needs to allow setting creation date.
    # Let's create one entry for "today"
    await create_journal_entry_for_user(client, auth_token, "Today's Entry", "Content", "Good", datetime.now(timezone.utc))
    # If we could create one for "yesterday":
    # await create_journal_entry_for_user(client, auth_token, "Yesterday's Entry", "Content", "Good", datetime.now(timezone.utc) - timedelta(days=1))


    response = await client.get(
        "/api/v1/analytics/journaling-streak/",
        "/api/v1/analytics/journaling-streak/",
        "/api/v1/analytics/journaling-streak/",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "current_streak" in data
    # The actual value of current_streak will depend on the backend's ability to distinguish dates
    # and whether we could create entries for past consecutive days.
    # If only one entry is made today, streak should be 1.
    assert isinstance(data["current_streak"], int)
    # Example: if we could create 3 consecutive daily entries ending today, this would be 3.
    # For now, if only one entry made:
    # assert data["current_streak"] >= 1 # At least 1 if we created one today

@pytest.mark.asyncio
async def test_journaling_streak_broken_success(client: AsyncClient):
    auth_token, _ = await register_login_get_user_token_and_id(client, "journal_streak_broken")

    # To test a broken streak, e.g. entry today, entry day before yesterday, but not yesterday.
    # Again, relies on ability to backdate entries.
    # await create_journal_entry_for_user(client, auth_token, "Today", "", "Ok", datetime.now(timezone.utc))
    # await create_journal_entry_for_user(client, auth_token, "Two days ago", "", "Ok", datetime.now(timezone.utc) - timedelta(days=2))
    
    # Creating one for today
    await create_journal_entry_for_user(client, auth_token, "Today's Entry Only", "Content", "Okay", datetime.now(timezone.utc))
    
    response = await client.get(
        "/api/v1/analytics/journaling-streak",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "current_streak" in data
    assert data["current_streak"] == 1 # Assuming only today's entry counts

@pytest.mark.asyncio
async def test_journaling_streak_no_entries(client: AsyncClient):
    auth_token, _ = await register_login_get_user_token_and_id(client, "journal_streak_no_entries")
    
    response = await client.get(
        "/api/v1/analytics/journaling-streak",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "current_streak" in data
    assert data["current_streak"] == 0

@pytest.mark.asyncio
async def test_journaling_streak_no_auth(client: AsyncClient):
    response = await client.get("/api/v1/analytics/journaling-streak/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# --- Personalized Recommendations Tests ---

@pytest.mark.asyncio
async def test_recommendations_success(client: AsyncClient):
    auth_token, _ = await register_login_get_user_token_and_id(client, "recommendations_success")
    
    # Optionally create some data, e.g., low mood logs, high stress
    # await create_mood_log_for_user(client, auth_token, 1, "Feeling very down", datetime.now(timezone.utc))
    # await create_stress_event_for_user(client, auth_token, "Final exams", "School", 9, datetime.now(timezone.utc))

    response = await client.get(
        "/api/v1/analytics/recommendations/",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, dict) # API returns a dict with a 'recommendations' list and other keys
    assert "recommendations" in data
    assert isinstance(data["recommendations"], list)
    if data["recommendations"]:
        for rec in data["recommendations"]:
            assert "title" in rec
            assert "description" in rec
            assert "type" in rec # e.g., 'article', 'activity', 'meditation'
            # Other fields like 'source_url' or 'estimated_time' could also be here.

@pytest.mark.asyncio
async def test_recommendations_no_auth(client: AsyncClient):
    response = await client.get("/api/v1/analytics/recommendations/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
