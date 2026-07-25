#!/usr/bin/env python3
"""Regression tests for Protocol UART transport-capacity validation."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from copy import deepcopy
from pathlib import Path
from typing import Callable

import yaml

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "tools" / "validate_transport_capacity.py"
PROTOCOL = ROOT / "protocol" / "protocol.yaml"
POLICY = ROOT / "validation" / "transport-capacity-policy.yaml"
Mutator = Callable[[dict, dict], None]


def run_validator(protocol: Path, policy: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), "--protocol", str(protocol), "--policy", str(policy)],
        check=False,
        capture_output=True,
        text=True,
    )


def set_stream_limit(document: dict, interval_us: int, rate_hz: int, utilization: float) -> None:
    document["stream_capacity"]["minimum_interval_us"] = interval_us
    document["stream_capacity"]["protocol_maximum_rate_hz"] = rate_hz
    document["stream_capacity"]["maximum_nominal_tx_utilization_percent"] = utilization
    for message in document["messages"]:
        if message["name"] == "SET_STREAM_CONFIG":
            message["payload"][0]["valid_range"][0] = interval_us
            message["payload"][0]["maximum_rate_hz"] = rate_hz
        if message["name"] == "DEVICE_INFO":
            for field in message["payload"]:
                if field["name"] == "maximum_stream_rate_hz":
                    field["maximum_allowed_value"] = rate_hz


def expect_failure(name: str, mutator: Mutator, expected_text: str) -> None:
    document = yaml.safe_load(PROTOCOL.read_text(encoding="utf-8"))
    policy = yaml.safe_load(POLICY.read_text(encoding="utf-8"))
    if not isinstance(document, dict) or not isinstance(policy, dict):
        raise AssertionError("baseline fixture root is not a mapping")
    mutator(document, policy)
    with tempfile.TemporaryDirectory(prefix="transport-capacity-") as temp_dir:
        protocol_path = Path(temp_dir) / "protocol.yaml"
        policy_path = Path(temp_dir) / "policy.yaml"
        protocol_path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
        policy_path.write_text(yaml.safe_dump(policy, sort_keys=False), encoding="utf-8")
        result = run_validator(protocol_path, policy_path)
        combined = result.stdout + result.stderr
        if result.returncode == 0:
            raise AssertionError(f"{name}: validator unexpectedly passed")
        if expected_text not in combined:
            raise AssertionError(f"{name}: expected diagnostic not found: {expected_text}\n{combined}")


def impossible_1000_us(document: dict, policy: dict) -> None:
    set_stream_limit(document, 1000, 1000, 208.34)


def mismatch_frame_size(document: dict, policy: dict) -> None:
    document["stream_capacity"]["telemetry_frame_size_bytes"] = 23


def remove_all_headroom(document: dict, policy: dict) -> None:
    set_stream_limit(document, 2083, 480, 100.0)


def compress_to_401_hz(document: dict, policy: dict) -> None:
    set_stream_limit(document, 2493, 401, 83.55)


def compress_to_479_hz(document: dict, policy: dict) -> None:
    set_stream_limit(document, 2087, 479, 99.79)


def overstate_device_capability(document: dict, policy: dict) -> None:
    for message in document["messages"]:
        if message["name"] == "DEVICE_INFO":
            for field in message["payload"]:
                if field["name"] == "maximum_stream_rate_hz":
                    field["maximum_allowed_value"] = 1000


def weaken_policy_only(document: dict, policy: dict) -> None:
    policy["policy"]["maximum_stream_rate_hz"] = 479


def main() -> int:
    baseline = run_validator(PROTOCOL, POLICY)
    if baseline.returncode != 0:
        print(baseline.stdout, end="")
        print(baseline.stderr, end="", file=sys.stderr)
        print("ERROR: baseline transport-capacity validation failed", file=sys.stderr)
        return 1

    cases = [
        ("impossible 1000-us stream", impossible_1000_us, "minimum interval 1000 us is below UART telemetry floor"),
        ("telemetry frame-size mismatch", mismatch_frame_size, "declared telemetry_frame_size_bytes 23 does not match computed 24"),
        ("transport headroom removal", remove_all_headroom, "shall be lower than theoretical 480 Hz"),
        ("401-Hz policy bypass", compress_to_401_hz, "policy.minimum_interval_us 2500 does not match Protocol value 2493"),
        ("479-Hz policy bypass", compress_to_479_hz, "protocol stream utilization 99.79% exceeds policy maximum 85.00%"),
        ("overstated DEVICE_INFO capability", overstate_device_capability, "maximum_allowed_value 1000 does not match protocol maximum 400"),
        ("policy-only weakening", weaken_policy_only, "policy.maximum_stream_rate_hz 479 does not match Protocol value 400"),
    ]
    for name, mutator, expected_text in cases:
        expect_failure(name, mutator, expected_text)
        print(f"PASS: {name} rejected")

    print("Protocol transport-capacity regression tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
