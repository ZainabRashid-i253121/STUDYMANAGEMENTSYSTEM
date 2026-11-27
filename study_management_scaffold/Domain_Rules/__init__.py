"""Shared domain validation and state-transition rules."""
from datetime import date, datetime, timezone
import re

MAX_TASK_TITLE_LENGTH = 200
MAX_COURSE_LENGTH = 100
# FR-13 / plan S03: a task is either Completed or Incomplete.
TASK_STATUSES = frozenset({"incomplete", "completed"})
REMINDER_STATUSES = frozenset({"pending", "delivering", "delivered", "dismissed", "cancelled", "skipped"})
ALLOWED_TASK_TRANSITIONS = {
    "incomplete": frozenset({"completed"}),
    "completed": frozenset({"incomplete"}),
}
MIN_PASSWORD_LENGTH = 8


class DomainRuleError(ValueError):
    """Raised when an operation violates a business/domain invariant."""


def validate_task_title(title):
    if not isinstance(title, str) or not title.strip():
        raise DomainRuleError("Task title is required.")
    if len(title.strip()) > MAX_TASK_TITLE_LENGTH:
        raise DomainRuleError(f"Task title must be at most {MAX_TASK_TITLE_LENGTH} characters.")
    return title.strip()


def validate_deadline(deadline):
    if isinstance(deadline, date):
        return deadline.isoformat()
    if not isinstance(deadline, str) or not deadline.strip():
        raise DomainRuleError("A valid deadline is required (YYYY-MM-DD).")
    try:
        parsed = date.fromisoformat(deadline.strip())
    except ValueError as exc:
        raise DomainRuleError("Deadline must be a valid date in YYYY-MM-DD format.") from exc
    return parsed.isoformat()


def validate_optional_deadline(deadline):
    """Deadline may be missing (FR-02: tasks without deadlines stay visible).

    ``None`` or a blank string means "no deadline" and returns ``None``.
    Any non-blank value must still be a valid ISO date.
    """
    if deadline is None or (isinstance(deadline, str) and not deadline.strip()):
        return None
    return validate_deadline(deadline)


def validate_task_status(status):
    if status not in TASK_STATUSES:
        raise DomainRuleError(f"Invalid task status: {status!r}.")
    return status


def validate_status_transition(current_status, new_status):
    validate_task_status(current_status)
    validate_task_status(new_status)
    if current_status == "completed" and new_status == "completed":
        raise DomainRuleError("An already completed task cannot be completed again.")
    if current_status == "incomplete" and new_status == "incomplete":
        raise DomainRuleError("An already incomplete task cannot be marked incomplete again.")
    if new_status not in ALLOWED_TASK_TRANSITIONS[current_status]:
        raise DomainRuleError(f"Task status cannot change from {current_status} to {new_status}.")
    return new_status


def validate_time_range(start_time, end_time):
    """Validate strict 24-hour HH:MM values and start < end; return normalized pair."""
    pattern = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    if not isinstance(start_time, str) or not pattern.fullmatch(start_time):
        raise DomainRuleError("Start time must use valid HH:MM format.")
    if not isinstance(end_time, str) or not pattern.fullmatch(end_time):
        raise DomainRuleError("End time must use valid HH:MM format.")
    if start_time >= end_time:
        raise DomainRuleError("Start time must be earlier than end time.")
    return start_time, end_time


def validate_day_of_week(day_of_week):
    if isinstance(day_of_week, bool) or not isinstance(day_of_week, int) or not 0 <= day_of_week <= 6:
        raise DomainRuleError("day_of_week must be an integer from 0 (Monday) to 6 (Sunday).")
    return day_of_week


def validate_iso_datetime(value):
    """Validate an ISO-8601 date/time string and return its normalized form."""
    if not isinstance(value, str) or not value.strip():
        raise DomainRuleError("remind_at must be a valid ISO date/time.")
    candidate = value.strip()
    try:
        parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DomainRuleError("remind_at must be a valid ISO date/time.") from exc
    if "T" not in candidate and " " not in candidate:
        raise DomainRuleError("remind_at must include both a date and a time.")
    return parsed.isoformat()



def validate_deadline_datetime(value):
    """Validate an ISO-8601 timestamp with an explicit UTC offset; return UTC ISO form.

    Date-only legacy deadlines are intentionally handled by validate_optional_deadline
    and are not assigned an invented time or timezone.
    """
    if not isinstance(value, str) or not value.strip():
        raise DomainRuleError("Deadline must be an ISO-8601 date/time with a timezone offset.")
    candidate = value.strip()
    if "T" not in candidate:
        raise DomainRuleError("Deadline must include both a date and time.")
    try:
        parsed = datetime.fromisoformat(candidate.replace("Z", "+00:00"))
    except ValueError as exc:
        raise DomainRuleError("Deadline must be a valid ISO-8601 date/time.") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise DomainRuleError("Deadline must include an explicit timezone offset.")
    return parsed.astimezone(timezone.utc).isoformat()


def identify_deadline_conflicts(tasks):
    """Return task IDs whose timezone-normalized deadline instant is shared.

    Only timestamp deadlines participate. Legacy date-only and missing deadlines
    remain unchanged and are not assigned an artificial time.
    """
    from collections import defaultdict

    by_instant = defaultdict(list)
    for task in tasks:
        value = task.get("deadline_at")
        if value is None:
            continue
        normalized = validate_deadline_datetime(value)
        by_instant[normalized].append(task["id"])
    return {task_id for ids in by_instant.values() if len(ids) > 1 for task_id in ids}


def validate_reminder_status(status):
    if status not in REMINDER_STATUSES:
        raise DomainRuleError(f"Invalid reminder status: {status!r}.")
    return status


def validate_course(course):
    """Course is optional; blank values become None."""
    if course is None:
        return None
    if not isinstance(course, str):
        raise DomainRuleError("Course must be text.")
    cleaned = course.strip()
    if not cleaned:
        return None
    if len(cleaned) > MAX_COURSE_LENGTH:
        raise DomainRuleError(f"Course must be at most {MAX_COURSE_LENGTH} characters.")
    return cleaned


def validate_email(email):
    """Return the normalized (trimmed, lower-case) email or raise DomainRuleError."""
    normalized = (email or "").strip().lower()
    if not normalized or "@" not in normalized:
        raise DomainRuleError("Enter a valid email address.")
    return normalized


def validate_password(password):
    """Return the password unchanged or raise DomainRuleError if it is too short."""
    if len(password or "") < MIN_PASSWORD_LENGTH:
        raise DomainRuleError(
            f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."
        )
    return password


__all__ = [
    "DomainRuleError", "validate_task_title", "validate_deadline", "validate_optional_deadline",
    "validate_email", "validate_password", "validate_task_status",
    "validate_status_transition", "validate_time_range", "validate_day_of_week",
    "validate_iso_datetime", "validate_reminder_status", "validate_course",
]
