# Protocol Ownership and Synchronization

## Current State

The current Protocol baseline is stored at:

```text
host-device-control-poc-pc-app/protocol/protocol.yaml
```

At PC commit `84bbc16f02a864084b1270db40b58460ad691e35`, it defines Protocol version `0.1.0`, wire version `0x01`, little-endian framing, CRC-16/CCITT-FALSE, command/response messages, and 5 ms telemetry configuration.

The PC repository explicitly states that the Protocol is shared by PC and MCU and is not semantically PC-owned. The file location nevertheless gives the PC repository practical change control unless an external project rule is established.

## Proposed Project-Layer Rule

The canonical shared Protocol shall be controlled by this system/project repository after an approved migration decision.

Recommended end state:

```text
host-device-control-poc-system/
└── protocol/
    ├── protocol.yaml
    ├── test-vectors/
    └── CHANGELOG.md
```

Each implementation repository then contains one of:

- a generated copy with the upstream system commit embedded;
- a synchronized copy verified by hash in CI;
- a submodule/subtree reference where operationally acceptable.

## Required Change Procedure

1. Change the project Protocol source.
2. Classify compatibility and wire-version impact.
3. Update test vectors.
4. Update both implementations independently.
5. Verify encoded bytes across C# and C.
6. Run PC component tests.
7. Run MCU component tests.
8. Run hardware interoperability tests.
9. Record exact commits and evidence.
10. Update the system baseline only after the intended combination is known.

## Interim Rule

Until migration is approved and completed:

- treat the PC repository's pinned `protocol/protocol.yaml` as the provisional canonical file;
- record its exact commit in `baselines/repositories.yaml`;
- prevent firmware from using an unrecorded local variant;
- report any mismatch as a blocking integration defect.
