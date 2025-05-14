# app/models/__init__.py
from .user import User
from .journal import JournalEntry
from .mental_health import MoodLog, StressEvent, SelfCareActivity

# This line is important for Alembic or similar migration tools to find the models
# when Base.metadata.create_all(bind=engine) is called, or when generating migrations.
from app.database import Base