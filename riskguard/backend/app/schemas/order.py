from pydantic import BaseModel, Field
from typing import Optional, Literal


class OrderIn(BaseModel):
    order_id: Optional[str] = Field(default=None, description="Merchant order reference; auto-generated if omitted")
    category: Literal["fashion", "electronics", "home", "beauty", "grocery", "other"]
    payment_method: Literal["cod", "prepaid_card", "upi", "wallet"]
    order_value: float = Field(..., gt=0, description="Order value in INR")
    discount_pct: float = Field(0, ge=0, le=100)
    customer_tenure_days: int = Field(0, ge=0)
    customer_past_orders: int = Field(0, ge=0)
    customer_past_returns: int = Field(0, ge=0)
    seller_rating: float = Field(4.5, ge=1, le=5)
    delivery_days: float = Field(3, ge=0)
    promised_delivery_days: float = Field(3, ge=0)
    is_weekend_purchase: int = Field(0, ge=0, le=1)
    hour_of_day: int = Field(12, ge=0, le=23)
    distance_km: float = Field(50, ge=0)

    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "ORD90210",
                "category": "fashion",
                "payment_method": "cod",
                "order_value": 2400,
                "discount_pct": 55,
                "customer_tenure_days": 5,
                "customer_past_orders": 1,
                "customer_past_returns": 1,
                "seller_rating": 3.6,
                "delivery_days": 6,
                "promised_delivery_days": 3,
                "is_weekend_purchase": 1,
                "hour_of_day": 23,
                "distance_km": 340,
            }
        }


class ReasonCode(BaseModel):
    code: str
    message: str
    weight: float


class OrderScoreOut(BaseModel):
    order_id: str
    risk_score: float
    risk_tier: Literal["low", "medium", "high"]
    reason_codes: list[ReasonCode]


class BatchScoreOut(BaseModel):
    results: list[OrderScoreOut]
    summary: dict
