# ==========================================
# 파일 위치 : app/repositories/card_statement_repository.py
# 역할 : card_statements 테이블 DB 접근 담당
# 담당:
# 1. 명세서 저장
# 2. 파일 목록 조회
# 3. 파일 상세 조회
# 4. 파일 조회
# 5. 파일 삭제
#
# Service에서 비즈니스 로직을 처리하고
# Repository는 DB CRUD만 담당
# ==========================================
from sqlalchemy.orm import Session

from app.models.card_statement_model import CardStatement
class FileRepository:
    def __init__(
        self,
        db:Session
    ):
        # DB 세션 저장
        self.db = db

    # ======================================
    # 명세서 저장
    # INSERT card_statements
    # ======================================
    def save(
        self,
        statement:CardStatement
    ):
        self.db.add(statement)
        self.db.commit()
        self.db.refresh(statement)
        return statement

    # ======================================
    # 파일 목록 조회
    # SELECT *
    # FROM card_statements
    # user 기준 조회
    # ======================================
    def find_all_by_user(
        self,
        user_id:int
    ):
        return (
            self.db.query(CardStatement).filter(
                CardStatement.user_id == user_id
            ).order_by(
                CardStatement.uploaded_at.desc()
            ).all()
        )

    # ======================================
    # 파일 상세 조회
    # SELECT *
    # ======================================
    def find_by_id(
        self,
        statement_id:int
    ):
        return (
            self.db.query(CardStatement).filter(
                CardStatement.id == statement_id
            ).first()
        )

    # ======================================
    # 파일 삭제
    # DELETE
    # ======================================
    def delete(
        self,
        statement:CardStatement
    ):
        self.db.delete(statement)
        self.db.commit()