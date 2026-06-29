from sqlalchemy.orm import Session
from app.models.user_model import FinanceProfile
from app.schemas.finance_profile_schema import FinanceProfileCreate


def create_finance_profile(
    db: Session,
    user_id: int,
    profile_data: FinanceProfileCreate
):
    profile = FinanceProfile(
        user_id=user_id,
        age_group=profile_data.age_group,
        income_level=profile_data.income_level,
        investment_type=profile_data.investment_type,
        financial_goal=profile_data.financial_goal
    )

    db.add(profile)
    db.commit()
    db.refresh(profile)

    return profile