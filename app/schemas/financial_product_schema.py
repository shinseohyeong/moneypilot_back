from pydantic import BaseModel


class DepositRateResponse(BaseModel):
    term_months: int
    base_rate: float
    max_rate: float | None
    rate_type: str | None

    class Config:
        from_attributes = True


class DepositProductResponse(BaseModel):
    id: int
    bank_name: str
    product_name: str
    
    rates: list[DepositRateResponse]

    class Config:
        from_attributes = True


class DepositRecommendResponse(BaseModel):
    id:int
    bank_name: str
    product_name: str
    max_rate: float
    principal: int
    expected_interest: int
    maturity_amount: int


class SavingRateResponse(BaseModel):
    term_months: int
    base_rate: float
    max_rate: float | None
    rate_type: str | None

    class Config:
        from_attributes = True


class SavingProductResponse(BaseModel):
    id:int
    bank_name: str
    product_name: str

    rates: list[SavingRateResponse]

    class Config:
        from_attributes = True


class SavingRecommendResponse(BaseModel):
    id:int
    bank_name: str
    product_name: str
    max_rate: float
    principal: int
    expected_interest: int
    maturity_amount: int