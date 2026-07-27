#!/usr/bin/env python3
"""Regression tests for the PoC project repository validator."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = Path("tools/validate_project_repository.py")


def ignore_transient(_directory: str, names: list[str]) -> set[str]:
    ignored = {".git", "__pycache__", ".pytest_cache", ".mypy_cache"}
    return {name for name in names if name in ignored or name.endswith(".pyc")}


class ProjectRepositoryValidatorTests(unittest.TestCase):
    def make_repo(self) -> tuple[tempfile.TemporaryDirectory[str], Path]:
        holder: tempfile.TemporaryDirectory[str] = tempfile.TemporaryDirectory()
        target = Path(holder.name) / "repo"
        shutil.copytree(ROOT, target, ignore=ignore_transient)
        return holder, target

    def run_validator(self, target: Path) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(VALIDATOR)],
            cwd=target,
            text=True,
            capture_output=True,
            check=False,
        )

    @staticmethod
    def set_release(target: Path, version: str, status: str, cycle_status: str) -> None:
        readme_path = target / "README.md"
        readme = readme_path.read_text(encoding="utf-8")
        readme = __import__("re").sub(r"- Candidate version: `[^`]+`", f"- Candidate version: `{version}`", readme, count=1)
        readme = __import__("re").sub(r"- Lifecycle status: `[^`]+`", f"- Lifecycle status: `{status}`", readme, count=1)
        readme_path.write_text(readme, encoding="utf-8", newline="\n")

        changelog_path = target / "CHANGELOG.md"
        changelog = changelog_path.read_text(encoding="utf-8")
        changelog = __import__("re").sub(
            r"^(## )[^ ]+( — \d{4}-\d{2}-\d{2} — )[^\n]+",
            rf"\g<1>{version}\g<2>{status}",
            changelog,
            count=1,
            flags=__import__("re").MULTILINE,
        )
        changelog_path.write_text(changelog, encoding="utf-8", newline="\n")

        baseline_path = target / "baselines/repositories.yaml"
        data = yaml.safe_load(baseline_path.read_text(encoding="utf-8"))
        data["alignment_cycles"][-1]["candidate_version"] = version
        data["alignment_cycles"][-1]["status"] = cycle_status
        baseline_path.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True), encoding="utf-8", newline="\n")

    def test_current_repository_passes(self) -> None:
        result = self.run_validator(ROOT)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_missing_work_continuation_is_rejected(self) -> None:
        holder, target = self.make_repo()
        with holder:
            (target / "WORK_CONTINUATION.md").unlink()
            result = self.run_validator(target)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing required file: WORK_CONTINUATION.md", result.stdout)

    def test_missing_gitattributes_is_rejected(self) -> None:
        holder, target = self.make_repo()
        with holder:
            (target / ".gitattributes").unlink()
            result = self.run_validator(target)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("missing required file: .gitattributes", result.stdout)

    def test_canonical_lf_rule_is_required(self) -> None:
        holder, target = self.make_repo()
        with holder:
            path = target / ".gitattributes"
            text = path.read_text(encoding="utf-8").replace("* text=auto eol=lf", "* text=auto")
            path.write_text(text, encoding="utf-8", newline="\n")
            result = self.run_validator(target)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(".gitattributes shall retain required rule: * text=auto eol=lf", result.stdout)

    def test_release_candidate_cannot_be_baseline(self) -> None:
        holder, target = self.make_repo()
        with holder:
            self.set_release(target, "v0.2.0-rc.1", "Baseline", "baseline")
            result = self.run_validator(target)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("release-candidate versions shall remain Draft for Review", result.stdout)

    def test_formal_version_cannot_remain_draft(self) -> None:
        holder, target = self.make_repo()
        with holder:
            self.set_release(target, "v0.2.0", "Draft for Review", "draft_for_review")
            result = self.run_validator(target)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("formal semantic version shall not remain Draft for Review", result.stdout)

    def test_multi_digit_semantic_version_is_allowed(self) -> None:
        holder, target = self.make_repo()
        with holder:
            self.set_release(target, "v0.12.34-rc.12", "Draft for Review", "draft_for_review")
            result = self.run_validator(target)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_changelog_version_drift_is_rejected(self) -> None:
        holder, target = self.make_repo()
        with holder:
            changelog_path = target / "CHANGELOG.md"
            text = __import__("re").sub(
                r"^(## )[^ ]+( — \d{4}-\d{2}-\d{2} — )",
                r"\g<1>v9.9.9-rc.1\g<2>",
                changelog_path.read_text(encoding="utf-8"),
                count=1,
                flags=__import__("re").MULTILINE,
            )
            changelog_path.write_text(text, encoding="utf-8", newline="\n")
            result = self.run_validator(target)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("README.md and CHANGELOG.md release version/status shall match", result.stdout)

    def test_handoff_non_authority_boundary_is_required(self) -> None:
        holder, target = self.make_repo()
        with holder:
            path = target / "WORK_CONTINUATION.md"
            text = path.read_text(encoding="utf-8").replace(
                "It does not grant approval, does not create V&V evidence, does not accept risk, does not authorize release, and does not establish Framework conformance.",
                "This is a working record.",
                1,
            )
            path.write_text(text, encoding="utf-8", newline="\n")
            result = self.run_validator(target)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("explicit non-authority boundary", result.stdout)

    def test_crlf_is_rejected(self) -> None:
        holder, target = self.make_repo()
        with holder:
            path = target / "CONTRIBUTING.md"
            text = path.read_text(encoding="utf-8")
            path.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
            result = self.run_validator(target)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("CR or CRLF line ending is prohibited: CONTRIBUTING.md", result.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
