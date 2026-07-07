from typing import Any, Optional

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import hashlib
import re
from datetime import datetime
from email.utils import parsedate_to_datetime
from html import unescape

from app.clients.naver_news_client import get_naver_news_client
from app.models.news_model import NewsCollectionSetting, NewsArticle, NewsCollectionLog
from app.repositories.news_admin_repository import NewsAdminRepository
from app.schemas.news_admin_schema import (
    NewsCollectionLogListResponse,
    NewsCollectionLogResponse,
    NewsCollectionSettingCreate,
    NewsCollectionSettingListResponse,
    NewsCollectionSettingResponse,
    NewsCollectionSettingUpdate,
    NewsCollectKeywordResult,
    NewsCollectRunResponse,
)


class NewsAdminService:
    """
    관리자 뉴스 수집 설정 비즈니스 로직을 담당합니다.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = NewsAdminRepository(db)
        self.naver_news_client = get_naver_news_client()

    def create_setting(
        self,
        request: NewsCollectionSettingCreate,
    ) -> NewsCollectionSettingResponse:
        keyword = request.keyword.strip()
        provider = request.provider.strip().upper()

        if request.sort not in ("date", "sim"):
            raise HTTPException(
                status_code=400,
                detail="sort는 date 또는 sim만 사용할 수 있습니다.",
            )

        existing = self.repository.get_setting_by_keyword_provider(
            keyword=keyword,
            provider=provider,
        )

        if existing:
            raise HTTPException(
                status_code=409,
                detail="이미 등록된 뉴스 수집 키워드입니다.",
            )

        try:
            setting = NewsCollectionSetting(
                keyword=keyword,
                category=request.category,
                provider=provider,
                interval_minutes=request.interval_minutes,
                display_count=request.display_count,
                sort=request.sort,
                is_active=request.is_active,
            )

            saved_setting = self.repository.create_setting(setting)

            self.db.commit()
            self.db.refresh(saved_setting)

            return self._to_setting_response(saved_setting)

        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=409,
                detail="이미 등록된 뉴스 수집 설정입니다.",
            )

        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"뉴스 수집 설정 등록 중 오류가 발생했습니다: {str(e)}",
            )

    def list_settings(
        self,
        active_only: bool = False,
    ) -> NewsCollectionSettingListResponse:
        settings = self.repository.list_settings(active_only=active_only)

        return NewsCollectionSettingListResponse(
            total_count=len(settings),
            items=[
                self._to_setting_response(setting)
                for setting in settings
            ],
        )

    def get_setting(
        self,
        setting_id: int,
    ) -> NewsCollectionSettingResponse:
        setting = self.repository.get_setting_by_id(setting_id=setting_id)

        if not setting:
            raise HTTPException(
                status_code=404,
                detail="해당 뉴스 수집 설정을 찾을 수 없습니다.",
            )

        return self._to_setting_response(setting)

    def update_setting(
        self,
        setting_id: int,
        request: NewsCollectionSettingUpdate,
    ) -> NewsCollectionSettingResponse:
        setting = self.repository.get_setting_by_id(setting_id=setting_id)

        if not setting:
            raise HTTPException(
                status_code=404,
                detail="해당 뉴스 수집 설정을 찾을 수 없습니다.",
            )

        update_data = request.model_dump(exclude_unset=True)

        if "keyword" in update_data and update_data["keyword"] is not None:
            update_data["keyword"] = update_data["keyword"].strip()

        if "provider" in update_data and update_data["provider"] is not None:
            update_data["provider"] = update_data["provider"].strip().upper()

        if "sort" in update_data and update_data["sort"] not in ("date", "sim"):
            raise HTTPException(
                status_code=400,
                detail="sort는 date 또는 sim만 사용할 수 있습니다.",
            )

        try:
            for field, value in update_data.items():
                setattr(setting, field, value)

            self.db.commit()
            self.db.refresh(setting)

            return self._to_setting_response(setting)

        except IntegrityError:
            self.db.rollback()
            raise HTTPException(
                status_code=409,
                detail="이미 등록된 뉴스 수집 설정과 중복됩니다.",
            )

        except Exception as e:
            self.db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"뉴스 수집 설정 수정 중 오류가 발생했습니다: {str(e)}",
            )

    def list_logs(
        self,
        limit: int = 50,
    ) -> NewsCollectionLogListResponse:
        logs = self.repository.list_logs(limit=limit)

        return NewsCollectionLogListResponse(
            total_count=len(logs),
            items=[
                self._to_log_response(log)
                for log in logs
            ],
        )

    def _to_setting_response(
        self,
        setting: Any,
    ) -> NewsCollectionSettingResponse:
        return NewsCollectionSettingResponse(
            id=setting.id,
            keyword=setting.keyword,
            category=setting.category,
            provider=setting.provider,
            interval_minutes=setting.interval_minutes,
            display_count=setting.display_count,
            sort=setting.sort,
            is_active=setting.is_active,
            last_collected_at=setting.last_collected_at,
            created_at=setting.created_at,
            updated_at=setting.updated_at,
        )

    def _to_log_response(
        self,
        log: Any,
    ) -> NewsCollectionLogResponse:
        return NewsCollectionLogResponse(
            id=log.id,
            setting_id=log.setting_id,
            keyword=log.keyword,
            provider=log.provider,
            status=log.status,
            requested_count=log.requested_count,
            saved_count=log.saved_count,
            duplicated_count=log.duplicated_count,
            error_message=log.error_message,
            started_at=log.started_at,
            finished_at=log.finished_at,
            created_at=log.created_at,
        )
    
    def run_news_collection(
        self,
        setting_id: Optional[int] = None,
    ) -> NewsCollectRunResponse:
        """
        뉴스 수집 설정을 기준으로 수동 뉴스 수집을 실행합니다.

        setting_id가 있으면 해당 설정 1개만 수집합니다.
        setting_id가 없으면 활성화된 전체 설정을 수집합니다.
        """
        if setting_id:
            setting = self.repository.get_setting_by_id(setting_id=setting_id)

            if not setting:
                raise HTTPException(
                    status_code=404,
                    detail="해당 뉴스 수집 설정을 찾을 수 없습니다.",
                )

            settings = [setting]

        else:
            settings = self.repository.list_active_settings()

        if not settings:
            raise HTTPException(
                status_code=404,
                detail="활성화된 뉴스 수집 설정이 없습니다.",
            )

        results = []

        for setting in settings:
            result = self._collect_news_by_setting(setting)
            results.append(result)

        return NewsCollectRunResponse(
            total_settings=len(results),
            success_count=len([item for item in results if item.status == "SUCCESS"]),
            failed_count=len([item for item in results if item.status == "FAILED"]),
            total_requested_count=sum(item.requested_count for item in results),
            total_saved_count=sum(item.saved_count for item in results),
            total_duplicated_count=sum(item.duplicated_count for item in results),
            items=results,
        )

    def _collect_news_by_setting(
        self,
        setting: Any,
    ) -> NewsCollectKeywordResult:
        """
        설정 1개 기준으로 네이버 뉴스를 수집하고 DB에 저장합니다.
        """
        started_at = datetime.now()
        requested_count = 0
        saved_count = 0
        duplicated_count = 0
        error_message = None
        status = "SUCCESS"

        try:
            api_result = self.naver_news_client.search_news(
                keyword=setting.keyword,
                display=setting.display_count,
                start=1,
                sort=setting.sort,
            )

            items = api_result.get("items", [])
            requested_count = len(items)

            for item in items:
                original_link = item.get("originallink")
                api_link = item.get("link")
                url = original_link or api_link

                if not url:
                    continue

                url_hash = self._make_url_hash(url)

                existing_article = self.repository.get_article_by_url_hash(
                    url_hash=url_hash,
                )

                if existing_article:
                    duplicated_count += 1
                    continue

                article = NewsArticle(
                    title=self._clean_text(item.get("title")),
                    description=self._clean_text(item.get("description")),
                    content=None,
                    original_link=original_link,
                    api_link=api_link,
                    url_hash=url_hash,
                    source_name="NAVER",
                    provider=setting.provider,
                    search_keyword=setting.keyword,
                    published_at=self._parse_pub_date(item.get("pubDate")),
                    collected_at=datetime.now(),
                    is_active=True,
                )

                self.repository.create_article(article)
                saved_count += 1

            finished_at = datetime.now()

            log = NewsCollectionLog(
                setting_id=setting.id,
                keyword=setting.keyword,
                provider=setting.provider,
                status=status,
                requested_count=requested_count,
                saved_count=saved_count,
                duplicated_count=duplicated_count,
                error_message=None,
                started_at=started_at,
                finished_at=finished_at,
            )

            self.repository.create_log(log)
            self.repository.update_setting_last_collected_at(
                setting=setting,
                collected_at=finished_at,
            )

            self.db.commit()

            return NewsCollectKeywordResult(
                setting_id=setting.id,
                keyword=setting.keyword,
                provider=setting.provider,
                requested_count=requested_count,
                saved_count=saved_count,
                duplicated_count=duplicated_count,
                status=status,
                error_message=None,
            )

        except Exception as e:
            self.db.rollback()

            status = "FAILED"
            error_message = str(e)
            finished_at = datetime.now()

            try:
                log = NewsCollectionLog(
                    setting_id=setting.id,
                    keyword=setting.keyword,
                    provider=setting.provider,
                    status=status,
                    requested_count=requested_count,
                    saved_count=saved_count,
                    duplicated_count=duplicated_count,
                    error_message=error_message,
                    started_at=started_at,
                    finished_at=finished_at,
                )

                self.repository.create_log(log)
                self.db.commit()

            except Exception:
                self.db.rollback()

            return NewsCollectKeywordResult(
                setting_id=setting.id,
                keyword=setting.keyword,
                provider=setting.provider,
                requested_count=requested_count,
                saved_count=saved_count,
                duplicated_count=duplicated_count,
                status=status,
                error_message=error_message,
            )

    def _make_url_hash(self, url: str) -> str:
        """
        URL 중복 저장 방지를 위한 해시를 생성합니다.
        """
        return hashlib.sha256(url.encode("utf-8")).hexdigest()

    def _clean_text(self, value: Optional[str]) -> Optional[str]:
        """
        네이버 뉴스 API 응답의 HTML 태그와 엔티티를 정리합니다.
        """
        if value is None:
            return None

        text = unescape(value)
        text = re.sub(r"<.*?>", "", text)
        return text.strip()

    def _parse_pub_date(self, value: Optional[str]) -> Optional[datetime]:
        """
        네이버 pubDate 문자열을 datetime으로 변환합니다.
        """
        if not value:
            return None

        try:
            parsed = parsedate_to_datetime(value)
            return parsed.replace(tzinfo=None)

        except Exception:
            return None