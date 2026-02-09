# Orders Management API (Pagination + Filtering)

A small REST API for managing orders, built with **FastAPI** + **SQLite** + **SQLAlchemy**.
Includes:
- `POST /orders` to create orders
- `GET /orders` to list orders with **pagination** (`page`, `limit`) and **filtering**
  (`status`, `min_amount`, `max_amount`, `start_date`, `end_date`)
- Seed script that inserts **50 sample orders**
- Pytest suite (~25 tests) with coverage target **80%+**

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
| Parameter | Type | Default | Constraints | Description |
|-----------|------|---------|-------------|-------------|
| `page` | int | 1 | >= 1 | Page number (1-indexed) |
| `limit` | int | 10 | 1–100 | Items per page |
| `status` | string | — | `pending\|paid\|shipped\|cancelled` | Filter by order status |
| `min_amount` | float | — | >= 0 | Minimum order amount |
| `max_amount` | float | — | >= 0 | Maximum order amount |
| `start_date` | string | — | YYYY-MM-DD | Filter orders from this date |
| `end_date` | string | — | YYYY-MM-DD | Filter orders up to this date |

#### Pagination example

Request:
```
GET /orders?page=2&limit=5
```

Response `200`:
```json
{
  "page": 2,
  "limit": 5,
  "total": 50,
  "pages": 10,
  "items": [
    {
      "id": 45,
      "customer_name": "Grace Hopper",
      "status": "shipped",
      "amount": 89.99,
      "order_date": "2026-01-20",
      "created_at": "2026-01-20T14:15:00.654321"
    }
  ]
}
```

The response includes pagination metadata:
- `page` — current page number
- `limit` — items per page
- `total` — total matching records across all pages
- `pages` — total number of pages (calculated as `ceil(total / limit)`)
- `items` — array of orders for the current page

Offset is calculated internally as `(page - 1) * limit`.

#### Combined filtering example

Request:
```
GET /orders?status=paid&min_amount=100&max_amount=500&start_date=2026-01-01&end_date=2026-01-31&page=1&limit=20
```

Response `200`:
```json
{
  "page": 1,
  "limit": 20,
  "total": 3,
  "pages": 1,
  "items": [
    {
      "id": 12,
      "customer_name": "Ada Lovelace",
      "status": "paid",
      "amount": 199.99,
      "order_date": "2026-01-15",
      "created_at": "2026-01-15T10:30:00.123456"
    }
  ]
}
```

#### Edge cases and validation

| Scenario | Response |
|----------|----------|
| Page beyond total pages (e.g. `page=9999`) | `200` with empty `items`, correct `total` and `pages` |
| `limit=0` or `limit=-1` | `422` validation error |
| `limit=101` (exceeds max) | `422` validation error |
| `min_amount > max_amount` | `422` "min_amount cannot be greater than max_amount" |
| `start_date > end_date` | `422` "start_date cannot be after end_date" |
| Invalid status value | `422` validation error |
| Filters matching no orders | `200` with `total: 0`, `pages: 0`, `items: []` |

---

## Running tests + coverage
```bash
pytest -q --cov=app --cov-report=term-missing
```

---

## Notes on security and performance
- **SQL injection prevention:** Filtering is built with SQLAlchemy expressions (no string interpolation), so it avoids SQL injection.
- **Input validation:** Pagination parameters are validated (page >= 1, limit capped to 100). Filter values are type-checked and constrained via Pydantic.
- **Performance (10k+ records):** All columns used in filtering and sorting (`status`, `amount`, `order_date`, `created_at`) have database indexes (`index=True`). The count query uses a subquery with only the `id` column for efficiency. Pagination ensures only `limit` rows are fetched per request.

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
  test_orders.py # ~25 tests
report.md        # Claude Code metrics report
```
