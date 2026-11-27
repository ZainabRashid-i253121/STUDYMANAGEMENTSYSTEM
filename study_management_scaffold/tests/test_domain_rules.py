import pytest
from Domain_Rules import (DomainRuleError, validate_task_title, validate_deadline,
                          validate_status_transition, validate_optional_deadline,
                          validate_email, validate_password)

def test_valid_title_is_trimmed():
    assert validate_task_title("  Read chapter  ") == "Read chapter"

@pytest.mark.parametrize("title", ["", "   ", None])
def test_title_required(title):
    with pytest.raises(DomainRuleError):
        validate_task_title(title)

def test_title_maximum_length():
    with pytest.raises(DomainRuleError):
        validate_task_title("x" * 201)

def test_valid_deadline():
    assert validate_deadline("2026-11-25") == "2026-11-25"

@pytest.mark.parametrize("deadline", ["2026-02-30", "not-a-date", ""])
def test_invalid_deadline(deadline):
    with pytest.raises(DomainRuleError):
        validate_deadline(deadline)

def test_incomplete_to_completed_is_valid():
    assert validate_status_transition("incomplete", "completed") == "completed"

def test_completed_can_be_reverted_to_incomplete():
    assert validate_status_transition("completed", "incomplete") == "incomplete"

def test_incomplete_cannot_be_marked_incomplete_again():
    with pytest.raises(DomainRuleError):
        validate_status_transition("incomplete", "incomplete")

@pytest.mark.parametrize("old_status", ["pending", "in_progress"])
def test_removed_statuses_are_rejected(old_status):
    with pytest.raises(DomainRuleError):
        validate_status_transition(old_status, "completed")

def test_completed_cannot_be_completed_twice():
    with pytest.raises(DomainRuleError):
        validate_status_transition("completed", "completed")

def test_invalid_transition_is_rejected():
    with pytest.raises(DomainRuleError):
        validate_status_transition("incomplete", "cancelled")

from Domain_Rules import (
    validate_time_range, validate_day_of_week, validate_iso_datetime,
    validate_reminder_status, validate_course,
)

@pytest.mark.parametrize("start,end", [("09:00", "10:00"), ("00:00", "23:59")])
def test_valid_time_ranges(start, end):
    assert validate_time_range(start, end) == (start, end)

@pytest.mark.parametrize("start,end", [("10:00", "09:00"), ("09:00", "09:00"), ("9:00", "10:00"), ("24:00", "25:00"), ("09:60", "10:00")])
def test_invalid_time_ranges(start, end):
    with pytest.raises(DomainRuleError):
        validate_time_range(start, end)

@pytest.mark.parametrize("day", range(7))
def test_valid_day_of_week(day):
    assert validate_day_of_week(day) == day

@pytest.mark.parametrize("day", [-1, 7, 1.5, "1", True, None])
def test_invalid_day_of_week(day):
    with pytest.raises(DomainRuleError):
        validate_day_of_week(day)

@pytest.mark.parametrize("value", ["2026-11-25T09:30:00", "2026-11-25T09:30:00+05:00", "2026-11-25T09:30:00Z"])
def test_valid_reminder_datetime(value):
    assert validate_iso_datetime(value)

@pytest.mark.parametrize("value", [None, "", "2026-11-25", "not-a-date-time", "2026-02-30T10:00"])
def test_invalid_reminder_datetime(value):
    with pytest.raises(DomainRuleError):
        validate_iso_datetime(value)

@pytest.mark.parametrize("status", ["pending", "delivering", "delivered", "dismissed", "cancelled", "skipped"])
def test_valid_reminder_status(status):
    assert validate_reminder_status(status) == status

def test_invalid_reminder_status():
    with pytest.raises(DomainRuleError):
        validate_reminder_status("sent")

def test_optional_course_validation():
    assert validate_course(None) is None
    assert validate_course("  ") is None
    assert validate_course("  Software Engineering  ") == "Software Engineering"

def test_course_maximum_length():
    assert len(validate_course("x" * 100)) == 100
    with pytest.raises(DomainRuleError):
        validate_course("x" * 101)


@pytest.mark.parametrize("value", [None, "", "   "])
def test_optional_deadline_allows_missing(value):
    assert validate_optional_deadline(value) is None

def test_optional_deadline_accepts_valid_date():
    assert validate_optional_deadline(" 2026-11-25 ") == "2026-11-25"

@pytest.mark.parametrize("value", ["2026-02-30", "not-a-date"])
def test_optional_deadline_rejects_invalid_non_empty_value(value):
    with pytest.raises(DomainRuleError):
        validate_optional_deadline(value)

def test_valid_email_is_normalized():
    assert validate_email("  Student@Example.COM ") == "student@example.com"

@pytest.mark.parametrize("email", [None, "", "   ", "no-at-sign"])
def test_invalid_email_is_rejected(email):
    with pytest.raises(DomainRuleError, match="valid email"):
        validate_email(email)

def test_password_minimum_length():
    assert validate_password("12345678") == "12345678"
    for bad in (None, "", "1234567"):
        with pytest.raises(DomainRuleError, match="at least 8 characters"):
            validate_password(bad)
