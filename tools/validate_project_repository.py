#!/usr/bin/env python3
"""Validate the PoC system repository structure and governance boundaries."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = [
    ".gitattributes",
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
    "WORK_CONTINUATION.md",
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
    "tools/test_project_repository_validator.py",
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

TEXT_SUFFIXES = {".md", ".txt", ".yaml", ".yml", ".json", ".py"}
TEXT_FILENAMES = {".gitignore", ".gitattributes"}
REQUIRED_GITATTRIBUTES = {
    "* text=auto eol=lf",
    "*.png binary",
    "*.jpg binary",
    "*.jpeg binary",
    "*.pdf binary",
    "*.zip binary",
    "*.bin binary",
    "*.hex binary",
    "*.elf binary",
}

SEMVER = r"v(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)(?:-rc\.(?:[1-9]\d*))?"
README_RELEASE_RE = re.compile(
    rf"- Candidate version: `(?P<version>{SEMVER})`\s*\n"
    rf"- Lifecycle status: `(?P<status>Draft for Review|Baseline)`\s*\n"
    rf"- Previous formal version: `(?P<previous>v(?:0|[1-9]\d*)\.(?:0|[1-9]\d*)\.(?:0|[1-9]\d*))`"
)
CHANGELOG_RELEASE_RE = re.compile(
    rf"^# Changelog\s*\n+## (?P<version>{SEMVER}) — \d{{4}}-\d{{2}}-\d{{2}} — (?P<status>Draft for Review|Baseline)",
    re.MULTILINE,
)

CONTINUATION_BOUNDARY = (
    "It does not grant approval, does not create V&V evidence, does not accept risk, "
    "does not authorize release, and does not establish Framework conformance."
)


def load_yaml(path: Path, errors: list[str]) -> Any:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        errors.append(f"invalid YAML {path.relative_to(ROOT)}: {exc}")
        return None


def is_text_repository_file(path: Path) -> bool:
    return path.name in TEXT_FILENAMES or path.suffix.lower() in TEXT_SUFFIXES


def validate_release_state(errors: list[str]) -> None:
    readme_path = ROOT / "README.md"
    changelog_path = ROOT / "CHANGELOG.md"
    baseline_path = ROOT / "baselines/repositories.yaml"
    if not readme_path.is_file() or not changelog_path.is_file() or not baseline_path.is_file():
        return

    readme = readme_path.read_text(encoding="utf-8", errors="replace")
    changelog = changelog_path.read_text(encoding="utf-8", errors="replace")
    readme_match = README_RELEASE_RE.search(readme)
    changelog_match = CHANGELOG_RELEASE_RE.search(changelog)
    if readme_match is None:
        errors.append("README.md shall contain the controlled candidate version, lifecycle status, and previous formal version")
        return
    if changelog_match is None:
        errors.append("CHANGELOG.md shall begin with the current candidate version and lifecycle status")
        return

    version = readme_match.group("version")
    status = readme_match.group("status")
    if changelog_match.group("version") != version or changelog_match.group("status") != status:
        errors.append("README.md and CHANGELOG.md release version/status shall match")

    is_rc = "-rc." in version
    if is_rc and status != "Draft for Review":
        errors.append("release-candidate versions shall remain Draft for Review")
    if not is_rc and status == "Draft for Review":
        errors.append("a formal semantic version shall not remain Draft for Review")

    baseline_doc = load_yaml(baseline_path, errors)
    if not isinstance(baseline_doc, dict):
        return
    cycles = baseline_doc.get("alignment_cycles")
    if not isinstance(cycles, list) or not cycles:
        errors.append("baselines/repositories.yaml shall contain at least one alignment cycle")
        return
    active = cycles[-1]
    if not isinstance(active, dict):
        errors.append("current alignment cycle shall be a mapping")
        return
    if active.get("candidate_version") != version:
        errors.append("current alignment-cycle candidate_version shall match README.md")
    expected_cycle_status = "draft_for_review" if status == "Draft for Review" else "baseline"
    if active.get("status") != expected_cycle_status:
        errors.append("current alignment-cycle status shall match the repository lifecycle status")

    working_sources = active.get("upstream_working_sources")
    if not isinstance(working_sources, list) or len(working_sources) < 2:
        errors.append("current alignment cycle shall identify Framework and Project Template working sources")
    else:
        expected_roles = {"reusable_framework_authority", "reusable_project_template"}
        found_roles: set[str] = set()
        for item in working_sources:
            if not isinstance(item, dict):
                errors.append("upstream working-source entries shall be mappings")
                continue
            role = item.get("role")
            if isinstance(role, str):
                found_roles.add(role)
            sha = item.get("package_sha256")
            if not isinstance(sha, str) or re.fullmatch(r"[0-9a-f]{64}", sha) is None:
                errors.append(f"upstream working source {role!r} shall contain a lowercase 64-character package_sha256")
            if item.get("identity_status") == "package_verified_commit_pin_pending" and item.get("exact_git_commit") != "TBD":
                errors.append(f"upstream working source {role!r} pending commit pin shall use exact_git_commit: TBD")
        if not expected_roles.issubset(found_roles):
            errors.append("current alignment cycle shall include both Framework and Project Template roles")


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

    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
            continue
        if is_text_repository_file(path):
            content = path.read_bytes()
            if b"\r" in content:
                errors.append(f"CR or CRLF line ending is prohibited: {path.relative_to(ROOT)}")

    attributes_path = ROOT / ".gitattributes"
    if attributes_path.is_file():
        attribute_lines = {
            line.strip()
            for line in attributes_path.read_text(encoding="utf-8", errors="replace").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        for required_line in sorted(REQUIRED_GITATTRIBUTES):
            if required_line not in attribute_lines:
                errors.append(f".gitattributes shall retain required rule: {required_line}")

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
    continuation_text = (ROOT / "WORK_CONTINUATION.md").read_text(encoding="utf-8", errors="replace") if (ROOT / "WORK_CONTINUATION.md").is_file() else ""
    if "Copyright © 2026 Ray Yang" not in license_text:
        errors.append("LICENSE copyright identity is missing or changed")
    if "NO LICENSE GRANTED" not in license_text:
        errors.append("LICENSE shall retain NO LICENSE GRANTED")
    if "No open-source license is granted" not in notice_text:
        errors.append("NOTICE.md shall retain the no-open-source-license notice")
    if CONTINUATION_BOUNDARY not in continuation_text:
        errors.append("WORK_CONTINUATION.md shall retain the explicit non-authority boundary")
    for required_heading in [
        "## Current Work State",
        "## Validation Actually Executed",
        "## Important Checks Not Executed",
        "## Known Failures, Limitations, and Incomplete Work",
        "## Next Bounded Actions",
        "## Human Decisions or Approvals Still Required",
        "## Handoff Checklist",
    ]:
        if required_heading not in continuation_text:
            errors.append(f"WORK_CONTINUATION.md missing required section: {required_heading}")

    workflow_path = ROOT / ".github/workflows/project-validation.yml"
    if workflow_path.is_file():
        workflow = workflow_path.read_text(encoding="utf-8")
        required_commands = [
            "validate_project_repository.py",
            "test_project_repository_validator.py",
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

    validate_release_state(errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Project repository validation failed with {len(errors)} error(s).")
        return 1

    print("Project repository validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
