"""Keep the Spring workbench visible to FreeCAD's bundled Python.

Some FreeCAD launchers rebuild ``sys.path`` and drop entries inherited
from ``PYTHONPATH``.  When that happens ``import Spring`` fails even if
the repository root is exported.  This helper installs a lightweight
``Spring`` package into site-packages (and optional ``Mod/`` trees) that
points back to the checkout so the interpreter always discovers the
workbench.

The script prefers the interpreter's own site-packages paths but also
considers FreeCAD-specific environment variables (``FREECAD_HOME`` or
``FREECAD_PREFIX``) for users who install the workbench directly under a
``Mod/`` tree.

Usage::

    pixi run install-spring-path

The command is idempotent and safe to re-run; the shim files are only
rewritten when their contents differ from the desired project root.
"""

from __future__ import annotations

import argparse
import os
import shutil
import site
import sys
import sysconfig
import textwrap
from pathlib import Path
from typing import Iterable, List, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
POINTER_FILENAME = "_spring_workbench_root.txt"

SPRING_PACKAGE_NAME = "Spring"
BOOTSTRAP_MODULE = "_bootstrap.py"

STUB_INIT_TEMPLATE = """
from __future__ import annotations

from pathlib import Path

from . import _bootstrap

_bootstrap.exec_legacy_module(globals(), Path(__file__).resolve().parent, "Init.py")
"""

STUB_INIT_GUI_TEMPLATE = """
from __future__ import annotations

from pathlib import Path

from . import _bootstrap

_bootstrap.exec_legacy_module(globals(), Path(__file__).resolve().parent, "InitGui.py")
"""


def unique_paths(paths: Iterable[Path]) -> List[Path]:
    """Deduplicate paths while preserving order."""

    seen: set[Path] = set()
    result: List[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved not in seen:
            seen.add(resolved)
            result.append(resolved)
    return result


def split_path_list(raw: str | None) -> Sequence[str]:
    if not raw:
        return []
    return [chunk for chunk in raw.split(os.pathsep) if chunk]


def discover_site_package_directories() -> List[Path]:
    """Return the interpreter's site-packages directories."""

    candidates: List[Path] = []

    try:
        site_packages = getattr(site, "getsitepackages", lambda: [])()
    except Exception:  # pragma: no cover - heavily implementation specific
        site_packages = []
    for entry in site_packages or []:
        path = Path(entry)
        if path.is_dir():
            candidates.append(path)

    try:
        user_site = site.getusersitepackages()
    except Exception:  # pragma: no cover - user site may be disabled
        user_site = None
    if user_site:
        path = Path(user_site)
        if path.is_dir():
            candidates.append(path)

    for key in ("purelib", "platlib"):
        try:
            location = sysconfig.get_path(key)
        except Exception:  # pragma: no cover - sysconfig failures are rare
            location = None
        if location:
            path = Path(location)
            if path.is_dir():
                candidates.append(path)

    return unique_paths(candidates)


def discover_mod_directories(env: os._Environ[str] | None = None) -> List[Path]:
    """Return candidate FreeCAD Mod directories based on the environment."""

    env = env or os.environ
    candidates: List[Path] = []

    for key in ("FREECAD_HOME", "FREECAD_MODPATH"):
        for chunk in split_path_list(env.get(key)):
            path = Path(chunk)
            if path.is_dir():
                candidates.append(path)

    prefix = env.get("FREECAD_PREFIX")
    if prefix:
        mod_dir = Path(prefix) / "Mod"
        if mod_dir.is_dir():
            candidates.append(mod_dir)

    sys_prefix_mod = Path(sys.prefix) / "Mod"
    if sys_prefix_mod.is_dir():
        candidates.append(sys_prefix_mod)

    # If FreeCAD is importable we can ask it directly.
    try:
        import FreeCAD  # type: ignore

        freecad_home = Path(FreeCAD.getHomePath())  # type: ignore[attr-defined]
        if freecad_home.is_dir():
            candidates.append(freecad_home)
    except Exception:
        pass

    return unique_paths(path for path in candidates if path.exists())


def discover_target_directories(env: os._Environ[str] | None = None) -> List[Path]:
    """Return directories that should receive the Spring ``.pth`` file."""

    env = env or os.environ
    site_dirs = discover_site_package_directories()
    mod_dirs = discover_mod_directories(env=env)
    return unique_paths([*site_dirs, *mod_dirs])


def _write_if_changed(target: Path, content: str) -> Path | None:
    if target.exists():
        try:
            current = target.read_text(encoding="utf-8")
        except OSError:
            current = ""
        if current == content:
            return None

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return target


def copy_package_file(source: Path, destination: Path) -> Path | None:
    if destination.exists():
        try:
            if destination.read_text(encoding="utf-8") == source.read_text(encoding="utf-8"):
                return None
        except OSError:
            pass

    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    return destination


def ensure_pointer_file(package_dir: Path, project_root: Path) -> Path | None:
    desired = f"{project_root}\n"
    return _write_if_changed(package_dir / POINTER_FILENAME, desired)


def ensure_stub_module(package_dir: Path, filename: str, template: str) -> Path | None:
    content = textwrap.dedent(template).lstrip()
    return _write_if_changed(package_dir / filename, content)


def install_stub_package(target_dir: Path, project_root: Path) -> List[Path]:
    package_dir = target_dir / SPRING_PACKAGE_NAME

    if package_dir.exists():
        try:
            if package_dir.resolve() == project_root.resolve():
                return []
        except OSError:
            pass

    written: List[Path] = []

    pointer = ensure_pointer_file(package_dir, project_root)
    if pointer is not None:
        written.append(pointer)

    bootstrap_source = PROJECT_ROOT / SPRING_PACKAGE_NAME / BOOTSTRAP_MODULE
    bootstrap_dest = package_dir / BOOTSTRAP_MODULE
    copied = copy_package_file(bootstrap_source, bootstrap_dest)
    if copied is not None:
        written.append(copied)

    init_source = PROJECT_ROOT / SPRING_PACKAGE_NAME / "__init__.py"
    init_dest = package_dir / "__init__.py"
    copied = copy_package_file(init_source, init_dest)
    if copied is not None:
        written.append(copied)

    for filename, template in ("Init.py", STUB_INIT_TEMPLATE), ("InitGui.py", STUB_INIT_GUI_TEMPLATE):
        updated = ensure_stub_module(package_dir, filename, template)
        if updated is not None:
            written.append(updated)

    return written


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mod",
        dest="mod_dirs",
        action="append",
        default=[],
        help="Explicit Mod directory to target; can be specified multiple times.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=PROJECT_ROOT,
        help="Override the Spring project root recorded in the .pth file.",
    )
    parser.add_argument(
        "--print-targets",
        action="store_true",
        help="Print the discovered Mod directories without writing files.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    targets = [Path(p) for p in args.mod_dirs]
    if not targets:
        targets = discover_target_directories()

    if not targets:
        print("No candidate Mod directories were found.", file=sys.stderr)
        return 1

    if args.print_targets:
        for mod_dir in targets:
            print(mod_dir)
        return 0

    any_written = False
    for mod_dir in targets:
        written = install_stub_package(mod_dir, project_root=args.project_root)
        for path in written:
            any_written = True
            print(f"Wrote {path}")

    if not any_written:
        print("Spring stub packages already up to date.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
