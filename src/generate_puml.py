#!/usr/bin/env python3
"""Thin CLI shim delegating to `uml_planterator.generator.PUMLGenerator`.

This module preserves a simple command-line interface but delegates
parsing, rendering and writing to the modular package so logic is fully
testable and maintainable.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from uml_planterator.generator import PUMLGenerator


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Generate PlantUML diagrams from a Python source tree."
    )
    parser.add_argument("--src", default="src")
    parser.add_argument("--out", default="docs/UML/Source")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    src_root = Path(args.src)
    out_root = Path(args.out)
    gen = PUMLGenerator(src_root=src_root, out_root=out_root, verbose=args.verbose)
    res = gen.run(dry_run=args.dry_run)
    counts = res.get("counts", {})
    total = sum(counts.values())
    print(f"Generated {total} .puml files (dry-run={args.dry_run})")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
