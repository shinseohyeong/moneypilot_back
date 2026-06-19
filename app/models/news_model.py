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
    JSON,
    text,
    Integer,
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

    matched_keyword = Column(String(100), nullable=True)

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

    matched_keywords = Column(JSON, nullable=True)
    relevance_score = Column(DECIMAL(5, 2), nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("news_id", "sector_id", name="uk_news_sector_mapping"),
    )


class NewsSummary(Base):
    __tablename__ = "news_summaries"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    news_id = Column(BigInteger, ForeignKey("news_articles.id"), nullable=False)

    one_line_summary = Column(String(500), nullable=True)
    summary_text = Column(Text, nullable=False)
    positive_factors = Column(JSON, nullable=True)
    risk_factors = Column(JSON, nullable=True)
    investment_note = Column(Text, nullable=True)
    sentiment = Column(String(20), nullable=True)
    model_name = Column(String(100), nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class SectorInsight(Base):
    __tablename__ = "sector_insights"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    sector_id = Column(BigInteger, ForeignKey("stock_sectors.id"), nullable=False)

    insight_date = Column(Date, nullable=False)
    period_days = Column(BigInteger, nullable=False, default=7)

    news_count = Column(Integer, server_default=text("0"))
    positive_count = Column(Integer, server_default=text("0"))
    neutral_count = Column(Integer, server_default=text("0"))
    negative_count = Column(Integer, server_default=text("0"))
    main_keywords = Column(JSON, nullable=True)

    issue_score = Column(DECIMAL(6, 2), nullable=True)
    insight_summary = Column(Text, nullable=True)
    risk_summary = Column(Text, nullable=True)

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

class StockReport(Base):
    __tablename__ = "stock_reports"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    # 사용자 ID
    user_id = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=False,
    )

    # 리포트 기준일
    report_date = Column(
        Date,
        nullable=False,
    )

    # 리포트 제목
    report_title = Column(
        String(100),
        nullable=False,
    )

    # 시장 요약
    market_summary = Column(
        Text,
        nullable=True,
    )

    # 섹터 요약
    sector_summary = Column(
        Text,
        nullable=True,
    )

    # 관심종목 요약
    watchlist_summary = Column(
        Text,
        nullable=True,
    )

    # 위험 요인
    risk_summary = Column(
        Text,
        nullable=True,
    )

    # 투자 유의 문구
    disclaimer = Column(
        Text,
        nullable=False,
    )

    # 생성일
    created_at = Column(
        DateTime,
        server_default=func.now(),
    )

class StockReportItem(Base):
    __tablename__ = "stock_report_items"

    id = Column(BigInteger, primary_key=True, autoincrement=True)

    report_id = Column(
        BigInteger,
        ForeignKey("stock_reports.id"),
        nullable=False,
    )

    stock_id = Column(
        BigInteger,
        ForeignKey("stocks.id"),
        nullable=False,
    )

    # 현재가
    current_price = Column(
        DECIMAL(15, 2),
        nullable=True,
        server_default=text("0"),
    )

    # 등락률
    change_rate = Column(
        DECIMAL(6, 2),
        nullable=True,
        server_default=text("0"),
    )

    # 관련 뉴스 요약
    news_summary = Column(Text, nullable=True)

    # 섹터 흐름 요약
    sector_summary = Column(Text, nullable=True)

    # 위험 요인
    risk_factors = Column(Text, nullable=True)

    created_at = Column(
        DateTime,
        server_default=func.now(),
    )