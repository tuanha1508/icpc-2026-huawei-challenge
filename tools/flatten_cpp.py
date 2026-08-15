#!/usr/bin/env python3
"""Expand project-local quoted C++ includes into one submission source file."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


LOCAL_INCLUDE = re.compile(r'^\s*#\s*include\s+"([^"]+)"\s*$')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--include-dir", action="append", type=Path, default=[], dest="include_dirs"
    )
    return parser.parse_args()


def resolve_include(name: str, parent: Path, include_dirs: list[Path]) -> Path:
    candidates = [parent / name, *(directory / name for directory in include_dirs)]
    for candidate in candidates:
        if candidate.is_file():
            return candidate.resolve()
    raise FileNotFoundError(f'cannot resolve local include "{name}" from {parent}')


def expand(path: Path, include_dirs: list[Path], seen: set[Path]) -> list[str]:
    resolved = path.resolve()
    if resolved in seen:
        return [f"// Local include already expanded: {resolved.name}\n"]
    seen.add(resolved)

    result = [f"// BEGIN LOCAL FILE: {resolved.name}\n"]
    for line in resolved.read_text(encoding="utf-8").splitlines(keepends=True):
        if line.strip() == "#pragma once":
            continue
        match = LOCAL_INCLUDE.match(line.rstrip("\r\n"))
        if match:
            included = resolve_include(match.group(1), resolved.parent, include_dirs)
            result.extend(expand(included, include_dirs, seen))
        else:
            result.append(line if line.endswith("\n") else line + "\n")
    result.append(f"// END LOCAL FILE: {resolved.name}\n")
    return result


def flatten(source: Path, include_dirs: list[Path]) -> str:
    if not source.is_file():
        raise FileNotFoundError(f"source does not exist: {source}")
    directories = [directory.resolve() for directory in include_dirs]
    return "".join(expand(source, directories, set()))


def main() -> int:
    args = parse_args()
    content = flatten(args.source, args.include_dirs)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(content, encoding="utf-8")
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

