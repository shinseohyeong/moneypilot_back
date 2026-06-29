from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)

from app.core.database import Base


class StockAlert(Base):
    __tablename__ = "stock_alerts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )

    stock_id = Column(
        BigInteger,
        ForeignKey("stocks.id"),
        nullable=True,
    )

    news_id = Column(
        BigInteger,
        ForeignKey("news_articles.id"),
        nullable=True,
    )

    sector_id = Column(
        BigInteger,
        ForeignKey("stock_sectors.id"),
        nullable=True,
    )

    # PRICE | NEWS | SECTOR | RISK
    alert_type = Column(String(30), nullable=False)

    title = Column(String(200), nullable=False)

    message = Column(Text, nullable=False)

    is_read = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, server_default=func.now())

    updated_at = Column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
    )

    read_at = Column(DateTime, nullable=True)