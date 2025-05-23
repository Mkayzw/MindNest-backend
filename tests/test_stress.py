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
    unique_email = f"testuser_stress_{email_suffix}_{random_component}@example.com"
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
async def test_log_stress_event_success(client: AsyncClient):
    auth_token, user_id = await register_login_get_user_token_and_id(client, "log_stress_success")
    
    stress_payload = {
        "description": "Feeling overwhelmed with work tasks.",
        "trigger_tag": "Work", # Assuming trigger_tag is a simple string for now
        "intensity": 8, # Assuming intensity is an integer, e.g., on a scale of 1-10
        # occurrence_time is usually auto-set by the server or can be optional
    }
    
    response = await client.post(
        "/api/v1/stress/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=stress_payload,
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["description"] == stress_payload["description"]
    assert data["trigger_tag"] == stress_payload["trigger_tag"]
    assert data["intensity"] == stress_payload["intensity"]
    assert "id" in data
    assert data["user_id"] == user_id
    assert "occurrence_time" in data # Check if the timestamp is returned

@pytest.mark.asyncio
async def test_log_stress_event_no_auth(client: AsyncClient):
    stress_payload = {
        "description": "Trying to log stress without auth.",
        "trigger_tag": "Test",
        "intensity": 5,
    }
    response = await client.post(
        "/api/v1/stress/",
        json=stress_payload, # No Authorization header
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_delete_stress_event_success(client: AsyncClient):
    auth_token, _ = await register_login_get_user_token_and_id(client, "delete_stress_success")
    
    # Log a stress event
    stress_payload = {"description": "Stress event to be deleted", "trigger_tag": "DeleteTest", "intensity": 2}
    create_response = await client.post(
        "/api/v1/stress/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=stress_payload,
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    stress_event_id = create_response.json()["id"]

    # Delete the stress event
    delete_response = await client.delete(
        f"/api/v1/stress/{stress_event_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert delete_response.status_code == status.HTTP_200_OK
    # Optionally, check if the response body contains the deleted item's details
    assert delete_response.json()["id"] == stress_event_id 

    # Try to GET the deleted stress event
    get_response = await client.get(
        f"/api/v1/stress/{stress_event_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_delete_stress_event_not_owned(client: AsyncClient):
    # User A logs a stress event
    auth_token_a, _ = await register_login_get_user_token_and_id(client, "delete_stress_not_owned_a")
    stress_payload_a = {"description": "User A's stress to protect", "trigger_tag": "Secure", "intensity": 7}
    create_response_a = await client.post(
        "/api/v1/stress/",
        headers={"Authorization": f"Bearer {auth_token_a}"},
        json=stress_payload_a,
    )
    assert create_response_a.status_code == status.HTTP_201_CREATED
    stress_event_id_a = create_response_a.json()["id"]

    # User B gets a token
    auth_token_b, _ = await register_login_get_user_token_and_id(client, "delete_stress_not_owned_b")

    # User B attempts to DELETE User A's stress event
    delete_response_b = await client.delete(
        f"/api/v1/stress/{stress_event_id_a}",
        headers={"Authorization": f"Bearer {auth_token_b}"},
    )
    assert delete_response_b.status_code == status.HTTP_404_NOT_FOUND

    # Verify User A's stress event still exists
    get_response_a = await client.get(
        f"/api/v1/stress/{stress_event_id_a}",
        headers={"Authorization": f"Bearer {auth_token_a}"}
    )
    assert get_response_a.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_delete_stress_event_no_auth(client: AsyncClient):
    # User A logs a stress event
    auth_token_a, _ = await register_login_get_user_token_and_id(client, "delete_stress_no_auth_a")
    stress_payload_a = {"description": "User A's stress for no auth delete test", "trigger_tag": "FinalTest", "intensity": 3}
    create_response_a = await client.post(
        "/api/v1/stress",
        headers={"Authorization": f"Bearer {auth_token_a}"},
        json=stress_payload_a,
    )
    assert create_response_a.status_code == status.HTTP_201_CREATED
    stress_event_id_a = create_response_a.json()["id"]

    # Attempt to DELETE User A's stress event with no auth
    response = await client.delete(
        f"/api/v1/stress/{stress_event_id_a}", # No Authorization header
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Verify User A's stress event still exists
    get_response_a_after_delete = await client.get(
        f"/api/v1/stress/{stress_event_id_a}",
        headers={"Authorization": f"Bearer {auth_token_a}"}
    )
    assert get_response_a_after_delete.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_log_stress_event_invalid_data(client: AsyncClient):
    auth_token, _ = await register_login_get_user_token_and_id(client, "log_stress_invalid")
    
    # Test case 1: Missing description (assuming description is required)
    invalid_payload_missing = {
        "trigger_tag": "Incomplete",
        "intensity": 3
    }
    response_missing = await client.post(
        "/api/v1/stress/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=invalid_payload_missing,
    )
    assert response_missing.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test case 2: Invalid type for intensity (e.g., string instead of int)
    invalid_payload_type = {
        "description": "Invalid intensity type",
        "trigger_tag": "TypeTest",
        "intensity": "this is not a number" 
    }
    response_type = await client.post(
        "/api/v1/stress/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=invalid_payload_type,
    )
    assert response_type.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Add more invalid cases as needed, e.g., intensity out of range if validated by Pydantic model
    # invalid_payload_range = {
    #     "description": "Intensity out of range",
    #     "trigger_tag": "RangeTest",
    #     "intensity": 100 # Assuming intensity is 1-10
    # }
    # response_range = await client.post(
    #     "/api/v1/stress/",
    #     headers={"Authorization": f"Bearer {auth_token}"},
    #     json=invalid_payload_range,
    # )
    # assert response_range.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.asyncio
async def test_list_stress_events_success(client: AsyncClient):
    # User A setup and stress events
    auth_token_a, user_id_a = await register_login_get_user_token_and_id(client, "list_stress_user_a")
    for i in range(2): # Log 2 stress events for User A
        await client.post(
            "/api/v1/stress/",
            headers={"Authorization": f"Bearer {auth_token_a}"},
            json={"description": f"User A stress event {i+1}", "trigger_tag": "Work", "intensity": 7},
        )

    # User B setup and stress event
    auth_token_b, _ = await register_login_get_user_token_and_id(client, "list_stress_user_b")
    await client.post(
        "/api/v1/stress/",
        headers={"Authorization": f"Bearer {auth_token_b}"},
        json={"description": "User B stress event 1", "trigger_tag": "Personal", "intensity": 5},
    )

    # List stress events as User A
    response = await client.get(
        "/api/v1/stress/",
        headers={"Authorization": f"Bearer {auth_token_a}"},
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2 # Should only list User A's stress events
    for stress_event in data:
        assert stress_event["user_id"] == user_id_a
        assert "User A stress event" in stress_event["description"]

@pytest.mark.asyncio
async def test_list_stress_events_no_auth(client: AsyncClient):
    response = await client.get("/api/v1/stress/") # No Authorization header
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_get_specific_stress_event_success(client: AsyncClient):
    auth_token, user_id = await register_login_get_user_token_and_id(client, "get_specific_stress_success")
    
    # Log a stress event
    stress_payload = {"description": "Specific stress event", "trigger_tag": "Test", "intensity": 6}
    create_response = await client.post(
        "/api/v1/stress/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=stress_payload,
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    created_stress_data = create_response.json()
    stress_event_id = created_stress_data["id"]

    # Get the specific stress event
    response = await client.get(
        f"/api/v1/stress/{stress_event_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == stress_event_id
    assert data["description"] == stress_payload["description"]
    assert data["user_id"] == user_id

@pytest.mark.asyncio
async def test_get_specific_stress_event_not_owned(client: AsyncClient):
    # User A logs a stress event
    auth_token_a, _ = await register_login_get_user_token_and_id(client, "get_stress_not_owned_user_a")
    stress_payload_a = {"description": "User A's private stress event", "trigger_tag": "Private", "intensity": 9}
    create_response_a = await client.post(
        "/api/v1/stress/",
        "/api/v1/stress/",
        headers={"Authorization": f"Bearer {auth_token_a}"},
        json=stress_payload_a,
    )
    assert create_response_a.status_code == status.HTTP_201_CREATED
    stress_event_id_a = create_response_a.json()["id"]

    # User B gets a token
    auth_token_b, _ = await register_login_get_user_token_and_id(client, "get_stress_not_owned_user_b")

    # User B attempts to GET User A's stress event
    response_b = await client.get(
        f"/api/v1/stress/{stress_event_id_a}",
        headers={"Authorization": f"Bearer {auth_token_b}"},
    )
    assert response_b.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_get_specific_stress_event_not_found(client: AsyncClient):
    auth_token, _ = await register_login_get_user_token_and_id(client, "get_stress_not_found")
    
    response = await client.get(
        "/api/v1/stress/9999999", # Non-existent ID
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_get_specific_stress_event_no_auth(client: AsyncClient):
    # User A logs a stress event
    auth_token_a, _ = await register_login_get_user_token_and_id(client, "get_stress_no_auth_user_a")
    stress_payload_a = {"description": "User A's stress for no auth test", "trigger_tag": "Test", "intensity": 4}
    create_response_a = await client.post(
        "/api/v1/stress",
        headers={"Authorization": f"Bearer {auth_token_a}"},
        json=stress_payload_a,
    )
    assert create_response_a.status_code == status.HTTP_201_CREATED
    stress_event_id_a = create_response_a.json()["id"]

    # Attempt to GET User A's stress event with no auth
    response = await client.get(
        f"/api/v1/stress/{stress_event_id_a}", # No Authorization header
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
