import pytest
from httpx import AsyncClient
from fastapi import status
from typing import Tuple
import secrets

# Helper function to register, login a user, and fetch their ID and token
async def register_login_get_user_token_and_id(
    client: AsyncClient, 
    email_suffix: str, 
    password_suffix: str = "password", 
    full_name_suffix: str = "User"
) -> Tuple[str, int]:
    """
    Creates a unique user, registers, logs in, and fetches user ID.
    Returns the auth token and the user ID.
    """
    random_component = secrets.token_hex(4)
    unique_email = f"testuser_mood_{email_suffix}_{random_component}@example.com"
    password = f"{password_suffix}_{email_suffix}_{random_component}" # Make password unique too
    full_name = f"{full_name_suffix} {email_suffix}_{random_component}"

    # Register user
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={"email": unique_email, "password": password, "full_name": full_name},
    )
    assert reg_response.status_code == status.HTTP_201_CREATED

    # Login user
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": unique_email, "password": password},  # Form data
    )
    assert login_response.status_code == status.HTTP_200_OK
    token_data = login_response.json()
    auth_token = token_data["access_token"]
    assert "access_token" in token_data

    # Get user ID from /users/me endpoint
    user_me_response = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert user_me_response.status_code == status.HTTP_200_OK
    user_data = user_me_response.json()
    user_id = user_data["id"]
    
    return auth_token, user_id

@pytest.mark.asyncio
async def test_log_mood_success(client: AsyncClient):
    auth_token, user_id = await register_login_get_user_token_and_id(client, "log_mood_success")
    
    mood_payload = {
        "mood_level": 5, # Assuming a scale, e.g., 1-5 or 1-10
        "note": "Feeling great today after a good night's sleep!",
        # date is usually auto-set by the server, or can be optional
    }
    
    response = await client.post(
        "/api/v1/moods/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=mood_payload,
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["mood_level"] == mood_payload["mood_level"]
    assert data["note"] == mood_payload["note"]
    assert "id" in data
    assert data["user_id"] == user_id
    assert "date" in data # Check if the date is returned

@pytest.mark.asyncio
async def test_log_mood_no_auth(client: AsyncClient):
    mood_payload = {
        "mood_level": 3,
        "note": "Trying to log mood without auth.",
    }
    response = await client.post(
        "/api/v1/moods/",
        json=mood_payload, # No Authorization header
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_delete_mood_log_success(client: AsyncClient):
    auth_token, _ = await register_login_get_user_token_and_id(client, "delete_mood_success")
    
    # Log a mood
    mood_payload = {"mood_level": 1, "note": "Mood to be deleted"}
    create_response = await client.post(
        "/api/v1/moods/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=mood_payload,
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    mood_id = create_response.json()["id"]

    # Delete the mood log
    delete_response = await client.delete(
        f"/api/v1/moods/{mood_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert delete_response.status_code == status.HTTP_200_OK
    assert delete_response.json()["id"] == mood_id # Check if the deleted object is returned

    # Try to GET the deleted mood log
    get_response = await client.get(
        f"/api/v1/moods/{mood_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_delete_mood_log_not_owned(client: AsyncClient):
    # User A logs a mood
    auth_token_a, _ = await register_login_get_user_token_and_id(client, "delete_mood_not_owned_a")
    mood_payload_a = {"mood_level": 3, "note": "User A's mood to protect"}
    create_response_a = await client.post(
        "/api/v1/moods/",
        headers={"Authorization": f"Bearer {auth_token_a}"},
        json=mood_payload_a,
    )
    assert create_response_a.status_code == status.HTTP_201_CREATED
    mood_id_a = create_response_a.json()["id"]

    # User B gets a token
    auth_token_b, _ = await register_login_get_user_token_and_id(client, "delete_mood_not_owned_b")

    # User B attempts to DELETE User A's mood log
    delete_response_b = await client.delete(
        f"/api/v1/moods/{mood_id_a}",
        headers={"Authorization": f"Bearer {auth_token_b}"},
    )
    assert delete_response_b.status_code == status.HTTP_404_NOT_FOUND

    # Verify User A's mood log still exists
    get_response_a = await client.get(
        f"/api/v1/moods/{mood_id_a}",
        headers={"Authorization": f"Bearer {auth_token_a}"}
    )
    assert get_response_a.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_delete_mood_log_no_auth(client: AsyncClient):
    # User A logs a mood
    auth_token_a, _ = await register_login_get_user_token_and_id(client, "delete_mood_no_auth_a")
    mood_payload_a = {"mood_level": 2, "note": "User A's mood for no auth delete test"}
    create_response_a = await client.post(
        "/api/v1/moods",
        headers={"Authorization": f"Bearer {auth_token_a}"},
        json=mood_payload_a,
    )
    assert create_response_a.status_code == status.HTTP_201_CREATED
    mood_id_a = create_response_a.json()["id"]

    # Attempt to DELETE User A's mood log with no auth
    response = await client.delete(
        f"/api/v1/moods/{mood_id_a}", # No Authorization header
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Verify User A's mood log still exists
    get_response_a_after_delete_attempt = await client.get(
        f"/api/v1/moods/{mood_id_a}",
        headers={"Authorization": f"Bearer {auth_token_a}"}
    )
    assert get_response_a_after_delete_attempt.status_code == status.HTTP_200_OK


@pytest.mark.asyncio
async def test_log_mood_invalid_data(client: AsyncClient):
    auth_token, _ = await register_login_get_user_token_and_id(client, "log_mood_invalid")
    
    # Example of invalid data: missing mood_level, or mood_level out of expected range
    # Assuming mood_level is required and an integer.
    # Test case 1: Missing mood_level
    invalid_payload_missing = {
        "note": "This mood log is missing the mood level."
    }
    response_missing = await client.post(
        "/api/v1/moods/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=invalid_payload_missing,
    )
    assert response_missing.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test case 2: Invalid type for mood_level (e.g., string instead of int)
    # Adjust if your Pydantic model handles type coercion differently or has specific range validators
    invalid_payload_type = {
        "mood_level": "this is not a number",
        "note": "Mood level is of invalid type."
    }
    response_type = await client.post(
        "/api/v1/moods/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=invalid_payload_type,
    )
    assert response_type.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # If your MoodLogCreate schema has validators (e.g., mood_level must be between 1 and 10):
    # invalid_payload_range = {
    #     "mood_level": 0, # Assuming 0 is out of range
    #     "note": "Mood level is out of range."
    # }
    # response_range = await client.post(
    #     "/api/v1/moods/",
    #     headers={"Authorization": f"Bearer {auth_token}"},
    #     json=invalid_payload_range,
    # )
    # assert response_range.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.asyncio
async def test_list_moods_success(client: AsyncClient):
    # User A setup and mood logs
    auth_token_a, user_id_a = await register_login_get_user_token_and_id(client, "list_moods_user_a")
    for i in range(2): # Log 2 moods for User A
        await client.post(
            "/api/v1/moods/",
            headers={"Authorization": f"Bearer {auth_token_a}"},
            json={"mood_level": 4, "note": f"User A mood log {i+1}"},
        )

    # User B setup and mood log
    auth_token_b, _ = await register_login_get_user_token_and_id(client, "list_moods_user_b")
    await client.post(
        "/api/v1/moods/",
        headers={"Authorization": f"Bearer {auth_token_b}"},
        json={"mood_level": 3, "note": "User B mood log 1"},
    )

    # List mood logs as User A
    response = await client.get(
        "/api/v1/moods/",
        headers={"Authorization": f"Bearer {auth_token_a}"},
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2 # Should only list User A's mood logs
    for mood_log in data:
        assert mood_log["user_id"] == user_id_a
        assert "User A mood log" in mood_log["note"]

@pytest.mark.asyncio
async def test_list_moods_no_auth(client: AsyncClient):
    response = await client.get("/api/v1/moods/") # No Authorization header
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_get_specific_mood_log_success(client: AsyncClient):
    auth_token, user_id = await register_login_get_user_token_and_id(client, "get_specific_mood_success")
    
    # Log a mood
    mood_payload = {"mood_level": 5, "note": "Specific mood log"}
    create_response = await client.post(
        "/api/v1/moods/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=mood_payload,
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    created_mood_data = create_response.json()
    mood_id = created_mood_data["id"]

    # Get the specific mood log
    response = await client.get(
        f"/api/v1/moods/{mood_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == mood_id
    assert data["mood_level"] == mood_payload["mood_level"]
    assert data["user_id"] == user_id

@pytest.mark.asyncio
async def test_get_specific_mood_log_not_owned(client: AsyncClient):
    # User A logs a mood
    auth_token_a, _ = await register_login_get_user_token_and_id(client, "get_mood_not_owned_user_a")
    mood_payload_a = {"mood_level": 4, "note": "User A's private mood"}
    create_response_a = await client.post(
        "/api/v1/moods/",
        "/api/v1/moods/",
        headers={"Authorization": f"Bearer {auth_token_a}"},
        json=mood_payload_a,
    )
    assert create_response_a.status_code == status.HTTP_201_CREATED
    mood_id_a = create_response_a.json()["id"]

    # User B gets a token
    auth_token_b, _ = await register_login_get_user_token_and_id(client, "get_mood_not_owned_user_b")

    # User B attempts to GET User A's mood log
    response_b = await client.get(
        f"/api/v1/moods/{mood_id_a}",
        headers={"Authorization": f"Bearer {auth_token_b}"},
    )
    assert response_b.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_get_specific_mood_log_not_found(client: AsyncClient):
    auth_token, _ = await register_login_get_user_token_and_id(client, "get_mood_not_found")
    
    response = await client.get(
        "/api/v1/moods/9999999", # Non-existent ID
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_get_specific_mood_log_no_auth(client: AsyncClient):
    # User A logs a mood
    auth_token_a, _ = await register_login_get_user_token_and_id(client, "get_mood_no_auth_user_a")
    mood_payload_a = {"mood_level": 2, "note": "User A's mood for no auth test"}
    create_response_a = await client.post(
        "/api/v1/moods",
        headers={"Authorization": f"Bearer {auth_token_a}"},
        json=mood_payload_a,
    )
    assert create_response_a.status_code == status.HTTP_201_CREATED
    mood_id_a = create_response_a.json()["id"]

    # Attempt to GET User A's mood log with no auth
    response = await client.get(
        f"/api/v1/moods/{mood_id_a}", # No Authorization header
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
