from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.financial_product_service import get_deposit_products, get_saving_products, sync_deposit_products, sync_saving_products, get_insurance_products
from app.clients.financial_product_client import fetch_deposit_products
from app.schemas.financial_product_schema import DepositProductResponse, SavingProductResponse

router = APIRouter(tags=["Financial Products"])

# 예금조회
@router.get(
        "/deposits",
        response_model=list[DepositProductResponse],)
def get_deposits(db: Session = Depends(get_db)):
    return get_deposit_products(db)

# 적금조회
@router.get(
        "/savings",
        response_model=list[SavingProductResponse],)
def get_savings(db: Session = Depends(get_db)):
    return get_saving_products(db)

# 예금 동기화
@router.post("/deposits/sync")
def sync_deposits(db: Session = Depends(get_db)):
    return sync_deposit_products(db)

# 적금 동기화
@router.post("/savings/sync")
def sync_savings(db: Session = Depends(get_db)):
    return sync_saving_products(db)

# 보험조회
@router.get("/insuances")
def read_insurance_products(db: Session = Depends(get_db)):
    return get_insurance_products(db)