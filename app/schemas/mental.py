from typing import Literal, Optional
from pydantic import BaseModel, Field

MENTAL_HEALTH_FIELDS = [
    'appetite', 'interest', 'fatigue', 'worthlessness', 'concentration',
    'agitation', 'suicidalIdeation', 'sleepDisturbance', 'aggression',
    'panicAttacks', 'hopelessness', 'restlessness'
]


class PredictRequest(BaseModel):
    userId: int
    language: Literal['en', 'id'] = 'en'
    # Scores 1..6 for each field
    appetite: int = Field(..., ge=1, le=6)
    interest: int = Field(..., ge=1, le=6)
    fatigue: int = Field(..., ge=1, le=6)
    worthlessness: int = Field(..., ge=1, le=6)
    concentration: int = Field(..., ge=1, le=6)
    agitation: int = Field(..., ge=1, le=6)
    suicidalIdeation: int = Field(..., ge=1, le=6)
    sleepDisturbance: int = Field(..., ge=1, le=6)
    aggression: int = Field(..., ge=1, le=6)
    panicAttacks: int = Field(..., ge=1, le=6)
    hopelessness: int = Field(..., ge=1, le=6)
    restlessness: int = Field(..., ge=1, le=6)


class PredictResponse(BaseModel):
    message: str
    depressionState: int
    suggestion: str
    data: dict


class HistoryResponse(BaseModel):
    message: str
    data: list


class LatestHistoryResponse(BaseModel):
    message: str
    data: Optional[dict]
