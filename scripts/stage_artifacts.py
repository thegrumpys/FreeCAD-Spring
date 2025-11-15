#!/usr/bin/env python3
"""Stage SpringCpp artefacts for the requested platform."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from typing import Iterable


def _discover_source(platform_root: Path) -> tuple[Path | None, list[Path]]:
    """Locate the SpringCpp build artefacts under *platform_root*.

    Returns a tuple containing the selected path (or ``None`` if not found)
    and the ordered list of candidate paths that were inspected.
    """

    expected = platform_root / "lib" / platform_root.name / "SpringCpp"
    candidates: list[Path] = [expected, expected.parent.parent / "SpringCpp"]

    for candidate in list(candidates):
        if candidate.is_dir():
            return candidate, candidates

    # Fall back to an exhaustive search when neither default layout is present.
    found = [path for path in platform_root.rglob("SpringCpp") if path.is_dir()]
    if found:
        found.sort(key=lambda p: (len(p.parts), "lib" not in p.parts))
        candidates.extend(found)
        return found[0], candidates

    return None, candidates


def _clear_destination(dest: Path, preserve: Iterable[str]) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    keep = set(preserve)
    for child in dest.iterdir():
        if child.name in keep:
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()


def _copy_tree(src: Path, dest: Path) -> int:
    count = 0
    for child in src.iterdir():
        target = dest / child.name
        if child.is_dir():
            shutil.copytree(child, target, dirs_exist_ok=True)
        else:
            shutil.copy2(child, target)
        count += 1
    return count


def stage(build_root: Path, platform: str) -> int:
    dest_map = {
        "linux": Path("lib/Linux/SpringCpp"),
        "linux-aarch64": Path("lib/Linux/SpringCpp"),
        "macos": Path("lib/Mac/SpringCpp"),
        "windows": Path("lib/Windows/SpringCpp"),
    }
    try:
        dest = dest_map[platform]
    except KeyError:  # pragma: no cover - defensive guard
        raise SystemExit(f"Unknown platform '{platform}'")

    platform_root = build_root / platform
    if not platform_root.is_dir():
        raise SystemExit(f"Missing build output root: {platform_root}")

    src, candidates = _discover_source(platform_root)
    if src is None:
        lines = "\n".join(f"  - {path}" for path in candidates)
        raise SystemExit(
            "Missing build output directory. Looked for:\n" f"{lines}"  # noqa: EM102
        )

    _clear_destination(dest, preserve=["__init__.py"])
    count = _copy_tree(src, dest)
    print(f"Staged {count} item(s) from {src} -> {dest}")
    return count


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("build_root", type=Path)
    parser.add_argument("platform")
    args = parser.parse_args(argv)

    stage(args.build_root, args.platform)
    return 0


if __name__ == "__main__":  # pragma: no cover - CLI entrypoint
    sys.exit(main())
