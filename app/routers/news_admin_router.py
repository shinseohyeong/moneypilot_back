from fastapi import APIRouter, Depends, Path, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.news_admin_schema import (
    NewsCollectRunResponse,
    NewsCollectionLogListResponse,
    NewsCollectionSettingCreate,
    NewsCollectionSettingListResponse,
    NewsCollectionSettingResponse,
    NewsCollectionSettingUpdate,
)
from app.services.news_admin_service import NewsAdminService


router = APIRouter(
    prefix="/api/v1/admin/news",
    tags=["관리자 뉴스 수집"],
)


def get_news_admin_service(
    db: Session = Depends(get_db),
) -> NewsAdminService:
    return NewsAdminService(db)


@router.post(
    "/settings",
    response_model=NewsCollectionSettingResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_news_collection_setting(
    request: NewsCollectionSettingCreate,
    service: NewsAdminService = Depends(get_news_admin_service),
):
    return service.create_setting(request=request)


@router.get(
    "/settings",
    response_model=NewsCollectionSettingListResponse,
)
def list_news_collection_settings(
    active_only: bool = Query(default=False),
    service: NewsAdminService = Depends(get_news_admin_service),
):
    return service.list_settings(active_only=active_only)


@router.get(
    "/settings/{setting_id}",
    response_model=NewsCollectionSettingResponse,
)
def get_news_collection_setting(
    setting_id: int = Path(..., ge=1),
    service: NewsAdminService = Depends(get_news_admin_service),
):
    return service.get_setting(setting_id=setting_id)


@router.patch(
    "/settings/{setting_id}",
    response_model=NewsCollectionSettingResponse,
)
def update_news_collection_setting(
    request: NewsCollectionSettingUpdate,
    setting_id: int = Path(..., ge=1),
    service: NewsAdminService = Depends(get_news_admin_service),
):
    return service.update_setting(
        setting_id=setting_id,
        request=request,
    )


@router.get(
    "/logs",
    response_model=NewsCollectionLogListResponse,
)
def list_news_collection_logs(
    limit: int = Query(default=50, ge=1, le=100),
    service: NewsAdminService = Depends(get_news_admin_service),
):
    return service.list_logs(limit=limit)

@router.post(
    "/collect/run",
    response_model=NewsCollectRunResponse,
)
def run_news_collection(
    setting_id: int | None = Query(default=None, ge=1),
    service: NewsAdminService = Depends(get_news_admin_service),
):
    """
    뉴스 수집 설정을 기준으로 수동 뉴스 수집을 실행합니다.

    - setting_id가 없으면 활성화된 전체 키워드를 수집합니다.
    - setting_id가 있으면 해당 설정 1개만 수집합니다.
    """
    return service.run_news_collection(setting_id=setting_id)