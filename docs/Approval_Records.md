# Approval Records

This file is an append-only index for real human authority decisions and immutable baselines. No formal record ID is pre-created by this template.

## Record Rules

- Create an ID only when a real decision exists.
- Never reuse an ID.
- Identify the exact artifact, commit/tag, scope, decision supplier, recorder, date, and evidence reference.
- Distinguish review, approval, risk acceptance, evidence acceptance, release, and Framework claim actions.
- A repository commit does not approve itself.

## Records

| ID | Type | Artifact / baseline | Scope | Decision | Decision supplier | Recorder | Date | Evidence |
|---|---|---|---|---|---|---|---|---|
| FRZ-001 | Freeze approval | `host-device-control-poc-system` repository tree identified as `v0.2.1` | Cross-platform LF governance patch only; Protocol, wire behavior, transport policy, implementation gaps, and evidence conclusions unchanged | Approved promotion of reviewed `v0.2.1-rc.1` content to frozen `v0.2.1`; commit/tag/Release identity and release approval remain pending | Repository owner | AI-assisted recorder | 2026-07-27 | Explicit user instruction to freeze; see `CHANGELOG.md` and `baselines/repositories.yaml` |
