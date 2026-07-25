# Validation Status

Last updated: 2026-07-25

## Status Definitions

- **PASS** — executed against an identified baseline; acceptance criteria met; evidence indexed.
- **FAIL** — executed against an identified baseline; acceptance criteria not met; evidence indexed.
- **OBSERVED** — credible engineering observation exists, but the repository does not yet contain a complete execution/evidence record.
- **IN PROGRESS** — implementation or execution is underway.
- **NOT RUN** — planned but not executed.
- **BLOCKED** — cannot proceed because a named prerequisite is missing.

## Current Dashboard

| Area | Status | Current conclusion |
|---|---|---|
| Framework and repository role mapping | PASS | The four upstream roles and the missing system/project integration layer are identified in this repository. |
| Project baseline manifest | PASS | Exact initialization commits are recorded in `baselines/repositories.yaml`. |
| PC application source availability | PASS | WPF Coordinator, fake and serial transports, protocol tests, and build/run instructions are present at the pinned PC baseline. |
| PC application local execution | OBSERVED | The application has been built and launched by the project owner; a formal execution record is not yet stored here. |
| PC protocol self-tests | NOT RUN | Test capability exists in the PC repository; no system-repository evidence record has been imported. |
| STM32 project source availability | PASS | A CubeIDE project exists at the pinned firmware baseline. |
| STM32 application-layer implementation | IN PROGRESS | Recent Protocol/Transport work is not yet represented by a newer pinned GitHub baseline in this initial system record. |
| STM32 clean build and flash | OBSERVED | Build activity has been observed during development; reproducible baseline evidence is pending. |
| Shared Protocol authority placement | IN PROGRESS | Current canonical file is stored in the PC repository; migration or controlled synchronization at the project layer is proposed. |
| PC fake-device streaming | OBSERVED | PC repository supports fake-device streaming; formal system evidence is pending. |
| PC-to-MCU command/response | NOT RUN | No indexed hardware execution record yet. |
| 5 ms / 200 Hz hardware telemetry | NOT RUN | No indexed timing capture yet. |
| Sequence and loss detection | NOT RUN | No indexed hardware stress result yet. |
| CRC rejection and resynchronization on hardware | NOT RUN | PC component tests exist; target behavior is unverified. |
| Long-duration streaming | NOT RUN | Duration and acceptance thresholds remain to be approved. |
| Framework conformance claim | NOT CLAIMED | No conformance conclusion is made by this repository. |
| Production readiness | NOT CLAIMED | This remains an engineering PoC. |

## Next Evidence-Producing Milestone

Pin and push the next STM32 firmware baseline, then execute a minimal end-to-end sequence:

```text
PING → GET_DEVICE_INFO → SET_STREAM_CONFIG(5000 us)
→ START_STREAM → capture telemetry → STOP_STREAM
```

The run shall record both implementation commits, the exact Protocol baseline, COM settings, board identity, logs, timing/loss measurements, and anomalies.
