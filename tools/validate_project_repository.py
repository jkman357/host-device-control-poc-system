#!/usr/bin/env python3
"""Validate the minimum structure and pinned-baseline syntax of this project repository."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
FULL_SHA_PATTERN = re.compile(r"^[0-9a-f]{40}$")

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
    "requirements-validation.txt",
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
    "tools/validate_protocol_contract.py",
    "tools/test_protocol_validator_regressions.py",
]

EXPECTED_REPOSITORIES = {
    "host-device-control-framework",
    "host-device-control-project-template",
    "host-device-control-poc-stm32f446re-fw",
    "host-device-control-poc-pc-app",
}


def fail(message: str) -> None:
    print(f"ERROR: {message}")


def load_yaml(path: Path) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        fail(f"{path.relative_to(ROOT)} is invalid YAML: {exc}")
        return None


def main() -> int:
    errors = 0

    for relative in REQUIRED_FILES:
        path = ROOT / relative
        if not path.is_file():
            fail(f"missing required file: {relative}")
            errors += 1

    baseline_path = ROOT / "baselines" / "repositories.yaml"
    if baseline_path.is_file():
        baseline = load_yaml(baseline_path)
        if not isinstance(baseline, dict):
            fail("baseline manifest root shall be a mapping")
            errors += 1
        else:
            repositories = baseline.get("repositories")
            if not isinstance(repositories, list):
                fail("baseline repositories shall be a list")
                errors += 1
            else:
                names: set[str] = set()
                for index, repository in enumerate(repositories):
                    if not isinstance(repository, dict):
                        fail(f"baseline repositories[{index}] shall be a mapping")
                        errors += 1
                        continue
                    name = repository.get("name")
                    commit = repository.get("commit")
                    if isinstance(name, str):
                        names.add(name)
                    else:
                        fail(f"baseline repositories[{index}].name shall be a string")
                        errors += 1
                    if not isinstance(commit, str) or not FULL_SHA_PATTERN.fullmatch(commit):
                        fail(f"baseline repository {name or index} commit shall be a full lowercase 40-character SHA")
                        errors += 1

                missing_names = EXPECTED_REPOSITORIES - names
                if missing_names:
                    fail("baseline manifest missing repositories: " + ", ".join(sorted(missing_names)))
                    errors += 1

            shared_contract = baseline.get("shared_contract")
            if not isinstance(shared_contract, dict):
                fail("shared Protocol contract record is missing")
                errors += 1
            else:
                authority = shared_contract.get("authority")
                if not isinstance(authority, dict):
                    fail("shared Protocol authority record is missing")
                    errors += 1
                else:
                    authority_commit = authority.get("repository_commit")
                    if not isinstance(authority_commit, str) or not FULL_SHA_PATTERN.fullmatch(authority_commit):
                        fail("shared Protocol authority commit shall be a full lowercase 40-character SHA")
                        errors += 1
                    if authority.get("repository_commit_status") != "pinned":
                        fail("shared Protocol authority commit status shall be pinned")
                        errors += 1

                if "project_layer_ownership_status" not in shared_contract:
                    fail("shared Protocol ownership status is not recorded")
                    errors += 1

    result_path = ROOT / "docs" / "VV_Results.md"
    result_text = result_path.read_text(encoding="utf-8") if result_path.is_file() else ""
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
