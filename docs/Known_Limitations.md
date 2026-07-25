# Known Limitations

## Current System Limitations

- Single Node only.
- No automatic reconnect.
- Exact Protocol wire version only; no negotiation beyond `0x01`.
- COM-port discovery uses port names rather than robust device identity.
- No authentication, encryption, replay protection, or credential lifecycle.
- No firmware update path.
- No installer or code signing.
- CSV output is engineering data, not regulated production data retention.
- Long-duration timing, loss, and recovery limits are not yet characterized.
- Hardware interoperability evidence has not yet been indexed.

## Repository Limitations

- Initial firmware GitHub baseline does not yet represent the latest Protocol/Transport development work discussed during bring-up.
- The shared Protocol is now controlled here, but PC/MCU implementation alignment is blocked by known wire-format and message-model differences.
- Formal approval and evidence records have not yet been created.
- The system repository does not independently execute or fetch external repositories in CI.

## Claim Boundary

The current deliverable may be described as an **initial Host-Device Control PoC project and validation framework**. It shall not be described as a validated product, certified reference design, production-ready system, or proven Framework-conformant implementation.

## Git Provenance Validation Outside a Clone

A source ZIP does not contain `.git` history. In an extracted ZIP, `tools/validate_protocol_contract.py` validates the current Protocol file, manifests, vectors, and semantic consistency, but reports that historical commit provenance was not verified. CI runs the validator with `--require-git-history` after `fetch-depth: 0`; that strict mode is the authoritative provenance check.
