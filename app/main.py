# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.api import api_router
from app.database import engine, Base
from app.models import user, journal, mental_health  # Ensure all models are imported so Base knows about them

# Create all database tables
# This is suitable for development. For production, consider using Alembic migrations.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MindNest API",
    openapi_url="/api/v1/openapi.json"
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/ping")
def pong():
    return {"ping": "pong!"}

# If you are using Uvicorn to run, you might have something like this
# at the end of the file for direct execution (though typically not in main.py for production):
# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)