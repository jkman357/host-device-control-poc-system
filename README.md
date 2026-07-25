# Host-Device Control PoC System

System-level project guide, repository map, integration baseline, and validation record for the Host-Device Control proof of concept.

This repository binds four related repositories into one traceable engineering project:

1. [`host-device-control-framework`](https://github.com/jkman357/host-device-control-framework) — reusable engineering authority set.
2. [`host-device-control-project-template`](https://github.com/jkman357/host-device-control-project-template) — reusable project workspace template.
3. [`host-device-control-poc-stm32f446re-fw`](https://github.com/jkman357/host-device-control-poc-stm32f446re-fw) — STM32F446RE Node firmware implementation.
4. [`host-device-control-poc-pc-app`](https://github.com/jkman357/host-device-control-poc-pc-app) — Windows WPF Coordinator application.

## Repository Role

This is the **system/project integration repository**. It owns:

- the cross-repository project overview;
- exact source baselines used for a validation cycle;
- the system-level architecture and responsibility map;
- the authoritative shared PC/MCU Protocol contract, test vectors, and synchronization rules;
- build, bring-up, and user guidance;
- system-level V&V planning, results, limitations, and evidence indexing.

It does **not**:

- replace the reusable Framework;
- duplicate the PC or MCU implementation repositories;
- claim that a draft, build, simulation, or tool result proves safety, regulatory compliance, production readiness, or Framework conformance;
- convert unexecuted plans or user observations into objective test evidence.

## Current Status

`v0.1.4 — Protocol Authority Pinning and Capacity-Policy Hardening`

The repository structure, Protocol authority, provenance metadata pinned to `b340645`, semantic contract validation, explicit UART headroom policy, Git-history provenance verification in CI, and expanded validator regression coverage are established. PC and STM32 implementations are still being aligned to the candidate contract, so end-to-end evidence remains incomplete.

See:

- [`START_HERE.md`](START_HERE.md) — reading and execution entry point;
- [`REPOSITORY_MAP.md`](REPOSITORY_MAP.md) — relationship among all repositories;
- [`QUICK_START.md`](QUICK_START.md) — practical setup and bring-up flow;
- [`VALIDATION_STATUS.md`](VALIDATION_STATUS.md) — current validation dashboard;
- [`docs/VV_Plan.md`](docs/VV_Plan.md) — planned system-level verification;
- [`docs/VV_Results.md`](docs/VV_Results.md) — executed-result register.

## Architecture at a Glance

```mermaid
flowchart TB
    H[Human Product / Project Authority]
    F[1. Host-Device Control Framework\nReusable authority set]
    T[2. Project Template\nReusable project skeleton]
    S[This repository\nPoC system project and evidence index]
    P[4. PC App\nCoordinator implementation]
    M[3. STM32 Firmware\nNode implementation]
    E[System Integration Evidence]

    H --> S
    F --> S
    T -. instantiated as .-> S
    S --> P
    S --> M
    P <--> |Shared framed protocol over ST-LINK VCP| M
    P --> E
    M --> E
    S --> E
```

## Source Baselines

The first project baseline is recorded in [`baselines/repositories.yaml`](baselines/repositories.yaml). A mutable `main` branch is not an immutable validation identity. Each validation cycle shall identify exact commits or controlled tags.

## Shared communication contract

The normative communication specification is [`protocol/protocol.yaml`](protocol/protocol.yaml). PC and MCU code are implementations of that contract, not alternative sources of protocol truth. The current contract is `candidate_for_alignment`; known differences are tracked in [`protocol/IMPLEMENTATION_ALIGNMENT.md`](protocol/IMPLEMENTATION_ALIGNMENT.md).

## Copyright and Use

Copyright © 2026 Ray Yang. No open-source license is granted. See [`LICENSE`](LICENSE) and [`NOTICE.md`](NOTICE.md).
