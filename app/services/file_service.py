# ==========================================
# 파일 위치 : moneypilot_back/app/services/file_service.py
# 역할 : 파일 업로드, 저장, 처리 로직을 담당하는 서비스 계층
#        파일 관련 비즈니스 로직을 API 라우터와 분리하여 관리
# ==========================================

from sqlalchemy.orm import Session
from fastapi import UploadFile
from pathlib import Path
import shutil

UPLOAD_DIR = Path("uploads")

class FileService:
    def __init__(self, db : Session):
        self.db = db
    
    def save_file(self, user_id: int, file):
        # 파일 저장 로직 구현
        # 1. 저장 폴더 없으면 생성
        UPLOAD_DIR.mkdir(
        exist_ok=True
    )

        # 2. 저장할 파일 경로 생성
        file_path = UPLOAD_DIR / file.filename

        # 3. 실제 파일 저장
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(
                file.file,
                buffer
            )

        # 4. 저장 경로 반환
        return str(file_path)
    
    def read_excel():
        # 엑셀 파일 읽기 로직 구현
        pass
    
    def parse_transactions():
        # 거래 내역 파싱 로직 구현
        pass
    
    def save_transactions():
        # 파싱된 거래 내역 DB 저장 로직 구현
        pass