#!/usr/bin/env python3
"""Validate required Protocol contract markers and normative frame vectors."""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL = ROOT / "protocol" / "protocol.yaml"
VECTORS = ROOT / "protocol" / "test-vectors" / "protocol-v0.1.0-vectors.json"


def crc16_ccitt_false(data: bytes) -> int:
    crc = 0xFFFF
    for value in data:
        crc ^= value << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def main() -> int:
    errors: list[str] = []
    if not PROTOCOL.is_file():
        errors.append("missing protocol/protocol.yaml")
    if not VECTORS.is_file():
        errors.append("missing normative Protocol vectors")
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    contract = PROTOCOL.read_text(encoding="utf-8")
    required_markers = [
        "name: host-device-control-poc",
        "version: 0.1.0",
        "wire_version: 0x01",
        "status: candidate_for_alignment",
        "repository: host-device-control-poc-system",
        "path: protocol/protocol.yaml",
        "algorithm: crc_16_ccitt_false",
        "bytes: [0xA5, 0x5A]",
    ]
    for marker in required_markers:
        if marker not in contract:
            errors.append(f"Protocol marker missing: {marker}")

    ids = re.findall(r"^\s{4}id:\s*(0x[0-9A-Fa-f]+|\d+)\s*$", contract, re.MULTILINE)
    if len(ids) != len(set(ids)):
        errors.append("duplicate message IDs in protocol.yaml")

    payload = json.loads(VECTORS.read_text(encoding="utf-8"))
    if payload.get("wire_version") != 1:
        errors.append("vector wire_version shall be 1")

    for vector in payload.get("vectors", []):
        try:
            frame = bytes.fromhex(vector["frame_hex"])
            declared_payload = bytes.fromhex(vector["payload_hex"])
        except (KeyError, ValueError) as exc:
            errors.append(f"invalid vector encoding: {vector.get('name', '<unnamed>')}: {exc}")
            continue
        if len(frame) < 10 or frame[:2] != bytes((0xA5, 0x5A)):
            errors.append(f"invalid frame prefix/length: {vector['name']}")
            continue
        length = frame[6] | (frame[7] << 8)
        if length != len(declared_payload):
            errors.append(f"payload length mismatch: {vector['name']}")
        if frame[8:8+length] != declared_payload:
            errors.append(f"payload bytes mismatch: {vector['name']}")
        received_crc = frame[-2] | (frame[-1] << 8)
        calculated_crc = crc16_ccitt_false(frame[2:-2])
        if received_crc != calculated_crc:
            errors.append(f"CRC mismatch: {vector['name']}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        print(f"Protocol validation failed with {len(errors)} error(s).")
        return 1
    print("Protocol contract and vectors validated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
