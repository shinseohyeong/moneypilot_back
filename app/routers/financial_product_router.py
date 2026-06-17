from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def financial_product_test():
    return {"message": "financial product router connected"}