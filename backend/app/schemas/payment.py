from datetime import datetime
from pydantic import BaseModel, ConfigDict

from app.models.enums import PaymentStatus, SubscriptionTier


class CheckoutCreateResponse(BaseModel):
    order_code: str
    payment_url: str
    amount: int

    model_config = ConfigDict(from_attributes=True)


class OrderStatusResponse(BaseModel):
    order_code: str
    status: PaymentStatus
    amount: int
    plan_type: str = "1_MONTH"
    paid_at: datetime | None = None
    tier: SubscriptionTier | None = None
    pro_expires_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

