#!/usr/bin/env python3
"""Run the repository's complete, repeatable local verification ladder."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--quick",
        action="store_true",
        help="skip the sanitizer build and tests",
    )
    return parser.parse_args()


def run(label: str, command: list[str]) -> bool:
    print(f"\n[{label}] {' '.join(command)}", flush=True)
    completed = subprocess.run(command, cwd=ROOT, check=False)
    if completed.returncode != 0:
        print(f"FAILED: {label} (exit {completed.returncode})", file=sys.stderr)
        return False
    return True


def check_repository_text() -> bool:
    print("\n[repository text] trailing whitespace and final newlines", flush=True)
    listed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if listed.returncode != 0:
        print("FAILED: could not enumerate repository files", file=sys.stderr)
        return False
    failed = False
    for relative_bytes in listed.stdout.split(b"\0"):
        if not relative_bytes:
            continue
        path = ROOT / relative_bytes.decode("utf-8")
        try:
            content = path.read_bytes()
        except OSError as error:
            print(f"{path}: {error}", file=sys.stderr)
            failed = True
            continue
        if b"\0" in content:
            continue
        for line_number, line in enumerate(content.splitlines(), start=1):
            if line.endswith((b" ", b"\t")):
                print(f"{path.relative_to(ROOT)}:{line_number}: trailing whitespace")
                failed = True
        if content and not content.endswith(b"\n"):
            print(f"{path.relative_to(ROOT)}: missing final newline")
            failed = True
    return not failed


def main() -> int:
    args = parse_args()
    steps: list[tuple[str, list[str]]] = [
        ("configure release", ["cmake", "--preset", "release"]),
        ("build release", ["cmake", "--build", "--preset", "release", "-j"]),
        (
            "test release",
            ["ctest", "--preset", "release", "--output-on-failure"],
        ),
    ]
    if not args.quick:
        steps.extend(
            [
                ("configure sanitizers", ["cmake", "--preset", "sanitize"]),
                (
                    "build sanitizers",
                    ["cmake", "--build", "--preset", "sanitize", "-j"],
                ),
                (
                    "test sanitizers",
                    ["ctest", "--preset", "sanitize", "--output-on-failure"],
                ),
            ]
        )
    steps.extend(
        [
            (
                "Python tests",
                [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-v"],
            ),
            (
                "Python syntax",
                [
                    sys.executable,
                    "-m",
                    "py_compile",
                    *[str(path.relative_to(ROOT)) for path in sorted((ROOT / "tools").glob("*.py"))],
                    *[
                        str(path.relative_to(ROOT))
                        for path in sorted((ROOT / "practice" / "xr2023").glob("*.py"))
                    ],
                ],
            ),
        ]
    )
    for label, command in steps:
        if not run(label, command):
            return 1
    if not check_repository_text():
        return 1
    print("\nFoundation verification passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
