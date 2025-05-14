# app/api/endpoints/storage.py
import os
import secrets
from typing import List, Optional
from datetime import datetime, timedelta
import base64
import aiohttp
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, Query, Response
from fastapi.responses import RedirectResponse, FileResponse
from sqlalchemy.orm import Session
import shutil
from pathlib import Path

from app import crud, models
from app.api.deps import get_db, get_current_active_user
from app.core.config import settings

router = APIRouter()

# Fallback to local storage if Supabase configuration is not set
USE_LOCAL_STORAGE = not (settings.SUPABASE_URL and settings.SUPABASE_KEY)

if USE_LOCAL_STORAGE:
    # Create upload directories if they don't exist
    UPLOAD_DIR = Path("uploads")
    JOURNAL_MEDIA_DIR = UPLOAD_DIR / "journal-media"
    PROFILE_PICS_DIR = UPLOAD_DIR / "profile-pics"

    JOURNAL_MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    PROFILE_PICS_DIR.mkdir(parents=True, exist_ok=True)

# Allowed file extensions
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}
ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".ogg", ".m4a"}

def validate_file_extension(file: UploadFile, allowed_extensions: set) -> bool:
    file_ext = os.path.splitext(file.filename)[1].lower()
    return file_ext in allowed_extensions

async def upload_to_supabase(file: UploadFile, bucket: str, file_path: str):
    """Upload a file to Supabase Storage"""
    url = f"{settings.SUPABASE_URL}/storage/v1/object/{bucket}/{file_path}"
    
    # Read file content
    contents = await file.read()
    
    # Reset file position to start
    await file.seek(0)
    
    headers = {
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": file.content_type
    }
    
    print(f"Uploading to Supabase URL: {url}")
    print(f"Content-Type: {file.content_type}")
    print(f"Authorization header starts with: Bearer {settings.SUPABASE_KEY[:20]}...")
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=contents, headers=headers) as response:
            if response.status != 200:
                error_text = await response.text()
                print(f"Supabase upload error: Status {response.status}, Response: {error_text}")
                
                if response.status == 404:
                    # Bucket doesn't exist
                    raise HTTPException(
                        status_code=500,
                        detail=f"Storage bucket '{bucket}' not found. Please create it in the Supabase dashboard."
                    )
                elif response.status == 403:
                    # Authentication issue
                    raise HTTPException(
                        status_code=500,
                        detail=f"Authentication error with Supabase storage. The key likely doesn't have the right permissions. Consider using the service_role key instead of the anon key, or make sure your RLS policies are set correctly."
                    )
                else:
                    raise HTTPException(
                        status_code=response.status, 
                        detail=f"Supabase storage upload failed: {error_text}"
                    )
            
            # Return the public URL
            return f"{settings.SUPABASE_URL}/storage/v1/object/public/{bucket}/{file_path}"

@router.post("/journal-media", status_code=201)
async def upload_journal_media(
    file: UploadFile = File(...),
    journal_id: Optional[int] = Form(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Upload media (image or audio) for a journal entry
    """
    # Validate file extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    if not (file_ext in ALLOWED_IMAGE_EXTENSIONS or file_ext in ALLOWED_AUDIO_EXTENSIONS):
        raise HTTPException(
            status_code=400, 
            detail=f"File type not allowed. Allowed image types: {ALLOWED_IMAGE_EXTENSIONS}, allowed audio types: {ALLOWED_AUDIO_EXTENSIONS}"
        )
    
    # Generate a unique filename
    random_filename = f"{current_user.id}_{secrets.token_hex(8)}{file_ext}"
    
    if USE_LOCAL_STORAGE:
        # Local storage implementation
        file_path = JOURNAL_MEDIA_DIR / random_filename
        
        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Generate URL for client to access the file
        media_url = f"/api/v1/storage/journal-media/{random_filename}"
        file_size = os.path.getsize(file_path)
    else:
        # Supabase storage implementation
        media_url = await upload_to_supabase(
            file, 
            settings.SUPABASE_JOURNAL_BUCKET, 
            random_filename
        )
        # We don't have direct access to the file size
        file_size = 0  # Could be estimated from file.file, but not reliable
    
    return {
        "filename": random_filename,
        "media_url": media_url,
        "content_type": file.content_type,
        "size": file_size
    }

@router.post("/profile-pic", status_code=201)
async def upload_profile_pic(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Upload a profile picture
    """
    # Validate file extension
    if not validate_file_extension(file, ALLOWED_IMAGE_EXTENSIONS):
        raise HTTPException(
            status_code=400, 
            detail=f"File type not allowed. Allowed types: {ALLOWED_IMAGE_EXTENSIONS}"
        )
    
    # Generate a unique filename (overwrite any existing profile pic)
    file_ext = os.path.splitext(file.filename)[1].lower()
    filename = f"profile_{current_user.id}{file_ext}"
    
    if USE_LOCAL_STORAGE:
        # Local storage implementation
        file_path = PROFILE_PICS_DIR / filename
        
        # Save the file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Update user profile with avatar URL
        avatar_url = f"/api/v1/storage/profile-pic/{filename}"
        file_size = os.path.getsize(file_path)
    else:
        # Supabase storage implementation
        avatar_url = await upload_to_supabase(
            file, 
            settings.SUPABASE_PROFILE_BUCKET, 
            filename
        )
        # We don't have direct access to the file size
        file_size = 0  # Could be estimated from file.file, but not reliable
    
    # Update user in database
    user_data = {"avatar_url": avatar_url}
    crud.user.update_user(db, user_id=current_user.id, user_in=user_data)
    
    return {
        "filename": filename,
        "avatar_url": avatar_url,
        "content_type": file.content_type,
        "size": file_size
    }

@router.get("/journal-media/{filename}")
async def get_journal_media(
    filename: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_active_user)
):
    """
    Retrieve journal media file
    
    This is a simplified implementation. In a production environment,
    you would need to check if the user has access to this media
    (e.g., it belongs to one of their journal entries).
    """
    # Basic security: check if the filename starts with the user's ID
    if not filename.startswith(f"{current_user.id}_"):
        raise HTTPException(status_code=403, detail="Not authorized to access this file")
    
    if USE_LOCAL_STORAGE:
        # Local storage implementation
        file_path = JOURNAL_MEDIA_DIR / filename
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(file_path)
    else:
        # Redirect to the Supabase storage URL
        return RedirectResponse(
            f"{settings.SUPABASE_URL}/storage/v1/object/public/{settings.SUPABASE_JOURNAL_BUCKET}/{filename}"
        )

@router.get("/profile-pic/{filename}")
async def get_profile_pic(filename: str):
    """
    Retrieve a profile picture
    
    Profile pictures are considered public and can be accessed by anyone
    """
    if USE_LOCAL_STORAGE:
        # Local storage implementation
        file_path = PROFILE_PICS_DIR / filename
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(file_path)
    else:
        # Redirect to the Supabase storage URL
        return RedirectResponse(
            f"{settings.SUPABASE_URL}/storage/v1/object/public/{settings.SUPABASE_PROFILE_BUCKET}/{filename}"
        ) 