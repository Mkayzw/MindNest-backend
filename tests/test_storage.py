import pytest
from httpx import AsyncClient
from fastapi import status, UploadFile
from typing import Tuple
import io
import secrets
from unittest.mock import AsyncMock # For mocking async methods

# Helper function to register, login a user, and fetch their ID and token
async def register_login_get_user_token_and_id(
    client: AsyncClient, 
    email_suffix: str, 
    password_suffix: str = "password", 
    full_name_suffix: str = "User"
) -> Tuple[str, int]:
    random_component = secrets.token_hex(4)
    unique_email = f"testuser_storage_{email_suffix}_{random_component}@example.com"
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

# --- Upload Journal Media Tests ---

@pytest.mark.asyncio
async def test_upload_journal_media_success(client: AsyncClient, mocker):
    auth_token, user_id = await register_login_get_user_token_and_id(client, "upload_journal_media")
    
    # Mock Supabase client
    # Assuming supabase client is accessed via app.services.storage_service.supabase
    # Adjust the path according to your project structure.
    # This path might be where the client is *used*, e.g., in your storage router/service file.

    # Mock aiohttp.ClientSession.post
    mock_post_response = AsyncMock()
    mock_post_response.status = 200 # Simulate successful Supabase upload
    mock_post_response.text = AsyncMock(return_value='{"Key": "some_key"}') # Simulate Supabase response if needed by handler

    mock_session_instance = AsyncMock()
    mock_session_instance.post = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_post_response)))

    mocker.patch('app.api.endpoints.storage.aiohttp.ClientSession', return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_session_instance)))

    # To assert the URL provided by the API, which is constructed from settings and filename
    expected_file_url_part = f"user_{user_id}/journal-media/test_image.png" # Simplified, actual filename is random in endpoint
    # The endpoint generates a random filename, so we can't predict the exact URL easily
    # We will check if the upload was called.

    files = {'file': ('test_image.png', b'fakeimagedata', 'image/png')}
    
    response = await client.post(
        "/api/v1/storage/journal-media",
        headers={"Authorization": f"Bearer {auth_token}"},
        files=files,
    )
    
    assert response.status_code == status.HTTP_200_OK # Or 201, depending on API
    data = response.json()
    assert "media_url" in data # Endpoint returns 'media_url'
    # The filename is randomized in the endpoint, so we check parts of the URL
    assert f"user_{current_user.id}" in data["media_url"] # Assuming current_user.id can be accessed if needed, or check general pattern
    assert data["media_url"].endswith(".png") # Check extension
    assert data["content_type"] == "image/png"

    mock_session_instance.post.assert_called_once()
    args, kwargs = mock_session_instance.post.call_args
    # args[0] is the URL, check if it contains the bucket and filename pattern
    assert settings.SUPABASE_JOURNAL_BUCKET in args[0]
    # The filename in the URL will be the randomized one, e.g. user_{id}_{random_hex}.png
    # Example: "https://<project_ref>.supabase.co/storage/v1/object/journal-media/user_1_abcdef1234567890.png"
    # We can check if it starts with the user_id and ends with the correct extension.
    uploaded_filename_in_url = args[0].split("/")[-1]
    assert uploaded_filename_in_url.startswith(f"{user_id}_")
    assert uploaded_filename_in_url.endswith(".png")
    
    assert kwargs['headers']['Content-Type'] == 'image/png'
    assert isinstance(kwargs['data'], bytes)


@pytest.mark.asyncio
async def test_upload_journal_media_no_auth(client: AsyncClient):
    files = {'file': ('test_image.png', b'fakeimagedata', 'image/png')}
    response = await client.post(
        "/api/v1/storage/journal-media",
        files=files,
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

@pytest.mark.asyncio
async def test_upload_journal_media_no_file(client: AsyncClient, mocker): # Mocker might not be needed if no auth
    auth_token, _ = await register_login_get_user_token_and_id(client, "upload_journal_no_file")
    
    response = await client.post(
        "/api/v1/storage/journal-media",
        headers={"Authorization": f"Bearer {auth_token}"},
        # No files attached
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# --- Upload Profile Picture Tests ---

@pytest.mark.asyncio
async def test_upload_profile_pic_success(client: AsyncClient, mocker):
    auth_token, user_id = await register_login_get_user_token_and_id(client, "upload_profile_pic")
    
    mock_supabase_client = AsyncMock()
    # Supabase's Python client upload might return a dict like {'data': {'Key': 'path'}, 'error': None}
    # or raise an exception on error. For success, we care about the path.
    # The actual return from supabase-py might be just the key/path string or an object.
    # Let's assume it returns an object from which a URL can be derived or the path itself.
    # For simplicity, let's assume the service constructs the URL.
    
    mock_post_response = AsyncMock()
    mock_post_response.status = 200
    mock_post_response.text = AsyncMock(return_value='{"Key": "some_key_profile"}')

    mock_session_instance = AsyncMock()
    mock_session_instance.post = AsyncMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_post_response)))
    
    mocker.patch('app.api.endpoints.storage.aiohttp.ClientSession', return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_session_instance)))
    
    # Mock the CRUD operation for updating user avatar
    # This path depends on where `crud.user.update_user` is called from within the endpoint.
    # Assuming it's `app.api.endpoints.storage.crud.user.update_user`
    mocker.patch('app.api.endpoints.storage.crud.user.update_user', return_value=models.User(id=user_id, email="test@example.com", avatar_url="new_url"))


    files = {'file': ('profile.jpg', b'fakejpegdata', 'image/jpeg')}
    
    response = await client.post(
        "/api/v1/storage/profile-pic",
        headers={"Authorization": f"Bearer {auth_token}"},
        files=files,
    )
    
    assert response.status_code == status.HTTP_201_CREATED # Endpoint uses 201
    data = response.json()
    assert "avatar_url" in data
    # The filename is deterministic for profile pics: profile_{user_id}.ext
    expected_filename = f"profile_{user_id}.jpg"
    assert data["filename"] == expected_filename
    assert data["avatar_url"].endswith(f"{settings.SUPABASE_PROFILE_BUCKET}/{expected_filename}")
    
    mock_session_instance.post.assert_called_once()
    args_upload, kwargs_upload = mock_session_instance.post.call_args
    assert settings.SUPABASE_PROFILE_BUCKET in args_upload[0]
    assert expected_filename in args_upload[0] # Check if constructed URL contains the expected filename
    assert kwargs_upload['headers']['Content-Type'] == 'image/jpeg'
    assert isinstance(kwargs_upload['data'], bytes)

    # Check if user crud update was called
    app.api.endpoints.storage.crud.user.update_user.assert_called_once()
    args_crud, _ = app.api.endpoints.storage.crud.user.update_user.call_args
    assert args_crud[1] == user_id # user_id
    assert "avatar_url" in args_crud[2] # user_in dict
    assert args_crud[2]["avatar_url"] == data["avatar_url"]


@pytest.mark.asyncio
async def test_upload_profile_pic_no_auth(client: AsyncClient):
    files = {'file': ('profile.jpg', b'fakejpegdata', 'image/jpeg')}
    response = await client.post(
        "/api/v1/storage/profile-pic",
        files=files,
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# --- Get Journal Media Tests ---

@pytest.mark.asyncio
async def test_get_journal_media_success(client: AsyncClient, mocker):
    auth_token, user_id = await register_login_get_user_token_and_id(client, "get_journal_media")
    # For GET requests that redirect, no direct Supabase client call is made from the endpoint itself
    # that needs mocking IF settings.USE_LOCAL_STORAGE is False. It just constructs a URL.
    # The filename in the path should be the one stored (which includes user_id prefix for journal media)
    # The endpoint itself generates a random filename, so we need to get it from a previous upload.
    # For this test, let's assume a file "user_{user_id}_test_image.png" exists.
    # This requires a bit of setup if we don't have an actual uploaded file's name.
    # Let's simulate an upload first to get a valid filename, or use a predictable pattern if possible.
    # The endpoint uses `random_filename = f"{current_user.id}_{secrets.token_hex(8)}{file_ext}"`
    # So, we can't directly predict.
    #
    # Option 1: Test with local storage by overriding settings (complex for this structure).
    # Option 2: First upload, then get (makes test dependent, but more realistic).
    # Option 3: Mock the filename generation or make it predictable for test (intrusive).
    # Option 4: For this test, we will assume the redirect happens correctly if Supabase is configured,
    # and the main logic to test is the path construction and auth.
    # We won't mock Supabase calls for GET if it's just a redirect.
    # The critical part is the auth check and correct filename in path.
    
    # To test the auth part and filename use, we'll construct a filename that would be valid for the user
    test_filename = f"{user_id}_sometestimage.png"


    response = await client.get(
        f"/api/v1/storage/journal-media/{test_filename}", 
        headers={"Authorization": f"Bearer {auth_token}"},
        follow_redirects=False # Important for testing redirects
    )
    
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["Location"] == mock_public_url
    # No Supabase client call to mock for redirect if USE_LOCAL_STORAGE is False


@pytest.mark.asyncio
async def test_get_journal_media_no_auth(client: AsyncClient, mocker):
    filename = "user_X/test_image.png" 
    response = await client.get(
        f"/api/v1/storage/journal-media/{filename}",
        follow_redirects=False
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

# --- Get Profile Picture Tests ---

@pytest.mark.asyncio
async def test_get_profile_pic_success(client: AsyncClient, mocker):
    auth_token, user_id = await register_login_get_user_token_and_id(client, "get_profile_pic")
    # Similar to get_journal_media, for profile pics, the filename is predictable: profile_{user_id}.ext
    test_filename = f"profile_{user_id}.jpg" # Construct a plausible filename for the user
    
    # Expected redirect URL
    expected_redirect_url = f"{settings.SUPABASE_URL}/storage/v1/object/public/{settings.SUPABASE_PROFILE_BUCKET}/{test_filename}"

    response = await client.get(
        f"/api/v1/storage/profile-pic/{test_filename}",
        headers={"Authorization": f"Bearer {auth_token}"},
        follow_redirects=False
    )
    
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT
    assert response.headers["Location"] == expected_redirect_url
    # No Supabase client call to mock for redirect if USE_LOCAL_STORAGE is False


@pytest.mark.asyncio
async def test_get_profile_pic_no_auth(client: AsyncClient, mocker):
    filename = "user_Y/profile.jpg"
    response = await client.get(
        f"/api/v1/storage/profile-pic/{filename}",
        follow_redirects=False
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
