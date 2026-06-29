# 파일 위치: app/services/stock_watchlist_service.py
# 역할: 관심종목 카테고리/관심종목 비즈니스 로직 처리

from fastapi import HTTPException

from app.repositories.stock_watchlist_repository import StockWatchlistRepository
from app.schemas.stock_watchlist_schema import (
    StockWatchlistCategoryCreate,
    StockWatchlistCategoryDeleteResponse,
    StockWatchlistCategoryGroup,
    StockWatchlistCategoryItem,
    StockWatchlistCategoryListResponse,
    StockWatchlistCategoryUpdate,
    StockWatchlistCreate,
    StockWatchlistDeleteResponse,
    StockWatchlistGroupedResponse,
    StockWatchlistItem,
    StockWatchlistLatestPrice,
    StockWatchlistUpdate,
)


class StockWatchlistService:
    def __init__(self, repository: StockWatchlistRepository):
        self.repository = repository

    # =========================
    # Category
    # =========================

    def create_category(
        self,
        user_id: int,
        request: StockWatchlistCategoryCreate,
    ) -> StockWatchlistCategoryItem:
        category_name = request.category_name.strip()

        if not category_name:
            raise HTTPException(
                status_code=400,
                detail="카테고리명을 입력해주세요.",
            )

        existing_category = self.repository.get_category_by_name(
            user_id=user_id,
            category_name=category_name,
        )

        if existing_category:
            raise HTTPException(
                status_code=409,
                detail="이미 존재하는 관심종목 카테고리입니다.",
            )

        try:
            category = self.repository.create_category(
                user_id=user_id,
                category_name=category_name,
                display_order=request.display_order,
                is_default=request.is_default,
            )
            self.repository.commit()

        except Exception as exc:
            self.repository.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"관심종목 카테고리 생성 중 오류가 발생했습니다: {exc}",
            ) from exc

        return self._to_category_item(category)

    def get_categories(
        self,
        user_id: int,
    ) -> StockWatchlistCategoryListResponse:
        categories = self.repository.get_categories_by_user(user_id)

        return StockWatchlistCategoryListResponse(
            items=[
                self._to_category_item(category)
                for category in categories
            ]
        )

    def update_category(
        self,
        user_id: int,
        category_id: int,
        request: StockWatchlistCategoryUpdate,
    ) -> StockWatchlistCategoryItem:
        category = self.repository.get_category_by_id_and_user(
            category_id=category_id,
            user_id=user_id,
        )

        if not category:
            raise HTTPException(
                status_code=404,
                detail="관심종목 카테고리를 찾을 수 없습니다.",
            )

        update_data = request.model_dump(exclude_unset=True)

        if "category_name" in update_data:
            update_data["category_name"] = update_data["category_name"].strip()

            if not update_data["category_name"]:
                raise HTTPException(
                    status_code=400,
                    detail="카테고리명을 입력해주세요.",
                )

            existing_category = self.repository.get_category_by_name(
                user_id=user_id,
                category_name=update_data["category_name"],
            )

            if existing_category and existing_category.id != category_id:
                raise HTTPException(
                    status_code=409,
                    detail="이미 존재하는 관심종목 카테고리입니다.",
                )

        try:
            updated_category = self.repository.update_category(
                category=category,
                update_data=update_data,
            )
            self.repository.commit()

        except Exception as exc:
            self.repository.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"관심종목 카테고리 수정 중 오류가 발생했습니다: {exc}",
            ) from exc

        return self._to_category_item(updated_category)

    def delete_category(
        self,
        user_id: int,
        category_id: int,
    ) -> StockWatchlistCategoryDeleteResponse:
        category = self.repository.get_category_by_id_and_user(
            category_id=category_id,
            user_id=user_id,
        )

        if not category:
            raise HTTPException(
                status_code=404,
                detail="관심종목 카테고리를 찾을 수 없습니다.",
            )

        watchlist_count = self.repository.count_watchlists_by_category(
            category_id=category_id,
            user_id=user_id,
        )

        if watchlist_count > 0:
            raise HTTPException(
                status_code=400,
                detail="카테고리에 관심종목이 있어 삭제할 수 없습니다. 먼저 관심종목을 삭제하거나 이동해주세요.",
            )

        try:
            self.repository.delete_category(category)
            self.repository.commit()

        except Exception as exc:
            self.repository.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"관심종목 카테고리 삭제 중 오류가 발생했습니다: {exc}",
            ) from exc

        return StockWatchlistCategoryDeleteResponse(
            category_id=category_id,
            message="관심종목 카테고리가 삭제되었습니다.",
        )

    # =========================
    # Watchlist
    # =========================

    def create_watchlist(
        self,
        user_id: int,
        request: StockWatchlistCreate,
    ) -> StockWatchlistItem:
        category = self.repository.get_category_by_id_and_user(
            category_id=request.category_id,
            user_id=user_id,
        )

        if not category:
            raise HTTPException(
                status_code=404,
                detail="관심종목 카테고리를 찾을 수 없습니다.",
            )

        stock = self.repository.get_stock_by_id(request.stock_id)

        if not stock:
            raise HTTPException(
                status_code=404,
                detail="종목을 찾을 수 없습니다.",
            )

        existing_watchlist = self.repository.get_watchlist_by_user_category_stock(
            user_id=user_id,
            category_id=request.category_id,
            stock_id=request.stock_id,
        )

        if existing_watchlist:
            raise HTTPException(
                status_code=409,
                detail="이미 해당 카테고리에 등록된 관심종목입니다.",
            )

        try:
            watchlist = self.repository.create_watchlist(
                user_id=user_id,
                category_id=request.category_id,
                stock_id=request.stock_id,
                memo=request.memo,
                alert_enabled=request.alert_enabled,
                alert_price=request.alert_price,
            )
            self.repository.commit()

        except Exception as exc:
            self.repository.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"관심종목 저장 중 오류가 발생했습니다: {exc}",
            ) from exc

        latest_price = self.repository.get_latest_price_by_stock_id(stock.id)

        return self._to_watchlist_item(
            watchlist=watchlist,
            stock=stock,
            category=category,
            latest_price=latest_price,
        )

    def get_watchlists(
        self,
        user_id: int,
    ) -> StockWatchlistGroupedResponse:
        categories = self.repository.get_categories_by_user(user_id)
        rows = self.repository.get_watchlists_with_details_by_user(user_id)

        # 카테고리별 빈 리스트를 먼저 만든다.
        grouped = {
            category.id: StockWatchlistCategoryGroup(
                category_id=category.id,
                category_name=category.category_name,
                display_order=category.display_order,
                is_default=category.is_default,
                items=[],
            )
            for category in categories
        }

        for watchlist, stock, category in rows:
            latest_price = self.repository.get_latest_price_by_stock_id(stock.id)

            item = self._to_watchlist_item(
                watchlist=watchlist,
                stock=stock,
                category=category,
                latest_price=latest_price,
            )

            if category.id not in grouped:
                grouped[category.id] = StockWatchlistCategoryGroup(
                    category_id=category.id,
                    category_name=category.category_name,
                    display_order=category.display_order,
                    is_default=category.is_default,
                    items=[],
                )

            grouped[category.id].items.append(item)

        return StockWatchlistGroupedResponse(
            categories=list(grouped.values())
        )

    def update_watchlist(
        self,
        user_id: int,
        watchlist_id: int,
        request: StockWatchlistUpdate,
    ) -> StockWatchlistItem:
        watchlist = self.repository.get_watchlist_by_id_and_user(
            watchlist_id=watchlist_id,
            user_id=user_id,
        )

        if not watchlist:
            raise HTTPException(
                status_code=404,
                detail="관심종목을 찾을 수 없습니다.",
            )

        update_data = request.model_dump(exclude_unset=True)

        # category_id가 들어오면 해당 사용자의 카테고리인지 확인
        if "category_id" in update_data:
            category = self.repository.get_category_by_id_and_user(
                category_id=update_data["category_id"],
                user_id=user_id,
            )

            if not category:
                raise HTTPException(
                    status_code=404,
                    detail="이동할 관심종목 카테고리를 찾을 수 없습니다.",
                )

            existing_watchlist = self.repository.get_watchlist_by_user_category_stock(
                user_id=user_id,
                category_id=update_data["category_id"],
                stock_id=watchlist.stock_id,
            )

            if existing_watchlist and existing_watchlist.id != watchlist_id:
                raise HTTPException(
                    status_code=409,
                    detail="이동하려는 카테고리에 이미 같은 종목이 등록되어 있습니다.",
                )

        try:
            updated_watchlist = self.repository.update_watchlist(
                watchlist=watchlist,
                update_data=update_data,
            )
            self.repository.commit()

        except Exception as exc:
            self.repository.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"관심종목 수정 중 오류가 발생했습니다: {exc}",
            ) from exc

        stock = self.repository.get_stock_by_id(updated_watchlist.stock_id)
        category = self.repository.get_category_by_id_and_user(
            category_id=updated_watchlist.category_id,
            user_id=user_id,
        )
        latest_price = self.repository.get_latest_price_by_stock_id(
            updated_watchlist.stock_id
        )

        return self._to_watchlist_item(
            watchlist=updated_watchlist,
            stock=stock,
            category=category,
            latest_price=latest_price,
        )

    def delete_watchlist(
        self,
        user_id: int,
        watchlist_id: int,
    ) -> StockWatchlistDeleteResponse:
        watchlist = self.repository.get_watchlist_by_id_and_user(
            watchlist_id=watchlist_id,
            user_id=user_id,
        )

        if not watchlist:
            raise HTTPException(
                status_code=404,
                detail="관심종목을 찾을 수 없습니다.",
            )

        try:
            self.repository.delete_watchlist(watchlist)
            self.repository.commit()

        except Exception as exc:
            self.repository.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"관심종목 삭제 중 오류가 발생했습니다: {exc}",
            ) from exc

        return StockWatchlistDeleteResponse(
            watchlist_id=watchlist_id,
            message="관심종목이 삭제되었습니다.",
        )

    # =========================
    # Response helpers
    # =========================

    def _to_category_item(self, category) -> StockWatchlistCategoryItem:
        return StockWatchlistCategoryItem(
            category_id=category.id,
            category_name=category.category_name,
            display_order=category.display_order,
            is_default=category.is_default,
            created_at=category.created_at,
            updated_at=category.updated_at,
        )

    def _to_latest_price(self, latest_price) -> StockWatchlistLatestPrice | None:
        if not latest_price:
            return None

        return StockWatchlistLatestPrice(
            price_date=latest_price.price_date,
            close_price=latest_price.close_price,
            price_change=latest_price.price_change,
            change_rate=latest_price.change_rate,
            volume=latest_price.volume,
            market_cap=latest_price.market_cap,
        )

    def _to_watchlist_item(
        self,
        watchlist,
        stock,
        category,
        latest_price,
    ) -> StockWatchlistItem:
        return StockWatchlistItem(
            watchlist_id=watchlist.id,

            category_id=category.id,
            category_name=category.category_name,

            stock_id=stock.id,
            stock_code=stock.stock_code,
            stock_name=stock.stock_name,
            market=stock.market,

            memo=watchlist.memo,
            alert_enabled=watchlist.alert_enabled,
            alert_price=watchlist.alert_price,

            created_at=watchlist.created_at,
            updated_at=watchlist.updated_at,

            latest_price=self._to_latest_price(latest_price),
        )