import pytest
from httpx import AsyncClient
from fastapi import status # For status codes

# Use a unique email for each test run where a user is created to avoid conflicts
# if tests are run multiple times without cleaning the database.
# A simple way is to append a timestamp or use a library like Faker.
# For now, just use distinct email strings.

import secrets

@pytest.mark.asyncio
async def test_successful_registration(client: AsyncClient):
    r_hex = secrets.token_hex(4)
    unique_email = f"testuser_reg_success_{r_hex}@example.com"
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "testpassword123",
            "full_name": "Test User Success"
        },
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == unique_email
    assert data["full_name"] == "Test User Success"
    assert "id" in data
    assert data["is_active"] is True
    assert "hashed_password" not in data # Ensure password is not returned


@pytest.mark.asyncio
async def test_registration_existing_email(client: AsyncClient):
    r_hex = secrets.token_hex(4)
    unique_email = f"testuser_dup_email_{r_hex}@example.com"
    # First, register a user
    response1 = await client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "testpassword123",
            "full_name": "Test User Duplicate"
        },
    )
    assert response1.status_code == status.HTTP_201_CREATED

    # Then, attempt to register another user with the same email
    response2 = await client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": "anotherpassword",
            "full_name": "Another User"
        },
    )
    assert response2.status_code == status.HTTP_400_BAD_REQUEST # Or 409 Conflict
    # Assuming your API returns a detail message like this. Adjust if necessary.
    assert "The user with this email already exists in the system." in response2.json().get("detail", "")


@pytest.mark.asyncio
async def test_successful_login(client: AsyncClient):
    r_hex = secrets.token_hex(4)
    unique_email = f"testuser_login_success_{r_hex}@example.com"
    password = f"login_password_{r_hex}"
    # Register user
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": password,
            "full_name": "Login Test User"
        },
    )
    # Login
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": unique_email, "password": password}, # Form data
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_incorrect_password(client: AsyncClient):
    r_hex = secrets.token_hex(4)
    unique_email = f"testuser_login_fail_pass_{r_hex}@example.com"
    correct_password = f"correct_password_{r_hex}"
    incorrect_password = f"incorrect_password_{r_hex}"
    # Register user
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": unique_email,
            "password": correct_password,
            "full_name": "Login Fail Pass User"
        },
    )
    # Attempt login with incorrect password
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": unique_email, "password": incorrect_password},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    # Assuming your API returns a detail message like this. Adjust if necessary.
    assert "Incorrect email or password" in response.json().get("detail", "")


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    r_hex = secrets.token_hex(4)
    non_existent_email = f"nonexistentuser_{r_hex}@example.com"
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": non_existent_email, "password": "anypassword"},
    )
    # Depending on API design, this could be 401 or 404.
    # 401 is often preferred to prevent user enumeration.
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    # Adjust assertion based on your API's actual error message
    assert "Incorrect email or password" in response.json().get("detail", "") # Or "User not found"
