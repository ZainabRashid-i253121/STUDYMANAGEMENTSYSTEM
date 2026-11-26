# Product Requirements Document (PRD)

## Study Management System

**Document Status:** Revised Draft (v1.2) — Incorporates user-selected clarifications recorded during review; FR-13 to FR-16 and related changes remain subject to group validation; final approval pending  
**Project:** Group #7 — Intro to Software Engineering, Deliverable 2  
**Intended User:** Ms. Arooj  
**Purpose:** To document the agreed product intent, requirements, business rules, constraints, acceptance criteria, main flows, edge cases, and unresolved decisions.

---

## Revision History

| Version | Description |
|---|---|
| v1.0 | Human-validated draft (original PRD). |
| v1.1 | Added three new requirements: task completion tracking (FR-13), deadline and study-session reminders (FR-14), and a study timer with recorded study time (FR-15). Updated scope, objectives, glossary, business rules, constraints, flows, edge cases, open questions, and traceability accordingly. Existing requirements FR-01 to FR-09 and NFR-01 to NFR-06 are unchanged except for cross-references to the new requirements. |
| v1.2 | Recorded user-selected clarifications: no manual task creation or task deletion; availability creation/update (FR-16); completed tasks excluded from priority and future schedule generation; browser notifications; multiple reminders; reminder handling for completion, missed times, delivery failures, and rescheduling; concurrent timers and timer recovery after interruption. Recorded Study Session correction, deletion, and manual creation remain unresolved. Updated relevant flows, business rules, edge cases, open questions, and traceability. |

---

## 1. Introduction

### 1.1 Purpose

The Study Management System is intended to help Ms. Arooj organize academic tasks and deadlines, prioritize tasks according to deadline proximity, and maintain a Flexible Study Schedule that accommodates her available time. It also helps her track which tasks are completed, receive reminders about upcoming deadlines and scheduled study sessions, and record the time she spends studying each task.

This document records the requirements established and reviewed during the group's requirements engineering phases. It distinguishes agreed requirements from decisions that still require human review.

### 1.2 Product Objectives

The system should aim to:

- Keep academic task and deadline information accurate and up to date.
- Prioritize tasks with closer deadlines according to agreed prioritization rules.
- Provide a flexible Study Schedule that suits Ms. Arooj.
- Allow Ms. Arooj to view academic tasks and available deadlines in one place.
- Support changes to task deadlines, priorities, and availability within the agreed scope.
- Allow Ms. Arooj to create and update availability information used by the Study Schedule.
- Let Ms. Arooj record which academic tasks are completed while preserving those tasks and their original deadlines.
- Remind Ms. Arooj of upcoming academic deadlines and scheduled study sessions at times she chooses.
- Record the time Ms. Arooj spends studying each task without altering the task's priority or deadline.

### 1.3 Intended User

Ms. Arooj is the intended user of the Study Management System. The system is intended to support her organization and planning of academic work.

### 1.4 Scope

The system's agreed scope is to:

- Organize academic tasks and deadlines.
- Help prioritize academic tasks.
- Support the creation, viewing, and adjustment of a Flexible Study Schedule.
- Import academic tasks from an external source, subject to feasibility investigation.
- Check for updates to imported academic tasks and deadlines.
- Create and update user availability information for the Study Schedule.
- Mark academic tasks as Completed or Incomplete and filter the task list by completion status.
- Configure and send reminders for upcoming academic deadlines and scheduled study sessions.
- Time study sessions against selected academic tasks and display the total recorded study time per task.
- Support access through desktop and mobile browsers.

The exact external source, synchronization behavior, prioritization rules, scheduling rules, reminder delivery method, and study-timer edge-case behavior remain subject to the Open Questions section.

---

## 2. Product Boundaries

### 2.1 Non-Goals

The Study Management System shall not:

- Take responsibility for Ms. Arooj's academic performance.
- Make academic decisions on Ms. Arooj's behalf.
- Act as the official source of academic deadlines.
- Assess Ms. Arooj's academic work.
- Support manual task creation; academic tasks enter the system through the external import capability (FR-01).
- Support task deletion; tasks are retained and their completion status is used to distinguish completed from incomplete tasks.

### 2.2 Boundary of Responsibility

The system is intended to organize information and support planning. Its task priorities and Study Schedule are intended to assist Ms. Arooj; they do not replace official academic information or make academic decisions for her. Likewise, completion status, reminders, and recorded study time are records and aids for Ms. Arooj; recorded study time does not automatically change Task Priority or deadlines (FR-15, BR-07).

---

## 3. Terminology and Glossary

The following agreed terms shall be used consistently throughout this document.

| Term | Usage in this PRD |
|---|---|
| Manual Task Entry | A term present in the group's earlier glossary. Manual task creation is not a supported system capability under the current product decision; academic tasks enter through the external import capability (FR-01). |
| Task Priority | The relative priority assigned to an academic task according to agreed prioritization rules. |
| Study Schedule | The schedule that organizes study sessions and tasks according to deadlines and available time. |
| Flexible Study Schedule | The Study Schedule that supports adjustments when relevant deadlines, priorities, or availability change. |
| Completion Status *(proposed)* | The state of an academic task, either Completed or Incomplete. A task that is Incomplete is also referred to as a pending task. |
| Completion Date *(proposed)* | The date recorded when a task is marked Completed. |
| Reminder *(proposed)* | A notification configured by Ms. Arooj and sent a selected amount of time before an academic deadline or a scheduled study session. |
| Scheduled Study Session *(proposed)* | A study session placed in the Study Schedule. |
| Study Timer *(proposed)* | A timer that Ms. Arooj can start, pause, resume, and stop for a selected academic task. |
| Recorded Study Session *(proposed)* | A completed timed study period, saved with its duration and date. It is distinct from a Scheduled Study Session. |
| Total Recorded Study Time *(proposed)* | The sum of the durations of all Recorded Study Sessions saved for a task. |

The group's approved glossary remains the authoritative source for the complete set of definitions. The terms marked *(proposed)* were introduced by the v1.1 requirement changes and require approval into the group's glossary before they are treated as authoritative.

**Minimum task record information:** Each task record shall contain a task identifier, task name, course, deadline information, and completion status. Deadline information may be unavailable, as FR-02 requires tasks without deadlines to remain visible and be marked accordingly. A completion date is recorded when the task is marked Completed. The method for obtaining or assigning task identifiers is not prescribed here.

---

## 4. Functional Requirements

### FR-01 — Import Academic Tasks

**Requirement:** The system shall support importing academic tasks and their available deadlines from an external source, subject to feasibility investigation.

**Acceptance Criteria**

- **AC-FR-01.1:** Successfully imported tasks and their available deadlines shall appear in the task list.
- **AC-FR-01.2:** Ms. Arooj shall be notified if an import fails or is incomplete.
- **AC-FR-01.3:** The system shall not show a failed or incomplete import as successful.

**Related edge cases:** Repeated imports, duplicate tasks, incomplete source data, interrupted imports, and external-source access failures remain to be specified.

### FR-02 — View Academic Tasks and Deadlines

**Requirement:** The system shall provide a view of academic tasks and their available deadlines in one place.

**Acceptance Criteria**

- **AC-FR-02.1:** The dashboard shall show academic tasks and available deadlines in one place.
- **AC-FR-02.2:** Tasks without deadlines shall remain visible and shall be marked as missing deadline information.

**Related edge case:** The ordering and priority display of tasks without deadlines remain unresolved.

**Related requirement:** Completion status display and filtering of the task list are specified in FR-13.

### FR-03 — Update Task Deadlines

**Requirement:** The system shall update task deadlines when a valid deadline change is accepted and adjust the task's position according to the agreed prioritization rules.

**Acceptance Criteria**

- **AC-FR-03.1:** When a valid deadline change is accepted, the system shall update the deadline and adjust the task's position according to agreed prioritization rules.
- **AC-FR-03.2:** If a deadline change creates a conflict, the affected task shall be flagged for review.

**Related edge cases:** Conflicting deadline values from the system and an external source, disputed deadline changes, and the timing of updates relative to review remain unresolved.

**Related requirement:** Pending reminders for a task whose deadline is updated are handled under FR-14.

### FR-04 — Identify Conflicting Deadlines

**Requirement:** The system shall identify deadline conflicts for Ms. Arooj to review.

**Acceptance Criteria**

- **AC-FR-04.1:** The system shall flag identified deadline conflicts for Ms. Arooj to review.

**Related edge cases:** The conditions that qualify as a conflict and the effect of conflicts on Task Priority or the Study Schedule remain unresolved.

### FR-05 — Prioritize Academic Tasks

**Requirement:** The system shall prioritize academic tasks using agreed prioritization rules that give weight to deadline proximity.

**Acceptance Criteria**

- **AC-FR-05.1:** Tasks with closer deadlines shall receive higher priority according to agreed prioritization rules.
- **AC-FR-05.2:** The system shall not use an unapproved rule to rank tasks with equal deadlines.

**Related edge cases:** Tasks with equal deadlines, missing deadlines, insufficient study time, and cases where the agreed rules do not establish a clear priority remain unresolved.

### FR-06 — Create and View a Study Schedule

**Requirement:** The system shall create and display a Study Schedule that organizes study sessions and tasks according to deadlines and available time.

**Acceptance Criteria**

- **AC-FR-06.1:** The Study Schedule shall organize sessions and tasks according to deadlines and available time.
- **AC-FR-06.2:** The Study Schedule shall use information specified in the agreed scheduling rules.

**Related edge cases:** Missing or outdated availability information, insufficient time for all tasks, and overlapping sessions remain unresolved.

### FR-07 — Adjust the Flexible Study Schedule

**Requirement:** The system shall support adjustments to the Flexible Study Schedule when Ms. Arooj updates her availability.

**Acceptance Criteria**

- **AC-FR-07.1:** When Ms. Arooj updates her availability, the Study Schedule shall reflect the changes.
- **AC-FR-07.2:** Schedule adjustments shall consider relevant deadline and Task Priority changes according to agreed scheduling rules.

**Related edge cases:** Whether existing sessions move automatically or require user approval, and which session details remain unchanged, require human decisions.

**Related requirement:** Pending reminders for rescheduled study sessions are handled under FR-14.

### FR-08 — Check Imported Task Updates

**Requirement:** The system shall check for updates to imported academic tasks and deadlines.

**Acceptance Criteria**

- **AC-FR-08.1:** The system shall check for updates to imported tasks and deadlines.
- **AC-FR-08.2:** The system shall not report an unsuccessful update as successful.

**Related edge cases:** Partial updates, retry attempts, cancelled or missing external tasks, outdated imported information, and external-source authentication failures remain unresolved.

### FR-09 — Support Study Schedule Changes

**Requirement:** The system shall support Study Schedule adjustments when relevant deadlines, Task Priorities, or availability change, according to agreed scheduling rules.

**Acceptance Criteria**

- **AC-FR-09.1:** The system shall support Study Schedule adjustments when deadlines, priorities, or availability change, according to agreed scheduling rules.
- **AC-FR-09.2:** Schedule adjustments shall consider the relevant changes defined in those rules.

**Related edge cases:** The distinction between FR-07 and FR-09, the handling of missed study sessions, and whether adjustments require user approval remain unresolved.

**Related requirement:** Pending reminders for rescheduled study sessions are handled under FR-14.

### FR-13 — Track Task Completion

**Requirement:** The system shall allow Ms. Arooj to mark academic tasks as Completed or Incomplete, record the completion date, visually distinguish completed tasks from pending tasks, and allow her to filter the task list by completion status, without deleting completed tasks or changing their original deadlines.

**Acceptance Criteria**

- **AC-FR-13.1:** Ms. Arooj shall be able to mark an academic task as Completed or as Incomplete.
- **AC-FR-13.2:** When a task is marked Completed, the system shall record the completion date.
- **AC-FR-13.3:** The task list shall visually distinguish Completed tasks from pending (Incomplete) tasks.
- **AC-FR-13.4:** Ms. Arooj shall be able to filter the task list by completion status.
- **AC-FR-13.5:** Marking a task as Completed shall not delete the task.
- **AC-FR-13.6:** Marking a task as Completed shall not change the task's original deadline.
- **AC-FR-13.7:** Completed tasks shall be excluded from Task Priority calculations and future Study Schedule generation or adjustment.

**Related edge cases:** The default task-list view, the completion date when a task is reverted to Incomplete, the handling of already scheduled study sessions for a task that becomes Completed, and reminders associated with scheduled study sessions remain to be specified.

### FR-14 — Configure and Send Reminders

**Requirement:** The system shall allow Ms. Arooj to configure one or more reminders for upcoming academic deadlines and Scheduled Study Sessions by selecting reminder times in advance of each event. Reminders shall be delivered through browser notifications. The system shall automatically update pending reminders when deadlines or Scheduled Study Sessions are rescheduled, cancel pending deadline reminders when a task is marked Completed, skip a reminder whose configured time has passed and notify Ms. Arooj, and record and retry reminder-delivery failures. Task deletion is not supported. Cancellation behavior for deleted Scheduled Study Sessions remains subject to the unresolved decision about whether session deletion is supported.

**Acceptance Criteria**

- **AC-FR-14.1:** Ms. Arooj shall be able to configure a reminder for an upcoming academic deadline by selecting a reminder time in advance of the deadline.
- **AC-FR-14.2:** Ms. Arooj shall be able to configure a reminder for a scheduled study session by selecting a reminder time in advance of the session.
- **AC-FR-14.3:** The system shall deliver each reminder through a browser notification at its configured time.
- **AC-FR-14.4:** When a deadline or Scheduled Study Session with a pending reminder is rescheduled, the system shall automatically update the pending reminder to correspond to the rescheduled event.
- **AC-FR-14.5:** When a task is marked Completed, the system shall cancel its pending academic-deadline reminders.
- **AC-FR-14.6:** Ms. Arooj shall be able to configure more than one reminder for an academic deadline or Scheduled Study Session.
- **AC-FR-14.7:** If a reminder's configured time has passed before it can be delivered, the system shall skip that reminder and notify Ms. Arooj.
- **AC-FR-14.8:** If reminder delivery fails, the system shall record the failure and attempt delivery again.

**Related edge cases:** Available reminder-time choices, browser notification behavior when the browser is closed or notifications are unavailable, retry limits and timing, and deletion of Scheduled Study Sessions remain to be specified. Task deletion is not supported under the current product decision.

### FR-15 — Study Timer and Recorded Study Time

**Requirement:** The system shall allow Ms. Arooj to start, pause, resume, and stop a Study Timer associated with a selected academic task. The system shall save the duration and date of each completed study session and display the total recorded study time for each task, without automatically modifying the task's Task Priority or academic deadline.

**Acceptance Criteria**

- **AC-FR-15.1:** Ms. Arooj shall be able to start a Study Timer associated with a selected academic task.
- **AC-FR-15.2:** Ms. Arooj shall be able to pause a running Study Timer and resume a paused Study Timer.
- **AC-FR-15.3:** Ms. Arooj shall be able to stop a Study Timer.
- **AC-FR-15.4:** When a study session is completed, the system shall save its duration and date as a Recorded Study Session for the associated task. Time during which the timer is paused shall not count toward the duration.
- **AC-FR-15.5:** The system shall display the Total Recorded Study Time for each task.
- **AC-FR-15.6:** Recording study time shall not automatically modify the task's Task Priority or academic deadline.
- **AC-FR-15.7:** The system shall allow more than one Study Timer to run simultaneously for different academic tasks.
- **AC-FR-15.8:** If the browser is closed or the connection is lost while a timer is running or paused, the system shall preserve the timer state and recover the elapsed time when Ms. Arooj returns.

**Related edge cases:** Correction, deletion, or manual creation of Recorded Study Sessions; timers on completed tasks; the relationship between Recorded Study Sessions and Scheduled Study Sessions; and behavior when an active timer's task is affected remain to be specified.

### FR-16 — Manage User Availability

**Requirement:** The system shall allow Ms. Arooj to create and update availability information used by the Study Schedule.

**Acceptance Criteria**

- **AC-FR-16.1:** Ms. Arooj shall be able to provide availability information for use in Study Schedule creation and adjustment.
- **AC-FR-16.2:** Ms. Arooj shall be able to update previously provided availability information.
- **AC-FR-16.3:** The Study Schedule shall use the available user-provided availability information according to the agreed scheduling rules.

**Related edge cases:** The format, granularity, recurrence, and handling of missing or outdated availability remain to be specified. Ownership of availability data is not assigned by this requirement and requires architectural clarification.

---

## 5. Non-Functional Requirements

### NFR-01 — Usability

**Requirement:** The system shall provide a dashboard and brief guidance to help Ms. Arooj use its main features.

**Acceptance Criteria**

- **AC-NFR-01.1:** The system shall provide a dashboard where users can view academic tasks and deadlines.
- **AC-NFR-01.2:** The system shall provide onboarding instructions or brief guidance for its main features.

**Open matter:** The team has not established a measurable target for ease of use.

### NFR-02 — Compatibility

**Requirement:** The system shall support desktop and mobile browsers within the agreed compatibility scope.

**Acceptance Criteria**

- **AC-NFR-02.1:** The system shall support desktop and mobile browsers within the agreed compatibility scope.

**Open matter:** The specific browsers, versions, and testing scope have not been established.

### NFR-03 — Security and Privacy

**Requirement:** The system shall restrict access to protected records to authenticated and authorized users and minimize credential storage according to agreed security and privacy requirements.

**Acceptance Criteria**

- **AC-NFR-03.1:** Only authenticated and authorized users shall be able to access protected records.
- **AC-NFR-03.2:** Credential storage shall be minimized according to agreed security and privacy requirements.

**Open matter:** The specific verification and testing procedures remain to be defined.

### NFR-04 — Reliability and Recovery

**Requirement:** The system shall support synchronization, backup, and recovery features included in the agreed requirements.

**Acceptance Criteria**

- **AC-NFR-04.1:** The system shall support the synchronization, backup, and recovery features included in the agreed requirements.

**Open matter:** The required failure scenarios, recovery coverage, verification procedures, and handling of partial synchronization and retries remain to be established. Whether completion status, reminders, and recorded study time are within backup and recovery scope is also undecided (OQ-50).

### NFR-05 — Performance

**Requirement:** The team shall establish measurable performance targets and verification procedures before finalizing performance acceptance criteria.

**Acceptance Criteria**

- **AC-NFR-05.1:** The team shall decide measurable response-time targets and test them before finalizing performance acceptance criteria.

**Open matter:** Acceptable response times for the system's main operations have not been established.

### NFR-06 — Availability

**Requirement:** The system shall support the agreed access expectations, with availability measurement and verification to be defined.

**Acceptance Criteria**

- **AC-NFR-06.1:** The team shall define how system availability is measured and verified.

**Open matter:** The acceptable availability target and its verification method have not been established.

---

## 6. Business Rules

### BR-01 — Deadline-Based Task Priority

Tasks with closer deadlines shall receive weight in Task Priority. The exact prioritization rules remain to be agreed.

### BR-02 — Accuracy and Currency of Task Information

Task and deadline information should be kept accurate and up to date.

### BR-03 — No Academic Decision-Making

The system shall not make academic decisions on Ms. Arooj's behalf.

### BR-04 — No Official Deadline Authority

The system shall not act as the official source of academic deadlines.

### BR-05 — No Academic Assessment

The system shall not assess Ms. Arooj's academic work.

### BR-06 — Completed Tasks Are Preserved

Marking a task as Completed shall not delete the task or change its original deadline. Task deletion is not supported under the current product scope. Completed tasks are excluded from Task Priority calculations and future Study Schedule generation or adjustment.

### BR-07 — Study Time Does Not Change Priority or Deadlines

Recording study time shall not automatically modify a task's Task Priority or academic deadline.

### BR-08 — Reminders Follow Their Events

A reminder shall remain consistent with the current deadline or Scheduled Study Session it refers to: it is updated when that event is rescheduled. Pending academic-deadline reminders are cancelled when the associated task is marked Completed. Task deletion is not supported. Whether Scheduled Study Sessions may be deleted, and the resulting reminder behavior, remains unresolved.

**Note:** The earlier business-rule candidate for a flexible study plan as a separate business rule was rejected. Flexibility remains a product objective supported by the Functional Requirements.

---

## 7. Product Constraints

### PC-01 — Academic Performance Responsibility

The system shall not take responsibility for Ms. Arooj's academic performance.

### PC-02 — Academic Decision-Making

The system shall not make academic decisions for Ms. Arooj.

### PC-03 — Official Deadline Authority

The system shall not act as the official source of deadlines.

### PC-04 — Academic Assessment

The system shall not assess Ms. Arooj's academic work.

### PC-05 — Product Scope

The system's scope is to organize academic tasks and deadlines, help prioritize tasks, support a Flexible Study Schedule, track task completion, send reminders for deadlines and scheduled study sessions, and record study time per task.

### PC-06 — Browser Access

The system shall support desktop and mobile browsers.

### PC-07 — Access Availability Expectations

The system is intended to be accessible at any time, including evenings and weekends. The measurable availability target and method of verification remain open.

---

## 8. Main Flows

The following flows summarize the agreed behavior. They do not prescribe unapproved implementation details or resolve open decisions.

### Flow 1 — Import Academic Tasks

1. The system attempts to import academic tasks and their available deadlines from an external source.
2. Successfully imported tasks and available deadlines appear in the task list.
3. If the import fails or is incomplete, Ms. Arooj is notified.
4. The system does not present an unsuccessful or incomplete import as successful.

**Open decisions:** External-source feasibility, duplicate handling, completeness detection, and external-source access failures.

### Flow 2 — View Academic Tasks and Deadlines

1. Ms. Arooj views the dashboard.
2. The dashboard presents academic tasks and their available deadlines in one place.
3. Tasks without deadlines remain visible and are marked as missing deadline information.

**Open decision:** How tasks without deadlines are ordered or represented in the priority display.

### Flow 3 — Handle a Deadline Change

1. A deadline change is received or entered.
2. The system determines whether the change is valid under rules that remain to be agreed.
3. When a valid change is accepted, the deadline is updated and the task's position is adjusted according to agreed prioritization rules.
4. If the change creates a conflict, the affected task is flagged for review.
5. Pending reminders for the task's deadline are updated to correspond to the new deadline (FR-14).

**Open decisions:** Validation, source-of-truth conflicts, disputed values, and whether updates occur before or after review.

### Flow 4 — Prioritize Academic Tasks

1. The system considers academic tasks and their available deadlines.
2. Tasks with closer deadlines receive higher priority according to agreed rules.
3. Equal-deadline tasks are not ranked using an unapproved rule.

**Open decisions:** Missing deadlines, equal deadlines, insufficient study time, and unclear priority outcomes.

### Flow 5 — Create a Study Schedule

1. The system uses deadlines and available time according to agreed scheduling rules.
2. The system organizes tasks and study sessions into a Study Schedule.
3. The Study Schedule is presented to Ms. Arooj.

**Open decisions:** Missing or outdated availability, insufficient time, and overlapping sessions.

### Flow 6 — Adjust the Flexible Study Schedule

1. A relevant change occurs in availability, deadlines, or Task Priority.
2. The system supports an adjustment to the Study Schedule according to agreed scheduling rules.
3. The resulting schedule reflects relevant changes.
4. Pending reminders for any rescheduled study sessions are updated to correspond to the new session times (FR-14).

**Open decisions:** Automatic versus user-approved adjustments, preservation of existing session details, and missed study sessions.

### Flow 6A — Maintain User Availability

1. Ms. Arooj provides availability information to the system.
2. The system makes that information available for Study Schedule creation and adjustment.
3. Ms. Arooj may update her availability information.
4. Relevant availability changes are handled by the Study Schedule according to agreed scheduling rules.

**Open decisions:** Availability format, granularity, recurrence, and ownership of availability data.

### Flow 7 — Check for Imported Updates

1. The system checks for updates to imported academic tasks and deadlines.
2. The system handles the result without reporting an unsuccessful update as successful.
3. The system's handling of outdated or incomplete information must follow rules that remain to be established.

**Open decisions:** Retry behavior, partial updates, removed or cancelled tasks, authentication failures, and user notification of stale information.

### Flow 8 — Mark a Task Completed or Incomplete

1. Ms. Arooj marks an academic task as Completed or Incomplete.
2. When the task is marked Completed, the system records the completion date.
3. The task list visually distinguishes Completed tasks from pending tasks.
4. Ms. Arooj may filter the task list by completion status.
5. The task is not deleted, and its original deadline is not changed.
6. Completed tasks are excluded from Task Priority calculations and future Study Schedule generation or adjustment.
7. Pending academic-deadline reminders for the completed task are cancelled.

**Open decisions:** Default list view, completion date on reversion, and handling of already scheduled study sessions for a task that becomes Completed.

### Flow 9 — Configure and Receive a Reminder

1. Ms. Arooj selects an upcoming academic deadline or Scheduled Study Session and selects one or more reminder times in advance of it.
2. The system delivers the reminder through a browser notification at the configured time.
3. If the deadline or session is rescheduled, the system updates the pending reminder automatically.
4. If a task is marked Completed, the system cancels its pending academic-deadline reminders.
5. If a reminder time has passed, the system skips that reminder and notifies Ms. Arooj.
6. If reminder delivery fails, the system records the failure and attempts delivery again.

**Boundary:** Task deletion is not supported. Whether Scheduled Study Sessions may be deleted remains unresolved.

**Open decisions:** Delivery method, available reminder times, past-due reminder times, delivery failures, and reminders for completed tasks.

### Flow 10 — Record Study Time for a Task

1. Ms. Arooj selects an academic task and starts the Study Timer.
2. More than one timer may run simultaneously for different academic tasks.
3. She may pause and resume each timer.
4. If the browser is closed or the connection is lost, the timer state and elapsed time are preserved and recovered when she returns.
5. When she stops a timer, the system saves the duration and date of the Recorded Study Session for that task.
6. The system displays the Total Recorded Study Time for the task.
7. The task's Task Priority and academic deadline are not automatically modified.

**Open decisions:** Correction, deletion, or manual creation of recorded sessions; timers on completed tasks; and the relationship to Scheduled Study Sessions.

---

## 9. Edge Cases and Exception Handling

The following cases have been identified but do not yet have complete, agreed handling rules.

| ID | Edge case | Current agreed behavior | Human decision still needed |
|---|---|---|---|
| EC-01 | Import fails or is incomplete | Notify Ms. Arooj; do not report success | Define completeness detection and recovery behavior |
| EC-02 | Repeated import or duplicate task | Not yet specified | Define duplicate identification and handling |
| EC-03 | Task has no deadline | Keep it visible and mark missing deadline information | Define priority and display behavior |
| EC-04 | Deadline changes conflict | Flag affected task for review when a conflict is created | Define conflict conditions and treatment of disputed values |
| EC-05 | Equal deadlines | Do not use an unapproved ranking rule | Define tie handling |
| EC-06 | Insufficient time for all tasks | No handling rule established | Define how priority and scheduling interact |
| EC-07 | Availability is missing or outdated | No handling rule established | Define whether schedule generation or adjustment is allowed and how it is handled |
| EC-08 | Study sessions overlap | No handling rule established | Define conflict detection and resolution |
| EC-09 | Missed study session | No handling rule established | Decide whether and how the schedule changes |
| EC-10 | Imported task is cancelled or disappears | No handling rule established | Define whether the task is removed, retained, or flagged |
| EC-11 | External-source authentication fails | No handling rule established | Define notification, retry, and stale-information handling |
| EC-12 | Synchronization is partial or unsuccessful | Do not report an unsuccessful update as successful | Define partial-update and retry behavior |
| EC-13 | Existing sessions require rescheduling | Schedule adjustments are supported | Define automatic adjustment, user approval, and session-detail preservation |
| EC-14 | Performance or availability target is unestablished | Targets must be defined before acceptance is finalized | Agree measurable targets and verification procedures |
| EC-25 | User availability is missing or outdated | The system allows Ms. Arooj to create and update availability information | Define availability format, granularity, recurrence, and handling of missing or outdated information |
| EC-15 | Completed task appears in prioritization or scheduling | Completed tasks are preserved, excluded from Task Priority calculations and future Study Schedule generation or adjustment, and keep their original deadlines | Define what happens to already scheduled sessions when a task becomes Completed |
| EC-16 | Completed task is reverted to Incomplete | Ms. Arooj may mark a task as Completed or Incomplete | Define what happens to the recorded completion date |
| EC-17 | Completed task has pending reminders | Pending academic-deadline reminders for the completed task are cancelled | Define handling of reminders for Scheduled Study Sessions associated with a completed task |
| EC-18 | Reminder time has already passed when set or after rescheduling | Skip the reminder and notify Ms. Arooj | Define notification details and behavior when browser notifications are unavailable |
| EC-19 | Reminder cannot be delivered | Record the delivery failure and attempt delivery again | Define retry limits, timing, and behavior after repeated failures |
| EC-20 | Study Timer is interrupted (e.g., browser closed or connection lost) | Preserve timer state and recover elapsed time when Ms. Arooj returns | Define the technical recovery limits and behavior if recovery data is unavailable |
| EC-21 | Multiple Study Timers are started | Multiple timers may run simultaneously for different academic tasks | Define behavior if multiple timers are started for the same task, if applicable |
| EC-22 | Task is Completed while its timer is running | Task deletion is not supported; timer behavior when its task becomes Completed remains unresolved | Define whether the timer may continue, must stop, or requires another handling rule |
| EC-23 | Task has Recorded Study Sessions | Task deletion is not supported under the current product scope | No task-deletion behavior is required; Recorded Study Session editing/deletion remains unresolved under OQ-46 |
| EC-24 | Study session spans midnight | The session's date is saved | Define which date is recorded |

---

## 10. Open Questions

This section tracks open questions and their resolution status. Items marked Resolved record decisions selected during review; items marked Partially resolved retain the remaining detail that still requires a decision. Their presence here does not imply that every listed matter is unresolved.

### 10.1 Import and External-Source Integration

- **OQ-01:** Which external source or sources are feasible for importing academic tasks?
- **OQ-02:** How should repeated imports and duplicate tasks be handled?
- **OQ-03:** How will the system determine whether an import is complete, partial, or interrupted?
- **OQ-04:** What should happen when an imported task is cancelled or disappears from the external source?
- **OQ-05:** How should expired, denied, or failed external-source authentication be handled?
- **OQ-06:** How should the system notify Ms. Arooj that imported information may be outdated?
- **OQ-07:** How should partial updates and retry attempts be handled?

### 10.2 Task Information and Deadlines

**Recorded product decisions:** Manual task creation is not supported; tasks enter through external import (FR-01). Task deletion is not supported; tasks are retained and completion status is used to distinguish completed from incomplete tasks.

- **OQ-08:** How should tasks without deadlines be ranked or displayed in the priority list?
- **OQ-09:** What conditions qualify as a deadline conflict?
- **OQ-10:** How should conflicting deadlines from the system and external source be handled?
- **OQ-11:** If deadline values disagree, which value should be retained or flagged for review?
- **OQ-12:** Should a disputed deadline be updated immediately or only after review?
- **OQ-13:** How should the system distinguish valid deadline changes from invalid or conflicting changes?

### 10.3 Task Priority

- **OQ-14:** How should tasks with equal deadlines be prioritized?
- **OQ-15:** How should tasks without deadlines be prioritized relative to tasks with deadlines?
- **OQ-16:** How should the system represent cases where the agreed rules do not establish a clear priority?
- **OQ-17:** How should priorities and the Study Schedule respond when there is insufficient time to study for every task?
- **OQ-18:** Should deadline conflicts affect Task Priority and Study Schedule generation, or only be flagged for review?

### 10.4 Study Schedule

- **OQ-19 (Partially resolved):** The system shall allow Ms. Arooj to create and update availability information (FR-16). How should missing or outdated availability information be handled?
- **OQ-20:** How should the system handle overlapping study sessions?
- **OQ-21:** Should existing sessions move automatically when the Study Schedule changes, or should Ms. Arooj approve adjustments?
- **OQ-22:** Which details of existing sessions should remain unchanged during schedule adjustments?
- **OQ-23:** Should missed study sessions lead to Study Schedule adjustments?
- **OQ-24:** How should FR-07 (adjusting the Flexible Study Schedule when availability changes) be distinguished from FR-09 (supporting schedule changes after relevant changes to deadlines, priorities, or availability)?
- **OQ-25:** Should FR-07 and FR-09 remain separate requirements, or should they be consolidated?

### 10.5 Quality Requirements and Constraints

- **OQ-26:** Should the team establish a measurable usability target?
- **OQ-27:** Which desktop and mobile browsers and versions are within the supported compatibility scope?
- **OQ-28:** Which security and privacy verification procedures should be used?
- **OQ-29:** Which failures and data-loss scenarios must backup and recovery cover?
- **OQ-30:** How will successful recovery be verified?
- **OQ-31:** How will partial synchronization and retry behavior be tested?
- **OQ-32:** What response-time targets should apply to the main operations?
- **OQ-33:** What availability target is appropriate, including evenings and weekends?
- **OQ-34:** How should availability be measured and verified?

### 10.6 Task Completion

- **OQ-35:** Should the task list show Completed tasks by default, or only after the filter is applied? Which filter options are offered (e.g., Completed, Incomplete, All)?
- **OQ-36 (Resolved):** Completed tasks are excluded from Task Priority calculations and future Study Schedule generation or adjustment.
- **OQ-37:** When a Completed task is reverted to Incomplete, should the recorded completion date be cleared or kept?

### 10.7 Reminders

- **OQ-38 (Partially resolved):** Reminders are delivered through browser notifications. How are reminders delivered when the browser is closed or browser notifications are unavailable?
- **OQ-39 (Partially resolved):** More than one reminder may be configured for an event. Which reminder times may Ms. Arooj select (preset or custom)?
- **OQ-40 (Resolved):** If a reminder time has passed when set or after rescheduling, the system skips that reminder and notifies Ms. Arooj. Notification details remain to be specified.
- **OQ-41 (Resolved):** Pending academic-deadline reminders for a task are cancelled when that task is marked Completed. Handling of reminders for associated Scheduled Study Sessions remains open.
- **OQ-42 (Partially resolved):** The system records reminder-delivery failures and attempts delivery again. Retry limits, timing, and handling after repeated failures remain open.
- **OQ-43 (Partially resolved):** Task deletion is not supported under the current product scope. Whether Scheduled Study Sessions may be deleted remains undecided; if deletion is supported, the group must confirm its effects on associated reminders.

### 10.8 Study Timer

- **OQ-44 (Resolved):** More than one Study Timer may run simultaneously for different academic tasks.
- **OQ-45 (Resolved):** Preserve the timer state and recover elapsed time when Ms. Arooj returns after browser closure or connection loss. Technical recovery limits remain to be defined.
- **OQ-46 (Unresolved):** May Ms. Arooj correct, delete, or manually add Recorded Study Sessions? No capability is assumed until the group decides.
- **OQ-47:** What should happen to a running timer or Recorded Study Sessions when the task is completed? Task deletion is not supported under the current product scope.
- **OQ-48:** Does a Recorded Study Session count toward a Scheduled Study Session, and does it affect the handling of missed sessions (EC-09, OQ-23)?
- **OQ-49:** Which date is recorded for a session that spans midnight?
- **OQ-50:** Are completion status, reminders, recorded study time, and user availability within backup and recovery scope?
- **OQ-51:** What format, granularity, and recurrence options should be supported for user availability information?
- **OQ-52:** What should happen to existing Scheduled Study Sessions when an associated task is marked Completed?

---

## 11. Traceability and Requirement Status

### 11.1 Requirement Traceability

| Requirement ID | Related acceptance criteria | Related business rule or constraint |
|---|---|---|
| FR-01 | AC-FR-01.1–AC-FR-01.3 | BR-02; external-source feasibility remains open |
| FR-02 | AC-FR-02.1–AC-FR-02.2 | BR-02, PC-05 |
| FR-03 | AC-FR-03.1–AC-FR-03.2 | BR-01, BR-02 |
| FR-04 | AC-FR-04.1 | BR-01; conflict effects remain open |
| FR-05 | AC-FR-05.1–AC-FR-05.2 | BR-01, BR-03 |
| FR-06 | AC-FR-06.1–AC-FR-06.2 | PC-05; BR-03 |
| FR-07 | AC-FR-07.1–AC-FR-07.2 | PC-05; BR-03 |
| FR-08 | AC-FR-08.1–AC-FR-08.2 | BR-02; external-source handling remains open |
| FR-09 | AC-FR-09.1–AC-FR-09.2 | PC-05; BR-03 |
| FR-13 | AC-FR-13.1–AC-FR-13.7 | BR-02, BR-06, PC-05; handling of already scheduled sessions remains open |
| FR-14 | AC-FR-14.1–AC-FR-14.8 | BR-02, BR-08, PC-05; browser-closed behavior and retry details remain open |
| FR-15 | AC-FR-15.1–AC-FR-15.8 | BR-07, PC-05; recorded-session management and other timer edge cases remain open |
| FR-16 | AC-FR-16.1–AC-FR-16.3 | FR-06, FR-07, FR-09; availability ownership and detailed scheduling rules remain open |
| NFR-01 | AC-NFR-01.1–AC-NFR-01.2 | PC-05 |
| NFR-02 | AC-NFR-02.1 | PC-06 |
| NFR-03 | AC-NFR-03.1–AC-NFR-03.2 | Security and privacy requirements; detailed verification open |
| NFR-04 | AC-NFR-04.1 | BR-02; synchronization, backup, and recovery scope open |
| NFR-05 | AC-NFR-05.1 | Measurable performance targets to be established |
| NFR-06 | AC-NFR-06.1 | PC-07 |

### 11.2 Candidate Requirements Confirmed as Rejected

The human validation review confirmed that the group's earlier decisions to reject the following candidates as separate active requirements still stand, because their scope overlaps with existing requirements:

- **FR-10 — Review Study Schedule:** Covered by FR-06.
- **FR-11 — Manage Task and Deadline Information:** Overlaps with FR-02, FR-03, and FR-08.
- **FR-12 — Flexible Study Plan:** Overlaps with FR-06 and FR-09.

These candidates remain rejected and are not assigned as active requirement IDs. The requirements added in v1.1 use IDs FR-13 to FR-15 so that the rejected IDs FR-10 to FR-12 are not reused. The possible overlap between FR-07 and FR-09 remains unresolved; OQ-24 and OQ-25 stay open for the group to decide whether those requirements should be combined.

### 11.3 Requirement Status

- **Document status:** Revised draft (v1.2). The content carried over from v1.0 remains based on prior human validation. User-selected clarifications recorded in this review have been incorporated, but the resulting changes and FR-13 to FR-16 require group validation. Final approval remains pending.
- **Requirements:** FR-01 to FR-09 and NFR-01 to NFR-06 are based on recorded group decisions and human-reviewed acceptance criteria. FR-13 to FR-15 are based on the v1.1 requirement changes (Req#1 to Req#3). FR-16 and the v1.2 clarifications are proposed additions/refinements pending group validation.
- **Unresolved behavior:** Listed in Open Questions and Edge Cases.
- **Technology and implementation:** No technology stack or implementation architecture is prescribed by this PRD.
- **Final approval:** Pending human review and resolution of relevant open questions.

---

## 12. Review and Validation Note

This PRD has been reviewed against the group's **PRD Critique and Human Validation Log**. The human decisions in that log have been applied as follows:

- The accepted findings about external-source integration, task prioritization, deadline conflicts and changes, synchronization and recovery, and requirement overlap do not authorize new assumptions or behavior. The existing requirements and related Open Questions remain unchanged where the validation log specified “No change.”
- The critique concerning incomplete Study Schedule rules was declined. FR-06, FR-07, and FR-09 remain as written, while their identified special cases remain open.
- The critique concerning measurable non-functional targets was declined. No response-time, availability, or other numerical targets have been invented.
- The critique concerning security and privacy clarification was declined. NFR-03 remains unchanged, and OQ-28 remains open for the testing method.
- The earlier rejection of FR-10, FR-11, and FR-12 as separate active requirements is confirmed. OQ-24 and OQ-25 remain open for the group to decide whether FR-07 and FR-09 should be combined.

This document is a revised draft that carries forward previously human-validated content and incorporates later user-selected clarifications. The v1.2 changes still require group validation, and the PRD is not finally approved. Final approval remains pending until the group resolves the open questions that affect acceptance testing and completes its required review against the class PRD structure and approved glossary. Unresolved matters remain explicitly recorded in the Open Questions and Edge Cases sections; they have not been answered by assumption.

### 12.1 v1.1 Revision Note

Version 1.1 applied three new requirements (Req#1 to Req#3) as FR-13, FR-14, and FR-15. They were not part of the original human validation review and remained pending human validation.

### 12.2 v1.2 Revision Note

Version 1.2 records the user's selections from the PRD/AGENTS review. Manual task creation and task deletion are excluded from the current product scope. User availability creation and update are introduced as FR-16, with detailed availability rules and architectural ownership still open. Completed tasks are excluded from Task Priority calculations and future Study Schedule generation or adjustment. Reminder delivery is through browser notifications; multiple reminders are supported; pending academic-deadline reminders are cancelled when a task is completed; passed reminder times are skipped with user notification; delivery failures are recorded and retried; and pending reminders are updated when their events are rescheduled. Because task deletion is not supported, reminder cancellation on task deletion is not an active behavior; deletion of Scheduled Study Sessions remains unresolved. Multiple timers may run simultaneously for different tasks, and timer state and elapsed time are to be recovered after browser closure or connection loss. Whether Recorded Study Sessions may be corrected, deleted, or manually created remains unresolved (OQ-46). These selections and the new FR-16 remain subject to group validation. The glossary terms marked *(proposed)* still await approval into the group's glossary. The v1.0 validation decisions continue to apply to content carried over unchanged.
