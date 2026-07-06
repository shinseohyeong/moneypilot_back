from sqlalchemy.orm import Session
from app.models.financial_product_model import DepositProduct, DepositProductRate, SavingProduct, SavingProductRate, InsuranceProduct
from app.clients.financial_product_client import fetch_deposit_products, fetch_saving_products

def get_deposit_products(db: Session):
    return db.query(DepositProduct).all()

def get_saving_products(db: Session):
    return db.query(SavingProduct).all()

def get_insurance_products(db: Session):
    return db.query(InsuranceProduct).all()


def sync_deposit_products(db: Session):
    data = fetch_deposit_products()   # 금융감독원 API 호출

    base_list = data["result"]["baseList"]  # 상품 목록 가져오기
    option_list = data["result"]["optionList"]

    for product in base_list:
        deposit_product = (
            db.query(DepositProduct).filter(DepositProduct.product_code == product["fin_prdt_cd"]).first()
        )   # DB 조회
        if deposit_product is None:
            deposit_product = DepositProduct(
                product_code=product["fin_prdt_cd"],
                bank_name=product["kor_co_nm"],
                product_name=product["fin_prdt_nm"],
            )   # 없을 시 저장

            db.add(deposit_product)

        else:   # 있을 시 수정
            deposit_product.bank_name = product["kor_co_nm"]
            deposit_product.product_name = product["fin_prdt_nm"]

    db.flush()

     # product_code -> product 객체
    product_map = {
        product.product_code: product
        for product in db.query(DepositProduct).all()
    }

    # 금리 저장
    for option in option_list:
        product = product_map.get(option["fin_prdt_cd"])

        if product is None:
            continue

        rate = (
            db.query(DepositProductRate)
            .filter(DepositProductRate.product_id == product.id,
                    DepositProductRate.term_months == int(option.get("save_trm") or 0),
                    )
            .first()
        )

        if rate is None:
            rate = DepositProductRate(
                product_id=product.id,
                term_months=int(option.get("save_trm") or 0),
                base_rate=float(option.get("intr_rate") or 0),
                max_rate=float(option.get("intr_rate2") or 0),
                rate_type=option.get("intr_rate_type_nm"),
            )

            db.add(rate)
        
        else:
            rate.base_rate = float(option.get("intr_rate") or 0)
            rate.max_rate = float(option.get("intr_rate2") or 0)
            rate.rate_type = option.get("intr_rate_type_nm")

    db.commit() # 저장

    return {
        "message": "예금 상품이 성공적으로 동기화되었습니다."
    }

def sync_saving_products(db: Session):
    data = fetch_saving_products()   # 금융감독원 API 호출

    base_list = data["result"]["baseList"]  # 상품 목록 가져오기
    option_list = data["result"]["optionList"]

    for product in base_list:
        saving_product = (
            db.query(SavingProduct).filter(SavingProduct.product_code == product["fin_prdt_cd"]).first()
        )   # DB 조회
        if saving_product is None:
            saving_product = SavingProduct(
                product_code=product["fin_prdt_cd"],
                bank_name=product["kor_co_nm"],
                product_name=product["fin_prdt_nm"],
            )   # 없을 시 저장

            db.add(saving_product)

        else:   # 있을 시 수정
            saving_product.bank_name = product["kor_co_nm"]
            saving_product.product_name = product["fin_prdt_nm"]

    db.flush()

    # product_code -> product 객체
    product_map = {
        product.product_code: product
        for product in db.query(SavingProduct).all()
    }

    # 금리 저장
    for option in option_list:
        product = product_map.get(option["fin_prdt_cd"])

        if product is None:
            continue

        rate = (
            db.query(SavingProductRate)
            .filter(SavingProductRate.product_id == product.id,
                    SavingProductRate.term_months == int(option["save_trm"] or 0),
                    )
            .first()
        )

        if rate is None:
            rate = SavingProductRate(
                product_id=product.id,
                term_months=int(option.get("save_trm") or 0),
                base_rate=float(option.get("intr_rate") or 0),
                max_rate=float(option.get("intr_rate2") or 0),
                rate_type=option.get("intr_rate_type_nm"),
            )

            db.add(rate)
        
        else:
            rate.base_rate = float(option.get("intr_rate") or 0)
            rate.max_rate = float(option.get("intr_rate2") or 0)
            rate.rate_type = option.get("intr_rate_type_nm")

    db.commit() # 저장

    return {
        "message": "적금 상품이 성공적으로 동기화되었습니다."
    }