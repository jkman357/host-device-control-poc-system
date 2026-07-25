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

AUTHORITY_COMMIT_PATTERN = re.compile(r"^[0-9a-f]{40}$")
SUPPORTED_CRC_ALGORITHM = "crc_16_ccitt_false"
FIXED_SCALAR_SIZES = {
    "uint8": 1,
    "uint16": 2,
    "uint32": 4,
    "float32_ieee754": 4,
}
INTEGER_TYPES = {"uint8", "uint16", "uint32"}
SUPPORTED_BYTE_ORDERS = {"little_endian", "big_endian"}


class ValidationContext:
    """Collect validation failures and non-fatal notices."""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.notices: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def notice(self, message: str) -> None:
        self.notices.append(message)

    def require(self, condition: bool, message: str) -> bool:
        if not condition:
            self.error(message)
            return False
        return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root to validate (defaults to the current repository).",
    )
    parser.add_argument(
        "--require-git-history",
        action="store_true",
        help="Fail unless the pinned authority commit can be verified from local Git history.",
    )
    return parser.parse_args()


def load_yaml_mapping(path: Path, ctx: ValidationContext, label: str) -> dict[str, Any] | None:
    if not path.is_file():
        ctx.error(f"missing {label}: {path}")
        return None
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        ctx.error(f"invalid YAML in {label}: {exc}")
        return None
    if not isinstance(payload, dict):
        ctx.error(f"{label} root shall be a mapping")
        return None
    return payload


def load_json_mapping(path: Path, ctx: ValidationContext, label: str) -> dict[str, Any] | None:
    if not path.is_file():
        ctx.error(f"missing {label}: {path}")
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        ctx.error(f"invalid JSON in {label}: {exc}")
        return None
    if not isinstance(payload, dict):
        ctx.error(f"{label} root shall be an object")
        return None
    return payload


def as_mapping(value: Any, ctx: ValidationContext, label: str) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        ctx.error(f"{label} shall be a mapping")
        return None
    return value


def as_list(value: Any, ctx: ValidationContext, label: str) -> list[Any] | None:
    if not isinstance(value, list):
        ctx.error(f"{label} shall be a list")
        return None
    return value


def as_int(value: Any, ctx: ValidationContext, label: str) -> int | None:
    if isinstance(value, bool):
        ctx.error(f"{label} shall be an integer, not boolean")
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value, 0)
        except ValueError:
            pass
    ctx.error(f"{label} shall be an integer or base-prefixed integer string")
    return None


def field_byte_order(
    field: dict[str, Any],
    protocol_byte_order: str,
    ctx: ValidationContext,
    label: str,
) -> str:
    field_type = field.get("type")
    size = field.get("size_bytes")
    explicit = field.get("byte_order")

    if explicit is not None and explicit not in SUPPORTED_BYTE_ORDERS:
        ctx.error(f"{label}.byte_order is unsupported: {explicit}")
        return protocol_byte_order

    if field_type in INTEGER_TYPES and isinstance(size, int) and size > 1:
        ctx.require(explicit is not None, f"{label}.byte_order shall be explicit for multi-byte integer fields")
        if explicit is not None:
            ctx.require(
                explicit == protocol_byte_order,
                f"{label}.byte_order shall match protocol.byte_order {protocol_byte_order}",
            )
            return explicit

    if explicit is not None:
        ctx.require(
            explicit == protocol_byte_order,
            f"{label}.byte_order shall match protocol.byte_order {protocol_byte_order}",
        )
        return explicit

    return protocol_byte_order


def read_uint(
    data: bytes,
    offset: int,
    size: int,
    byte_order: str,
    ctx: ValidationContext,
    label: str,
) -> int | None:
    if offset < 0 or size <= 0 or offset + size > len(data):
        ctx.error(f"{label} is outside the encoded frame")
        return None
    if byte_order not in SUPPORTED_BYTE_ORDERS:
        ctx.error(f"unsupported byte order for {label}: {byte_order}")
        return None
    python_order = "little" if byte_order == "little_endian" else "big"
    return int.from_bytes(data[offset : offset + size], python_order)


def crc16_ccitt_false(data: bytes, polynomial: int, initial_value: int, xor_output: int) -> int:
    crc = initial_value
    for value in data:
        crc ^= value << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ polynomial) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc ^ xor_output


def fixed_payload_size(message: dict[str, Any], ctx: ValidationContext) -> int | None:
    payload = message.get("payload")
    if not isinstance(payload, list):
        ctx.error(f"message {message.get('name', '<unnamed>')} payload shall be a list")
        return None

    total = 0
    for index, field in enumerate(payload):
        if not isinstance(field, dict):
            ctx.error(f"message {message.get('name', '<unnamed>')} payload[{index}] shall be a mapping")
            return None
        field_type = field.get("type")
        if field_type in FIXED_SCALAR_SIZES:
            total += FIXED_SCALAR_SIZES[field_type]
        elif field_type in {"byte_array", "utf8_byte_array"}:
            size = field.get("size_bytes")
            if isinstance(size, int):
                total += size
            else:
                return None
        else:
            ctx.error(
                f"message {message.get('name', '<unnamed>')} payload field "
                f"{field.get('name', index)} has unsupported type: {field_type}"
            )
            return None
    return total


def validate_field_type_and_size(
    field: dict[str, Any],
    ctx: ValidationContext,
    label: str,
) -> None:
    field_type = field.get("type")
    size = field.get("size_bytes")
    if field_type in FIXED_SCALAR_SIZES:
        expected_size = FIXED_SCALAR_SIZES[field_type]
        ctx.require(
            size == expected_size,
            f"{label} type {field_type} requires size_bytes {expected_size}",
        )
    elif field_type == "byte_array":
        ctx.require(size == "payload_length", f"{label} byte_array size_bytes shall reference payload_length")
    else:
        ctx.error(f"{label} has unsupported type: {field_type}")


def validate_sequence_rules(
    contract_doc: dict[str, Any],
    fields_by_name: dict[str, dict[str, Any]],
    messages_by_name: dict[str, dict[str, Any]],
    ctx: ValidationContext,
) -> None:
    sequence_rules = as_mapping(contract_doc.get("sequence_rules"), ctx, "sequence_rules")
    if sequence_rules is None:
        return

    sequence_size = as_int(
        fields_by_name["sequence"].get("size_bytes"),
        ctx,
        "framing field sequence.size_bytes",
    )
    if sequence_size is None:
        return
    expected_width_bits = sequence_size * 8

    host_command = as_mapping(sequence_rules.get("host_command"), ctx, "sequence_rules.host_command")
    direct_response = as_mapping(sequence_rules.get("direct_response"), ctx, "sequence_rules.direct_response")
    unsolicited = as_mapping(
        sequence_rules.get("unsolicited_device_message"),
        ctx,
        "sequence_rules.unsolicited_device_message",
    )
    if host_command is not None:
        width = as_int(host_command.get("width_bits"), ctx, "sequence_rules.host_command.width_bits")
        if width is not None:
            ctx.require(
                width == expected_width_bits,
                f"sequence_rules.host_command.width_bits shall equal sequence field width {expected_width_bits}",
            )
        ctx.require(isinstance(host_command.get("zero_allowed"), bool), "sequence_rules.host_command.zero_allowed shall be boolean")
    if direct_response is not None:
        ctx.require(
            direct_response.get("copies_request_sequence") is True,
            "sequence_rules.direct_response.copies_request_sequence shall be true",
        )
    if unsolicited is not None:
        width = as_int(
            unsolicited.get("width_bits"),
            ctx,
            "sequence_rules.unsolicited_device_message.width_bits",
        )
        if width is not None:
            ctx.require(
                width == expected_width_bits,
                f"sequence_rules.unsolicited_device_message.width_bits shall equal sequence field width {expected_width_bits}",
            )

    for name, message in messages_by_name.items():
        kind = message.get("kind")
        direction = message.get("direction")
        if kind == "command":
            ctx.require(direction == "pc_to_mcu", f"message {name} command direction shall be pc_to_mcu")
        elif kind == "response":
            ctx.require(direction == "mcu_to_pc", f"message {name} response direction shall be mcu_to_pc")
            ctx.require(
                message.get("sequence_rule") == "copy_request_sequence",
                f"message {name} sequence_rule shall be copy_request_sequence",
            )
        elif kind in {"event", "response_or_event"}:
            ctx.require(direction == "mcu_to_pc", f"message {name} {kind} direction shall be mcu_to_pc")


def validate_contract(
    contract_doc: dict[str, Any],
    ctx: ValidationContext,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[int, dict[str, Any]]] | None:
    protocol = as_mapping(contract_doc.get("protocol"), ctx, "protocol")
    framing = as_mapping(contract_doc.get("framing"), ctx, "framing")
    messages = as_list(contract_doc.get("messages"), ctx, "messages")
    if protocol is None or framing is None or messages is None:
        return None

    ctx.require(protocol.get("name") == "host-device-control-poc", "protocol.name shall be host-device-control-poc")
    version = protocol.get("version")
    ctx.require(
        isinstance(version, str) and bool(re.fullmatch(r"\d+\.\d+\.\d+", version)),
        "protocol.version shall use semantic x.y.z syntax",
    )
    wire_version = as_int(protocol.get("wire_version"), ctx, "protocol.wire_version")
    if wire_version is not None:
        ctx.require(0 <= wire_version <= 0xFF, "protocol.wire_version shall fit uint8")

    lifecycle = as_mapping(protocol.get("lifecycle"), ctx, "protocol.lifecycle")
    if lifecycle is not None:
        allowed_statuses = as_list(lifecycle.get("allowed_statuses"), ctx, "protocol.lifecycle.allowed_statuses")
        if allowed_statuses is not None:
            ctx.require(protocol.get("status") in allowed_statuses, "protocol.status shall be listed in lifecycle.allowed_statuses")

    authority = as_mapping(protocol.get("authority"), ctx, "protocol.authority")
    if authority is not None:
        ctx.require(authority.get("repository") == "host-device-control-poc-system", "protocol authority repository is incorrect")
        ctx.require(authority.get("path") == "protocol/protocol.yaml", "protocol authority path is incorrect")
        ctx.require(authority.get("rule") == "specification_precedes_implementation", "protocol authority rule is incorrect")

    byte_order = protocol.get("byte_order")
    ctx.require(byte_order in SUPPORTED_BYTE_ORDERS, "protocol.byte_order is unsupported")
    scalar_encoding = as_mapping(protocol.get("scalar_encoding"), ctx, "protocol.scalar_encoding")
    if scalar_encoding is not None and byte_order in SUPPORTED_BYTE_ORDERS:
        ctx.require(
            scalar_encoding.get("unsigned_integers") == byte_order,
            "protocol.scalar_encoding.unsigned_integers shall match protocol.byte_order",
        )
        expected_float = f"ieee_754_binary32_{byte_order}"
        ctx.require(
            scalar_encoding.get("float32") == expected_float,
            f"protocol.scalar_encoding.float32 shall be {expected_float}",
        )
        ctx.require(
            scalar_encoding.get("crc16_storage") == byte_order,
            "protocol.scalar_encoding.crc16_storage shall match protocol.byte_order",
        )

    sof = as_mapping(framing.get("sof"), ctx, "framing.sof")
    fields = as_list(framing.get("fields"), ctx, "framing.fields")
    crc = as_mapping(framing.get("crc"), ctx, "framing.crc")
    if sof is None or fields is None or crc is None:
        return None

    sof_values = as_list(sof.get("bytes"), ctx, "framing.sof.bytes")
    sof_bytes: bytes | None = None
    if sof_values is not None:
        parsed_sof: list[int] = []
        for index, value in enumerate(sof_values):
            parsed = as_int(value, ctx, f"framing.sof.bytes[{index}]")
            if parsed is not None and ctx.require(0 <= parsed <= 0xFF, f"framing.sof.bytes[{index}] shall fit uint8"):
                parsed_sof.append(parsed)
        if len(parsed_sof) == len(sof_values):
            sof_bytes = bytes(parsed_sof)
            ctx.require(len(sof_bytes) > 0, "framing.sof.bytes shall not be empty")
    ctx.require(sof.get("included_in_crc") is False, "this validator supports framing.sof.included_in_crc=false")

    fields_by_name: dict[str, dict[str, Any]] = {}
    for index, raw_field in enumerate(fields):
        field = as_mapping(raw_field, ctx, f"framing.fields[{index}]")
        if field is None:
            continue
        name = field.get("name")
        if not isinstance(name, str) or not name:
            ctx.error(f"framing.fields[{index}].name shall be a non-empty string")
            continue
        if name in fields_by_name:
            ctx.error(f"duplicate framing field name: {name}")
            continue
        fields_by_name[name] = field

    required_field_names = {"version", "message_id", "sequence", "payload_length", "payload", "crc16"}
    missing_fields = required_field_names - fields_by_name.keys()
    if missing_fields:
        ctx.error("framing.fields missing: " + ", ".join(sorted(missing_fields)))
        return None

    for name in ["version", "message_id", "sequence", "payload_length", "payload", "crc16"]:
        validate_field_type_and_size(fields_by_name[name], ctx, f"framing field {name}")
        if byte_order in SUPPORTED_BYTE_ORDERS:
            field_byte_order(fields_by_name[name], byte_order, ctx, f"framing field {name}")

    ctx.require(fields_by_name["crc16"].get("type") == "uint16", "framing field crc16 type shall be uint16")

    fixed_order = ["version", "message_id", "sequence", "payload_length"]
    expected_offset = len(sof_bytes) if sof_bytes is not None else 0
    for name in fixed_order:
        field = fields_by_name[name]
        offset = as_int(field.get("offset_bytes"), ctx, f"framing field {name}.offset_bytes")
        size = as_int(field.get("size_bytes"), ctx, f"framing field {name}.size_bytes")
        if offset is not None:
            ctx.require(offset == expected_offset, f"framing field {name} offset shall be {expected_offset}, got {offset}")
        if size is not None:
            ctx.require(size > 0, f"framing field {name} size shall be positive")
            expected_offset += max(size, 0)

    payload_field = fields_by_name["payload"]
    payload_offset = as_int(payload_field.get("offset_bytes"), ctx, "framing field payload.offset_bytes")
    if payload_offset is not None:
        ctx.require(payload_offset == expected_offset, f"payload offset shall be {expected_offset}, got {payload_offset}")

    crc_field = fields_by_name["crc16"]
    expected_crc_offset = f"{expected_offset}_plus_payload_length"
    ctx.require(crc_field.get("offset_bytes") == expected_crc_offset, f"crc16 offset shall be {expected_crc_offset}")
    crc_size = as_int(crc_field.get("size_bytes"), ctx, "framing field crc16.size_bytes")

    minimum_frame_size = as_int(framing.get("minimum_frame_size_bytes"), ctx, "framing.minimum_frame_size_bytes")
    if minimum_frame_size is not None and crc_size is not None:
        ctx.require(minimum_frame_size == expected_offset + crc_size, "minimum_frame_size_bytes does not match the field layout")

    maximum_payload = as_int(framing.get("maximum_payload_size_bytes"), ctx, "framing.maximum_payload_size_bytes")
    length_size = as_int(fields_by_name["payload_length"].get("size_bytes"), ctx, "payload_length.size_bytes")
    if maximum_payload is not None and length_size is not None:
        ctx.require(0 <= maximum_payload <= (1 << (8 * length_size)) - 1, "maximum payload does not fit payload_length")

    if scalar_encoding is not None and byte_order in SUPPORTED_BYTE_ORDERS:
        crc_order = field_byte_order(crc_field, byte_order, ctx, "framing field crc16")
        ctx.require(
            scalar_encoding.get("crc16_storage") == crc_order,
            "framing field crc16.byte_order shall match protocol.scalar_encoding.crc16_storage",
        )

    ctx.require(crc.get("algorithm") == SUPPORTED_CRC_ALGORITHM, f"CRC algorithm shall be {SUPPORTED_CRC_ALGORITHM}")
    ctx.require(crc.get("reflect_input") is False, "CRC reflect_input shall be false")
    ctx.require(crc.get("reflect_output") is False, "CRC reflect_output shall be false")
    ctx.require(crc.get("covered_bytes") == "version_through_end_of_payload", "unsupported CRC coverage")
    polynomial = as_int(crc.get("polynomial"), ctx, "framing.crc.polynomial")
    initial_value = as_int(crc.get("initial_value"), ctx, "framing.crc.initial_value")
    xor_output = as_int(crc.get("xor_output"), ctx, "framing.crc.xor_output")
    check_vector = as_mapping(crc.get("check_vector"), ctx, "framing.crc.check_vector")
    if None not in {polynomial, initial_value, xor_output} and check_vector is not None:
        expected_check = as_int(check_vector.get("expected"), ctx, "framing.crc.check_vector.expected")
        input_ascii = check_vector.get("input_ascii")
        if isinstance(input_ascii, str) and expected_check is not None:
            try:
                encoded_check = input_ascii.encode("ascii")
            except UnicodeEncodeError:
                ctx.error("framing.crc.check_vector.input_ascii shall contain ASCII characters only")
            else:
                actual_check = crc16_ccitt_false(encoded_check, polynomial, initial_value, xor_output)
                ctx.require(actual_check == expected_check, "CRC check vector does not match declared parameters")
        else:
            ctx.error("framing.crc.check_vector.input_ascii shall be a string")

    message_id_size = as_int(fields_by_name["message_id"].get("size_bytes"), ctx, "message_id.size_bytes")
    max_message_id = (1 << (8 * message_id_size)) - 1 if message_id_size is not None else None
    messages_by_name: dict[str, dict[str, Any]] = {}
    messages_by_id: dict[int, dict[str, Any]] = {}
    for index, raw_message in enumerate(messages):
        message = as_mapping(raw_message, ctx, f"messages[{index}]")
        if message is None:
            continue
        name = message.get("name")
        message_id = as_int(message.get("id"), ctx, f"messages[{index}].id")
        if not isinstance(name, str) or not name:
            ctx.error(f"messages[{index}].name shall be a non-empty string")
            continue
        if name in messages_by_name:
            ctx.error(f"duplicate message name: {name}")
        else:
            messages_by_name[name] = message
        if message_id is not None:
            if max_message_id is not None:
                ctx.require(0 <= message_id <= max_message_id, f"message ID {name} does not fit message_id field")
            if message_id in messages_by_id:
                ctx.error(f"duplicate message ID: 0x{message_id:X}")
            else:
                messages_by_id[message_id] = message
        ctx.require(message.get("direction") in {"pc_to_mcu", "mcu_to_pc"}, f"message {name} has invalid direction")
        ctx.require(message.get("kind") in {"command", "response", "event", "response_or_event"}, f"message {name} has invalid kind")
        computed_payload_size = fixed_payload_size(message, ctx)
        declared_payload_size = message.get("payload_size_bytes")
        if declared_payload_size is not None:
            declared_payload_size_int = as_int(declared_payload_size, ctx, f"message {name}.payload_size_bytes")
            if computed_payload_size is not None and declared_payload_size_int is not None:
                ctx.require(declared_payload_size_int == computed_payload_size, f"message {name} payload_size_bytes is inconsistent")

    validate_sequence_rules(contract_doc, fields_by_name, messages_by_name, ctx)

    for name, message in messages_by_name.items():
        responses = message.get("valid_responses")
        if responses is None:
            continue
        ctx.require(message.get("kind") == "command", f"message {name}.valid_responses is only allowed for commands")
        response_names = as_list(responses, ctx, f"message {name}.valid_responses")
        if response_names is None:
            continue
        ctx.require(len(response_names) > 0, f"message {name}.valid_responses shall not be empty")
        for response_name in response_names:
            response = messages_by_name.get(response_name)
            if response is None:
                ctx.error(f"message {name} references unknown response: {response_name}")
                continue
            ctx.require(
                response.get("direction") == "mcu_to_pc",
                f"message {name} response {response_name} shall be mcu_to_pc",
            )
            ctx.require(
                response.get("kind") == "response",
                f"message {name} response {response_name} shall have kind response",
            )
            ctx.require(
                response.get("sequence_rule") == "copy_request_sequence",
                f"message {name} response {response_name} shall copy the request sequence",
            )

    return protocol, fields_by_name, messages_by_id


def run_git(root: Path, arguments: list[str]) -> subprocess.CompletedProcess[bytes] | None:
    try:
        return subprocess.run(
            ["git", "-C", str(root), *arguments],
            check=False,
            capture_output=True,
        )
    except FileNotFoundError:
        return None


def verify_git_provenance(
    root: Path,
    commit: str,
    authority_path: str,
    recorded_sha256: str,
    require_git_history: bool,
    ctx: ValidationContext,
) -> None:
    probe = run_git(root, ["rev-parse", "--is-inside-work-tree"])
    if probe is None or probe.returncode != 0 or probe.stdout.strip() != b"true":
        message = "Git history is unavailable; pinned authority commit provenance was not verified"
        if require_git_history:
            ctx.error(message)
        else:
            ctx.notice(message + ". Run from a full checkout with --require-git-history for CI-grade validation.")
        return

    exists = run_git(root, ["cat-file", "-e", f"{commit}^{{commit}}"])
    if exists is None or exists.returncode != 0:
        ctx.error(f"pinned authority commit does not exist in local Git history: {commit}")
        return

    ancestor = run_git(root, ["merge-base", "--is-ancestor", commit, "HEAD"])
    if ancestor is None or ancestor.returncode != 0:
        ctx.error(f"pinned authority commit is not an ancestor of HEAD: {commit}")
        return

    historical = run_git(root, ["show", f"{commit}:{authority_path}"])
    if historical is None or historical.returncode != 0:
        ctx.error(f"pinned authority commit does not contain {authority_path}: {commit}")
        return

    historical_sha256 = hashlib.sha256(historical.stdout).hexdigest()
    ctx.require(
        historical_sha256 == recorded_sha256,
        "historical Protocol SHA-256 at the pinned authority commit does not match the recorded SHA-256",
    )


def validate_provenance(
    root: Path,
    protocol: dict[str, Any],
    actual_sha256: str,
    require_git_history: bool,
    ctx: ValidationContext,
) -> None:
    baseline_path = root / "baselines" / "repositories.yaml"
    status_path = root / "protocol" / "implementation-status.yaml"
    baseline_doc = load_yaml_mapping(baseline_path, ctx, "baseline manifest")
    status_doc = load_yaml_mapping(status_path, ctx, "implementation status")
    if baseline_doc is None or status_doc is None:
        return

    shared_contract = as_mapping(baseline_doc.get("shared_contract"), ctx, "baseline.shared_contract")
    authority = as_mapping(shared_contract.get("authority"), ctx, "baseline.shared_contract.authority") if shared_contract else None
    protocol_contract = as_mapping(status_doc.get("protocol_contract"), ctx, "implementation-status.protocol_contract")
    if authority is None or protocol_contract is None:
        return

    baseline_commit = authority.get("repository_commit")
    status_commit = protocol_contract.get("system_repository_commit")
    valid_commits = True
    for label, value in (
        ("baseline authority repository_commit", baseline_commit),
        ("implementation status system_repository_commit", status_commit),
    ):
        valid_commits &= ctx.require(
            isinstance(value, str) and bool(AUTHORITY_COMMIT_PATTERN.fullmatch(value)),
            f"{label} shall be a full lowercase 40-character SHA",
        )

    ctx.require(authority.get("repository") == protocol_contract.get("repository") == "host-device-control-poc-system", "authority repository provenance is inconsistent")
    ctx.require(authority.get("path") == protocol_contract.get("path") == "protocol/protocol.yaml", "authority path provenance is inconsistent")
    ctx.require(authority.get("repository_commit_status") == "pinned", "authority repository_commit_status shall be pinned")
    ctx.require(baseline_commit == status_commit, "authority commit differs between baseline and implementation status")
    ctx.require(authority.get("file_sha256") == actual_sha256, "baseline Protocol SHA-256 does not match protocol/protocol.yaml")
    ctx.require(protocol_contract.get("sha256") == actual_sha256, "implementation-status Protocol SHA-256 does not match protocol/protocol.yaml")
    ctx.require(shared_contract.get("protocol_version") == protocol.get("version"), "baseline protocol_version differs from contract")
    ctx.require(as_int(shared_contract.get("wire_version"), ctx, "baseline.shared_contract.wire_version") == as_int(protocol.get("wire_version"), ctx, "protocol.wire_version"), "baseline wire_version differs from contract")
    ctx.require(protocol_contract.get("version") == protocol.get("version"), "implementation status version differs from contract")
    ctx.require(as_int(protocol_contract.get("wire_version"), ctx, "implementation-status.wire_version") == as_int(protocol.get("wire_version"), ctx, "protocol.wire_version"), "implementation status wire_version differs from contract")
    ctx.require(protocol_contract.get("status") == protocol.get("status"), "implementation status lifecycle state differs from contract")

    if valid_commits and baseline_commit == status_commit and isinstance(baseline_commit, str):
        authority_path = authority.get("path")
        recorded_sha256 = authority.get("file_sha256")
        if isinstance(authority_path, str) and isinstance(recorded_sha256, str):
            verify_git_provenance(
                root,
                baseline_commit,
                authority_path,
                recorded_sha256,
                require_git_history,
                ctx,
            )


def validate_vectors(
    vectors_doc: dict[str, Any],
    protocol: dict[str, Any],
    fields: dict[str, dict[str, Any]],
    messages_by_id: dict[int, dict[str, Any]],
    framing_doc: dict[str, Any],
    ctx: ValidationContext,
) -> None:
    wire_version = as_int(protocol.get("wire_version"), ctx, "protocol.wire_version")
    ctx.require(vectors_doc.get("protocol") == protocol.get("name"), "vector protocol name differs from contract")
    ctx.require(vectors_doc.get("protocol_version") == protocol.get("version"), "vector protocol_version differs from contract")
    ctx.require(as_int(vectors_doc.get("wire_version"), ctx, "vectors.wire_version") == wire_version, "vector wire_version differs from contract")
    ctx.require(vectors_doc.get("contract_status") == protocol.get("status"), "vector contract_status differs from contract")
    ctx.require(vectors_doc.get("byte_order") == protocol.get("byte_order"), "vector byte_order differs from contract")
    scalar_encoding = as_mapping(protocol.get("scalar_encoding"), ctx, "protocol.scalar_encoding")
    if scalar_encoding is not None:
        ctx.require(vectors_doc.get("crc_storage") == scalar_encoding.get("crc16_storage"), "vector CRC storage differs from contract")

    sof = as_mapping(framing_doc.get("sof"), ctx, "framing.sof")
    crc = as_mapping(framing_doc.get("crc"), ctx, "framing.crc")
    if sof is None or crc is None:
        return
    sof_values = sof.get("bytes")
    if not isinstance(sof_values, list) or not all(isinstance(value, int) for value in sof_values):
        ctx.error("framing.sof.bytes is not usable for vector validation")
        return
    sof_bytes = bytes(sof_values)

    required_names = ["version", "message_id", "sequence", "payload_length", "payload", "crc16"]
    if any(name not in fields for name in required_names):
        return

    version_offset = as_int(fields["version"].get("offset_bytes"), ctx, "version.offset_bytes")
    version_size = as_int(fields["version"].get("size_bytes"), ctx, "version.size_bytes")
    message_offset = as_int(fields["message_id"].get("offset_bytes"), ctx, "message_id.offset_bytes")
    message_size = as_int(fields["message_id"].get("size_bytes"), ctx, "message_id.size_bytes")
    sequence_offset = as_int(fields["sequence"].get("offset_bytes"), ctx, "sequence.offset_bytes")
    sequence_size = as_int(fields["sequence"].get("size_bytes"), ctx, "sequence.size_bytes")
    length_offset = as_int(fields["payload_length"].get("offset_bytes"), ctx, "payload_length.offset_bytes")
    length_size = as_int(fields["payload_length"].get("size_bytes"), ctx, "payload_length.size_bytes")
    payload_offset = as_int(fields["payload"].get("offset_bytes"), ctx, "payload.offset_bytes")
    crc_size = as_int(fields["crc16"].get("size_bytes"), ctx, "crc16.size_bytes")
    if None in {version_offset, version_size, message_offset, message_size, sequence_offset, sequence_size, length_offset, length_size, payload_offset, crc_size}:
        return

    protocol_order = protocol.get("byte_order")
    if protocol_order not in SUPPORTED_BYTE_ORDERS:
        return
    version_order = field_byte_order(fields["version"], protocol_order, ctx, "framing field version")
    message_order = field_byte_order(fields["message_id"], protocol_order, ctx, "framing field message_id")
    sequence_order = field_byte_order(fields["sequence"], protocol_order, ctx, "framing field sequence")
    length_order = field_byte_order(fields["payload_length"], protocol_order, ctx, "framing field payload_length")
    crc_order = field_byte_order(fields["crc16"], protocol_order, ctx, "framing field crc16")

    polynomial = as_int(crc.get("polynomial"), ctx, "framing.crc.polynomial")
    initial_value = as_int(crc.get("initial_value"), ctx, "framing.crc.initial_value")
    xor_output = as_int(crc.get("xor_output"), ctx, "framing.crc.xor_output")
    if None in {polynomial, initial_value, xor_output}:
        return

    vectors = as_list(vectors_doc.get("vectors"), ctx, "vectors")
    if vectors is None:
        return

    seen_names: set[str] = set()
    coverage: set[str] = set()
    for index, raw_vector in enumerate(vectors):
        vector = as_mapping(raw_vector, ctx, f"vectors[{index}]")
        if vector is None:
            continue
        name = vector.get("name")
        if not isinstance(name, str) or not name:
            ctx.error(f"vectors[{index}].name shall be a non-empty string")
            name = f"<vector-{index}>"
        elif name in seen_names:
            ctx.error(f"duplicate vector name: {name}")
        else:
            seen_names.add(name)

        try:
            frame = bytes.fromhex(vector["frame_hex"])
            declared_payload = bytes.fromhex(vector["payload_hex"])
        except (KeyError, TypeError, ValueError) as exc:
            ctx.error(f"invalid vector encoding for {name}: {exc}")
            continue

        if not ctx.require(frame.startswith(sof_bytes), f"vector {name} has invalid SOF"):
            continue
        encoded_version = read_uint(frame, version_offset, version_size, version_order, ctx, f"vector {name} version")
        encoded_message_id = read_uint(frame, message_offset, message_size, message_order, ctx, f"vector {name} message_id")
        encoded_sequence = read_uint(frame, sequence_offset, sequence_size, sequence_order, ctx, f"vector {name} sequence")
        encoded_length = read_uint(frame, length_offset, length_size, length_order, ctx, f"vector {name} payload_length")
        declared_message_id = as_int(vector.get("message_id"), ctx, f"vector {name}.message_id")
        declared_sequence = as_int(vector.get("sequence"), ctx, f"vector {name}.sequence")
        if None in {encoded_version, encoded_message_id, encoded_sequence, encoded_length, declared_message_id, declared_sequence}:
            continue

        ctx.require(encoded_version == wire_version, f"vector {name} encoded wire version differs from contract")
        ctx.require(encoded_message_id == declared_message_id, f"vector {name} metadata message_id differs from encoded frame")
        ctx.require(encoded_sequence == declared_sequence, f"vector {name} metadata sequence differs from encoded frame")
        ctx.require(encoded_length == len(declared_payload), f"vector {name} payload length metadata differs from encoded frame")
        expected_frame_size = payload_offset + encoded_length + crc_size
        ctx.require(len(frame) == expected_frame_size, f"vector {name} frame size shall be {expected_frame_size}, got {len(frame)}")
        if len(frame) != expected_frame_size:
            continue
        ctx.require(frame[payload_offset : payload_offset + encoded_length] == declared_payload, f"vector {name} payload bytes differ from payload_hex")

        message = messages_by_id.get(encoded_message_id)
        if message is None:
            ctx.error(f"vector {name} uses undefined message ID 0x{encoded_message_id:X}")
        else:
            expected_payload_size = fixed_payload_size(message, ctx)
            if expected_payload_size is not None:
                ctx.require(encoded_length == expected_payload_size, f"vector {name} payload length differs from message {message.get('name')} definition")
            direction = message.get("direction")
            kind = message.get("kind")
            if direction == "pc_to_mcu" and kind == "command":
                coverage.add("command")
            if direction == "mcu_to_pc" and kind == "response":
                coverage.add("response")
            if direction == "mcu_to_pc" and kind in {"event", "response_or_event"}:
                coverage.add("event")

        received_crc = read_uint(
            frame,
            payload_offset + encoded_length,
            crc_size,
            crc_order,
            ctx,
            f"vector {name} crc16",
        )
        calculated_crc = crc16_ccitt_false(
            frame[version_offset : payload_offset + encoded_length],
            polynomial,
            initial_value,
            xor_output,
        )
        if received_crc is not None:
            ctx.require(received_crc == calculated_crc, f"vector {name} CRC mismatch")

    required_coverage = {"command", "response", "event"}
    missing_coverage = required_coverage - coverage
    if missing_coverage:
        ctx.error("normative vectors missing coverage: " + ", ".join(sorted(missing_coverage)))


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    protocol_path = root / "protocol" / "protocol.yaml"
    vectors_path = root / "protocol" / "test-vectors" / "protocol-v0.1.0-vectors.json"
    ctx = ValidationContext()

    contract_doc = load_yaml_mapping(protocol_path, ctx, "Protocol contract")
    vectors_doc = load_json_mapping(vectors_path, ctx, "normative Protocol vectors")
    if contract_doc is None or vectors_doc is None:
        for notice in ctx.notices:
            print(f"NOTICE: {notice}")
        for error in ctx.errors:
            print(f"ERROR: {error}")
        print(f"Protocol validation failed with {len(ctx.errors)} error(s).")
        return 1

    validated = validate_contract(contract_doc, ctx)
    if validated is not None:
        protocol, fields, messages_by_id = validated
        actual_sha256 = hashlib.sha256(protocol_path.read_bytes()).hexdigest()
        validate_provenance(root, protocol, actual_sha256, args.require_git_history, ctx)
        framing_doc = contract_doc.get("framing")
        if isinstance(framing_doc, dict):
            validate_vectors(vectors_doc, protocol, fields, messages_by_id, framing_doc, ctx)

    for notice in ctx.notices:
        print(f"NOTICE: {notice}")
    if ctx.errors:
        for error in ctx.errors:
            print(f"ERROR: {error}")
        print(f"Protocol validation failed with {len(ctx.errors)} error(s).")
        return 1

    print("Protocol contract, provenance, and vectors validated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
