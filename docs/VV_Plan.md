# Verification and Validation Plan

## Scope

This plan covers engineering verification of the single-PC/single-STM32 PoC vertical slice. It does not define Product validation, safety validation, regulatory validation, or production release qualification.

## Planned Test Groups

| Group | Objective |
|---|---|
| REPO | Confirm repository identities, pinned baselines, responsibility boundaries, and Presentation dependency rules |
| PC | Confirm Coordinator build, headless Application/Core tests, fake-device behavior, Presentation adapter behavior, UI decoupling, and CSV behavior |
| FW | Confirm MCU build, parser, command state, telemetry generation, and bounded resource behavior |
| PROTO | Confirm shared vectors, CRC, framing, IDs, endianness, lengths, and compatibility |
| INT | Confirm real serial command/response and stream interoperability |
| PERF | Measure interval, throughput, jitter, loss, UI responsiveness, and long-duration behavior |
| FAULT | Confirm rejection, resynchronization, timeout, disconnect, reset, and recovery behavior |
| EVID | Confirm every conclusion is traceable to exact baselines and retained evidence |

## Presentation Boundary Verification

The PC implementation shall provide objective checks for the following boundaries:

1. Application/Core projects contain no direct WPF Framework dependency and do not reference WPF-specific windows, controls, visual types, dialogs, brushes, visibility values, or Dispatcher implementations.
2. Application/Core component tests execute without creating a WPF `Application`, `Window`, visual tree, or Dispatcher loop.
3. Protocol parsing, CRC, correlation, device state, timeout/retry, sequence/loss handling, telemetry processing, and persistence rules are testable below the Presentation layer.
4. WPF-specific behavior is tested at the Presentation adapter boundary, including binding, command routing, navigation/dialog behavior, chart rendering, virtualization/caching where applicable, and UI-thread affinity.
5. The Composition Root is the controlled location that selects concrete WPF, transport, file, and logging adapters.
6. Narrow UI service ports do not copy WPF APIs or expose concrete WPF types into Application/Core.
7. Any approved framework-leakage exception identifies the owner, reason, affected layer, test impact, and approval record.
8. UI replacement impact is assessed separately from core behavioral compatibility; a successful UI test does not prove Protocol or device behavior.

Recommended evidence includes project-reference inspection, dependency/namespace scanning, headless component-test execution, Presentation adapter tests, and an architecture review record tied to exact PC application source identity.

## Entry Criteria for Hardware Integration

- PC application builds at an identified commit.
- PC Protocol and Application/Core self-tests pass at an identified commit without requiring a WPF runtime loop.
- PC Presentation adapter tests pass at an identified commit or open limitations are recorded.
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
- Application/Core tests execute headlessly and no unapproved WPF dependency is present outside Presentation/Composition Root boundaries.
- UI responsiveness and decoupling are characterized without allowing UI load to block transport or Protocol processing.
- Known limitations and open defects are recorded.
- Exact baselines and evidence are indexed.
- Human project authority records the conclusion and permitted claim wording.

## Result Semantics

A build pass is not a functional pass. A fake-device pass is not a target pass. A target pass is not production validation. A WPF UI pass is not proof of Application/Core correctness, and a headless core pass is not proof of Presentation usability. Evidence acceptance does not change the underlying execution outcome.
