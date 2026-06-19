from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    DECIMAL,
    ForeignKey,
    String,
    func,
)

from app.core.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )

    statement_id = Column(
        BigInteger,
        ForeignKey("card_statements.id"),
        nullable=True,
    )

    transaction_date = Column(Date, nullable=False)

    # 예: 2026-06
    month = Column(String(7), nullable=False)

    merchant_name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)

    amount = Column(DECIMAL(15, 2), nullable=False)

    category = Column(String(50), nullable=True)

    is_recurring = Column(Boolean, nullable=False, default=False)

    # FIXED | VARIABLE
    expense_type = Column(
        String(20),
        nullable=False,
        default="VARIABLE",
    )

    created_at = Column(DateTime, server_default=func.now())

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )