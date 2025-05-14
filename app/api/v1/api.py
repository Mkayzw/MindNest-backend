# app/api/v1/api.py
from fastapi import APIRouter

from app.api.endpoints import auth, users, journal, moods, stress, self_care, analytics, storage

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(journal.router, prefix="/journals", tags=["journals"])
api_router.include_router(moods.router, prefix="/moods", tags=["moods"])
api_router.include_router(stress.router, prefix="/stress", tags=["stress"])
api_router.include_router(self_care.router, prefix="/self-care", tags=["self-care"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(storage.router, prefix="/storage", tags=["storage"])