# Start Here — PoC System Project Guide

## Purpose

This file is the entry point for a human or AI system working across the Host-Device Control PoC repositories.

## Required Reading Order

1. Read this file.
2. Read `FRAMEWORK_REFERENCE.md`.
3. Read `PROJECT_INPUT.md`.
4. Read `REPOSITORY_MAP.md`.
5. Read `baselines/repositories.yaml`.
6. Read `docs/Decision_Log.md` and `docs/Approval_Records.md`.
7. Read only the implementation and validation documents relevant to the requested scope.
8. Read the applicable source repository at the exact baseline recorded for the current validation cycle.

## Authority Order

Use the following order for this PoC project:

1. Applicable law, contract, third-party license, and mandatory external obligation.
2. Project facts and decisions supplied or approved by authorized humans.
3. The pinned Host-Device Control Framework baseline and its resolved applicability.
4. The shared Project Protocol baseline.
5. The PC and MCU implementation repositories at their pinned baselines.
6. Draft analysis, AI output, and general engineering knowledge.

A lower source does not silently override a higher source.

## Working Rules

- Work only on the requested scope.
- Separate facts, assumptions, proposals, observations, and objective evidence.
- Do not claim a test was executed unless an execution record and evidence identity exist.
- Do not treat PC fake-device success as MCU or hardware interoperability evidence.
- Do not treat a successful build as functional validation.
- Do not claim Framework conformance unless the required claim boundary, applicability, records, evidence, and human approvals exist.
- Use `TBD`, `Unknown`, `None`, or `N/A` rather than inventing missing information.

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
