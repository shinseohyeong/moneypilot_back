from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
    DECIMAL,
    text,
)
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    email = Column(String(100), nullable=False, unique=True)

    password = Column(String(255), nullable=False)

    username = Column(String(50), nullable=False)

    profile_image_url = Column(String(500), nullable=True)

    # LOCAL | OAUTH | BOTH
    # DB 기본값까지 반영하기 위해 server_default 사용
    login_type = Column(
        String(20),
        nullable=False,
        server_default=text("'LOCAL'"),
    )

    # 생년월일
    birth_date = Column(Date, nullable=True)

    # 성별
    gender = Column(String(10), nullable=True)

    # 계정 활성화 여부
    is_active = Column(
        Boolean,
        nullable=False,
        server_default=text("1"),
    )

    # USER: 일반사용자 / ADMIN: 관리자
    role = Column(
        String(20),
        nullable=False,
        server_default=text("'USER'"),
    )

    created_at = Column(DateTime, server_default=func.now())

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )

class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"

    __table_args__ = (
        UniqueConstraint(
            "provider",
            "provider_user_id",
            name="uq_oauth_accounts_provider_user_id",
        ),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )

    provider = Column(String(30), nullable=False)

    provider_user_id = Column(String(255), nullable=False)

    provider_email = Column(String(255), nullable=False)

    access_token = Column(Text, nullable=True)

    refresh_token = Column(Text, nullable=True)

    token_expires_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)

    token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=False)

    is_revoked = Column(Boolean, nullable=False, default=False)

    expires_at = Column(DateTime, server_default=func.now())
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class FinanceProfile(Base):
    __tablename__ = "finance_profiles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # users.id를 참조하는 FK
    # 사용자 1명당 금융 프로필 1개만 가지도록 unique=True
    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
        unique=True,
    )

    # 월급: DECIMAL(15, 2), NOT NULL
    monthly_salary = Column(
        DECIMAL(15, 2),
        nullable=False,
    )

    # 연봉: DECIMAL(15, 2), NOT NULL
    annual_salary = Column(
        DECIMAL(15, 2),
        nullable=True,
    )

    # 사용자가 입력한 월 고정비
    # 엑셀에 DEFAULT 0으로 되어 있으므로 server_default 사용
    fixed_expense = Column(
        DECIMAL(15, 2),
        nullable=True,
        server_default=text("0"),
    )

    # 투자 성향
    risk_type = Column(
        String(30),
        nullable=False,
    )

    # 투자 목표
    investment_goal = Column(
        String(100),
        nullable=True,
    )

    # 목표 저축액
    target_saving_amount = Column(
        DECIMAL(15, 2),
        nullable=True,
        server_default=text("0"),
    )

    created_at = Column(
        DateTime,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )