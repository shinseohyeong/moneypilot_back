# ============================================================
# 파일 위치: app/services/news_service.py
# 역할:
#   - 뉴스 수집/조회 비즈니스 로직을 담당합니다.
#   - 네이버 API 응답을 NewsArticle 모델로 변환합니다.
#   - 중복 뉴스 저장을 방지합니다.
#   - 종목 뉴스는 StockNewsMapping으로 종목과 연결합니다.
#   - commit/rollback 트랜잭션 처리를 담당합니다.
# ============================================================

import hashlib
import re
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from email.utils import parsedate_to_datetime
from typing import Dict, Optional, Any, List
from urllib.parse import urlparse

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.clients.naver_news_client import NaverNewsClient
from app.models.news_model import NewsArticle, StockNewsMapping
from app.repositories.news_repository import NewsRepository
from app.schemas.news_schema import (
    NewsArticleResponse,
    StockNewsArticleResponse,
)


class NewsService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = NewsRepository(db)
        self.client = NaverNewsClient()

    def _collect_news_within_days(
        self,
        query: str,
        days: int,
        display: int = 100,
        sort: str = "date",
    ) -> List[Dict[str, Any]]:
        """
        최근 days일 이내의 네이버 뉴스를 페이지 단위로 수집합니다.
        """
        if days <= 0:
            raise HTTPException(
                status_code=400,
                detail="days는 1 이상이어야 합니다.",
            )

        cutoff_datetime = (
            datetime.now(timezone.utc) - timedelta(days=days)
        )

        collected_items: List[Dict[str, Any]] = []

        page_size = max(1, min(display, 100))
        start = 1
        max_pages = 5

        for _ in range(max_pages):
            response = self.client.search_news(
                query=query,
                display=page_size,
                start=start,
                sort=sort,
            )

            raw_items = response.get("items", [])

            if not raw_items:
                break

            reached_cutoff = False

            for item in raw_items:
                pub_date = item.get("pubDate")

                if not pub_date:
                    continue

                try:
                    published_at = parsedate_to_datetime(pub_date)

                    if published_at.tzinfo is None:
                        published_at = published_at.replace(
                            tzinfo=timezone.utc,
                        )
                except Exception:
                    continue

                if published_at < cutoff_datetime:
                    reached_cutoff = True
                    continue

                collected_items.append(item)

            if reached_cutoff or len(raw_items) < page_size:
                break

            start += page_size

        return collected_items

    # ------------------------------------------------------------
    # 경제 뉴스 수집
    # ------------------------------------------------------------
    def collect_economy_news(
        self,
        query: str = "경제",
        display: int = 10,
        sort: str = "date",
    ) -> Dict:
        """
        경제 뉴스 수집

        흐름:
        1. query 값 정리
        2. 네이버 뉴스 API 호출
        3. url_hash 기준으로 중복 확인
        4. 새 뉴스만 news_articles에 저장
        5. commit
        """

        normalized_query = self._normalize_query(query)
        search_query = normalized_query or "경제"

        try:
            naver_response = self.client.search_news(
                query=search_query,
                display=display,
                start=1,
                sort=sort,
            )

            raw_items = naver_response.get("items", [])

            saved_items = []
            response_items = []
            duplicated_count = 0

            for item in raw_items:
                article, is_created = self._get_or_create_article_from_naver_item(
                    item=item,
                    search_keyword=search_query,
                )

                if is_created:
                    saved_items.append(article)
                else:
                    duplicated_count += 1

                response_items.append(article)

            self.db.commit()

            return {
                "query": search_query,
                "requested_count": display,
                "fetched_count": len(raw_items),
                "saved_count": len(saved_items),
                "duplicated_count": duplicated_count,
                "mapped_count": 0,
                "items": [self._to_article_response(item) for item in response_items],
            }

        except HTTPException:
            self.db.rollback()
            raise
        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"경제 뉴스 수집 중 오류가 발생했습니다: {str(e)}",
            )

    # ------------------------------------------------------------
    # 종목 뉴스 수집
    # ------------------------------------------------------------
    def collect_stock_news(
        self,
        stock_id: int,
        query: Optional[str] = None,
        display: int = 100,
        sort: str = "date",
        days: int = 30,
    ) -> Dict:
        """
        특정 종목 뉴스 수집

        query가 없으면 '{stock_name} 주식'으로 자동 검색합니다.
        수집된 뉴스는 news_articles에 저장하고,
        stock_news_mappings로 종목과 연결합니다.
        """
        stock = self.repository.get_stock_by_id(stock_id)

        if not stock:
            raise HTTPException(
                status_code=404,
                detail="해당 종목을 찾을 수 없습니다.",
            )

        normalized_query = self._normalize_query(query)
        search_query = normalized_query or f"{stock.stock_name} 주식"

        try:
            raw_items = self._collect_news_within_days(
                query=search_query,
                days=days,
                display=display,
                sort=sort,
            )

            saved_items = []
            response_items = []
            duplicated_count = 0
            mapped_count = 0

            for item in raw_items:
                article, is_created = (
                    self._get_or_create_article_from_naver_item(
                        item=item,
                        search_keyword=search_query,
                    )
                )

                if is_created:
                    saved_items.append(article)
                else:
                    duplicated_count += 1

                existing_mapping = self.repository.get_stock_mapping(
                    news_id=article.id,
                    stock_id=stock_id,
                )

                if not existing_mapping:
                    mapping = StockNewsMapping(
                        news_id=article.id,
                        stock_id=stock_id,
                        matched_keyword=stock.stock_name,
                        relevance_score=Decimal("100.00"),
                    )

                    self.repository.create_stock_mapping(mapping)
                    mapped_count += 1

                response_items.append(article)

            self.db.commit()

            return {
                "query": search_query,
                "days": days,
                "requested_count": display,
                "fetched_count": len(raw_items),
                "saved_count": len(saved_items),
                "duplicated_count": duplicated_count,
                "mapped_count": mapped_count,
                "items": [
                    self._to_article_response(item)
                    for item in response_items
                ],
            }

        except HTTPException:
            self.db.rollback()
            raise

        except Exception as e:
            self.db.rollback()

            raise HTTPException(
                status_code=500,
                detail=f"종목 뉴스 수집 중 오류가 발생했습니다: {str(e)}",
            )

    # ------------------------------------------------------------
    # 뉴스 조회
    # ------------------------------------------------------------
    def get_economy_news(
        self,
        limit: int = 20,
        sort: str = "latest",
    ) -> Dict:
        """
        저장된 경제/일반 뉴스 조회

        sort:
        - latest: 최신순
        - oldest: 오래된순
        - relevance: 현재 경제 뉴스에서는 latest와 동일하게 처리
        - default: 기본순, 현재 latest와 동일하게 처리
        """
        normalized_sort = self._normalize_news_sort(sort)

        items = self.repository.list_economy_news(
            limit=limit,
            sort=normalized_sort,
        )

        return {
            "total_count": len(items),
            "items": [self._to_article_response(item) for item in items],
        }

    def get_stock_news(
        self,
        stock_id: int,
        limit: int = 20,
        sort: str = "latest",
    ) -> Dict:
        """
        저장된 특정 종목 뉴스 조회

        sort:
        - latest: 최신순
        - oldest: 오래된순
        - relevance: 종목명 포함 여부 기준 관련도순
        - default: 기본순, 현재 latest와 동일하게 처리
        """
        normalized_sort = self._normalize_news_sort(sort)

        stock = self.repository.get_stock_by_id(stock_id)

        if not stock:
            raise HTTPException(
                status_code=404,
                detail="해당 종목을 찾을 수 없습니다.",
            )

        rows = self.repository.list_stock_news(
            stock_id=stock_id,
            limit=limit,
            sort=normalized_sort,
            stock_name=stock.stock_name,
        )

        items = []

        for article, mapping in rows:
            items.append(
                self._to_stock_article_response(
                    article=article,
                    mapping=mapping,
                )
            )

        return {
            "stock_id": stock_id,
            "total_count": len(items),
            "items": items,
        }

    # ------------------------------------------------------------
    # 내부 변환 함수
    # ------------------------------------------------------------
    def _get_or_create_article_from_naver_item(
        self,
        item: Dict,
        search_keyword: str,
    ) -> tuple[NewsArticle, bool]:
        """
        네이버 API item을 NewsArticle로 변환하고,
        url_hash 기준으로 기존 뉴스가 있으면 재사용합니다.

        반환:
        - NewsArticle 객체
        - 새로 생성되었는지 여부
        """
        original_link = item.get("originallink")
        api_link = item.get("link")

        # 중복 판단 기준 URL
        # 원문 링크가 있으면 원문 링크를 우선 사용합니다.
        canonical_url = original_link or api_link

        if not canonical_url:
            raise HTTPException(
                status_code=500,
                detail="뉴스 URL이 없어 저장할 수 없습니다.",
            )

        url_hash = self._make_url_hash(canonical_url)

        existing_article = self.repository.get_article_by_url_hash(url_hash)

        if existing_article:
            return existing_article, False

        article = NewsArticle(
            title=self._clean_html(item.get("title", "")),
            content=None,
            description=self._clean_html(item.get("description", "")),
            original_link=original_link,
            api_link=api_link,
            url_hash=url_hash,
            source_name=self._extract_source_name(canonical_url),
            provider="NAVER",
            search_keyword=search_keyword,
            published_at=self._parse_pub_date(item.get("pubDate")),
            is_active=True,
        )

        created_article = self.repository.create_article(article)

        return created_article, True

    def _to_article_response(self, article: NewsArticle) -> NewsArticleResponse:
        """
        NewsArticle 모델을 API 응답 schema로 변환합니다.
        """
        return NewsArticleResponse(
            news_id=article.id,
            title=article.title,
            content=article.content,
            description=article.description,
            original_link=article.original_link,
            api_link=article.api_link,
            source_name=article.source_name,
            provider=article.provider,
            search_keyword=article.search_keyword,
            published_at=article.published_at,
            collected_at=article.collected_at,
            updated_at=article.updated_at,
            is_active=article.is_active,
        )

    def _to_stock_article_response(
        self,
        article: NewsArticle,
        mapping: StockNewsMapping,
    ) -> StockNewsArticleResponse:
        """
        NewsArticle + StockNewsMapping을 종목 뉴스 응답 schema로 변환합니다.
        """
        return StockNewsArticleResponse(
            news_id=article.id,
            title=article.title,
            content=article.content,
            description=article.description,
            original_link=article.original_link,
            api_link=article.api_link,
            source_name=article.source_name,
            provider=article.provider,
            search_keyword=article.search_keyword,
            published_at=article.published_at,
            collected_at=article.collected_at,
            updated_at=article.updated_at,
            is_active=article.is_active,
            stock_id=mapping.stock_id,
            matched_keyword=mapping.matched_keyword,
            relevance_score=(
                str(mapping.relevance_score)
                if mapping.relevance_score is not None
                else None
            ),
        )

    def _make_url_hash(self, url: str) -> str:
        """
        URL을 SHA-256 해시로 변환합니다.

        DB에는 긴 URL 자체보다 url_hash를 unique로 두면
        중복 판단이 안정적입니다.
        """
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    def _clean_html(self, text: Optional[str]) -> str:
        """
        네이버 검색 결과의 <b> 태그 및 HTML entity를 간단히 제거합니다.
        """
        if not text:
            return ""

        cleaned = re.sub(r"<[^>]+>", "", text)

        cleaned = (
            cleaned.replace("&quot;", '"')
            .replace("&amp;", "&")
            .replace("&lt;", "<")
            .replace("&gt;", ">")
        )

        return cleaned.strip()

    def _parse_pub_date(self, pub_date: Optional[str]) -> Optional[datetime]:
        """
        네이버 pubDate 문자열을 datetime으로 변환합니다.

        예:
        Mon, 26 Sep 2016 07:50:00 +0900
        """
        if not pub_date:
            return None

        try:
            parsed = parsedate_to_datetime(pub_date)

            # MariaDB DateTime 컬럼에는 timezone 없는 datetime이 안전합니다.
            if parsed.tzinfo:
                parsed = parsed.replace(tzinfo=None)

            return parsed

        except Exception:
            return None

    def _extract_source_name(self, url: Optional[str]) -> Optional[str]:
        """
        URL에서 언론사 도메인을 추출합니다.
        """
        if not url:
            return None

        try:
            netloc = urlparse(url).netloc
            return netloc.replace("www.", "")
        except Exception:
            return None
        
    def _normalize_query(self, query: Optional[str]) -> Optional[str]:
        """
        Swagger나 프론트에서 query가 문자열 'null', 'undefined', 빈 문자열로 들어오는 경우
        실제 검색어로 쓰지 않도록 None으로 변환합니다.
        """
        if query is None:
            return None

        cleaned = query.strip()

        if not cleaned:
            return None

        if cleaned.lower() in ("null", "none", "undefined", "string"):
            return None

        return cleaned
    
    def _normalize_news_sort(self, sort: Optional[str]) -> str:
        """
        뉴스 조회 정렬값을 안전하게 정규화합니다.

        허용값:
        - default
        - latest
        - oldest
        - relevance

        잘못된 값이 들어오면 latest로 처리합니다.
        """
        allowed_sorts = {"default", "latest", "oldest", "relevance"}

        if not sort:
            return "latest"

        cleaned = sort.strip().lower()

        if cleaned not in allowed_sorts:
            return "latest"

        return cleaned