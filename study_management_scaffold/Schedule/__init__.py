"""Public availability and scheduled-study-session service interface."""
from datetime import date, timedelta

from Data_Access.database import (
    insert_availability,
    insert_study_session,
    insert_study_sessions,
    select_availability,
    select_study_sessions,
    update_availability as persist_availability_update,
)
from Domain_Rules import DomainRuleError, validate_deadline, validate_day_of_week, validate_time_range
from Priority import prioritize_tasks
from Task_Management import get_task, list_tasks


def set_availability(user_id, day_of_week, start_time, end_time):
    if not user_id:
        raise DomainRuleError("An authenticated user_id is required.")
    day = validate_day_of_week(day_of_week)
    start, end = validate_time_range(start_time, end_time)
    return insert_availability(user_id, day, start, end)


def list_availability(user_id):
    return select_availability(user_id)


def update_availability(user_id, availability_id, day_of_week, start_time, end_time):
    """Update one availability period owned by user_id; return None if not owned."""
    if not user_id:
        raise DomainRuleError("An authenticated user_id is required.")
    day = validate_day_of_week(day_of_week)
    start, end = validate_time_range(start_time, end_time)
    return persist_availability_update(user_id, availability_id, day, start, end)


def schedule_study_session(user_id, session_date, start_time, end_time, task_id=None, notes=None):
    if not user_id:
        raise DomainRuleError("An authenticated user_id is required.")
    clean_date = validate_deadline(session_date)
    start, end = validate_time_range(start_time, end_time)
    if task_id is not None and get_task(user_id, task_id) is None:
        raise DomainRuleError("The task does not exist for this user.")
    return insert_study_session(user_id, clean_date, start, end, task_id, notes)


def list_study_sessions(user_id):
    return select_study_sessions(user_id)


def _clock_minutes(value):
    hour, minute = (int(part) for part in value.split(":"))
    return hour * 60 + minute


def _clock_text(value):
    return f"{value // 60:02d}:{value % 60:02d}"


def _available_intervals(user_id, start_date, end_date):
    """Expand weekly availability and subtract already scheduled sessions."""
    availability = list_availability(user_id)
    sessions = [row for row in list_study_sessions(user_id) if row["status"] == "scheduled"]
    periods_by_day = {}
    for period in availability:
        periods_by_day.setdefault(period["day_of_week"], []).append(
            (_clock_minutes(period["start_time"]), _clock_minutes(period["end_time"]))
        )

    # Merge overlapping/adjacent availability entries so time is never counted twice.
    merged_by_day = {}
    for day, periods in periods_by_day.items():
        merged = []
        for begin, finish in sorted(periods):
            if merged and begin <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(merged[-1][1], finish))
            else:
                merged.append((begin, finish))
        merged_by_day[day] = merged

    busy_by_date = {}
    for session in sessions:
        busy_by_date.setdefault(session["session_date"], []).append(
            (_clock_minutes(session["start_time"]), _clock_minutes(session["end_time"]))
        )

    slots = []
    current = start_date
    while current <= end_date:
        busy = sorted(busy_by_date.get(current.isoformat(), []))
        for begin, finish in merged_by_day.get(current.weekday(), []):
            free = [(begin, finish)]
            for busy_begin, busy_finish in busy:
                next_free = []
                for free_begin, free_finish in free:
                    if busy_finish <= free_begin or busy_begin >= free_finish:
                        next_free.append((free_begin, free_finish))
                    else:
                        if free_begin < busy_begin:
                            next_free.append((free_begin, busy_begin))
                        if busy_finish < free_finish:
                            next_free.append((busy_finish, free_finish))
                free = next_free
            slots.extend(
                {"date": current, "start": free_begin, "end": free_finish}
                for free_begin, free_finish in free if free_begin < free_finish
            )
        current += timedelta(days=1)
    return slots


def generate_study_schedule(user_id, as_of=None):
    """Generate dated sessions from user estimates, priorities, and availability.

    Tasks without an estimate, deadline, or determinable priority remain
    unscheduled. A task may span availability slots, but all its sessions must
    end no later than its deadline. Existing scheduled sessions are preserved
    and treated as occupied time; their durations count toward task estimates
    so repeated generation does not duplicate allocated study time.
    """
    if not user_id:
        raise DomainRuleError("An authenticated user_id is required.")
    if as_of is None:
        planning_start = date.today()
    elif isinstance(as_of, str):
        planning_start = date.fromisoformat(as_of)
    elif isinstance(as_of, date):
        planning_start = as_of
    else:
        raise DomainRuleError("Schedule start date must be a date or YYYY-MM-DD string.")

    tasks = list_tasks(user_id, status="incomplete")
    prioritized = prioritize_tasks(user_id, as_of=planning_start, tasks=tasks)
    task_order = {task["id"]: index for index, task in enumerate(prioritized)}
    priority_order = {"High": 0, "Medium": 1, "Low": 2}
    existing_sessions = [row for row in list_study_sessions(user_id) if row["status"] == "scheduled"]
    candidates = [
        task for task in prioritized
        if task.get("deadline") is not None
        if task.get("study_duration_minutes") is not None
        and task.get("priority") in priority_order
    ]
    candidates.sort(key=lambda task: (
        priority_order[task["priority"]], task["deadline"], task_order[task["id"]]
    ))

    if candidates:
        latest_deadline = max(date.fromisoformat(task["deadline"]) for task in candidates)
        free_slots = (
            _available_intervals(user_id, planning_start, latest_deadline)
            if latest_deadline >= planning_start else []
        )
    else:
        free_slots = []

    candidates_by_id = {task["id"]: task for task in candidates}
    existing_minutes_by_task = {}
    for row in existing_sessions:
        task = candidates_by_id.get(row["task_id"])
        if task is None:
            continue
        session_date = date.fromisoformat(row["session_date"])
        deadline = date.fromisoformat(task["deadline"])
        if planning_start <= session_date <= deadline:
            existing_minutes_by_task[row["task_id"]] = (
                existing_minutes_by_task.get(row["task_id"], 0)
                + _clock_minutes(row["end_time"]) - _clock_minutes(row["start_time"])
            )

    planned = []
    scheduled_task_ids = {
        task["id"] for task in prioritized
        if task["id"] in existing_minutes_by_task
        and existing_minutes_by_task[task["id"]] >= (task.get("study_duration_minutes") or 0)
    }
    for task in candidates:
        remaining = max(
            0,
            task["study_duration_minutes"] - existing_minutes_by_task.get(task["id"], 0),
        )
        if remaining == 0:
            scheduled_task_ids.add(task["id"])
            continue
        deadline = date.fromisoformat(task["deadline"])
        trial_slots = [dict(slot) for slot in free_slots]
        task_sessions = []
        for slot in trial_slots:
            if slot["date"] > deadline or remaining <= 0:
                continue
            duration = min(remaining, slot["end"] - slot["start"])
            if duration <= 0:
                continue
            task_sessions.append({
                "task_id": task["id"],
                "session_date": slot["date"].isoformat(),
                "start_time": _clock_text(slot["start"]),
                "end_time": _clock_text(slot["start"] + duration),
            })
            slot["start"] += duration
            remaining -= duration
        if remaining:
            continue
        free_slots = [slot for slot in trial_slots if slot["start"] < slot["end"]]
        planned.extend(task_sessions)
        scheduled_task_ids.add(task["id"])

    # Validate all generated values before one transaction persists the schedule.
    for session in planned:
        validate_deadline(session["session_date"])
        validate_time_range(session["start_time"], session["end_time"])
    session_ids = insert_study_sessions(user_id, planned)

    unscheduled = sorted(
        task["id"] for task in prioritized if task["id"] not in scheduled_task_ids
    )
    return {
        "session_ids": session_ids,
        "scheduled_task_ids": sorted(scheduled_task_ids),
        "unscheduled_task_ids": unscheduled,
    }


__all__ = [
    "set_availability", "list_availability", "update_availability",
    "schedule_study_session", "list_study_sessions", "generate_study_schedule",
]
