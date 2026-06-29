from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import auth_service
from app.schemas.auth import (
    SignupRequest, SignupResponse,
    LoginRequest, TokenResponse,
    RefreshRequest, AccessTokenResponse,
)

router = APIRouter()


@router.post("/signup", response_model=SignupResponse,
             status_code=status.HTTP_201_CREATED, summary="회원가입")
def signup(body: SignupRequest, db: Session = Depends(get_db)) -> SignupResponse:
    return auth_service.signup(db, body)


@router.post("/login", response_model=TokenResponse, summary="로그인")
def login(body: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    return TokenResponse(**auth_service.login(db, body))


@router.post("/token/refresh", response_model=AccessTokenResponse, summary="토큰 갱신")
def refresh_token(body: RefreshRequest, db: Session = Depends(get_db)) -> AccessTokenResponse:
    return AccessTokenResponse(access_token=auth_service.refresh_access_token(db, body.refresh_token))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="로그아웃")
def logout(body: RefreshRequest, db: Session = Depends(get_db)) -> None:
    auth_service.logout(db, body.refresh_token)
    return None