#!/usr/bin/env python3
"""Execute a deterministic grid of solver commands over a fixed input set."""

from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


FIELDS = [
    "timestamp_utc",
    "candidate",
    "parameters_json",
    "case",
    "wall_ms",
    "exit_code",
    "timed_out",
    "output_bytes",
    "output_sha256",
    "score",
    "scorer_exit_code",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--inputs", required=True, type=Path)
    parser.add_argument("--outputs", required=True, type=Path)
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--pattern", default="*")
    args = parser.parse_args()
    if args.jobs < 1:
        parser.error("--jobs must be at least 1")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    return args


def load_config(path: Path) -> dict[str, Any]:
    config = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(config.get("command"), list) or not config["command"]:
        raise ValueError("config.command must be a non-empty JSON list")
    grid = config.get("grid", {})
    if not isinstance(grid, dict) or any(not isinstance(v, list) or not v for v in grid.values()):
        raise ValueError("config.grid values must be non-empty JSON lists")
    if "scorer" in config and not isinstance(config["scorer"], list):
        raise ValueError("config.scorer must be a JSON list")
    return config


def combinations(grid: dict[str, list[Any]]) -> list[dict[str, Any]]:
    keys = sorted(grid)
    return [
        dict(zip(keys, values, strict=True))
        for values in itertools.product(*(grid[key] for key in keys))
    ] or [{}]


def format_command(template: list[Any], values: dict[str, Any]) -> list[str]:
    return [str(part).format_map(values) for part in template]


def run_one(
    command_template: list[Any],
    scorer_template: list[Any] | None,
    parameters: dict[str, Any],
    candidate: str,
    input_path: Path,
    output_path: Path,
    timeout: float,
) -> dict[str, object]:
    values = {**parameters, "input": str(input_path), "output": str(output_path)}
    command = format_command(command_template, values)
    started = time.perf_counter()
    timed_out = False
    exit_code = 0
    output = b""
    with input_path.open("rb") as input_handle:
        try:
            completed = subprocess.run(
                command,
                stdin=input_handle,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                check=False,
            )
            exit_code = completed.returncode
            output = completed.stdout
        except subprocess.TimeoutExpired as error:
            timed_out = True
            exit_code = -1
            output = error.stdout or b""
    wall_ms = (time.perf_counter() - started) * 1000.0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(output)

    score = ""
    scorer_exit_code: int | str = ""
    if exit_code == 0 and not timed_out and scorer_template:
        try:
            scorer = subprocess.run(
                format_command(scorer_template, values),
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            scorer_exit_code = scorer.returncode
            if scorer.returncode == 0:
                score = scorer.stdout.strip()
        except subprocess.TimeoutExpired:
            scorer_exit_code = -1

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "candidate": candidate,
        "parameters_json": json.dumps(parameters, sort_keys=True, separators=(",", ":")),
        "case": input_path.name,
        "wall_ms": f"{wall_ms:.3f}",
        "exit_code": exit_code,
        "timed_out": int(timed_out),
        "output_bytes": len(output),
        "output_sha256": hashlib.sha256(output).hexdigest(),
        "score": score,
        "scorer_exit_code": scorer_exit_code,
    }


def main() -> int:
    args = parse_args()
    config = load_config(args.config)
    cases = sorted(path.resolve() for path in args.inputs.glob(args.pattern) if path.is_file())
    if not cases:
        raise SystemExit("no input files matched")
    parameter_sets = combinations(config.get("grid", {}))

    tasks = []
    for index, parameters in enumerate(parameter_sets):
        candidate = f"candidate-{index:04d}"
        for input_path in cases:
            output_path = args.outputs / candidate / f"{input_path.name}.out"
            tasks.append((parameters, candidate, input_path, output_path))

    rows: list[dict[str, object]] = []
    with ThreadPoolExecutor(max_workers=args.jobs) as executor:
        futures = [
            executor.submit(
                run_one,
                config["command"],
                config.get("scorer"),
                parameters,
                candidate,
                input_path,
                output_path,
                args.timeout,
            )
            for parameters, candidate, input_path, output_path in tasks
        ]
        for future in as_completed(futures):
            row = future.result()
            rows.append(row)
            print(
                f"{row['candidate']} {row['case']} wall_ms={row['wall_ms']} "
                f"exit={row['exit_code']} score={row['score']}"
            )

    rows.sort(key=lambda row: (str(row["candidate"]), str(row["case"])))
    args.log.parent.mkdir(parents=True, exist_ok=True)
    with args.log.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
