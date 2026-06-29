from pydantic import BaseModel


class DepositProductResponse(BaseModel):
    id: int
    bank_name: str
    product_name: str
    interest_rate: float
    max_rate: float | None
    join_period: int

    class Config:
        from_attributes = True