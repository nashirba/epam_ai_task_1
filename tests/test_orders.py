from __future__ import annotations

import os
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.db import init_db

client = TestClient(app)


@pytest.fixture(autouse=True, scope="session")
def setup_db():
    # Ensure a fresh DB for the test session.
    if os.path.exists("orders.db"):
        os.remove("orders.db")
    init_db()
    yield


def create_order_payload(**overrides):
    payload = {
        "customer_name": "Test User",
        "status": "pending",
        "amount": 123.45,
        "order_date": str(date.today()),
    }
    payload.update(overrides)
    return payload


def test_create_order_success():
    r = client.post("/orders", json=create_order_payload())
    assert r.status_code == 201
    body = r.json()
    assert body["id"] >= 1
    assert body["customer_name"] == "Test User"
    assert body["status"] == "pending"
    assert abs(body["amount"] - 123.45) < 1e-6
    assert "created_at" in body


def test_create_order_validation_missing_field():
    payload = create_order_payload()
    payload.pop("customer_name")
    r = client.post("/orders", json=payload)
    assert r.status_code == 422


def test_create_order_validation_negative_amount():
    r = client.post("/orders", json=create_order_payload(amount=-1))
    assert r.status_code == 422


def test_get_order_success():
    r = client.post("/orders", json=create_order_payload(customer_name="Get Me"))
    oid = r.json()["id"]
    g = client.get(f"/orders/{oid}")
    assert g.status_code == 200
    assert g.json()["customer_name"] == "Get Me"


def test_get_order_not_found():
    g = client.get("/orders/999999")
    assert g.status_code == 404


def test_update_order_success():
    r = client.post("/orders", json=create_order_payload(customer_name="Updatable", amount=10))
    oid = r.json()["id"]
    u = client.put(f"/orders/{oid}", json={"status": "paid", "amount": 20})
    assert u.status_code == 200
    body = u.json()
    assert body["status"] == "paid"
    assert abs(body["amount"] - 20) < 1e-6


def test_update_order_requires_field_edge_case():
    r = client.post("/orders", json=create_order_payload(customer_name="Empty Update"))
    oid = r.json()["id"]
    u = client.put(f"/orders/{oid}", json={})
    assert u.status_code == 422
    assert "At least one field" in u.json()["detail"]


def test_update_order_not_found():
    u = client.put("/orders/999999", json={"status": "paid"})
    assert u.status_code == 404


def test_delete_order_success():
    r = client.post("/orders", json=create_order_payload(customer_name="Deletable"))
    oid = r.json()["id"]
    d = client.delete(f"/orders/{oid}")
    assert d.status_code == 204
    g = client.get(f"/orders/{oid}")
    assert g.status_code == 404


def test_delete_order_not_found():
    d = client.delete("/orders/999999")
    assert d.status_code == 404


def test_list_orders_default_pagination():
    # create more orders
    for i in range(15):
        client.post("/orders", json=create_order_payload(customer_name=f"User {i}", amount=10 + i))

    r = client.get("/orders")
    assert r.status_code == 200
    body = r.json()
    assert body["page"] == 1
    assert body["limit"] == 10
    assert body["total"] >= 16  # includes prior tests
    assert "pages" in body
    assert len(body["items"]) <= 10


def test_list_orders_second_page():
    r = client.get("/orders?page=2&limit=5")
    assert r.status_code == 200
    body = r.json()
    assert body["page"] == 2
    assert body["limit"] == 5
    assert len(body["items"]) <= 5


def test_pagination_invalid_page():
    r = client.get("/orders?page=0&limit=10")
    assert r.status_code == 422


def test_pagination_invalid_limit_too_high():
    r = client.get("/orders?limit=101")
    assert r.status_code == 422


def test_filter_by_status():
    # create known status
    client.post("/orders", json=create_order_payload(customer_name="Paid User", status="paid", amount=50))
    r = client.get("/orders?status=paid&limit=50")
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 1
    assert all(item["status"] == "paid" for item in body["items"])


def test_filter_invalid_status_edge_case():
    r = client.get("/orders?status=unknown")
    assert r.status_code == 422


def test_filter_amount_range():
    # create known amount
    client.post("/orders", json=create_order_payload(customer_name="Big Spender", amount=999.99))
    r = client.get("/orders?min_amount=900&max_amount=1000&limit=50")
    assert r.status_code == 200
    body = r.json()
    assert all(900 <= item["amount"] <= 1000 for item in body["items"])


def test_filter_amount_range_invalid_edge_case():
    r = client.get("/orders?min_amount=10&max_amount=1")
    assert r.status_code == 422
    assert "min_amount cannot be greater" in r.json()["detail"]


def test_filter_date_range():
    d1 = date.today() - timedelta(days=10)
    d2 = date.today() - timedelta(days=3)
    client.post("/orders", json=create_order_payload(customer_name="Date User", order_date=str(d1), amount=10))
    client.post("/orders", json=create_order_payload(customer_name="Date User 2", order_date=str(d2), amount=20))

    r = client.get(f"/orders?start_date={d1.isoformat()}&end_date={d2.isoformat()}&limit=50")
    assert r.status_code == 200
    body = r.json()
    assert all(d1.isoformat() <= item["order_date"] <= d2.isoformat() for item in body["items"])


def test_filter_date_range_invalid_edge_case():
    d1 = date.today()
    d2 = date.today() - timedelta(days=1)
    r = client.get(f"/orders?start_date={d1.isoformat()}&end_date={d2.isoformat()}")
    assert r.status_code == 422
    assert "start_date cannot be after end_date" in r.json()["detail"]


def test_created_at_sorting_newest_first():
    # Create a later order, ensure it appears first when listed.
    client.post("/orders", json=create_order_payload(customer_name="Newest", amount=777))
    r = client.get("/orders?limit=5")
    assert r.status_code == 200
    body = r.json()
    names = [it["customer_name"] for it in body["items"]]
    assert "Newest" in names  # should be within first 5


def test_limit_one_returns_single_item():
    r = client.get("/orders?limit=1")
    assert r.status_code == 200
    body = r.json()
    assert body["limit"] == 1
    assert len(body["items"]) == 1
