from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app
from Data_Access import database
from Task_Management import create_task, get_completion_summary, get_task, list_tasks, transition_task_status


@pytest.fixture
def app(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DATABASE_PATH", tmp_path / "s03-test.db")
    return create_app({"TESTING": True, "SECRET_KEY": "test-secret"})


@pytest.fixture
def manual_app(tmp_path, monkeypatch):
    """App with the development/demo manual-entry flag switched on."""
    monkeypatch.setattr(database, "DATABASE_PATH", tmp_path / "s03-manual.db")
    return create_app({"TESTING": True, "SECRET_KEY": "test-secret", "ALLOW_MANUAL_TASK_ENTRY": True})


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def manual_client(manual_app):
    return manual_app.test_client()


def add_user(email):
    with database.connection_scope() as db:
        cursor = db.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
            (email, "test-only-hash", "Registered User"),
        )
        return cursor.lastrowid


def authenticate(client, user_id):
    with client.session_transaction() as session:
        session["user_id"] = user_id
    response = client.get("/dashboard")
    assert response.status_code == 200
    with client.session_transaction() as session:
        return session["_csrf_token"]


def test_dashboard_requires_login(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_dashboard_empty_state_without_manual_entry(client):
    token = authenticate(client, add_user("student1@example.com"))
    page = client.get("/dashboard")
    assert b"No tasks yet" in page.data
    assert b"Add a task" not in page.data        # form is not rendered
    assert token


def test_manual_entry_disabled_by_default_returns_404(client):
    token = authenticate(client, add_user("student-off@example.com"))
    response = client.post("/tasks", data={"csrf_token": token, "title": "X", "deadline": "2099-01-10"})
    assert response.status_code == 404
    assert list_tasks(1) == []


def test_manual_entry_enabled_shows_form_and_adds_task(manual_client):
    token = authenticate(manual_client, add_user("student-on@example.com"))
    assert b"Add a task" in manual_client.get("/dashboard").data
    response = manual_client.post("/tasks", data={
        "csrf_token": token, "title": "Read chapter 4",
        "course": "Software Engineering", "deadline": "2099-01-10",
    })
    assert response.status_code == 302
    page = manual_client.get("/dashboard")
    assert b"Read chapter 4" in page.data
    assert b"Software Engineering" in page.data
    assert b"incomplete" in page.data


def test_manual_entry_without_deadline_is_allowed(manual_client):
    token = authenticate(manual_client, add_user("student-nodl@example.com"))
    response = manual_client.post("/tasks", data={"csrf_token": token, "title": "Undated", "deadline": ""})
    assert response.status_code == 302
    assert list_tasks(1)[0]["deadline"] is None


def test_manual_entry_requires_csrf_when_enabled(manual_client):
    authenticate(manual_client, add_user("student-csrf@example.com"))
    assert manual_client.post("/tasks", data={"title": "X"}).status_code == 400


def test_invalid_task_shows_domain_error_flash(manual_client):
    token = authenticate(manual_client, add_user("student2@example.com"))
    response = manual_client.post("/tasks", data={
        "csrf_token": token, "title": "   ", "course": "Math", "deadline": "2099-01-10",
    }, follow_redirects=True)
    assert b"Task title is required" in response.data
    assert b"No tasks yet" in response.data


def test_invalid_non_empty_deadline_is_rejected(manual_client):
    token = authenticate(manual_client, add_user("student-baddl@example.com"))
    response = manual_client.post("/tasks", data={
        "csrf_token": token, "title": "Bad date", "deadline": "2026-02-30",
    }, follow_redirects=True)
    assert b"valid date" in response.data
    assert list_tasks(1) == []


def test_tasks_without_deadline_stay_visible_and_are_marked(client):
    user_id = add_user("missing@example.com")
    create_task(user_id, "Has deadline", "2099-05-01")
    create_task(user_id, "Has no deadline")
    authenticate(client, user_id)
    page = client.get("/dashboard")
    assert b"Has no deadline" in page.data
    assert b"Missing deadline information" in page.data
    # undated tasks are listed after dated tasks
    assert page.data.index(b"Has deadline") < page.data.index(b"Has no deadline")


def test_complete_task_and_completed_state(client):
    user_id = add_user("student3@example.com")
    task_id = create_task(user_id, "Submit assignment", "2099-02-01", "SE")
    token = authenticate(client, user_id)
    response = client.post(f"/tasks/{task_id}/complete", data={"csrf_token": token})
    assert response.status_code == 302
    page = client.get("/dashboard")
    assert b"Completed" in page.data
    # the guidance text also names these actions, so check the real buttons
    assert b">Mark complete</button>" not in page.data
    assert b">Mark incomplete</button>" in page.data
    task = get_task(user_id, task_id)
    assert task["completed_at"] is not None and task["deadline"] == "2099-02-01"


def test_completing_twice_is_rejected_with_flash(client):
    user_id = add_user("student4@example.com")
    task_id = create_task(user_id, "Finish notes", "2099-03-01")
    token = authenticate(client, user_id)
    assert client.post(f"/tasks/{task_id}/complete", data={"csrf_token": token}).status_code == 302
    second = client.post(f"/tasks/{task_id}/complete", data={"csrf_token": token}, follow_redirects=True)
    assert b"already completed" in second.data


def test_mark_incomplete_reverts_and_clears_completion_date(client):
    user_id = add_user("revert@example.com")
    task_id = create_task(user_id, "Undo me", "2099-03-05")
    token = authenticate(client, user_id)
    client.post(f"/tasks/{task_id}/complete", data={"csrf_token": token})
    client.post(f"/tasks/{task_id}/incomplete", data={"csrf_token": token})
    task = get_task(user_id, task_id)
    assert task["status"] == "incomplete"
    assert task["completed_at"] is None     # PROVISIONAL pending G-08


def test_marking_incomplete_twice_is_rejected_with_flash(client):
    user_id = add_user("twice@example.com")
    task_id = create_task(user_id, "Already open", "2099-03-06")
    token = authenticate(client, user_id)
    response = client.post(f"/tasks/{task_id}/incomplete", data={"csrf_token": token}, follow_redirects=True)
    assert b"already incomplete" in response.data


def test_user_cannot_complete_or_revert_another_users_task(client):
    user_a = add_user("owner@example.com")
    user_b = add_user("other@example.com")
    task_id = create_task(user_b, "Private task", "2099-04-01")
    token = authenticate(client, user_a)
    assert client.post(f"/tasks/{task_id}/complete", data={"csrf_token": token}).status_code == 404
    assert client.post(f"/tasks/{task_id}/incomplete", data={"csrf_token": token}).status_code == 404
    assert get_task(user_b, task_id)["status"] == "incomplete"


def test_completion_routes_require_csrf(client):
    user_id = add_user("csrf3@example.com")
    task_id = create_task(user_id, "Guarded", "2099-04-02")
    authenticate(client, user_id)
    assert client.post(f"/tasks/{task_id}/complete", data={}).status_code == 400
    assert client.post(f"/tasks/{task_id}/incomplete", data={}).status_code == 400


def test_completion_summary_counts_are_correct(app):
    user_id = add_user("summary@example.com")
    create_task(user_id, "Open task", "2099-05-01")
    create_task(user_id, "Undated open task")
    done_id = create_task(user_id, "Done task", "2099-05-03")
    transition_task_status(user_id, done_id, "completed")
    assert get_completion_summary(user_id) == {
        "total": 3, "incomplete": 2, "completed": 1, "completion_percentage": 33.3,
    }


def test_dashboard_filter_by_completion_status(client):
    user_id = add_user("filter@example.com")
    create_task(user_id, "Still open", "2099-06-01")
    done_id = create_task(user_id, "Already done", "2099-06-02")
    transition_task_status(user_id, done_id, "completed")
    authenticate(client, user_id)
    both = client.get("/dashboard?status=all").data
    assert b"Still open" in both and b"Already done" in both
    only_open = client.get("/dashboard?status=incomplete").data
    assert b"Still open" in only_open and b"Already done" not in only_open
    only_done = client.get("/dashboard?status=completed").data
    assert b"Already done" in only_done and b"Still open" not in only_done
    unknown = client.get("/dashboard?status=bogus").data   # falls back to all
    assert b"Still open" in unknown and b"Already done" in unknown


def test_filter_with_no_matches_shows_message_not_empty_state(client):
    user_id = add_user("nomatch@example.com")
    create_task(user_id, "Only open", "2099-06-03")
    authenticate(client, user_id)
    page = client.get("/dashboard?status=completed")
    assert b"No completed tasks to show" in page.data
    assert b"No tasks yet" not in page.data


def test_dashboard_shows_guidance(client):
    authenticate(client, add_user("guide@example.com"))
    page = client.get("/dashboard")
    assert b"How to use this dashboard" in page.data
    assert b"Missing deadline information" in page.data     # guidance mentions the marker


def test_dashboard_has_no_overdue_marking(client):
    user_id = add_user("overdue@example.com")
    create_task(user_id, "Past deadline", "2000-01-01")
    authenticate(client, user_id)
    page = client.get("/dashboard")
    assert b"Past deadline" in page.data
    assert b"Overdue" not in page.data


def test_dashboard_is_responsive_shell(client):
    authenticate(client, add_user("mobile@example.com"))
    assert b'name="viewport"' in client.get("/dashboard").data


def test_dashboard_shows_only_owned_tasks_sorted_by_deadline(client):
    user_a = add_user("dashboard-owner@example.com")
    user_b = add_user("dashboard-other@example.com")
    create_task(user_a, "Later task", "2099-08-20")
    create_task(user_a, "Earlier task", "2099-08-10")
    create_task(user_b, "Other user's private task", "2099-08-01")
    authenticate(client, user_a)
    data = client.get("/dashboard").data
    assert b"Other user&#39;s private task" not in data
    assert data.index(b"Earlier task") < data.index(b"Later task")
