#!/usr/bin/env python3
"""Validate the PoC system repository structure and governance boundaries."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    ".github/workflows/project-validation.yml",
    ".gitignore",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "FRAMEWORK_REFERENCE.md",
    "LICENSE",
    "NOTICE.md",
    "PROJECT_INPUT.md",
    "QUICK_START.md",
    "README.md",
    "REPOSITORY_MAP.md",
    "START_HERE.md",
    "THIRD_PARTY_NOTICES.md",
    "VALIDATION_OUTPUT.txt",
    "VALIDATION_STATUS.md",
    "requirements-validation.txt",
    "baselines/repositories.yaml",
    "docs/Approval_Records.md",
    "docs/Decision_Log.md",
    "docs/Evidence_Index.md",
    "docs/Integration_and_Bringup_Guide.md",
    "docs/Known_Limitations.md",
    "docs/Project_Requirements.md",
    "docs/Protocol_Ownership.md",
    "docs/System_Architecture.md",
    "docs/VV_Plan.md",
    "docs/VV_Results.md",
    "evidence/README.md",
    "evidence/templates/Test_Execution_Record.md",
    "protocol/CHANGELOG.md",
    "protocol/IMPLEMENTATION_ALIGNMENT.md",
    "protocol/README.md",
    "protocol/implementation-status.yaml",
    "protocol/protocol.yaml",
    "protocol/test-vectors/README.md",
    "protocol/test-vectors/protocol-v0.1.0-vectors.json",
    "tools/finalize_protocol_authority.py",
    "tools/test_protocol_validator_regressions.py",
    "tools/test_transport_capacity_validator.py",
    "tools/validate_project_repository.py",
    "tools/validate_protocol_contract.py",
    "tools/validate_transport_capacity.py",
    "validation/test-cases.yaml",
    "validation/transport-capacity-policy.yaml",
    "validation/results/README.md",
]

FORBIDDEN_PACKAGE_FILES = {
    "APPLY.md",
    "COMMIT_MESSAGES.txt",
    "TEST_RESULTS.txt",
}


def load_yaml(path: Path, errors: list[str]) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        errors.append(f"invalid YAML {path.relative_to(ROOT)}: {exc}")
        return None


def main() -> int:
    errors: list[str] = []

    for relative in REQUIRED_FILES:
        path = ROOT / relative
        if not path.is_file():
            errors.append(f"missing required file: {relative}")
            continue
        try:
            content = path.read_bytes()
        except OSError as exc:
            errors.append(f"unable to read {relative}: {exc}")
            continue
        if not content:
            errors.append(f"required file is empty: {relative}")
        if b"\x00" in content:
            errors.append(f"text repository file contains NUL bytes: {relative}")

    for name in FORBIDDEN_PACKAGE_FILES:
        if (ROOT / name).exists():
            errors.append(f"package-only file shall not be committed: {name}")
    for path in ROOT.rglob("*.patch"):
        if ".git" not in path.parts:
            errors.append(f"package-only patch shall not be committed: {path.relative_to(ROOT)}")

    for relative in [
        "baselines/repositories.yaml",
        "protocol/implementation-status.yaml",
        "protocol/protocol.yaml",
        "validation/test-cases.yaml",
        "validation/transport-capacity-policy.yaml",
        ".github/workflows/project-validation.yml",
    ]:
        path = ROOT / relative
        if path.is_file():
            document = load_yaml(path, errors)
            if document is not None and not isinstance(document, dict):
                errors.append(f"YAML root shall be a mapping: {relative}")

    vector_path = ROOT / "protocol/test-vectors/protocol-v0.1.0-vectors.json"
    if vector_path.is_file():
        try:
            vector_doc = json.loads(vector_path.read_text(encoding="utf-8"))
            if not isinstance(vector_doc, dict):
                errors.append("Protocol vector JSON root shall be an object")
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            errors.append(f"invalid Protocol vector JSON: {exc}")

    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8", errors="replace") if (ROOT / "LICENSE").is_file() else ""
    notice_text = (ROOT / "NOTICE.md").read_text(encoding="utf-8", errors="replace") if (ROOT / "NOTICE.md").is_file() else ""
    if "Copyright © 2026 Ray Yang" not in license_text:
        errors.append("LICENSE copyright identity is missing or changed")
    if "NO LICENSE GRANTED" not in license_text:
        errors.append("LICENSE shall retain NO LICENSE GRANTED")
    if "No open-source license is granted" not in notice_text:
        errors.append("NOTICE.md shall retain the no-open-source-license notice")

    workflow_path = ROOT / ".github/workflows/project-validation.yml"
    if workflow_path.is_file():
        workflow = workflow_path.read_text(encoding="utf-8")
        required_commands = [
            "validate_project_repository.py",
            "validate_protocol_contract.py --require-git-history",
            "test_protocol_validator_regressions.py",
            "validate_transport_capacity.py",
            "test_transport_capacity_validator.py",
        ]
        for command in required_commands:
            if command not in workflow:
                errors.append(f"CI workflow does not execute required validation: {command}")
        if "fetch-depth: 0" not in workflow:
            errors.append("CI checkout shall use fetch-depth: 0 for provenance verification")

    requirements = (ROOT / "requirements-validation.txt").read_text(encoding="utf-8").splitlines()
    active_requirements = [line.strip() for line in requirements if line.strip() and not line.lstrip().startswith("#")]
    if not any(line.startswith("PyYAML==") for line in active_requirements):
        errors.append("requirements-validation.txt shall pin PyYAML with ==")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Project repository validation failed with {len(errors)} error(s).")
        return 1

    print("Project repository validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
