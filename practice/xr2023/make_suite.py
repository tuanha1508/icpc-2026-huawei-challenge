#!/usr/bin/env python3
"""Create deterministic XR tuning, held-out, and stress suites with hashes."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--generator", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def cases() -> list[dict[str, int | str]]:
    result: list[dict[str, int | str]] = []
    for seed in range(1, 13):
        result.append(
            {
                "suite": "tuning",
                "seed": seed,
                "profile": ["mixed", "burst", "tight", "interference"][seed % 4],
                "users": 12,
                "cells": 3,
                "ttis": 40,
                "rbgs": 4,
                "frames": 55,
            }
        )
    heldout_shapes = [
        (6, 1, 25, 2, 25),
        (20, 4, 60, 5, 100),
        (30, 2, 80, 8, 130),
        (10, 6, 50, 3, 75),
    ]
    profiles = ["mixed", "burst", "tight", "interference"]
    for offset in range(12):
        users, cells, ttis, rbgs, frames = heldout_shapes[offset % len(heldout_shapes)]
        result.append(
            {
                "suite": "heldout",
                "seed": 1001 + offset,
                "profile": profiles[offset % len(profiles)],
                "users": users,
                "cells": cells,
                "ttis": ttis,
                "rbgs": rbgs,
                "frames": frames,
            }
        )
    stress_shapes = [
        (100, 10, 200, 10, 800, "mixed"),
        (80, 8, 250, 8, 1000, "burst"),
        (60, 10, 300, 10, 900, "tight"),
        (100, 6, 200, 10, 750, "interference"),
    ]
    for offset, shape in enumerate(stress_shapes):
        users, cells, ttis, rbgs, frames, profile = shape
        result.append(
            {
                "suite": "stress",
                "seed": 9001 + offset,
                "profile": profile,
                "users": users,
                "cells": cells,
                "ttis": ttis,
                "rbgs": rbgs,
                "frames": frames,
            }
        )
    return result


def main() -> int:
    args = parse_args()
    generator = args.generator.resolve()
    if not generator.is_file():
        raise SystemExit(f"generator does not exist: {generator}")
    manifest = []
    for index, specification in enumerate(cases()):
        suite = str(specification["suite"])
        name = f"{index:03d}-{specification['profile']}-s{specification['seed']}.in"
        path = args.output / suite / name
        path.parent.mkdir(parents=True, exist_ok=True)
        command = [str(generator)]
        for key in ["seed", "profile", "users", "cells", "ttis", "rbgs", "frames"]:
            command.extend([f"--{key}", str(specification[key])])
        completed = subprocess.run(command, capture_output=True, check=True)
        path.write_bytes(completed.stdout)
        manifest.append(
            {
                **specification,
                "path": str(path.relative_to(args.output)),
                "bytes": len(completed.stdout),
                "sha256": hashlib.sha256(completed.stdout).hexdigest(),
            }
        )
        print(path)
    (args.output / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
