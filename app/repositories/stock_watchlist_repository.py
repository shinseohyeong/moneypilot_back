# 파일 위치: app/repositories/stock_watchlist_repository.py
# 역할: 관심종목 카테고리, 관심종목 DB 조회/저장/수정/삭제 담당

from typing import List, Optional, Tuple

from sqlalchemy.orm import Session

from app.models.stock_model import (
    Stock,
    StockPrice,
    StockWatchlist,
    StockWatchlistCategory,
)


class StockWatchlistRepository:
    def __init__(self, db: Session):
        self.db = db

    # =========================
    # Category
    # =========================

    def get_category_by_id_and_user(
        self,
        category_id: int,
        user_id: int,
    ) -> Optional[StockWatchlistCategory]:
        return (
            self.db.query(StockWatchlistCategory)
            .filter(
                StockWatchlistCategory.id == category_id,
                StockWatchlistCategory.user_id == user_id,
            )
            .first()
        )

    def get_category_by_name(
        self,
        user_id: int,
        category_name: str,
    ) -> Optional[StockWatchlistCategory]:
        return (
            self.db.query(StockWatchlistCategory)
            .filter(
                StockWatchlistCategory.user_id == user_id,
                StockWatchlistCategory.category_name == category_name,
            )
            .first()
        )

    def get_categories_by_user(
        self,
        user_id: int,
    ) -> List[StockWatchlistCategory]:
        return (
            self.db.query(StockWatchlistCategory)
            .filter(StockWatchlistCategory.user_id == user_id)
            .order_by(
                StockWatchlistCategory.display_order.asc(),
                StockWatchlistCategory.id.asc(),
            )
            .all()
        )

    def create_category(
        self,
        user_id: int,
        category_name: str,
        display_order: int,
        is_default: bool,
    ) -> StockWatchlistCategory:
        category = StockWatchlistCategory(
            user_id=user_id,
            category_name=category_name,
            display_order=display_order,
            is_default=is_default,
        )

        self.db.add(category)
        self.db.flush()  # commit 전 id를 받아오기 위해 flush 사용
        return category

    def update_category(
        self,
        category: StockWatchlistCategory,
        update_data: dict,
    ) -> StockWatchlistCategory:
        for key, value in update_data.items():
            setattr(category, key, value)

        self.db.flush()
        return category

    def count_watchlists_by_category(
        self,
        category_id: int,
        user_id: int,
    ) -> int:
        return (
            self.db.query(StockWatchlist)
            .filter(
                StockWatchlist.category_id == category_id,
                StockWatchlist.user_id == user_id,
            )
            .count()
        )

    def delete_category(
        self,
        category: StockWatchlistCategory,
    ) -> None:
        self.db.delete(category)

    # =========================
    # Stock / Price
    # =========================

    def get_stock_by_id(self, stock_id: int) -> Optional[Stock]:
        return (
            self.db.query(Stock)
            .filter(
                Stock.id == stock_id,
                Stock.is_active == True,
            )
            .first()
        )

    def get_latest_price_by_stock_id(
        self,
        stock_id: int,
    ) -> Optional[StockPrice]:
        return (
            self.db.query(StockPrice)
            .filter(
                StockPrice.stock_id == stock_id,
                StockPrice.source == "PUBLIC_DATA",
            )
            .order_by(StockPrice.price_date.desc())
            .first()
        )

    # =========================
    # Watchlist
    # =========================

    def get_watchlist_by_user_category_stock(
        self,
        user_id: int,
        category_id: int,
        stock_id: int,
    ) -> Optional[StockWatchlist]:
        return (
            self.db.query(StockWatchlist)
            .filter(
                StockWatchlist.user_id == user_id,
                StockWatchlist.category_id == category_id,
                StockWatchlist.stock_id == stock_id,
            )
            .first()
        )

    def get_watchlist_by_id_and_user(
        self,
        watchlist_id: int,
        user_id: int,
    ) -> Optional[StockWatchlist]:
        return (
            self.db.query(StockWatchlist)
            .filter(
                StockWatchlist.id == watchlist_id,
                StockWatchlist.user_id == user_id,
            )
            .first()
        )

    def create_watchlist(
        self,
        user_id: int,
        category_id: int,
        stock_id: int,
        memo: Optional[str],
        alert_enabled: bool,
        alert_price,
    ) -> StockWatchlist:
        watchlist = StockWatchlist(
            user_id=user_id,
            category_id=category_id,
            stock_id=stock_id,
            memo=memo,
            alert_enabled=alert_enabled,
            alert_price=alert_price,
        )

        self.db.add(watchlist)
        self.db.flush()
        return watchlist

    def get_watchlists_with_details_by_user(
        self,
        user_id: int,
    ) -> List[Tuple[StockWatchlist, Stock, StockWatchlistCategory]]:
        """
        관심종목 + 종목 + 카테고리 정보를 함께 조회한다.
        최근 시세는 stock_id 기준으로 별도 조회해서 service에서 붙인다.
        """
        return (
            self.db.query(StockWatchlist, Stock, StockWatchlistCategory)
            .join(Stock, StockWatchlist.stock_id == Stock.id)
            .join(
                StockWatchlistCategory,
                StockWatchlist.category_id == StockWatchlistCategory.id,
            )
            .filter(StockWatchlist.user_id == user_id)
            .order_by(
                StockWatchlistCategory.display_order.asc(),
                StockWatchlistCategory.id.asc(),
                Stock.stock_name.asc(),
            )
            .all()
        )

    def update_watchlist(
        self,
        watchlist: StockWatchlist,
        update_data: dict,
    ) -> StockWatchlist:
        for key, value in update_data.items():
            setattr(watchlist, key, value)

        self.db.flush()
        return watchlist

    def delete_watchlist(
        self,
        watchlist: StockWatchlist,
    ) -> None:
        self.db.delete(watchlist)

    # =========================
    # Transaction
    # =========================

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()