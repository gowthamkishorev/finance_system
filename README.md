# FinTrack — Python Finance System Backend

A clean, role-based financial tracking API built with **FastAPI**, **SQLAlchemy**, and **SQLite**.

---

## Features

- **Full CRUD** for financial transactions (income & expenses)
- **Role-based access control**: Admin, Analyst, Viewer
- **JWT authentication** (Bearer tokens)
- **Analytics**: total income/expenses, balance, category breakdown, monthly trends
- **Filtering & pagination** on transaction listing
- **Input validation** and consistent error responses (Pydantic + FastAPI)
- **Auto-seeded demo data** on first startup
- **Unit tests** with pytest and an isolated test database

---

## Tech Stack

| Layer        | Choice                                  |
|--------------|-----------------------------------------|
| Framework    | FastAPI                                 |
| ORM          | SQLAlchemy 2.x                          |
| Database     | SQLite (file: `fintrack.db`)            |
| Auth         | JWT via `python-jose`, bcrypt passwords |
| Validation   | Pydantic v2                             |
| Tests        | pytest + httpx (TestClient)             |
| Server       | Uvicorn                                 |

---

## Setup

### 1. Clone / unzip the project

```bash
cd finance_system
```

### 2. Create a virtual environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the server

```bash
uvicorn app.main:app --reload
```

The server starts at **http://localhost:8000**.

On first startup, the database is created and seeded automatically with demo data.

---

## Interactive API Docs

| URL                                | Description               |
|------------------------------------|---------------------------|
| http://localhost:8000/docs         | Swagger UI (try it live)  |
| http://localhost:8000/redoc        | ReDoc documentation       |

---

## Demo Credentials

These accounts are seeded automatically:

| Role     | Username | Password   |
|----------|----------|------------|
| Admin    | `admin`  | `admin123` |
| Analyst  | `alice`  | `alice123` |
| Viewer   | `bob`    | `bob123`   |

### How to authenticate in Swagger UI:

1. Go to `POST /auth/login`
2. Enter username and password
3. Copy the `access_token` from the response
4. Click **Authorize** (top right) → paste `<token>` in the Bearer field

---

## API Overview

### Authentication

| Method | Endpoint         | Description              |
|--------|------------------|--------------------------|
| POST   | `/auth/register` | Register a new user      |
| POST   | `/auth/login`    | Login → returns JWT      |

### Users

| Method | Endpoint          | Access        | Description              |
|--------|-------------------|---------------|--------------------------|
| GET    | `/users/me`       | All           | Get own profile          |
| GET    | `/users/`         | Admin         | List all users           |
| GET    | `/users/{id}`     | Admin / Self  | Get user by ID           |
| PATCH  | `/users/{id}`     | Admin / Self  | Update user              |
| DELETE | `/users/{id}`     | Admin         | Delete user              |

### Transactions

| Method | Endpoint                  | Access              | Description                        |
|--------|---------------------------|---------------------|------------------------------------|
| POST   | `/transactions/`          | Admin, Analyst      | Create a transaction               |
| GET    | `/transactions/`          | All                 | List with filters & pagination     |
| GET    | `/transactions/{id}`      | All (scoped)        | Get single transaction             |
| PATCH  | `/transactions/{id}`      | Admin, Analyst      | Update a transaction               |
| DELETE | `/transactions/{id}`      | Admin, Analyst      | Delete a transaction               |

#### Transaction filters (query params)

| Param        | Type     | Example                    |
|--------------|----------|----------------------------|
| `type`       | string   | `income` or `expense`      |
| `category`   | string   | `salary`, `food`, etc.     |
| `start_date` | datetime | `2024-01-01T00:00:00`      |
| `end_date`   | datetime | `2024-12-31T23:59:59`      |
| `owner_id`   | int      | Admin/Analyst only         |
| `page`       | int      | Default: 1                 |
| `page_size`  | int      | Default: 20, max: 100      |

### Analytics

| Method | Endpoint             | Access         | Description                      |
|--------|----------------------|----------------|----------------------------------|
| GET    | `/analytics/summary` | All (scoped)   | Full financial summary           |

Summary includes: total income, expenses, balance, category breakdown, monthly totals, recent 10 transactions.

---

## Role Permissions Summary

| Action                        | Viewer | Analyst | Admin |
|-------------------------------|--------|---------|-------|
| View own transactions         | ✅     | ✅      | ✅    |
| View all transactions         | ❌     | ✅      | ✅    |
| Create transactions           | ❌     | ✅      | ✅    |
| Update own transactions       | ❌     | ✅      | ✅    |
| Update any transaction        | ❌     | ❌      | ✅    |
| Delete transactions           | ❌     | ✅*     | ✅    |
| View own analytics summary    | ✅     | ✅      | ✅    |
| View all analytics            | ❌     | ✅      | ✅    |
| Manage users                  | ❌     | ❌      | ✅    |

*Analysts can only delete their own transactions.

---

## Transaction Categories

**Income:** `salary`, `freelance`, `investment`

**Expense:** `food`, `transport`, `housing`, `entertainment`, `healthcare`, `utilities`, `shopping`, `other`

---

## Running Tests

```bash
pytest tests/ -v
```

Tests use an isolated SQLite database (`test_fintrack.db`) that is created and torn down automatically. No changes to your main database.

---

## Project Structure

```
finance_system/
├── app/
│   ├── main.py              # FastAPI app, middleware, router registration
│   ├── database.py          # SQLAlchemy engine, session, get_db dependency
│   ├── auth.py              # JWT creation/validation, role enforcement
│   ├── schemas.py           # Pydantic request/response models
│   ├── seed.py              # Demo data seeder (runs on startup)
│   ├── models/
│   │   ├── user.py          # User ORM model + UserRole enum
│   │   └── transaction.py   # Transaction ORM model + enums
│   ├── routes/
│   │   ├── auth.py          # /auth endpoints
│   │   ├── users.py         # /users endpoints
│   │   ├── transactions.py  # /transactions endpoints
│   │   └── analytics.py     # /analytics endpoints
│   └── services/
│       ├── transaction_service.py  # CRUD logic, access control
│       └── analytics_service.py   # Summary computation
├── tests/
│   └── test_api.py          # pytest unit tests
├── requirements.txt
└── README.md
```

---

## Design Decisions & Assumptions

1. **SQLite** was chosen for simplicity and zero-config setup. Switching to PostgreSQL only requires changing `DATABASE_URL` in `database.py`.

2. **JWT tokens** are stateless (no token blacklist). In production, add a Redis-backed revocation list or use short-lived tokens with refresh tokens.

3. **Roles are assigned at registration.** In a real system, only admins would be able to elevate roles — the `/users/{id}` PATCH endpoint already enforces this.

4. **Analysts own their transactions.** An Analyst can create/update/delete only their own records. Admin can manage all.

5. **Amount validation** enforces `> 0`. Transaction type (`income`/`expense`) is the semantic indicator of direction, not a negative amount.

6. **Secret key** is hardcoded for demo purposes. In production, load it from an environment variable or secrets manager.

---

## Example: Quick API Walkthrough

```bash
# 1. Login
curl -X POST http://localhost:8000/auth/login \
  -d "username=admin&password=admin123"

# 2. Use the returned token
TOKEN="<paste_token_here>"

# 3. Create a transaction
curl -X POST http://localhost:8000/transactions/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount": 3000, "type": "income", "category": "salary", "notes": "March salary"}'

# 4. Get analytics summary
curl http://localhost:8000/analytics/summary \
  -H "Authorization: Bearer $TOKEN"

# 5. Filter transactions
curl "http://localhost:8000/transactions/?type=expense&category=food&page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```
