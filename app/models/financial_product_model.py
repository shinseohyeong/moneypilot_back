from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    DECIMAL,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)

from app.core.database import Base


class DepositProduct(Base):
    __tablename__ = "deposit_products"

    # 상품 ID
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # 금융감독원 코드
    product_code = Column(String(100), nullable=False, unique=True)
    # 금융기관명
    bank_name = Column(String(100), nullable=False)
    # 상품명
    product_name = Column(String(200), nullable=False)

    # 생성일
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    # 금융감독원/외부 API 데이터 갱신 시각
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SavingProduct(Base):
    __tablename__ = "saving_products"

    # 상품 ID
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # 금융감독원 코드
    product_code = Column(String(100), nullable=False, unique=True)
    # 금융기관명
    bank_name = Column(String(100), nullable=False)
    # 상품명
    product_name = Column(String(200), nullable=False)

    # 생성일
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    # 금융감독원/외부 API 데이터 갱신 시각
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class FinancialProductRecommendation(Base):
    __tablename__ = "financial_product_recommendations"

    # 추천 이력 ID
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # 사용자
    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )

    # DEPOSIT | SAVING | INSURANCE
    product_type = Column(String(30), nullable=False)

    # 추천 상품 ID
    # product_type에 따라 deposit_products.id,
    # saving_products.id,
    # insurance_products.id 중 하나를 의미함
    product_id = Column(BigInteger, nullable=False)

    # 추천 사유
    recommendation_reason = Column(Text, nullable=True)

    # 추천 시각
    created_at = Column(DateTime, server_default=func.now(), nullable=False,)

    # 수정 시각
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class InsuranceProduct(Base):
    __tablename__ = "insurance_products"

    # 보험 상품 ID
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # 보험사
    company_name = Column(String(100), nullable=False)
    # 보험 상품명
    insurance_name = Column(String(200), nullable=False)

    # 보험 종류(실손보험, 암보험, 종신보험 등)
    insurance_type = Column(String(50), nullable=False)

    # 설명
    description = Column(Text, nullable=True)

    # 생성일
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    # 외부 API 또는 관리자 데이터 갱신 시각
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )


class InterestCalculationHistory(Base):
    __tablename__ = "interest_calculation_histories"

    # 계산 ID
    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # 사용자
    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )

    # DEPOSIT | SAVING
    product_type = Column(String(20), nullable=False)

    # 원금
    principal = Column(BigInteger, nullable=False)

    # 가입 기간 개월 수
    period_month = Column(Integer, nullable=False)

    # 적용 금리
    interest_rate = Column(DECIMAL(5, 2), nullable=False)

    # 세전 이자
    before_tax_amount = Column(BigInteger, nullable=False)
    # 세후 이자
    after_tax_amount = Column(BigInteger, nullable=False)
    # 만기 수령액
    maturity_amount = Column(BigInteger, nullable=False)

    # 생성일
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    # 수정일
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )


class DepositProductRate(Base):
    __tablename__ = "deposit_product_rates"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    product_id = Column(
        BigInteger,
        ForeignKey("deposit_products.id"),
        nullable=False,
    )

    term_months = Column(Integer, nullable=False)

    base_rate = Column(DECIMAL(5, 2), nullable=False)

    max_rate = Column(DECIMAL(5, 2), nullable=True)

    rate_type = Column(String(20), nullable=True)

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class SavingProductRate(Base):
    __tablename__ = "saving_product_rates"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    product_id = Column(
        BigInteger,
        ForeignKey("saving_products.id"),
        nullable=False,
    )

    term_months = Column(Integer, nullable=False)

    base_rate = Column(DECIMAL(5, 2), nullable=False)

    max_rate = Column(DECIMAL(5, 2), nullable=True)

    rate_type = Column(String(20), nullable=True)

    created_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )