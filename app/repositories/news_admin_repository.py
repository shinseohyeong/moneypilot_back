from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.news_model import NewsArticle, NewsCollectionLog, NewsCollectionSetting


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
    
    def list_active_settings(self) -> List[NewsCollectionSetting]:
        """
        활성화된 뉴스 수집 설정 목록을 조회합니다.
        """
        return (
            self.db.query(NewsCollectionSetting)
            .filter(NewsCollectionSetting.is_active.is_(True))
            .order_by(NewsCollectionSetting.id.asc())
            .all()
        )

    def get_article_by_url_hash(
        self,
        url_hash: str,
    ) -> Optional[NewsArticle]:
        """
        URL 해시 기준으로 이미 저장된 뉴스인지 확인합니다.
        """
        return (
            self.db.query(NewsArticle)
            .filter(NewsArticle.url_hash == url_hash)
            .first()
        )

    def create_article(
        self,
        article: NewsArticle,
    ) -> NewsArticle:
        """
        뉴스 기사를 저장합니다.
        """
        self.db.add(article)
        self.db.flush()
        return article

    def update_setting_last_collected_at(
        self,
        setting: NewsCollectionSetting,
        collected_at,
    ) -> NewsCollectionSetting:
        """
        뉴스 수집 설정의 마지막 수집 시간을 갱신합니다.
        """
        setting.last_collected_at = collected_at
        self.db.flush()
        return setting