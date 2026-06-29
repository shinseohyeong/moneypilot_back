from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.finance_profile_schema import (
    FinanceProfileCreate,
    FinanceProfileResponse
)
from app.services.finance_profile_service import (
    create_finance_profile
)

router = APIRouter(
    prefix="/finance-profiles",
    tags=["Finance Profile"]
)

@router.post(
    "",
    response_model=FinanceProfileResponse
)
def create_profile(
    profile_data: FinanceProfileCreate,
    db: Session = Depends(get_db)
):
    user_id = 1  # 나중에 JWT에서 가져오기

    return create_finance_profile(
        db,
        user_id,
        profile_data
    )