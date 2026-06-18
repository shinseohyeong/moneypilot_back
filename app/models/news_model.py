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
)
from app.core.database import Base


class NewsArticle(Base):
    __tablename__ = "news_articles"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=True)
    description = Column(Text, nullable=True)

    original_link = Column(String(1000), nullable=True)
    api_link = Column(String(1000), nullable=True)
    url_hash = Column(String(64), nullable=True, unique=True)

    source_name = Column(String(100), nullable=True)
    provider = Column(String(50), nullable=False)
    search_keyword = Column(String(100), nullable=True)

    published_at = Column(DateTime, nullable=True)
    collected_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    is_active = Column(Boolean, nullable=False, default=True)


class StockNewsMapping(Base):
    __tablename__ = "stock_news_mappings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    news_id = Column(BigInteger, ForeignKey("news_articles.id"), nullable=False)
    stock_id = Column(BigInteger, ForeignKey("stocks.id"), nullable=False)

    relevance_score = Column(DECIMAL(5, 2), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("news_id", "stock_id", name="uk_news_stock_mapping"),
    )


class NewsSectorMapping(Base):
    __tablename__ = "news_sector_mappings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    news_id = Column(BigInteger, ForeignKey("news_articles.id"), nullable=False)
    sector_id = Column(BigInteger, ForeignKey("stock_sectors.id"), nullable=False)

    relevance_score = Column(DECIMAL(5, 2), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("news_id", "sector_id", name="uk_news_sector_mapping"),
    )


class NewsSummary(Base):
    __tablename__ = "news_summaries"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    news_id = Column(BigInteger, ForeignKey("news_articles.id"), nullable=False)

    summary = Column(Text, nullable=False)
    sentiment = Column(String(20), nullable=True)
    keywords = Column(Text, nullable=True)
    investment_view = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class SectorInsight(Base):
    __tablename__ = "sector_insights"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sector_id = Column(BigInteger, ForeignKey("stock_sectors.id"), nullable=False)

    insight_date = Column(Date, nullable=False)
    period_days = Column(BigInteger, nullable=False, default=7)

    issue_score = Column(DECIMAL(6, 2), nullable=True)
    risk_summary = Column(Text, nullable=True)
    trend_summary = Column(Text, nullable=True)
    keywords = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        UniqueConstraint(
            "sector_id",
            "insight_date",
            "period_days",
            name="uk_sector_insight_period",
        ),
    )