# ==========================================
# 파일 위치 : moneypilot_back/app/routers/transaction_router.py
# 역할 : 거래내역 관련 API 엔드포인트 정의
# 기능 :
# 1. 파싱된 거래내역 조회
# 2. 거래 수정
# 3. 거래 삭제
# 4. 현금 거래 직접 입력
# ==========================================
from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.schemas.transaction import TransactionCreate
from app.services.transaction_service import TransactionService
from app.core.database import get_db
from app.core.dependencies import get_current_user

router = APIRouter(
    tags=["Transactions"]
)

# ==========================================
# 월별 거래내역 조회
# GET
# /api/transactions/{month}
# 파일 목록 클릭 후 호출
# ==========================================
@router.get(
    "/",
    summary="월별 거래내역 조회"
)
def get_transactions(
    month: str = Query(
        ...,
        pattern=r"^\d{4}-\d{2}$",
        description="조회할 월 (YYYY-MM)"
    ),
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = TransactionService(db)
    return service.get_transactions(
        current_user.id,
        month
    )

# ==========================================
# 특정 날짜 거래 조회
# GET /transactions/date?date=2026-01-15
# ==========================================
@router.get("/date")
def get_transactions_by_date(
    date: date,
    current_user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    service = TransactionService(db)

    return service.get_transactions_by_date(
        current_user.id,
        date
    )
    
# ==========================================
# 거래 수정
# PUT
# /api/transactions/{transactionId}
# 사용자가 직접 수정
# ==========================================
@router.put(
    "/{transaction_id}",
    summary="거래내역 수정"
)
def update_transaction(
    transaction_id:int,
    request:TransactionCreate,
    db:Session=Depends(get_db),
    current_user = Depends(get_current_user)
):
    service = TransactionService(db)
    return service.update_transaction(
        transaction_id,
        current_user.id,
        request
    )
    
# ==========================================
# 현금 거래 삭제
# DELETE
# /api/transactions/{transaction_id
# ==========================================
@router.delete(
    "/{transaction_id}",
    summary="거래 삭제"
)
def delete_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    service = TransactionService(db)

    service.delete_transaction(
        transaction_id,
        current_user.id
    )

    return {
        "message": "거래 삭제 완료"
    }
    
# ==========================================
# 현금 거래 수기 입력
# POST
# /api/transactions/manual
# statement_id = NULL
# ==========================================
@router.post(
    "/manual",
    status_code=201,
    summary="현금 거래 입력"
)
def create_manual_transaction(
    request:TransactionCreate,
    current_user=Depends(get_current_user),
    db:Session=Depends(get_db)
):
    service = TransactionService(db)
    return service.create_manual_transaction(
        current_user.id,
        request=request
    )