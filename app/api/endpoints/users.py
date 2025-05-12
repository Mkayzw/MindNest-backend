# app/api/endpoints/users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, List, Optional

from pydantic import EmailStr
from app import crud, models, schemas
from app.api import deps

router = APIRouter()

@router.get("/me", response_model=schemas.User)
def read_users_me(
    current_user: models.User = Depends(deps.get_current_active_user)
) -> Any:
    """
    Get current user.
    """
    return current_user

@router.get("/{user_id}", response_model=schemas.User)
def read_user_by_id(
    user_id: int,
    current_user: models.User = Depends(deps.get_current_active_superuser), # Or a less restrictive dependency
    db: Session = Depends(deps.get_db)
) -> Any:
    """
    Get a specific user by id. Only superusers can access this.
    """
    user = crud.user.get_user(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Add more authorization logic if needed, e.g. if current_user.id == user_id
    return user

@router.put("/me", response_model=schemas.User)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    password: Optional[str] = None, # Example: allow password update
    full_name: Optional[str] = None, # Example: allow full_name update
    email: Optional[EmailStr] = None, # Example: allow email update
    current_user: models.User = Depends(deps.get_current_active_user),
):
    """
    Update own user.
    """
    user_in_update = {}
    if password is not None:
        user_in_update["password"] = password
    if full_name is not None:
        user_in_update["full_name"] = full_name
    if email is not None:
        user_in_update["email"] = email
    
    # You might want to create a UserUpdate schema for this
    # For now, we pass a dict to the crud function
    user = crud.user.update_user(db, user_id=current_user.id, user_in=user_in_update)
    return user