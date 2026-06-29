from sqlalchemy.orm import Session
from app.models.financial_product_model import DepositProduct

def get_deposit_products(db: Session):
    return db.query(DepositProduct).all()