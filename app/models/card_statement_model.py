from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)

from app.core.database import Base


class CardStatement(Base):
    __tablename__ = "card_statements"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )

    file_name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_type = Column(String(20), nullable=False)

    # PROCESSING | COMPLETED | FAILED
    status = Column(
        String(20),
        nullable=False,
        default="PROCESSING",
    )

    error_message = Column(Text, nullable=True)

    uploaded_at = Column(DateTime, server_default=func.now())
    processed_at = Column(DateTime, nullable=True)

    card_name = Column(String(20), nullable=False)

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )