from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def news_test():
    return {"message": "news router connected"}