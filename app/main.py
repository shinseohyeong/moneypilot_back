from fastapi import FastAPI

from app.routers import admin_router

from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth_router
from app.routers import chatbot_router
from app.routers import file_router
from app.routers import finance_router
from app.routers import financial_product_router
from app.routers import news_router
from app.routers import spending_router
from app.routers import stock_router
from app.routers import transaction_router
from app.routers import user_router


app = FastAPI(
    title="MoneyPilot API",
    description="MoneyPilot FastAPI Backend",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "MoneyPilot API server is running"}


app.include_router(admin_router.router, prefix="/api/admin", tags=["Admin"])
app.include_router(auth_router.router, prefix="/api/auth", tags=["Auth"])
app.include_router(chatbot_router.router, prefix="/api/chatbot", tags=["Chatbot"])
app.include_router(file_router.router, prefix="/api/files", tags=["Files"])
app.include_router(finance_router.router, prefix="/api/finance", tags=["Finance"])
app.include_router(financial_product_router.router, prefix="/api/financial-products", tags=["Financial Products"])
app.include_router(news_router.router, prefix="/api/news", tags=["News"])
app.include_router(spending_router.router, prefix="/api/spending", tags=["Spending"])
app.include_router(stock_router.router)
app.include_router(transaction_router.router, prefix="/api/transactions", tags=["Transactions"])
app.include_router(user_router.router, prefix="/api/users",  tags=["Users"])