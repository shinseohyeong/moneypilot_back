from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def admin_test():
    return {"message": "admin router connected"}