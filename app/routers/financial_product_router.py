from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.financial_product_service import get_deposit_products, get_saving_products, get_insurance_products

router = APIRouter(prefix="/financial_products", tags=["Financial Products"])

@router.get("/deposits")
def read_deposit_products(db: Session = Depends(get_db)):
    return get_deposit_products(db)

@router.get("/savings")
def read_saving_products(db: Session = Depends(get_db)):
    return get_saving_products(db)

@router.get("/insuances")
def read_insurance_products(db: Session = Depends(get_db)):
    return get_insurance_products(db)