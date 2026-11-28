"""Public task service interface. Other modules call these functions only."""
from datetime import datetime, timezone
import sqlite3

import Events
from Data_Access.database import connection_scope
from Domain_Rules import (
    validate_course, validate_optional_deadline, validate_status_transition,
    validate_task_title, validate_task_status, validate_deadline_datetime,
    identify_deadline_conflicts, validate_study_duration_minutes,
)

TASK_COLUMNS = (
    "id, user_id, title, course, deadline, deadline_at, study_duration_minutes, "
    "status, completed_at, created_at"
)


def create_task(user_id, title, deadline=None, course=None, *, source_import_id=None, deadline_at=None):
    """Create a task; a missing deadline is allowed (FR-02).

    source_import_id makes external-import acceptance idempotent.
    """
    if not user_id:
        raise ValueError("An authenticated user_id is required.")
    clean_title = validate_task_title(title)
    clean_deadline = validate_optional_deadline(deadline)
    clean_deadline_at = validate_deadline_datetime(deadline_at) if deadline_at is not None else None
    if clean_deadline_at is not None:
        utc_date = clean_deadline_at[:10]
        if clean_deadline is not None and clean_deadline != utc_date:
            raise ValueError("deadline date must match the UTC date of deadline_at.")
        clean_deadline = utc_date
    clean_course = validate_course(course)
    try:
        with connection_scope() as db:
            cursor = db.execute(
                "INSERT INTO tasks (user_id, title, course, deadline, deadline_at, source_import_id) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, clean_title, clean_course, clean_deadline, clean_deadline_at, source_import_id),
            )
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        # A concurrent caller may already have created this import's task.
        if source_import_id is not None:
            with connection_scope() as db:
                existing = db.execute(
                    "SELECT id FROM tasks WHERE user_id = ? AND source_import_id = ?",
                    (user_id, source_import_id),
                ).fetchone()
            if existing is not None:
                return existing["id"]
        raise


def get_task(user_id, task_id):
    """Fetch one task only when it belongs to user_id."""
    with connection_scope() as db:
        row = db.execute(
            f"SELECT {TASK_COLUMNS} FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id)
        ).fetchone()
    if row is None:
        return None
    task = dict(row)
    task["deadline_conflict"] = task["id"] in _conflicting_task_ids(user_id)
    return task


def _conflicting_task_ids(user_id, db=None):
    """Ask Domain Rules to identify conflicts within one user's tasks."""
    if db is not None:
        rows = db.execute(
            "SELECT id, deadline_at FROM tasks WHERE user_id = ?", (user_id,)
        ).fetchall()
        return identify_deadline_conflicts([dict(row) for row in rows])
    with connection_scope() as connection:
        rows = connection.execute(
            "SELECT id, deadline_at FROM tasks WHERE user_id = ?", (user_id,)
        ).fetchall()
    return identify_deadline_conflicts([dict(row) for row in rows])


def list_tasks(user_id, status=None):
    """List the user's tasks, optionally filtered by completion status.

    Tasks with a deadline come first (earliest first); tasks without a
    deadline are listed after them but remain visible (FR-02).
    """
    sql = f"SELECT {TASK_COLUMNS} FROM tasks WHERE user_id = ?"
    params = [user_id]
    if status is not None:
        validate_task_status(status)
        sql += " AND status = ?"
        params.append(status)
    sql += " ORDER BY deadline IS NULL, deadline, id"
    with connection_scope() as db:
        rows = db.execute(sql, params).fetchall()
    tasks = [dict(row) for row in rows]
    conflicts = identify_deadline_conflicts(tasks)
    for task in tasks:
        task["deadline_conflict"] = task["id"] in conflicts
    return tasks


def update_task_deadline(user_id, task_id, deadline_at):
    """Update an owned task's imported deadline timestamp.

    External Integration is the intended caller (S06 supplies the matched task).
    The timestamp is normalized to UTC and the change event is committed atomically.
    Returns None for a task not owned by the supplied user.
    """
    if not user_id:
        raise ValueError("An authenticated user_id is required.")
    normalized = validate_deadline_datetime(deadline_at)
    with connection_scope() as db:
        row = db.execute(
            "SELECT deadline, deadline_at FROM tasks WHERE id = ? AND user_id = ?",
            (task_id, user_id),
        ).fetchone()
        if row is None:
            return None
        old_deadline_at = row["deadline_at"]
        old_deadline = row["deadline"]
        if old_deadline_at == normalized:
            return get_task(user_id, task_id)
        # Keep the legacy date field populated for existing S03/S05 consumers.
        db.execute(
            "UPDATE tasks SET deadline = ?, deadline_at = ? WHERE id = ? AND user_id = ?",
            (normalized[:10], normalized, task_id, user_id),
        )
        conflicts = _conflicting_task_ids(user_id, db=db)
        Events.publish_event(
            "task.deadline_changed", user_id,
            {"task_id": task_id, "old_deadline": old_deadline,
             "old_deadline_at": old_deadline_at, "new_deadline": normalized[:10],
             "new_deadline_at": normalized, "conflicting_task_ids": sorted(conflicts)},
            db=db,
        )
    return get_task(user_id, task_id)


def update_study_duration(user_id, task_id, study_duration_minutes):
    """Save a user's study-duration estimate on one of their tasks."""
    if not user_id:
        raise ValueError("An authenticated user_id is required.")
    duration = validate_study_duration_minutes(study_duration_minutes)
    with connection_scope() as db:
        cursor = db.execute(
            "UPDATE tasks SET study_duration_minutes = ? WHERE id = ? AND user_id = ?",
            (duration, task_id, user_id),
        )
        if cursor.rowcount == 0:
            return None
    return get_task(user_id, task_id)


def get_completion_summary(user_id):
    """Return task counts and completion percentage for one user."""
    if not user_id:
        raise ValueError("An authenticated user_id is required.")
    with connection_scope() as db:
        row = db.execute(
            """SELECT COUNT(*) AS total,
                SUM(CASE WHEN status = 'incomplete' THEN 1 ELSE 0 END) AS incomplete,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) AS completed
                FROM tasks WHERE user_id = ?""", (user_id,)
        ).fetchone()
    total = row["total"] or 0
    completed = row["completed"] or 0
    return {
        "total": total, "incomplete": row["incomplete"] or 0, "completed": completed,
        "completion_percentage": round((completed / total) * 100, 1) if total else 0.0,
    }


def _completed_at_for_status(new_status):
    """Completion date for a new status.

    PROVISIONAL pending G-08: what happens to the completion date when a
    completed task is reverted to Incomplete is undecided. Until the group
    decides, the date is cleared on reversion. Completing never changes the
    task's deadline (BR-06).
    """
    return datetime.now(timezone.utc).isoformat() if new_status == "completed" else None


def transition_task_status(user_id, task_id, new_status):
    """Mark a task completed or incomplete; None if it is not the user's task.

    A ``task.completion_changed`` event is recorded in the same transaction;
    if Domain Rules rejects the change nothing (task or event) is committed.
    """
    with connection_scope() as db:
        row = db.execute(
            "SELECT status FROM tasks WHERE id = ? AND user_id = ?", (task_id, user_id)
        ).fetchone()
        if row is None:
            return None
        current = row["status"]
        validate_status_transition(current, new_status)
        completed_at = _completed_at_for_status(new_status)
        db.execute(
            "UPDATE tasks SET status = ?, completed_at = ? WHERE id = ? AND user_id = ?",
            (new_status, completed_at, task_id, user_id),
        )
        Events.publish_event(
            "task.completion_changed", user_id,
            {"task_id": task_id, "old_status": current, "new_status": new_status,
             "completed_at": completed_at},
            db=db,
        )
    return get_task(user_id, task_id)


__all__ = [
    "create_task", "get_task", "list_tasks", "update_task_deadline",
    "update_study_duration", "transition_task_status", "get_completion_summary",
]
