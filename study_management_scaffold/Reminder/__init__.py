"""Reminder preferences, pending reminder lifecycle, and delivery coordination.

Reminder owns reminder records and delivery state. Task and Schedule records remain
owned by their respective modules; cross-module changes arrive through Events.
"""
from datetime import datetime, timedelta, timezone
import uuid

import Events
from Data_Access.database import connection_scope
from Domain_Rules import DomainRuleError, validate_deadline_datetime, validate_iso_datetime, validate_reminder_status
from Task_Management import get_task
from Schedule import list_study_sessions

POLL_INTERVAL_SECONDS = 30
CLAIM_LEASE_SECONDS = POLL_INTERVAL_SECONDS


def _utc_datetime(value):
    """Parse stored reminder times; new S09 writes are timezone-aware UTC."""
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _clean_instant(value, field_name, *, require_offset=False):
    if require_offset:
        try:
            return validate_deadline_datetime(value)
        except DomainRuleError as exc:
            raise DomainRuleError(f"{field_name} must include a timezone offset.") from exc
    return validate_iso_datetime(value)


def get_preferences(user_id):
    if not user_id:
        raise DomainRuleError("An authenticated user_id is required.")
    with connection_scope() as db:
        db.execute(
            "INSERT OR IGNORE INTO reminder_preferences (user_id) VALUES (?)", (user_id,)
        )
        row = db.execute(
            "SELECT user_id, enabled, deadline_enabled, session_enabled, updated_at "
            "FROM reminder_preferences WHERE user_id = ?", (user_id,)
        ).fetchone()
    return dict(row)


def update_preferences(user_id, *, enabled, deadline_enabled=True, session_enabled=True):
    if not user_id:
        raise DomainRuleError("An authenticated user_id is required.")
    values = (bool(enabled), bool(deadline_enabled), bool(session_enabled))
    with connection_scope() as db:
        db.execute(
            "INSERT INTO reminder_preferences (user_id, enabled, deadline_enabled, session_enabled) "
            "VALUES (?, ?, ?, ?) ON CONFLICT(user_id) DO UPDATE SET "
            "enabled=excluded.enabled, deadline_enabled=excluded.deadline_enabled, "
            "session_enabled=excluded.session_enabled, updated_at=CURRENT_TIMESTAMP",
            (user_id, *(int(value) for value in values)),
        )
    return get_preferences(user_id)


def _event_target(user_id, task_id, session_id, event_at):
    if task_id is not None and session_id is not None:
        raise DomainRuleError("A reminder can target a task deadline or a study session, not both.")
    if task_id is not None:
        task = get_task(user_id, task_id)
        if task is None:
            raise DomainRuleError("The task does not exist for this user.")
        if task["status"] == "completed":
            raise DomainRuleError("Completed tasks cannot receive deadline reminders.")
        target = task.get("deadline_at")
        if target is None:
            # Preserve the original S01 API for date-only legacy reminders. Such rows
            # cannot be automatically recalculated until a timestamp deadline exists.
            return "deadline", None
        return "deadline", _clean_instant(target, "The task deadline", require_offset=True)
    if session_id is not None:
        session_row = next(
            (item for item in list_study_sessions(user_id) if item["id"] == session_id), None
        )
        if session_row is None:
            raise DomainRuleError("The Scheduled Study Session does not exist for this user.")
        if session_row.get("status") != "scheduled":
            raise DomainRuleError("Only scheduled sessions can receive reminders.")
        if event_at is None:
            raise DomainRuleError("The session event time is required.")
        return "session", _clean_instant(event_at, "The session event time", require_offset=True)
    if event_at is not None:
        raise DomainRuleError("An event time requires a task or session target.")
    return "general", None


def _insert_notice(db, user_id, reminder_id, message):
    db.execute(
        "INSERT INTO reminder_notices (user_id, reminder_id, notice_type, message) "
        "VALUES (?, ?, 'skipped', ?)", (user_id, reminder_id, message)
    )


def create_reminder(user_id, remind_at, task_id=None, message=None, *, session_id=None, event_at=None):
    """Create a reminder for an owned deadline/session or a legacy general reminder."""
    if not user_id:
        raise DomainRuleError("An authenticated user_id is required.")
    if task_id is None and session_id is None:
        clean_remind_at = validate_iso_datetime(remind_at)
        event_type, clean_event_at, offset_seconds = "general", None, None
    else:
        clean_remind_at = _clean_instant(remind_at, "remind_at")
        event_type, clean_event_at = _event_target(user_id, task_id, session_id, event_at)
        if clean_event_at is not None:
            offset_seconds = int((_utc_datetime(clean_event_at) - _utc_datetime(clean_remind_at)).total_seconds())
            if offset_seconds <= 0:
                raise DomainRuleError("The reminder time must be before its event.")
        else:
            offset_seconds = None

    now = datetime.now(timezone.utc)
    is_past = _utc_datetime(clean_remind_at) <= now
    with connection_scope() as db:
        cursor = db.execute(
            "INSERT INTO reminders "
            "(user_id, task_id, session_id, event_type, remind_at, event_at, offset_seconds, status, message) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, task_id, session_id, event_type, clean_remind_at, clean_event_at,
             offset_seconds, "skipped" if is_past else "pending", message),
        )
        reminder_id = cursor.lastrowid
        if is_past:
            _insert_notice(db, user_id, reminder_id,
                           "A reminder time had already passed and was skipped.")
    return reminder_id


def list_reminders(user_id, status=None):
    if not user_id:
        raise DomainRuleError("An authenticated user_id is required.")
    sql = ("SELECT id, user_id, task_id, session_id, event_type, remind_at, event_at, "
           "offset_seconds, status, message, attempts, last_error, last_attempt_at, created_at "
           "FROM reminders WHERE user_id = ?")
    params = [user_id]
    if status is not None:
        clean_status = validate_reminder_status(status)
        sql += " AND status = ?"
        params.append(clean_status)
    sql += " ORDER BY remind_at, id"
    with connection_scope() as db:
        rows = db.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def update_reminder_status(user_id, reminder_id, status):
    clean_status = validate_reminder_status(status)
    # A late browser acknowledgment must never resurrect or overwrite cancellation.
    with connection_scope() as db:
        cursor = db.execute(
            "UPDATE reminders SET status = ?, updated_at = CURRENT_TIMESTAMP "
            "WHERE id = ? AND user_id = ? AND status IN ('pending', 'delivering')",
            (clean_status, reminder_id, user_id),
        )
        return cursor.rowcount == 1


def list_reminder_presets(user_id, event_type):
    """Return previously used offsets as user-specific reusable presets.

    No fixed preset durations are prescribed by the project documents.
    """
    if event_type not in {"deadline", "session"}:
        raise DomainRuleError("Unknown reminder event type.")
    with connection_scope() as db:
        rows = db.execute(
            "SELECT DISTINCT offset_seconds FROM reminders "
            "WHERE user_id = ? AND event_type = ? AND offset_seconds > 0 "
            "ORDER BY offset_seconds DESC", (user_id, event_type)
        ).fetchall()
    return [row["offset_seconds"] for row in rows]


def _handle_deadline_changed(event):
    payload = event["payload"]
    task_id = payload.get("task_id")
    new_event_at = payload.get("new_deadline_at")
    old_event_at = payload.get("old_deadline_at")
    if task_id is None or not new_event_at:
        return
    clean_event_at = _clean_instant(new_event_at, "The new task deadline", require_offset=True)
    clean_old_event_at = (
        _clean_instant(old_event_at, "The previous task deadline", require_offset=True)
        if old_event_at else None
    )
    now = datetime.now(timezone.utc)
    with connection_scope() as db:
        rows = db.execute(
            "SELECT id, remind_at, offset_seconds FROM reminders WHERE user_id = ? AND task_id = ? "
            "AND event_type = 'deadline' AND status IN ('pending', 'delivering')",
            (event["user_id"], task_id),
        ).fetchall()
        for row in rows:
            offset_seconds = row["offset_seconds"]
            if offset_seconds is None and clean_old_event_at is not None:
                offset_seconds = int((_utc_datetime(clean_old_event_at) - _utc_datetime(row["remind_at"])).total_seconds())
                if offset_seconds <= 0:
                    continue
            if offset_seconds is None:
                continue  # Date-only legacy deadline has no approved event time.
            new_remind_at = (_utc_datetime(clean_event_at) - timedelta(seconds=offset_seconds)).isoformat()
            if _utc_datetime(new_remind_at) <= now:
                db.execute(
                    "UPDATE reminders SET event_at = ?, remind_at = ?, offset_seconds = ?, status = 'skipped', "
                    "claim_token = NULL, claim_expires_at = NULL, updated_at = CURRENT_TIMESTAMP "
                    "WHERE id = ? AND status IN ('pending', 'delivering')",
                    (clean_event_at, new_remind_at, offset_seconds, row["id"]),
                )
                _insert_notice(db, event["user_id"], row["id"],
                               "A reminder became overdue after its event was rescheduled and was skipped.")
            else:
                db.execute(
                    "UPDATE reminders SET event_at = ?, remind_at = ?, offset_seconds = ?, status = 'pending', "
                    "last_attempt_at = NULL, claim_token = NULL, claim_expires_at = NULL, "
                    "updated_at = CURRENT_TIMESTAMP "
                    "WHERE id = ? AND status IN ('pending', 'delivering')",
                    (clean_event_at, new_remind_at, offset_seconds, row["id"]),
                )


def _handle_task_completion_changed(event):
    payload = event["payload"]
    if payload.get("new_status") != "completed" or payload.get("task_id") is None:
        return
    with connection_scope() as db:
        db.execute(
            "UPDATE reminders SET status = 'cancelled', claim_token = NULL, claim_expires_at = NULL, "
            "updated_at = CURRENT_TIMESTAMP WHERE user_id = ? AND task_id = ? "
            "AND event_type = 'deadline' AND status IN ('pending', 'delivering')",
            (event["user_id"], payload["task_id"]),
        )


def register_event_handlers():
    """Register Reminder consumers for the established Task Management events."""
    for event_type, consumer, handler in (
        ("task.deadline_changed", "reminder.deadline_updates", _handle_deadline_changed),
        ("task.completion_changed", "reminder.task_completion", _handle_task_completion_changed),
    ):
        try:
            Events.register_handler(event_type, consumer, handler)
        except ValueError:
            # create_app may be invoked more than once in a test or local process.
            pass


def claim_due_reminders(user_id, now=None, limit=50):
    """Atomically claim due reminders so concurrent tabs cannot deliver duplicates."""
    if not user_id:
        raise DomainRuleError("An authenticated user_id is required.")
    current = now or datetime.now(timezone.utc)
    current_iso = current.astimezone(timezone.utc).isoformat()
    late_before = (current - timedelta(seconds=POLL_INTERVAL_SECONDS)).astimezone(timezone.utc).isoformat()
    token_prefix = uuid.uuid4().hex
    with connection_scope() as db:
        pref = db.execute(
            "SELECT enabled FROM reminder_preferences WHERE user_id = ?", (user_id,)
        ).fetchone()
        if pref is not None and not pref["enabled"]:
            return []
        # A claim left by a tab that closed before acknowledgment becomes eligible again.
        db.execute(
            "UPDATE reminders SET status = 'pending', claim_token = NULL, claim_expires_at = NULL "
            "WHERE user_id = ? AND status = 'delivering' AND claim_expires_at <= ?",
            (user_id, current_iso),
        )
        # A reminder more than one polling interval late is skipped rather than sent stale.
        stale = db.execute(
            "SELECT id FROM reminders WHERE user_id = ? AND status = 'pending' "
            "AND remind_at < ? AND last_attempt_at IS NULL AND (event_at IS NULL OR event_at > ?)",
            (user_id, late_before, current_iso),
        ).fetchall()
        for row in stale:
            db.execute(
                "UPDATE reminders SET status = 'skipped', updated_at = CURRENT_TIMESTAMP "
                "WHERE id = ? AND status = 'pending'", (row["id"],)
            )
            _insert_notice(db, user_id, row["id"],
                           "A reminder time passed while notifications were unavailable; it was skipped.")
        # Do not deliver a reminder after its associated event has already happened.
        expired_event = db.execute(
            "SELECT id FROM reminders WHERE user_id = ? AND status = 'pending' "
            "AND remind_at <= ? AND event_at IS NOT NULL AND event_at <= ?",
            (user_id, current_iso, current_iso),
        ).fetchall()
        for row in expired_event:
            db.execute(
                "UPDATE reminders SET status = 'skipped', updated_at = CURRENT_TIMESTAMP "
                "WHERE id = ? AND status = 'pending'", (row["id"],)
            )
            _insert_notice(db, user_id, row["id"], "The event has already passed; its reminder was skipped.")
        due = db.execute(
            "SELECT id, event_type FROM reminders WHERE user_id = ? AND status = 'pending' "
            "AND remind_at <= ? AND (event_at IS NULL OR event_at > ?) "
            "ORDER BY remind_at, id LIMIT ?", (user_id, current_iso, current_iso, limit)
        ).fetchall()
        claimed = []
        for index, row in enumerate(due):
            category_column = (
                "deadline_enabled" if row["event_type"] == "deadline"
                else "session_enabled" if row["event_type"] == "session"
                else None
            )
            if pref is not None and category_column is not None:
                category = db.execute(
                    f"SELECT {category_column} AS enabled FROM reminder_preferences WHERE user_id = ?",
                    (user_id,),
                ).fetchone()
                if category is not None and not category["enabled"]:
                    continue
            token = f"{token_prefix}-{index}"
            expires = (current + timedelta(seconds=CLAIM_LEASE_SECONDS)).astimezone(timezone.utc).isoformat()
            cursor = db.execute(
                "UPDATE reminders SET status = 'delivering', claim_token = ?, claim_expires_at = ?, "
                "last_attempt_at = ?, updated_at = CURRENT_TIMESTAMP "
                "WHERE id = ? AND user_id = ? AND status = 'pending'",
                (token, expires, current_iso, row["id"], user_id),
            )
            if cursor.rowcount == 1:
                item = db.execute(
                    "SELECT id, user_id, task_id, session_id, event_type, remind_at, event_at, message, "
                    "attempts, claim_token FROM reminders WHERE id = ? AND user_id = ?",
                    (row["id"], user_id),
                ).fetchone()
                claimed.append(dict(item))
    return claimed


def complete_delivery(user_id, reminder_id, claim_token, *, success, error=None):
    """Complete a claimed delivery; failure remains retryable on the next poll."""
    with connection_scope() as db:
        if success:
            cursor = db.execute(
                "UPDATE reminders SET status = 'delivered', claim_token = NULL, claim_expires_at = NULL, "
                "last_error = NULL, updated_at = CURRENT_TIMESTAMP "
                "WHERE id = ? AND user_id = ? AND status = 'delivering' AND claim_token = ?",
                (reminder_id, user_id, claim_token),
            )
        else:
            cursor = db.execute(
                "UPDATE reminders SET status = 'pending', attempts = attempts + 1, last_error = ?, "
                "claim_token = NULL, claim_expires_at = NULL, updated_at = CURRENT_TIMESTAMP "
                "WHERE id = ? AND user_id = ? AND status = 'delivering' AND claim_token = ?",
                (str(error or "Notification delivery failed")[:1000], reminder_id, user_id, claim_token),
            )
    return cursor.rowcount == 1


def list_notices(user_id, *, include_dismissed=False):
    with connection_scope() as db:
        sql = "SELECT id, reminder_id, notice_type, message, dismissed, created_at FROM reminder_notices WHERE user_id = ?"
        if not include_dismissed:
            sql += " AND dismissed = 0"
        sql += " ORDER BY id DESC"
        rows = db.execute(sql, (user_id,)).fetchall()
    return [dict(row) for row in rows]


def dismiss_notice(user_id, notice_id):
    with connection_scope() as db:
        cursor = db.execute(
            "UPDATE reminder_notices SET dismissed = 1 WHERE id = ? AND user_id = ? AND dismissed = 0",
            (notice_id, user_id),
        )
    return cursor.rowcount == 1


__all__ = [
    "create_reminder", "list_reminders", "update_reminder_status", "get_preferences",
    "update_preferences", "list_reminder_presets", "register_event_handlers",
    "claim_due_reminders", "complete_delivery", "list_notices", "dismiss_notice",
    "POLL_INTERVAL_SECONDS",
]
