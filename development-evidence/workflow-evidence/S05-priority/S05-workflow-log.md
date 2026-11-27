# S05 – Task Priority Calculation and Display
## Workflow Evidence Log

### Entry 1: Requirements and Implementation

**Responsible member:** Person 2  
**Slice:** S05 – Task Priority Calculation and Display  
**Implementation mode:** AFK (AI implementation with human review)

The S05 requirements and acceptance criteria were reviewed before implementation. The following priority rules were agreed upon:

- **High:** Overdue or deadline within 3 days.
- **Medium:** Deadline 4–7 days away.
- **Low:** Deadline more than 7 days away.
- Missing deadlines receive the lowest priority.
- Tasks with equal deadlines receive equal priority.
- Unclear outcomes are marked Undetermined and require review.
- Completed tasks are excluded from priority calculation.
- Deadline conflicts do not change priority and remain a separate flag.
- Priority calculation uses conflict information from Domain Rules rather than duplicating conflict detection.

The implementation was completed for the core S05 functionality.

### Entry 2: Implementation and Testing

The implementation was tested locally using the project's virtual environment.

**Test commands and results:**

```cmd
python -m pytest -q tests/test_s05_priority.py
```

Result: **8 passed in 0.93s**

```cmd
python -m pytest -q
```

Result: **141 passed in 8.09s**

No test failures occurred.

Test evidence screenshots were saved in:

`development-evidence/test-evidence/S05-priority/`

### Entry 3: Final Human Review and Acceptance

**Human decision: ACCEPT**

The responsible member reviewed the implementation and local test results and accepted the core S05 functionality.

The following limitation was identified and documented:

**AC-07 – Insufficient Study Time**

The existing system does not provide the estimated study-duration information required to determine whether a task has insufficient study time.

Therefore:
- Priority remains unchanged.
- The scheduling-review flag is deferred to the Schedule slice.
- This flag is not claimed as implemented in S05.

The deferral does not prevent acceptance of the core S05 functionality.

### Scope and Architecture

- The implementation follows the agreed S05 priority rules.
- Conflict identification remains owned by Domain Rules, following ADR-006.
- No unrelated slice changes were intended.
- S04 and S09 were not part of this implementation.

### Integration Status

**Pending.**

S05 has been accepted locally but has not yet been integrated with Person 1's S01–S03 implementation.

Integration, merge-conflict resolution and integrated testing will take place later when the group is ready.

### Evidence Collected

- S05-specific test results screenshot.
- Full test suite results screenshot.
- AI implementation and review interactions.
- Final human acceptance decision.

### Final Status

**S05: ACCEPTED**

Core functionality implemented and tested successfully. AC-07 scheduling-review flag deferred to the Schedule slice. Integration remains pending.
