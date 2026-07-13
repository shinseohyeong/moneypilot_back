# ==========================================
# 파일 위치 :
# moneypilot_back/app/services/transaction_service.py
# 역할 :
# 거래내역 관리 서비스
# 기능:
# 1. 거래 조회
# 2. 거래 수정
# 3. 거래 삭제
# 4. 현금 입력
# ==========================================
from sqlalchemy.orm import Session

from app.models.transaction_model import Transaction
from app.repositories.transaction_repository import (
    TransactionRepository
)
from app.repositories.card_statement_repository import (
    FileRepository
)

class TransactionService:
    def __init__(
        self,
        db:Session
    ):
        self.db=db
        self.transaction_repo = TransactionRepository(db)
        self.file_repo = FileRepository(db)

    # ======================================
    # 월별 거래내역 조회
    # ======================================
    def get_transactions(
        self,
        user_id: int,
        month: str
    ):
        return self.transaction_repo.find_all_by_month(
        user_id,
        month
    )
        
    # ======================================
    # 날짜별 거래 조회
    # ======================================
    def get_transactions_by_date(
        self,
        user_id: int,
        date
    ):
        return self.transaction_repo.find_all_by_date(
            user_id,
            date
        )

    # ======================================
    # 거래 수정
    # ======================================
    def update_transaction(
        self,
        transaction_id:int,
        user_id: int,
        request
    ):
        transaction = self.transaction_repo.find_by_id(transaction_id,user_id)
        
        if not transaction:
            raise Exception(
                status_code=400,
                detail="거래 없음"
            )
        data=request.model_dump(exclude_none=True)

        for key,value in data.items():
            setattr(
                transaction,
                key,
                value
            )
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    # ======================================
    # 거래 삭제
    # ======================================
    def delete_transaction(
        self,
        transaction_id:int,
        user_id: int
    ):
        transaction = self.transaction_repo.find_by_id(transaction_id, user_id)
        if not transaction:
            raise Exception(
                status_code=400,
                detail="거래 없음"
            )

        self.db.delete(transaction)
        self.db.commit()

    # ======================================
    # 현금 거래 입력
    # statement_id = NULL
    # ======================================
    def create_manual_transaction(
        self,
        user_id:int,
        request
    ):
        transaction=Transaction(
            user_id=user_id,
            statement_id=None,
            transaction_date=request.transaction_date,
            month=str(
                request.transaction_date
            )[:7],
            merchant_name=request.merchant_name,
            description=request.description,
            amount=request.amount,
            category=request.category,
            expense_type=request.expense_type

        )

        self.transaction_repo.save(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction