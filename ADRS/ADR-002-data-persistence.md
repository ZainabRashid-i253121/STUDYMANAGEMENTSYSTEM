# ADR-002: Data Persistence, Transactions, Backup and Recovery

**Status:** Proposed

## Context

The Study Management System stores tasks, deadlines, completion information, Recorded Study Sessions, priorities, user availability, Scheduled Study Sessions, reminders, user access information, staged imported data, and synchronization/operation records.

The system must maintain accurate information and support recovery. Operations within one domain require transactional consistency. Updates that span module boundaries use event-driven communication and eventual consistency rather than distributed transactions.

## Alternatives Considered

1. File-based storage
2. Relational SQL database
3. NoSQL database

## Decision

The proposed decision is to use a **centralized relational database** for persisted application data. Data is logically organized according to module ownership. The database product remains to be selected.

Operations within an individual domain use database transactions so that the domain's changes are committed together or rolled back on failure. Cross-module dependent updates are communicated through events and are eventually consistent; they do not require a distributed transaction spanning modules.

The system will maintain operation logs and event identifiers. Scheduled automated database backups will protect persisted application data. Recovery will restore the application database from the latest valid backup, followed by reconciliation of pending events/operations and verification of dependent module data. External integrations may require synchronization after restoration.

## Rationale

File-based storage was rejected because relationships among tasks, scheduled sessions, reminders, and users would require additional manual handling. File storage also does not provide the same built-in relational constraints and transaction support needed for domain-level consistency.

NoSQL storage was considered but rejected because its flexible data models and varying transaction capabilities would introduce additional data-modeling and consistency considerations without a clear benefit for this system's structured relationships.

Relational SQL storage was selected because it supports structured records, primary and foreign key constraints, and transactions. Centralized persistence also simplifies controlled access across modules while module ownership is enforced through service and Data Access boundaries.

## Transaction and Event Consistency

- A state-changing operation within one domain uses a database transaction.
- Cross-module changes are communicated through events after the initiating operation has successfully completed.
- Dependent modules process events independently. Their data may temporarily lag behind the initiating operation.
- Event retries and duplicate prevention are defined in ADR-005.
- Reconciliation after restoration must account for event identifiers and processing records so that already-applied effects are not applied again.

## Backup and Recovery

- Scheduled automated database backups protect persisted application data.
- The recovery boundary is the application database and its persisted records.
- Restoration uses the latest valid backup available.
- After restoration, pending events and operations are reconciled and dependent module data is verified.
- External integrations may need to be synchronized again after restoration.
- Backup frequency, retention, database product, and implementation details remain to be decided during implementation.

## Trade-offs / Consequences

- Supports structured data organization and relational integrity.
- Supports atomic updates within an individual domain.
- Cross-module updates may be temporarily inconsistent until events are processed.
- Requires event retry, duplicate prevention, logging, and reconciliation.
- Requires database design, backup scheduling, and recovery procedures.
- Database availability is important to the application as a whole.
