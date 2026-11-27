"""Public availability and scheduled-study-session service interface."""
from Data_Access.database import connection_scope
from Domain_Rules import DomainRuleError, validate_deadline, validate_day_of_week, validate_time_range
from Task_Management import get_task


def set_availability(user_id, day_of_week, start_time, end_time):
    if not user_id:
        raise DomainRuleError("An authenticated user_id is required.")
    day = validate_day_of_week(day_of_week)
    start, end = validate_time_range(start_time, end_time)
    with connection_scope() as db:
        cursor = db.execute(
            "INSERT INTO availability (user_id, day_of_week, start_time, end_time) VALUES (?, ?, ?, ?)",
            (user_id, day, start, end),
        )
        return cursor.lastrowid


def list_availability(user_id):
    with connection_scope() as db:
        rows = db.execute(
            "SELECT id, user_id, day_of_week, start_time, end_time, created_at "
            "FROM availability WHERE user_id = ? ORDER BY day_of_week, start_time", (user_id,)
        ).fetchall()
    return [dict(row) for row in rows]


def schedule_study_session(user_id, session_date, start_time, end_time, task_id=None, notes=None):
    if not user_id:
        raise DomainRuleError("An authenticated user_id is required.")
    clean_date = validate_deadline(session_date)
    start, end = validate_time_range(start_time, end_time)
    if task_id is not None and get_task(user_id, task_id) is None:
        raise DomainRuleError("The task does not exist for this user.")
    with connection_scope() as db:
        cursor = db.execute(
            "INSERT INTO study_sessions (user_id, task_id, session_date, start_time, end_time, notes) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, task_id, clean_date, start, end, notes),
        )
        return cursor.lastrowid


def list_study_sessions(user_id):
    with connection_scope() as db:
        rows = db.execute(
            "SELECT id, user_id, task_id, session_date, start_time, end_time, status, notes, created_at "
            "FROM study_sessions WHERE user_id = ? ORDER BY session_date, start_time", (user_id,)
        ).fetchall()
    return [dict(row) for row in rows]


__all__ = ["set_availability", "list_availability", "schedule_study_session", "list_study_sessions"]
