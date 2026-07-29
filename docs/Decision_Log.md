# Decision Log

| ID | Date | Topic | Decision / current direction | Status | Rationale / next action |
|---|---|---|---|---|---|
| DEC-001 | 2026-07-25 | System repository role | Use a separate system/project repository to bind Framework, template, PC, MCU, and evidence | Active | Prevent shared project meaning and evidence from being owned by one implementation repository |
| DEC-002 | 2026-07-25 | Repository name | Use `host-device-control-poc-system` | Active | Consistent with existing PoC names and clearly indicates cross-repository system scope |
| DEC-003 | 2026-07-25 | Source baselines | Pin exact commits for every validation cycle | Active | Mutable `main` cannot identify what combination was actually tested |
| DEC-004 | 2026-07-25 | Protocol authority | Control the canonical Protocol at `protocol/protocol.yaml`; implementation repositories are non-authoritative | Active | The Protocol is shared and shall not be semantically PC-owned or MCU-owned |
| DEC-005 | 2026-07-25 | Evidence status | Use explicit `OBSERVED`, `NOT RUN`, and `IN PROGRESS` states | Active | Avoid manufacturing pass evidence during development |
| DEC-006 | 2026-07-25 | Conformance | Do not claim Framework conformance in the initial PoC framework | Active | Applicability, evidence, and approval prerequisites are incomplete |
| DEC-007 | 2026-07-25 | Protocol lifecycle | Treat v0.1.0 as `candidate_for_alignment` until both implementations and hardware evidence agree | Active | Prevent specification authority from being confused with completed verification |

| DEC-008 | 2026-07-27 | Work continuity | Use `WORK_CONTINUATION.md` as a mutable, non-authoritative handoff record across AI tools, models, providers, sessions, and engineers | Active | Preserve portable working state without allowing chat or AI memory to become engineering authority |
| DEC-009 | 2026-07-27 | Repository version lifecycle | Use `vMAJOR.MINOR.PATCH-rc.N` during review; promote only after explicit authorized-human freeze approval | Active | Prevent iterative discussion from rapidly consuming formal versions and distinguish mutable candidates from frozen baselines |
| DEC-010 | 2026-07-27 | Upstream alignment history | Preserve the initial baseline and add a separate alignment cycle for newer Framework/Template working sources | Active | Avoid rewriting history while allowing deliberate methodology upgrades with explicit impact and source identity |
| DEC-011 | 2026-07-27 | Cross-platform line endings | Treat LF as the canonical repository text form and enforce it through `.gitattributes` plus validation | Active | Frozen in repository baseline `v0.2.1`; prevent Windows checkout conversion from dirtying the complete tree or invalidating byte-based Protocol provenance |
| DEC-012 | 2026-07-29 | Coordinator Presentation boundary | Treat WPF as a replaceable Presentation adapter; keep Application/Core, Protocol, device-session, and transport-contract behavior free of direct WPF dependency | Active | Align the PoC with Framework and Project Template v1.1.2 while accepting that View/XAML, binding, navigation, charts, and framework-specific ViewModels may require reimplementation |
