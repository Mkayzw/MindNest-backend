import pytest
from httpx import AsyncClient
from fastapi import status
from typing import Tuple
from datetime import datetime, timedelta
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
    unique_email = f"testuser_selfcare_{email_suffix}_{random_component}@example.com"
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
async def test_create_self_care_activity_success(client: AsyncClient):
    auth_token, user_id = await register_login_get_user_token_and_id(client, "create_sc_success")
    
    activity_payload = {
        "name": "Morning Meditation",
        "description": "10 minutes of guided meditation.",
        "is_completed": False,
        "scheduled_for": (datetime.utcnow() + timedelta(days=1)).isoformat() # Schedule for tomorrow
    }
    
    response = await client.post(
        "/api/v1/self-care/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=activity_payload,
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == activity_payload["name"]
    assert data["description"] == activity_payload["description"]
    assert data["is_completed"] == activity_payload["is_completed"]
    assert "id" in data
    assert data["user_id"] == user_id
    # Ensure scheduled_for is handled, possibly comparing parsed datetimes if format varies
    assert data["scheduled_for"] is not None 

@pytest.mark.asyncio
async def test_create_self_care_activity_no_auth(client: AsyncClient):
    activity_payload = {
        "name": "Unauthorized Activity",
        "description": "This should not be created.",
        "is_completed": False,
        "scheduled_for": datetime.utcnow().isoformat()
    }
    response = await client.post(
        "/api/v1/self-care/",
        json=activity_payload, # No Authorization header
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_update_self_care_activity_success(client: AsyncClient):
    auth_token, user_id = await register_login_get_user_token_and_id(client, "update_sc_success")
    
    # Create an activity
    initial_payload = {
        "name": "Initial Activity Name", 
        "description": "Initial description.", 
        "is_completed": False,
        "scheduled_for": datetime.utcnow().isoformat()
    }
    create_response = await client.post(
        "/api/v1/self-care/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=initial_payload,
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    activity_id = create_response.json()["id"]

    # Update the activity
    update_payload = {
        "name": "Updated Activity Name",
        "description": "Updated description!",
        "is_completed": True
        # Not updating scheduled_for here, but could be tested
    }
    update_response = await client.patch( # Assuming PATCH for partial updates
        f"/api/v1/self-care/{activity_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=update_payload,
    )
    
    assert update_response.status_code == status.HTTP_200_OK
    data = update_response.json()
    assert data["id"] == activity_id
    assert data["name"] == update_payload["name"]
    assert data["description"] == update_payload["description"]
    assert data["is_completed"] == update_payload["is_completed"]
    assert data["user_id"] == user_id

@pytest.mark.asyncio
async def test_update_self_care_activity_not_owned(client: AsyncClient):
    # User A creates an activity
    auth_token_a, _ = await register_login_get_user_token_and_id(client, "update_sc_not_owned_user_a")
    initial_payload_a = {
        "name": "User A's Unupdatable Activity", 
        "description": "Content A", 
        "is_completed": False,
        "scheduled_for": datetime.utcnow().isoformat()
    }
    create_response_a = await client.post(
        "/api/v1/self-care/",
        headers={"Authorization": f"Bearer {auth_token_a}"},
        json=initial_payload_a,
    )
    assert create_response_a.status_code == status.HTTP_201_CREATED
    activity_id_a = create_response_a.json()["id"]

    # User B gets a token
    auth_token_b, _ = await register_login_get_user_token_and_id(client, "update_sc_not_owned_user_b")
    update_payload_b = {
        "name": "Attempted Update by B", 
        "is_completed": True
    }

    # User B attempts to PATCH User A's activity
    response_b = await client.patch(
        f"/api/v1/self-care/{activity_id_a}",
        headers={"Authorization": f"Bearer {auth_token_b}"},
        json=update_payload_b,
    )
    assert response_b.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_update_self_care_activity_no_auth(client: AsyncClient):
    # User A creates an activity
    auth_token_a, _ = await register_login_get_user_token_and_id(client, "update_sc_no_auth_user_a")
    initial_payload_a = {
        "name": "Activity for No Auth Update", 
        "description": "Content", 
        "is_completed": False,
        "scheduled_for": datetime.utcnow().isoformat()
    }
    create_response_a = await client.post(
        "/api/v1/self-care",
        headers={"Authorization": f"Bearer {auth_token_a}"},
        json=initial_payload_a,
    )
    assert create_response_a.status_code == status.HTTP_201_CREATED
    activity_id_a = create_response_a.json()["id"]

    update_payload = {
        "name": "Updated Title No Auth", 
        "is_completed": True
    }
    
    # Attempt to PATCH User A's activity with no auth
    response = await client.patch(
        f"/api/v1/self-care/{activity_id_a}",
        json=update_payload, # No Authorization header
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_delete_self_care_activity_success(client: AsyncClient):
    auth_token, _ = await register_login_get_user_token_and_id(client, "delete_sc_success")
    
    # Create an activity
    payload = {
        "name": "Activity to Delete", 
        "description": "This will be deleted.", 
        "is_completed": False,
        "scheduled_for": datetime.utcnow().isoformat()
    }
    create_response = await client.post(
        "/api/v1/self-care/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=payload,
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    activity_id = create_response.json()["id"]

    # Delete the activity
    delete_response = await client.delete(
        f"/api/v1/self-care/{activity_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert delete_response.status_code == status.HTTP_200_OK
    # Optionally, assert the deleted activity data is returned
    assert delete_response.json()["id"] == activity_id 

    # Try to GET the deleted activity
    get_response = await client.get(
        f"/api/v1/self-care/{activity_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_delete_self_care_activity_not_owned(client: AsyncClient):
    # User A creates an activity
    auth_token_a, _ = await register_login_get_user_token_and_id(client, "delete_sc_not_owned_user_a")
    payload_a = {
        "name": "User A's Protected Activity", 
        "description": "Content A", 
        "is_completed": False,
        "scheduled_for": datetime.utcnow().isoformat()
    }
    create_response_a = await client.post(
        "/api/v1/self-care/",
        "/api/v1/self-care/",
        headers={"Authorization": f"Bearer {auth_token_a}"},
        json=payload_a,
    )
    assert create_response_a.status_code == status.HTTP_201_CREATED
    activity_id_a = create_response_a.json()["id"]

    # User B gets a token
    auth_token_b, _ = await register_login_get_user_token_and_id(client, "delete_sc_not_owned_user_b")

    # User B attempts to DELETE User A's activity
    delete_response_b = await client.delete(
        f"/api/v1/self-care/{activity_id_a}",
        headers={"Authorization": f"Bearer {auth_token_b}"},
    )
    assert delete_response_b.status_code == status.HTTP_404_NOT_FOUND

    # Verify User A's activity still exists
    get_response_a = await client.get(
        f"/api/v1/self-care/{activity_id_a}",
        headers={"Authorization": f"Bearer {auth_token_a}"}
    )
    assert get_response_a.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_delete_self_care_activity_no_auth(client: AsyncClient):
    # User A creates an activity
    auth_token_a, _ = await register_login_get_user_token_and_id(client, "delete_sc_no_auth_user_a")
    payload_a = {
        "name": "Activity for No Auth Delete", 
        "description": "Content", 
        "is_completed": False,
        "scheduled_for": datetime.utcnow().isoformat()
    }
    create_response_a = await client.post(
        "/api/v1/self-care",
        headers={"Authorization": f"Bearer {auth_token_a}"},
        json=payload_a,
    )
    assert create_response_a.status_code == status.HTTP_201_CREATED
    activity_id_a = create_response_a.json()["id"]

    # Attempt to DELETE User A's activity with no auth
    response = await client.delete(
        f"/api/v1/self-care/{activity_id_a}", # No Authorization header
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Verify User A's activity still exists
    get_response_a_after_delete = await client.get(
        f"/api/v1/self-care/{activity_id_a}",
        headers={"Authorization": f"Bearer {auth_token_a}"}
    )
    assert get_response_a_after_delete.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_create_self_care_activity_invalid_data(client: AsyncClient):
    auth_token, _ = await register_login_get_user_token_and_id(client, "create_sc_invalid")
    
    # Test case 1: Missing 'name'
    invalid_payload_missing_name = {
        "description": "Activity with no name.",
        "is_completed": False,
        "scheduled_for": datetime.utcnow().isoformat()
    }
    response_missing = await client.post(
        "/api/v1/self-care/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=invalid_payload_missing_name,
    )
    assert response_missing.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Test case 2: Invalid 'scheduled_for' date format
    invalid_payload_bad_date = {
        "name": "Bad Date Activity",
        "description": "This activity has a badly formatted date.",
        "is_completed": False,
        "scheduled_for": "not-a-date"
    }
    response_bad_date = await client.post(
        "/api/v1/self-care/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=invalid_payload_bad_date,
    )
    assert response_bad_date.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.asyncio
async def test_list_self_care_activities_success(client: AsyncClient):
    # User A setup and activities
    auth_token_a, user_id_a = await register_login_get_user_token_and_id(client, "list_sc_user_a")
    for i in range(2): # Create 2 activities for User A
        await client.post(
            "/api/v1/self-care/",
            headers={"Authorization": f"Bearer {auth_token_a}"},
            json={
                "name": f"User A Activity {i+1}", 
                "description": "User A's activity",
                "is_completed": False,
                "scheduled_for": datetime.utcnow().isoformat()
            },
        )

    # User B setup and activity
    auth_token_b, _ = await register_login_get_user_token_and_id(client, "list_sc_user_b")
    await client.post(
        "/api/v1/self-care/",
        headers={"Authorization": f"Bearer {auth_token_b}"},
        json={
            "name": "User B Activity 1", 
            "description": "User B's activity",
            "is_completed": True,
            "scheduled_for": datetime.utcnow().isoformat()
        },
    )

    # List activities as User A
    response = await client.get(
        "/api/v1/self-care/",
        headers={"Authorization": f"Bearer {auth_token_a}"},
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2 # Should only list User A's activities
    for activity in data:
        assert activity["user_id"] == user_id_a
        assert "User A Activity" in activity["name"]

@pytest.mark.asyncio
async def test_list_self_care_activities_no_auth(client: AsyncClient):
    response = await client.get("/api/v1/self-care/") # No Authorization header
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_get_specific_self_care_activity_success(client: AsyncClient):
    auth_token, user_id = await register_login_get_user_token_and_id(client, "get_sc_specific_success")
    
    # Create an activity
    activity_payload = {
        "name": "Specific Activity", 
        "description": "Details...", 
        "is_completed": False,
        "scheduled_for": datetime.utcnow().isoformat()
    }
    create_response = await client.post(
        "/api/v1/self-care/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=activity_payload,
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    created_activity_data = create_response.json()
    activity_id = created_activity_data["id"]

    # Get the specific activity
    response = await client.get(
        f"/api/v1/self-care/{activity_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == activity_id
    assert data["name"] == activity_payload["name"]
    assert data["user_id"] == user_id

@pytest.mark.asyncio
async def test_get_specific_self_care_activity_not_owned(client: AsyncClient):
    # User A creates an activity
    auth_token_a, _ = await register_login_get_user_token_and_id(client, "get_sc_not_owned_user_a")
    activity_payload_a = {
        "name": "User A's Private Activity", 
        "description": "Content A", 
        "is_completed": False,
        "scheduled_for": datetime.utcnow().isoformat()
    }
    create_response_a = await client.post(
        "/api/v1/self-care/",
        "/api/v1/self-care/",
        headers={"Authorization": f"Bearer {auth_token_a}"},
        json=activity_payload_a,
    )
    assert create_response_a.status_code == status.HTTP_201_CREATED
    activity_id_a = create_response_a.json()["id"]

    # User B gets a token
    auth_token_b, _ = await register_login_get_user_token_and_id(client, "get_sc_not_owned_user_b")

    # User B attempts to GET User A's activity
    response_b = await client.get(
        f"/api/v1/self-care/{activity_id_a}",
        headers={"Authorization": f"Bearer {auth_token_b}"},
    )
    assert response_b.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_get_specific_self_care_activity_no_auth(client: AsyncClient):
    # User A creates an activity
    auth_token_a, _ = await register_login_get_user_token_and_id(client, "get_sc_no_auth_user_a")
    activity_payload_a = {
        "name": "User A's Activity for No Auth Test", 
        "description": "Content", 
        "is_completed": False,
        "scheduled_for": datetime.utcnow().isoformat()
    }
    create_response_a = await client.post(
        "/api/v1/self-care",
        headers={"Authorization": f"Bearer {auth_token_a}"},
        json=activity_payload_a,
    )
    assert create_response_a.status_code == status.HTTP_201_CREATED
    activity_id_a = create_response_a.json()["id"]

    # Attempt to GET User A's activity with no auth
    response = await client.get(
        f"/api/v1/self-care/{activity_id_a}", # No Authorization header
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
