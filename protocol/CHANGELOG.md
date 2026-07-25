# Protocol Changelog

## 0.1.0 — Candidate for alignment — 2026-07-25

- Established `host-device-control-poc-system/protocol/protocol.yaml` as the project-level communication authority.
- Defined ST-LINK VCP / UART transport settings.
- Defined SOF, field widths and order, little-endian serialization, CRC-16/CCITT-FALSE, sequences, messages, states, timeouts, and error behavior.
- Added normative byte-level test vectors.
- Recorded that the current STM32 implementation does not yet match this candidate framing and message model.

No verified interoperability claim is made by this entry.

## Validation-artifact update — 2026-07-25

- Added a normative ACK response vector so command, direct-response, and event encoding are all covered.
- Added semantic YAML, provenance, frame-layout, metadata, payload, CRC, and cross-file validation.
- Added regression tests for previously identified validation bypasses.

This entry does not change Protocol version `0.1.0` or wire version `0x01`.

## Validation-artifact hardening update — 2026-07-25

- Added strict Git-history verification of the pinned authority commit and historical Protocol SHA-256.
- Added frame-field type/size and byte-order consistency checks.
- Added sequence-width, response sequence-copy, direction/kind, and valid-response relationship checks.
- Expanded regression coverage for known semantic and provenance bypasses.
- Corrected CI action versions and enabled full-history checkout.

This entry changes validation artifacts only. Protocol version `0.1.0`, wire version `0x01`, and the wire contract remain unchanged.
