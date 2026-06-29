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


@router.get("/{provider}/callback", response_model=OAuthTokenResponse,
            summary="소셜 로그인 콜백")
def oauth_callback(provider: str, code: str, db: Session = Depends(get_db)) -> OAuthTokenResponse:
    """
    소셜 인증 후 code를 받아 처리한다.
    code → 소셜 토큰 → 유저 정보 → 우리 유저 생성/조회 → 우리 JWT 발급.
    """
    result = oauth_service.process_callback(db, provider, code)
    return OAuthTokenResponse(**result)