#!/usr/bin/env python3
"""Validate the authoritative Protocol contract, provenance, and normative vectors."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")
FIXED_TYPES = {
    "uint8": 1,
    "uint16": 2,
    "uint32": 4,
    "float32_ieee754": 4,
}


class Context:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.notices: list[str] = []

    def require(self, condition: bool, message: str) -> bool:
        if not condition:
            self.errors.append(message)
            return False
        return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--require-git-history", action="store_true")
    return parser.parse_args()


def load_yaml(path: Path, label: str, ctx: Context) -> dict[str, Any] | None:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        ctx.errors.append(f"invalid YAML in {label}: {exc}")
        return None
    if not isinstance(value, dict):
        ctx.errors.append(f"{label} root shall be a mapping")
        return None
    return value


def load_json(path: Path, label: str, ctx: Context) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        ctx.errors.append(f"invalid JSON in {label}: {exc}")
        return None
    if not isinstance(value, dict):
        ctx.errors.append(f"{label} root shall be an object")
        return None
    return value


def as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError:
            return None
    return None


def crc16_ccitt_false(data: bytes, polynomial: int = 0x1021, initial: int = 0xFFFF, xor_output: int = 0) -> int:
    crc = initial
    for value in data:
        crc ^= value << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ polynomial) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc ^ xor_output


def payload_fixed_size(message: dict[str, Any], ctx: Context) -> int | None:
    payload = message.get("payload")
    if not isinstance(payload, list):
        ctx.errors.append(f"message {message.get('name', '<unnamed>')} payload shall be a list")
        return None
    total = 0
    for index, field in enumerate(payload):
        if not isinstance(field, dict):
            ctx.errors.append(f"message {message.get('name', '<unnamed>')} payload[{index}] shall be a mapping")
            return None
        field_type = field.get("type")
        if field_type in FIXED_TYPES:
            total += FIXED_TYPES[field_type]
        elif field_type in {"byte_array", "utf8_byte_array"}:
            size = field.get("size_bytes")
            if isinstance(size, int) and not isinstance(size, bool):
                total += size
            else:
                return None
        else:
            ctx.errors.append(
                f"message {message.get('name', '<unnamed>')} payload field {field.get('name', index)} "
                f"has unsupported type: {field_type}"
            )
            return None
    return total


def validate_contract(document: dict[str, Any], ctx: Context) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[int, dict[str, Any]]] | None:
    protocol = document.get("protocol")
    framing = document.get("framing")
    messages = document.get("messages")
    if not isinstance(protocol, dict):
        ctx.errors.append("protocol shall be a mapping")
        return None
    if not isinstance(framing, dict):
        ctx.errors.append("framing shall be a mapping")
        return None
    if not isinstance(messages, list):
        ctx.errors.append("messages shall be a list")
        return None

    ctx.require(protocol.get("name") == "host-device-control-poc", "protocol.name shall be host-device-control-poc")
    ctx.require(isinstance(protocol.get("version"), str) and bool(SEMVER_RE.fullmatch(protocol["version"])), "protocol.version shall use semantic x.y.z syntax")
    wire_version = as_int(protocol.get("wire_version"))
    ctx.require(wire_version is not None and 0 <= wire_version <= 0xFF, "protocol.wire_version shall fit uint8")
    ctx.require(protocol.get("byte_order") == "little_endian", "protocol.byte_order shall be little_endian")
    lifecycle = protocol.get("lifecycle")
    if isinstance(lifecycle, dict) and isinstance(lifecycle.get("allowed_statuses"), list):
        ctx.require(protocol.get("status") in lifecycle["allowed_statuses"], "protocol.status shall be listed in lifecycle.allowed_statuses")
    else:
        ctx.errors.append("protocol.lifecycle.allowed_statuses shall be a list")
    authority = protocol.get("authority")
    if not isinstance(authority, dict):
        ctx.errors.append("protocol.authority shall be a mapping")
    else:
        ctx.require(authority.get("repository") == "host-device-control-poc-system", "protocol authority repository is incorrect")
        ctx.require(authority.get("path") == "protocol/protocol.yaml", "protocol authority path is incorrect")
        ctx.require(authority.get("rule") == "specification_precedes_implementation", "protocol authority rule is incorrect")

    sof = framing.get("sof")
    fields = framing.get("fields")
    crc = framing.get("crc")
    if not isinstance(sof, dict) or not isinstance(fields, list) or not isinstance(crc, dict):
        ctx.errors.append("framing.sof, framing.fields, and framing.crc are required")
        return None
    sof_values = sof.get("bytes")
    if not isinstance(sof_values, list) or not all(isinstance(v, int) and not isinstance(v, bool) and 0 <= v <= 255 for v in sof_values):
        ctx.errors.append("framing.sof.bytes shall be a byte list")
        return None
    sof_bytes = bytes(sof_values)
    ctx.require(sof_bytes == b"\xA5\x5A", "framing SOF shall be A5 5A")
    ctx.require(sof.get("included_in_crc") is False, "framing.sof.included_in_crc shall be false")

    fields_by_name: dict[str, dict[str, Any]] = {}
    for index, raw in enumerate(fields):
        if not isinstance(raw, dict):
            ctx.errors.append(f"framing.fields[{index}] shall be a mapping")
            continue
        name = raw.get("name")
        if not isinstance(name, str) or not name:
            ctx.errors.append(f"framing.fields[{index}].name shall be a non-empty string")
            continue
        if name in fields_by_name:
            ctx.errors.append(f"duplicate framing field name: {name}")
        fields_by_name[name] = raw

    expected_layout = [
        ("version", 2, "uint8", 1, None),
        ("message_id", 3, "uint8", 1, None),
        ("sequence", 4, "uint16", 2, "little_endian"),
        ("payload_length", 6, "uint16", 2, "little_endian"),
        ("payload", 8, "byte_array", "payload_length", None),
        ("crc16", "8_plus_payload_length", "uint16", 2, "little_endian"),
    ]
    for name, offset, field_type, size, byte_order in expected_layout:
        field = fields_by_name.get(name)
        if field is None:
            ctx.errors.append(f"framing.fields missing: {name}")
            continue
        ctx.require(field.get("offset_bytes") == offset, f"framing field {name} offset shall be {offset}")
        ctx.require(field.get("type") == field_type, f"framing field {name} type shall be {field_type}")
        ctx.require(field.get("size_bytes") == size, f"framing field {name} size_bytes shall be {size}")
        if byte_order is not None:
            ctx.require(field.get("byte_order") == byte_order, f"framing field {name}.byte_order shall be {byte_order}")
    ctx.require(framing.get("minimum_frame_size_bytes") == 10, "minimum_frame_size_bytes does not match the field layout")
    maximum_payload = as_int(framing.get("maximum_payload_size_bytes"))
    ctx.require(maximum_payload is not None and 0 <= maximum_payload <= 0xFFFF, "maximum payload does not fit payload_length")

    ctx.require(crc.get("algorithm") == "crc_16_ccitt_false", "CRC algorithm shall be crc_16_ccitt_false")
    ctx.require(as_int(crc.get("polynomial")) == 0x1021, "CRC polynomial shall be 0x1021")
    ctx.require(as_int(crc.get("initial_value")) == 0xFFFF, "CRC initial value shall be 0xFFFF")
    ctx.require(crc.get("reflect_input") is False and crc.get("reflect_output") is False, "CRC reflection shall be false")
    ctx.require(as_int(crc.get("xor_output")) == 0, "CRC xor_output shall be zero")
    ctx.require(crc.get("covered_bytes") == "version_through_end_of_payload", "unsupported CRC coverage")
    check_vector = crc.get("check_vector")
    if isinstance(check_vector, dict):
        expected_crc = as_int(check_vector.get("expected"))
        text = check_vector.get("input_ascii")
        if isinstance(text, str) and expected_crc is not None:
            ctx.require(crc16_ccitt_false(text.encode("ascii")) == expected_crc, "CRC check vector does not match declared parameters")
        else:
            ctx.errors.append("CRC check vector is malformed")
    else:
        ctx.errors.append("framing.crc.check_vector shall be a mapping")

    messages_by_name: dict[str, dict[str, Any]] = {}
    messages_by_id: dict[int, dict[str, Any]] = {}
    for index, raw in enumerate(messages):
        if not isinstance(raw, dict):
            ctx.errors.append(f"messages[{index}] shall be a mapping")
            continue
        name = raw.get("name")
        message_id = as_int(raw.get("id"))
        if not isinstance(name, str) or not name:
            ctx.errors.append(f"messages[{index}].name shall be a non-empty string")
            continue
        if name in messages_by_name:
            ctx.errors.append(f"duplicate message name: {name}")
        else:
            messages_by_name[name] = raw
        if message_id is None or not 0 <= message_id <= 0xFF:
            ctx.errors.append(f"message ID {name} shall fit uint8")
        elif message_id in messages_by_id:
            ctx.errors.append(f"duplicate message ID: 0x{message_id:02X}")
        else:
            messages_by_id[message_id] = raw
        kind = raw.get("kind")
        direction = raw.get("direction")
        ctx.require(kind in {"command", "response", "event", "response_or_event"}, f"message {name} has invalid kind")
        ctx.require(direction in {"pc_to_mcu", "mcu_to_pc"}, f"message {name} has invalid direction")
        if kind == "command":
            ctx.require(direction == "pc_to_mcu", f"message {name} command direction shall be pc_to_mcu")
        if kind == "response":
            ctx.require(direction == "mcu_to_pc", f"message {name} response direction shall be mcu_to_pc")
            ctx.require(raw.get("sequence_rule") == "copy_request_sequence", f"message {name} sequence_rule shall be copy_request_sequence")
        if kind in {"event", "response_or_event"}:
            ctx.require(direction == "mcu_to_pc", f"message {name} {kind} direction shall be mcu_to_pc")
        computed_size = payload_fixed_size(raw, ctx)
        declared_size = as_int(raw.get("payload_size_bytes")) if raw.get("payload_size_bytes") is not None else None
        if declared_size is not None and computed_size is not None:
            ctx.require(declared_size == computed_size, f"message {name} payload_size_bytes is inconsistent")

    required_messages = {
        "PING", "GET_DEVICE_INFO", "SET_STREAM_CONFIG", "START_STREAM", "STOP_STREAM",
        "ACK", "NACK", "DEVICE_INFO", "DEVICE_STATUS", "TELEMETRY_SAMPLE", "ERROR_REPORT",
    }
    missing = required_messages - messages_by_name.keys()
    if missing:
        ctx.errors.append("messages missing: " + ", ".join(sorted(missing)))

    sequence_rules = document.get("sequence_rules")
    if not isinstance(sequence_rules, dict):
        ctx.errors.append("sequence_rules shall be a mapping")
    else:
        host = sequence_rules.get("host_command")
        direct = sequence_rules.get("direct_response")
        unsolicited = sequence_rules.get("unsolicited_device_message")
        ctx.require(isinstance(host, dict) and as_int(host.get("width_bits")) == 16, "sequence_rules.host_command.width_bits shall equal sequence field width 16")
        ctx.require(isinstance(direct, dict) and direct.get("copies_request_sequence") is True, "sequence_rules.direct_response.copies_request_sequence shall be true")
        ctx.require(isinstance(unsolicited, dict) and as_int(unsolicited.get("width_bits")) == 16, "sequence_rules.unsolicited_device_message.width_bits shall equal sequence field width 16")

    for name, message in messages_by_name.items():
        responses = message.get("valid_responses")
        if responses is None:
            continue
        ctx.require(message.get("kind") == "command", f"message {name}.valid_responses is only allowed for commands")
        if not isinstance(responses, list) or not responses:
            ctx.errors.append(f"message {name}.valid_responses shall be a non-empty list")
            continue
        for response_name in responses:
            response = messages_by_name.get(response_name)
            if response is None:
                ctx.errors.append(f"message {name} references unknown response: {response_name}")
                continue
            ctx.require(response.get("kind") == "response", f"message {name} response {response_name} shall have kind response")
            ctx.require(response.get("direction") == "mcu_to_pc", f"message {name} response {response_name} shall be mcu_to_pc")
            ctx.require(response.get("sequence_rule") == "copy_request_sequence", f"message {name} response {response_name} shall copy the request sequence")

    return protocol, messages_by_name, messages_by_id


def run_git(root: Path, *arguments: str) -> subprocess.CompletedProcess[bytes] | None:
    try:
        return subprocess.run(["git", "-C", str(root), *arguments], check=False, capture_output=True)
    except FileNotFoundError:
        return None


def validate_provenance(root: Path, protocol: dict[str, Any], actual_sha: str, require_git: bool, ctx: Context) -> None:
    baseline = load_yaml(root / "baselines/repositories.yaml", "baseline manifest", ctx)
    status = load_yaml(root / "protocol/implementation-status.yaml", "implementation status", ctx)
    if baseline is None or status is None:
        return
    try:
        shared = baseline["shared_contract"]
        authority = shared["authority"]
        protocol_status = status["protocol_contract"]
    except (KeyError, TypeError):
        ctx.errors.append("Protocol provenance mappings are incomplete")
        return
    if not isinstance(shared, dict) or not isinstance(authority, dict) or not isinstance(protocol_status, dict):
        ctx.errors.append("Protocol provenance mappings are invalid")
        return

    baseline_commit = authority.get("repository_commit")
    status_commit = protocol_status.get("system_repository_commit")
    ctx.require(isinstance(baseline_commit, str) and bool(COMMIT_RE.fullmatch(baseline_commit)), "baseline authority repository_commit shall be a full lowercase 40-character SHA")
    ctx.require(isinstance(status_commit, str) and bool(COMMIT_RE.fullmatch(status_commit)), "implementation status system_repository_commit shall be a full lowercase 40-character SHA")
    ctx.require(baseline_commit == status_commit, "authority commit differs between baseline and implementation status")
    ctx.require(authority.get("repository") == protocol_status.get("repository") == "host-device-control-poc-system", "authority repository provenance is inconsistent")
    ctx.require(authority.get("path") == protocol_status.get("path") == "protocol/protocol.yaml", "authority path provenance is inconsistent")
    ctx.require(authority.get("repository_commit_status") == "pinned", "authority repository_commit_status shall be pinned")
    ctx.require(authority.get("file_sha256") == actual_sha, "baseline Protocol SHA-256 does not match protocol/protocol.yaml")
    ctx.require(protocol_status.get("sha256") == actual_sha, "implementation-status Protocol SHA-256 does not match protocol/protocol.yaml")
    ctx.require(shared.get("protocol_version") == protocol.get("version"), "baseline protocol_version differs from contract")
    ctx.require(as_int(shared.get("wire_version")) == as_int(protocol.get("wire_version")), "baseline wire_version differs from contract")
    ctx.require(protocol_status.get("version") == protocol.get("version"), "implementation status version differs from contract")
    ctx.require(as_int(protocol_status.get("wire_version")) == as_int(protocol.get("wire_version")), "implementation status wire_version differs from contract")
    ctx.require(protocol_status.get("status") == protocol.get("status"), "implementation status lifecycle state differs from contract")

    if not isinstance(baseline_commit, str) or not COMMIT_RE.fullmatch(baseline_commit):
        return
    probe = run_git(root, "rev-parse", "--is-inside-work-tree")
    if probe is None or probe.returncode != 0 or probe.stdout.strip() != b"true":
        message = "Git history is unavailable; pinned authority commit provenance was not verified"
        if require_git:
            ctx.errors.append(message)
        else:
            ctx.notices.append(message + ". Run from a full checkout with --require-git-history for CI-grade validation.")
        return
    exists = run_git(root, "cat-file", "-e", f"{baseline_commit}^{{commit}}")
    if exists is None or exists.returncode != 0:
        ctx.errors.append(f"pinned authority commit does not exist in local Git history: {baseline_commit}")
        return
    ancestor = run_git(root, "merge-base", "--is-ancestor", baseline_commit, "HEAD")
    if ancestor is None or ancestor.returncode != 0:
        ctx.errors.append(f"pinned authority commit is not an ancestor of HEAD: {baseline_commit}")
        return
    historical = run_git(root, "show", f"{baseline_commit}:protocol/protocol.yaml")
    if historical is None or historical.returncode != 0:
        ctx.errors.append(f"pinned authority commit does not contain protocol/protocol.yaml: {baseline_commit}")
        return
    historical_sha = hashlib.sha256(historical.stdout).hexdigest()
    ctx.require(historical_sha == actual_sha, "historical Protocol SHA-256 at the pinned authority commit does not match the recorded SHA-256")


def validate_vectors(vector_doc: dict[str, Any], protocol: dict[str, Any], messages_by_id: dict[int, dict[str, Any]], ctx: Context) -> None:
    ctx.require(vector_doc.get("protocol") == protocol.get("name"), "vector protocol metadata mismatch")
    ctx.require(vector_doc.get("protocol_version") == protocol.get("version"), "vector protocol_version metadata mismatch")
    ctx.require(as_int(vector_doc.get("wire_version")) == as_int(protocol.get("wire_version")), "vector wire_version metadata mismatch")
    ctx.require(vector_doc.get("contract_status") == protocol.get("status"), "vector contract_status metadata mismatch")
    ctx.require(vector_doc.get("byte_order") == protocol.get("byte_order"), "vector byte_order metadata mismatch")
    ctx.require(vector_doc.get("crc_storage") == "little_endian", "vector crc_storage metadata mismatch")
    vectors = vector_doc.get("vectors")
    if not isinstance(vectors, list) or not vectors:
        ctx.errors.append("vectors shall be a non-empty list")
        return
    seen_names: set[str] = set()
    covered_kinds: set[str] = set()
    for index, vector in enumerate(vectors):
        if not isinstance(vector, dict):
            ctx.errors.append(f"vectors[{index}] shall be an object")
            continue
        name = vector.get("name")
        if not isinstance(name, str) or not name:
            ctx.errors.append(f"vectors[{index}].name shall be a non-empty string")
            continue
        if name in seen_names:
            ctx.errors.append(f"duplicate vector name: {name}")
        seen_names.add(name)
        message_id = as_int(vector.get("message_id"))
        sequence = as_int(vector.get("sequence"))
        try:
            payload = bytes.fromhex(vector.get("payload_hex", ""))
            frame = bytes.fromhex(vector.get("frame_hex", ""))
        except (TypeError, ValueError):
            ctx.errors.append(f"vector {name} contains invalid hexadecimal text")
            continue
        if message_id is None or sequence is None:
            ctx.errors.append(f"vector {name} message_id or sequence is invalid")
            continue
        if len(frame) < 10:
            ctx.errors.append(f"vector {name} frame is shorter than minimum frame size")
            continue
        ctx.require(frame[:2] == b"\xA5\x5A", f"vector {name} SOF mismatch")
        ctx.require(frame[2] == as_int(protocol.get("wire_version")), f"vector {name} wire version mismatch")
        ctx.require(frame[3] == message_id, f"vector {name} encoded message ID mismatch")
        ctx.require(int.from_bytes(frame[4:6], "little") == sequence, f"vector {name} encoded sequence mismatch")
        payload_length = int.from_bytes(frame[6:8], "little")
        ctx.require(payload_length == len(payload), f"vector {name} payload length mismatch")
        ctx.require(len(frame) == 10 + payload_length, f"vector {name} frame size mismatch")
        if len(frame) == 10 + payload_length:
            ctx.require(frame[8 : 8 + payload_length] == payload, f"vector {name} payload bytes mismatch")
            expected_crc = int.from_bytes(frame[-2:], "little")
            actual_crc = crc16_ccitt_false(frame[2:-2])
            ctx.require(actual_crc == expected_crc, f"vector {name} CRC mismatch")
        message = messages_by_id.get(message_id)
        if message is None:
            ctx.errors.append(f"vector {name} references unknown message ID 0x{message_id:02X}")
            continue
        covered_kinds.add(str(message.get("kind")))
        fixed_size = payload_fixed_size(message, ctx)
        if fixed_size is not None:
            ctx.require(len(payload) == fixed_size, f"vector {name} payload size does not match message definition")
    ctx.require("command" in covered_kinds, "vector set shall cover at least one command")
    ctx.require("response" in covered_kinds, "vector set shall cover at least one response")
    ctx.require("event" in covered_kinds, "vector set shall cover at least one event")


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    ctx = Context()
    protocol_path = root / "protocol/protocol.yaml"
    contract = load_yaml(protocol_path, "Protocol contract", ctx)
    if contract is None:
        for error in ctx.errors:
            print(f"ERROR: {error}")
        return 1
    validated = validate_contract(contract, ctx)
    if validated is not None:
        protocol, _messages_by_name, messages_by_id = validated
        actual_sha = hashlib.sha256(protocol_path.read_bytes()).hexdigest()
        validate_provenance(root, protocol, actual_sha, args.require_git_history, ctx)
        vectors = load_json(root / "protocol/test-vectors/protocol-v0.1.0-vectors.json", "Protocol vectors", ctx)
        if vectors is not None:
            validate_vectors(vectors, protocol, messages_by_id, ctx)

    for notice in ctx.notices:
        print(f"NOTICE: {notice}")
    if ctx.errors:
        for error in ctx.errors:
            print(f"ERROR: {error}")
        print(f"Protocol contract validation failed with {len(ctx.errors)} error(s).")
        return 1
    print("Protocol contract, provenance, and vectors validated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
