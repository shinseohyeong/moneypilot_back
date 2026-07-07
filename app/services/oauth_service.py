"""
services/oauth_service.py — OAuth(소셜 로그인) 비즈니스 로직

code 방식:
  1. build_login_url(provider)         소셜 로그인 URL 생성
  2. process_callback(provider, code)  code로 토큰 교환 → 유저 정보 → 우리 유저 생성/조회 → JWT 발급

지원 provider: google, kakao
실제 OAuthAccount 모델 컬럼 기준:
  provider, provider_user_id, provider_email (NOT NULL)
  access_token, refresh_token, token_expires_at (nullable)
"""

import logging
from datetime import datetime, timedelta, timezone

import requests
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, create_refresh_token
from app.models.user_model import User, OAuthAccount, RefreshToken

logger = logging.getLogger(__name__)

# 외부 API 호출 타임아웃(초)
HTTP_TIMEOUT = 10

# ── provider별 엔드포인트 ──────────────────
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

KAKAO_AUTH_URL = "https://kauth.kakao.com/oauth/authorize"
KAKAO_TOKEN_URL = "https://kauth.kakao.com/oauth/token"
KAKAO_USERINFO_URL = "https://kapi.kakao.com/v2/user/me"


# ════════════════════════════════════════════
# 1. 로그인 URL 생성
# ════════════════════════════════════════════
def build_login_url(provider: str) -> str:
    if provider == "google":
        return (
            f"{GOOGLE_AUTH_URL}"
            f"?client_id={settings.GOOGLE_CLIENT_ID}"
            f"&redirect_uri={settings.GOOGLE_REDIRECT_URI}"
            f"&response_type=code"
            f"&scope=openid%20email%20profile"
            f"&access_type=offline"
        )
    elif provider == "kakao":
        return (
            f"{KAKAO_AUTH_URL}"
            f"?client_id={settings.KAKAO_CLIENT_ID}"
            f"&redirect_uri={settings.KAKAO_REDIRECT_URI}"
            f"&response_type=code"
        )
    else:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"지원하지 않는 provider입니다: {provider}")


# ════════════════════════════════════════════
# 2. code → 소셜 토큰 교환
# ════════════════════════════════════════════
def _exchange_code_for_token(provider: str, code: str) -> dict:
    if provider == "google":
        token_url = GOOGLE_TOKEN_URL
        data = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        }
    elif provider == "kakao":
        token_url = KAKAO_TOKEN_URL
        data = {
            "client_id": settings.KAKAO_CLIENT_ID,
            "client_secret": settings.KAKAO_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": settings.KAKAO_REDIRECT_URI,
        }
    else:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"지원하지 않는 provider입니다: {provider}")

    try:
        resp = requests.post(token_url, data=data, timeout=HTTP_TIMEOUT)
    except requests.RequestException as e:
        logger.error(f"{provider} 토큰 교환 요청 실패: {e}")
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "소셜 인증 서버 통신에 실패했습니다.")

    if resp.status_code != 200:
        logger.error(f"{provider} 토큰 교환 실패: {resp.status_code} {resp.text}")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "소셜 인증에 실패했습니다. (토큰 교환 실패)")

    return resp.json()


# ════════════════════════════════════════════
# 3. 소셜 토큰 → 유저 정보 조회
# ════════════════════════════════════════════
def _fetch_user_info(provider: str, social_access_token: str) -> dict:
    headers = {"Authorization": f"Bearer {social_access_token}"}

    if provider == "google":
        userinfo_url = GOOGLE_USERINFO_URL
    elif provider == "kakao":
        userinfo_url = KAKAO_USERINFO_URL
    else:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"지원하지 않는 provider입니다: {provider}")

    try:
        resp = requests.get(userinfo_url, headers=headers, timeout=HTTP_TIMEOUT)
    except requests.RequestException as e:
        logger.error(f"{provider} 유저 정보 조회 실패: {e}")
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, "소셜 인증 서버 통신에 실패했습니다.")

    if resp.status_code != 200:
        logger.error(f"{provider} 유저 정보 조회 실패: {resp.status_code} {resp.text}")
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "소셜 유저 정보 조회에 실패했습니다.")

    raw = resp.json()

    # provider별 응답 형식이 달라서 공통 형태로 정규화
    if provider == "google":
        return {
            "provider_user_id": str(raw.get("id")),
            "email": raw.get("email"),
            "username": raw.get("name") or (raw.get("email") or "").split("@")[0],
        }
    else:  # kakao
        kakao_account = raw.get("kakao_account", {})
        profile = kakao_account.get("profile", {})
        return {
            "provider_user_id": str(raw.get("id")),
            "email": kakao_account.get("email"),
            "username": profile.get("nickname") or f"kakao_{raw.get('id')}",
        }


# ════════════════════════════════════════════
# 4. 우리 유저 생성/조회 + OAuthAccount 저장
# ════════════════════════════════════════════
def _get_or_create_user(db: Session, provider: str, info: dict, social_tokens: dict) -> tuple[User, bool]:
    """
    Returns: (user, is_new_user)
    """
    provider_user_id = info["provider_user_id"]
    email = info["email"]

    if not email:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "소셜 계정에서 이메일을 가져오지 못했습니다.")

    # 1) 이미 연결된 OAuth 계정이 있나?
    oauth = db.query(OAuthAccount).filter(
        OAuthAccount.provider == provider,
        OAuthAccount.provider_user_id == provider_user_id,
    ).first()

    if oauth:
        user = db.query(User).filter(User.id == oauth.user_id).first()
        _update_oauth_tokens(oauth, social_tokens)
        db.commit()
        return user, False

    # 2) 같은 이메일의 유저가 이미 있나? (다른 방식으로 가입)
    user = db.query(User).filter(User.email == email).first()
    is_new_user = False

    if not user:
        # 3) 신규 유저 생성 (소셜 가입은 비밀번호가 없으므로 빈 문자열)
        user = User(
            email=email,
            password="",  # 소셜 로그인은 비밀번호 없음
            username=info["username"],
            login_type="OAUTH",
            role="USER",
            is_active=True,
        )
        db.add(user)
        db.flush()  # user.id 확보
        is_new_user = True

    # 4) OAuthAccount 연결 생성
    new_oauth = OAuthAccount(
        user_id=user.id,
        provider=provider,
        provider_user_id=provider_user_id,
        provider_email=email,
    )
    _update_oauth_tokens(new_oauth, social_tokens)
    db.add(new_oauth)
    db.commit()
    db.refresh(user)

    return user, is_new_user


def _update_oauth_tokens(oauth: OAuthAccount, social_tokens: dict) -> None:
    """소셜에서 받은 토큰을 OAuthAccount에 저장."""
    oauth.access_token = social_tokens.get("access_token")
    oauth.refresh_token = social_tokens.get("refresh_token")
    expires_in = social_tokens.get("expires_in")
    if expires_in:
        oauth.token_expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))


# ════════════════════════════════════════════
# 5. 콜백 전체 처리 (라우터가 호출)
# ════════════════════════════════════════════
def process_callback(db: Session, provider: str, code: str) -> dict:
    if provider not in ("google", "kakao"):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"지원하지 않는 provider입니다: {provider}")

    # 1) code → 소셜 토큰
    social_tokens = _exchange_code_for_token(provider, code)
    social_access_token = social_tokens.get("access_token")
    if not social_access_token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "소셜 access_token을 받지 못했습니다.")

    # 2) 소셜 토큰 → 유저 정보
    info = _fetch_user_info(provider, social_access_token)

    # 3) 우리 유저 생성/조회
    user, is_new_user = _get_or_create_user(db, provider, info, social_tokens)

    # 4) 우리 서비스 JWT 발급
    access_token = create_access_token(user.id)
    refresh_token_str = create_refresh_token(user.id)

    db.add(RefreshToken(
        user_id=user.id,
        refresh_token=refresh_token_str,
        is_revoked=False,
    ))
    db.commit()

    logger.info(f"{provider} 소셜 로그인 성공 — user_id={user.id}, is_new={is_new_user}")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token_str,
        "is_new_user": is_new_user,
    }