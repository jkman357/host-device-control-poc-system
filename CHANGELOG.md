# Changelog

## v0.1.3 — 2026-07-25

- Corrected GitHub Actions to `actions/checkout@v6` and `actions/setup-python@v6`.
- Added `fetch-depth: 0` and required Git-history provenance validation in CI.
- Verified that the pinned authority commit exists, is an ancestor of `HEAD`, contains the authoritative Protocol path, and matches the recorded historical SHA-256.
- Added frame-field type/size and per-field byte-order consistency checks.
- Added sequence-width, direct-response sequence-copy, direction/kind, and command-response relationship checks.
- Changed vector decoding to use each field's declared byte order rather than silently relying on a global default.
- Expanded regression coverage to reject endian conflicts, type/size mismatches, sequence-rule mismatches, event-as-response misuse, missing Git history in strict mode, historical blob drift, and fake authority commits.
- Preserved Protocol version `0.1.0`, wire version `0x01`, and the pinned authority commit; no wire-format change was made.

## v0.1.2 — 2026-07-25

- Pinned the Protocol authority provenance to commit `e4aa40b4d5dfc3e7f878f82f5a89115de9fe3679`.
- Replaced marker and regular-expression checks with safe YAML parsing and semantic cross-file validation.
- Added frame-layout, metadata, message-definition, version, SHA-256, CRC, and vector-coverage checks.
- Added regression tests for malformed YAML, vector metadata mismatch, framing-offset mismatch, and stale Protocol hashes.
- Updated GitHub Actions to `actions/checkout@v7` and `actions/setup-python@v7`.
- Added a pinned PyYAML validation dependency.


## v0.1.1 — 2026-07-25

- Established `protocol/protocol.yaml` as the authoritative PC/MCU communication contract.
- Added normative test vectors, protocol lifecycle, compatibility rules, and implementation provenance requirements.
- Added machine-readable implementation alignment status.
- Recorded blocking differences between the candidate contract and the observed compiled STM32 implementation.
- Extended CI validation to cover Protocol files and vector CRCs.


## v0.1.0 — 2026-07-25

- Established the system/project integration repository structure.
- Defined the relationship and responsibility boundaries among the Framework, Project Template, PC application, and STM32 firmware repositories.
- Recorded exact initialization commits.
- Added project input, architecture, Protocol-ownership proposal, quick-start guide, V&V plan, status dashboard, result register, and evidence templates.
- Marked incomplete or unexecuted validation work without manufacturing pass evidence.
