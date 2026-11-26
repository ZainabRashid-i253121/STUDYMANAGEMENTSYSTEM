# ADR-005: Communication Between System Modules

**Status:** Proposed

## Context

The Study Management System contains modules with related responsibilities. A task deadline change may affect priority and may cause other modules to update dependent information. Rescheduling or deleting tasks and Scheduled Study Sessions affects pending reminders.

Modules must exchange information without direct access to each other's internal implementation or owned database tables. The system uses a hybrid consistency approach: domain operations are transactional, while cross-module dependent updates use events and eventual consistency.

## Alternatives Considered

1. Direct communication through internal implementation access.
2. Direct access to shared database records by all modules.
3. Defined internal service interfaces and events.

## Decision

Modules will communicate through **defined internal service interfaces and events**.

### Service calls

Service calls are used when a module:
- Requires an immediate response.
- Needs to retrieve information owned by another module.
- Requests an operation from another module.

For example, Schedule Management may request task information from Task Management through Task Management's defined service interface.

### Events

Events are used to notify interested modules after an operation has successfully completed and other modules need to respond independently.

For example, when a Scheduled Study Session is successfully rescheduled, Schedule Management generates an event to notify Reminder. Task Management similarly notifies Reminder after a task is successfully rescheduled or deleted.

### Event processing and failure handling

- Cross-module dependent updates use event-driven communication and eventual consistency.
- The background event-processing mechanism manages retries according to a predefined retry policy.
- Retry interval and maximum attempts are configured during implementation.
- Unique event identifiers are used to prevent duplicate processing during retries.
- Events that continue to fail after the retry limit are logged for investigation.
- An authorized system operator or maintenance process investigates persistent failures and initiates recovery where necessary.
- Operation logs support investigation and reconciliation.
- Following database restoration, pending events/operations are reconciled and dependent module data is verified. Reconciliation must account for event identifiers and processing records to avoid applying an already-completed effect twice.

The exact event technology and implementation details remain open.

## Eventual Consistency

Cross-module updates may not be reflected immediately in every dependent module. For example, after a task is deleted, its associated reminder may remain temporarily until the deletion event is successfully processed. Retry and recovery mechanisms support eventual consistency across dependent modules.

## Rationale

Service interfaces provide explicit boundaries for immediate requests and information retrieval. Events allow independent modules to react to completed operations without requiring the initiating module to directly control every dependent module. This reduces unnecessary coupling while making eventual consistency and failure recovery explicit.

## Trade-offs / Consequences

- Reduces direct dependencies between modules.
- Protects module ownership and implementation boundaries.
- Supports immediate request/response interactions through service calls.
- Supports independent dependent updates through events.
- Cross-module changes may be temporarily inconsistent.
- Requires event identifiers, retry processing, failure logging, operation logs, and recovery/reconciliation procedures.
- Poorly designed interfaces or event contracts can still create unnecessary dependencies.
