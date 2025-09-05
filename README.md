# Psyche API

FastAPI service with modular auth and mental health endpoints. PostgreSQL (e.g., Supabase) is supported; SQLite is used by default for local dev.

## Features
- Auth
  - POST /auth/register → returns { message, user { username, email } }
  - POST /auth/login → returns { message, user { id, username, email }, token }
  - Login body uses a single field `username` that can be either the actual username or the email
  - Secure password hashing (bcrypt) and JWT tokens (HS256)
- Mental Health
  - POST /mental/predict → predicts depressionState (0..3) using psyche_model.keras, stores record, and returns a suggestion
  - Optional Gemini suggestion generation (with a precise prompt template) or local fallback mapping
  - GET /mental/history/{user_id} → list of previous tests (latest first)
  - GET /mental/history/{user_id}/latest → latest test or null

## Project Structure
- main.py → app bootstrap (FastAPI lifespan), router wiring
- app/
  - controllers/ → route handlers (auth_controller.py, mental_controller.py)
  - services/ → business logic (auth_service.py, mental_service.py)
  - schemas/ → Pydantic DTOs (auth.py, mental.py)
  - models/ → SQLAlchemy models (user.py, health_test.py)
  - db/session.py → engine/session/Base + create_all()
  - core/ → config (env), security (hash/JWT)
- psyche_model.keras → Keras model file used by /mental/predict

## Setup
1. Create a virtual environment (recommended).
2. Install dependencies:
```
pip install -r requirements.txt
```
3. Create a .env file and set values:
   - DATABASE_URL for Postgres (e.g., Supabase). If not set, uses SQLite at ./app.db
   - SECRET_KEY (JWT)
   - Optional Gemini:
     - USE_GEMINI_SUGGESTION=true
     - GEMINI_API_KEY=your_key
     - GEMINI_MODEL=gemini-1.5-flash (default)

## Run
```
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
Open http://127.0.0.1:8000/docs for interactive docs.

## API Reference (examples)

### Auth
- Register
  - Request (POST /auth/register):
    {"username":"alice","email":"alice@example.com","password":"secret123"}
  - Response (201):
    {"message":"User created successfully","user":{"username":"alice","email":"alice@example.com"}}

- Login (username or email in the same field)
  - Request (POST /auth/login):
    {"username":"alice","password":"secret123"}
    or {"username":"alice@example.com","password":"secret123"}
  - Success Response (200):
    {"message":"Login successful","user":{"id":1,"username":"alice","email":"alice@example.com"},"token":"..."}
  - Error Responses:
    - 404: {"message":"User Not Found"}
    - 401: {"message":"Password Incorrect"}

### Mental Health
- Predict
  - Request (POST /mental/predict):
    {
      "userId": 1,
      "language": "en",  // or "id"
      "appetite": 3,
      "interest": 4,
      "fatigue": 2,
      "worthlessness": 4,
      "concentration": 3,
      "agitation": 2,
      "suicidalIdeation": 6,
      "sleepDisturbance": 3,
      "aggression": 2,
      "panicAttacks": 5,
      "hopelessness": 3,
      "restlessness": 4
    }
  - Response (201):
    {
      "message": "Depression state predicted and recorded successfully.",
      "depressionState": 0,
      "suggestion": "...",
      "data": { "id": 1, "userId": 1, "appetite": 3, ..., "language": "en", "healthTestDate": "..." }
    }
  - Notes:
    - Requires psyche_model.keras in project root
    - Suggestion provider:
      - If USE_GEMINI_SUGGESTION=true and GEMINI_API_KEY is set, uses Gemini with your provided prompt template (including specificScoreDetails from high scores)
      - Otherwise falls back to a local mapping

- History
  - GET /mental/history/{user_id} → {"message":"...","data":[ ... ]}
  - GET /mental/history/{user_id}/latest → {"message":"...","data":{...}} or data: null

## Notes
- Emails are normalized to lowercase for uniqueness and login matching.
- Tables are created at startup (lifespan) if they do not exist; consider Alembic for production migrations.
- PostgreSQL URL starting with postgres:// is normalized for SQLAlchemy/psycopg2.

## Troubleshooting
- Gemini not used / fallback message in logs:
  - Ensure google-generativeai is installed, USE_GEMINI_SUGGESTION=true, GEMINI_API_KEY is set, and server is restarted
- Missing model file:
  - Place psyche_model.keras in the repo root
- Postgres connection errors:
  - Verify DATABASE_URL, SSL requirements (Supabase needs sslmode=require), and network access

## Dev helpers
- HTTP samples: test_main.http
- Quick smoke test:
```
python smoke_test.py
```
This uses an isolated SQLite DB, registers a user, tests login (username + email), and calls /mental/predict.
