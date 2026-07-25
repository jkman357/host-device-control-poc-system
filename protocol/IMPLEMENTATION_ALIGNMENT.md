# Implementation Alignment

## Current conclusion

The project-level contract is now located in this repository, but the available PC candidate and current compiled STM32 implementation are not yet demonstrated to be mutually interoperable. Status remains **BLOCKED / candidate alignment required**.

## Blocking differences

| Gap ID | Contract candidate | Observed STM32 implementation | Required disposition |
|---|---|---|---|
| PROTO-GAP-001 | `message_id` is `uint8` | `message_id` is `uint16` | Update MCU to contract, or approve a contract revision before either side continues |
| PROTO-GAP-002 | No frame `flags` field | Frame includes a `uint8 flags` field | Same as above |
| PROTO-GAP-003 | `payload_length` is `uint16` | `payload_length` is `uint8` | Same as above |
| PROTO-GAP-004 | Minimum frame size is 10 bytes | Frame overhead is 11 bytes | Same as above |
| PROTO-GAP-005 | Candidate message IDs include `0x01..0x05`, `0x80..0x91` | Compiled MCU uses a different 16-bit message namespace, including telemetry `0x2000` | Align IDs and response model |
| PROTO-GAP-006 | Candidate maximum payload is 1024 bytes | Compiled MCU parser limit is 48 bytes | Approve one project requirement and implement it consistently |
| PROTO-GAP-007 | Candidate uses generic `ACK` / `NACK` | Compiled MCU includes command-specific response IDs and an error response | Align response semantics and vectors |

## Rule

Do not resolve these gaps by silently editing only one implementation. The project contract shall be reviewed first; then both repositories shall be updated against the same committed contract.

## Exit criteria

Alignment is complete only when:

- both implementations identify the same Protocol version, wire version, source commit, and file SHA-256;
- all normative test vectors pass in C and C#;
- command/state/error behavior tests pass;
- the board and PC complete an indexed end-to-end run; and
- `implementation-status.yaml` contains pinned commits and evidence IDs.
