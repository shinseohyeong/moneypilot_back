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
from app.models.card_statement_model import CardStatement
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
        self.repository = TransactionRepository(db)

    # ======================================
    # 월별 거래내역 조회
    # ======================================
    def get_transactions(
        self,
        user_id: int,
        month: str
    ):
        return self.repository.find_all_by_month(
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
        return self.repository.find_all_by_date(
            user_id,
            date
        )

    # ======================================
    # 거래 수정
    # ======================================
    def update_transaction(
        self,
        transaction_id:int,
        request
    ):
        transaction=(
            self.db.query(Transaction).filter(
                Transaction.id==transaction_id
            ).first()
        )
        if not transaction:
            raise Exception(
                "거래 없음"
            )
        data=request.dict(
            exclude_none=True
        )

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
        transaction_id:int
    ):
        transaction=(
            self.db.query(Transaction).filter(
                Transaction.id==transaction_id
            ).first()
        )
        if not transaction:
            raise Exception(
                "거래 없음"
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

        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction