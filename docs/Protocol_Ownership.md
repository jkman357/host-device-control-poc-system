# Protocol Authority and Synchronization

## Active project rule

The canonical PC/MCU communication contract is:

```text
host-device-control-poc-system/protocol/protocol.yaml
```

This is no longer only an ownership proposal. The system repository owns the specification, its lifecycle, test vectors, compatibility decisions, implementation-alignment status, and verification evidence.

The PC and MCU repositories own only their respective implementations. Neither repository may redefine the frame, message, payload, timeout, state, sequence, or error semantics locally.

## Implementation reference requirements

Every tested implementation baseline shall record:

- Protocol name and semantic version;
- wire version;
- system-repository commit;
- `protocol/protocol.yaml` SHA-256;
- implementation commit; and
- test-vector result.

A synchronized or generated local copy is permitted for build convenience, but it shall carry provenance and shall be checked against the system source by CI.

## Required change procedure

1. Propose and review the system-level contract change.
2. Classify backward compatibility and wire-version impact.
3. Update versioned test vectors.
4. Update both implementations independently.
5. Verify exact bytes in C# and C.
6. Execute PC component, MCU component, and hardware interoperability tests.
7. Record exact commits and evidence.
8. Promote the contract lifecycle status only after approval.

## Current boundary

Protocol `0.1.0` / wire `0x01` is an authoritative **candidate target**, not a verified baseline. Known implementation differences are controlled in `protocol/IMPLEMENTATION_ALIGNMENT.md`; no end-to-end conformity claim is made until those gaps are closed.
