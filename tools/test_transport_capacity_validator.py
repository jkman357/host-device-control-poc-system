#!/usr/bin/env python3
"""Regression tests for Protocol UART transport-capacity validation."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable

import yaml

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tools" / "validate_transport_capacity.py"
PROTOCOL = ROOT / "protocol" / "protocol.yaml"
Mutator = Callable[[dict], None]


def run_validator(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), "--protocol", str(path)],
        check=False,
        capture_output=True,
        text=True,
    )


def expect_failure(name: str, mutator: Mutator, expected_text: str) -> None:
    document = yaml.safe_load(PROTOCOL.read_text(encoding="utf-8"))
    if not isinstance(document, dict):
        raise AssertionError("Protocol fixture root is not a mapping")
    mutator(document)
    with tempfile.TemporaryDirectory(prefix="transport-capacity-") as temp_dir:
        path = Path(temp_dir) / "protocol.yaml"
        path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
        result = run_validator(path)
        combined = result.stdout + result.stderr
        if result.returncode == 0:
            raise AssertionError(f"{name}: validator unexpectedly passed")
        if expected_text not in combined:
            raise AssertionError(f"{name}: expected diagnostic not found: {expected_text}\n{combined}")


def allow_impossible_1000_us(document: dict) -> None:
    document["stream_capacity"]["minimum_interval_us"] = 1000
    document["stream_capacity"]["protocol_maximum_rate_hz"] = 1000
    for message in document["messages"]:
        if message["name"] == "SET_STREAM_CONFIG":
            message["payload"][0]["valid_range"][0] = 1000
            message["payload"][0]["maximum_rate_hz"] = 1000
        if message["name"] == "DEVICE_INFO":
            for field in message["payload"]:
                if field["name"] == "maximum_stream_rate_hz":
                    field["maximum_allowed_value"] = 1000


def mismatch_frame_size(document: dict) -> None:
    document["stream_capacity"]["telemetry_frame_size_bytes"] = 23


def remove_headroom(document: dict) -> None:
    document["stream_capacity"]["protocol_maximum_rate_hz"] = 480
    document["stream_capacity"]["minimum_interval_us"] = 2083


def overstate_device_capability(document: dict) -> None:
    for message in document["messages"]:
        if message["name"] == "DEVICE_INFO":
            for field in message["payload"]:
                if field["name"] == "maximum_stream_rate_hz":
                    field["maximum_allowed_value"] = 1000


def main() -> int:
    baseline = run_validator(PROTOCOL)
    if baseline.returncode != 0:
        print(baseline.stdout, end="")
        print(baseline.stderr, end="", file=sys.stderr)
        print("ERROR: baseline transport-capacity validation failed", file=sys.stderr)
        return 1

    cases = [
        ("impossible 1000-us stream", allow_impossible_1000_us, "minimum interval 1000 us is below UART telemetry floor"),
        ("telemetry frame-size mismatch", mismatch_frame_size, "declared telemetry_frame_size_bytes 23 does not match computed 24"),
        ("transport headroom removal", remove_headroom, "shall be lower than theoretical 480 Hz"),
        ("overstated DEVICE_INFO capability", overstate_device_capability, "maximum_allowed_value 1000 does not match protocol maximum 400"),
    ]
    for name, mutator, expected_text in cases:
        expect_failure(name, mutator, expected_text)
        print(f"PASS: {name} rejected")

    print("Protocol transport-capacity regression tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
