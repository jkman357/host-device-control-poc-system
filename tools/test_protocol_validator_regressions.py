#!/usr/bin/env python3
"""Regression tests for previously identified Protocol validation bypasses."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tools" / "validate_protocol_contract.py"


def run_validator(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), "--root", str(root)],
        check=False,
        capture_output=True,
        text=True,
    )


def expect_failure(name: str, mutator, expected_text: str) -> None:
    with tempfile.TemporaryDirectory(prefix="protocol-validator-") as temp_dir:
        copy_root = Path(temp_dir) / "repo"
        shutil.copytree(ROOT, copy_root, ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc"))
        mutator(copy_root)
        result = run_validator(copy_root)
        combined = result.stdout + result.stderr
        if result.returncode == 0:
            raise AssertionError(f"{name}: validator unexpectedly passed")
        if expected_text not in combined:
            raise AssertionError(f"{name}: expected diagnostic not found: {expected_text}\n{combined}")


def break_yaml(root: Path) -> None:
    (root / "protocol" / "protocol.yaml").write_text("protocol: [unterminated\n", encoding="utf-8")


def mismatch_vector_message_id(root: Path) -> None:
    path = root / "protocol" / "test-vectors" / "protocol-v0.1.0-vectors.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["vectors"][0]["message_id"] = "0xFF"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def overlap_frame_offsets(root: Path) -> None:
    path = root / "protocol" / "protocol.yaml"
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    for field in payload["framing"]["fields"]:
        if field["name"] == "message_id":
            field["offset_bytes"] = 4
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def stale_protocol_sha(root: Path) -> None:
    path = root / "protocol" / "protocol.yaml"
    path.write_text(path.read_text(encoding="utf-8") + "\n# mutation\n", encoding="utf-8")


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
    ]
    for name, mutator, expected_text in cases:
        expect_failure(name, mutator, expected_text)
        print(f"PASS: {name} rejected")

    print("Protocol validator regression tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
