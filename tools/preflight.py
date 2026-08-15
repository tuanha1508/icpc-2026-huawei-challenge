#!/usr/bin/env python3
"""Check whether the local machine and repository are ready for contest work."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--min-free-gib", type=float, default=10.0)
    parser.add_argument("--warn-free-gib", type=float, default=20.0)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args()
    if args.min_free_gib < 0 or args.warn_free_gib < args.min_free_gib:
        parser.error("require 0 <= --min-free-gib <= --warn-free-gib")
    return args


def command_output(command: list[str], cwd: Path) -> str | None:
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def add(checks: list[dict[str, object]], name: str, status: str, detail: str) -> None:
    checks.append({"name": name, "status": status, "detail": detail})


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    command_cwd = root if root.is_dir() else ROOT
    checks: list[dict[str, object]] = []

    for name, version_command in [
        ("c++", ["c++", "--version"]),
        ("cmake", ["cmake", "--version"]),
        ("python3", ["python3", "--version"]),
        ("git", ["git", "--version"]),
    ]:
        executable = shutil.which(name)
        if executable is None:
            add(checks, f"tool:{name}", "error", "not found on PATH")
            continue
        version = command_output(version_command, command_cwd)
        first_line = version.splitlines()[0] if version else "version unavailable"
        add(checks, f"tool:{name}", "ok", f"{executable}: {first_line}")

    if not root.is_dir():
        add(checks, "workspace", "error", f"missing directory: {root}")
    else:
        add(checks, "workspace", "ok", str(root))
        usage = shutil.disk_usage(root)
        free_gib = usage.free / (1024**3)
        free_percent = 100.0 * usage.free / usage.total
        detail = f"{free_gib:.2f} GiB free ({free_percent:.1f}%)"
        if free_gib < args.min_free_gib:
            add(checks, "disk", "error", detail)
        elif free_gib < args.warn_free_gib:
            add(checks, "disk", "warn", detail)
        else:
            add(checks, "disk", "ok", detail)

    commit = command_output(["git", "rev-parse", "HEAD"], root) if root.is_dir() else None
    branch = (
        command_output(["git", "branch", "--show-current"], root)
        if root.is_dir()
        else None
    )
    status = (
        command_output(["git", "status", "--porcelain"], root)
        if root.is_dir()
        else None
    )
    if commit is None:
        add(checks, "git-repository", "error", "not a Git worktree")
    else:
        add(checks, "git-repository", "ok", f"{branch or '(detached)'} {commit}")
        if status:
            changed = len(status.splitlines())
            add(checks, "git-worktree", "warn", f"{changed} changed/untracked entries")
        else:
            add(checks, "git-worktree", "ok", "clean")

    local_now = datetime.now().astimezone()
    report = {
        "checked_utc": datetime.now(timezone.utc).isoformat(),
        "local_time": local_now.isoformat(),
        "timezone": str(local_now.tzinfo),
        "root": str(root),
        "checks": checks,
    }
    if args.as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"UTC:   {report['checked_utc']}")
        print(f"Local: {report['local_time']} ({report['timezone']})")
        for check in checks:
            print(f"{str(check['status']).upper():5} {check['name']}: {check['detail']}")

    return 1 if any(check["status"] == "error" for check in checks) else 0


if __name__ == "__main__":
    raise SystemExit(main())
