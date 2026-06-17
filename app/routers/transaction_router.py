from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def transaction_test():
    return {"message": "transaction router connected"}