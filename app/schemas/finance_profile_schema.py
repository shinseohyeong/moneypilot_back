from pydantic import BaseModel

class FinanceProfileCreate(BaseModel):
    age_group: str
    income_level: str
    investment_type: str
    financial_goal: str


class FinanceProfileResponse(BaseModel):
    id: int
    user_id: int
    age_group: str
    income_level: str
    investment_type: str
    financial_goal: str

    class Config:
        from_attributes = True