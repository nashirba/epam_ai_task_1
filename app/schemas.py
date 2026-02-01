from __future__ import annotations

from datetime import date, datetime
from typing import Literal, Optional, List

from pydantic import BaseModel, Field, ConfigDict

OrderStatus = Literal["pending", "paid", "shipped", "cancelled"]


class OrderCreate(BaseModel):
    customer_name: str = Field(min_length=1, max_length=120)
    status: OrderStatus
    amount: float = Field(ge=0)
    order_date: date


class OrderUpdate(BaseModel):
    # All optional; at least one field must be provided (enforced in endpoint).
    customer_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    status: Optional[OrderStatus] = None
    amount: Optional[float] = Field(default=None, ge=0)
    order_date: Optional[date] = None


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    customer_name: str
    status: OrderStatus
    amount: float
    order_date: date
    created_at: datetime


class OrdersPage(BaseModel):
    page: int
    limit: int
    total: int
    pages: int
    items: List[OrderOut]


class OrderFilters(BaseModel):
    status: Optional[OrderStatus] = None
    min_amount: Optional[float] = Field(default=None, ge=0)
    max_amount: Optional[float] = Field(default=None, ge=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
