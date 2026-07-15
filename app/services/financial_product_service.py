from sqlalchemy.orm import Session, selectinload
from app.models.financial_product_model import DepositProduct, DepositProductRate, SavingProduct, SavingProductRate, InsuranceProduct
from app.clients.financial_product_client import fetch_deposit_products, fetch_saving_products, fetch_insurance_products
from app.repositories.financial_product_repository import (
    get_deposit_products, get_saving_products, get_insurance_products
)


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

def sync_insurance_products(db: Session):
    data = fetch_insurance_products()   # API 호출

    insurance_list = (
        db.query(InsuranceProduct)
        .filter(
            InsuranceProduct.company_code == product.get("cmpyCd"),
            InsuranceProduct.insurance_name == product.get("prdNm"),
        )
        .first()
    )

    for product in insurance_list:

        if not product.get("cmpyCd") or not product.get("prdNm"):
            continue

        insurance_product = get_insurance_products(
            db,
            product.get("cmpyCd"),
            product.get("prdNm")
        )

        # 없으면 추가
        if insurance_product is None:
            insurance_product = InsuranceProduct(
                company_code=product.get("cmpyCd"),
                company_name=product.get("cmpyNm"),
                insurance_name=product.get("prdNm"),
                insurance_type=product.get("ptrn"),
                description=product.get("mog"),
                age=product.get("age"),
                male_insurance_rate=product.get("mlInsRt"),
                female_insurance_rate=product.get("fmlInsRt"),
            )

            db.add(insurance_product)

        # 있으면 수정
        else:
            insurance_product.company_name = product.get("cmpyNm")
            insurance_product.insurance_name = product.get("prdNm")
            insurance_product.insurance_type = product.get("ptrn")
            insurance_product.description = product.get("mog")
            insurance_product.age = product.get("age")
            insurance_product.male_insurance_rate = product.get("mlInsRt")
            insurance_product.female_insurance_rate = product.get("fmlInsRt")


    db.commit() # 저장

    return {
        "message": "보험 상품이 성공적으로 동기화되었습니다."
    }


def recommend_deposit_products(
    db: Session,
    term: int,
    deposit_amount: int,
    limit: int = 5,
    preferred_bank: str | None = None
):
    
    products = get_deposit_products(
        db=db,
        bank=preferred_bank,
        term=term,
    )

    recommend_list = []

    # 원하는 가입기간만 선택
    for product in products:
        rates = [
            rate for rate in product.rates
            if rate.term_months == term
        ]

        if not rates:
            continue

        max_rate = float(max(rate.max_rate for rate in rates))

        # 추천 점수 계산
        score = max_rate

        # 선호은행 가산점
        if preferred_bank and product.bank_name == preferred_bank:
            score += 0.1

        # 일반 과세(이자소득세 15.4%)
        principal = deposit_amount

        before_tax_interest = (
            principal
            * (max_rate / 100)
            * (term / 12)
        )
        
        after_tax_interest = before_tax_interest * 0.846

        maturity_amount = principal + after_tax_interest

        recommend_list.append({
            "id": product.id,
            "bank_name": product.bank_name,
            "product": product,
            "product_name": product.product_name,
            "score": score,
            "max_rate": max_rate,
            "principal": principal,
            "before_tax_interest": int(before_tax_interest),
            "after_tax_interest": int(after_tax_interest),
            "maturity_amount": int(maturity_amount),
        })

    # 점수 순 정렬
    recommend_list.sort(
        key=lambda x: x["score"],
        reverse=True,
    )

    result = []

    for item in recommend_list[:limit]:
        product = item["product"]

        result.append({
            "id": product.id,
            "bank_name": product.bank_name,
            "product_name": product.product_name,
            "max_rate": item["max_rate"],
            "principal": item["principal"],
            "before_tax_interest": item["before_tax_interest"],
            "after_tax_interest": item["after_tax_interest"],
            "maturity_amount": item["maturity_amount"],
        })
    return result


def recommend_saving_products(
    db: Session,
    term: int,
    monthly_amount: int,    # 매월 저축 금액
    limit: int = 5,
    preferred_bank: str | None = None
):
    products = get_saving_products(
        db=db,
        bank=preferred_bank,
        term=term,
    )

    recommend_list = []

    # 원하는 가입기간만 선택
    for product in products:
        rates = [
            rate for rate in product.rates
            if rate.term_months == term
        ]

        if not rates:
            continue

        max_rate = float(max(rate.max_rate for rate in rates))

        # 추천 점수 계산
        score = max_rate

        # 선호은행 가산점
        if preferred_bank and product.bank_name == preferred_bank:
            score += 0.1

        principal = monthly_amount * term

        before_tax_interest = (
            monthly_amount
            * (max_rate / 100)
            * (term + 1)
            /24
        )

        after_tax_interest = before_tax_interest * 0.846

        maturity_amount = principal + after_tax_interest

        recommend_list.append({
            "id": product.id,
            "bank_name": product.bank_name,
            "product_name": product.product_name,
            "product": product,
            "score": score,
            "max_rate": max_rate,
            "principal": principal,
            "before_tax_interest": int(before_tax_interest),
            "after_tax_interest": int(after_tax_interest),
            "maturity_amount": int(maturity_amount),
        })

    # 점수 순 정렬
    recommend_list.sort(
        key=lambda x: x["score"],
        reverse=True,
    )

    result = []

    for item in recommend_list[:limit]:
        product = item["product"]

        result.append({
            "id": product.id,
            "bank_name": product.bank_name,
            "product_name": product.product_name,
            "max_rate": item["max_rate"],
            "principal": item["principal"],
            "before_tax_interest": item["before_tax_interest"],
            "after_tax_interest": item["after_tax_interest"],
            "maturity_amount": item["maturity_amount"],
        })
    return result


def recommend_insurance_products(
    db: Session,
    gender: str | None = None,
    insurance_type: str | None = None,
    company_name: str | None = None,
    limit: int = 5,
):
    products = get_insurance_products(
        db=db,
        company_name=company_name,
        insurance_type=insurance_type,
    )

    # 성별 기준 보험료 오름차순 정렬
    if gender == "남자":
        products.sort(
            key=lambda x: int(
                x.male_insurance_rate or 999
            )
        )

    elif gender == "여자":
        products.sort(
            key=lambda x: int(
                x.female_insurance_rate or 999
            )
        )

    # 상위 10개 추천
    return products[:limit]