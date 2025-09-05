from sqlalchemy import Column, Integer, String, DateTime, func, Text
from app.db.session import Base
from app.core.config import DATABASE_URL


class HealthTest(Base):
    __tablename__ = "health_test"
    __table_args__ = ({"schema": "public"} if not DATABASE_URL.startswith("sqlite") else {})

    id = Column(Integer, primary_key=True, index=True)
    userId = Column(Integer, nullable=False, index=True)

    appetite = Column(Integer, nullable=False)
    interest = Column(Integer, nullable=False)
    fatigue = Column(Integer, nullable=False)
    worthlessness = Column(Integer, nullable=False)
    concentration = Column(Integer, nullable=False)
    agitation = Column(Integer, nullable=False)
    suicidalIdeation = Column(Integer, nullable=False)
    sleepDisturbance = Column(Integer, nullable=False)
    aggression = Column(Integer, nullable=False)
    panicAttacks = Column(Integer, nullable=False)
    hopelessness = Column(Integer, nullable=False)
    restlessness = Column(Integer, nullable=False)

    depressionState = Column(Integer, nullable=False)
    generatedSuggestion = Column(Text, nullable=False)
    language = Column(String(8), nullable=False)

    healthTestDate = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

