# app/crud/user.py
from sqlalchemy.orm import Session
from typing import Optional

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash, verify_password
from fastapi import HTTPException

def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, hashed_password=hashed_password, full_name=user.full_name)
    try:
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Error creating user in database"
        ) from e
    return db_user

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email=email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user

def update_user(db: Session, user_id: int, user_in: dict) -> Optional[User]:
    db_user = get_user(db, user_id)
    if db_user:
        if "password" in user_in and user_in["password"]:
            hashed_password = get_password_hash(user_in["password"])
            db_user.hashed_password = hashed_password
            del user_in["password"] # remove password from dict to avoid setting it directly
        
        for key, value in user_in.items():
            if hasattr(db_user, key) and value is not None:
                setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
    return db_user