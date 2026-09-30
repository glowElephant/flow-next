#!/usr/bin/env python3
"""Idempotent, dedup-safe normalization of the Codex hooks feature flag.

Flow-Next ships no Codex hooks, so it never adds `hooks = true`. It only
repairs what older installs left behind: a config carrying BOTH `codex_hooks`
(written by older install-codex.sh) AND `hooks` ended up with a duplicate
`hooks` key after a naive sed migration, which is invalid TOML and breaks
Codex hook loading.

Rules (applied only inside the `[features]` table):
  - a `codex_hooks = ...` line (deprecated pre-2026 spelling) becomes
    `hooks = ...` with the same value when the table has no `hooks` key yet,
    and is dropped otherwise
  - keep the FIRST `hooks = ...` line, drop any later duplicates
  - never add a `hooks` key or a `[features]` table (an existing `hooks`
    may enable the user's own hooks, so it is never removed either)
Everything outside `[features]` is preserved byte-for-byte. Re-running is a
no-op once normalized (idempotent).

Usage:
    python3 normalize_codex_hooks.py <path/to/config.toml>
Exit 0 on success (writes in place only when content changed); exit 2 on a
missing path argument. A missing file stays missing.
"""
from __future__ import annotations

import re
import sys

# A section header like `[features]` or `[agents.foo]`. Leading whitespace tolerated.
_SECTION_RE = re.compile(r"^\s*\[(\[?[^\]]+\]?)\]\s*(?:#.*)?$")
_CODEX_HOOKS_RE = re.compile(r"^(\s*)codex_hooks(\s*=.*)$")
_HOOKS_RE = re.compile(r"^\s*hooks\s*=")


def normalize(text: str) -> str:
    if not text:
        return text
    lines = text.splitlines()
    out: list[str] = []
    in_features = False
    has_hooks = False

    # A table may hold `codex_hooks` before a later `hooks`; find which
    # [features] tables already carry the modern key so the rename never
    # creates a duplicate.
    modern: set[int] = set()
    table = -1
    for line in lines:
        m = _SECTION_RE.match(line)
        if m:
            table += 1
            in_features = m.group(1).strip() == "features"
            continue
        if in_features and _HOOKS_RE.match(line):
            modern.add(table)

    in_features = False
    table = -1
    for line in lines:
        m = _SECTION_RE.match(line)
        if m:
            table += 1
            in_features = m.group(1).strip() == "features"
            has_hooks = False
            out.append(line)
            continue

        if in_features:
            legacy = _CODEX_HOOKS_RE.match(line)
            if legacy:
                if table in modern or has_hooks:
                    continue
                # Keep the user's setting under its current name.
                line = f"{legacy.group(1)}hooks{legacy.group(2)}"
            if _HOOKS_RE.match(line):
                if has_hooks:
                    continue
                has_hooks = True

        out.append(line)

    return "\n".join(out).rstrip("\n") + "\n"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        sys.stderr.write("usage: normalize_codex_hooks.py <config.toml>\n")
        return 2
    path = argv[1]
    try:
        with open(path, "r", encoding="utf-8") as fh:
            original = fh.read()
    except FileNotFoundError:
        return 0
    updated = normalize(original)
    if updated != original:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(updated)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
