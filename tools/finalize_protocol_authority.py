#!/usr/bin/env python3
"""Pin the current committed Protocol blob after an authority-changing commit."""

from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from pathlib import Path

import yaml


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Repository root.",
    )
    return parser.parse_args()


def run_git(root: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or f"git {' '.join(args)} failed")
    return result.stdout.strip()


def replace_once(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.MULTILINE)
    if count != 1:
        raise RuntimeError(f"unable to update {label}")
    return updated


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    try:
        if run_git(root, "rev-parse", "--is-inside-work-tree") != "true":
            raise RuntimeError("root is not a Git work tree")
        if run_git(root, "status", "--porcelain"):
            raise RuntimeError("work tree shall be clean; commit the Protocol correction before finalizing provenance")
        authority_commit = run_git(root, "rev-parse", "HEAD")

        protocol_path = root / "protocol" / "protocol.yaml"
        protocol_bytes = protocol_path.read_bytes()
        protocol_doc = yaml.safe_load(protocol_bytes)
        if not isinstance(protocol_doc, dict) or not isinstance(protocol_doc.get("protocol"), dict):
            raise RuntimeError("protocol/protocol.yaml is not a valid Protocol mapping")
        protocol = protocol_doc["protocol"]
        version = protocol.get("version")
        wire_version = protocol.get("wire_version")
        status = protocol.get("status")
        if not isinstance(version, str) or not isinstance(wire_version, int) or not isinstance(status, str):
            raise RuntimeError("Protocol version, wire_version, or status is invalid")
        digest = hashlib.sha256(protocol_bytes).hexdigest()

        baseline_path = root / "baselines" / "repositories.yaml"
        baseline = baseline_path.read_text(encoding="utf-8")
        baseline = replace_once(
            baseline,
            r"^(\s*repository_commit:\s*)[0-9a-f]{40}\s*$",
            rf"\g<1>{authority_commit}",
            "baseline authority repository_commit",
        )
        baseline = replace_once(
            baseline,
            r"^(\s*file_sha256:\s*)[0-9a-f]{64}\s*$",
            rf"\g<1>{digest}",
            "baseline authority file_sha256",
        )
        baseline = replace_once(
            baseline,
            r"^(\s*protocol_version:\s*).+$",
            rf"\g<1>{version}",
            "baseline protocol_version",
        )
        baseline = replace_once(
            baseline,
            r"^(\s*wire_version:\s*).+$",
            rf"\g<1>0x{wire_version:02X}",
            "baseline wire_version",
        )
        baseline_path.write_text(baseline, encoding="utf-8")

        status_path = root / "protocol" / "implementation-status.yaml"
        status_text = status_path.read_text(encoding="utf-8")
        status_text = replace_once(
            status_text,
            r"^(\s*system_repository_commit:\s*)[0-9a-f]{40}\s*$",
            rf"\g<1>{authority_commit}",
            "implementation status system_repository_commit",
        )
        status_text = replace_once(
            status_text,
            r"^(\s*version:\s*).+$",
            rf"\g<1>{version}",
            "implementation status version",
        )
        status_text = replace_once(
            status_text,
            r"^(\s*wire_version:\s*).+$",
            rf"\g<1>0x{wire_version:02X}",
            "implementation status wire_version",
        )
        status_text = replace_once(
            status_text,
            r"^(\s*status:\s*).+$",
            rf"\g<1>{status}",
            "implementation status lifecycle state",
        )
        status_text = replace_once(
            status_text,
            r"^(\s*sha256:\s*)[0-9a-f]{64}\s*$",
            rf"\g<1>{digest}",
            "implementation status sha256",
        )
        status_path.write_text(status_text, encoding="utf-8")
    except (OSError, RuntimeError, subprocess.SubprocessError, yaml.YAMLError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Pinned Protocol authority commit: {authority_commit}")
    print(f"Pinned Protocol SHA-256: {digest}")
    print("Review the two modified provenance files, run validation, and commit them as a second commit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
