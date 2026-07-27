# Framework Reference

## Historical Project Initialization Sources

The following identities describe the original 2026-07-25 project initialization and remain preserved in `baselines/repositories.yaml`:

- Framework repository: `https://github.com/jkman357/host-device-control-framework`
- Initial pinned Framework commit: `7a68980ef5faa2e897a3574af121683d65f74638`
- Initial Framework adoption status: `Proposed for this PoC; formal project approval record not yet created`
- Project Template repository: `https://github.com/jkman357/host-device-control-project-template`
- Initial pinned Project Template commit: `491816c07390066221b6fbdbc413364626722e6b`

This release does not rewrite those historical identities.

## Current Working Alignment Cycle

- System repository baseline: `v0.2.0` — `Baseline`
- Framework working package: `v1.1.0`
- Supplied Framework ZIP SHA-256: `bea96dba07baf3449e2879668ba06bcbcf7e1abf418ba86c4c8a944e70a83783`
- Project Template working package: `v1.1.0`
- Supplied Project Template ZIP SHA-256: `69e1d25bd0f19e40765e3c1f26aeb18e622d9836fa2aea9b4367f6fde1384492`
- Exact upstream Framework commit: `TBD before controlled baseline adoption`
- Exact upstream Project Template commit: `TBD before controlled baseline adoption`
- System repository freeze approval: `Received 2026-07-27`; exact final Git commit/tag or controlled Release remains pending

The package checksums identify the complete working sources supplied for this alignment cycle. They support portable work continuation, but they do not replace exact upstream full commit SHAs or protected/signed tags for controlled approval, validation-baseline adoption, release, or Framework conformance reliance.

## Applicable Domains for This PoC

- Coordinator/Node responsibility separation;
- Single-Node topology;
- shared Protocol definition and message ownership;
- transport-independent application boundaries;
- bounded timing, buffers, queues, and failure behavior;
- Embedded C implementation rules for Product-owned MCU code;
- C# and Coordinator engineering rules for the PC application;
- provider-independent AI work continuity and controlled handoff;
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
- exact upstream Framework and Project Template commit identities for the current alignment cycle;
- whether any Framework conformance claim will be pursued.

## Change Impact

Changing the pinned Framework or Project Template baseline requires review of project applicability, architecture, Protocol, implementation assumptions, V&V coverage, continuation records, and any prior conclusion that depended on the earlier baseline. A newer working package does not silently supersede an approved or historically recorded source baseline.
