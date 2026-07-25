# Decision Log

| ID | Date | Topic | Decision / current direction | Status | Rationale / next action |
|---|---|---|---|---|---|
| DEC-001 | 2026-07-25 | System repository role | Use a separate system/project repository to bind Framework, template, PC, MCU, and evidence | Proposed | Prevent shared project meaning and evidence from being owned by one implementation repository |
| DEC-002 | 2026-07-25 | Repository name | Use `host-device-control-poc-system` | Proposed | Consistent with existing PoC names and clearly indicates cross-repository system scope |
| DEC-003 | 2026-07-25 | Source baselines | Pin exact commits for every validation cycle | Active | Mutable `main` cannot identify what combination was actually tested |
| DEC-004 | 2026-07-25 | Protocol ownership | Move canonical Protocol authority to the system/project layer or enforce controlled synchronization | Proposed | The Protocol is shared and shall not be semantically PC-owned or MCU-owned |
| DEC-005 | 2026-07-25 | Evidence status | Use explicit `OBSERVED`, `NOT RUN`, and `IN PROGRESS` states | Active | Avoid manufacturing pass evidence during development |
| DEC-006 | 2026-07-25 | Conformance | Do not claim Framework conformance in the initial PoC framework | Active | Applicability, evidence, and approval prerequisites are incomplete |
