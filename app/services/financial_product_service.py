from sqlalchemy.orm import Session
from app.models.financial_product_model import DepositProduct, SavingProduct, InsuranceProduct

def get_deposit_products(db: Session):
    return db.query(DepositProduct).all()

def get_saving_products(db: Session):
    return db.query(SavingProduct).all()

def get_insurance_products(db: Session):
    return db.query(InsuranceProduct).all()