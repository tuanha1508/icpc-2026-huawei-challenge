#!/usr/bin/env python3
"""Create a stable, duplicate-safe tuning/held-out case manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inputs", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--seed", default="contest-v1")
    parser.add_argument("--heldout-percent", type=int, default=25)
    parser.add_argument("--pattern", default="*")
    parser.add_argument("--recursive", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.heldout_percent <= 99:
        parser.error("--heldout-percent must be between 1 and 99")
    return args


def file_digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            hasher.update(block)
    return hasher.hexdigest()


def assignment_digest(seed: str, content_digest: str) -> str:
    return hashlib.sha256(f"{seed}\0{content_digest}".encode()).hexdigest()


def main() -> int:
    args = parse_args()
    inputs = args.inputs.resolve()
    output = args.output.resolve()
    if not inputs.is_dir():
        raise SystemExit(f"input directory does not exist: {inputs}")
    iterator = inputs.rglob(args.pattern) if args.recursive else inputs.glob(args.pattern)
    paths = sorted(
        path for path in iterator if path.is_file() and path.resolve() != output
    )
    if len(paths) < 2:
        raise SystemExit("at least two cases are required")

    groups: dict[str, list[Path]] = defaultdict(list)
    for path in paths:
        groups[file_digest(path)].append(path)
    if len(groups) < 2:
        raise SystemExit("at least two distinct case contents are required")

    ranks = {
        digest: assignment_digest(args.seed, digest) for digest in sorted(groups)
    }
    split_by_digest = {
        digest: "heldout"
        if int(rank[:16], 16) % 100 < args.heldout_percent
        else "tuning"
        for digest, rank in ranks.items()
    }
    if "heldout" not in split_by_digest.values():
        split_by_digest[min(ranks, key=ranks.get)] = "heldout"
    if "tuning" not in split_by_digest.values():
        split_by_digest[max(ranks, key=ranks.get)] = "tuning"

    cases = []
    corpus_hasher = hashlib.sha256()
    for digest, grouped_paths in sorted(groups.items()):
        for path in sorted(grouped_paths):
            relative = path.relative_to(inputs).as_posix()
            corpus_hasher.update(relative.encode())
            corpus_hasher.update(b"\0")
            corpus_hasher.update(digest.encode())
            corpus_hasher.update(b"\n")
            cases.append(
                {
                    "path": relative,
                    "bytes": path.stat().st_size,
                    "sha256": digest,
                    "split": split_by_digest[digest],
                }
            )

    manifest = {
        "version": 1,
        "root": str(inputs),
        "seed": args.seed,
        "heldout_percent": args.heldout_percent,
        "corpus_sha256": corpus_hasher.hexdigest(),
        "counts": {
            "total": len(cases),
            "tuning": sum(case["split"] == "tuning" for case in cases),
            "heldout": sum(case["split"] == "heldout" for case in cases),
        },
        "cases": sorted(cases, key=lambda case: str(case["path"])),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(
        f"split {len(cases)} cases: {manifest['counts']['tuning']} tuning, "
        f"{manifest['counts']['heldout']} held-out -> {output}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
