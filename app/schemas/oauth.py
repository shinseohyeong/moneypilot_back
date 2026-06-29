"""
schemas/oauth.py — OAuth(소셜 로그인) 관련 스키마
"""

from pydantic import BaseModel


class OAuthLoginURLResponse(BaseModel):
    """소셜 로그인 페이지로 보낼 URL 응답."""
    login_url: str


class OAuthTokenResponse(BaseModel):
    """소셜 로그인 성공 후 우리 서비스가 발급하는 토큰."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    is_new_user: bool  # 이번에 새로 가입했는지 여부