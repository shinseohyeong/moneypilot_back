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

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    product_code = Column(String(100), nullable=False, unique=True)
    bank_name = Column(String(100), nullable=False)
    product_name = Column(String(200), nullable=False)

    interest_rate = Column(DECIMAL(5, 2), nullable=False)
    max_rate = Column(DECIMAL(5, 2), nullable=True)

    # 가입 기간 개월 수
    join_period = Column(Integer, nullable=False)

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

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    product_code = Column(String(100), nullable=False, unique=True)
    bank_name = Column(String(100), nullable=False)
    product_name = Column(String(200), nullable=False)

    interest_rate = Column(DECIMAL(5, 2), nullable=False)
    max_rate = Column(DECIMAL(5, 2), nullable=True)

    # 가입 기간 개월 수
    join_period = Column(Integer, nullable=False)

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

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )

    # DEPOSIT | SAVING | INSURANCE
    product_type = Column(String(30), nullable=False)

    # 상품 ID
    # product_type에 따라 deposit_products.id,
    # saving_products.id,
    # insurance_products.id 중 하나를 의미함
    product_id = Column(BigInteger, nullable=False)

    recommendation_reason = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now(), nullable=False,)

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class InsuranceProduct(Base):
    __tablename__ = "insurance_products"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    company_name = Column(String(100), nullable=False)
    insurance_name = Column(String(200), nullable=False)

    # 실손보험, 암보험, 종신보험 등
    insurance_type = Column(String(50), nullable=False)

    description = Column(Text, nullable=True)

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

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )

    # DEPOSIT | SAVING
    product_type = Column(String(20), nullable=False)

    principal = Column(BigInteger, nullable=False)

    # 가입 기간 개월 수
    period_month = Column(Integer, nullable=False)

    interest_rate = Column(DECIMAL(5, 2), nullable=False)

    before_tax_amount = Column(BigInteger, nullable=False)
    after_tax_amount = Column(BigInteger, nullable=False)
    maturity_amount = Column(BigInteger, nullable=False)

    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )