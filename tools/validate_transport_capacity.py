#!/usr/bin/env python3
"""Validate that Protocol stream limits fit the declared UART transport capacity."""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path
from typing import Any

import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[1]
    parser.add_argument(
        "--protocol",
        type=Path,
        default=root / "protocol" / "protocol.yaml",
        help="Path to protocol.yaml.",
    )
    parser.add_argument(
        "--policy",
        type=Path,
        default=root / "validation" / "transport-capacity-policy.yaml",
        help="Path to the system transport-capacity policy.",
    )
    return parser.parse_args()


def require_mapping(value: Any, label: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        errors.append(f"{label} shall be a mapping")
        return {}
    return value


def require_positive_int(value: Any, label: str, errors: list[str]) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        errors.append(f"{label} shall be a positive integer")
        return None
    return value


def find_message(messages: Any, name: str, errors: list[str]) -> dict[str, Any]:
    if not isinstance(messages, list):
        errors.append("messages shall be a list")
        return {}
    matches = [message for message in messages if isinstance(message, dict) and message.get("name") == name]
    if len(matches) != 1:
        errors.append(f"messages shall contain exactly one {name} definition")
        return {}
    return matches[0]


def find_payload_field(message: dict[str, Any], name: str, errors: list[str]) -> dict[str, Any]:
    payload = message.get("payload")
    if not isinstance(payload, list):
        errors.append(f"message {message.get('name', '<unnamed>')} payload shall be a list")
        return {}
    matches = [field for field in payload if isinstance(field, dict) and field.get("name") == name]
    if len(matches) != 1:
        errors.append(f"message {message.get('name', '<unnamed>')} shall contain exactly one payload field {name}")
        return {}
    return matches[0]


def validate(protocol_path: Path, policy_path: Path) -> list[str]:
    errors: list[str] = []
    try:
        document = yaml.safe_load(protocol_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        return [f"unable to load Protocol contract: {exc}"]
    if not isinstance(document, dict):
        return ["Protocol contract root shall be a mapping"]

    try:
        policy_document = yaml.safe_load(policy_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        return [f"unable to load transport-capacity policy: {exc}"]
    if not isinstance(policy_document, dict):
        return ["transport-capacity policy root shall be a mapping"]
    policy = require_mapping(policy_document.get("policy"), "policy", errors)

    transport = require_mapping(document.get("transport_profile"), "transport_profile", errors)
    framing = require_mapping(document.get("framing"), "framing", errors)
    capacity = require_mapping(document.get("stream_capacity"), "stream_capacity", errors)

    baud = require_positive_int(transport.get("baud_rate_bps"), "transport_profile.baud_rate_bps", errors)
    start_bits = require_positive_int(transport.get("start_bits"), "transport_profile.start_bits", errors)
    data_bits = require_positive_int(transport.get("data_bits"), "transport_profile.data_bits", errors)
    stop_bits = require_positive_int(transport.get("stop_bits"), "transport_profile.stop_bits", errors)
    parity = transport.get("parity")
    parity_bits = 0 if parity == "none" else 1 if parity in {"even", "odd"} else None
    if parity_bits is None:
        errors.append("transport_profile.parity shall be none, even, or odd")

    declared_wire_bits = require_positive_int(
        transport.get("wire_bits_per_byte"),
        "transport_profile.wire_bits_per_byte",
        errors,
    )
    computed_wire_bits: int | None = None
    if None not in {start_bits, data_bits, stop_bits, parity_bits}:
        computed_wire_bits = int(start_bits) + int(data_bits) + int(stop_bits) + int(parity_bits)
        if declared_wire_bits != computed_wire_bits:
            errors.append(
                f"transport_profile.wire_bits_per_byte {declared_wire_bits} does not match computed {computed_wire_bits}"
            )

    minimum_frame_size = require_positive_int(
        framing.get("minimum_frame_size_bytes"),
        "framing.minimum_frame_size_bytes",
        errors,
    )
    telemetry = find_message(document.get("messages"), "TELEMETRY_SAMPLE", errors)
    telemetry_payload_size = require_positive_int(
        telemetry.get("payload_size_bytes"),
        "TELEMETRY_SAMPLE.payload_size_bytes",
        errors,
    )

    declared_payload_size = require_positive_int(
        capacity.get("telemetry_payload_size_bytes"),
        "stream_capacity.telemetry_payload_size_bytes",
        errors,
    )
    if telemetry_payload_size is not None and declared_payload_size != telemetry_payload_size:
        errors.append(
            "stream_capacity.telemetry_payload_size_bytes "
            f"{declared_payload_size} does not match TELEMETRY_SAMPLE payload {telemetry_payload_size}"
        )

    declared_frame_size = require_positive_int(
        capacity.get("telemetry_frame_size_bytes"),
        "stream_capacity.telemetry_frame_size_bytes",
        errors,
    )
    computed_frame_size: int | None = None
    if minimum_frame_size is not None and telemetry_payload_size is not None:
        computed_frame_size = minimum_frame_size + telemetry_payload_size
        if declared_frame_size != computed_frame_size:
            errors.append(
                f"declared telemetry_frame_size_bytes {declared_frame_size} does not match computed {computed_frame_size}"
            )

    theoretical_rate: int | None = None
    theoretical_floor_us: int | None = None
    if baud is not None and computed_wire_bits is not None and computed_frame_size is not None:
        frame_wire_bits = computed_wire_bits * computed_frame_size
        theoretical_rate = baud // frame_wire_bits
        theoretical_floor_us = math.ceil(frame_wire_bits * 1_000_000 / baud)

        declared_theoretical = require_positive_int(
            capacity.get("theoretical_maximum_rate_hz"),
            "stream_capacity.theoretical_maximum_rate_hz",
            errors,
        )
        if declared_theoretical != theoretical_rate:
            errors.append(
                "stream_capacity.theoretical_maximum_rate_hz "
                f"{declared_theoretical} does not match computed {theoretical_rate}"
            )

        calculation = require_mapping(capacity.get("calculation"), "stream_capacity.calculation", errors)
        usable_bytes = require_positive_int(
            calculation.get("usable_uart_bytes_per_second"),
            "stream_capacity.calculation.usable_uart_bytes_per_second",
            errors,
        )
        expected_usable_bytes = baud // computed_wire_bits
        if usable_bytes != expected_usable_bytes:
            errors.append(
                "stream_capacity.calculation.usable_uart_bytes_per_second "
                f"{usable_bytes} does not match computed {expected_usable_bytes}"
            )
        declared_frame_bits = require_positive_int(
            calculation.get("telemetry_wire_bits_per_frame"),
            "stream_capacity.calculation.telemetry_wire_bits_per_frame",
            errors,
        )
        if declared_frame_bits != frame_wire_bits:
            errors.append(
                "stream_capacity.calculation.telemetry_wire_bits_per_frame "
                f"{declared_frame_bits} does not match computed {frame_wire_bits}"
            )
        declared_floor = require_positive_int(
            calculation.get("theoretical_interval_floor_us"),
            "stream_capacity.calculation.theoretical_interval_floor_us",
            errors,
        )
        if declared_floor != theoretical_floor_us:
            errors.append(
                "stream_capacity.calculation.theoretical_interval_floor_us "
                f"{declared_floor} does not match computed {theoretical_floor_us}"
            )

    minimum_interval = require_positive_int(
        capacity.get("minimum_interval_us"),
        "stream_capacity.minimum_interval_us",
        errors,
    )
    protocol_maximum_rate = require_positive_int(
        capacity.get("protocol_maximum_rate_hz"),
        "stream_capacity.protocol_maximum_rate_hz",
        errors,
    )
    if minimum_interval is not None and theoretical_floor_us is not None and minimum_interval < theoretical_floor_us:
        errors.append(
            f"minimum interval {minimum_interval} us is below UART telemetry floor {theoretical_floor_us} us"
        )
    if protocol_maximum_rate is not None and theoretical_rate is not None and protocol_maximum_rate >= theoretical_rate:
        errors.append(
            f"protocol maximum rate {protocol_maximum_rate} Hz shall be lower than theoretical {theoretical_rate} Hz"
        )
    if minimum_interval is not None and protocol_maximum_rate is not None:
        interval_rate = 1_000_000 // minimum_interval
        if protocol_maximum_rate != interval_rate:
            errors.append(
                f"protocol maximum rate {protocol_maximum_rate} Hz does not match minimum interval rate {interval_rate} Hz"
            )

    set_config = find_message(document.get("messages"), "SET_STREAM_CONFIG", errors)
    interval_field = find_payload_field(set_config, "interval_us", errors)
    valid_range = interval_field.get("valid_range")
    if not (
        isinstance(valid_range, list)
        and len(valid_range) == 2
        and all(isinstance(value, int) and not isinstance(value, bool) for value in valid_range)
    ):
        errors.append("SET_STREAM_CONFIG.interval_us.valid_range shall contain two integers")
    else:
        if minimum_interval is not None and valid_range[0] != minimum_interval:
            errors.append(
                f"SET_STREAM_CONFIG minimum {valid_range[0]} us does not match stream_capacity minimum {minimum_interval} us"
            )
        if valid_range[0] > valid_range[1]:
            errors.append("SET_STREAM_CONFIG.interval_us.valid_range minimum exceeds maximum")
        default_interval = interval_field.get("poc_default")
        if not isinstance(default_interval, int) or isinstance(default_interval, bool):
            errors.append("SET_STREAM_CONFIG.interval_us.poc_default shall be an integer")
        elif not (valid_range[0] <= default_interval <= valid_range[1]):
            errors.append("SET_STREAM_CONFIG.interval_us.poc_default is outside valid_range")
        field_maximum_rate = interval_field.get("maximum_rate_hz")
        if field_maximum_rate != protocol_maximum_rate:
            errors.append(
                "SET_STREAM_CONFIG.interval_us.maximum_rate_hz "
                f"{field_maximum_rate} does not match protocol maximum {protocol_maximum_rate}"
            )

    device_info = find_message(document.get("messages"), "DEVICE_INFO", errors)
    maximum_rate_field = find_payload_field(device_info, "maximum_stream_rate_hz", errors)
    device_maximum = maximum_rate_field.get("maximum_allowed_value")
    if device_maximum != protocol_maximum_rate:
        errors.append(
            "DEVICE_INFO.maximum_stream_rate_hz maximum_allowed_value "
            f"{device_maximum} does not match protocol maximum {protocol_maximum_rate}"
        )

    if (
        baud is not None
        and computed_wire_bits is not None
        and computed_frame_size is not None
        and protocol_maximum_rate is not None
    ):
        utilization = computed_frame_size * computed_wire_bits * protocol_maximum_rate * 100 / baud
        declared_utilization = capacity.get("maximum_nominal_tx_utilization_percent")
        if not isinstance(declared_utilization, (int, float)) or isinstance(declared_utilization, bool):
            errors.append("stream_capacity.maximum_nominal_tx_utilization_percent shall be numeric")
        elif not math.isclose(float(declared_utilization), utilization, abs_tol=0.02):
            errors.append(
                "stream_capacity.maximum_nominal_tx_utilization_percent "
                f"{declared_utilization} does not match computed {utilization:.2f}"
            )
        if utilization >= 100.0:
            errors.append(f"protocol stream utilization {utilization:.2f}% leaves no transport headroom")

        policy_maximum_utilization = policy.get("maximum_nominal_tx_utilization_percent")
        if not isinstance(policy_maximum_utilization, (int, float)) or isinstance(policy_maximum_utilization, bool):
            errors.append("policy.maximum_nominal_tx_utilization_percent shall be numeric")
        elif utilization > float(policy_maximum_utilization) + 1e-9:
            errors.append(
                f"protocol stream utilization {utilization:.2f}% exceeds policy maximum "
                f"{float(policy_maximum_utilization):.2f}%"
            )

        reserved_headroom = 100.0 - utilization
        policy_minimum_headroom = policy.get("minimum_reserved_headroom_percent")
        if not isinstance(policy_minimum_headroom, (int, float)) or isinstance(policy_minimum_headroom, bool):
            errors.append("policy.minimum_reserved_headroom_percent shall be numeric")
        elif reserved_headroom + 1e-9 < float(policy_minimum_headroom):
            errors.append(
                f"reserved transport headroom {reserved_headroom:.2f}% is below policy minimum "
                f"{float(policy_minimum_headroom):.2f}%"
            )

    protocol_meta = require_mapping(document.get("protocol"), "protocol", errors)
    expected_policy_values = {
        "protocol_version": protocol_meta.get("version"),
        "wire_version": protocol_meta.get("wire_version"),
        "transport_profile_name": transport.get("name"),
        "minimum_interval_us": minimum_interval,
        "maximum_stream_rate_hz": protocol_maximum_rate,
    }
    for key, expected in expected_policy_values.items():
        actual = policy.get(key)
        if actual != expected:
            errors.append(f"policy.{key} {actual!r} does not match Protocol value {expected!r}")

    return errors


def main() -> int:
    args = parse_args()
    errors = validate(args.protocol.resolve(), args.policy.resolve())
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Protocol transport-capacity validation failed with {len(errors)} error(s).")
        return 1
    print("Protocol transport capacity validated: 115200-bps 8N1, 24-byte telemetry, 2500 us minimum, 400 Hz maximum.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
