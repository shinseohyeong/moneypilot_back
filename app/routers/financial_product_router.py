from fastapi import APIRouter,Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.financial_product_service import get_deposit_products, get_saving_products, sync_deposit_products, sync_saving_products, get_insurance_products, sync_insurance_products, recommend_deposit_products, recommend_saving_products, recommend_insurance_products
from app.clients.financial_product_client import fetch_deposit_products
from app.schemas.financial_product_schema import DepositProductResponse, SavingProductResponse, DepositRecommendResponse, SavingRecommendResponse, InsuranceProductResponse, InsuranceRecommendResponse, DepositRecommendRequest

router = APIRouter(tags=["Financial Products"])

# 예금조회
@router.get(
        "/deposits",
        response_model=list[DepositProductResponse],)
def get_deposits(
    db: Session = Depends(get_db),
    bank: str | None = None,
    term: int | None = None,
    sort: str | None = None
    ):
    return get_deposit_products(
        db=db,
        bank=bank,
        term=term,
        sort=sort
        )

# 적금조회
@router.get(
        "/savings",
        response_model=list[SavingProductResponse],)
def get_savings(db: Session = Depends(get_db)):
    return get_saving_products(db)

# 보험조회
@router.get(
        "/insuances",
        response_model=list[InsuranceProductResponse]
)
def read_insurances(
    insurance_type: str | None = None,
    company_code: str | None = None,
    db: Session = Depends(get_db)
):
    return get_insurance_products(
        db,
        insurance_type,
        company_code
    )

# 예금 동기화
@router.post("/deposits/sync")
def sync_deposits(db: Session = Depends(get_db)):
    return sync_deposit_products(db)

# 적금 동기화
@router.post("/savings/sync")
def sync_savings(db: Session = Depends(get_db)):
    return sync_saving_products(db)

# 보험 동기화
@router.post("/insurances/sync")
def sync_insurances(db: Session = Depends(get_db)):
    return sync_insurance_products(db)


@router.post(
    "/deposits/recommend",
    response_model=list[DepositRecommendResponse],
)
def recommend_deposits(
    request: DepositRecommendRequest,
    db: Session = Depends(get_db),
):
    return recommend_deposit_products(
        db=db,
        deposit_amount=request.deposit_amount,
        term=request.term,
        preferred_bank=request.preferred_bank,
    )

@router.post(
        "/savings/recommend",
        response_model=list[SavingRecommendResponse],
        )
def recommend_savings_products(
    term: int,
    monthly_amount: int,
    db: Session = Depends(get_db),
    preferred_bank: str | None = None,
    limit: int = 5,
):
    return recommend_saving_products(
        db=db,
        term=term,
        monthly_amount=monthly_amount,
        limit=limit,
        preferred_bank=preferred_bank,
    )

@router.post(
    "/insurances/recommend",
    response_model=list[InsuranceRecommendResponse]
)
def recommend_insurances(
    gender: str,
    insurance_type: str | None = None,
    company_name: str | None = None,
    limit: int = 5,
    db: Session = Depends(get_db),
):
    return recommend_insurance_products(
        db=db,
        gender=gender,
        insurance_type=insurance_type,
        company_name=company_name,
        limit=limit,
    )