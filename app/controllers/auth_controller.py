from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    RegisterResponse,
    RegisterUserBrief,
    LoginResponse,
    LoginUserBrief,
)
from app.services.auth_service import register_user, login_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    try:
        user = register_user(db, payload)
        return RegisterResponse(
            message="User created successfully",
            user=RegisterUserBrief(username=user.username, email=user.email),
        )
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    try:
        token, user = login_user(db, payload)
        return LoginResponse(
            message="Login successful",
            user=LoginUserBrief(id=user.id, username=user.username, email=user.email),
            token=token,
        )
    except LookupError as le:
        # Username/email not found
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"message": str(le)})
    except PermissionError as pe:
        # Wrong password
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"message": str(pe)})
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(ve))
