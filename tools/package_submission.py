#!/usr/bin/env python3
"""Create a non-overwriting, hashed snapshot of a C++ submission."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from flatten_cpp import flatten


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("artifacts/submissions"))
    parser.add_argument("--label", default="candidate")
    parser.add_argument(
        "--include-dir", action="append", type=Path, default=[], dest="include_dirs"
    )
    parser.add_argument("--parameters", default="{}", help="JSON object")
    return parser.parse_args()


def git_value(arguments: list[str]) -> str | None:
    completed = subprocess.run(
        ["git", *arguments], capture_output=True, text=True, check=False
    )
    return completed.stdout.strip() if completed.returncode == 0 else None


def main() -> int:
    args = parse_args()
    parameters = json.loads(args.parameters)
    if not isinstance(parameters, dict):
        raise SystemExit("--parameters must be a JSON object")

    label = re.sub(r"[^A-Za-z0-9_.-]+", "-", args.label).strip("-.")
    if not label:
        raise SystemExit("--label must contain a safe filename character")
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    package = args.output_dir / f"{timestamp}-{label}"
    package.mkdir(parents=True, exist_ok=False)

    content = flatten(args.source, args.include_dirs)
    source_bytes = content.encode("utf-8")
    digest = hashlib.sha256(source_bytes).hexdigest()
    submission = package / "submission.cpp"
    submission.write_bytes(source_bytes)

    status = git_value(["status", "--porcelain"])
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "label": label,
        "source": str(args.source.resolve()),
        "submission": submission.name,
        "sha256": digest,
        "bytes": len(source_bytes),
        "git_commit": git_value(["rev-parse", "HEAD"]),
        "git_dirty": bool(status),
        "parameters": parameters,
    }
    (package / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(package)
    print(digest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

