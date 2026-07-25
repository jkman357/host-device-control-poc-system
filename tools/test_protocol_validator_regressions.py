#!/usr/bin/env python3
"""Regression tests for semantic Protocol and provenance validation."""

from __future__ import annotations

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


def run_validator(root: Path, strict: bool = False) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(VALIDATOR), "--root", str(root)]
    if strict:
        command.append("--require-git-history")
    return subprocess.run(command, check=False, capture_output=True, text=True)


def load_yaml(path: Path) -> dict:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise AssertionError(f"fixture root is not a mapping: {path}")
    return value


def save_yaml(path: Path, value: dict) -> None:
    path.write_text(yaml.safe_dump(value, sort_keys=False), encoding="utf-8")


def expect_failure(name: str, mutator: Mutator, expected: str, strict: bool = False, initialize_git: bool = False) -> None:
    with tempfile.TemporaryDirectory(prefix="protocol-regression-") as temp_dir:
        root = Path(temp_dir) / "repo"
        shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns("__pycache__"))
        if initialize_git:
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.email", "ci@example.invalid"], check=True)
            subprocess.run(["git", "-C", str(root), "config", "user.name", "CI"], check=True)
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            subprocess.run(["git", "-C", str(root), "commit", "-qm", "fixture"], check=True)
        mutator(root)
        result = run_validator(root, strict=strict)
        combined = result.stdout + result.stderr
        if result.returncode == 0:
            raise AssertionError(f"{name}: validator unexpectedly passed")
        if expected not in combined:
            raise AssertionError(f"{name}: expected diagnostic not found: {expected}\n{combined}")
        print(f"PASS: {name} rejected")


def invalid_yaml(root: Path) -> None:
    (root / "protocol/protocol.yaml").write_text("protocol: [\n", encoding="utf-8")


def vector_metadata(root: Path) -> None:
    path = root / "protocol/test-vectors/protocol-v0.1.0-vectors.json"
    value = json.loads(path.read_text(encoding="utf-8"))
    value["protocol_version"] = "9.9.9"
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def framing_offset(root: Path) -> None:
    path = root / "protocol/protocol.yaml"
    value = load_yaml(path)
    value["framing"]["fields"][0]["offset_bytes"] = 1
    save_yaml(path, value)


def stale_hash(root: Path) -> None:
    path = root / "baselines/repositories.yaml"
    value = load_yaml(path)
    value["shared_contract"]["authority"]["file_sha256"] = "0" * 64
    save_yaml(path, value)


def sequence_endian(root: Path) -> None:
    path = root / "protocol/protocol.yaml"
    value = load_yaml(path)
    for field in value["framing"]["fields"]:
        if field["name"] == "sequence":
            field["byte_order"] = "big_endian"
    save_yaml(path, value)


def field_type_size(root: Path) -> None:
    path = root / "protocol/protocol.yaml"
    value = load_yaml(path)
    for field in value["framing"]["fields"]:
        if field["name"] == "message_id":
            field["type"] = "uint16"
    save_yaml(path, value)


def sequence_width(root: Path) -> None:
    path = root / "protocol/protocol.yaml"
    value = load_yaml(path)
    value["sequence_rules"]["host_command"]["width_bits"] = 32
    save_yaml(path, value)


def event_as_response(root: Path) -> None:
    path = root / "protocol/protocol.yaml"
    value = load_yaml(path)
    for message in value["messages"]:
        if message["name"] == "ACK":
            message["kind"] = "event"
    save_yaml(path, value)


def response_sequence(root: Path) -> None:
    path = root / "protocol/protocol.yaml"
    value = load_yaml(path)
    for message in value["messages"]:
        if message["name"] == "NACK":
            message["sequence_rule"] = "independent"
    save_yaml(path, value)


def duplicate_id(root: Path) -> None:
    path = root / "protocol/protocol.yaml"
    value = load_yaml(path)
    value["messages"][1]["id"] = value["messages"][0]["id"]
    save_yaml(path, value)


def crc_parameters(root: Path) -> None:
    path = root / "protocol/protocol.yaml"
    value = load_yaml(path)
    value["framing"]["crc"]["polynomial"] = 0x8005
    save_yaml(path, value)


def unknown_response(root: Path) -> None:
    path = root / "protocol/protocol.yaml"
    value = load_yaml(path)
    for message in value["messages"]:
        if message["name"] == "PING":
            message["valid_responses"].append("NOT_DEFINED")
    save_yaml(path, value)


def no_change(root: Path) -> None:
    return None


def fake_authority_commit(root: Path) -> None:
    for relative, keys in [
        ("baselines/repositories.yaml", ("shared_contract", "authority", "repository_commit")),
        ("protocol/implementation-status.yaml", ("protocol_contract", "system_repository_commit")),
    ]:
        path = root / relative
        value = load_yaml(path)
        target = value
        for key in keys[:-1]:
            target = target[key]
        target[keys[-1]] = "f" * 40
        save_yaml(path, value)


def main() -> int:
    baseline = run_validator(ROOT)
    if baseline.returncode != 0:
        print(baseline.stdout, end="")
        print(baseline.stderr, end="", file=sys.stderr)
        print("ERROR: baseline Protocol validation failed", file=sys.stderr)
        return 1

    cases = [
        ("malformed YAML", invalid_yaml, "invalid YAML in Protocol contract", False, False),
        ("vector metadata drift", vector_metadata, "vector protocol_version metadata mismatch", False, False),
        ("framing offset drift", framing_offset, "framing field version offset shall be 2", False, False),
        ("stale Protocol hash", stale_hash, "baseline Protocol SHA-256 does not match", False, False),
        ("sequence endian conflict", sequence_endian, "framing field sequence.byte_order shall be little_endian", False, False),
        ("field type mismatch", field_type_size, "framing field message_id type shall be uint8", False, False),
        ("sequence width mismatch", sequence_width, "host_command.width_bits shall equal sequence field width 16", False, False),
        ("event used as command response", event_as_response, "response ACK shall have kind response", False, False),
        ("response sequence mismatch", response_sequence, "message NACK sequence_rule shall be copy_request_sequence", False, False),
        ("duplicate message ID", duplicate_id, "duplicate message ID", False, False),
        ("CRC parameter drift", crc_parameters, "CRC polynomial shall be 0x1021", False, False),
        ("unknown response name", unknown_response, "references unknown response: NOT_DEFINED", False, False),
        ("missing Git history in strict mode", no_change, "Git history is unavailable", True, False),
        ("fake authority commit", fake_authority_commit, "pinned authority commit does not exist", True, True),
    ]
    for name, mutator, expected, strict, initialize_git in cases:
        expect_failure(name, mutator, expected, strict, initialize_git)

    print("Protocol validator regression tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
