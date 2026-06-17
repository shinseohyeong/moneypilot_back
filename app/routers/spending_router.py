from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def spending_test():
    return {"message": "spending router connected"}