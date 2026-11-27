"""Authenticated dashboard and delivery endpoint tests for S09."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from Authentication import register_user
from Data_Access import database
from Reminder import list_reminders
from Task_Management import create_task


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DATABASE_PATH", tmp_path / "s09-routes.db")
    return create_app({"TESTING": True, "SECRET_KEY": "s09-route-test-secret"})


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, email):
    response = client.get("/login")
    with client.session_transaction() as sess:
        token = sess["_csrf_token"]
    response = client.post("/login", data={
        "csrf_token": token, "email": email, "password": "correct-password"
    })
    assert response.status_code == 302
    client.get("/dashboard")
    with client.session_transaction() as sess:
        return sess["user_id"], sess["_csrf_token"]


def test_reminder_preferences_are_saved_for_authenticated_user(client):
    register_user("s09-route@example.com", "correct-password")
    user_id, token = login(client, "s09-route@example.com")
    response = client.post("/reminder-preferences", data={
        "csrf_token": token, "enabled": "on", "deadline_enabled": "on"
    })
    assert response.status_code == 302
    from Reminder import get_preferences
    preferences = get_preferences(user_id)
    assert preferences["enabled"] == 1
    assert preferences["deadline_enabled"] == 1
    assert preferences["session_enabled"] == 0


def test_reminder_creation_poll_and_acknowledgment(client, app):
    user_id = register_user("s09-create@example.com", "correct-password")
    event_at = datetime.now(timezone.utc) + timedelta(days=2)
    task_id = create_task(user_id, "Route deadline", event_at.date().isoformat(), deadline_at=event_at.isoformat())
    _, token = login(client, "s09-create@example.com")
    remind_at = (event_at - timedelta(hours=1)).isoformat()
    response = client.post("/reminders", data={
        "csrf_token": token, "target_type": "deadline", "task_id": str(task_id),
        "remind_at": remind_at, "message": "Prepare submission"
    })
    assert response.status_code == 302
    reminder = list_reminders(user_id)[0]
    with database.connection_scope() as db:
        db.execute(
            "UPDATE reminders SET remind_at = ? WHERE id = ?",
            ((datetime.now(timezone.utc) - timedelta(seconds=1)).isoformat(), reminder["id"]),
        )
    poll = client.get("/api/reminders/poll")
    assert poll.status_code == 200
    claimed = poll.get_json()["reminders"]
    assert len(claimed) == 1
    ack = client.post(
        f"/api/reminders/{reminder['id']}/delivery",
        json={"claim_token": claimed[0]["claim_token"], "success": True},
        headers={"X-CSRF-Token": token},
    )
    assert ack.status_code == 200
    assert list_reminders(user_id)[0]["status"] == "delivered"


def test_reminder_endpoints_require_authentication(client):
    assert client.get("/api/reminders/poll").status_code == 302
    assert client.post("/reminder-preferences", data={}).status_code == 302
