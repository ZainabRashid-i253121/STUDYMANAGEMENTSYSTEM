"""Event foundation tests (plan S01). PROVISIONAL pending G-01 / G-12."""
from datetime import datetime, timedelta, timezone

import pytest

import Events
from Events import process_pending_events, publish_event, register_handler


@pytest.fixture(autouse=True)
def clean_handlers():
    Events.clear_handlers()
    yield
    Events.clear_handlers()


def test_event_ids_are_unique(test_db, user_id):
    ids = {publish_event("demo.event", user_id, {"n": i}) for i in range(25)}
    assert len(ids) == 25
    assert len(Events.list_events(user_id)) == 25


def test_event_is_stored_pending_with_payload(test_db, user_id):
    event_id = publish_event("demo.event", user_id, {"k": "v"})
    event = Events.get_event(event_id)
    assert event["status"] == "pending" and event["attempts"] == 0
    assert event["payload"] == {"k": "v"} and event["user_id"] == user_id


def test_event_joins_callers_transaction_and_rolls_back(test_db, user_id):
    with pytest.raises(RuntimeError):
        with test_db.connection_scope() as db:
            publish_event("demo.event", user_id, {}, db=db)
            raise RuntimeError("operation rejected")
    assert Events.list_events(user_id) == []


def test_rejected_task_operation_commits_no_event(test_db, user_id):
    from Domain_Rules import DomainRuleError
    from Task_Management import create_task, transition_task_status
    task_id = create_task(user_id, "Once", "2099-01-01")
    transition_task_status(user_id, task_id, "completed")
    assert len(Events.list_events(user_id)) == 1
    with pytest.raises(DomainRuleError):
        transition_task_status(user_id, task_id, "completed")      # rejected by Domain Rules
    assert len(Events.list_events(user_id)) == 1                   # no extra event committed


def test_completion_change_publishes_event_in_same_transaction(test_db, user_id):
    from Task_Management import create_task, transition_task_status
    task_id = create_task(user_id, "Evented", "2099-01-01")
    assert Events.list_events(user_id) == []                       # creating publishes nothing
    transition_task_status(user_id, task_id, "completed")
    transition_task_status(user_id, task_id, "incomplete")
    events = Events.list_events(user_id)
    assert [e["event_type"] for e in events] == ["task.completion_changed"] * 2
    assert [e["payload"]["new_status"] for e in events] == ["completed", "incomplete"]
    assert events[0]["payload"]["task_id"] == task_id


def test_event_for_another_users_task_is_not_created(test_db, user_id):
    from Task_Management import create_task, transition_task_status
    with test_db.connection_scope() as db:
        other = db.execute("INSERT INTO users (email, password_hash, role) VALUES "
                           "('o@example.com', 'h', 'Registered User')").lastrowid
    task_id = create_task(other, "Not yours", "2099-01-01")
    assert transition_task_status(user_id, task_id, "completed") is None
    assert Events.list_events() == []


def test_handler_applies_once_even_if_processing_runs_twice(test_db, user_id):
    calls = []
    register_handler("demo.event", "consumer-a", lambda event: calls.append(event["event_id"]))
    event_id = publish_event("demo.event", user_id, {})
    first = process_pending_events()
    second = process_pending_events()
    assert calls == [event_id]
    assert first["processed"] == 1 and second["processed"] == 0
    assert Events.get_event(event_id)["status"] == "processed"


def test_already_handled_consumer_is_skipped_on_redelivery(test_db, user_id):
    """If consumer A succeeded but B failed, a retry must not re-run A."""
    calls = {"a": 0, "b": 0}
    def handler_a(event): calls["a"] += 1
    def handler_b(event):
        calls["b"] += 1
        if calls["b"] == 1:
            raise RuntimeError("temporary")
    register_handler("demo.event", "a", handler_a)
    register_handler("demo.event", "b", handler_b)
    event_id = publish_event("demo.event", user_id, {})
    now = datetime.now(timezone.utc)
    process_pending_events(now=now)
    process_pending_events(now=now + timedelta(hours=1))
    assert calls == {"a": 1, "b": 2}
    assert Events.get_event(event_id)["status"] == "processed"


def test_failure_is_logged_retried_then_marked_failed(test_db, user_id):
    def always_fails(event):
        raise ValueError("boom")
    register_handler("demo.event", "flaky", always_fails)
    event_id = publish_event("demo.event", user_id, {})
    now = datetime.now(timezone.utc)

    first = process_pending_events(max_attempts=2, retry_interval_seconds=60, now=now)
    event = Events.get_event(event_id)
    assert first["retry_scheduled"] == 1
    assert event["status"] == "pending" and event["attempts"] == 1
    assert "ValueError: boom" in event["last_error"]           # failure is logged

    # not due yet: the retry interval has not elapsed
    assert process_pending_events(max_attempts=2, now=now + timedelta(seconds=10))["failed"] == 0
    assert Events.get_event(event_id)["attempts"] == 1

    second = process_pending_events(max_attempts=2, retry_interval_seconds=60, now=now + timedelta(seconds=120))
    event = Events.get_event(event_id)
    assert second["failed"] == 1
    assert event["status"] == "failed" and event["attempts"] == 2
    assert "boom" in event["last_error"]

    # a failed event is not retried again
    assert process_pending_events(now=now + timedelta(hours=1)) == {
        "processed": 0, "retry_scheduled": 0, "failed": 0, "skipped_no_handler": 0}


def test_event_without_handler_stays_pending(test_db, user_id):
    event_id = publish_event("nobody.listens", user_id, {})
    summary = process_pending_events()
    assert summary["skipped_no_handler"] == 1
    assert Events.get_event(event_id)["status"] == "pending"


def test_duplicate_consumer_registration_is_rejected():
    register_handler("demo.event", "same", lambda e: None)
    with pytest.raises(ValueError):
        register_handler("demo.event", "same", lambda e: None)


def test_provisional_policy_constants_exist():
    assert Events.EVENT_MAX_ATTEMPTS >= 1 and Events.EVENT_RETRY_INTERVAL_SECONDS >= 0
