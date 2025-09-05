from sqlalchemy import Column, Integer, String, DateTime, func
from app.db.session import Base
from app.core.config import DATABASE_URL


class User(Base):
    __tablename__ = "users"
    __table_args__ = ({"schema": "public"} if not DATABASE_URL.startswith("sqlite") else {})

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    passwordHash = Column(String, nullable=False)
    createdAt = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

