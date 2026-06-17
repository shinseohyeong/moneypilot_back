from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def file_test():
    return {"message": "file router connected"}