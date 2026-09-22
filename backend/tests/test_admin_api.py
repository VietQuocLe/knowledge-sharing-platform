"""Tests for Admin API endpoints: /api/admin/stats, /api/admin/activities, /api/admin/trends."""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.api.auth import get_current_user
from app.models.user import User
from app.models.enums import UserRole, SubscriptionTier


# ── Fixtures ──────────────────────────────────────────────────────────────────

def make_admin_user() -> User:
    u = User()
    u.id = 1
    u.email = "admin@test.com"
    u.full_name = "Admin"
    u.role = UserRole.ADMIN
    u.tier = SubscriptionTier.FREE
    u.is_active = True
    return u


def make_regular_user() -> User:
    u = User()
    u.id = 2
    u.email = "user@test.com"
    u.full_name = "User"
    u.role = UserRole.USER
    u.tier = SubscriptionTier.FREE
    u.is_active = True
    return u


@pytest.fixture()
def admin_client():
    """TestClient with admin user injected as current user."""
    admin = make_admin_user()
    app.dependency_overrides[get_current_user] = lambda: admin
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture()
def user_client():
    """TestClient with regular (non-admin) user injected."""
    user = make_regular_user()
    app.dependency_overrides[get_current_user] = lambda: user
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


# ── /api/admin/stats ──────────────────────────────────────────────────────────

def test_admin_stats_returns_correct_schema(admin_client: TestClient):
    response = admin_client.get("/admin/stats")
    assert response.status_code == 200
    data = response.json()
    assert "users" in data
    assert "documents" in data
    assert "notebooks" in data
    assert "payments" in data
    # Verify user sub-keys
    assert set(data["users"].keys()) >= {"total", "pro", "free", "active"}
    # Verify payment sub-keys
    assert set(data["payments"].keys()) >= {"total_revenue", "successful_orders"}


def test_admin_stats_values_are_non_negative(admin_client: TestClient):
    response = admin_client.get("/admin/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["users"]["total"] >= 0
    assert data["users"]["pro"] >= 0
    assert data["users"]["free"] >= 0
    assert data["documents"]["total"] >= 0
    assert data["notebooks"]["total"] >= 0
    assert data["payments"]["total_revenue"] >= 0


def test_admin_stats_forbidden_for_non_admin(user_client: TestClient):
    response = user_client.get("/admin/stats")
    assert response.status_code == 403


# ── /api/admin/activities ─────────────────────────────────────────────────────

def test_admin_activities_returns_correct_schema(admin_client: TestClient):
    response = admin_client.get("/admin/activities")
    assert response.status_code == 200
    data = response.json()
    assert "recent_transactions" in data
    assert "recent_users" in data
    assert isinstance(data["recent_transactions"], list)
    assert isinstance(data["recent_users"], list)
    assert len(data["recent_transactions"]) <= 10
    assert len(data["recent_users"]) <= 10


def test_admin_activities_forbidden_for_non_admin(user_client: TestClient):
    response = user_client.get("/admin/activities")
    assert response.status_code == 403


# ── /admin/trends ─────────────────────────────────────────────────────────────

def test_admin_trends_returns_30_day_data(admin_client: TestClient):
    response = admin_client.get("/admin/trends")
    assert response.status_code == 200
    data = response.json()
    assert "user_registrations" in data
    assert "daily_revenue" in data
    assert len(data["user_registrations"]) == 30
    assert len(data["daily_revenue"]) == 30


def test_admin_trends_data_points_have_correct_keys(admin_client: TestClient):
    response = admin_client.get("/admin/trends")
    assert response.status_code == 200
    data = response.json()
    for point in data["user_registrations"]:
        assert "date" in point
        assert "count" in point
        assert point["count"] >= 0
    for point in data["daily_revenue"]:
        assert "date" in point
        assert "amount" in point
        assert point["amount"] >= 0


def test_admin_trends_forbidden_for_non_admin(user_client: TestClient):
    response = user_client.get("/admin/trends")
    assert response.status_code == 403
