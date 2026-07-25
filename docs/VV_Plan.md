# Verification and Validation Plan

## Scope

This plan covers engineering verification of the single-PC/single-STM32 PoC vertical slice. It does not define Product validation, safety validation, regulatory validation, or production release qualification.

## Planned Test Groups

| Group | Objective |
|---|---|
| REPO | Confirm repository identities, pinned baselines, and responsibility boundaries |
| PC | Confirm Coordinator build, component tests, fake-device behavior, UI decoupling, and CSV behavior |
| FW | Confirm MCU build, parser, command state, telemetry generation, and bounded resource behavior |
| PROTO | Confirm shared vectors, CRC, framing, IDs, endianness, lengths, and compatibility |
| INT | Confirm real serial command/response and stream interoperability |
| PERF | Measure interval, throughput, jitter, loss, UI responsiveness, and long-duration behavior |
| FAULT | Confirm rejection, resynchronization, timeout, disconnect, reset, and recovery behavior |
| EVID | Confirm every conclusion is traceable to exact baselines and retained evidence |

## Entry Criteria for Hardware Integration

- PC application builds at an identified commit.
- PC Protocol self-tests pass at an identified commit.
- MCU firmware builds and flashes at an identified commit.
- Both implementations identify the same Protocol version and content.
- COM port and serial configuration are known.
- Test operator has the approved test-case revision.

## Exit Criteria for Initial PoC Completion

- Minimal command sequence succeeds on hardware.
- Nominal 5 ms telemetry is demonstrated with approved measurement criteria.
- Sequence/loss behavior is characterized.
- CRC rejection and resynchronization are demonstrated on both component and target boundaries as applicable.
- At least one disconnect/reset scenario is characterized.
- Known limitations and open defects are recorded.
- Exact baselines and evidence are indexed.
- Human project authority records the conclusion and permitted claim wording.

## Result Semantics

A build pass is not a functional pass. A fake-device pass is not a target pass. A target pass is not production validation. Evidence acceptance does not change the underlying execution outcome.
