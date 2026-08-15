#!/usr/bin/env python3
"""Run a solver repeatedly over input files and append reproducible timing data."""

from __future__ import annotations

import argparse
import csv
import hashlib
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path


FIELDS = [
    "timestamp_utc",
    "case",
    "run",
    "wall_ms",
    "exit_code",
    "timed_out",
    "output_bytes",
    "output_sha256",
    "solver",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--solver", required=True, type=Path)
    parser.add_argument("--inputs", required=True, type=Path)
    parser.add_argument("--outputs", required=True, type=Path)
    parser.add_argument("--runs", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--log", type=Path, default=Path("experiments/runs.csv"))
    parser.add_argument("--pattern", default="*")
    args = parser.parse_args()
    if args.runs < 1:
        parser.error("--runs must be at least 1")
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    return args


def append_row(path: Path, row: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    needs_header = not path.exists() or path.stat().st_size == 0
    with path.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        if needs_header:
            writer.writeheader()
        writer.writerow(row)


def run_case(
    solver: Path, input_path: Path, output_path: Path, timeout: float
) -> tuple[int, bool, float, bytes]:
    started = time.perf_counter()
    timed_out = False
    exit_code = 0
    output = b""
    with input_path.open("rb") as input_handle:
        try:
            completed = subprocess.run(
                [str(solver)],
                stdin=input_handle,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout,
                check=False,
            )
            exit_code = completed.returncode
            output = completed.stdout
            if completed.stderr:
                print(
                    f"[{input_path.name}] stderr: "
                    f"{completed.stderr.decode(errors='replace').rstrip()}"
                )
        except subprocess.TimeoutExpired as error:
            timed_out = True
            exit_code = -1
            output = error.stdout or b""
    wall_ms = (time.perf_counter() - started) * 1000.0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(output)
    return exit_code, timed_out, wall_ms, output


def main() -> int:
    args = parse_args()
    solver = args.solver.resolve()
    if not solver.is_file():
        raise SystemExit(f"solver does not exist: {solver}")
    if not args.inputs.is_dir():
        raise SystemExit(f"input directory does not exist: {args.inputs}")
    cases = sorted(path for path in args.inputs.glob(args.pattern) if path.is_file())
    if not cases:
        raise SystemExit("no input files matched")

    for input_path in cases:
        for run_number in range(1, args.runs + 1):
            output_path = args.outputs / f"{input_path.name}.run-{run_number}.out"
            exit_code, timed_out, wall_ms, output = run_case(
                solver, input_path, output_path, args.timeout
            )
            digest = hashlib.sha256(output).hexdigest()
            append_row(
                args.log,
                {
                    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                    "case": input_path.name,
                    "run": run_number,
                    "wall_ms": f"{wall_ms:.3f}",
                    "exit_code": exit_code,
                    "timed_out": int(timed_out),
                    "output_bytes": len(output),
                    "output_sha256": digest,
                    "solver": str(solver),
                },
            )
            print(
                f"{input_path.name} run={run_number} wall_ms={wall_ms:.3f} "
                f"exit={exit_code} timeout={timed_out} bytes={len(output)}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

