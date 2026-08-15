#!/usr/bin/env python3
"""Rank sweep candidates using an explicitly selected score aggregation rule."""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", required=True, type=Path)
    parser.add_argument(
        "--aggregate", required=True, choices=["sum", "mean", "min", "max"]
    )
    parser.add_argument(
        "--direction", required=True, choices=["maximize", "minimize"]
    )
    return parser.parse_args()


def aggregate(values: list[float], method: str) -> float:
    if method == "sum":
        return math.fsum(values)
    if method == "mean":
        return math.fsum(values) / len(values)
    if method == "min":
        return min(values)
    if method == "max":
        return max(values)
    raise ValueError(f"unknown aggregation method: {method}")


def main() -> int:
    args = parse_args()
    grouped: dict[tuple[str, str], list[float]] = defaultdict(list)
    invalid: set[tuple[str, str]] = set()
    with args.log.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            key = (row["candidate"], row["parameters_json"])
            if (
                row["exit_code"] != "0"
                or row["timed_out"] != "0"
                or row["scorer_exit_code"] != "0"
                or not row["score"].strip()
            ):
                invalid.add(key)
                continue
            try:
                grouped[key].append(float(row["score"]))
            except ValueError:
                invalid.add(key)

    ranked = [
        (aggregate(scores, args.aggregate), candidate, parameters, len(scores))
        for (candidate, parameters), scores in grouped.items()
        if (candidate, parameters) not in invalid
    ]
    ranked.sort(reverse=args.direction == "maximize")
    print("rank\tcandidate\taggregate\tcases\tparameters")
    for rank, (value, candidate, parameters, case_count) in enumerate(ranked, 1):
        print(f"{rank}\t{candidate}\t{value:.17g}\t{case_count}\t{parameters}")
    if invalid:
        print(f"excluded_invalid_candidates={len(invalid)}")
    return 0 if ranked else 2


if __name__ == "__main__":
    raise SystemExit(main())

