from sqlalchemy.orm import Session, selectinload

from app.models.financial_product_model import (
    DepositProduct,
    SavingProduct,
    InsuranceProduct,
)


def get_deposit_products(
        db: Session,
        bank: str | None = None,
        term: int | None = None,
        sort: str | None = None,
        ):
    query = (
        db.query(DepositProduct)
        .options(selectinload(DepositProduct.rates))
    )
    
    # 은행명으로 조회
    if bank:
        query = query.filter(
            DepositProduct.bank_name == bank
        )

    products = query.all()

    # 가입기간으로 조회
    if term:
        result = []

        for product in products:
            product.rates = [
                rate for rate in product.rates
                if rate.term_months == term
            ]

            if product.rates:
                result.append(product)

        products = result
    
    if sort == "max_rate":
        products.sort(
            key=lambda product: max(rate.max_rate for rate in product.rates),
            reverse=True
        )
    elif sort == "base_rate":
        products.sort(
            key=lambda product: max(rate.base_rate for rate in product.rates),
            reverse=True
        )
    
    return products


def get_saving_products(
        db: Session,
        bank: str | None = None,
        term: int | None = None,
        sort: str | None = None,
        ):
    
    query = (
        db.query(SavingProduct)
        .options(selectinload(SavingProduct.rates))
    )
    
    # 은행명으로 조회
    if bank:
        query = query.filter(
            SavingProduct.bank_name == bank
        )

    products = query.all()

    # 가입기간으로 조회
    if term:
        result = []

        for product in products:
            product.rates = [
                rate for rate in product.rates
                if rate.term_months == term
            ]

            if product.rates:
                result.append(product)

        products = result
    
    if sort == "max_rate":
        products.sort(
            key=lambda product: max(rate.max_rate for rate in product.rates),
            reverse=True
        )
    elif sort == "base_rate":
        products.sort(
            key=lambda product: max(rate.base_rate for rate in product.rates),
            reverse=True
        )
    
    return products


# 동기화용
def get_insurance_products(
    db: Session,
    insurance_type: str | None = None,
    company_code: str | None = None
):
    query = db.query(InsuranceProduct)

    if insurance_type:
        query = query.filter(
            InsuranceProduct.insurance_type.contains(
                insurance_type
            )
        )

    if company_code:
        query = query.filter(
            InsuranceProduct.company_code == company_code
        )

    return query.all()