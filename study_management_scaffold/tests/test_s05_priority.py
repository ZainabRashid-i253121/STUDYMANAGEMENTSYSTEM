"""S05 tests for approved deadline-based Task Priority behavior."""
from Priority import prioritize_tasks
from Task_Management import create_task, transition_task_status, update_task_deadline, get_task


def test_priority_thresholds_and_overdue_boundaries(test_db, user_id):
    cases = [
        ("Overdue", "2026-11-26", "High"),
        ("Today", "2026-11-27", "High"),
        ("Three days", "2026-11-30", "High"),
        ("Four days", "2026-12-01", "Medium"),
        ("Seven days", "2026-12-04", "Medium"),
        ("Eight days", "2026-12-05", "Low"),
    ]
    for title, deadline, _ in cases:
        create_task(user_id, title, deadline)

    result = prioritize_tasks(user_id, as_of="2026-11-27")
    by_title = {task["title"]: task["priority"] for task in result}
    assert by_title == {title: expected for title, _, expected in cases}


def test_missing_deadline_gets_low_priority(test_db, user_id):
    create_task(user_id, "No deadline")
    task = prioritize_tasks(user_id, as_of="2026-11-27")[0]
    assert task["priority"] == "Low"
    assert task["days_until_deadline"] is None


def test_equal_deadlines_receive_same_priority_without_tiebreaking(test_db, user_id):
    create_task(user_id, "First equal", "2026-11-29")
    create_task(user_id, "Second equal", "2026-11-29")
    tasks = prioritize_tasks(user_id, as_of="2026-11-27")
    assert [task["priority"] for task in tasks] == ["High", "High"]


def test_completed_tasks_are_excluded_and_saved_priority_removed(test_db, user_id):
    task_id = create_task(user_id, "Complete me", "2026-11-28")
    prioritize_tasks(user_id, as_of="2026-11-27")
    with test_db.connection_scope() as db:
        assert db.execute("SELECT COUNT(*) FROM task_priorities WHERE task_id = ?", (task_id,)).fetchone()[0] == 1

    transition_task_status(user_id, task_id, "completed")
    result = prioritize_tasks(user_id, as_of="2026-11-27")
    assert result[0]["priority"] is None
    with test_db.connection_scope() as db:
        assert db.execute("SELECT COUNT(*) FROM task_priorities WHERE task_id = ?", (task_id,)).fetchone()[0] == 0


def test_undetermined_deadline_is_marked_for_review(test_db, user_id):
    task_id = create_task(user_id, "Invalid legacy value", "2026-11-30")
    tasks = [get_task(user_id, task_id)]
    tasks[0]["deadline"] = "not-a-date"
    result = prioritize_tasks(user_id, as_of="2026-11-27", tasks=tasks)
    assert result[0]["priority"] == "Undetermined"
    assert result[0]["priority_requires_review"] is True


def test_conflict_flag_is_consumed_separately_without_changing_priority(test_db, user_id):
    first = create_task(user_id, "Conflict A", "2026-12-01")
    second = create_task(user_id, "Conflict B", "2026-12-02")
    update_task_deadline(user_id, first, "2026-12-10T09:00:00Z")
    update_task_deadline(user_id, second, "2026-12-10T09:00:00Z")
    result = {task["id"]: task for task in prioritize_tasks(user_id, as_of="2026-11-27")}
    assert result[first]["priority"] == "Low"
    assert result[second]["priority"] == "Low"
    assert result[first]["deadline_conflict"] is True
    assert result[second]["deadline_conflict"] is True


def test_priority_is_user_scoped_and_does_not_change_deadline(test_db, user_id):
    with test_db.connection_scope() as db:
        other_user = db.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
            ("s05-other@example.com", "hash", "Registered User"),
        ).lastrowid
    task_id = create_task(user_id, "Owned task", "2026-12-01")
    own_result = prioritize_tasks(user_id, as_of="2026-11-27")
    other_result = prioritize_tasks(other_user, as_of="2026-11-27")
    assert own_result[0]["priority"] == "Medium"
    assert other_result == []
    assert get_task(user_id, task_id)["deadline"] == "2026-12-01"
    with test_db.connection_scope() as db:
        assert db.execute("SELECT COUNT(*) FROM task_priorities WHERE user_id = ?", (other_user,)).fetchone()[0] == 0


def test_dashboard_displays_priority_and_separate_conflict_flag(tmp_path, monkeypatch):
    from app import create_app
    from Data_Access import database

    monkeypatch.setattr(database, "DATABASE_PATH", tmp_path / "s05-dashboard.db")
    app = create_app({"TESTING": True, "SECRET_KEY": "s05-test-secret"})
    with database.connection_scope() as db:
        user_id = db.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
            ("s05-dashboard@example.com", "hash", "Registered User"),
        ).lastrowid
    first = create_task(user_id, "Dashboard priority A", "2026-11-29")
    second = create_task(user_id, "Dashboard priority B", "2026-11-30")
    update_task_deadline(user_id, first, "2026-12-10T09:00:00Z")
    update_task_deadline(user_id, second, "2026-12-10T09:00:00Z")
    client = app.test_client()
    with client.session_transaction() as session:
        session["user_id"] = user_id
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert b"Priority: <strong>Low</strong>" in response.data
    assert b"Deadline conflict " + "\u2014".encode() + b" review required" in response.data
