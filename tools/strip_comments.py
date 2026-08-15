#!/usr/bin/env python3
"""Strip C++ comments for submission. Codeforces caps source at 65535 bytes.

The solver carries heavy explanatory comments (they are the record of what was
measured and why), which pushed it to 66408 bytes. This removes comments only --
never code -- so the compiled behaviour is identical. String and character
literals are tracked so that a // or /* inside one is preserved.

Usage: python3 tools/strip_comments.py src/main.cpp out.cpp
"""
from __future__ import annotations
import sys


def strip(src: str) -> str:
    out = []
    i, n = 0, len(src)
    while i < n:
        c = src[i]
        # string literal
        if c == '"':
            out.append(c)
            i += 1
            while i < n:
                if src[i] == '\\':
                    out.append(src[i:i + 2])
                    i += 2
                    continue
                out.append(src[i])
                if src[i] == '"':
                    i += 1
                    break
                i += 1
            continue
        # character literal
        if c == "'":
            out.append(c)
            i += 1
            while i < n:
                if src[i] == '\\':
                    out.append(src[i:i + 2])
                    i += 2
                    continue
                out.append(src[i])
                if src[i] == "'":
                    i += 1
                    break
                i += 1
            continue
        # line comment
        if c == '/' and i + 1 < n and src[i + 1] == '/':
            while i < n and src[i] != '\n':
                i += 1
            continue
        # block comment
        if c == '/' and i + 1 < n and src[i + 1] == '*':
            i += 2
            while i + 1 < n and not (src[i] == '*' and src[i + 1] == '/'):
                i += 1
            i += 2
            continue
        out.append(c)
        i += 1
    # drop lines that became blank, keep preprocessor structure intact
    lines = "".join(out).split('\n')
    keep = [ln.rstrip() for ln in lines]
    res = []
    for ln in keep:
        if ln.strip() == '' and (not res or res[-1].strip() == ''):
            continue
        res.append(ln)
    return '\n'.join(res) + '\n'


if __name__ == '__main__':
    src = open(sys.argv[1]).read()
    dst = strip(src)
    open(sys.argv[2], 'w').write(dst)
    print(f"{sys.argv[1]}: {len(src)} bytes -> {sys.argv[2]}: {len(dst)} bytes "
          f"({100*(1-len(dst)/len(src)):.1f}% smaller)")
    if len(dst) >= 65535:
        print(f"  WARNING: still over the 65535 limit by {len(dst)-65534}")
    else:
        print(f"  under the 65535 limit with {65535-len(dst)} bytes to spare")
