# ==========================================
# 파일 위치 :
# moneypilot_back/app/repositories/transaction_repository.py
# 역할 :
# transactions 테이블 DB 접근 담당
# 담당:
# 1. 거래 저장
# 2. 거래 조회
# 3. 거래 수정
# 4. 거래 삭제
# ==========================================
from sqlalchemy.orm import Session

from app.models import Transaction

class TransactionRepository:
    def __init__(
        self,
        db:Session
    ):
        self.db=db

    # ======================================
    # 거래 저장
    # INSERT transactions
    # ======================================
    def save(
        self,
        transaction:Transaction
    ):
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    # ======================================
    # 여러 거래 저장
    # 엑셀 파싱 결과 bulk insert용
    # ======================================
    def save_all(
        self,
        transactions:list
    ):
        self.db.add_all(
            transactions
        )
        self.db.commit()
        return transactions

    # ======================================
    # 명세서별 거래 조회
    # 파일 클릭했을 때 사용
    # ======================================
    def find_all_by_statement(
        self,
        statement_id:int
    ):
        return (
            self.db.query(Transaction).filter(
                Transaction.statement_id == statement_id
            ).all()
        )
        
    # ======================================
    # 거래 단건 조회
    # 수정/삭제 전 조회
    # ======================================
    def find_by_id(
        self,
        transaction_id:int
    ):
        return (
            self.db.query(Transaction).filter(
                Transaction.id == transaction_id
            ).first()
        )

    # ======================================
    # 거래 수정
    # UPDATE
    # ======================================
    def update(
        self,
        transaction:Transaction
    ):
        self.db.commit()
        self.db.refresh(transaction)
        return transaction

    # ======================================
    # 거래 삭제
    # DELETE
    # ======================================
    def delete(
        self,
        transaction:Transaction
    ):
        self.db.delete(transaction)
        self.db.commit()