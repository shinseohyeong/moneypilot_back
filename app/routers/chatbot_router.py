from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def chatbot_test():
    return {"message": "chatbot router connected"}