import os
from fastapi import APIRouter, Depends, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services import auth_service, oauth_service
from app.schemas.auth import (
    SignupRequest, SignupResponse,
    LoginRequest, TokenResponse,
    RefreshRequest, AccessTokenResponse,
)
from app.schemas.oauth import OAuthLoginURLResponse, OAuthTokenResponse

router = APIRouter()


# ════════════════════════════════════════════
# 일반 회원가입 / 로그인
# ════════════════════════════════════════════
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


# ════════════════════════════════════════════
# OAuth (소셜 로그인) — google / kakao
# ════════════════════════════════════════════
@router.get("/{provider}/login", response_model=OAuthLoginURLResponse,
            summary="소셜 로그인 URL 발급")
def oauth_login(provider: str) -> OAuthLoginURLResponse:
    """
    google 또는 kakao 로그인 페이지 URL을 반환한다.
    프론트는 이 URL로 사용자를 보내면 된다.
    """
    login_url = oauth_service.build_login_url(provider)
    return OAuthLoginURLResponse(login_url=login_url)


@router.get("/{provider}/callback", summary="소셜 로그인 콜백")
def oauth_callback(provider: str, code: str, db: Session = Depends(get_db)):
    """
    소셜 인증 후 code를 받아 처리하고, 토큰과 함께 프론트로 리다이렉트한다.
    """
    result = oauth_service.process_callback(db, provider, code)

    # 프론트 콜백 페이지로 리다이렉트 (토큰 포함)
    front_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    redirect_url = (
        f"{front_url}/auth/callback"
        f"?access_token={result['access_token']}"
        f"&refresh_token={result['refresh_token']}"
        f"&is_new_user={str(result['is_new_user']).lower()}"
    )
    return RedirectResponse(url=redirect_url)