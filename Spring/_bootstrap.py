"""Helpers for loading the Spring workbench from arbitrary locations."""

from __future__ import annotations

import importlib.util
import os
import pathlib
from types import ModuleType

POINTER_FILENAME = "_spring_workbench_root.txt"
ENVIRONMENT_VARIABLE = "SPRING_WORKBENCH_ROOT"


def _read_pointer(package_dir: pathlib.Path) -> pathlib.Path | None:
    pointer_path = package_dir / POINTER_FILENAME
    if not pointer_path.exists():
        return None

    try:
        raw = pointer_path.read_text(encoding="utf-8")
    except OSError:
        return None

    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        candidate = pathlib.Path(stripped)
        if not candidate.is_absolute():
            candidate = (package_dir / candidate).resolve()
        return candidate

    return None


def _environment_path() -> pathlib.Path | None:
    raw = os.environ.get(ENVIRONMENT_VARIABLE)
    if not raw:
        return None
    candidate = pathlib.Path(raw)
    if not candidate.is_absolute():
        candidate = candidate.resolve()
    return candidate


def discover_workbench_root(package_dir: pathlib.Path) -> pathlib.Path:
    """Return the directory that contains the real ``Init.py`` module."""

    package_dir = package_dir.resolve()

    direct_parent = package_dir.parent
    pointer_path = _read_pointer(package_dir)
    env_path = _environment_path()

    candidates = (
        direct_parent,
        pointer_path,
        env_path,
    )

    for candidate in candidates:
        if candidate is None:
            continue
        init_candidate = candidate / "Init.py"
        if init_candidate.exists():
            return candidate

    raise ImportError(
        "Unable to locate Spring workbench root. Checked parent directory, pointer file, "
        f"and environment variable {ENVIRONMENT_VARIABLE}. Package directory was {package_dir!s}."
    )


def load_init_module(module: ModuleType) -> None:
    """Execute ``Init.py`` in ``module`` keeping metadata aligned."""

    package_dir = pathlib.Path(module.__file__).resolve().parent
    workbench_root = discover_workbench_root(package_dir)
    init_path = workbench_root / "Init.py"

    spec = importlib.util.spec_from_file_location(
        module.__name__, init_path, submodule_search_locations=[str(workbench_root)]
    )
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot create spec for Init.py at {init_path!s}")

    module.__file__ = str(init_path)
    module.__spec__ = spec
    module.__loader__ = spec.loader
    module.__package__ = module.__name__
    module.__path__ = [str(workbench_root)]

    spec.loader.exec_module(module)


def exec_legacy_module(module_globals: dict, package_dir: pathlib.Path, filename: str) -> None:
    """Execute a legacy FreeCAD entry point (``Init.py``/``InitGui.py``)."""

    workbench_root = discover_workbench_root(package_dir)
    target = workbench_root / filename
    if not target.exists():
        raise ImportError(f"Expected {filename} at {target!s}")

    module_globals["__file__"] = str(target)
    module_globals.setdefault("__package__", "Spring")

    with target.open("r", encoding="utf-8") as handle:
        source = handle.read()

    code = compile(source, str(target), "exec")
    exec(code, module_globals)

