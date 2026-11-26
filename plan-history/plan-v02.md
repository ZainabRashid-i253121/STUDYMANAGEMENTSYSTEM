# plan.md — Study Management System Implementation Plan

**Project:** Group #7 — Study Management System  
**Stage:** 2 — Validate & Plan  
**Plan version:** v0.2 — revised from v0.1  
**Status:** Draft for project-team review  
**Planning basis:** `final-prd.md` (PRD v1.2), `architecture.md`, `AGENTS.md`, and ADR-001 to ADR-006.

> This plan groups the original 27 proposed slices into 12 broader vertical slices. It does not approve unresolved requirements or proposed ADR decisions. Testing and final verification are a separate Stage 5 activity, not an implementation slice.

---

## 1. Product Objective

The Study Management System is a web application for Ms. Arooj to organize academic tasks and deadlines, understand task priority, create and adjust a Flexible Study Schedule, import academic tasks from an external source (subject to feasibility), track task completion, configure in-app reminders, and record study time.

The system is an organizational and planning aid. It must not take responsibility for academic performance, make academic decisions on the user's behalf, act as the official source of academic deadlines, or assess academic work.

## 2. Planning Rules, Assumptions, and Open Decisions

### 2.1 Source-document authority

- The PRD is the authority for product scope, requirement wording, acceptance criteria, business rules, edge cases, and open questions.
- `architecture.md` and ADR-001 to ADR-006 define the proposed architecture, module boundaries, data ownership, and communication approach.
- The supplied ADRs have **Proposed** status. Do not describe their decisions as finally approved.
- The PRD v1.2 is an updated draft and final approval is pending. FR-13 and FR-15 retain their recorded validation status unless the group formally changes it.
- Where `AGENTS.md` conflicts with the PRD, architecture, or ADRs, do not silently choose one version. Resolve the conflict with the group before implementing the affected behavior.

### 2.2 Architecture assumptions from the supplied documents

1. The proposed architecture is a **Layered Modular Monolith**: Presentation, Business, and Data Access layers, initially deployed as one application.
2. The proposed persistence approach is one centralized relational database, logically organized by module ownership. The database product is not yet selected.
3. Operations within one domain use database transactions. Cross-module dependent updates use events and eventual consistency, not distributed transactions.
4. There is one proposed role: **Registered User**. Users may access only their own private records. No Administrator role is in the current scope.
5. Domain Rules is a shared Business Layer component, not a separate business module. It is the single enforcer of domain invariants for state-changing operations.
6. Modules communicate through defined internal service interfaces and events. Modules must not access another module's private implementation or database tables directly.
7. Task Management owns academic tasks, deadlines, completion information, Recorded Study Sessions, and total recorded study time.
8. Priority owns Task Priority.
9. Schedule Management owns user availability, the Study Schedule, and Scheduled Study Sessions.
10. Reminder owns reminder preferences, configurations, and pending reminders.
11. External Integration owns staged imported task information and synchronization logs. Domain Rules validates staged data; Task Management accepts validated tasks.
12. **Recorded Study Sessions** (historical study activity) and **Scheduled Study Sessions** (planned future activity) are different concepts and must not be conflated.
13. Reminders are in-app notifications using a background scheduling mechanism. Delivery while the application is closed depends on deployment capabilities and is not guaranteed independently of the environment.
14. Manual task creation is not established as an approved requirement. The documented supported path is external import followed by validation and acceptance. The group must resolve what happens if external import is infeasible.

### 2.3 Decision gates

The following matters must be resolved by the group before implementing the affected behavior. A blocked part of a slice must not be implemented by guessing.

| Gate | Decision required | Affected slice(s) |
|---|---|---|
| G-01 | Select language, framework, database product, hosting/deployment, background-processing mechanism, event mechanism, and test framework. | S01, S02, S09, S12 |
| G-02 | Decide authentication mechanism, credential/password handling, session management, and any external authentication provider. | S02, S06 |
| G-03 | Select the external academic source and establish feasibility and authentication approach. | S06 |
| G-04 | Decide import behavior for duplicates, incomplete data, cancelled/disappearing tasks, partial updates, outdated information, and retries. | S06 |
| G-05 | Approve exact prioritization rules, including equal deadlines, missing deadlines, and unclear outcomes. | S03, S04, S05, S06, S07 |
| G-06 | Define valid deadline changes, conflict conditions, disputed values, review timing, and conflict effects on priority/scheduling. | S04, S05, S06, S08 |
| G-07 | Approve scheduling rules, availability format, insufficient-time behavior, overlaps, missed sessions, automatic vs user-approved adjustment, preserved session details, and the FR-07/FR-09 relationship. | S07, S08 |
| G-08 | Decide completion-list defaults, completion effects on priority/scheduling, completion-date behavior on reversion, and existing scheduled sessions when a task is completed. | S03, S05, S07, S09, S10 |
| G-09 | Decide reminder-time choices, multiple reminders, passed reminder times, completed-task reminders, delivery-failure handling, and deployment background-processing capability. | S09 |
| G-10 | Decide concurrent timer behavior, interrupted timer recovery, timer behavior for completed/deleted tasks, sessions spanning midnight, and whether Recorded Study Sessions can be corrected/deleted/manually created. | S10, S11 |
| G-11 | Decide what happens to Recorded Study Sessions when their associated task is deleted. | S11 |
| G-12 | Decide backup frequency/retention, recovery scenarios, recovery verification, event retry interval, and maximum attempts. | S01, S12 |
| G-13 | Define measurable usability, browser compatibility, security, performance, and availability targets and verification procedures. | Stage 5 validation; UI work as applicable |
| G-14 | Reconcile contradictions between `AGENTS.md`, PRD v1.2, architecture, and ADR-006; decide the manual-task-entry gap. | S03, S06, S07, S08, S09, S10, S11 |
| G-15 | Decide user-visible behavior when a cross-module event is delayed or fails, and define the operational recovery procedure. | S01, S09, S11, S12 |

### 2.4 Additional open issues to resolve

- **OI-01 — Task creation path:** If external import is infeasible, the PRD has no approved alternative task-creation requirement. Decide whether manual entry is in scope.
- **OI-02 — Deadline-change initiator:** Confirm whether deadline changes can be user-initiated, import-initiated, or both.
- **OI-03 — Schedule notification:** Confirm how Schedule Management learns about deadline and priority changes. The architecture does not fully specify the trigger mechanism.
- **OI-04 — Task deletion effects:** Decide effects on Priority data, Scheduled Study Sessions linked to the task, and imported staging records.
- **OI-05 — Scheduled-session deletion:** Decide whether deleting a Scheduled Study Session triggers schedule adjustment.
- **OI-06 — Availability ownership:** Architecture/ADR-006 assigns availability to Schedule Management, while `AGENTS.md` says not to assign ownership until the architecture is updated. Resolve through G-14.
- **OI-07 — Timer state location:** Decide where running/paused timer state is stored and how it is recovered.
- **OI-08 — Failed-event log access:** Define the authorized operator or maintenance process for investigating persistent event failures without introducing an unapproved Administrator role.
- **OI-09 — Schedule interaction direction:** Confirm the documented Schedule Management → Task Management service-call direction where the architecture diagram is ambiguous.
- **OI-10 — Approval status:** PRD approval remains pending, ADRs remain Proposed, and FR-13/FR-15 retain their validation status.

---

## 3. Vertical Slices

### Slice rules

- There are **12 implementation slices**. Each delivers a coherent increment of working product behavior across the layers it needs.
- A slice may contain several closely related requirements where they form one meaningful user capability.
- Each slice has acceptance criteria and requirement references. These are used to determine whether the slice is complete; they do **not** make testing a separate slice.
- Testing, regression checks, system-wide quality verification, and final acceptance are performed in **Stage 5**, after implementation slices have been integrated.
- Do not implement behavior that depends on an unresolved gate until the group has decided it.
- A slice can be split into smaller tasks for team allocation, but the team should retain the slice's single outcome and acceptance criteria.
- Keep the PRD's terminology precise: Study Schedule, Scheduled Study Session, Study Timer, Recorded Study Session, and Total Recorded Study Time are not interchangeable.

### S01 — Application foundation, persistence, Domain Rules, and module communication

**Outcome:** A runnable application foundation following the proposed Layered Modular Monolith structure. It includes the Presentation, Business, and Data Access layers; centralized relational persistence; domain-level transaction support; a shared Domain Rules validation gateway for state-changing operations; and the internal service/event communication foundation needed by the modules.

**In scope:**
- Establish the application structure and layer boundaries.
- Establish controlled Data Access interfaces and module-level data ownership boundaries.
- Establish database transaction handling and operation/event records.
- Establish the Domain Rules entry point so state-changing operations are validated before persistence commits.
- Establish event publication/consumption foundations, unique event identifiers, duplicate prevention, retry handling, and failure logging according to approved decisions.
- Provide the initial responsive application shell.

**Requirements / sources:** ADR-001, ADR-002, ADR-005, ADR-006; architecture §§4–7; NFR-02, NFR-04.

**Acceptance criteria:**
- The application starts and its layers have the documented responsibilities.
- Persistent data is accessed through the Data Access Layer.
- A state-changing operation can be rejected by Domain Rules without committing its changes.
- Modules can communicate through defined service interfaces and events rather than private implementation access.
- Event processing records identifiers and supports the approved retry/failure-handling policy.
- The UI shell supports desktop and mobile browser layouts.

**Dependencies / gates:** G-01, G-12, G-15, OI-08. This is the foundation for the remaining slices.

### S02 — Registration, authentication, and authorization

**Outcome:** A person can register as a Registered User, sign in, and access protected operations only when authenticated and authorized. Each user can access only their own records.

**In scope:**
- Registration and automatic assignment of the Registered User role.
- Sign-in and sign-out/session handling.
- Authorization checks at protected service interfaces and data retrieval/update operations.
- User-specific record ownership and isolation.

**Requirements / sources:** NFR-03; ADR-003; architecture §5; PRD OQ-51.

**Acceptance criteria:**
- Registration assigns the single Registered User role.
- Unauthenticated users cannot access protected operations.
- A user cannot view or modify another user's private records.
- Authorization is enforced by protected services/data operations, not only by hiding UI elements.

**Dependencies / gates:** S01; G-01, G-02. Authentication choices must be approved before implementation.

### S03 — Task dashboard and task completion tracking

**Outcome:** A signed-in user can view their academic tasks and available deadlines in one place, understand which tasks are completed or incomplete, and filter the list by completion status.

**In scope:**
- Task list/dashboard showing academic tasks and available deadlines.
- Tasks without deadlines remain visible and are marked as missing deadline information.
- Display task completion status.
- Mark a task Completed or Incomplete.
- Record the completion date according to the approved rule.
- Filter tasks by completion status.
- Provide brief guidance for the main features in the dashboard/onboarding experience.

**Requirements / sources:** FR-02 and AC-FR-02.1–02.2; FR-13 and AC-FR-13.1–13.6; NFR-01, NFR-02, NFR-03; BR-02, BR-06.

**Acceptance criteria:**
- The dashboard displays the user's own tasks and available deadlines.
- Tasks with no deadline remain visible and are clearly identified as missing deadline information.
- Completed and Incomplete tasks are visually distinguishable.
- The user can change completion status and filter by status.
- Marking a task Completed does not delete it or change its original deadline.
- Brief guidance is available for the main implemented features.
- The dashboard is usable on supported desktop and mobile browser layouts.

**Dependencies / gates:** S01, S02; G-05, G-08, G-13 (if a measurable usability target is set), G-14, OI-01. Task records must enter Task Management through an approved creation/acceptance path; do not silently add manual entry.

### S04 — Deadline management and conflict identification

**Outcome:** The user can make an approved deadline change. The system validates the change, updates the task deadline, and identifies/flags conflicts for the user's review without deciding the official deadline.

**In scope:**
- User-facing deadline update flow, subject to the group's decision on who may initiate changes.
- Domain Rules validation of deadline changes.
- Updating the task's deadline after an accepted valid change.
- Identifying and flagging deadline conflicts for user review.
- Notify dependent modules of successful deadline changes through the approved communication approach.

**Requirements / sources:** FR-03 and AC-FR-03.1–03.2; FR-04 and AC-FR-04.1; BR-01, BR-02, BR-04; ADR-005, ADR-006.

**Acceptance criteria:**
- A deadline is changed only when it satisfies the approved validity rules.
- An accepted change updates the stored deadline.
- A conflict that meets the approved definition is flagged for user review.
- The system does not claim to determine the official academic deadline.
- Dependent modules receive the approved notification after a successful change.

**Dependencies / gates:** S01, S02, S03; G-06, G-14, G-15, OI-02. Priority recalculation and schedule adjustment are handled by their respective slices.

### S05 — Task Priority calculation and display

**Outcome:** The system calculates and displays Task Priority according to the group's approved deadline-based rules. Closer deadlines receive higher priority as required, without inventing rules for unresolved cases.

**In scope:**
- Priority module and its ownership of Task Priority.
- Obtain task/deadline information through Task Management's service interface.
- Calculate and persist priority according to approved rules.
- Display task priority/order.
- Recalculate priority when relevant task/deadline information changes.
- Apply the approved behavior for Completed tasks and tasks without deadlines.

**Requirements / sources:** FR-05 and AC-FR-05.1–05.2; BR-01, BR-03; architecture §§5–7; ADR-005, ADR-006.

**Acceptance criteria:**
- Tasks with closer deadlines receive higher priority according to the approved rules.
- Equal-deadline and missing-deadline cases follow explicit group decisions; no unapproved tie-breaker is introduced.
- Priority is owned by the Priority module.
- Priority does not modify task deadlines.
- Recorded study time does not affect Task Priority.

**Dependencies / gates:** S01, S02, S03; G-05, G-08, G-14. S04 provides the deadline-change behavior that triggers recalculation.

### S06 — External academic task import and synchronization

**Outcome:** Subject to feasibility, the system imports academic tasks and available deadlines from the selected external source, stages and validates imported information before acceptance, reports failures accurately, and checks imported tasks for updates.

**In scope:**
- External source communication isolated in External Integration and Synchronization.
- Import staging and synchronization logs.
- Domain Rules validation before Task Management accepts imported tasks.
- Accurate reporting of failed or incomplete imports.
- Checking imported tasks and deadlines for updates.
- Applying accepted updates through the relevant Task Management operations.

**Requirements / sources:** FR-01 and AC-FR-01.1–01.3; FR-08 and AC-FR-08.1–08.2; BR-02; ADR-004, ADR-006; EC-01, EC-02, EC-10–EC-12.

**Acceptance criteria:**
- Imported information is staged before it becomes an accepted task.
- Domain Rules validates staged information before Task Management accepts it.
- Accepted tasks appear in the task list.
- Failed or incomplete imports are recorded and reported as unsuccessful.
- The system checks imported tasks/deadlines for updates.
- Unsuccessful update checks are not reported as successful.
- External communication remains isolated from Task Management.

**Dependencies / gates:** S01, S02, S03, S04, S05; G-02, G-03, G-04, G-06, G-14; OI-01, OI-02. If feasibility is not established, do not claim the import requirement is complete.

### S07 — User availability and Study Schedule creation/viewing

**Outcome:** The user can provide availability information and view a Study Schedule containing Scheduled Study Sessions organized around academic tasks, deadlines, Task Priority, and available time according to approved scheduling rules.

**In scope:**
- Create, update, and view the user's availability information.
- Create a Study Schedule.
- Display Scheduled Study Sessions.
- Retrieve task and priority information through defined module interfaces.
- Keep availability, Study Schedule, and Scheduled Study Sessions under the approved ownership boundary.

**Requirements / sources:** FR-06 and AC-FR-06.1–06.2; FR-07 availability input; architecture §§5–8; ADR-005, ADR-006.

**Acceptance criteria:**
- The user can manage their availability information.
- The Study Schedule displays Scheduled Study Sessions.
- Schedule creation uses task, deadline, priority, and availability information as defined by the approved rules.
- Schedule Management owns the Study Schedule and Scheduled Study Sessions.
- The system does not invent scheduling rules for insufficient availability, overlaps, or other unresolved cases.

**Dependencies / gates:** S01, S02, S03, S05; G-07, G-08, G-14, OI-06, OI-09.

### S08 — Flexible Study Schedule adjustments

**Outcome:** The Study Schedule can be adjusted when availability, relevant deadlines, or Task Priority change, according to the group's approved scheduling and user-approval rules.

**In scope:**
- Reflect availability changes in the Study Schedule.
- Support adjustments when relevant deadlines or priorities change.
- Apply approved rules for automatic or user-approved adjustments.
- Preserve session details as decided by the group.
- Notify Reminder when a Scheduled Study Session is successfully rescheduled.

**Requirements / sources:** FR-07 and AC-FR-07.1–07.2; FR-09 and AC-FR-09.1–09.2; ADR-005, ADR-006; EC-06–EC-09, EC-13.

**Acceptance criteria:**
- Availability changes are reflected in the Study Schedule according to approved rules.
- Relevant deadline and priority changes can trigger/support schedule adjustment.
- The system follows the approved adjustment/confirmation behavior.
- Successfully rescheduled Scheduled Study Sessions notify Reminder through the agreed event/interface.

**Dependencies / gates:** S01, S04, S05, S07; G-06, G-07, G-08, G-14, G-15, OI-03, OI-05.

### S09 — Reminder preferences, delivery, and updates

**Outcome:** The user can enable or disable reminders and configure reminder times for academic deadlines and Scheduled Study Sessions. The system delivers in-app notifications and updates or cancels pending reminders when the associated item changes, according to the PRD.

**In scope:**
- Reminder preferences and configured notification times.
- Pending reminders for academic deadlines and Scheduled Study Sessions.
- Background scheduling and in-app notification delivery.
- Suppress reminders while the user's reminder preference is disabled.
- Update pending reminders after a deadline or Scheduled Study Session is rescheduled.
- Cancel pending reminders when an associated task or Scheduled Study Session is deleted.
- Apply approved behavior for completed tasks and delivery failures.

**Requirements / sources:** FR-14 and AC-FR-14.1–14.7; BR-08; ADR-005, ADR-006; EC-17–EC-19, EC-25–EC-26.

**Acceptance criteria:**
- The user can enable/disable reminders.
- The user can configure reminder times for deadlines and Scheduled Study Sessions.
- In-app notifications are triggered at configured times subject to the selected deployment's background-processing capability.
- Disabled reminders are not triggered.
- Pending reminders are updated after associated rescheduling.
- Pending reminders are cancelled after approved task/session deletion behavior.
- Delayed/failed event and delivery behavior follows the group's documented decisions.

**Dependencies / gates:** S01, S02, S03, S04, S07, S08; G-01, G-06, G-09, G-14, G-15. Deletion-related cancellation is integrated with S11.

### S10 — Study Timer and Recorded Study Time

**Outcome:** The user can time study activity for a selected task, pause and resume the timer, save completed Recorded Study Sessions with duration and date, and view total recorded study time per task.

**In scope:**
- Start, pause, resume, and stop a Study Timer for a selected task.
- Save each completed timed session with duration and date.
- Display total Recorded Study Time per task.
- Support multiple concurrent timers only if confirmed by the approved PRD decision.
- Recover timer state and elapsed time after browser closure or connection loss according to the approved decision.
- Ensure timer activity does not change Task Priority or task deadlines.

**Requirements / sources:** FR-15 and AC-FR-15.1–15.6; BR-07; ADR-006; EC-20–EC-24.

**Acceptance criteria:**
- The user can start, pause, resume, and stop a timer for a selected task.
- A completed Recorded Study Session is saved with duration and date.
- Total Recorded Study Time is displayed per task.
- Paused time is handled according to the approved rule.
- Timer state recovery follows the approved interruption behavior.
- Timer operations and recorded time do not automatically modify Task Priority or deadlines.
- Recorded Study Sessions remain distinct from Scheduled Study Sessions.

**Dependencies / gates:** S01, S02, S03; G-08, G-10, G-14, OI-07. The slice must not assume unresolved timer behavior.

### S11 — Explicit deletion of tasks and Scheduled Study Sessions

**Outcome:** The user can explicitly delete an academic task or a Scheduled Study Session. The owning module performs the deletion and notifies Reminder so associated pending reminders are cancelled.

**In scope:**
- Explicit task deletion through Task Management.
- Explicit Scheduled Study Session deletion through Schedule Management.
- Domain Rules validation before deletion commits.
- Notify Reminder after successful deletion.
- Apply approved handling for dependent priority, schedule, staging, and Recorded Study Session data.

**Requirements / sources:** FR-16 and its acceptance criteria; FR-14 AC-FR-14.6; BR-08, BR-09; ADR-005, ADR-006; Flow 11 and Flow 12.

**Acceptance criteria:**
- The user can explicitly delete a task, subject to the approved deletion rules.
- The user can explicitly delete a Scheduled Study Session, subject to the approved deletion rules.
- Only the owning module changes its records.
- Reminder is notified after successful deletion and cancels associated pending reminders.
- Effects on dependent records follow explicit group decisions; no dependent data is silently orphaned or deleted by assumption.

**Dependencies / gates:** S01, S02, S03, S07, S09, S10; G-10, G-11, G-14, G-15, OI-04, OI-05.

### S12 — Backup, restoration, and operational recovery

**Outcome:** The system protects persisted application data through scheduled automated backups and can restore the database from the latest valid backup, reconcile pending events/operations, and verify dependent module data.

**In scope:**
- Scheduled automated database backups.
- Restore from the latest valid backup.
- Reconcile pending events and operations after restoration.
- Avoid reapplying effects that have already been processed by using event identifiers and processing records.
- Verify dependent module data after recovery.
- Re-synchronize external integration data where required.
- Document the recovery procedure and operational responsibilities.

**Requirements / sources:** NFR-04; ADR-002, ADR-005; PRD §10.10.

**Acceptance criteria:**
- Automated backups run according to the approved frequency and retention policy.
- The application database can be restored from the latest valid backup.
- Pending events/operations are reconciled after restoration.
- Already-applied event effects are not applied a second time.
- Dependent module data is verified after recovery.
- External integration is re-synchronized where the approved recovery procedure requires it.

**Dependencies / gates:** S01 and the persistence-owning slices implemented to date; G-01, G-12, G-15. This slice is completed after the main persistence and event flows exist.

---

## 4. Requirement Coverage

The following table shows where each PRD requirement is addressed. Cross-cutting non-functional requirements are also listed.

| Requirement | Slice |
|---|---|
| FR-01 — Import Academic Tasks | S06 |
| FR-02 — View Academic Tasks and Deadlines | S03 |
| FR-03 — Update Task Deadlines | S04 |
| FR-04 — Identify Conflicting Deadlines | S04 |
| FR-05 — Prioritize Academic Tasks | S05 |
| FR-06 — Create and View a Study Schedule | S07 |
| FR-07 — Adjust schedule when availability changes | S07, S08 |
| FR-08 — Check Imported Task Updates | S06 |
| FR-09 — Support Study Schedule Changes | S08 |
| FR-13 — Track Task Completion | S03 |
| FR-14 — Configure and Send Reminders | S09 |
| FR-15 — Study Timer and Recorded Study Time | S10 |
| FR-16 — Delete Tasks and Scheduled Study Sessions | S11 |
| NFR-01 — Usability / guidance | S03; overall review in Stage 5 |
| NFR-02 — Desktop and mobile browser compatibility | S01 and all UI slices; overall review in Stage 5 |
| NFR-03 — Security and private user records | S02 and protected operations in all slices; overall review in Stage 5 |
| NFR-04 — Backup and recovery | S01, S12 |
| NFR-05 — Performance | Requirements/targets established and verified in Stage 5 |
| NFR-06 — Availability | Requirements/targets established and verified in Stage 5 |

**Coverage note:** Requirement coverage does not mean every behavior is ready to implement. The gates in Section 2.3 must be resolved first. In particular, external import is subject to feasibility, and several priority, scheduling, reminder, timer, and deletion rules remain open.

---

## 5. Dependencies and Parallel Work

### 5.1 Are the 12 slices independent?

No. They are separate implementation units, but they are **not all independent**. Some need data, interfaces, or behavior delivered by earlier slices.

A useful distinction:

- **Hard dependency:** the later slice cannot be completed until the earlier slice provides its required capability.
- **Parallelizable work:** different members can work at the same time if they agree on interfaces, data contracts, and ownership first.
- **Decision dependency:** a slice may be technically ready but must wait for the group to resolve an open gate.

### 5.2 Slice dependencies

| Slice | Hard dependencies | Reason |
|---|---|---|
| S01 | None (but G-01 decisions are required) | Establishes the application and shared technical foundations. |
| S02 | S01 | Authentication uses the application structure and persistence. |
| S03 | S01, S02 | Task data and dashboard operations require persistence and protected access. |
| S04 | S01, S02, S03 | Deadline changes and conflicts operate on existing tasks. |
| S05 | S01, S02, S03 | Priority needs task/deadline information from Task Management. |
| S06 | S01, S02, S03, S04 | Import needs staging, validation, task acceptance, and update paths. |
| S07 | S01, S02, S03, S05 | Schedule creation needs availability, tasks, and priority information. |
| S08 | S01, S04, S05, S07 | Schedule adjustment responds to availability, deadline, and priority changes. |
| S09 | S01, S02, S03, S04, S07, S08 | Reminders need task deadlines, scheduled sessions, and rescheduling notifications. |
| S10 | S01, S02, S03 | Timer records are associated with existing tasks. |
| S11 | S01, S02, S03, S07, S09, S10 | Deletion affects tasks/sessions, reminders, and potentially recorded study data. |
| S12 | S01 and persistence/event flows from implemented slices | Recovery must account for persisted data and pending events. |

### 5.3 Suggested parallel work

After S01's shared foundations and interfaces are agreed, some work can proceed in parallel:

- S04 (deadline changes) and S05 (priority) can be developed in parallel after the Task Management interface and task data contract from S03 are stable.
- S06 (external integration) can be developed alongside S07 (availability and schedule creation) once their interfaces and shared data contracts are agreed. S06 still needs the task acceptance and deadline-update interfaces.
- S10 (timer) is largely independent of schedule and reminder implementation once S03's task interface exists.
- S09 (reminders) can be prepared while S08 is being implemented, but its rescheduling integration depends on the event contracts and schedule/deadline producers.
- S12 (recovery) should be finalized after the main persistence and event flows are implemented.

Parallel work does not remove the need for integration. Agree on service interfaces, event names/payloads, ownership, and shared data structures before members implement against them.

---

## 6. Suggested Implementation Order

This is a proposed order, not a claim that every slice must be completed strictly one after another.

1. S01 — Application foundation, persistence, Domain Rules, and module communication
2. S02 — Registration, authentication, and authorization
3. S03 — Task dashboard and task completion tracking
4. S04 — Deadline management and conflict identification
5. S05 — Task Priority calculation and display
6. S06 — External academic task import and synchronization
7. S07 — User availability and Study Schedule creation/viewing
8. S08 — Flexible Study Schedule adjustments
9. S09 — Reminder preferences, delivery, and updates
10. S10 — Study Timer and Recorded Study Time
11. S11 — Explicit deletion of tasks and Scheduled Study Sessions
12. S12 — Backup, restoration, and operational recovery

If a slice is blocked by an unresolved gate, the team may continue with another slice whose dependencies are satisfied. Do not implement the blocked behavior by making an unapproved assumption.

---

## 7. Separate Stage 5 — Testing, Final Validation, and Demonstration

**Testing is not one of the 12 implementation slices.** It is a separate project phase after the implementation slices have been integrated.

Stage 5 must include:

- Verify each slice against its acceptance criteria and linked PRD requirements.
- Run integration checks across module/service/event boundaries.
- Run regression checks to ensure previously accepted functionality still works.
- Verify authentication, authorization, and user-specific data isolation.
- Verify desktop/mobile browser compatibility against the agreed support list.
- Verify performance and availability against measurable targets approved under G-13.
- Verify backup, restoration, event reconciliation, and recovery procedures.
- Verify import failure/partial outcome behavior if external integration is feasible and implemented.
- Review the final system against the PRD, architecture, ADRs, and AGENTS.md.
- Record results, unresolved limitations, human acceptance/revision decisions, and demonstration evidence.

Do not mark the product fully validated merely because all 12 slices have been implemented.

---

## 8. Per-Slice Implementation and Review Loop

For each slice during Stage 4:

1. Select the slice and identify its requirement IDs and acceptance criteria.
2. Check that its hard dependencies are complete and its decision gates are resolved.
3. Give the AI only the relevant PRD, architecture, ADR, AGENTS.md, prior code, and supporting artefacts.
4. Refine the slice's acceptance criteria and implementation approach before coding.
5. Choose **HITL** (human review/approval during execution) or **AFK/delegated execution** based on uncertainty, risk, and importance. Record the mode and reason.
6. Implement only the selected slice; do not ask for the entire product in one prompt.
7. Review the implementation against the slice's scope and acceptance criteria. This is slice-level review, not the separate Stage 5 system-wide testing phase.
8. Human reviewer records Accept, Revise, or Reject with a reason.
9. Integrate accepted work and resolve interface conflicts with other members.
10. Update `plan.md`, architecture, or ADRs if implementation reveals a necessary change. Do not silently change an approved boundary or requirement.

### 8.1 Slice completion record

For each slice, keep a short record containing:

- Slice ID and name.
- Requirement IDs covered.
- Dependencies and decision gates cleared.
- Implementation owner(s).
- HITL/AFK mode and reason.
- Relevant code/commit or task reference.
- Human review decision and reason.
- Remaining limitations or follow-up work.

---

## 9. Plan Maintenance and Version History

This plan is a living artefact. Update it when:

- A decision gate is resolved.
- A requirement, scope item, or acceptance criterion changes.
- A slice is split, combined, reordered, or re-scoped.
- A dependency or module interface changes.
- Implementation reveals an architectural issue or a new open question.

Preserve meaningful versions in Git history or as separate versioned files (for example, `plan-v01.md`, `plan-v02.md`). Do not overwrite the only record of a previous approved plan.

| Version | Description |
|---|---|
| v0.1 | Initial plan containing 27 proposed slices. |
| v0.2 | Consolidated implementation plan containing 12 slices; testing and final validation moved to a separate Stage 5 phase. |

---

## 10. Important Scope and Consistency Warnings

1. `AGENTS.md` currently says task deletion is not supported, while PRD v1.2, architecture, and ADR-006 describe explicit task deletion. Resolve this under G-14 before S11.
2. `AGENTS.md` treats Scheduled Study Session deletion as unresolved, while PRD v1.2 and ADR-006 describe it. Resolve this under G-14 before S11.
3. `AGENTS.md` says availability ownership should not be assigned until architecture is updated, while architecture and ADR-006 assign it to Schedule Management. Resolve this under G-14 before S07.
4. `AGENTS.md` says completed tasks are excluded from priority and future schedule generation/adjustment, while the PRD retains open questions about completion effects. Resolve G-08 before implementing those effects.
5. The PRD defines Manual Task Entry in its glossary, but the functional requirements do not establish it as an implemented feature; `AGENTS.md` says manual task creation is not supported. Resolve OI-01/G-14, especially if external import is infeasible.
6. The exact prioritization and scheduling rules are not fully specified. Do not invent formulas, tie-breakers, scheduling behavior, or automatic adjustment rules.
7. External source selection and feasibility are unresolved. Do not present external import as complete unless a feasible source and approved integration path exist.
8. All ADRs are Proposed in the supplied documents. Preserve that status unless the group formally approves them.
