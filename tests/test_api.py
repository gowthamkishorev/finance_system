"""
Unit tests for FinTrack API.
Run with: pytest tests/ -v
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.main import app

# Use an in-memory SQLite database for tests
TEST_DATABASE_URL = "sqlite:///./test_fintrack.db"
test_engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


@pytest.fixture(scope="module")
def admin_token(client):
    client.post("/auth/register", json={
        "username": "testadmin",
        "email": "testadmin@test.com",
        "password": "admin123",
        "role": "admin",
    })
    resp = client.post("/auth/login", data={"username": "testadmin", "password": "admin123"})
    return resp.json()["access_token"]


@pytest.fixture(scope="module")
def viewer_token(client):
    client.post("/auth/register", json={
        "username": "testviewer",
        "email": "testviewer@test.com",
        "password": "viewer123",
        "role": "viewer",
    })
    resp = client.post("/auth/login", data={"username": "testviewer", "password": "viewer123"})
    return resp.json()["access_token"]


# ── Auth Tests ────────────────────────────────────────────────────────────────

class TestAuth:
    def test_register_success(self, client):
        resp = client.post("/auth/register", json={
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "pass1234",
        })
        assert resp.status_code == 201
        assert resp.json()["username"] == "newuser"
        assert resp.json()["role"] == "viewer"

    def test_register_duplicate_username(self, client):
        client.post("/auth/register", json={"username": "dupuser", "email": "dup@test.com", "password": "pass1234"})
        resp = client.post("/auth/register", json={"username": "dupuser", "email": "dup2@test.com", "password": "pass1234"})
        assert resp.status_code == 400

    def test_login_success(self, client):
        resp = client.post("/auth/login", data={"username": "newuser", "password": "pass1234"})
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_wrong_password(self, client):
        resp = client.post("/auth/login", data={"username": "newuser", "password": "wrongpass"})
        assert resp.status_code == 401

    def test_register_invalid_email(self, client):
        resp = client.post("/auth/register", json={
            "username": "bademail",
            "email": "not-an-email",
            "password": "pass1234",
        })
        assert resp.status_code == 422


# ── Transaction Tests ─────────────────────────────────────────────────────────

class TestTransactions:
    def test_create_transaction_as_admin(self, client, admin_token):
        resp = client.post("/transactions/", json={
            "amount": 1500.0,
            "type": "income",
            "category": "salary",
            "notes": "Monthly salary",
        }, headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 201
        assert resp.json()["amount"] == 1500.0

    def test_create_transaction_negative_amount(self, client, admin_token):
        resp = client.post("/transactions/", json={
            "amount": -100.0,
            "type": "expense",
            "category": "food",
        }, headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 422

    def test_viewer_cannot_create_transaction(self, client, viewer_token):
        resp = client.post("/transactions/", json={
            "amount": 100.0,
            "type": "expense",
            "category": "food",
        }, headers={"Authorization": f"Bearer {viewer_token}"})
        assert resp.status_code == 403

    def test_list_transactions(self, client, admin_token):
        resp = client.get("/transactions/", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "items" in data
        assert "total" in data

    def test_filter_by_type(self, client, admin_token):
        resp = client.get("/transactions/?type=income", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        for item in resp.json()["items"]:
            assert item["type"] == "income"

    def test_update_transaction(self, client, admin_token):
        # Create then update
        create_resp = client.post("/transactions/", json={
            "amount": 200.0, "type": "expense", "category": "food",
        }, headers={"Authorization": f"Bearer {admin_token}"})
        t_id = create_resp.json()["id"]

        update_resp = client.patch(f"/transactions/{t_id}", json={"amount": 250.0},
                                   headers={"Authorization": f"Bearer {admin_token}"})
        assert update_resp.status_code == 200
        assert update_resp.json()["amount"] == 250.0

    def test_delete_transaction(self, client, admin_token):
        create_resp = client.post("/transactions/", json={
            "amount": 50.0, "type": "expense", "category": "transport",
        }, headers={"Authorization": f"Bearer {admin_token}"})
        t_id = create_resp.json()["id"]

        del_resp = client.delete(f"/transactions/{t_id}",
                                 headers={"Authorization": f"Bearer {admin_token}"})
        assert del_resp.status_code == 204

        get_resp = client.get(f"/transactions/{t_id}",
                              headers={"Authorization": f"Bearer {admin_token}"})
        assert get_resp.status_code == 404


# ── Analytics Tests ───────────────────────────────────────────────────────────

class TestAnalytics:
    def test_summary_returns_correct_structure(self, client, admin_token):
        resp = client.get("/analytics/summary", headers={"Authorization": f"Bearer {admin_token}"})
        assert resp.status_code == 200
        data = resp.json()
        assert "total_income" in data
        assert "total_expenses" in data
        assert "balance" in data
        assert "category_breakdown" in data
        assert "monthly_totals" in data

    def test_balance_calculation(self, client, admin_token):
        resp = client.get("/analytics/summary", headers={"Authorization": f"Bearer {admin_token}"})
        data = resp.json()
        expected_balance = round(data["total_income"] - data["total_expenses"], 2)
        assert data["balance"] == expected_balance
