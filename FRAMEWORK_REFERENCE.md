# Framework Reference

## Historical Project Initialization Sources

The following identities describe the original 2026-07-25 project initialization and remain preserved in `baselines/repositories.yaml`:

- Framework repository: `https://github.com/jkman357/host-device-control-framework`
- Initial pinned Framework commit: `7a68980ef5faa2e897a3574af121683d65f74638`
- Initial Framework adoption status: `Proposed for this PoC; formal project approval record not yet created`
- Project Template repository: `https://github.com/jkman357/host-device-control-project-template`
- Initial pinned Project Template commit: `491816c07390066221b6fbdbc413364626722e6b`

This baseline update does not rewrite those historical identities.

## Current Working Alignment Cycle

- System repository baseline: `v0.2.2` — `Baseline`; previous formal baseline: `v0.2.1`
- Framework working package: `v1.1.2`
- Supplied Framework ZIP SHA-256: `d6cea78f17f410bb5cbbdd6a0d672d470cead0bc4a5753468b875f5381aa809c`
- Project Template working package: `v1.1.2`
- Supplied Project Template ZIP SHA-256: `1976d05e209f59d4cb564b886b9829daab699edafe002b27856bfd6d43ca6ec7`
- Exact upstream Framework commit: `TBD before controlled baseline adoption`
- Exact upstream Project Template commit: `TBD before controlled baseline adoption`
- System repository freeze approval: `Received 2026-07-29`; record `FRZ-002`; exact final Git commit/tag or controlled Release identity pending

The package checksums identify the complete working sources supplied for this alignment cycle. They support portable work continuation, but they do not replace exact upstream full commit SHAs or protected/signed tags for controlled approval, validation-baseline adoption, release, or Framework conformance reliance.

## Applicable Domains for This PoC

- Coordinator/Node responsibility separation;
- Single-Node topology;
- shared Protocol definition and message ownership;
- transport-independent application boundaries;
- bounded timing, buffers, queues, and failure behavior;
- Embedded C implementation rules for Product-owned MCU code;
- C# and Coordinator engineering rules for the PC application;
- WPF as a replaceable Presentation adapter rather than the owner of core behavior;
- headless Application/Core verification without a WPF runtime, window, visual tree, or Dispatcher loop;
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
- approved exceptions, if any, that allow UI-framework or platform-specific types outside the Presentation/Infrastructure boundary;
- whether any Framework conformance claim will be pursued.

## Change Impact

Changing the pinned Framework or Project Template baseline requires review of project applicability, architecture, Protocol, implementation assumptions, V&V coverage, continuation records, and any prior conclusion that depended on the earlier baseline. A newer working package does not silently supersede an approved or historically recorded source baseline.

This `v1.1.2` alignment adds project-level Presentation-boundary requirements only. It does not authorize changes to the Protocol authority, wire format, MCU behavior, transport capacity, or prior evidence conclusions.
