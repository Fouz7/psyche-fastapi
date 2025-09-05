import os
from dotenv import load_dotenv

# Load environment variables from .env for local dev
load_dotenv()

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL") or "sqlite:///./app.db"

# Normalize postgres URL for SQLAlchemy/psycopg2
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)

# Auth / JWT
SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

# Gemini (optional)
USE_GEMINI_SUGGESTION = os.getenv("USE_GEMINI_SUGGESTION", "false").lower() == "true"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
