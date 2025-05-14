# MindNest API

MindNest is a comprehensive mental wellness API that helps users track their moods, journal feelings, log stress triggers, practice self-care, and analyze trends over time.

## Features

- 🧠 **Auth & User Profiles** - Secure authentication with profile management
- 📖 **Journal Entries** - Create and manage journal entries with text, audio, and images
- 🎭 **Mood Tracking** - Log moods with optional notes
- 💥 **Stress & Trigger Events** - Track stressful events and their triggers
- 💆🏽 **Self-Care Activities** - Manage self-care tasks and mark completions
- 📊 **Trends & Analytics** - View mood trends, journaling streaks, and stress patterns
- 📁 **Media Uploads** - Upload and manage images and audio recordings

## Tech Stack

- **FastAPI** - High-performance web framework
- **SQLAlchemy** - SQL toolkit and ORM
- **PostgreSQL (Supabase)** - Database backend
- **JWT Authentication** - Secure user authentication
- **Pydantic** - Data validation and settings management

## Getting Started

### Prerequisites

- Python 3.8+
- PostgreSQL or Supabase account

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/mindnest-api.git
   cd mindnest-api
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root with the following variables:
   ```
   DATABASE_URL=postgresql://username:password@host:port/dbname
   SECRET_KEY=your-secret-key
   ```

### Running the Application

```
python run.py
```

The API will be available at http://127.0.0.0:8000. You can access the interactive API documentation at http://127.0.0.0:8000/docs.

## API Endpoints

### Authentication

- `POST /api/v1/auth/register` - Register a new user
- `POST /api/v1/auth/login` - Log in and get access token

### User Profiles

- `GET /api/v1/users/me` - Get current user profile
- `PATCH /api/v1/users/me` - Update user profile

### Journal Entries

- `GET /api/v1/journals` - List all journal entries
- `POST /api/v1/journals` - Create a new journal entry
- `GET /api/v1/journals/{id}` - Get a specific journal entry
- `PUT /api/v1/journals/{id}` - Update a journal entry
- `DELETE /api/v1/journals/{id}` - Delete a journal entry

### Mood Tracking

- `POST /api/v1/moods` - Log a new mood
- `GET /api/v1/moods` - List all mood logs
- `GET /api/v1/moods/{id}` - Get a specific mood log
- `DELETE /api/v1/moods/{id}` - Delete a mood log

### Stress Events

- `POST /api/v1/stress` - Log a new stress event
- `GET /api/v1/stress` - List all stress events
- `GET /api/v1/stress/{id}` - Get a specific stress event
- `DELETE /api/v1/stress/{id}` - Delete a stress event

### Self-Care Activities

- `POST /api/v1/self-care` - Create a new self-care activity
- `GET /api/v1/self-care` - List all self-care activities
- `GET /api/v1/self-care/{id}` - Get a specific self-care activity
- `PATCH /api/v1/self-care/{id}` - Update a self-care activity
- `DELETE /api/v1/self-care/{id}` - Delete a self-care activity

### Analytics

- `GET /api/v1/analytics/mood-trend` - Get mood trends over time
- `GET /api/v1/analytics/stress-patterns` - Get patterns in stress triggers
- `GET /api/v1/analytics/journaling-streak` - Get journaling streak
- `GET /api/v1/analytics/recommendations` - Get personalized recommendations

### Storage

- `POST /api/v1/storage/journal-media` - Upload media for journal entries
- `POST /api/v1/storage/profile-pic` - Upload a profile picture
- `GET /api/v1/storage/journal-media/{filename}` - Get journal media
- `GET /api/v1/storage/profile-pic/{filename}` - Get profile picture

## Data Models

### User

```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "User Name",
  "bio": "About me",
  "avatar_url": "/api/v1/storage/profile-pic/profile_1.jpg",
  "wellness_goals": "Reduce stress and improve sleep",
  "is_active": true,
  "created_at": "2023-01-01T00:00:00.000Z",
  "updated_at": "2023-01-01T00:00:00.000Z"
}
```

### Journal Entry

```json
{
  "id": 1,
  "owner_id": 1,
  "title": "My Journal Entry",
  "content": "Today was a good day...",
  "mood": "happy",
  "created_at": "2023-01-01T00:00:00.000Z",
  "updated_at": "2023-01-01T00:00:00.000Z"
}
```

### Mood Log

```json
{
  "id": 1,
  "user_id": 1,
  "mood_level": 4,
  "note": "Feeling good after exercise",
  "logged_at": "2023-01-01T00:00:00.000Z"
}
```

### Stress Event

```json
{
  "id": 1,
  "user_id": 1,
  "description": "Had a difficult meeting at work",
  "trigger_tag": "Work",
  "intensity": 3,
  "timestamp": "2023-01-01T00:00:00.000Z"
}
```

### Self-Care Activity

```json
{
  "id": 1,
  "user_id": 1,
  "name": "Morning Meditation",
  "description": "10 minutes of mindfulness meditation",
  "is_completed": false,
  "scheduled_for": "2023-01-01T08:00:00.000Z",
  "completed_at": null,
  "created_at": "2023-01-01T00:00:00.000Z"
}
```

## Security

The API uses JWT tokens for authentication. Include the token in the `Authorization` header of your requests:

```
Authorization: Bearer <your_token>
```

Row Level Security (RLS) ensures that users can only access their own data.

## Development

### Project Structure

```
mindnest-api/
├── app/
│   ├── api/
│   │   ├── endpoints/
│   │   │   ├── auth.py
│   │   │   ├── journal.py
│   │   │   ├── moods.py
│   │   │   ├── stress.py
│   │   │   ├── self_care.py
│   │   │   ├── analytics.py
│   │   │   ├── storage.py
│   │   │   └── users.py
│   │   ├── deps.py
│   │   └── v1/
│   │       └── api.py
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── crud/
│   │   ├── journal.py
│   │   ├── mental_health.py
│   │   └── user.py
│   ├── models/
│   │   ├── journal.py
│   │   ├── mental_health.py
│   │   └── user.py
│   ├── schemas/
│   │   ├── journal.py
│   │   ├── mental_health.py
│   │   ├── token.py
│   │   └── user.py
│   ├── database.py
│   ├── dependencies.py
│   └── main.py
├── uploads/
│   ├── journal-media/
│   └── profile-pics/
├── .env
├── requirements.txt
├── run.py
└── README.md
```

## License

This project is licensed under the MIT License.

## Acknowledgements

- FastAPI for the amazing web framework
- Supabase for the robust database and authentication service
- All the contributors and users who make this project better

