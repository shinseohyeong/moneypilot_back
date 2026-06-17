from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def user_test():
    return {"message": "user router connected"}