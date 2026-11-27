"""Event publication/consumption foundation (plan S01).

PROVISIONAL pending G-01 (event mechanism) and G-12 (retry interval and
maximum attempts). This is a small database-backed, in-application mechanism:
no broker, no network protocol, no separate service. It is S01 foundation
infrastructure, not a business module, and has NO consumers from other
slices. AGENTS.md section 10 requires human approval for the mechanism.

Guarantees:
- ``publish_event`` can join the caller's transaction, so a rejected
  operation commits no event.
- Every event has a unique ``event_id`` (UUID4).
- A handler is applied at most once per (event, consumer) through the
  ``processed_events`` table.
- Failures store ``last_error``, count attempts, and become ``failed`` after
  ``EVENT_MAX_ATTEMPTS``.
- An event with no registered handler stays ``pending`` (nothing is lost
  before consumer slices exist).
"""
from datetime import datetime, timedelta, timezone
import uuid

from Data_Access import event_store
from Data_Access.database import connection_scope

# PROVISIONAL pending G-12: retry interval and maximum attempts are undecided.
EVENT_RETRY_INTERVAL_SECONDS = 60
EVENT_MAX_ATTEMPTS = 3

_HANDLERS = {}  # event_type -> list of (consumer, callable)


def register_handler(event_type, consumer, fn):
    """Register ``fn(event_dict)`` for ``event_type`` under a consumer name."""
    handlers = _HANDLERS.setdefault(event_type, [])
    if any(name == consumer for name, _ in handlers):
        raise ValueError(f"Consumer {consumer!r} is already registered for {event_type!r}.")
    handlers.append((consumer, fn))


def clear_handlers():
    """Remove all handlers (used by tests)."""
    _HANDLERS.clear()


def publish_event(event_type, user_id, payload=None, *, db=None):
    """Record a new pending event and return its unique event_id.

    Pass the caller's open connection as ``db`` to publish in the same
    transaction as the state change.
    """
    if not event_type or not user_id:
        raise ValueError("event_type and user_id are required.")
    event_id = uuid.uuid4().hex
    if db is not None:
        event_store.insert_event(db, event_id, event_type, user_id, payload or {})
    else:
        with connection_scope() as own_db:
            event_store.insert_event(own_db, event_id, event_type, user_id, payload or {})
    return event_id


def list_events(user_id=None, status=None):
    with connection_scope() as db:
        return event_store.list_events(db, user_id=user_id, status=status)


def get_event(event_id):
    with connection_scope() as db:
        return event_store.get_event(db, event_id)


def process_pending_events(max_attempts=None, retry_interval_seconds=None, now=None, user_id=None):
    """Deliver due pending events, optionally scoped to one authenticated user."""
    max_attempts = EVENT_MAX_ATTEMPTS if max_attempts is None else max_attempts
    interval = EVENT_RETRY_INTERVAL_SECONDS if retry_interval_seconds is None else retry_interval_seconds
    current = now or datetime.now(timezone.utc)
    summary = {"processed": 0, "retry_scheduled": 0, "failed": 0, "skipped_no_handler": 0}

    with connection_scope() as db:
        due = event_store.list_due_pending_events(db, current.isoformat(), user_id=user_id)

    for event in due:
        handlers = _HANDLERS.get(event["event_type"], [])
        if not handlers:
            summary["skipped_no_handler"] += 1
            continue
        error = None
        for consumer, fn in handlers:
            with connection_scope() as db:
                if event_store.is_handled(db, event["event_id"], consumer):
                    continue
            try:
                fn(event)
            except Exception as exc:  # handler failures are logged, not raised
                error = f"{consumer}: {type(exc).__name__}: {exc}"
                break
            with connection_scope() as db:
                event_store.mark_handled(db, event["event_id"], consumer)
        with connection_scope() as db:
            if error is None:
                event_store.mark_processed(db, event["event_id"])
                summary["processed"] += 1
            else:
                next_at = (current + timedelta(seconds=interval)).isoformat()
                event_store.record_failure(db, event["event_id"], error, max_attempts, next_at)
                if event_store.get_event(db, event["event_id"])["status"] == "failed":
                    summary["failed"] += 1
                else:
                    summary["retry_scheduled"] += 1
    return summary


__all__ = [
    "publish_event", "register_handler", "clear_handlers", "process_pending_events",
    "list_events", "get_event", "EVENT_RETRY_INTERVAL_SECONDS", "EVENT_MAX_ATTEMPTS",
]
