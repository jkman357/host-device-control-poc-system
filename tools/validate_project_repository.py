#!/usr/bin/env python3
"""Validate the minimum structure and pinned-baseline syntax of this project repository."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    "README.md",
    "START_HERE.md",
    "FRAMEWORK_REFERENCE.md",
    "PROJECT_INPUT.md",
    "REPOSITORY_MAP.md",
    "QUICK_START.md",
    "VALIDATION_STATUS.md",
    "LICENSE",
    "NOTICE.md",
    "baselines/repositories.yaml",
    "docs/Approval_Records.md",
    "docs/Decision_Log.md",
    "docs/Project_Requirements.md",
    "docs/System_Architecture.md",
    "docs/Protocol_Ownership.md",
    "docs/Integration_and_Bringup_Guide.md",
    "docs/VV_Plan.md",
    "docs/VV_Results.md",
    "docs/Evidence_Index.md",
    "docs/Known_Limitations.md",
    "validation/test-cases.yaml",
    "protocol/protocol.yaml",
    "protocol/CHANGELOG.md",
    "protocol/IMPLEMENTATION_ALIGNMENT.md",
    "protocol/implementation-status.yaml",
    "protocol/test-vectors/protocol-v0.1.0-vectors.json",
]

EXPECTED_REPOSITORIES = {
    "host-device-control-framework",
    "host-device-control-project-template",
    "host-device-control-poc-stm32f446re-fw",
    "host-device-control-poc-pc-app",
}

SHA_PATTERN = re.compile(r"^\s*commit:\s*([0-9a-f]{40})\s*$", re.MULTILINE)
NAME_PATTERN = re.compile(r"^\s*name:\s*([a-z0-9-]+)\s*$", re.MULTILINE)


def fail(message: str) -> None:
    print(f"ERROR: {message}")


def main() -> int:
    errors = 0

    for relative in REQUIRED_FILES:
        path = ROOT / relative
        if not path.is_file():
            fail(f"missing required file: {relative}")
            errors += 1

    baseline_path = ROOT / "baselines/repositories.yaml"
    if baseline_path.is_file():
        text = baseline_path.read_text(encoding="utf-8")
        commits = SHA_PATTERN.findall(text)
        names = set(NAME_PATTERN.findall(text))

        if len(commits) < 4:
            fail("baseline manifest shall contain at least four full 40-character commits")
            errors += 1

        missing_names = EXPECTED_REPOSITORIES - names
        if missing_names:
            fail("baseline manifest missing repositories: " + ", ".join(sorted(missing_names)))
            errors += 1

        if "project_layer_ownership_status:" not in text:
            fail("shared Protocol ownership status is not recorded")
            errors += 1

    result_text = (ROOT / "docs/VV_Results.md").read_text(encoding="utf-8") if (ROOT / "docs/VV_Results.md").is_file() else ""
    if "No system-level test is marked `PASS`" not in result_text:
        fail("V&V result boundary statement is missing")
        errors += 1

    if errors:
        print(f"Validation failed with {errors} error(s).")
        return 1

    print("Project repository validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
