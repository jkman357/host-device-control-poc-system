# Framework Reference

## Canonical Upstream

- Repository: `https://github.com/jkman357/host-device-control-framework`
- Pinned commit: `7a68980ef5faa2e897a3574af121683d65f74638`
- Source status at project initialization: Framework repository release candidate / maintained authority set
- Project adoption status: `Proposed for this PoC; formal project approval record not yet created`

## Template Source

- Repository: `https://github.com/jkman357/host-device-control-project-template`
- Pinned commit: `491816c07390066221b6fbdbc413364626722e6b`
- Use: structural starting point and authority/evidence separation model

## Applicable Domains for This PoC

- Coordinator/Node responsibility separation;
- Single-Node topology;
- shared Protocol definition and message ownership;
- transport-independent application boundaries;
- bounded timing, buffers, queues, and failure behavior;
- Embedded C implementation rules for Product-owned MCU code;
- C# and Coordinator engineering rules for the PC application;
- validation evidence identity and claim boundaries;
- human approval and final responsibility.

## Project-Specific Resolution Required

The following remain project decisions, not automatically settled by the Framework:

- exact transport and baud rate;
- frame format and message set;
- telemetry rate and acceptable jitter/loss;
- command timeout and retry policy;
- hardware and software tool versions;
- acceptance criteria;
- evidence retention method;
- whether any Framework conformance claim will be pursued.

## Change Impact

Changing the pinned Framework baseline requires review of project applicability, architecture, Protocol, implementation assumptions, V&V coverage, and any prior conclusion that depended on the earlier baseline.
