from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.financial_product_service import get_deposit_products

router = APIRouter(prefix="/financial_products", tags=["Financial Products"])

@router.get("/deposits")
def read_deposit_products(db: Session = Depends(get_db)):
    return get_deposit_products(db)