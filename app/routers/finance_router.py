from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def finance_test():
    return {"message": "finance router connected"}