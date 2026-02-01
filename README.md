# Orders Management API (Pagination + Filtering)

A small REST API for managing orders, built with **FastAPI** + **SQLite** + **SQLAlchemy**.
Includes:
- `POST /orders` to create orders
- `GET /orders` to list orders with **pagination** (`page`, `limit`) and **filtering**
  (`status`, `min_amount`, `max_amount`, `start_date`, `end_date`)
- Seed script that inserts **50 sample orders**
- Pytest suite (12–15 tests) with coverage target **80%+**

## Quickstart

### 1) Create & activate a virtualenv
```bash
python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Run database migration (auto-creates tables)
The app creates tables on startup, so you can just run the API:

```bash
uvicorn app.main:app --reload
```

### 4) Seed 50 sample orders
In another terminal:
```bash
python -m app.seed
```

### 5) Open API docs
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

---

## API

### Create an order
**POST** `/orders`

Request body:
```json
{
  "customer_name": "Ada Lovelace",
  "status": "pending",
  "amount": 199.99,
  "order_date": "2026-01-15"
}
```

Response `201`:
```json
{
  "id": 1,
  "customer_name": "Ada Lovelace",
  "status": "pending",
  "amount": 199.99,
  "order_date": "2026-01-15",
  "created_at": "2026-02-01T10:30:00.123456"
}
```

### Get an order
**GET** `/orders/{id}`

### Update an order
**PUT** `/orders/{id}`

Body (any subset):
```json
{ "status": "shipped", "amount": 49.99 }
```

### Delete an order
**DELETE** `/orders/{id}`

### List orders (pagination + filters)
**GET** `/orders?page=1&limit=10`

Optional query params:
- `page` (>=1, default: 1)
- `limit` (1..100, default: 10)
- `status` (`pending|paid|shipped|cancelled`)
- `min_amount` (>=0)
- `max_amount` (>=0)
- `start_date` (YYYY-MM-DD)
- `end_date` (YYYY-MM-DD)

Response `200`:
```json
{
  "page": 1,
  "limit": 10,
  "total": 50,
  "pages": 5,
  "items": [ ... ]
}
```

---

## Running tests + coverage
```bash
pytest -q --cov=app --cov-report=term-missing
```

---

## Notes on security
- Filtering is built with SQLAlchemy expressions (no string interpolation), so it avoids SQL injection.
- Pagination parameters are validated (page >= 1, limit capped to 100).

---

## Repo structure
```
app/
  main.py        # FastAPI app + routes
  db.py          # DB engine/session + init
  models.py      # SQLAlchemy model(s)
  schemas.py     # Pydantic schemas
  crud.py        # DB operations (create/list)
  seed.py        # Seeds 50 sample orders
tests/
  test_orders.py # 15 tests
report.md        # Copilot metrics report (template)
```
