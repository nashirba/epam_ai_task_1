from __future__ import annotations

import random
from datetime import date, timedelta

from sqlalchemy.orm import Session

from .db import SessionLocal, init_db
from .models import Order

STATUSES = ["pending", "paid", "shipped", "cancelled"]
FIRST_NAMES = ["Ada", "Grace", "Alan", "Linus", "Margaret", "Katherine", "Tim", "Guido", "Donald", "Edsger"]
LAST_NAMES = ["Lovelace", "Hopper", "Turing", "Torvalds", "Hamilton", "Johnson", "Berners-Lee", "van Rossum", "Knuth", "Dijkstra"]


def seed_orders(db: Session, n: int = 50) -> int:
    # Avoid reseeding endlessly: if table already has rows, do nothing.
    existing = db.query(Order).count()
    if existing > 0:
        return 0

    today = date.today()
    orders = []
    for _ in range(n):
        customer = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        status = random.choice(STATUSES)
        amount = round(random.uniform(5, 2000), 2)
        order_date = today - timedelta(days=random.randint(0, 120))
        orders.append(
            Order(
                customer_name=customer,
                status=status,
                amount=amount,
                order_date=order_date,
            )
        )

    db.add_all(orders)
    db.commit()
    return n


def main():
    init_db()
    db = SessionLocal()
    try:
        inserted = seed_orders(db, 50)
        if inserted:
            print(f"Seeded {inserted} orders.")
        else:
            print("Orders already exist; skipping seed.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
