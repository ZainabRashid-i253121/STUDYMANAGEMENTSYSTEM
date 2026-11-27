"""Flask route tests for registration, login/logout, CSRF, and completion toggling."""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from Data_Access import database
from Task_Management import create_task, get_task


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DATABASE_PATH", tmp_path / "cleanup-test.db")
    return create_app({"TESTING": True, "SECRET_KEY": "cleanup-test-secret"})


@pytest.fixture
def client(app):
    return app.test_client()


def form_token(client, page):
    response = client.get(page)
    assert response.status_code == 200
    with client.session_transaction() as sess:
        return sess["_csrf_token"]


def add_user(email, password="correct-password"):
    from Authentication import register_user
    return register_user(email, password)


def log_in(client, email="routeuser@example.com", password="correct-password"):
    token = form_token(client, "/login")
    response = client.post("/login", data={"csrf_token": token, "email": email, "password": password})
    assert response.status_code == 302
    # Login rotates the session; request a protected page to establish its CSRF token.
    assert client.get("/dashboard").status_code == 200
    with client.session_transaction() as sess:
        return sess["user_id"], sess["_csrf_token"]


def test_register_success(client):
    token = form_token(client, "/register")
    response = client.post("/register", data={
        "csrf_token": token, "email": "newuser@example.com", "password": "long-password"
    })
    assert response.status_code == 302
    assert get_task is not None
    with client.session_transaction() as sess:
        assert sess.get("user_id") is not None


def test_register_duplicate_email(client):
    add_user("duplicate@example.com")
    token = form_token(client, "/register")
    response = client.post("/register", data={
        "csrf_token": token, "email": "duplicate@example.com", "password": "long-password"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"already exists" in response.data


def test_register_short_password(client):
    token = form_token(client, "/register")
    response = client.post("/register", data={
        "csrf_token": token, "email": "short@example.com", "password": "short"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"at least 8 characters" in response.data


def test_login_success_and_wrong_password(client):
    add_user("routeuser@example.com")
    token = form_token(client, "/login")
    wrong = client.post("/login", data={
        "csrf_token": token, "email": "routeuser@example.com", "password": "wrong-password"
    }, follow_redirects=True)
    assert b"Email or password is incorrect" in wrong.data
    token = form_token(client, "/login")
    good = client.post("/login", data={
        "csrf_token": token, "email": "routeuser@example.com", "password": "correct-password"
    })
    assert good.status_code == 302
    with client.session_transaction() as sess:
        assert sess.get("user_id") is not None


def test_logout(client):
    add_user("logout@example.com")
    _, token = log_in(client, "logout@example.com")
    response = client.post("/logout", data={"csrf_token": token})
    assert response.status_code == 302
    with client.session_transaction() as sess:
        assert "user_id" not in sess


def test_complete_then_revert_task_to_incomplete(client):
    user_id = add_user("reverter@example.com")
    task_id = create_task(user_id, "Toggle me", "2099-10-01")
    _, token = log_in(client, "reverter@example.com")
    done = client.post(f"/tasks/{task_id}/complete", data={"csrf_token": token})
    assert done.status_code == 302
    assert get_task(user_id, task_id)["status"] == "completed"
    assert get_task(user_id, task_id)["completed_at"] is not None
    assert b">Mark incomplete</button>" in client.get("/dashboard").data
    reverted = client.post(f"/tasks/{task_id}/incomplete", data={"csrf_token": token})
    assert reverted.status_code == 302
    task = get_task(user_id, task_id)
    assert task["status"] == "incomplete"
    assert task["deadline"] == "2099-10-01"   # BR-06: the original deadline is never changed


def test_revert_another_users_task_returns_404(client):
    add_user("task-owner@example.com")
    other_id = add_user("task-visitor@example.com")
    task_id = create_task(other_id, "Private done task", "2099-10-02")
    from Task_Management import transition_task_status
    transition_task_status(other_id, task_id, "completed")
    _, token = log_in(client, "task-owner@example.com")
    response = client.post(f"/tasks/{task_id}/incomplete", data={"csrf_token": token})
    assert response.status_code == 404
    assert get_task(other_id, task_id)["status"] == "completed"


def test_start_route_no_longer_exists(client):
    user_id = add_user("nostart@example.com")
    task_id = create_task(user_id, "No start", "2099-10-02")
    _, token = log_in(client, "nostart@example.com")
    assert client.post(f"/tasks/{task_id}/start", data={"csrf_token": token}).status_code == 404


@pytest.mark.parametrize("path,method", [
    ("/register", "post"), ("/login", "post"),
])
def test_public_post_routes_reject_missing_csrf(client, path, method):
    response = getattr(client, method)(path, data={})
    assert response.status_code == 400


def test_authenticated_post_routes_reject_missing_csrf(client):
    user_id = add_user("csrf-user@example.com")
    task_id = create_task(user_id, "CSRF task", "2099-10-03")
    log_in(client, "csrf-user@example.com")

    # /logout deliberately redirects back to the dashboard when CSRF is
    # missing; importantly, the session remains authenticated.
    logout_response = client.post("/logout", data={})
    assert logout_response.status_code == 302
    assert logout_response.headers["Location"].endswith("/dashboard")
    with client.session_transaction() as sess:
        assert sess.get("user_id") == user_id

    # The task mutation endpoints reject missing CSRF tokens with HTTP 400.
    for path in [f"/tasks/{task_id}/incomplete", f"/tasks/{task_id}/complete"]:
        response = client.post(path, data={})
        assert response.status_code == 400, path
