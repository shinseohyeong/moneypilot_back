# ==========================================
# 파일 위치 : moneypilot_back/app/routers/transaction_router.py
# 역할 : 거래내역 관련 API 엔드포인트 정의
# 기능 :
# 1. 파싱된 거래내역 조회
# 2. 거래 수정
# 3. 거래 삭제
# 4. 현금 거래 직접 입력
# ==========================================
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.transaction import TransactionCreate
from app.services.transaction_service import TransactionService
from app.core.database import get_db
from app.core.dependencies import get_current_user

router = APIRouter(
    tags=["Transactions"]
)

# ==========================================
# 거래내역 상세 조회
# GET
# /api/transactions/{transactionId}
# 파일 목록 클릭 후 호출
# ==========================================
@router.get(
    "/{statement_id}",
    summary="거래내역 조회"
)
def get_transactions(
    statement_id:int,
    db:Session=Depends(get_db),
    current_user = Depends(get_current_user)
):
    service = TransactionService(db)
    return service.get_transactions(
        statement_id,
        current_user.id
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
    db:Session=Depends(get_db),
    current_user = Depends(get_current_user)
):
    service = TransactionService(db)
    return service.create_manual_transaction(
        user_id=current_user.id,
        request=request
    )