"""Public staged-import interface. Imported data is not a task until accepted."""
import json

from Data_Access.database import connection_scope
from Domain_Rules import validate_course, validate_deadline, validate_deadline_datetime, validate_task_title
from Task_Management import create_task, update_task_deadline


def stage_import(user_id, source, title, deadline, course=None):
    if not user_id:
        raise ValueError("An authenticated user_id is required.")
    if not source or not str(source).strip():
        raise ValueError("Import source is required.")
    clean_title = validate_task_title(title)
    if isinstance(deadline, str) and "T" in deadline:
        clean_deadline_at = validate_deadline_datetime(deadline)
        clean_deadline = clean_deadline_at[:10]
    else:
        clean_deadline = validate_deadline(deadline)
        clean_deadline_at = None
    clean_course = validate_course(course)
    with connection_scope() as db:
        cursor = db.execute(
            "INSERT INTO staged_imports (user_id, source, title, course, deadline, deadline_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, str(source).strip(), clean_title, clean_course, clean_deadline, clean_deadline_at),
        )
        import_id = cursor.lastrowid
        db.execute(
            "INSERT INTO sync_logs (user_id, source, outcome, details) VALUES (?, ?, ?, ?)",
            (user_id, str(source).strip(), "staged", json.dumps({"import_id": import_id})),
        )
    return import_id


def list_staged_imports(user_id, status="staged"):
    with connection_scope() as db:
        rows = db.execute(
            "SELECT id, user_id, source, title, course, deadline, deadline_at, status, accepted_task_id, created_at "
            "FROM staged_imports WHERE user_id = ? AND status = ? ORDER BY id", (user_id, status)
        ).fetchall()
    return [dict(row) for row in rows]


def accept_staged_import(user_id, import_id):
    """Accept an import exactly once, even if callers retry or race.

    Task_Management enforces a unique (user_id, source_import_id) key. Thus the
    task creation call is idempotent; the conditional import update and log
    insertion ensure only one caller records the accepted transition.
    """
    with connection_scope() as db:
        row = db.execute(
            "SELECT id, source, title, course, deadline, deadline_at, status, accepted_task_id "
            "FROM staged_imports WHERE id = ? AND user_id = ?", (import_id, user_id)
        ).fetchone()
    if row is None:
        return None
    if row["status"] == "accepted":
        return row["accepted_task_id"]
    if row["status"] != "staged":
        return None

    # Keep task creation behind Task_Management's public API.
    task_id = create_task(
        user_id, row["title"], row["deadline"], row["course"],
        source_import_id=import_id, deadline_at=row["deadline_at"],
    )

    with connection_scope() as db:
        cursor = db.execute(
            "UPDATE staged_imports SET status = 'accepted', accepted_task_id = ? "
            "WHERE id = ? AND user_id = ? AND status = 'staged'",
            (task_id, import_id, user_id),
        )
        if cursor.rowcount == 1:
            db.execute(
                "INSERT INTO sync_logs (user_id, source, outcome, details) VALUES (?, ?, ?, ?)",
                (user_id, row["source"], "accepted",
                 json.dumps({"import_id": import_id, "task_id": task_id})),
            )
        else:
            # Another caller completed the state transition after our initial read.
            accepted = db.execute(
                "SELECT accepted_task_id FROM staged_imports WHERE id = ? AND user_id = ? AND status = 'accepted'",
                (import_id, user_id),
            ).fetchone()
            if accepted is not None:
                return accepted["accepted_task_id"]
    return task_id


def update_imported_task_deadline(user_id, task_id, deadline_at):
    """Apply a deadline timestamp after S06 has matched an imported task.

    This is only the integration hook; source selection, matching, and update
    discovery remain outside S04 and are not implemented here.
    """
    return update_task_deadline(user_id, task_id, deadline_at)


def record_sync_result(user_id, source, outcome, details=None):
    with connection_scope() as db:
        cursor = db.execute(
            "INSERT INTO sync_logs (user_id, source, outcome, details) VALUES (?, ?, ?, ?)",
            (user_id, source, outcome, details),
        )
        return cursor.lastrowid


__all__ = ["stage_import", "list_staged_imports", "accept_staged_import", "update_imported_task_deadline", "record_sync_result"]
