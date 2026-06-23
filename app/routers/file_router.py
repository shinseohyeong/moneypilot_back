# ==========================================
# 파일 위치 : moneypilot_back/app/routers/file_router.py
# 역할 : 파일 업로드, 조회, 삭제 등 파일 관련 API 엔드포인트 정의
# ==========================================
from fastapi import APIRouter, File, UploadFile

router = APIRouter(
    prefix="/api/files",
    tags=["Files"]
)

@router.get("", status_code=201, summary="파일 목록 조회", description="사용자가 업로드한 파일 목록을 조회합니다.")
def file_list():
    return {"message": "파일 목록 조회"}

@router.post("/upload", status_code=201, summary="파일 업로드", description="사용자가 파일을 업로드합니다.")
async def upload_file(file: UploadFile = File(...)):
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "message": "파일 업로드"
    }

@router.get("/{statement_id}", status_code=201, summary="파일 상세 조회", description="특정 파일의 상세 정보를 조회합니다.")
def get_file(statement_id: int):
    return {"statement_id": statement_id, 
            "message": "파일 상세 조회"}

@router.delete("/{statement_id}", status_code=201, summary="파일 삭제", description="특정 파일을 삭제합니다.")
def delete_file(statement_id: int):
    return {"deleted_id": statement_id, 
            "message": "파일 삭제"}

@router.get("/{statement_id}/status", status_code=201, summary="파일 처리 상태 조회", description="특정 파일의 처리 상태를 조회합니다.")
def get_file_status(statement_id: int):
    return {
        "statement_id": statement_id,
        "status": "PROCESSING",
        "message": "파일 처리 상태 조회"
    }