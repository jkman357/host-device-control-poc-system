# Project Protocol Directory

## Current State

The canonical Protocol file has not yet been migrated into this repository.

The provisional source is:

- repository: `host-device-control-poc-pc-app`
- path: `protocol/protocol.yaml`
- pinned commit: `84bbc16f02a864084b1270db40b58460ad691e35`
- Protocol version: `0.1.0`
- wire version: `0x01`

## Planned State

After a human-approved ownership migration, this directory should contain:

```text
protocol/
├── protocol.yaml
├── CHANGELOG.md
└── test-vectors/
```

Do not copy the file here and silently declare it authoritative. The migration shall identify the source commit, compare bytes, update implementation references, and record the decision.
