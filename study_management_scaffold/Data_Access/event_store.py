"""SQL for the in-application event records (S01 foundation).

PROVISIONAL pending G-01 (event mechanism) and G-12 (retry policy).
All event SQL lives here so that the Events module contains no SQL.
Every function takes an open connection so callers control the transaction.
"""
import json
from datetime import datetime, timezone


def _now():
    return datetime.now(timezone.utc).isoformat()


def insert_event(db, event_id, event_type, user_id, payload):
    db.execute(
        "INSERT INTO events (event_id, event_type, user_id, payload) VALUES (?, ?, ?, ?)",
        (event_id, event_type, user_id, json.dumps(payload, sort_keys=True)),
    )


def get_event(db, event_id):
    row = db.execute("SELECT * FROM events WHERE event_id = ?", (event_id,)).fetchone()
    return _decode(row)


def list_events(db, user_id=None, status=None):
    sql, params = "SELECT * FROM events WHERE 1 = 1", []
    if user_id is not None:
        sql += " AND user_id = ?"
        params.append(user_id)
    if status is not None:
        sql += " AND status = ?"
        params.append(status)
    sql += " ORDER BY id"
    return [_decode(row) for row in db.execute(sql, params).fetchall()]


def list_due_pending_events(db, now_iso, user_id=None):
    sql = (
        "SELECT * FROM events WHERE status = 'pending' "
        "AND (next_attempt_at IS NULL OR next_attempt_at <= ?)"
    )
    params = [now_iso]
    if user_id is not None:
        sql += " AND user_id = ?"
        params.append(user_id)
    sql += " ORDER BY id"
    rows = db.execute(sql, params).fetchall()
    return [_decode(row) for row in rows]


def is_handled(db, event_id, consumer):
    return db.execute(
        "SELECT 1 FROM processed_events WHERE event_id = ? AND consumer = ?",
        (event_id, consumer),
    ).fetchone() is not None


def mark_handled(db, event_id, consumer):
    db.execute(
        "INSERT OR IGNORE INTO processed_events (event_id, consumer) VALUES (?, ?)",
        (event_id, consumer),
    )


def mark_processed(db, event_id):
    db.execute(
        "UPDATE events SET status = 'processed', processed_at = ?, last_error = NULL "
        "WHERE event_id = ?",
        (_now(), event_id),
    )


def record_failure(db, event_id, error_text, max_attempts, next_attempt_iso):
    """Increment attempts, store the error, and mark failed once attempts run out."""
    db.execute(
        "UPDATE events SET attempts = attempts + 1, last_error = ?, next_attempt_at = ? "
        "WHERE event_id = ?",
        (error_text, next_attempt_iso, event_id),
    )
    db.execute(
        "UPDATE events SET status = 'failed' WHERE event_id = ? AND attempts >= ?",
        (event_id, max_attempts),
    )


def _decode(row):
    if row is None:
        return None
    data = dict(row)
    data["payload"] = json.loads(data["payload"])
    return data
