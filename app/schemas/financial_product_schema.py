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
    maturity_amount: int
    before_tax_interest: int
    after_tax_interest: int


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
    maturity_amount: int
    before_tax_interest: int
    after_tax_interest: int


class InsuranceProductResponse(BaseModel):
    id: int
    company_code: str
    company_name: str
    insurance_name: str
    insurance_type: str | None
    description: str | None
    age: str | None
    male_insurance_rate: str | None
    female_insurance_rate: str | None

    class Config:
        from_attributes = True


class InsuranceRecommendResponse(BaseModel):
    id: int
    company_name: str
    insurance_name: str
    insurance_type: str | None
    male_insurance_rate: str | None
    female_insurance_rate: str | None

    class Config:
        from_attributes = True


class DepositRecommendRequest(BaseModel):
    deposit_amount: int
    term: int
    preferred_bank: str | None = None