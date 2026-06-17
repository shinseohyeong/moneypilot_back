from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def stock_test():
    return {"message": "stock router connected"}