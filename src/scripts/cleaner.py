"""cleanenv.py — Remove common Python/tooling cache & build artifacts from a project tree.

Usage:
    python cleanenv.py [PATH] [--dry-run] [--extra NAME ...] [--quiet]

Examples:
    python cleanenv.py                     # clean current directory
    python cleanenv.py ~/projects/myapp    # clean a specific project
    python cleanenv.py --dry-run           # preview only, delete nothing
    python cleanenv.py --extra .idea .DS_Store
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# Directory names to remove wherever found (recursively)
DIR_TARGETS: set[str] = {
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".coverage_html",
    "build",
    "dist",
    ".cache",
}

# File name patterns to remove wherever found
FILE_TARGETS: set[str] = {
    "*.pyc",
    "*.pyo",
    ".coverage",
}


def iter_targets(root: Path, extra_dirs: list[str]) -> list[Path]:
    """Collect every matching file/dir under root, deepest paths first."""
    names = DIR_TARGETS | set(extra_dirs)
    found: set[Path] = set()

    for pattern in names:
        if "*" in pattern:
            found.update(root.rglob(pattern))
        else:
            found.update(p for p in root.rglob(pattern) if p.is_dir())

    for pattern in FILE_TARGETS:
        found.update(p for p in root.rglob(pattern) if p.is_file())

    # Sort deepest-first so nested paths are removed before their parents
    return sorted(found, key=lambda p: len(p.parts), reverse=True)


def human_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return sum(f.stat().st_size for f in path.rglob("*") if f.is_file())


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Clean Python/tooling cache artifacts.",
    )
    parser.add_argument("path", nargs="?", default=".", help="Root directory to clean")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be removed"
    )
    parser.add_argument(
        "--extra", nargs="*", default=[], help="Extra dir names to remove"
    )
    parser.add_argument("--quiet", action="store_true", help="Only print a summary")
    args = parser.parse_args()

    root = Path(args.path).resolve()
    if not root.exists():
        print(f"Path not found: {root}", file=sys.stderr)
        return 1

    targets = iter_targets(root, args.extra)
    if not targets:
        print("Nothing to clean.")
        return 0

    total_bytes = 0
    for p in targets:
        size = human_size(p)
        total_bytes += size
        if not args.quiet:
            action = "[dry-run] would remove" if args.dry_run else "removing"
            print(f"{action}: {p}  ({size / 1024:.1f} KB)")

        if not args.dry_run:
            if p.is_dir():
                shutil.rmtree(p, ignore_errors=True)
            else:
                p.unlink(missing_ok=True)

    verb = "Would free" if args.dry_run else "Freed"
    print(
        f"\n{verb} {total_bytes / (1024 * 1024):.2f} MB across {len(targets)} item(s)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
