# ADR-006: Module Responsibilities, Domain Rules, and Data Ownership

**Status:** Proposed

## Context

The Study Management System is a Layered Modular Monolithic application (ADR-001). Its modules read and update related data. Explicit ownership is needed to prevent multiple modules from independently changing the same records or duplicating business rules.

This ADR defines module data ownership, the shared Domain Rules boundary, imported-data staging and acceptance, and the Reminder Module boundary. It builds on ADR-002 (persistence), ADR-003 (authentication and authorization), ADR-004 (external integration), and ADR-005 (module communication).

FR-13 to FR-15 originated as additional requirements in the supplied PRD. Their original validation status must be retained unless the project team formally changes it.

## Alternatives Considered

### Data ownership
1. Each category of data has one owning module; other modules access it through the owner's interfaces.
2. Data is shared and any module may read and write any record.
3. Ownership is assigned only by technical layer, without module-level ownership.

### Business-rule enforcement
1. Each module enforces business rules independently.
2. One shared Domain Rules component enforces business rules within the Business Layer.

### Imported data lifecycle
1. External Integration owns staging, Domain Rules validates, and Task Management accepts validated tasks.
2. Task Management owns imported information from the moment it is received.
3. Imported data is written directly to shared tables before validation.

## Decision

The proposed decision has five parts.

### 1. Single-module data ownership

| Data | Owner |
|---|---|
| Academic tasks, deadlines, completion status/date, explicit task deletion | Task Management |
| Recorded Study Sessions and total recorded study time | Task Management |
| Task Priority | Priority |
| User availability, Study Schedule, Scheduled Study Sessions, and scheduled-session deletion | Schedule Management |
| Reminder preferences, configurations, and pending reminders | Reminder |
| Users, authentication information, and role assignments | Authentication and Authorization |
| Staged imported task information and synchronization log | External Integration and Synchronization |

Each category has one owner. Other modules retrieve information or request changes only through the owner's defined service interfaces (ADR-005). Handling or using information does not make a module its owner.

### 2. Recorded and Scheduled Study Sessions

- Task Management owns **Recorded Study Sessions**, which represent study activities the user has completed or recorded.
- Schedule Management owns **Scheduled Study Sessions**, which represent planned study activities organized for future dates and times.
- Each module manages its own records and exposes required information through defined service interfaces.

### 3. Shared Domain Rules component

Domain Rules is a shared component within the Business Layer. It is not a business module and owns no persistent business records. It is the **single enforcer** of domain invariants.

Its responsibilities include:
- Validating state-changing operations before persistence.
- Enforcing that marking a task Completed does not itself delete the task or change its original deadline (BR-06).
- Enforcing that timer operations and recorded study time do not automatically change Task Priority or task deadlines (BR-07).
- Validating staged imported data and import/synchronization outcomes before acceptance or success reporting.
- Ensuring failed or incomplete imports are never presented as successful.
- Identifying deadline conflicts and flagging them for user review.

Domain Rules does not decide the official academic deadline and does not make academic decisions for the user. It does not depend on presentation, database, or external-source implementation details.

All state-changing operations pass invariant validation in Domain Rules before the corresponding Data Access operation is committed. Read-only queries may use Data Access interfaces directly, subject to authentication, authorization, and ownership rules.

### 4. Imported task staging and acceptance

The imported-data lifecycle is explicitly assigned:
1. External Integration receives and stores imported information as staged data. External Integration owns staged records.
2. Domain Rules validates the staged information and relevant synchronization outcome.
3. Task Management accepts validated imported tasks and becomes the owner of the accepted application task records.
4. External Integration continues to own staging records and synchronization logs.

External Integration does not apply business rules and does not write directly to database tables.

### 5. Reminder Module boundary and deletion behavior

Reminder owns reminder preferences, configurations, and pending reminders for academic deadlines and Scheduled Study Sessions. It does not own task or Scheduled Study Session records.

- Users control reminder preferences, including enabling or disabling reminders and configuring notification times.
- Reminders are delivered through in-app notifications.
- Reminder uses a background scheduling mechanism to trigger notifications at configured times. Delivery while the application is closed depends on background-processing capabilities of the deployment environment.
- Task Management owns task deletion. After a task is successfully deleted, Task Management notifies Reminder, which cancels associated pending reminders.
- Schedule Management owns Scheduled Study Session deletion. After a scheduled session is successfully deleted, Schedule Management notifies Reminder, which cancels associated pending reminders.
- The same owning modules notify Reminder after successful rescheduling so pending reminders can be updated.
- These reminder associations apply to tasks and Scheduled Study Sessions, not Recorded Study Sessions.

## Rationale

Single-module ownership gives each record category one place where it can be changed. Domain Rules provides one enforcement point for shared invariants and deadline-conflict identification. Explicit staging prevents unvalidated external data from becoming an accepted task. The Reminder boundary keeps reminder configuration and delivery separate from task and schedule ownership while allowing reminders to react to successful changes.

## Trade-offs / Consequences

- Gives each data category one clear owner.
- Reduces duplicated or bypassed business rules.
- Makes the distinction between historical Recorded Study Sessions and planned Scheduled Study Sessions explicit.
- Requires modules to use service interfaces and events to access or react to data they do not own.
- Domain Rules is an important dependency for state-changing operations.
- Imported tasks cannot become accepted Task Management records until Domain Rules validation succeeds.
- Event-driven reminder updates may be temporarily delayed; retries and recovery support eventual consistency.
- In-app notification behavior when the application is closed depends on deployment capabilities.
