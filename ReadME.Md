# MindNest Backend

Welcome to the MindNest Backend! This repository houses the backend codebase for the MindNest application, a platform designed to help users manage their mental health and well-being.

## Table of Contents

- [Introduction](#introduction)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Project Structure](#project-structure)
- [Directory Responsibilities](#directory-responsibilities)
- [Example main.py](#example-mainpy)
- [Why This Structure Rocks](#why-this-structure-rocks)

## Introduction

MindNest is a comprehensive mental health management platform that aims to empower users to take control of their mental well-being. This backend repository is responsible for handling the server-side logic, data storage, and API endpoints.

## Getting Started

### Prerequisites

Before you begin, ensure you have met the following requirements:

- Python 3.9 or higher
- Supabase account and project (provides a PostgreSQL database)   

### Installation

1.  **Set up the environment:**
    *   Copy the example environment file:
        ```bash
        cp .env.example .env
        ```
    *   Open the `.env` file and fill in your actual values for `DATABASE_URL` (your Supabase connection string) and `SECRET_KEY`.

2.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application:**
    ```bash
    uvicorn app.main:app --reload
    ```
    The application will typically be available at `http://127.0.0.1:8000`.


1. Clone the repository:

   ```bash
   git clone

1. Clone the repository:

   ```bash
   git clone URL_ADDRESS.com/yourusername/mindnest-backend.git
   cd mindnest-backend
   ```
2. Create a virtual environment (optional but recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
   ```
3. Install the dependencies:

   ```bash
   pip install -r requirements.txt
   ```
4. Set up your environment variables:   

   Get your Supabase connection string from your Supabase project's dashboard (Settings > Database > Connection string) and set it as `DATABASE_URL` in your `.env` file.
   Example format: `postgresql://postgres:[YOUR-PASSWORD]@[AWS-REGION].pooler.supabase.com:5432/postgres`
   Also, set your `JWT_SECRET`.
5. Run the application:

   ```bash
   uvicorn app.main:app --reload
   ```
## Project Structure
mindnest-backend/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py
│   ├── database.py
│   ├── dependencies.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── journal.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── journal.py
│   ├── crud/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── journal.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py
│   │       ├── users.py
│   │       └── journals.py
│   └── services/
│       ├── __init__.py
│       └── notification.py
├── alembic/                  # (optional) for migrations
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_users.py
│   └── test_journals.py
├── .env                      # environment variables (not in VCS)
├── requirements.txt
└── README.md
📚 Directory Responsibilities
app/main.py

Entrypoint: Instantiates FastAPI, includes routers, initializes DB, and loads middleware.

app/core/config.py

Configuration: Loads environment variables (via python-dotenv) for DB URLs, JWT secrets, etc.

Use Pydantic’s BaseSettings for typed config.

app/database.py

DB Setup: Creates SQLAlchemy Engine, SessionLocal, and Base.

Provides a get_db dependency.

app/dependencies.py

Shared Dependencies:

get_db() for DB sessions

get_current_user() for JWT-backed auth

app/models/

SQLAlchemy Models:

user.py: User table (id, email, hashed_pw, created_at, etc.)

journal.py: JournalEntry (id, user_id FK, mood, content, timestamp)

app/schemas/

Pydantic Schemas (request & response DTOs):

user.py: UserCreate, UserRead, UserLogin

journal.py: JournalCreate, JournalRead

app/crud/

CRUD Functions (data access layer):

user.py: get_user_by_email(), create_user(), authenticate_user()

journal.py: create_journal(), get_journals_for_user()

app/api/v1/

API Routers:

### Running the Application

To start the development server, run:

```bash
uvicorn app.main:app --reload
```

This command will start the Uvicorn server, and it will automatically reload when code changes are detected. You can access the API at `http://127.0.0.1:8000`.

### API Endpoints Overview

auth.py: /auth/register, /auth/login

users.py: /users/me, /users/{id}

journals.py: /journals/ endpoints

Versioned under /api/v1 so you can add /api/v2 later without breaking clients.

app/services/

Business-Logic-Adjunct Services:

notification.py: Push notifications, email reminders, etc.

Keeps non-CRUD logic out of your routers and CRUD modules.

alembic/ (optional)

Migrations: Auto-generated scripts for evolving your schema.

tests/

Unit & Integration Tests:

Use pytest + SQLAlchemy in-memory SQLite fixture.

conftest.py defines shared fixtures.

.env & requirements.txt

.env: Secrets & config (Git-ignored!).

requirements.txt: Pin your dependencies for reproducible installs.

🔧 Example main.py
python
Copy
Edit
from fastapi import FastAPI
from app.core.config import settings
from app.database import engine, Base
from app.api.v1 import auth, users, journals

# Create tables (for dev; use Alembic for prod)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MindNest API", version="1.0")

# Include routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(journals.router, prefix="/api/v1/journals", tags=["journals"])
🚀 Why This Structure Rocks
Separation of Concerns: Models ↔ Schemas ↔ CRUD ↔ Routers ↔ Services

Versioning: Easy to evolve your API without breaking clients.

Testable: Clear modules to target unit tests and integration tests.

Scalable: Drop in new features (e.g., mood tracker, self-care logs) by copying the pattern.

Maintainable: Other devs (or future you) will thank you for the clarity.

