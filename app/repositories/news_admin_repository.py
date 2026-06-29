from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.news_model import NewsCollectionLog, NewsCollectionSetting


class NewsAdminRepository:
    """
    뉴스 수집 설정/로그 DB 처리를 담당합니다.

    주의:
    - repository에서는 commit/rollback을 하지 않습니다.
    - commit/rollback은 service에서 처리합니다.
    """

    def __init__(self, db: Session):
        self.db = db

    def create_setting(
        self,
        setting: NewsCollectionSetting,
    ) -> NewsCollectionSetting:
        self.db.add(setting)
        self.db.flush()
        return setting

    def get_setting_by_id(
        self,
        setting_id: int,
    ) -> Optional[NewsCollectionSetting]:
        return (
            self.db.query(NewsCollectionSetting)
            .filter(NewsCollectionSetting.id == setting_id)
            .first()
        )

    def get_setting_by_keyword_provider(
        self,
        keyword: str,
        provider: str,
    ) -> Optional[NewsCollectionSetting]:
        return (
            self.db.query(NewsCollectionSetting)
            .filter(
                NewsCollectionSetting.keyword == keyword,
                NewsCollectionSetting.provider == provider,
            )
            .first()
        )

    def list_settings(
        self,
        active_only: bool = False,
    ) -> List[NewsCollectionSetting]:
        query = self.db.query(NewsCollectionSetting)

        if active_only:
            query = query.filter(NewsCollectionSetting.is_active.is_(True))

        return query.order_by(NewsCollectionSetting.id.desc()).all()

    def create_log(
        self,
        log: NewsCollectionLog,
    ) -> NewsCollectionLog:
        self.db.add(log)
        self.db.flush()
        return log

    def list_logs(
        self,
        limit: int = 50,
    ) -> List[NewsCollectionLog]:
        return (
            self.db.query(NewsCollectionLog)
            .order_by(NewsCollectionLog.id.desc())
            .limit(limit)
            .all()
        )