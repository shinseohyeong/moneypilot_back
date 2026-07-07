from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    DECIMAL,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)

from app.core.database import Base


class MonthlySpendingSummary(Base):
    __tablename__ = "monthly_spending_summaries"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )

    # 예: 2026-06
    month = Column(String(7), nullable=False)

    total_income = Column(
        DECIMAL(15, 2),
        nullable=False,
        server_default=text("0"),
    )

    monthly_salary = Column(
        DECIMAL(15, 2),
        nullable=False,
        server_default=text("0"),
    )

    total_spending = Column(
        DECIMAL(15, 2),
        nullable=False,
        server_default=text("0"),
    )

    fixed_expense = Column(
        DECIMAL(15, 2),
        nullable=False,
        server_default=text("0"),
    )

    variable_expense = Column(
        DECIMAL(15, 2),
        nullable=False,
        server_default=text("0"),
    )

    remaining_money = Column(
        DECIMAL(15, 2),
        nullable=False,
        server_default=text("0"),
    )

    spending_diff = Column(
        DECIMAL(15, 2),
        nullable=True,
        server_default=text("0"),
    )

    spending_change_rate = Column(
        DECIMAL(6, 2),
        nullable=True,
        server_default=text("0"),
    )

    created_at = Column(DateTime, server_default=func.now())

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("user_id", "month", name="uk_monthly_summary_user_month"),
    )


class CategorySpending(Base):
    __tablename__ = "category_spendings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    summary_id = Column(
        BigInteger,
        ForeignKey("monthly_spending_summaries.id"),
        nullable=False,
    )

    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )

    # 예: 2026-06
    month = Column(String(7), nullable=False)

    category = Column(String(50), nullable=False)

    category_amount = Column(
        DECIMAL(15, 2),
        nullable=False,
        server_default=text("0"),
    )

    category_ratio = Column(
        DECIMAL(6, 2),
        nullable=False,
        server_default=text("0"),
    )

    transaction_count = Column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    previous_category_amount = Column(
        DECIMAL(15, 2),
        nullable=True,
        server_default=text("0"),
    )

    spending_diff = Column(
        DECIMAL(15, 2),
        nullable=True,
        server_default=text("0"),
    )

    spending_change_rate = Column(
        DECIMAL(6, 2),
        nullable=True,
        server_default=text("0"),
    )

    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("summary_id", "category", name="uk_category_spending_summary_category"),
    )


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    summary_id = Column(
        BigInteger,
        ForeignKey("monthly_spending_summaries.id"),
        nullable=False,
        unique=True,
    )

    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )

    # 예: 2026-06
    month = Column(String(7), nullable=False)

    report_title = Column(String(100), nullable=False)

    summary_text = Column(Text, nullable=False)

    category_text = Column(Text, nullable=True)

    overspending_text = Column(Text, nullable=True)

    card_text = Column(Text, nullable=True)

    compare_text = Column(Text, nullable=True)

    recommendation_text = Column(Text, nullable=True)

    agent_response = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now())


class CardSpending(Base):
    __tablename__ = "card_spendings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    summary_id = Column(
        BigInteger,
        ForeignKey("monthly_spending_summaries.id"),
        nullable=False,
    )

    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )

    # 예: 2026-06
    month = Column(String(7), nullable=False)

    card_name = Column(String(50), nullable=False)

    card_amount = Column(
        DECIMAL(15, 2),
        nullable=False,
        server_default=text("0"),
    )

    card_ratio = Column(
        DECIMAL(6, 2),
        nullable=False,
        server_default=text("0"),
    )

    transaction_count = Column(
        Integer,
        nullable=False,
        server_default=text("0"),
    )

    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("summary_id", "card_name", name="uk_card_spending_summary_card"),
    )