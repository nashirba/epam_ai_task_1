from __future__ import annotations

from math import ceil

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .models import Order
from .schemas import OrderCreate, OrderUpdate, OrderFilters


def create_order(db: Session, payload: OrderCreate) -> Order:
    order = Order(
        customer_name=payload.customer_name,
        status=payload.status,
        amount=float(payload.amount),
        order_date=payload.order_date,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def get_order(db: Session, order_id: int) -> Order | None:
    return db.get(Order, order_id)


def update_order(db: Session, order: Order, payload: OrderUpdate) -> Order:
    # Only set fields provided by the client.
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(order, key, value)
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def delete_order(db: Session, order: Order) -> None:
    db.delete(order)
    db.commit()


def _apply_filters(stmt, filters: OrderFilters):
    # Built with SQLAlchemy expressions (no string interpolation), reducing SQLi risk.
    if filters.status:
        stmt = stmt.where(Order.status == filters.status)

    if filters.min_amount is not None:
        stmt = stmt.where(Order.amount >= float(filters.min_amount))

    if filters.max_amount is not None:
        stmt = stmt.where(Order.amount <= float(filters.max_amount))

    if filters.start_date is not None:
        stmt = stmt.where(Order.order_date >= filters.start_date)

    if filters.end_date is not None:
        stmt = stmt.where(Order.order_date <= filters.end_date)

    return stmt


def list_orders(
    db: Session,
    *,
    page: int,
    limit: int,
    filters: OrderFilters,
):
    # Base select (order newest first).
    base_stmt = select(Order).order_by(Order.created_at.desc(), Order.id.desc())
    base_stmt = _apply_filters(base_stmt, filters)

    # Total count (filters included).
    count_stmt = select(func.count()).select_from(_apply_filters(select(Order.id), filters).subquery())
    total = int(db.execute(count_stmt).scalar() or 0)

    # Pagination.
    offset = (page - 1) * limit
    paged_stmt = base_stmt.offset(offset).limit(limit)
    items = list(db.scalars(paged_stmt).all())

    pages = int(ceil(total / limit)) if total else 0

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "pages": pages,
        "items": items,
    }
