from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Query, status
from sqlalchemy.orm import Session

from .db import SessionLocal, init_db
from .crud import (
    create_order,
    list_orders,
    get_order,
    update_order,
    delete_order,
)
from .schemas import (
    OrderCreate,
    OrderUpdate,
    OrderOut,
    OrdersPage,
    OrderFilters,
)

app = FastAPI(title="Orders Management API", version="1.1.0")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
def on_startup():
    init_db()


@app.post("/orders", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order_endpoint(payload: OrderCreate, db: Session = Depends(get_db)):
    return create_order(db, payload)


@app.get("/orders/{order_id}", response_model=OrderOut)
def get_order_endpoint(order_id: int, db: Session = Depends(get_db)):
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.put("/orders/{order_id}", response_model=OrderOut)
def update_order_endpoint(order_id: int, payload: OrderUpdate, db: Session = Depends(get_db)):
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Enforce at least one field in request body.
    if not payload.model_dump(exclude_unset=True):
        raise HTTPException(status_code=422, detail="At least one field must be provided")

    return update_order(db, order, payload)


@app.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order_endpoint(order_id: int, db: Session = Depends(get_db)):
    order = get_order(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    delete_order(db, order)
    return None


@app.get("/orders", response_model=OrdersPage)
def list_orders_endpoint(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(10, ge=1, le=100, description="Page size (max 100)"),
    status: str | None = Query(None, description="Filter by status"),
    min_amount: float | None = Query(None, ge=0, description="Minimum order amount"),
    max_amount: float | None = Query(None, ge=0, description="Maximum order amount"),
    start_date: str | None = Query(None, description="Filter start date (YYYY-MM-DD)"),
    end_date: str | None = Query(None, description="Filter end date (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """List orders with pagination and server-side filtering.

    Pagination: page (default 1, min 1) and limit (default 10, min 1, max 100).
    Offset is calculated as (page - 1) * limit. Pages beyond total return empty items.

    Filters (all optional): status (pending|paid|shipped|cancelled), min_amount,
    max_amount, start_date (YYYY-MM-DD), end_date (YYYY-MM-DD). Filters can be
    combined. Validates min_amount <= max_amount and start_date <= end_date.
    """
    # Pydantic validates status/amount/date formats via OrderFilters.
    try:
        filters = OrderFilters(
            status=status,
            min_amount=min_amount,
            max_amount=max_amount,
            start_date=start_date,
            end_date=end_date,
        )
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    if filters.min_amount is not None and filters.max_amount is not None:
        if filters.min_amount > filters.max_amount:
            raise HTTPException(status_code=422, detail="min_amount cannot be greater than max_amount")

    if filters.start_date is not None and filters.end_date is not None:
        if filters.start_date > filters.end_date:
            raise HTTPException(status_code=422, detail="start_date cannot be after end_date")

    return list_orders(db, page=page, limit=limit, filters=filters)
