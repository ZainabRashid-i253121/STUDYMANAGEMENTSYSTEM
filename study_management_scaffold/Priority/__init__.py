"""Task Priority services; Task Management remains the source of task data."""
from datetime import date

from Data_Access.database import connection_scope
from Task_Management import get_task, list_tasks


def _distance(task, reference):
    """Return deadline distance in calendar days, or None without a deadline."""
    if not task.get("deadline"):
        return None
    due = date.fromisoformat(task["deadline"])
    return {"task_id": task["id"], "deadline": due.isoformat(),
            "days_until_deadline": (due - reference).days}


def deadline_distance(user_id, task_id, as_of=None):
    """Return days until deadline for an owned task (negative means overdue)."""
    task = get_task(user_id, task_id)
    if task is None:
        return None
    reference = as_of or date.today()
    if isinstance(reference, str):
        reference = date.fromisoformat(reference)
    return _distance(task, reference)


def deadline_distances(user_id, as_of=None, *, tasks=None):
    """Return distances for a supplied task list, or fetch it once."""
    reference = as_of or date.today()
    if isinstance(reference, str):
        reference = date.fromisoformat(reference)
    owned_tasks = list_tasks(user_id) if tasks is None else tasks
    distances = {task["id"]: _distance(task, reference) for task in owned_tasks}
    return {task_id: distance for task_id, distance in distances.items() if distance is not None}


def _priority_for(task, reference):
    """Apply the human-approved calendar-day thresholds to one task."""
    deadline = task.get("deadline")
    if not deadline:
        return {
            "priority": "Low", "days_until_deadline": None,
            "priority_requires_review": False,
        }
    try:
        due = date.fromisoformat(deadline)
    except (TypeError, ValueError):
        return {
            "priority": "Undetermined", "days_until_deadline": None,
            "priority_requires_review": True,
        }
    days = (due - reference).days
    if days <= 3:
        priority = "High"
    elif days <= 7:
        priority = "Medium"
    else:
        priority = "Low"
    return {
        "priority": priority, "days_until_deadline": days,
        "priority_requires_review": False,
    }


def prioritize_tasks(user_id, as_of=None, *, tasks=None):
    """Return tasks enriched with owned, persisted priority and Domain Rules flags.

    Completed tasks are excluded. Conflict information is consumed from the
    Task Management service response; this module does not identify conflicts.
    """
    if not user_id:
        raise ValueError("An authenticated user_id is required.")
    reference = as_of or date.today()
    if isinstance(reference, str):
        reference = date.fromisoformat(reference)
    source_tasks = list_tasks(user_id) if tasks is None else tasks
    result = []
    with connection_scope() as db:
        for source in source_tasks:
            task = dict(source)
            if task.get("status") == "completed":
                db.execute(
                    "DELETE FROM task_priorities WHERE task_id = ? AND user_id = ?",
                    (task["id"], user_id),
                )
                task["priority"] = None
                task["priority_requires_review"] = False
                result.append(task)
                continue
            details = _priority_for(task, reference)
            db.execute(
                """INSERT INTO task_priorities
                   (task_id, user_id, priority, days_until_deadline, deadline, priority_requires_review)
                   VALUES (?, ?, ?, ?, ?, ?)
                   ON CONFLICT(task_id, user_id) DO UPDATE SET
                     priority = excluded.priority,
                     days_until_deadline = excluded.days_until_deadline,
                     deadline = excluded.deadline,
                     priority_requires_review = excluded.priority_requires_review,
                     updated_at = CURRENT_TIMESTAMP""",
                (task["id"], user_id, details["priority"], details["days_until_deadline"],
                 task.get("deadline"), int(details["priority_requires_review"])),
            )
            task.update(details)
            # This flag is produced by Domain Rules through Task Management.
            task["deadline_conflict"] = bool(task.get("deadline_conflict", False))
            result.append(task)
    return result


__all__ = ["deadline_distance", "deadline_distances", "prioritize_tasks"]
