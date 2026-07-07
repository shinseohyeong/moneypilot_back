from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    DECIMAL,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from app.core.database import Base


class Stock(Base):
    __tablename__ = "stocks"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stock_code = Column(String(20), nullable=False, unique=True)
    stock_name = Column(String(100), nullable=False)
    market = Column(String(20), nullable=False)
    representative_sector = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class StockPrice(Base):
    __tablename__ = "stock_prices"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stock_id = Column(BigInteger, ForeignKey("stocks.id"), nullable=False)

    price_date = Column(Date, nullable=False)
    close_price = Column(DECIMAL(15, 2), nullable=False)
    previous_close = Column(DECIMAL(15, 2), server_default=text("0"))
    price_change = Column(DECIMAL(15, 2), server_default=text("0"))
    change_rate = Column(DECIMAL(6, 2), server_default=text("0"))

    open_price = Column(DECIMAL(15, 2), server_default=text("0"))
    high_price = Column(DECIMAL(15, 2), server_default=text("0"))
    low_price = Column(DECIMAL(15, 2), server_default=text("0"))

    volume = Column(BigInteger, server_default=text("0"))
    trade_value = Column(DECIMAL(20, 2), server_default=text("0"))

    # 공공데이터 상장주식
    listed_shares = Column(BigInteger, server_default=text("0"))

    # 공공데이터 시가총액
    market_cap = Column(DECIMAL(25, 2), server_default=text("0"))

    source = Column(String(50), nullable=False, default="PUBLIC_DATA")
    fetched_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint(
            "stock_id",
            "price_date",
            "source",
            name="uk_stock_price_date_source",
        ),
    )


class StockWatchlist(Base):
    __tablename__ = "stock_watchlists"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)
    category_id = Column(BigInteger, ForeignKey("stock_watchlist_categories.id"), nullable=False)
    stock_id = Column(BigInteger, ForeignKey("stocks.id"), nullable=False)

    memo = Column(String(255), nullable=True)
    alert_enabled = Column(Boolean, nullable=False, default=False)
    alert_price = Column(DECIMAL(15, 2), nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "category_id",
            "stock_id",
            name="uk_watchlist_user_category_stock",
        ),
    )

class StockWatchlistCategory(Base):
    __tablename__ = "stock_watchlist_categories"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=False)

    category_name = Column(String(100), nullable=False)
    display_order = Column(BigInteger, nullable=False, server_default=text("0"))
    is_default = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "category_name",
            name="uk_watchlist_category_user_name",
        ),
    )


class StockSector(Base):
    __tablename__ = "stock_sectors"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sector_name = Column(String(100), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    risk_level = Column(String(20), nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class SectorKeyword(Base):
    __tablename__ = "sector_keywords"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sector_id = Column(BigInteger, ForeignKey("stock_sectors.id"), nullable=False)
    keyword = Column(String(100), nullable=False)
    weight = Column(DECIMAL(5, 2), nullable=False, default=1.0)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint("sector_id", "keyword", name="uk_sector_keyword"),
    )


class StockSectorMapping(Base):
    __tablename__ = "stock_sector_mappings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    stock_id = Column(BigInteger, ForeignKey("stocks.id"), nullable=False)
    sector_id = Column(BigInteger, ForeignKey("stock_sectors.id"), nullable=False)

    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("stock_id", "sector_id", name="uk_stock_sector_mapping"),
    )