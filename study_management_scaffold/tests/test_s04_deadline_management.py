"""S04 tests: timezone-aware imported deadline updates and conflict identification."""
import pytest

from Domain_Rules import (
    DomainRuleError,
    identify_deadline_conflicts,
    validate_deadline_datetime,
)
from Task_Management import create_task, get_task, list_tasks, update_task_deadline
from Events import list_events


def test_deadline_timestamp_requires_explicit_offset():
    assert validate_deadline_datetime("2026-12-10T14:00:00+05:00") == "2026-12-10T09:00:00+00:00"
    assert validate_deadline_datetime("2026-12-10T09:00:00Z") == "2026-12-10T09:00:00+00:00"
    with pytest.raises(DomainRuleError):
        validate_deadline_datetime("2026-12-10T09:00:00")
    with pytest.raises(DomainRuleError):
        validate_deadline_datetime("2026-02-30T09:00:00+00:00")
    with pytest.raises(DomainRuleError):
        validate_deadline_datetime("2026-12-10")


def test_conflicts_use_exact_normalized_instant_only():
    tasks = [
        {"id": 1, "deadline_at": "2026-12-10T14:00:00+05:00"},
        {"id": 2, "deadline_at": "2026-12-10T09:00:00Z"},
        {"id": 3, "deadline_at": "2026-12-10T09:00:01Z"},
        {"id": 4, "deadline_at": None},
        {"id": 5, "deadline": "2026-12-10"},
    ]
    assert identify_deadline_conflicts(tasks) == {1, 2}


def test_import_deadline_update_normalizes_stores_and_publishes_event(test_db, user_id):
    task_id = create_task(user_id, "Imported essay", "2026-12-01")
    updated = update_task_deadline(user_id, task_id, "2026-12-10T14:00:00+05:00")
    assert updated["deadline"] == "2026-12-10"
    assert updated["deadline_at"] == "2026-12-10T09:00:00+00:00"
    events = list_events(user_id)
    assert len(events) == 1
    assert events[0]["event_type"] == "task.deadline_changed"
    assert events[0]["payload"]["new_deadline_at"] == "2026-12-10T09:00:00+00:00"


def test_same_instant_deadlines_flag_both_tasks_and_dashboard_data(test_db, user_id):
    first = create_task(user_id, "First", "2026-12-01")
    second = create_task(user_id, "Second", "2026-12-02")
    update_task_deadline(user_id, first, "2026-12-10T14:00:00+05:00")
    update_task_deadline(user_id, second, "2026-12-10T09:00:00Z")
    tasks = {task["id"]: task for task in list_tasks(user_id)}
    assert tasks[first]["deadline_conflict"] is True
    assert tasks[second]["deadline_conflict"] is True
    assert get_task(user_id, first)["deadline_conflict"] is True


def test_conflict_identification_is_user_scoped(test_db, user_id):
    with test_db.connection_scope() as db:
        other_user = db.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
            ("other-s04@example.com", "test-hash", "Registered User"),
        ).lastrowid
    own_task = create_task(user_id, "Mine", "2026-12-01")
    other_task = create_task(other_user, "Theirs", "2026-12-02")
    update_task_deadline(user_id, own_task, "2026-12-10T09:00:00Z")
    update_task_deadline(other_user, other_task, "2026-12-10T09:00:00Z")
    assert get_task(user_id, own_task)["deadline_conflict"] is False
    assert get_task(other_user, other_task)["deadline_conflict"] is False


def test_update_cannot_change_another_users_task(test_db, user_id):
    with test_db.connection_scope() as db:
        other_user = db.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
            ("private-s04@example.com", "test-hash", "Registered User"),
        ).lastrowid
    task_id = create_task(other_user, "Private", "2026-12-01")
    assert update_task_deadline(user_id, task_id, "2026-12-10T09:00:00Z") is None
    assert get_task(other_user, task_id)["deadline_at"] is None
    assert list_events(user_id) == []


def test_rejected_timestamp_update_changes_neither_task_nor_event(test_db, user_id):
    task_id = create_task(user_id, "Keep old deadline", "2026-12-01")
    with pytest.raises(DomainRuleError):
        update_task_deadline(user_id, task_id, "2026-12-10T09:00:00")
    assert get_task(user_id, task_id)["deadline"] == "2026-12-01"
    assert get_task(user_id, task_id)["deadline_at"] is None
    assert list_events(user_id) == []


def test_legacy_date_only_deadline_is_preserved_without_invented_time(test_db, user_id):
    task_id = create_task(user_id, "Legacy", "2026-12-01")
    task = get_task(user_id, task_id)
    assert task["deadline"] == "2026-12-01"
    assert task["deadline_at"] is None
    assert task["deadline_conflict"] is False


def test_external_integration_exposes_import_update_hook(test_db, user_id):
    from External_Integration import update_imported_task_deadline
    task_id = create_task(user_id, "Matched import", "2026-12-01")
    updated = update_imported_task_deadline(user_id, task_id, "2026-12-10T09:00:00Z")
    assert updated["deadline_at"] == "2026-12-10T09:00:00+00:00"


def test_staged_import_accepts_timezone_aware_deadline(test_db, user_id):
    from External_Integration import stage_import, accept_staged_import, list_staged_imports
    import_id = stage_import(user_id, "school portal", "Timestamped task", "2026-12-10T14:00:00+05:00")
    staged = list_staged_imports(user_id)[0]
    assert staged["deadline"] == "2026-12-10"
    assert staged["deadline_at"] == "2026-12-10T09:00:00+00:00"
    task_id = accept_staged_import(user_id, import_id)
    task = get_task(user_id, task_id)
    assert task["deadline_at"] == "2026-12-10T09:00:00+00:00"


def test_legacy_database_migration_adds_timestamp_columns_without_inventing_values(tmp_path, monkeypatch):
    import sqlite3
    from Data_Access import database
    legacy_path = tmp_path / "legacy.db"
    monkeypatch.setattr(database, "DATABASE_PATH", legacy_path)
    db = sqlite3.connect(legacy_path)
    db.executescript("""
        CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL, role TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
        INSERT INTO users (email, password_hash, role) VALUES ('legacy@example.com', 'hash', 'Registered User');
        CREATE TABLE tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
            title TEXT NOT NULL, course TEXT, deadline TEXT, status TEXT NOT NULL DEFAULT 'incomplete',
            completed_at TEXT, created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            source_import_id INTEGER, FOREIGN KEY (user_id) REFERENCES users(id), UNIQUE (id, user_id));
        INSERT INTO tasks (user_id, title, deadline) VALUES (1, 'Legacy deadline', '2026-12-01');
    """)
    db.commit(); db.close()
    database.init_db()
    with database.connection_scope() as migrated:
        task = migrated.execute("SELECT deadline, deadline_at FROM tasks WHERE id = 1").fetchone()
        assert task["deadline"] == "2026-12-01"
        assert task["deadline_at"] is None
        task_columns = {row[1] for row in migrated.execute("PRAGMA table_info(tasks)")}
        staged_columns = {row[1] for row in migrated.execute("PRAGMA table_info(staged_imports)")}
        assert "deadline_at" in task_columns and "deadline_at" in staged_columns
