# ==========================================
# 파일 위치 : moneypilot_back/app/services/file_service.py
# 역할 : 거래명세서 파일 관련 비즈니스 로직
# 담당:
# 1. 파일 저장
# 2. card_statements 저장
# 3. 엑셀 파싱
# 4. transactions 저장
# 5. 파일 목록 조회
# 6. 파일 삭제
# 7. 상태 조회
# ==========================================
from pathlib import Path
import os
from datetime import datetime
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
import uuid

from app.models import (
    CardStatement,
    Transaction
)
from app.repositories.card_statement_repository import FileRepository
from app.repositories.transaction_repository import TransactionRepository
from app.services.vision_service import VisionService
from app.repositories.admin_repository import AdminRepository

UPLOAD_DIR = Path("uploads")

class FileService:
    def __init__(self, db: Session):
        # DB 세션 저장
        self.db = db
        self.file_repository = FileRepository(db)
        self.transaction_repository = TransactionRepository(db)
        self.admin_repository = AdminRepository(db)
        self.vision_service = VisionService()
    # ===============================
    # 1. 파일 저장
    # 역할:
    # 사용자가 업로드한 엑셀 파일을
    # 서버 uploads 폴더에 저장
    # return:
    # 저장된 파일 경로
    # ===============================
    def save_file(
        self,
        file: UploadFile
    ):
        filename = f"{uuid.uuid4()}_{file.filename}"
        # 저장 폴더 생성(없으면)
        UPLOAD_DIR.mkdir(
            exist_ok=True
        )
        # 저장경로 생성
        file_path = UPLOAD_DIR / filename
        # 파일 저장
        with file_path.open("wb") as buffer:
            buffer.write(
                file.file.read()
            )
        file.file.seek(0)
        return file_path
    
    # =====================================
    # 업로드 처리 상태
    # 1. 명세서 저장
    # 2. 거래 저장
    # 3. 상태 변경
    # =====================================
    def upload_process(
        self,
        user_id:int,
        file_name:str,
        file_url:str,
        file_type:str,
        card_name:str,
        transactions:list
    ):
        try:
            # 1. 명세서 저장
            statement = self.save_statement(
                user_id,
                file_name,
                file_url,
                file_type,
                card_name
            )

            # INSERT를 DB에 먼저 반영해서 statement.id 생성
            self.db.flush()

            # 2. 거래 저장
            self.save_transactions(
                user_id,
                statement.id,
                transactions
            )

            # 3. 성공 상태 변경
            statement.status = "COMPLETED"
            statement.processed_at = datetime.now()

            # 마지막에 한 번만 commit
            self.db.commit()
            return statement

        except Exception as e:
            # 실패하면 둘 다 취소
            self.db.rollback()
            raise e
    
    # =====================================
    # 2. 카드 명세서 저장
    # card_statements 테이블 저장
    # 업로드 파일 정보 저장
    # =====================================
    def save_statement(
        self,
        user_id:int,
        file_name:str,
        file_url:str,
        file_type:str,
        card_name:str
    ):
        statement = CardStatement(
            user_id=user_id,
            file_name=file_name,
            file_url=file_url,
            file_type=file_type.upper(),
            status="PROCESSING",
            card_name=card_name
        )

        return self.file_repository.save(statement)

    # ======================================
    # 3. Vision 거래내역 추출
    # 거래일
    # 가맹점명
    # 금액 ...
    # ↓
    # DB 저장용 dictionary 변환
    # ======================================
    def parse_card_statement(
        self,
        file_path: str,
        user_id: int,
    ):
        result = self.vision_service.extract_transactions(file_path=file_path,
    db=self.db,
    user_id=user_id,)

        transactions = result["transactions"]
        response = result["response"]

        usage = response.usage

        prompt_tokens = getattr(usage, "input_tokens", 0)
        completion_tokens = getattr(usage, "output_tokens", 0)

        from decimal import Decimal

        estimated_cost = (
            (Decimal(prompt_tokens) / Decimal("1000000")) * Decimal("2.50")
            + (Decimal(completion_tokens) / Decimal("1000000")) * Decimal("10.00")
        )

        self.admin_repository.create_token_usage_log(
            user_id=user_id,
            feature_type="ocr",
            model_name=response.model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            embedding_tokens=0,
            estimated_cost=estimated_cost,
        )

        return transactions
    # ===============================
    # 4. 거래내역 DB 저장
    # transactions 테이블 INSERT
    # 파일 업로드 거래는 statement_id를 가지고 있음
    # ===============================
    def save_transactions(
    self,
    user_id:int,
    statement_id:int,
    transactions:list
    ):
        for data in transactions:
            transaction = Transaction(
                user_id=user_id,
                statement_id=statement_id,
                **data
            )

            self.transaction_repository.save(transaction)
    
    # ======================================
    # 업로드 파일 목록 조회
    # ======================================
    def get_file_list(
        self,
        user_id:int
    ):
        return self.file_repository.find_all_by_user(user_id)

    # ======================================
    # 파일 상세 조회
    # 파일 정보 반환
    # 거래내역은 transaction_router에서 조회
    # ======================================
    def get_file_detail(
        self,
        statement_id: int,
        user_id: int,
    ):
        statement = self.file_repository.find_by_id(
            statement_id,
            user_id,
        )

        if not statement:
            raise HTTPException(
                status_code=404,
                detail="파일이 존재하지 않습니다."
            )

        transactions = self.transaction_repository.find_by_statement_id(
            statement_id
        )

        return {
            "statement": statement,
            "transactions": transactions,
        }

    # ======================================
    # 파일 삭제
    # 삭제:
    # 1. 실제 파일
    # 2. transactions
    # 3. card_statements
    # ======================================
    def delete_file(
        self,
        statement_id: int,
        user_id: int
    ):
        statement = self.file_repository.find_by_id(
            statement_id,
            user_id
        )

        if not statement:
            raise HTTPException(
                status_code=404,
                detail="파일이 존재하지 않습니다."
            )

        try:
            # 실제 파일 삭제
            if os.path.exists(statement.file_url):
                os.remove(statement.file_url)

            # 거래내역 삭제
            self.transaction_repository.delete_by_statement_id(
                statement.id
            )

            # 명세서 삭제
            self.file_repository.delete(
                statement
            )

            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

    # ======================================
    # 처리 상태 조회
    # ======================================
    def get_file_status(
        self,
        statement_id:int,
        user_id:int
    ):
        statement = self.file_repository.find_by_id(statement_id, user_id)
        if not statement:
            raise HTTPException(
            status_code=404,
            detail="파일이 존재하지 않습니다."
        )
        return {
        "statement_id":statement.id,
        "status":statement.status,
        "error_message":statement.error_message
    }
    # 거래내역 보여주는 함수
    def find_by_statement_id(
        self,
        statement_id: int,
    ):
        return (
            self.db.query(Transaction)
            .filter(
                Transaction.statement_id == statement_id
            )
            .all()
        )