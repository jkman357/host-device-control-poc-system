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
| Framework and repository role mapping | PASS | The four upstream roles and the system/project integration layer are identified in this repository. |
| Project baseline manifest | PASS | Exact initialization commits and the Protocol authority identity are recorded in `baselines/repositories.yaml`. |
| PC application source availability | PASS | WPF Coordinator, fake and serial transports, protocol tests, and build/run instructions are present at the pinned PC baseline. |
| PC application local execution | OBSERVED | The application has been built and launched by the project owner; a formal execution record is not yet stored here. |
| PC protocol self-tests | NOT RUN | Test capability exists in the PC repository; no system-repository evidence record has been imported. |
| STM32 project source availability | PASS | A CubeIDE project exists at the pinned firmware baseline. |
| STM32 application-layer implementation | IN PROGRESS | Recent Protocol/Transport work is not yet represented by a newer pinned system baseline. |
| STM32 clean build and flash | OBSERVED | Build activity has been observed during development; reproducible baseline evidence is pending. |
| Shared Protocol authority placement | PASS | `protocol/protocol.yaml` is the project-level source of truth. |
| Protocol authority metadata | PASS | Both provenance records identify commit `b340645e6cb8fef9906aa7fecf22e2ca011a32bc` and SHA-256 `c8e59c7d4afb33eb4858c146ffcfef0260f7ee3fb43a7bedf46df7953abe90ef`. |
| Historical Protocol provenance | CI-GATED | The source ZIP has no `.git` directory. A full checkout shall run `validate_protocol_contract.py --require-git-history` to verify that `b340645` is an ancestor and contains the identical Protocol blob. |
| Protocol contract validation | PASS | Local source-package validation checks YAML structure, framing semantics, IDs, sequence rules, response relationships, cross-file hashes, vectors, payload lengths, and CRCs. |
| Protocol transport-capacity validation | PASS | Local validation derives the 115200-bps 8N1 budget, verifies the 24-byte telemetry frame, enforces 2500 us / 400 Hz, and applies the separate 85%-utilization / 15%-headroom policy. |
| Protocol validator regression tests | PASS | Fourteen cases passed locally. Temporary fixtures exclude caller `.git` history, and the fake-commit case first proves a valid synthetic two-commit provenance baseline before applying the negative mutation. |
| Transport-capacity regression tests | PASS | Seven cases were executed locally, including 401-Hz and 479-Hz policy-bypass attempts. |
| GitHub Actions | CI-GATED | The workflow runs on push and pull request. Dynamic run status is maintained in GitHub Actions rather than hard-coded into this source file. |
| PC fake-device streaming | OBSERVED | PC repository supports fake-device streaming; formal system evidence is pending. |
| Protocol implementation alignment | BLOCKED | Current pinned STM32 and PC baselines have not yet been reverified against the corrected authority; see `protocol/IMPLEMENTATION_ALIGNMENT.md`. |
| PC-to-MCU command/response | NOT RUN | No indexed hardware execution record yet. |
| 5 ms / 200 Hz hardware telemetry | NOT RUN | No indexed timing capture yet. |
| Sequence and loss detection | NOT RUN | No indexed hardware stress result yet. |
| CRC rejection and resynchronization on hardware | NOT RUN | Target behavior remains unverified. |
| Long-duration streaming | NOT RUN | Duration and acceptance thresholds remain to be approved. |
| Framework conformance claim | NOT CLAIMED | No conformance conclusion is made by this repository. |
| Production readiness | NOT CLAIMED | This remains an engineering PoC. |

## Next Evidence-Producing Milestone

Commit and push this replacement tree, confirm the complete GitHub Actions workflow, then synchronize the STM32 and PC implementations to the pinned Protocol authority. After both implementation commits are pinned, execute:

```text
PING → GET_DEVICE_INFO → SET_STREAM_CONFIG(5000 us)
→ START_STREAM → capture telemetry → STOP_STREAM
```

The run shall record both implementation commits, the exact Protocol baseline, COM settings, board identity, logs, timing/loss measurements, and anomalies.
