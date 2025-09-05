from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    # 'username' can be either a real username or an email string
    username: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)


class RegisterUserBrief(BaseModel):
    username: str
    email: EmailStr


class RegisterResponse(BaseModel):
    message: str
    user: RegisterUserBrief


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginUserBrief(BaseModel):
    id: int
    username: str
    email: EmailStr


class LoginResponse(BaseModel):
    message: str
    user: LoginUserBrief
    token: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
