from datetime import datetime, timedelta, timezone

from Reminder import (
    claim_due_reminders,
    complete_delivery,
    create_reminder,
    dismiss_notice,
    get_preferences,
    list_notices,
    list_reminder_presets,
    list_reminders,
    register_event_handlers,
    update_preferences,
)
from Schedule import schedule_study_session
from Task_Management import create_task, transition_task_status, update_task_deadline
import Events


def iso(value):
    return value.astimezone(timezone.utc).isoformat()


def test_preferences_are_user_scoped_and_can_be_disabled(test_db, user_id):
    with test_db.connection_scope() as db:
        other = db.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
            ("s09-other@example.com", "hash", "Registered User"),
        ).lastrowid
    assert get_preferences(user_id)["enabled"] == 1
    update_preferences(user_id, enabled=False, deadline_enabled=True, session_enabled=False)
    assert get_preferences(user_id)["enabled"] == 0
    assert get_preferences(user_id)["session_enabled"] == 0
    assert get_preferences(other)["enabled"] == 1


def test_create_multiple_deadline_reminders_and_reuse_saved_offsets(test_db, user_id):
    event_at = datetime.now(timezone.utc) + timedelta(days=3)
    task_id = create_task(user_id, "S09 deadline", event_at.date().isoformat(), deadline_at=iso(event_at))
    first = event_at - timedelta(hours=1)
    second = event_at - timedelta(hours=2)
    first_id = create_reminder(user_id, iso(first), task_id=task_id)
    second_id = create_reminder(user_id, iso(second), task_id=task_id)
    reminders = list_reminders(user_id)
    assert {row["id"] for row in reminders} >= {first_id, second_id}
    assert all(row["event_type"] == "deadline" for row in reminders if row["id"] in {first_id, second_id})
    assert set(list_reminder_presets(user_id, "deadline")) == {3600, 7200}


def test_task_deadline_event_updates_pending_reminder(test_db, user_id):
    register_event_handlers()
    old_event = datetime.now(timezone.utc) + timedelta(days=4)
    task_id = create_task(user_id, "Move deadline", old_event.date().isoformat(), deadline_at=iso(old_event))
    remind_at = old_event - timedelta(hours=3)
    reminder_id = create_reminder(user_id, iso(remind_at), task_id=task_id)
    new_event = old_event + timedelta(days=2)
    update_task_deadline(user_id, task_id, iso(new_event))
    Events.process_pending_events()
    reminder = next(row for row in list_reminders(user_id) if row["id"] == reminder_id)
    assert reminder["event_at"] == iso(new_event)
    assert datetime.fromisoformat(reminder["remind_at"]) == new_event - timedelta(hours=3)


def test_completion_cancels_pending_deadline_reminders(test_db, user_id):
    register_event_handlers()
    event_at = datetime.now(timezone.utc) + timedelta(days=2)
    task_id = create_task(user_id, "Complete task", event_at.date().isoformat(), deadline_at=iso(event_at))
    reminder_id = create_reminder(user_id, iso(event_at - timedelta(hours=1)), task_id=task_id)
    transition_task_status(user_id, task_id, "completed")
    Events.process_pending_events()
    reminder = next(row for row in list_reminders(user_id) if row["id"] == reminder_id)
    assert reminder["status"] == "cancelled"


def test_session_reminder_uses_owned_scheduled_session(test_db, user_id):
    session_date = (datetime.now(timezone.utc) + timedelta(days=3)).date().isoformat()
    session_id = schedule_study_session(user_id, session_date, "10:00", "11:00")
    event_at = datetime.now(timezone.utc) + timedelta(days=3, hours=10)
    reminder_id = create_reminder(
        user_id, iso(event_at - timedelta(minutes=30)), session_id=session_id, event_at=iso(event_at)
    )
    reminder = next(row for row in list_reminders(user_id) if row["id"] == reminder_id)
    assert reminder["event_type"] == "session"
    assert reminder["session_id"] == session_id
    assert reminder["offset_seconds"] == 1800


def test_due_reminders_are_claimed_once_across_tabs(test_db, user_id):
    event_at = datetime.now(timezone.utc) + timedelta(days=1)
    task_id = create_task(user_id, "Due soon", event_at.date().isoformat(), deadline_at=iso(event_at))
    remind_at = datetime.now(timezone.utc) + timedelta(seconds=2)
    reminder_id = create_reminder(user_id, iso(remind_at), task_id=task_id)
    claim_time = remind_at + timedelta(seconds=1)
    first = claim_due_reminders(user_id, now=claim_time)
    second = claim_due_reminders(user_id, now=claim_time)
    assert [item["id"] for item in first] == [reminder_id]
    assert second == []
    assert complete_delivery(user_id, reminder_id, first[0]["claim_token"], success=True)
    assert not complete_delivery(user_id, reminder_id, first[0]["claim_token"], success=True)
    assert next(row for row in list_reminders(user_id) if row["id"] == reminder_id)["status"] == "delivered"


def test_delivery_failure_is_recorded_and_retryable_without_fixed_maximum(test_db, user_id):
    event_at = datetime.now(timezone.utc) + timedelta(days=1)
    task_id = create_task(user_id, "Retry me", event_at.date().isoformat(), deadline_at=iso(event_at))
    remind_at = datetime.now(timezone.utc) + timedelta(seconds=2)
    reminder_id = create_reminder(user_id, iso(remind_at), task_id=task_id)
    claim = claim_due_reminders(user_id, now=remind_at + timedelta(seconds=1))[0]
    assert complete_delivery(user_id, reminder_id, claim["claim_token"], success=False, error="browser unavailable")
    row = next(row for row in list_reminders(user_id) if row["id"] == reminder_id)
    assert row["status"] == "pending"
    assert row["attempts"] == 1
    assert row["last_error"] == "browser unavailable"
    retry = claim_due_reminders(user_id, now=remind_at + timedelta(seconds=2))
    assert [item["id"] for item in retry] == [reminder_id]
    assert complete_delivery(user_id, reminder_id, retry[0]["claim_token"], success=False, error="still unavailable")
    row = next(row for row in list_reminders(user_id) if row["id"] == reminder_id)
    assert row["attempts"] == 2 and row["status"] == "pending"


def test_passed_reminder_is_skipped_and_notice_can_be_dismissed(test_db, user_id):
    event_at = datetime.now(timezone.utc) + timedelta(days=1)
    task_id = create_task(user_id, "Late setup", event_at.date().isoformat(), deadline_at=iso(event_at))
    reminder_id = create_reminder(user_id, iso(datetime.now(timezone.utc) - timedelta(minutes=1)), task_id=task_id)
    row = next(row for row in list_reminders(user_id) if row["id"] == reminder_id)
    assert row["status"] == "skipped"
    notices = list_notices(user_id)
    assert len(notices) == 1
    assert dismiss_notice(user_id, notices[0]["id"])
    assert list_notices(user_id) == []


def test_cancelled_reminder_ignores_late_delivery_acknowledgment(test_db, user_id):
    register_event_handlers()
    event_at = datetime.now(timezone.utc) + timedelta(days=1)
    task_id = create_task(user_id, "Cancel during delivery", event_at.date().isoformat(), deadline_at=iso(event_at))
    remind_at = datetime.now(timezone.utc) + timedelta(seconds=2)
    reminder_id = create_reminder(user_id, iso(remind_at), task_id=task_id)
    claim = claim_due_reminders(user_id, now=remind_at + timedelta(seconds=1))[0]
    transition_task_status(user_id, task_id, "completed")
    Events.process_pending_events()
    assert not complete_delivery(user_id, reminder_id, claim["claim_token"], success=True)
    row = next(row for row in list_reminders(user_id) if row["id"] == reminder_id)
    assert row["status"] == "cancelled"


def test_disabled_preferences_suppress_due_reminders(test_db, user_id):
    event_at = datetime.now(timezone.utc) + timedelta(days=1)
    task_id = create_task(user_id, "Muted", event_at.date().isoformat(), deadline_at=iso(event_at))
    remind_at = datetime.now(timezone.utc) + timedelta(seconds=2)
    reminder_id = create_reminder(user_id, iso(remind_at), task_id=task_id)
    update_preferences(user_id, enabled=False)
    assert claim_due_reminders(user_id, now=remind_at + timedelta(seconds=1)) == []
    row = next(row for row in list_reminders(user_id) if row["id"] == reminder_id)
    assert row["status"] == "pending"


def test_legacy_date_only_task_reminder_remains_supported(test_db, user_id):
    task_id = create_task(user_id, "Legacy date-only", "2099-01-01")
    reminder_id = create_reminder(user_id, "2098-12-31T10:00:00", task_id=task_id)
    row = next(row for row in list_reminders(user_id) if row["id"] == reminder_id)
    assert row["status"] == "pending"
    assert row["event_at"] is None
    assert row["offset_seconds"] is None


def test_reminder_more_than_one_poll_interval_late_is_skipped(test_db, user_id):
    event_at = datetime.now(timezone.utc) + timedelta(days=1)
    task_id = create_task(user_id, "Late poll", event_at.date().isoformat(), deadline_at=iso(event_at))
    remind_at = datetime.now(timezone.utc) + timedelta(seconds=2)
    reminder_id = create_reminder(user_id, iso(remind_at), task_id=task_id)
    claimed = claim_due_reminders(user_id, now=remind_at + timedelta(seconds=31))
    assert claimed == []
    row = next(row for row in list_reminders(user_id) if row["id"] == reminder_id)
    assert row["status"] == "skipped"
    assert "passed" in list_notices(user_id)[0]["message"]


def test_category_preference_suppresses_only_selected_reminder_type(test_db, user_id):
    now = datetime.now(timezone.utc)
    task_event = now + timedelta(days=1)
    task_id = create_task(user_id, "Deadline muted", task_event.date().isoformat(), deadline_at=iso(task_event))
    remind_at = now + timedelta(seconds=2)
    task_reminder = create_reminder(user_id, iso(remind_at), task_id=task_id)
    session_date = (now + timedelta(days=2)).date().isoformat()
    session_id = schedule_study_session(user_id, session_date, "10:00", "11:00")
    session_event = now + timedelta(days=2, hours=10)
    session_reminder = create_reminder(
        user_id, iso(remind_at), session_id=session_id, event_at=iso(session_event)
    )
    update_preferences(user_id, enabled=True, deadline_enabled=False, session_enabled=True)
    claimed = claim_due_reminders(user_id, now=remind_at + timedelta(seconds=1))
    assert [item["id"] for item in claimed] == [session_reminder]
    rows = {row["id"]: row for row in list_reminders(user_id)}
    assert rows[task_reminder]["status"] == "pending"
    assert rows[session_reminder]["status"] == "delivering"


def test_reminder_database_migration_preserves_legacy_rows_and_foreign_keys(tmp_path, monkeypatch):
    import sqlite3
    from Data_Access import database

    path = tmp_path / "reminder-legacy.db"
    connection = sqlite3.connect(path)
    connection.executescript("""
        CREATE TABLE users (id INTEGER PRIMARY KEY, email TEXT, password_hash TEXT, role TEXT);
        CREATE TABLE tasks (id INTEGER PRIMARY KEY, user_id INTEGER, title TEXT, UNIQUE(id,user_id));
        CREATE TABLE study_sessions (id INTEGER PRIMARY KEY, user_id INTEGER, session_date TEXT, start_time TEXT, end_time TEXT);
        CREATE TABLE reminders (id INTEGER PRIMARY KEY, user_id INTEGER, task_id INTEGER, remind_at TEXT,
            status TEXT DEFAULT 'pending', message TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
        INSERT INTO users VALUES (1, 'legacy@example.com', 'hash', 'Registered User');
        INSERT INTO tasks VALUES (2, 1, 'Legacy task');
        INSERT INTO reminders (id,user_id,task_id,remind_at,message)
            VALUES (3,1,2,'2099-01-01T09:00:00','keep me');
    """)
    connection.commit()
    connection.close()
    monkeypatch.setattr(database, "DATABASE_PATH", path)
    database.init_db()
    with database.connection_scope() as db:
        row = db.execute("SELECT id,user_id,task_id,event_type,message,status FROM reminders WHERE id=3").fetchone()
        assert tuple(row) == (3, 1, 2, "deadline", "keep me", "pending")
        assert db.execute("PRAGMA foreign_key_check").fetchall() == []


def test_deadline_reschedule_invalidates_an_in_flight_claim(test_db, user_id):
    register_event_handlers()
    old_event = datetime.now(timezone.utc) + timedelta(days=2)
    task_id = create_task(user_id, "Reschedule while claimed", old_event.date().isoformat(), deadline_at=iso(old_event))
    remind_at = datetime.now(timezone.utc) + timedelta(seconds=2)
    reminder_id = create_reminder(user_id, iso(remind_at), task_id=task_id)
    claim = claim_due_reminders(user_id, now=remind_at + timedelta(seconds=1))[0]
    new_event = old_event + timedelta(days=1)
    update_task_deadline(user_id, task_id, iso(new_event))
    Events.process_pending_events()
    assert not complete_delivery(user_id, reminder_id, claim["claim_token"], success=True)
    row = next(row for row in list_reminders(user_id) if row["id"] == reminder_id)
    assert row["status"] == "pending"
    assert row["event_at"] == iso(new_event)


def test_expired_claim_can_be_retried_without_duplicate_claims(test_db, user_id):
    event_at = datetime.now(timezone.utc) + timedelta(days=1)
    task_id = create_task(user_id, "Tab closed", event_at.date().isoformat(), deadline_at=iso(event_at))
    remind_at = datetime.now(timezone.utc) + timedelta(seconds=2)
    reminder_id = create_reminder(user_id, iso(remind_at), task_id=task_id)
    first = claim_due_reminders(user_id, now=remind_at + timedelta(seconds=1))[0]
    second = claim_due_reminders(user_id, now=remind_at + timedelta(seconds=32))
    assert [item["id"] for item in second] == [reminder_id]
    assert second[0]["claim_token"] != first["claim_token"]


def test_event_polling_can_be_scoped_to_authenticated_user(test_db, user_id):
    register_event_handlers()
    with test_db.connection_scope() as db:
        other_id = db.execute(
            "INSERT INTO users (email,password_hash,role) VALUES (?,?,?)",
            ("s09-event-other@example.com", "hash", "Registered User"),
        ).lastrowid
    from Events import publish_event, get_event
    own_event = publish_event("task.completion_changed", user_id, {"task_id": 999, "new_status": "incomplete"})
    other_event = publish_event("task.completion_changed", other_id, {"task_id": 998, "new_status": "incomplete"})
    Events.process_pending_events(user_id=user_id)
    assert get_event(own_event)["status"] == "processed"
    assert get_event(other_event)["status"] == "pending"


def test_completed_task_does_not_cancel_linked_session_reminders_deferred_oq41(test_db, user_id):
    register_event_handlers()
    task_event = datetime.now(timezone.utc) + timedelta(days=2)
    task_id = create_task(user_id, "Task with session", task_event.date().isoformat(), deadline_at=iso(task_event))
    session_date = (datetime.now(timezone.utc) + timedelta(days=2)).date().isoformat()
    session_id = schedule_study_session(user_id, session_date, "10:00", "11:00", task_id=task_id)
    session_event = datetime.now(timezone.utc) + timedelta(days=2, hours=10)
    reminder_id = create_reminder(
        user_id, iso(session_event - timedelta(hours=1)), session_id=session_id, event_at=iso(session_event)
    )
    transition_task_status(user_id, task_id, "completed")
    Events.process_pending_events()
    row = next(row for row in list_reminders(user_id) if row["id"] == reminder_id)
    assert row["status"] == "pending"
