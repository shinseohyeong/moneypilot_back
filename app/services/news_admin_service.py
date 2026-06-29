from typing import Any

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.news_model import NewsCollectionSetting
from app.repositories.news_admin_repository import NewsAdminRepository
from app.schemas.news_admin_schema import (
    NewsCollectionLogListResponse,
    NewsCollectionLogResponse,
    NewsCollectionSettingCreate,
    NewsCollectionSettingListResponse,
    NewsCollectionSettingResponse,
    NewsCollectionSettingUpdate,
)


class NewsAdminService:
    """
    관리자 뉴스 수집 설정 비즈니스 로직을 담당합니다.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repository = NewsAdminRepository(db)

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