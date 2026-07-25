#!/usr/bin/env python3
"""Regression tests for previously identified Protocol validation bypasses."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable

import yaml

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tools" / "validate_protocol_contract.py"
Mutator = Callable[[Path], None]


def run_validator(root: Path, require_git_history: bool = False) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(VALIDATOR), "--root", str(root)]
    if require_git_history:
        command.append("--require-git-history")
    return subprocess.run(command, check=False, capture_output=True, text=True)


def copy_repository(destination: Path) -> None:
    shutil.copytree(
        ROOT,
        destination,
        ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"),
    )


def load_protocol(root: Path) -> dict:
    path = root / "protocol" / "protocol.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise AssertionError("Protocol fixture root is not a mapping")
    return payload


def save_protocol(root: Path, payload: dict) -> None:
    path = root / "protocol" / "protocol.yaml"
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def update_recorded_protocol_sha(root: Path) -> None:
    digest = hashlib.sha256((root / "protocol" / "protocol.yaml").read_bytes()).hexdigest()

    baseline_path = root / "baselines" / "repositories.yaml"
    baseline = yaml.safe_load(baseline_path.read_text(encoding="utf-8"))
    baseline["shared_contract"]["authority"]["file_sha256"] = digest
    baseline_path.write_text(yaml.safe_dump(baseline, sort_keys=False), encoding="utf-8")

    status_path = root / "protocol" / "implementation-status.yaml"
    status = yaml.safe_load(status_path.read_text(encoding="utf-8"))
    status["protocol_contract"]["sha256"] = digest
    status_path.write_text(yaml.safe_dump(status, sort_keys=False), encoding="utf-8")


def expect_failure(name: str, mutator: Mutator, expected_text: str) -> None:
    with tempfile.TemporaryDirectory(prefix="protocol-validator-") as temp_dir:
        copy_root = Path(temp_dir) / "repo"
        copy_repository(copy_root)
        mutator(copy_root)
        result = run_validator(copy_root)
        combined = result.stdout + result.stderr
        if result.returncode == 0:
            raise AssertionError(f"{name}: validator unexpectedly passed")
        if expected_text not in combined:
            raise AssertionError(f"{name}: expected diagnostic not found: {expected_text}\n{combined}")


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        check=True,
        capture_output=True,
        text=True,
    )


def initialize_git_authority_fixture(root: Path) -> str:
    run_git(root, "init")
    run_git(root, "config", "user.name", "Protocol Validator Test")
    run_git(root, "config", "user.email", "validator@example.invalid")
    run_git(root, "add", "protocol/protocol.yaml")
    run_git(root, "commit", "-m", "test: add protocol authority")
    authority_commit = run_git(root, "rev-parse", "HEAD").stdout.strip()

    baseline_path = root / "baselines" / "repositories.yaml"
    baseline = yaml.safe_load(baseline_path.read_text(encoding="utf-8"))
    baseline["shared_contract"]["authority"]["repository_commit"] = authority_commit
    baseline_path.write_text(yaml.safe_dump(baseline, sort_keys=False), encoding="utf-8")

    status_path = root / "protocol" / "implementation-status.yaml"
    status = yaml.safe_load(status_path.read_text(encoding="utf-8"))
    status["protocol_contract"]["system_repository_commit"] = authority_commit
    status_path.write_text(yaml.safe_dump(status, sort_keys=False), encoding="utf-8")
    return authority_commit


def break_yaml(root: Path) -> None:
    (root / "protocol" / "protocol.yaml").write_text("protocol: [unterminated\n", encoding="utf-8")


def mismatch_vector_message_id(root: Path) -> None:
    path = root / "protocol" / "test-vectors" / "protocol-v0.1.0-vectors.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["vectors"][0]["message_id"] = "0xFF"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def overlap_frame_offsets(root: Path) -> None:
    payload = load_protocol(root)
    for field in payload["framing"]["fields"]:
        if field["name"] == "message_id":
            field["offset_bytes"] = 4
    save_protocol(root, payload)
    update_recorded_protocol_sha(root)


def stale_protocol_sha(root: Path) -> None:
    path = root / "protocol" / "protocol.yaml"
    path.write_text(path.read_text(encoding="utf-8") + "\n# mutation\n", encoding="utf-8")


def sequence_endian_conflict(root: Path) -> None:
    payload = load_protocol(root)
    for field in payload["framing"]["fields"]:
        if field["name"] == "sequence":
            field["byte_order"] = "big_endian"
    save_protocol(root, payload)
    update_recorded_protocol_sha(root)


def crc_endian_conflict(root: Path) -> None:
    payload = load_protocol(root)
    for field in payload["framing"]["fields"]:
        if field["name"] == "crc16":
            field["byte_order"] = "big_endian"
    save_protocol(root, payload)
    update_recorded_protocol_sha(root)


def field_type_size_mismatch(root: Path) -> None:
    payload = load_protocol(root)
    for field in payload["framing"]["fields"]:
        if field["name"] == "message_id":
            field["type"] = "uint16"
            field["size_bytes"] = 1
    save_protocol(root, payload)
    update_recorded_protocol_sha(root)


def sequence_width_mismatch(root: Path) -> None:
    payload = load_protocol(root)
    payload["sequence_rules"]["host_command"]["width_bits"] = 32
    save_protocol(root, payload)
    update_recorded_protocol_sha(root)


def event_as_direct_response(root: Path) -> None:
    payload = load_protocol(root)
    for message in payload["messages"]:
        if message["name"] == "PING":
            message["valid_responses"] = ["TELEMETRY_SAMPLE"]
    save_protocol(root, payload)
    update_recorded_protocol_sha(root)


def response_sequence_rule_conflict(root: Path) -> None:
    payload = load_protocol(root)
    for message in payload["messages"]:
        if message["name"] == "ACK":
            message["sequence_rule"] = "independent"
    save_protocol(root, payload)
    update_recorded_protocol_sha(root)


def expect_missing_git_history_rejected() -> None:
    with tempfile.TemporaryDirectory(prefix="protocol-validator-") as temp_dir:
        copy_root = Path(temp_dir) / "repo"
        copy_repository(copy_root)
        result = run_validator(copy_root, require_git_history=True)
        combined = result.stdout + result.stderr
        if result.returncode == 0:
            raise AssertionError("required Git history: validator unexpectedly passed")
        if "Git history is unavailable" not in combined:
            raise AssertionError(f"required Git history: expected diagnostic not found\n{combined}")


def expect_historical_protocol_mismatch_rejected() -> None:
    with tempfile.TemporaryDirectory(prefix="protocol-validator-git-") as temp_dir:
        copy_root = Path(temp_dir) / "repo"
        copy_repository(copy_root)
        initialize_git_authority_fixture(copy_root)

        protocol_path = copy_root / "protocol" / "protocol.yaml"
        protocol_path.write_text(
            protocol_path.read_text(encoding="utf-8") + "\n# post-authority wire-contract mutation\n",
            encoding="utf-8",
        )
        update_recorded_protocol_sha(copy_root)

        result = run_validator(copy_root, require_git_history=True)
        combined = result.stdout + result.stderr
        if result.returncode == 0:
            raise AssertionError("historical Protocol mismatch: validator unexpectedly passed")
        if "historical Protocol SHA-256" not in combined:
            raise AssertionError(
                f"historical Protocol mismatch: expected diagnostic not found\n{combined}"
            )


def expect_fake_authority_commit_rejected() -> None:
    with tempfile.TemporaryDirectory(prefix="protocol-validator-git-") as temp_dir:
        copy_root = Path(temp_dir) / "repo"
        copy_repository(copy_root)
        initialize_git_authority_fixture(copy_root)

        baseline = run_validator(copy_root, require_git_history=True)
        if baseline.returncode != 0:
            raise AssertionError(
                "valid Git provenance fixture failed before mutation\n"
                + baseline.stdout
                + baseline.stderr
            )

        fake_commit = "0" * 40
        baseline_path = copy_root / "baselines" / "repositories.yaml"
        baseline_doc = yaml.safe_load(baseline_path.read_text(encoding="utf-8"))
        baseline_doc["shared_contract"]["authority"]["repository_commit"] = fake_commit
        baseline_path.write_text(yaml.safe_dump(baseline_doc, sort_keys=False), encoding="utf-8")

        status_path = copy_root / "protocol" / "implementation-status.yaml"
        status_doc = yaml.safe_load(status_path.read_text(encoding="utf-8"))
        status_doc["protocol_contract"]["system_repository_commit"] = fake_commit
        status_path.write_text(yaml.safe_dump(status_doc, sort_keys=False), encoding="utf-8")

        result = run_validator(copy_root, require_git_history=True)
        combined = result.stdout + result.stderr
        if result.returncode == 0:
            raise AssertionError("fake authority commit: validator unexpectedly passed")
        if "pinned authority commit does not exist" not in combined:
            raise AssertionError(f"fake authority commit: expected diagnostic not found\n{combined}")


def main() -> int:
    baseline = run_validator(ROOT)
    if baseline.returncode != 0:
        print(baseline.stdout, end="")
        print(baseline.stderr, end="", file=sys.stderr)
        print("ERROR: baseline Protocol validation failed before regression mutations", file=sys.stderr)
        return 1

    cases = [
        ("invalid YAML", break_yaml, "invalid YAML in Protocol contract"),
        ("vector metadata mismatch", mismatch_vector_message_id, "metadata message_id differs from encoded frame"),
        ("frame offset mismatch", overlap_frame_offsets, "framing field message_id offset shall be 3"),
        ("stale Protocol SHA", stale_protocol_sha, "Protocol SHA-256 does not match"),
        ("sequence field endian conflict", sequence_endian_conflict, "framing field sequence.byte_order shall match protocol.byte_order"),
        ("CRC field endian conflict", crc_endian_conflict, "framing field crc16.byte_order shall match protocol.byte_order"),
        ("field type-size mismatch", field_type_size_mismatch, "type uint16 requires size_bytes 2"),
        ("sequence width mismatch", sequence_width_mismatch, "host_command.width_bits shall equal sequence field width 16"),
        ("event accepted as direct response", event_as_direct_response, "shall have kind response"),
        ("response sequence rule conflict", response_sequence_rule_conflict, "message ACK sequence_rule shall be copy_request_sequence"),
    ]
    for name, mutator, expected_text in cases:
        expect_failure(name, mutator, expected_text)
        print(f"PASS: {name} rejected")

    expect_missing_git_history_rejected()
    print("PASS: required Git history absence rejected")

    expect_historical_protocol_mismatch_rejected()
    print("PASS: historical Protocol blob mismatch rejected")

    expect_fake_authority_commit_rejected()
    print("PASS: fake authority commit rejected")

    print("Protocol validator regression tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
