# app/api/v1/api.py
from fastapi import APIRouter

from app.api.endpoints import auth, users, journal

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(journal.router, prefix="/journals", tags=["journals"])