#!/usr/bin/env python3
"""Diagnostic helper for the Spring workbench C++ build."""
from __future__ import annotations

import importlib
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
import textwrap
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


def _header(title: str) -> None:
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def _print_table(pairs: Iterable[tuple[str, str]]) -> None:
    items = list(pairs)
    width = max((len(key) for key, _ in items), default=0)
    for key, value in items:
        print(f"{key.ljust(width)} : {value}")


def _safe_resolve(path_str: str | None) -> Path | None:
    if not path_str:
        return None
    try:
        return Path(path_str).expanduser().resolve()
    except OSError:  # pragma: no cover - diagnostic resilience
        return None


def _split_path_entries(raw: str | None) -> list[Path]:
    entries: list[Path] = []
    if not raw:
        return entries
    for piece in raw.split(os.pathsep):
        if not piece:
            continue
        try:
            entries.append(Path(piece).expanduser().resolve())
        except OSError:  # pragma: no cover - diagnostic resilience
            entries.append(Path(piece))
    return entries


def _check_marker(path: Path, markers: Iterable[str]) -> str:
    if not path.exists():
        return "missing"
    for marker in markers:
        candidate = path / marker
        if candidate.exists():
            return f"present (found {marker})"
    return "present (no known marker)"

def _try_import_freecad():
    try:
        import FreeCAD  # type: ignore
    except Exception as exc:  # pragma: no cover - diagnostic output only
        return None, exc
    return FreeCAD, None


def _augment_sys_path_for_freecad() -> list[Path]:
    major = sys.version_info.major
    minor = sys.version_info.minor
    version_dir = f"python{major}.{minor}"

    candidates: list[Path] = []

    def _add_path(path: Path) -> None:
        try:
            resolved = path.expanduser().resolve()
        except OSError:  # pragma: no cover - defensive
            return
        candidates.append(resolved)

    env_path_vars = [
        "FREECAD_PYTHONPATH",
        "FREECAD_MOD_DIR",
    ]
    for var in env_path_vars:
        value = os.environ.get(var)
        if not value:
            continue
        for raw in value.split(os.pathsep):
            if raw:
                _add_path(Path(raw))

    prefix_vars = [
        "FREECAD_PREFIX",
    ]
    prefixes: list[Path] = []
    for var in prefix_vars:
        value = os.environ.get(var)
        if value:
            prefixes.append(Path(value))

    exec_prefix = Path(sys.executable).resolve().parent.parent
    prefixes.append(exec_prefix)

    for prefix in prefixes:
        _add_path(prefix)
        _add_path(prefix / "Mod")
        _add_path(prefix / "lib")
        _add_path(prefix / "lib" / version_dir)
        _add_path(prefix / "lib" / version_dir / "site-packages")
        _add_path(prefix / "lib" / version_dir / "dist-packages")

    freecad_home_env = os.environ.get("FREECAD_HOME")
    if freecad_home_env:
        home_path = Path(freecad_home_env)
        _add_path(home_path)
        _add_path(home_path.parent)

    inserted: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if not candidate.exists():
            continue
        candidate_str = str(candidate)
        if candidate_str in sys.path:
            continue
        sys.path.insert(0, candidate_str)
        inserted.append(candidate)
    return inserted


@dataclass
class FreeCADState:
    module: Any | None
    import_error: Exception | None
    added_paths: list[Path]
    module_path: Path | None
    home_path: Path | None
    user_data_dir: Path | None
    gui_import_error: Exception | None
    initial_error: Exception | None


@dataclass
class FreeCADCmdResult:
    path: str | None
    stdout: str | None
    stderr: str | None
    info: dict[str, Any] | None
    error: Exception | None


def _report_environment() -> None:
    _header("Environment Overview")
    print(f"Platform : {platform.platform()}")
    print(f"Python   : {sys.executable}")
    print(f"Version  : {sys.version.replace(os.linesep, ' ')}")
    print(f"cwd      : {Path.cwd()}")

    _header("Key Environment Variables")
    important_vars = [
        "VIRTUAL_ENV",
        "PYTHONPATH",
        "FreeCAD_DIR",
        "CMAKE_PREFIX_PATH",
        "CMAKE_MODULE_PATH",
        "PATH",
        "QT_HOST_PATH",
        "FREECAD_SOURCE_DIR",
        "FREECAD_BUILD_DIR",
        "FREECAD_PYCXX_INCLUDE_DIR",
    ]
    _print_table((var, os.environ.get(var, "<unset>")) for var in important_vars)

    _header("PATH Entries")
    for entry in os.environ.get("PATH", "").split(os.pathsep):
        print(f"  - {entry}")

    source_dirs = os.environ.get("FREECAD_SOURCE_DIR")
    if source_dirs:
        _header("FREECAD_SOURCE_DIR Entries")
        for entry in source_dirs.split(os.pathsep):
            print(f"  - {entry}")

    build_dirs = os.environ.get("FREECAD_BUILD_DIR")
    if build_dirs:
        _header("FREECAD_BUILD_DIR Entries")
        for entry in build_dirs.split(os.pathsep):
            print(f"  - {entry}")

    _header("Python sys.path")
    for entry in sys.path:
        print(f"  - {entry}")


def _report_spring_visibility() -> None:
    _header("Spring Python Probe")

    repo_root = Path(__file__).resolve().parent.parent
    print(f"Repository root : {repo_root}")

    pythonpath_entries = _split_path_entries(os.environ.get("PYTHONPATH"))
    if pythonpath_entries:
        print("PYTHONPATH entries (resolved):")
        for entry in pythonpath_entries:
            print(f"  - {entry}")
    else:
        print("PYTHONPATH entries (resolved): <none>")

    def _matches_repo(path: Path) -> bool:
        if path == repo_root:
            return True
        try:
            return path.resolve() == repo_root
        except OSError:  # pragma: no cover - diagnostic resilience
            return False

    sys_matches: list[str] = []
    for entry in sys.path:
        try:
            candidate = Path(entry)
        except TypeError:  # pragma: no cover - defensive
            continue
        if _matches_repo(candidate):
            sys_matches.append(entry)

    if sys_matches:
        print("sys.path entries matching the repository root:")
        for entry in sys_matches:
            print(f"  - {entry}")
    else:
        print("sys.path entries matching the repository root: <none>")

    spec = importlib.util.find_spec("Spring")
    if spec is None:
        print("Spring module spec: <not found>")
    else:
        origin = spec.origin or "<unknown>"
        print(f"Spring module spec origin : {origin}")
        locations = spec.submodule_search_locations or []
        if locations:
            print("Spring spec submodule search locations:")
            for location in locations:
                print(f"  - {location}")
        else:
            print("Spring spec submodule search locations: <none>")

    try:
        spring_module = importlib.import_module("Spring")
    except Exception as exc:  # pragma: no cover - diagnostic output only
        print(f"Import Spring failed: {exc!r}")
    else:
        module_file = getattr(spring_module, "__file__", "<unset>")
        print(f"Import Spring succeeded. __file__={module_file}")
        module_path = getattr(spring_module, "__path__", None)
        if module_path is None:
            print("Spring.__path__ : <unset>")
        else:
            print("Spring.__path__ entries:")
            for entry in module_path:
                print(f"  - {entry}")

        exposed = [
            name
            for name in ("Gui", "App", "__all__", "__package__")
            if hasattr(spring_module, name)
        ]
        if exposed:
            print("Spring exports:")
            for name in exposed:
                value = getattr(spring_module, name)
                print(f"  - {name}: {type(value).__name__}")
        else:
            print("Spring exports: <none detected>")


def _report_qt_host() -> None:
    _header("Qt Host Tooling")
    qt_host_env = os.environ.get("QT_HOST_PATH")
    if qt_host_env:
        resolved_qt_host = _safe_resolve(qt_host_env)
        print(f"QT_HOST_PATH : {qt_host_env}")
        if resolved_qt_host:
            qt_markers = [
                "bin/moc",
                "bin/qtpaths",
                "lib/cmake/Qt6Core",
            ]
            print(
                f"Resolved path : {resolved_qt_host}"
                f" ({_check_marker(resolved_qt_host, qt_markers)})"
            )
        else:  # pragma: no cover - diagnostic resilience
            print("Resolved path : <unable to resolve>")
    else:
        print("QT_HOST_PATH : <unset>")

    freecad_prefix = _safe_resolve(os.environ.get("FREECAD_PREFIX"))
    if freecad_prefix:
        print(f"Resolved FREECAD_PREFIX : {freecad_prefix}")
        qt_host_candidate = freecad_prefix / "qt-host"
        qt_markers = [
            "bin/moc",
            "bin/qtpaths",
            "lib/cmake/Qt6Core",
        ]
        status = _check_marker(qt_host_candidate, qt_markers)
        print(f"FREECAD_PREFIX/qt-host : {status} ({qt_host_candidate})")
    else:
        print("FREECAD_PREFIX : <unset>")

    conda_prefix = os.environ.get("CONDA_PREFIX")
    if conda_prefix:
        resolved_conda = _safe_resolve(conda_prefix)
        if resolved_conda:
            qt_markers = [
                "bin/qtpaths",
                "bin/qtpaths6",
                "lib/cmake/Qt6Core",
            ]
            status = _check_marker(resolved_conda, qt_markers)
            print(f"CONDA_PREFIX : {conda_prefix}")
            print(f"Resolved CONDA_PREFIX : {resolved_conda} ({status})")
            if not qt_host_env and status.startswith("present"):
                print(
                    "Hint: export QT_HOST_PATH=\"$CONDA_PREFIX\" before running"
                    " configure/build tasks so CMake can locate Qt host tools."
                )


def _collect_freecad_state() -> tuple[FreeCADState, FreeCADCmdResult]:
    initial_module, initial_error = _try_import_freecad()
    module = initial_module
    import_error = initial_error
    added_paths: list[Path] = []

    if module is None:
        added_paths = _augment_sys_path_for_freecad()
        if added_paths:
            module, import_error = _try_import_freecad()

    module_path: Path | None = None
    home_path: Path | None = None
    user_dir: Path | None = None
    gui_error: Exception | None = None

    if module is not None:
        raw_module_path = getattr(module, "__file__", None)
        if raw_module_path:
            try:
                module_path = Path(raw_module_path).resolve()
            except OSError:  # pragma: no cover - diagnostic resilience
                module_path = None

        home_fn = getattr(module, "getHomePath", None)
        if callable(home_fn):
            try:
                home_path = Path(home_fn()).resolve()
            except Exception as exc:  # pragma: no cover - diagnostic resilience
                print(f"FreeCAD home : <error retrieving path> ({exc})")
                home_path = None

        user_fn = getattr(module, "getUserAppDataDir", None)
        if callable(user_fn):
            try:
                user_dir = Path(user_fn()).resolve()
            except Exception as exc:  # pragma: no cover - diagnostic resilience
                print(f"User data dir: <error retrieving path> ({exc})")
                user_dir = None

        if module_path is None and home_path is not None:
            for candidate in (
                home_path / "lib" / "FreeCAD.so",
                home_path / "lib" / "FreeCAD.pyd",
                home_path / "lib" / "FreeCAD.dll",
                home_path / "lib" / "libFreeCADApp.dylib",
            ):
                if candidate.exists():
                    try:
                        module_path = candidate.resolve()
                    except OSError:  # pragma: no cover - diagnostic resilience
                        module_path = candidate
                    break

        try:
            import FreeCADGui  # type: ignore  # noqa: F401
        except Exception as exc:  # pragma: no cover - diagnostic output only
            gui_error = exc

    cmd_result = _probe_freecadcmd()

    state = FreeCADState(
        module=module,
        import_error=import_error,
        added_paths=added_paths,
        module_path=module_path,
        home_path=home_path,
        user_data_dir=user_dir,
        gui_import_error=gui_error,
        initial_error=initial_error,
    )
    return state, cmd_result


def _report_freecad_probe(state: FreeCADState) -> None:
    _header("FreeCAD Python Probe")

    if state.module is None and state.added_paths and state.initial_error is not None:
        failure_msg = (
            "Initial import failed"
            f" ({state.initial_error!r}); added candidate directories to sys.path:"
        )
        print(failure_msg)
        for path in state.added_paths:
            print(f"  - {path}")

    if state.module is None:
        print("Import failed: " + repr(state.import_error))
    else:
        print("Import succeeded.")

    if state.module_path is not None:
        print(f"Module path : {state.module_path}")
    else:
        print("Module path : <unavailable>")

    if state.home_path is not None:
        print(f"FreeCAD home : {state.home_path}")
    elif state.module is not None:
        print("FreeCAD home : <unavailable>")

    if state.user_data_dir is not None:
        print(f"User data dir: {state.user_data_dir}")
    elif state.module is not None:
        print("User data dir: <unavailable>")

    if state.module is not None:
        if state.gui_import_error is None:
            print("FreeCADGui import succeeded.")
        else:
            print(f"FreeCADGui import failed: {state.gui_import_error!r}")


def _report_header_hints() -> None:
    _header("FreeCAD Header Hints")

    source_entries = _split_path_entries(os.environ.get("FREECAD_SOURCE_DIR"))
    build_entries = _split_path_entries(os.environ.get("FREECAD_BUILD_DIR"))
    pycxx_entries = _split_path_entries(os.environ.get("FREECAD_PYCXX_INCLUDE_DIR"))

    if not source_entries:
        print(
            "FREECAD_SOURCE_DIR is unset. Point it at your FreeCAD checkout (e.g."
            " /path/to/FreeCAD) so Spring can use headers from src/."
        )
    else:
        print("FREECAD_SOURCE_DIR candidates:")
        for entry in source_entries:
            console_header = entry / "src" / "Base" / "Console.h"
            status = "present" if console_header.exists() else "missing"
            print(f"  - {entry} -> src/Base/Console.h {status}")

    if not build_entries:
        print(
            "FREECAD_BUILD_DIR is unset. Set it to the FreeCAD build tree that"
            " produced generated headers such as src/QtCore.h (for example"
            " /path/to/FreeCAD/build/debug)."
        )
    else:
        print("FREECAD_BUILD_DIR candidates:")
        for entry in build_entries:
            qtcore_header = entry / "src" / "QtCore.h"
            status = "present" if qtcore_header.exists() else "missing"
            print(f"  - {entry} -> src/QtCore.h {status}")

    if not pycxx_entries:
        print(
            "FREECAD_PYCXX_INCLUDE_DIR is unset. Spring will scan the detected"
            " FreeCAD include directories and common site-packages folders for"
            " CXX/Extensions.hxx. Export the variable if the headers live"
            " elsewhere."
        )
    else:
        print("FREECAD_PYCXX_INCLUDE_DIR candidates:")
        for entry in pycxx_entries:
            header = entry / "CXX" / "Extensions.hxx"
            status = "present" if header.exists() else "missing"
            print(f"  - {entry} -> CXX/Extensions.hxx {status}")

    if source_entries and build_entries:
        print(
            "If QtCore.h is still missing, confirm the build tree matches the"
            " configuration you compiled (e.g. debug vs release) or export"
            " multiple entries separated by your platform's path separator."
        )


def _guess_module_from_home(home_value: str) -> Path | None:
    try:
        guessed_home = Path(home_value).resolve()
    except OSError:  # pragma: no cover - diagnostic resilience
        return None
    for candidate in (
        guessed_home / "lib" / "FreeCAD.so",
        guessed_home / "lib" / "FreeCAD.pyd",
        guessed_home / "lib" / "FreeCAD.dll",
        guessed_home / "lib" / "libFreeCADApp.dylib",
    ):
        if candidate.exists():
            try:
                return candidate.resolve()
            except OSError:  # pragma: no cover - diagnostic resilience
                return candidate
    return None


def _probe_freecadcmd() -> FreeCADCmdResult:
    path = shutil.which("freecadcmd")
    if not path:
        return FreeCADCmdResult(None, None, None, None, None)

    probe_code = textwrap.dedent(
        """
        import importlib.util
        import json
        import os
        import sys

        import FreeCAD  # noqa: F401  # pylint: disable=unused-import

        result = {
            "home": None,
            "module": None,
            "pythonpath": os.environ.get("PYTHONPATH"),
            "sys_path": sys.path,
        }

        home_fn = getattr(FreeCAD, "getHomePath", None)
        if callable(home_fn):
            try:
                result["home"] = home_fn()
            except Exception as exc:  # pragma: no cover - diagnostic output only
                result["home_error"] = repr(exc)

        module_path = getattr(FreeCAD, "__file__", None)
        if module_path is not None:
            result["module"] = module_path

        spec = importlib.util.find_spec("Spring")
        if spec is not None:
            result["spring_spec_origin"] = spec.origin
            locations = spec.submodule_search_locations
            if locations is not None:
                result["spring_spec_locations"] = list(locations)

        try:
            import Spring  # type: ignore  # noqa: F401
        except Exception as exc:  # pragma: no cover - diagnostic output only
            result["spring_import_error"] = repr(exc)
        else:
            import Spring as _spring  # type: ignore

            result["spring_file"] = getattr(_spring, "__file__", None)
            path = getattr(_spring, "__path__", None)
            if path is not None:
                result["spring_path"] = list(path)

        print(json.dumps(result))
        """
    ).strip()
    cmd = [path, "-c", probe_code]

    try:
        completed = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as err:  # pragma: no cover - diagnostics only
        stdout = err.stdout.strip() if err.stdout else None
        stderr = err.stderr.strip() if err.stderr else None
        return FreeCADCmdResult(path, stdout, stderr, None, err)

    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    info: dict[str, Any] | None = None
    if stdout:
        try:
            parsed = json.loads(stdout)
        except json.JSONDecodeError:  # pragma: no cover - best effort
            info = None
        else:
            if isinstance(parsed, dict):
                info = parsed
                home_value = parsed.get("home")
                module_value = parsed.get("module")
                if isinstance(home_value, str) and not module_value:
                    guessed = _guess_module_from_home(home_value)
                    if guessed:
                        info["module_guess"] = str(guessed)
    return FreeCADCmdResult(
        path=path,
        stdout=stdout or None,
        stderr=stderr or None,
        info=info,
        error=None,
    )


def _run_qtpaths(executable: str) -> dict[str, str]:
    probes = {
        "qt_version": "--qt-version",
        "install_prefix": "--install-prefix",
        "headers_dir": "--headers-dir",
        "libraries_dir": "--libraries-dir",
        "plugins_dir": "--plugin-dir",
    }
    info: dict[str, str] = {}
    for label, arg in probes.items():
        try:
            completed = subprocess.run(
                [executable, arg],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):  # pragma: no cover - best effort
            continue
        value = completed.stdout.strip()
        if value:
            info[label] = value
    return info


def _run_qmake(executable: str) -> dict[str, str]:
    queries = [
        "QT_VERSION",
        "QT_INSTALL_PREFIX",
        "QT_INSTALL_HEADERS",
        "QT_INSTALL_LIBS",
        "QT_INSTALL_PLUGINS",
    ]
    try:
        completed = subprocess.run(
            [executable, "-query"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):  # pragma: no cover - best effort
        return {}
    info: dict[str, str] = {}
    for line in completed.stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        if key in queries and value:
            info[key.lower()] = value.strip()
    return info


def _report_qt_installation() -> None:
    _header("Qt Installation Probe")

    qt_tools = [
        "qtpaths6",
        "qtpaths-qt6",
        "qtpaths",
        "qtpaths-qt5",
    ]
    qmake_tools = [
        "qmake6",
        "qmake-qt6",
        "qmake",
        "qmake-qt5",
    ]

    qt_roots: dict[Path, set[str]] = {}

    def _record_root(raw_path: str, source: str) -> None:
        resolved = _safe_resolve(raw_path)
        if resolved is None:
            return
        qt_roots.setdefault(resolved, set()).add(source)

    found_any = False
    for tool in qt_tools:
        path = shutil.which(tool)
        if not path:
            continue
        found_any = True
        print(f"{tool}: {path}")
        info = _run_qtpaths(path)
        if info:
            for key, value in sorted(info.items()):
                print(f"    {key.replace('_', ' ')}: {value}")
                if key in {"install_prefix", "headers_dir", "libraries_dir"}:
                    _record_root(value, f"{tool}:{key}")
        else:
            print("    (no information reported)")

    for tool in qmake_tools:
        path = shutil.which(tool)
        if not path:
            continue
        found_any = True
        print(f"{tool}: {path}")
        info = _run_qmake(path)
        if info:
            for key, value in sorted(info.items()):
                print(f"    {key}: {value}")
                if key in {"qt_install_prefix", "qt_install_headers", "qt_install_libs"}:
                    _record_root(value, f"{tool}:{key}")
        else:
            print("    (no information reported)")

    if not found_any:
        print("No Qt helper tools (qtpaths/qmake) were found on PATH.")

    env_vars = ["QTDIR", "Qt5_DIR", "Qt6_DIR", "QT_PLUGIN_PATH", "QT_INCLUDE_DIR"]
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            print(f"{var}={value}")
            for part in value.split(os.pathsep):
                if part:
                    _record_root(part, var)

    cmake_prefixes = os.environ.get("CMAKE_PREFIX_PATH", "").split(os.pathsep)
    for entry in cmake_prefixes:
        if not entry:
            continue
        resolved = _safe_resolve(entry)
        if resolved is None:
            continue
        include_dir = resolved / "include"
        if (include_dir / "QtCore").exists():
            _record_root(str(resolved), "CMAKE_PREFIX_PATH")

    if qt_roots:
        print("\nInferred Qt prefixes:")

        def _derive_include_dir(base: Path) -> Path:
            candidates = [
                base,
                base / "include",
                base / "Headers",
            ]
            for candidate in candidates:
                if candidate.is_dir() and (candidate / "QtCore").exists():
                    return candidate
            return candidates[0]

        for root, sources in sorted(qt_roots.items()):
            labels = ", ".join(sorted(sources))
            include_dir = _derive_include_dir(root)
            headers_state = _check_marker(include_dir, [
                "QtCore/qglobal.h",
                "QtCore/qobject.h",
            ])

            lib_state = "missing"
            lib_dirs = [root / "lib", root / "lib64"]
            lib_markers = [
                "libQt6Core.so",
                "libQt6Core.dylib",
                "libQt6Core.dll",
                "libQt5Core.so",
                "libQt5Core.dylib",
                "libQt5Core.dll",
            ]
            for lib_dir in lib_dirs:
                if lib_dir.is_dir():
                    state = _check_marker(lib_dir, lib_markers)
                    if state.startswith("present"):
                        lib_state = state
                        break
            if lib_state == "missing":
                framework_paths = [
                    root / "lib" / "QtCore.framework",
                    root / "lib" / "Qt5Core.framework",
                    root / "lib" / "Qt6Core.framework",
                    root / "QtCore.framework",
                    root / "Qt5Core.framework",
                    root / "Qt6Core.framework",
                ]
                for framework in framework_paths:
                    if framework.exists():
                        lib_state = f"present ({framework})"
                        break

            print(f"- {root} (sources: {labels})")
            print(f"    headers: {include_dir} -> {headers_state}")
            print(f"    libs   : {lib_state}")
    else:
        print("No Qt installation directories were inferred. Install Qt (see README).")


def _report_freecadcmd(cmd_result: FreeCADCmdResult) -> None:
    _header("freecadcmd Probe")
    if not cmd_result.path:
        print("freecadcmd not found on PATH.")
        return

    print(f"Executable : {cmd_result.path}")

    if cmd_result.error is not None:
        print("Invocation failed:")
        stderr = cmd_result.stderr or "<no stderr>"
        print(textwrap.indent(stderr, prefix="    "))
        if cmd_result.stdout:
            print("Invocation stdout:")
            print(textwrap.indent(cmd_result.stdout, prefix="    "))
        return

    print("Invocation stdout:")
    print(textwrap.indent(cmd_result.stdout or "<no stdout>", prefix="    "))
    if cmd_result.stderr:
        print("Invocation stderr:")
        print(textwrap.indent(cmd_result.stderr, prefix="    "))
    info = cmd_result.info or {}
    home_value = info.get("home")
    if home_value:
        print(f"Reported FreeCAD home : {home_value}")
    home_error = info.get("home_error")
    if home_error:
        print(f"FreeCAD home retrieval error: {home_error}")

    module_value = info.get("module")
    if module_value:
        print(f"Reported FreeCAD module : {module_value}")
    elif home_value and info.get("module_guess"):
        print(f"Derived module path guess: {info['module_guess']}")

    if "pythonpath" in info:
        print(f"Observed PYTHONPATH : {info['pythonpath']}")

    observed_sys_path = info.get("sys_path")
    repo_root = Path(__file__).resolve().parent.parent
    observed_pythonpath = info.get("pythonpath")
    if isinstance(observed_sys_path, list):
        print("Observed sys.path entries:")
        matched_repo = False
        for entry in observed_sys_path:
            print(f"  - {entry}")
            try:
                entry_path = Path(entry).expanduser().resolve()
            except OSError:  # pragma: no cover - best effort for diagnostics
                continue
            if entry_path == repo_root:
                matched_repo = True
        if not matched_repo:
            hint = (
                "Spring checkout not found on freecadcmd sys.path; ensure the repository root is "
                "available via PYTHONPATH or install the Spring loader package so freecadcmd can "
                "import the workbench."
            )
            if isinstance(observed_pythonpath, str) and observed_pythonpath:
                hint += (
                    " The command inherited PYTHONPATH, so FreeCAD's launcher may be sanitising "
                    "sys.path entries. Run 'pixi run install-spring-path' to install the helper "
                    "package into site-packages (and any detected Mod/ directories) or manually "
                    "symlink the workbench under Mod/."
                )
            print(hint)

    spec_origin = info.get("spring_spec_origin")
    if spec_origin:
        print(f"Spring spec origin : {spec_origin}")
    else:
        print("Spring spec origin : <not discovered>")

    locations = info.get("spring_spec_locations")
    if isinstance(locations, list) and locations:
        print("Spring spec search locations:")
        for location in locations:
            print(f"  - {location}")

    spring_error = info.get("spring_import_error")
    if spring_error:
        print(f"Import Spring via freecadcmd failed: {spring_error}")
    else:
        spring_file = info.get("spring_file")
        if spring_file:
            print(f"Import Spring via freecadcmd succeeded. __file__={spring_file}")
        spring_path = info.get("spring_path")
        if isinstance(spring_path, list) and spring_path:
            print("Spring.__path__ entries reported by freecadcmd:")
            for entry in spring_path:
                print(f"  - {entry}")

    module_guess = info.get("module_guess")
    if module_guess and not module_value:
        print(f"Derived module path guess: {module_guess}")


def _report_freecad_prefixes(state: FreeCADState, cmd_result: FreeCADCmdResult) -> None:
    _header("FreeCAD Prefix Heuristics")

    suggestions: list[str] = []

    def _describe_candidate(label: str, prefix: Path) -> None:
        include_dir = prefix / "include"
        lib_dir = prefix / "lib"
        home_dir = prefix / "Mod"

        def _status(path: Path) -> str:
            return "exists" if path.exists() else "missing"

        include_state = _status(include_dir)
        lib_state = _status(lib_dir)
        mod_state = _status(home_dir)

        print(f"- {label} -> {prefix}")
        print(f"    include: {include_dir} ({include_state})")
        print(f"    lib    : {lib_dir} ({lib_state})")
        print(f"    Mod    : {home_dir} ({mod_state})")

        pycxx_roots: list[Path] = []
        direct_candidate = include_dir
        if (direct_candidate / "CXX" / "Extensions.hxx").exists():
            pycxx_roots.append(direct_candidate)
        for pattern in ("python*/site-packages", "python*/dist-packages"):
            for candidate in direct_candidate.glob(pattern):
                if (candidate / "CXX" / "Extensions.hxx").exists():
                    pycxx_roots.append(candidate)

        if pycxx_roots:
            for root in dict.fromkeys(pycxx_roots):
                print(f"    PyCXX : {root} (contains CXX/Extensions.hxx)")
        else:
            print("    PyCXX : missing (no CXX/Extensions.hxx)")

        if state.module is None and mod_state == "exists":
            suggestions.append(
                "FreeCAD Python import failed; consider exporting PYTHONPATH=%s"
                % home_dir
            )

    prefix_candidates: list[tuple[str, Path]] = []

    if state.home_path is not None:
        prefix_candidates.append(("Python import", state.home_path))

    info = cmd_result.info or {}
    home_value = info.get("home") if isinstance(info, dict) else None
    if isinstance(home_value, str):
        try:
            freecad_home = Path(home_value).resolve()
        except Exception:  # pragma: no cover - diagnostic resilience
            pass
        else:
            prefix_candidates.append(("freecadcmd", freecad_home))

    env_prefix = os.environ.get("FREECAD_PREFIX")
    if env_prefix:
        try:
            prefix_candidates.append(("FREECAD_PREFIX", Path(env_prefix).resolve()))
        except Exception:  # pragma: no cover - diagnostic resilience
            pass

    freecad_home_env = os.environ.get("FREECAD_HOME")
    if freecad_home_env:
        try:
            home_parent = Path(freecad_home_env).resolve().parent
        except Exception:  # pragma: no cover - diagnostic resilience
            pass
        else:
            prefix_candidates.append(("FREECAD_HOME parent", home_parent))

    ordered_prefixes: dict[Path, list[str]] = {}
    for label, prefix in prefix_candidates:
        ordered_prefixes.setdefault(prefix, []).append(label)

    if ordered_prefixes:
        for prefix, labels in ordered_prefixes.items():
            label_display = ", ".join(labels)
            _describe_candidate(label_display, prefix)
    else:
        print("No heuristic prefixes detected.")

    if suggestions:
        print("\nHints:")
        for hint in dict.fromkeys(suggestions):
            print(f"  - {hint}")


def _report_toolchain_versions() -> None:
    _header("Toolchain Versions")
    for tool in ("cmake", "ninja", "clang", "clang++"):
        path = shutil.which(tool)
        if not path:
            print(f"{tool}: not found")
            continue
        try:
            out = subprocess.check_output(
                [tool, "--version"], text=True, stderr=subprocess.STDOUT
            )
        except Exception as exc:  # pragma: no cover - diagnostics only
            print(f"{tool}: failed to query version ({exc})")
            continue
        first_line = out.splitlines()[0] if out else "<no output>"
        print(f"{tool}: {first_line} (path: {path})")


def _report_freecad_library_search(
    state: FreeCADState, cmd_result: FreeCADCmdResult
) -> list[Path]:
    _header("FreeCAD Library Search")
    search_roots: list[Path] = []
    if state.home_path is not None:
        search_roots.append(state.home_path)

    if cmd_result.path:
        try:
            env_prefix = Path(cmd_result.path).resolve().parents[2]
        except IndexError:  # pragma: no cover - defensive
            env_prefix = Path(cmd_result.path).resolve().parent
        search_roots.append(env_prefix)

    seen: set[Path] = set()
    lib_names = [
        "libFreeCADApp.dylib",
        "libFreeCADApp.so",
        "FreeCADApp.dll",
        "libFreeCADBase.dylib",
        "libFreeCADBase.so",
        "FreeCADBase.dll",
    ]
    for root in search_roots:
        if root in seen:
            continue
        seen.add(root)
        print(f"Searching under: {root}")
        if not root.exists():
            print("  (missing)")
            continue
        matches = []
        for pattern in lib_names:
            matches.extend(root.rglob(pattern))
        if matches:
            for match in matches:
                print(f"  found {match}")
        else:
            print("  no FreeCAD libraries located")
    return search_roots


def _gather_cmake_dirs(prefix: Path) -> list[str]:
    candidates = [
        prefix / "lib" / "cmake" / "FreeCAD",
        prefix / "share" / "cmake" / "FreeCAD",
        prefix / "cmake",
    ]
    return [str(path) for path in candidates if path.exists()]


def _report_cmake_module_paths(search_roots: Iterable[Path]) -> list[str]:
    _header("CMake Module Path Discovery")
    cmake_dirs: list[str] = []
    for root in search_roots:
        cmake_dirs.extend(_gather_cmake_dirs(root))
    if cmake_dirs:
        cmake_dirs = list(dict.fromkeys(cmake_dirs))
        print("Potential CMake package directories:")
        for path in cmake_dirs:
            print(f"  - {path}")
    else:
        print("No FreeCAD CMake directories found under the inspected roots.")
    return cmake_dirs


def _report_suggested_cmake(cmake_dirs: list[str]) -> None:
    _header("Suggested CMake Invocation")
    basic_args = [
        "cmake",
        "-S",
        "src",
        "-B",
        "build/diagnostic",
        f"-DPython3_EXECUTABLE={sys.executable}",
    ]
    if cmake_dirs:
        hint = cmake_dirs[0]
        basic_args.append(f"-DCMAKE_PREFIX_PATH={hint}")
    print(" \\\n+".join(basic_args))


def main() -> None:
    _report_environment()
    _report_spring_visibility()
    _report_qt_host()
    state, cmd_result = _collect_freecad_state()
    _report_freecad_probe(state)
    _report_header_hints()
    _report_qt_installation()
    _report_freecadcmd(cmd_result)
    _report_freecad_prefixes(state, cmd_result)
    _report_toolchain_versions()
    search_roots = _report_freecad_library_search(state, cmd_result)
    cmake_dirs = _report_cmake_module_paths(search_roots)
    _report_suggested_cmake(cmake_dirs)
    _header("Done")


if __name__ == "__main__":
    main()
