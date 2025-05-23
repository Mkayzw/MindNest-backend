import pytest
from httpx import AsyncClient
from fastapi import status
from typing import Tuple

import secrets
from typing import Tuple # Ensure Tuple is imported

# Helper function to register, login a user, and fetch their ID
async def register_login_create_user(
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
    unique_email = f"testuser_journal_{email_suffix}_{random_component}@example.com"
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
async def test_create_journal_entry_success(client: AsyncClient):
    auth_token, user_id = await register_login_create_user(client, "create_success")
    
    journal_payload = {
        "title": "My First Journal",
        "content": "This is the content of my first journal entry.",
        "mood": "Happy"
    }
    
    response = await client.post(
        "/api/v1/journals/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=journal_payload,
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == journal_payload["title"]
    assert data["content"] == journal_payload["content"]
    assert data["mood"] == journal_payload["mood"]
    assert "id" in data
    assert data["user_id"] == user_id # Assuming the field is user_id based on model

@pytest.mark.asyncio
async def test_create_journal_entry_no_auth(client: AsyncClient):
    journal_payload = {
        "title": "No Auth Journal",
        "content": "This should not be created.",
        "mood": "Sad"
    }
    response = await client.post(
        "/api/v1/journals/",
        json=journal_payload, # No Authorization header
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_update_journal_entry_success(client: AsyncClient):
    auth_token, user_id = await register_login_create_user(client, "update_success")
    
    # Create an entry
    initial_payload = {"title": "Initial Title", "content": "Initial content.", "mood": "Okay"}
    create_response = await client.post(
        "/api/v1/journals",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=initial_payload,
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    journal_id = create_response.json()["id"]

    # Update the entry
    update_payload = {"title": "Updated Title", "content": "Updated content!", "mood": "Great"}
    update_response = await client.put(
        f"/api/v1/journals/{journal_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=update_payload,
    )
    
    assert update_response.status_code == status.HTTP_200_OK
    data = update_response.json()
    assert data["id"] == journal_id
    assert data["title"] == update_payload["title"]
    assert data["content"] == update_payload["content"]
    assert data["mood"] == update_payload["mood"]
    assert data["user_id"] == user_id

@pytest.mark.asyncio
async def test_update_journal_entry_not_owned(client: AsyncClient):
    # User A creates an entry
    auth_token_a, _ = await register_login_create_user(client, "update_not_owned_user_a")
    initial_payload_a = {"title": "User A's Private Entry", "content": "Content A", "mood": "Secret"}
    create_response_a = await client.post(
        "/api/v1/journals",
        headers={"Authorization": f"Bearer {auth_token_a}"},
        json=initial_payload_a,
    )
    assert create_response_a.status_code == status.HTTP_201_CREATED
    journal_id_a = create_response_a.json()["id"]

    # User B gets a token
    auth_token_b, _ = await register_login_create_user(client, "update_not_owned_user_b")
    update_payload_b = {"title": "Attempted Update by B", "content": "New content by B", "mood": "Sneaky"}

    # User B attempts to PUT User A's entry
    response_b = await client.put(
        f"/api/v1/journals/{journal_id_a}",
        headers={"Authorization": f"Bearer {auth_token_b}"},
        json=update_payload_b,
    )
    assert response_b.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_update_journal_entry_no_auth(client: AsyncClient):
    # User A creates an entry
    auth_token_a, _ = await register_login_create_user(client, "update_no_auth_user_a")
    initial_payload_a = {"title": "Entry for No Auth Update", "content": "Content", "mood": "Testy"}
    create_response_a = await client.post(
        "/api/v1/journals",
        headers={"Authorization": f"Bearer {auth_token_a}"},
        json=initial_payload_a,
    )
    assert create_response_a.status_code == status.HTTP_201_CREATED
    journal_id_a = create_response_a.json()["id"]

    update_payload = {"title": "Updated Title No Auth", "content": "This should not work.", "mood": "Failed"}
    
    # Attempt to PUT User A's entry with no auth
    response = await client.put(
        f"/api/v1/journals/{journal_id_a}",
        json=update_payload, # No Authorization header
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_delete_journal_entry_success(client: AsyncClient):
    auth_token, _ = await register_login_create_user(client, "delete_success")
    
    # Create an entry
    payload = {"title": "To Be Deleted", "content": "Delete me.", "mood": "Fleeting"}
    create_response = await client.post(
        "/api/v1/journals",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=payload,
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    journal_id = create_response.json()["id"]

    # Delete the entry
    delete_response = await client.delete(
        f"/api/v1/journals/{journal_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert delete_response.status_code == status.HTTP_200_OK
    # Optionally, assert the deleted entry data is returned
    assert delete_response.json()["id"] == journal_id 

    # Try to GET the deleted entry
    get_response = await client.get(
        f"/api/v1/journals/{journal_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert get_response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_delete_journal_entry_not_owned(client: AsyncClient):
    # User A creates an entry
    auth_token_a, _ = await register_login_create_user(client, "delete_not_owned_user_a")
    payload_a = {"title": "User A's Entry to Protect", "content": "Content A", "mood": "Safe"}
    create_response_a = await client.post(
        "/api/v1/journals",
        headers={"Authorization": f"Bearer {auth_token_a}"},
        json=payload_a,
    )
    assert create_response_a.status_code == status.HTTP_201_CREATED
    journal_id_a = create_response_a.json()["id"]

    # User B gets a token
    auth_token_b, _ = await register_login_create_user(client, "delete_not_owned_user_b")

    # User B attempts to DELETE User A's entry
    delete_response_b = await client.delete(
        f"/api/v1/journals/{journal_id_a}",
        headers={"Authorization": f"Bearer {auth_token_b}"},
    )
    assert delete_response_b.status_code == status.HTTP_404_NOT_FOUND

    # Verify User A's entry still exists
    get_response_a = await client.get(
        f"/api/v1/journals/{journal_id_a}",
        headers={"Authorization": f"Bearer {auth_token_a}"}
    )
    assert get_response_a.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_delete_journal_entry_no_auth(client: AsyncClient):
    # User A creates an entry
    auth_token_a, _ = await register_login_create_user(client, "delete_no_auth_user_a")
    payload_a = {"title": "Entry for No Auth Delete", "content": "Content", "mood": "Testy"}
    create_response_a = await client.post(
        "/api/v1/journals",
        headers={"Authorization": f"Bearer {auth_token_a}"},
        json=payload_a,
    )
    assert create_response_a.status_code == status.HTTP_201_CREATED
    journal_id_a = create_response_a.json()["id"]

    # Attempt to DELETE User A's entry with no auth
    response = await client.delete(
        f"/api/v1/journals/{journal_id_a}", # No Authorization header
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

    # Verify User A's entry still exists
    get_response_a = await client.get(
        f"/api/v1/journals/{journal_id_a}",
        headers={"Authorization": f"Bearer {auth_token_a}"}
    )
    assert get_response_a.status_code == status.HTTP_200_OK

@pytest.mark.asyncio
async def test_list_journal_entries_success(client: AsyncClient):
    # User A setup and entries
    auth_token_a, user_id_a = await register_login_create_user(client, "list_user_a")
    for i in range(2): # Create 2 entries for User A
        await client.post(
            "/api/v1/journals/",
            headers={"Authorization": f"Bearer {auth_token_a}"},
            json={"title": f"User A Entry {i+1}", "content": "Content...", "mood": "Neutral"},
        )

    # User B setup and entry
    auth_token_b, _ = await register_login_create_user(client, "list_user_b") # User ID B not needed for this test logic
    await client.post(
        "/api/v1/journals/",
        headers={"Authorization": f"Bearer {auth_token_b}"},
        json={"title": "User B Entry 1", "content": "Content...", "mood": "Curious"},
    )

    # List entries as User A
    response = await client.get(
        "/api/v1/journals/",
        headers={"Authorization": f"Bearer {auth_token_a}"},
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2 # Should only list User A's entries
    for entry in data:
        assert entry["user_id"] == user_id_a
        assert "User A Entry" in entry["title"]

@pytest.mark.asyncio
async def test_list_journal_entries_no_auth(client: AsyncClient):
    response = await client.get("/api/v1/journals/") # No Authorization header
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_get_specific_journal_entry_success(client: AsyncClient):
    auth_token, user_id = await register_login_create_user(client, "get_specific_success")
    
    # Create an entry
    journal_payload = {"title": "Specific Entry", "content": "Details...", "mood": "Focused"}
    create_response = await client.post(
        "/api/v1/journals/",
        headers={"Authorization": f"Bearer {auth_token}"},
        json=journal_payload,
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    created_entry_data = create_response.json()
    journal_id = created_entry_data["id"]

    # Get the specific entry
    response = await client.get(
        f"/api/v1/journals/{journal_id}",
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["id"] == journal_id
    assert data["title"] == journal_payload["title"]
    assert data["user_id"] == user_id

@pytest.mark.asyncio
async def test_get_specific_journal_entry_not_owned(client: AsyncClient):
    # User A creates an entry
    auth_token_a, _ = await register_login_create_user(client, "get_not_owned_user_a")
    journal_payload_a = {"title": "User A's Entry", "content": "Content A", "mood": "Private"}
    create_response_a = await client.post(
        "/api/v1/journals/",
        headers={"Authorization": f"Bearer {auth_token_a}"},
        json=journal_payload_a,
    )
    assert create_response_a.status_code == status.HTTP_201_CREATED
    journal_id_a = create_response_a.json()["id"]

    # User B gets a token
    auth_token_b, _ = await register_login_create_user(client, "get_not_owned_user_b")

    # User B attempts to GET User A's entry
    response_b = await client.get(
        f"/api/v1/journals/{journal_id_a}",
        headers={"Authorization": f"Bearer {auth_token_b}"},
    )
    assert response_b.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_get_specific_journal_entry_not_found(client: AsyncClient):
    auth_token, _ = await register_login_create_user(client, "get_not_found")
    
    response = await client.get(
        "/api/v1/journals/9999999", # Non-existent ID
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND

@pytest.mark.asyncio
async def test_get_specific_journal_entry_no_auth(client: AsyncClient):
    # User A creates an entry
    auth_token_a, _ = await register_login_create_user(client, "get_no_auth_user_a")
    journal_payload_a = {"title": "User A's Entry for No Auth Test", "content": "Content", "mood": "Testy"}
    create_response_a = await client.post(
        "/api/v1/journals/",
        headers={"Authorization": f"Bearer {auth_token_a}"},
        json=journal_payload_a,
    )
    assert create_response_a.status_code == status.HTTP_201_CREATED
    journal_id_a = create_response_a.json()["id"]

    # Attempt to GET User A's entry with no auth
    response = await client.get(
        f"/api/v1/journals/{journal_id_a}", # No Authorization header
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
