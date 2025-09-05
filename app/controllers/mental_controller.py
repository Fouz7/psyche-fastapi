from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.mental import PredictRequest, PredictResponse, HistoryResponse, LatestHistoryResponse
from app.services.mental_service import predict_and_save, history_by_user, latest_history_by_user

router = APIRouter(prefix="/mental", tags=["mental-health"])


@router.post("/predict", response_model=PredictResponse, status_code=status.HTTP_201_CREATED)
def predict(payload: PredictRequest, db: Session = Depends(get_db)):
    try:
        result = predict_and_save(db, payload)
        return PredictResponse(**result)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except RuntimeError as re:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(re))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/history/{user_id}", response_model=HistoryResponse)
def history(user_id: int, db: Session = Depends(get_db)):
    try:
        data = history_by_user(db, user_id)
        return HistoryResponse(message="Test history retrieved successfully.", data=data)
    except LookupError as le:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(le))


@router.get("/history/{user_id}/latest", response_model=LatestHistoryResponse)
def latest(user_id: int, db: Session = Depends(get_db)):
    try:
        data = latest_history_by_user(db, user_id)
        if data is None:
            return LatestHistoryResponse(message="No test history found for this user.", data=None)
        return LatestHistoryResponse(message="Latest test history retrieved successfully.", data=data)
    except LookupError as le:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(le))

