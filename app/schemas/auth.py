import re
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import date


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    username: str = Field(..., min_length=2, max_length=100)
    birth_date: Optional[date] = None
    gender: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_must_contain_letter_and_number(cls, v: str) -> str:
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("비밀번호는 영문자를 1자 이상 포함해야 합니다.")
        if not re.search(r"\d", v):
            raise ValueError("비밀번호는 숫자를 1자 이상 포함해야 합니다.")
        return v


class SignupResponse(BaseModel):
    id: int
    email: str
    username: str
    model_config = {"from_attributes": True}


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"