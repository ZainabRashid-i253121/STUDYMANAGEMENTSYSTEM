def test_public_service_interfaces_exist():
    from Task_Management import create_task, get_task, list_tasks, transition_task_status, update_study_duration
    from Priority import deadline_distance
    from Schedule import (
        set_availability, update_availability, list_availability,
        generate_study_schedule, schedule_study_session, list_study_sessions,
    )
    from Reminder import create_reminder, list_reminders, update_reminder_status
    from External_Integration import stage_import, list_staged_imports, accept_staged_import
    assert all(callable(x) for x in [create_task, get_task, list_tasks, transition_task_status,
        deadline_distance, set_availability, update_availability, list_availability,
        generate_study_schedule, schedule_study_session, list_study_sessions,
        update_study_duration, create_reminder, list_reminders, update_reminder_status,
        stage_import, list_staged_imports, accept_staged_import])

def test_task_crud_and_user_scoping(test_db, user_id):
    from Task_Management import create_task, get_task, list_tasks
    with test_db.connection_scope() as db:
        cur = db.execute("INSERT INTO users (email, password_hash, role) VALUES (?, ?, ?)",
                         ("other@example.com", "hash", "Registered User"))
        other_id = cur.lastrowid
    task_id = create_task(user_id, "Study", "2026-11-25")
    assert get_task(user_id, task_id)["title"] == "Study"
    assert get_task(other_id, task_id) is None
    assert len(list_tasks(user_id)) == 1
    assert list_tasks(other_id) == []

def test_cross_module_workflow(test_db, user_id):
    from External_Integration import stage_import, accept_staged_import
    from Task_Management import get_task
    from Reminder import create_reminder, list_reminders
    from Schedule import set_availability, list_availability, schedule_study_session
    imported_id = stage_import(user_id, "school portal", "Essay", "2026-12-01", "English")
    task_id = accept_staged_import(user_id, imported_id)
    assert get_task(user_id, task_id)["title"] == "Essay"
    create_reminder(user_id, "2026-11-30T18:00:00", task_id, "Essay due soon")
    assert len(list_reminders(user_id)) == 1
    set_availability(user_id, 0, "09:00", "12:00")
    assert len(list_availability(user_id)) == 1
    schedule_study_session(user_id, "2026-11-26", "10:00", "11:00", task_id)


def test_accept_staged_import_twice_creates_only_one_task(test_db, user_id):
    from External_Integration import stage_import, accept_staged_import
    from Task_Management import list_tasks
    import_id = stage_import(user_id, "school portal", "Single task", "2026-12-15")
    first_task_id = accept_staged_import(user_id, import_id)
    second_task_id = accept_staged_import(user_id, import_id)
    assert first_task_id == second_task_id
    assert len(list_tasks(user_id)) == 1


def test_new_domain_rules_are_used_by_schedule_reminder_and_task_services(test_db, user_id):
    import pytest
    from Domain_Rules import DomainRuleError
    from Schedule import set_availability, schedule_study_session
    from Reminder import create_reminder, update_reminder_status
    from Task_Management import create_task

    with pytest.raises(DomainRuleError):
        set_availability(user_id, 7, "09:00", "10:00")
    with pytest.raises(DomainRuleError):
        set_availability(user_id, 1, "9:00", "10:00")
    with pytest.raises(DomainRuleError):
        schedule_study_session(user_id, "2026-11-25", "11:00", "10:00")
    with pytest.raises(DomainRuleError):
        create_reminder(user_id, "2026-11-25")
    with pytest.raises(DomainRuleError):
        update_reminder_status(user_id, 1, "sent")
    with pytest.raises(DomainRuleError):
        create_task(user_id, "Valid title", "2026-11-25", "x" * 101)


def test_priority_batch_distances_uses_supplied_task_list(test_db, user_id, monkeypatch):
    from Task_Management import create_task, list_tasks
    from Priority import deadline_distances
    create_task(user_id, "Due soon", "2099-01-01")
    tasks = list_tasks(user_id)
    import Priority
    monkeypatch.setattr(Priority, "list_tasks", lambda _user_id: (_ for _ in ()).throw(AssertionError("unexpected extra query")))
    result = deadline_distances(user_id, as_of="2098-12-31", tasks=tasks)
    assert result[tasks[0]["id"]]["days_until_deadline"] == 1


def test_events_interface_exists():
    from Events import publish_event, register_handler, process_pending_events
    assert all(callable(x) for x in [publish_event, register_handler, process_pending_events])


def test_modules_do_not_crash_on_tasks_without_deadline(test_db, user_id):
    from Task_Management import create_task, list_tasks
    from Priority import deadline_distance, deadline_distances
    from Schedule import schedule_study_session
    from Reminder import create_reminder
    from External_Integration import stage_import, accept_staged_import
    task_id = create_task(user_id, "No deadline task")
    assert deadline_distance(user_id, task_id, as_of="2026-11-25") is None
    assert deadline_distances(user_id, as_of="2026-11-25") == {}
    schedule_study_session(user_id, "2026-11-26", "10:00", "11:00", task_id)
    create_reminder(user_id, "2026-11-26T09:00:00", task_id, "no deadline")
    imported = accept_staged_import(user_id, stage_import(user_id, "portal", "Imported", "2026-12-01"))
    assert imported is not None
    assert len(list_tasks(user_id)) == 2
