from sqlalchemy.orm import Session

from app.models.financial_product_model import (
    DepositProduct,
    SavingProduct,
    InsuranceProduct
)

from sqlalchemy.orm import selectinload


def build_financial_documents(db: Session):

    documents = []


    # 예금
    deposits = (
    db.query(DepositProduct)
    .options(selectinload(DepositProduct.rates))
    .all()
)

    for product in deposits:

        # 최고금리 계산
        max_rate = None
        if product.rates:
            max_rate = max(rate.max_rate for rate in product.rates)

        # 가입기간 목록
        terms = sorted({rate.term_months for rate in product.rates})
        term_text = ", ".join(f"{t}개월" for t in terms)

        text = f"""
        금융상품 종류: 예금

        은행명: {product.bank_name}

        상품명: {product.product_name}

        상품코드: {product.product_code}

        가입 가능 기간: {term_text}

        최고금리: {max_rate:.2f}%""" if max_rate else f"""
        금융상품 종류: 예금

        은행명: {product.bank_name}

        상품명: {product.product_name}

        상품코드: {product.product_code}

        가입 가능 기간: {term_text}
        """

        text += """

        상품 설명:
        정기예금 상품으로 만기까지 예치하여 이자를 받을 수 있습니다.
        """

        documents.append({
            "content": text,
            "metadata": {
                "type": "deposit",
                "product_id": product.id
            }
        })


    # 적금
    savings = (
    db.query(SavingProduct)
    .options(selectinload(SavingProduct.rates))
    .all()
)

    for product in savings:

        max_rate = None
        if product.rates:
            max_rate = max(rate.max_rate for rate in product.rates)

        terms = sorted({rate.term_months for rate in product.rates})
        term_text = ", ".join(f"{t}개월" for t in terms)

        text = f"""
        금융상품 종류: 적금

        은행명: {product.bank_name}

        상품명: {product.product_name}

        상품코드: {product.product_code}

        가입 가능 기간: {term_text}
        """

        if max_rate is not None:
            text += f"\n최고금리: {max_rate:.2f}%\n"

        text += """
    상품 설명:
    매월 일정 금액을 납입하는 적립식 금융상품입니다.
    목돈 마련을 원하는 고객에게 적합합니다.
    """

        documents.append({
            "content": text,
            "metadata": {
                "type": "saving",
                "product_id": product.id
            }
        })


    # 보험
    insurances = db.query(InsuranceProduct).all()

    for product in insurances:

        text = f"""
    금융상품 종류: 보험

    보험사: {product.company_name}

    상품명: {product.insurance_name}

    보험 유형: {product.insurance_type}

    가입 가능 연령: {product.age if product.age else "정보 없음"}

    남성 보험료: {product.male_insurance_rate}

    여성 보험료: {product.female_insurance_rate}

    상품 설명:
    {product.description}
    """

        documents.append({
            "content": text,
            "metadata": {
                "type": "insurance",
                "product_id": product.id
            }
        })

    return documents
