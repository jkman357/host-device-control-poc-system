# Start Here — PoC System Project Guide

## Purpose

This file is the entry point for a human or AI system working across the Host-Device Control PoC repositories.

## Required Reading Order

1. Read this file.
2. Read `WORK_CONTINUATION.md`.
3. Read `FRAMEWORK_REFERENCE.md`.
4. Read `PROJECT_INPUT.md`.
5. Read `REPOSITORY_MAP.md`.
6. Read `baselines/repositories.yaml`.
7. Read `docs/Decision_Log.md` and `docs/Approval_Records.md`.
8. Read only the implementation and validation documents relevant to the requested scope.
9. Read the applicable source repository at the exact baseline recorded for the current validation cycle.

If live repository access is unavailable, identify the complete repository or ZIP package actually supplied and record its checksum and limitations in `WORK_CONTINUATION.md`. A package checksum supports working continuity but does not replace the exact upstream Git commit or protected/signed tag required for controlled approval, evidence disposition, release, or Framework conformance reliance.

## Authority Order

Use the following order for this PoC project:

1. Applicable law, contract, third-party license, and mandatory external obligation.
2. Project facts and decisions supplied or approved by authorized humans.
3. The pinned Host-Device Control Framework baseline and its resolved applicability.
4. The shared Project Protocol baseline.
5. The PC and MCU implementation repositories at their pinned baselines.
6. Draft analysis, AI output, continuation records, and general engineering knowledge.

A lower source does not silently override a higher source.

## Working Rules

- Work only on the requested scope.
- Separate facts, assumptions, proposals, observations, prior-AI conclusions, and objective evidence.
- Do not claim a test was executed unless an execution record and evidence identity exist.
- Do not treat PC fake-device success as MCU or hardware interoperability evidence.
- Do not treat a successful build as functional validation.
- Do not claim Framework conformance unless the required claim boundary, applicability, records, evidence, and human approvals exist.
- Do not allow `WORK_CONTINUATION.md`, a chat transcript, model memory, a ZIP, or a generated report to become approval or release authority.
- Use `TBD`, `Unknown`, `None`, or `N/A` rather than inventing missing information.

## Resuming or Switching AI / Tool / Provider

When work resumes in a different session, tool, model, provider, or with another engineer:

1. Obtain the complete controlled repository, working tree, or complete Project ZIP.
2. Read `WORK_CONTINUATION.md`; treat prior statements as handoff information, not inherited truth.
3. Confirm the source/package identity, current candidate version, requested scope, and intentionally unchanged areas.
4. Re-read the applicable authority documents and distinguish source-backed facts from assumptions or prior-AI proposals.
5. Re-run all applicable repository, Protocol, build, and test checks available in the new environment.
6. Record actual results and limitations; do not inherit a previous `PASS` without re-establishing the source state.
7. Update `WORK_CONTINUATION.md` before another handoff.
8. Return a complete updated project package when complete-package exchange is required.

## Release-Candidate and Freeze Rule

During one review cycle, keep the intended formal version fixed and increment only the RC suffix:

```text
v0.2.0-rc.1 → v0.2.0-rc.2 → v0.2.0-rc.3
```

An RC remains `Draft for Review`. Remove the RC suffix only after explicit authorized-human freeze approval. The exact final commit shall then be identified by a controlled tag or Release before the repository is treated as an immutable formal baseline.

## Expected Project Flow

```text
Human-defined project purpose and constraints
        ↓
Pinned Framework and project-template baselines
        ↓
System architecture and shared Protocol baseline
        ↓
Independent PC and MCU implementations
        ↓
Component tests and cross-language protocol vectors
        ↓
Hardware bring-up and end-to-end integration tests
        ↓
Evidence review, limitation statement, and human conclusion
```

## Current Boundary

This repository currently provides the project and validation framework. It does not yet contain sufficient objective evidence for a complete end-to-end validation conclusion.
