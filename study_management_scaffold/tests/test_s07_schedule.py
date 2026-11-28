"""S07 tests for task study-duration estimates and schedule management."""
import pytest
import Schedule

from Domain_Rules import DomainRuleError
from Schedule import (
    generate_study_schedule, list_availability, list_study_sessions,
    schedule_study_session, set_availability, update_availability,
)
from Task_Management import (
    create_task, get_task, transition_task_status, update_study_duration,
)


def _create_user(test_db, email):
    with test_db.connection_scope() as db:
        return db.execute(
            "INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
            (email, "hash", "Registered User"),
        ).lastrowid


def test_availability_can_be_updated_and_is_user_scoped(test_db, user_id):
    availability_id = set_availability(user_id, 0, "09:00", "12:00")
    assert update_availability(user_id, availability_id, 1, "10:00", "13:00") == availability_id
    own_period = list_availability(user_id)[0]
    assert (own_period["day_of_week"], own_period["start_time"], own_period["end_time"]) == (
        1, "10:00", "13:00"
    )

    other_user = _create_user(test_db, "s07-other@example.com")
    assert update_availability(other_user, availability_id, 2, "11:00", "14:00") is None
    assert list_availability(other_user) == []
    assert list_availability(user_id)[0]["day_of_week"] == 1


def test_task_duration_estimate_is_saved_and_user_scoped(test_db, user_id):
    task_id = create_task(user_id, "Read chapter", "2099-12-01")
    updated = update_study_duration(user_id, task_id, 45)
    assert updated["study_duration_minutes"] == 45
    assert get_task(user_id, task_id)["study_duration_minutes"] == 45

    other_user = _create_user(test_db, "s07-duration-other@example.com")
    assert update_study_duration(other_user, task_id, 60) is None
    assert get_task(user_id, task_id)["study_duration_minutes"] == 45


def test_one_minute_is_the_minimum_valid_task_duration(test_db, user_id):
    task_id = create_task(user_id, "One-minute estimate")

    updated = update_study_duration(user_id, task_id, 1)

    assert updated["study_duration_minutes"] == 1
    assert get_task(user_id, task_id)["study_duration_minutes"] == 1


@pytest.mark.parametrize("duration", [0, -1, 1.5, True, None])
def test_task_duration_estimate_must_be_positive_whole_minutes(test_db, user_id, duration):
    task_id = create_task(user_id, "Invalid estimate")
    with pytest.raises(DomainRuleError):
        update_study_duration(user_id, task_id, duration)


def test_schedule_view_displays_only_the_signed_in_users_sessions(test_db, user_id):
    from app import create_app

    other_user = _create_user(test_db, "s07-sessions-other@example.com")
    task_id = create_task(user_id, "Exam review", "2099-12-01")
    other_task = create_task(other_user, "Private task", "2099-12-02")
    set_availability(user_id, 0, "09:00", "12:00")
    schedule_study_session(user_id, "2099-11-30", "09:00", "10:00", task_id)
    schedule_study_session(other_user, "2099-11-30", "10:00", "11:00", other_task)

    app = create_app({"TESTING": True, "SECRET_KEY": "s07-test-secret"})
    client = app.test_client()
    with client.session_transaction() as session:
        session["user_id"] = user_id
    response = client.get("/schedule")
    assert response.status_code == 200
    assert b"Monday" in response.data
    assert b"Exam review" in response.data
    assert b"Private task" not in response.data


def test_schedule_page_requires_authentication(test_db):
    from app import create_app

    app = create_app({"TESTING": True, "SECRET_KEY": "s07-auth-secret"})
    assert app.test_client().get("/schedule").status_code == 302


def test_schedule_generation_orders_tasks_and_splits_across_available_slots(test_db, user_id):
    set_availability(user_id, 0, "09:00", "10:00")
    set_availability(user_id, 1, "09:00", "10:00")
    high_id = create_task(user_id, "High priority", "2026-12-02")
    medium_id = create_task(user_id, "Medium priority", "2026-12-05")
    update_study_duration(user_id, high_id, 90)
    update_study_duration(user_id, medium_id, 30)

    result = generate_study_schedule(user_id, as_of="2026-11-30")
    sessions = list_study_sessions(user_id)
    high_sessions = [row for row in sessions if row["task_id"] == high_id]
    medium_sessions = [row for row in sessions if row["task_id"] == medium_id]
    assert [(row["session_date"], row["start_time"], row["end_time"]) for row in high_sessions] == [
        ("2026-11-30", "09:00", "10:00"), ("2026-12-01", "09:00", "09:30")
    ]
    assert [(row["session_date"], row["start_time"], row["end_time"]) for row in medium_sessions] == [
        ("2026-12-01", "09:30", "10:00")
    ]
    assert set(result["scheduled_task_ids"]) == {high_id, medium_id}
    assert result["unscheduled_task_ids"] == []


def test_schedule_generation_uses_nearest_deadline_for_equal_priorities(test_db, user_id):
    set_availability(user_id, 0, "09:00", "10:00")
    set_availability(user_id, 1, "09:00", "10:00")
    later_id = create_task(user_id, "Later deadline", "2026-12-03")
    nearer_id = create_task(user_id, "Nearer deadline", "2026-12-01")
    update_study_duration(user_id, later_id, 60)
    update_study_duration(user_id, nearer_id, 60)

    generate_study_schedule(user_id, as_of="2026-11-30")
    sessions = list_study_sessions(user_id)
    assert sessions[0]["task_id"] == nearer_id
    assert sessions[0]["session_date"] == "2026-11-30"
    assert sessions[1]["task_id"] == later_id
    assert sessions[1]["session_date"] == "2026-12-01"


@pytest.mark.parametrize(
    ("duration", "expected_sessions"),
    [
        (60, [("2026-11-30", "09:00", "10:00")]),
        (61, []),
    ],
)
def test_schedule_generation_respects_deadline_date_cutoff(
    test_db, user_id, duration, expected_sessions
):
    set_availability(user_id, 0, "09:00", "10:00")
    set_availability(user_id, 1, "09:00", "10:00")
    task_id = create_task(user_id, "Task due at cutoff", "2026-11-30")
    update_study_duration(user_id, task_id, duration)

    result = generate_study_schedule(user_id, as_of="2026-11-30")
    sessions = [row for row in list_study_sessions(user_id) if row["task_id"] == task_id]

    assert [
        (row["session_date"], row["start_time"], row["end_time"])
        for row in sessions
    ] == expected_sessions
    if expected_sessions:
        assert result["scheduled_task_ids"] == [task_id]
        assert result["unscheduled_task_ids"] == []
    else:
        assert result["scheduled_task_ids"] == []
        assert result["unscheduled_task_ids"] == [task_id]


def test_insufficient_availability_leaves_task_unscheduled_without_blocking_next_task(test_db, user_id):
    set_availability(user_id, 0, "09:00", "10:00")
    set_availability(user_id, 1, "09:00", "10:00")
    urgent_id = create_task(user_id, "Long urgent task", "2026-12-01")
    later_id = create_task(user_id, "Short later task", "2026-12-05")
    update_study_duration(user_id, urgent_id, 180)
    update_study_duration(user_id, later_id, 60)

    result = generate_study_schedule(user_id, as_of="2026-11-30")
    assert result["scheduled_task_ids"] == [later_id]
    assert result["unscheduled_task_ids"] == [urgent_id]
    assert all(row["task_id"] != urgent_id for row in list_study_sessions(user_id))


def test_schedule_generation_leaves_tasks_without_estimates_or_deadlines_unscheduled(test_db, user_id):
    set_availability(user_id, 0, "09:00", "10:00")
    estimated_id = create_task(user_id, "Estimated task", "2026-12-01")
    missing_estimate_id = create_task(user_id, "No estimate", "2026-12-01")
    undated_id = create_task(user_id, "No deadline")
    update_study_duration(user_id, estimated_id, 30)
    update_study_duration(user_id, undated_id, 60)

    result = generate_study_schedule(user_id, as_of="2026-11-30")
    assert result["scheduled_task_ids"] == [estimated_id]
    assert set(result["unscheduled_task_ids"]) == {missing_estimate_id, undated_id}
    assert all(row["task_id"] != undated_id for row in list_study_sessions(user_id))


def test_schedule_generation_leaves_undetermined_priority_unscheduled(test_db, user_id, monkeypatch):
    set_availability(user_id, 0, "09:00", "10:00")
    task_id = create_task(user_id, "Priority needs review", "2026-12-01")
    update_study_duration(user_id, task_id, 30)

    def undetermined_priorities(user_id, as_of=None, *, tasks=None):
        return [
            {**task, "priority": "Undetermined", "priority_requires_review": True}
            for task in tasks
        ]

    monkeypatch.setattr(Schedule, "prioritize_tasks", undetermined_priorities)
    result = generate_study_schedule(user_id, as_of="2026-11-30")

    assert result["scheduled_task_ids"] == []
    assert result["unscheduled_task_ids"] == [task_id]
    assert list_study_sessions(user_id) == []


def test_schedule_generation_excludes_completed_tasks(test_db, user_id):
    set_availability(user_id, 0, "09:00", "10:00")
    task_id = create_task(user_id, "Completed task", "2026-12-01")
    update_study_duration(user_id, task_id, 30)
    transition_task_status(user_id, task_id, "completed")

    result = generate_study_schedule(user_id, as_of="2026-11-30")
    assert result["scheduled_task_ids"] == []
    assert result["unscheduled_task_ids"] == []
    assert list_study_sessions(user_id) == []


def test_schedule_generation_reuses_existing_planned_duration_without_duplicates(test_db, user_id):
    set_availability(user_id, 0, "09:00", "10:00")
    set_availability(user_id, 1, "09:00", "10:00")
    task_id = create_task(user_id, "Incremental estimate", "2026-12-05")
    update_study_duration(user_id, task_id, 30)
    first = generate_study_schedule(user_id, as_of="2026-11-30")
    assert len(first["session_ids"]) == 1

    assert generate_study_schedule(user_id, as_of="2026-11-30")["session_ids"] == []
    assert len(list_study_sessions(user_id)) == 1

    update_study_duration(user_id, task_id, 60)
    second = generate_study_schedule(user_id, as_of="2026-11-30")
    assert len(second["session_ids"]) == 1
    assert len(list_study_sessions(user_id)) == 2


def test_overlapping_availability_is_not_counted_twice(test_db, user_id):
    set_availability(user_id, 0, "09:00", "11:00")
    set_availability(user_id, 0, "10:00", "12:00")
    task_id = create_task(user_id, "Use merged availability", "2026-12-01")
    update_study_duration(user_id, task_id, 180)

    result = generate_study_schedule(user_id, as_of="2026-11-30")
    assert result["scheduled_task_ids"] == [task_id]
    sessions = list_study_sessions(user_id)
    assert [(row["start_time"], row["end_time"]) for row in sessions] == [("09:00", "12:00")]


def test_duration_update_route_saves_estimate_with_csrf(test_db, user_id):
    from app import create_app

    task_id = create_task(user_id, "Exam review", "2099-12-01")
    app = create_app({"TESTING": True, "SECRET_KEY": "s07-duration-secret"})
    client = app.test_client()
    with client.session_transaction() as session:
        session["user_id"] = user_id
    assert client.get("/dashboard").status_code == 200
    with client.session_transaction() as session:
        token = session["_csrf_token"]
    response = client.post(
        f"/tasks/{task_id}/study-duration",
        data={"csrf_token": token, "study_duration_minutes": "90"},
    )
    assert response.status_code == 302
    assert get_task(user_id, task_id)["study_duration_minutes"] == 90


def test_availability_routes_create_and_update_owned_periods_with_csrf(test_db, user_id):
    from app import create_app

    app = create_app({"TESTING": True, "SECRET_KEY": "s07-availability-secret"})
    client = app.test_client()
    with client.session_transaction() as session:
        session["user_id"] = user_id
    assert client.get("/schedule").status_code == 200
    with client.session_transaction() as session:
        token = session["_csrf_token"]

    response = client.post("/availability", data={
        "csrf_token": token, "day_of_week": "0", "start_time": "09:00", "end_time": "12:00",
    })
    assert response.status_code == 302
    availability_id = list_availability(user_id)[0]["id"]
    response = client.post(f"/availability/{availability_id}", data={
        "csrf_token": token, "day_of_week": "2", "start_time": "10:00", "end_time": "13:00",
    })
    assert response.status_code == 302
    period = list_availability(user_id)[0]
    assert (period["day_of_week"], period["start_time"], period["end_time"]) == (2, "10:00", "13:00")


def test_schedule_generation_route_rejects_missing_csrf(test_db, user_id):
    from app import create_app

    app = create_app({"TESTING": True, "SECRET_KEY": "s07-generate-secret"})
    client = app.test_client()
    with client.session_transaction() as session:
        session["user_id"] = user_id
    assert client.post("/schedule/generate").status_code == 400
