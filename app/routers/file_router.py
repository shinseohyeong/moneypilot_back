# ==========================================
# 파일 위치 :
# moneypilot_back/app/routers/file_router.py
# 역할 :
# 거래명세서 파일 업로드
# 파일 목록 조회
# 파일 상세 조회
# 파일 삭제
# 파일 처리 상태 조회 API
# ==========================================
from fastapi import (
    APIRouter,
    UploadFile,
    File,
    Depends,
    Form
)
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.file_service import FileService

router = APIRouter(
    tags=["Files"]
)

# 파일 저장 위치
UPLOAD_DIR="uploads"

# ==========================================
# 업로드 파일 목록 조회
# GET
# /api/files
# card_statements 테이블 조회
# ==========================================
@router.get(
    "",
    summary="파일 목록 조회",
    description="사용자가 업로드한 거래명세서 목록을 조회합니다."
)
def file_list(
    db:Session = Depends(get_db)
):
    service = FileService(db)
    return service.get_file_list(
        user_id=1
    )

# ==========================================
# 파일 업로드
# POST
# /api/files/upload
# 처리 과정:
# 1. 파일 저장
# 2. card_statements 저장
# 3. 엑셀 읽기
# 4. 거래내역 저장
# ==========================================
@router.post(
    "/upload",
    status_code=201,
    summary="파일 업로드",
    description="사용자가 거래명세서 파일을 업로드합니다."
)
async def upload_file(
    file:UploadFile = File(...),
    card_name:str = Form(...),
    db:Session = Depends(get_db)
):
    service = FileService(db)
    # 1. 실제 파일 저장
    file_path = service.save_file(file)
    
    # 2. 엑셀 읽기
    df = service.read_excel(file_path)
    
    # 3. 거래내역 파싱
    transactions = service.parse_transactions(df, card_name)

    # 4. 명세서 + 거래내역 한번에 저장
    statement = service.upload_process(
        user_id=1,
        file_name=file.filename,
        file_url=str(file_path),
        file_type=file.filename.split(".")[-1],
        card_name=card_name,
        transactions=transactions
    )
    return {
        "message":"파일 업로드 완료",
        "statement_id":statement.id,
        "file_name":file.filename,
        "status":statement.status
    }

# ==========================================
# 파일 상세 조회
# GET
# /api/files/{statement_id}
# ==========================================
@router.get(
    "/{statement_id}",
    summary="파일 상세 조회",
    description="특정 거래명세서 상세 정보를 조회합니다."
)
def get_file(
    statement_id:int,
    db:Session = Depends(get_db)
):
    service = FileService(db)
    result = service.get_file_detail(
        statement_id
    )
    return result

# ==========================================
# 파일 삭제
# DELETE
# /api/files/{statement_id}
# 역할 :
# 선택한 거래명세서 파일 삭제
# 삭제 대상 :
# 1. card_statements 데이터 삭제
# 2. 연결된 transactions 삭제
# 3. 실제 업로드 파일 삭제
# ==========================================
@router.delete(
    "/{statement_id}",
    summary="파일 삭제",
    description="특정 거래명세서를 삭제합니다."
)
def delete_file(
    statement_id:int,
    db:Session = Depends(get_db)
):
    service = FileService(db)
    service.delete_file(
        statement_id
    )
    return {
        "message":"파일 삭제 완료"
    }
    
# ==========================================
# 파일 처리 상태 조회
# GET
# /api/files/{statement_id}/status
# ==========================================
@router.get(
    "/{statement_id}/status",
    summary="파일 처리 상태 조회",
    description="파일 처리 상태를 조회합니다."
)
def get_file_status(
    statement_id:int,
    db:Session = Depends(get_db)
):
    service = FileService(db)
    result = service.get_file_status(
        statement_id
    )
    return result