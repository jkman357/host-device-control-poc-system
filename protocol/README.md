# Shared PC/MCU Communication Contract

This directory is the **project-level authority** for communication between:

- `host-device-control-poc-pc-app`; and
- `host-device-control-poc-stm32f446re-fw`.

Neither implementation repository owns the wire protocol. Source code, constants, comments, or generated files in an implementation repository cannot override [`protocol.yaml`](protocol.yaml).

## Current status

`protocol.yaml` version `0.1.0`, wire version `0x01`, is currently `candidate_for_alignment`. It is the normative target for both implementations, but it is not yet a `verified_baseline`.

A candidate becomes a verified baseline only when all of the following agree:

1. the contract;
2. normative test vectors;
3. PC encoder, parser, state handling, and timeouts;
4. MCU encoder, parser, state handling, and error behavior;
5. hardware interoperability evidence;
6. pinned PC, MCU, and system-repository commits; and
7. human approval recorded in this repository.

## Stream timing limit

The current transport is 115200-bps UART using 8N1, which carries 10 wire bits for each byte. A `TELEMETRY_SAMPLE` contains 14 payload bytes and 10 framing bytes, for a 24-byte / 240-bit frame. The telemetry-only theoretical ceiling is therefore 480 frames per second.

The Protocol intentionally limits configuration to `2500..60000 us`, corresponding to a maximum of 400 Hz and approximately 83.34% nominal TX utilization. The remaining bandwidth is reserved for ACK/NACK, status/error events, scheduling jitter, and recovery traffic. The PoC default remains `5000 us` / 200 Hz.

The 400-Hz value is a Protocol admission limit, not hardware qualification evidence. Promotion beyond `candidate_for_alignment` still requires long-duration hardware measurements with zero unexpected loss and bounded command-response latency.

## Directory contents

```text
protocol/
├── protocol.yaml
├── README.md
├── CHANGELOG.md
├── IMPLEMENTATION_ALIGNMENT.md
├── implementation-status.yaml
└── test-vectors/
    ├── README.md
    └── protocol-v0.1.0-vectors.json
```


## Contract validation

From a full repository clone:

```text
python tools/validate_protocol_contract.py --require-git-history
python tools/test_protocol_validator_regressions.py
```

The first command validates the current YAML contract, cross-file provenance records, field semantics, normative vectors, CRCs, and the pinned historical authority blob. The second command verifies that known validation bypasses remain rejected. Without Git history, omit `--require-git-history`; the tool will report that historical provenance was not verified.

## Change procedure

1. Change `protocol.yaml` first.
2. Classify compatibility and wire-version impact.
3. Update or add versioned test vectors.
4. Update the PC and MCU implementations independently.
5. Run byte-for-byte contract tests in both languages.
6. Run hardware bring-up and fault/recovery tests.
7. Pin exact commits and index evidence.
8. Promote status only after human review.

An implementation mismatch is a defect against the contract; it is not an alternative protocol definition.
