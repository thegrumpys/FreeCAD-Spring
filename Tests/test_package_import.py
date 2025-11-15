"""Tests ensuring the workbench entry points are importable."""

import importlib
import importlib.util
import pathlib
import sys

from scripts import install_spring_mod_path as installer

# Ensure the add-on root is importable when tests run outside FreeCAD.
ADDON_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ADDON_ROOT) not in sys.path:
    sys.path.insert(0, str(ADDON_ROOT))


def test_init_modules_are_discoverable():
    spec_init = importlib.util.find_spec("Init")
    spec_init_gui = importlib.util.find_spec("InitGui")
    assert spec_init is not None, "Init module should be discoverable"
    assert spec_init_gui is not None, "InitGui module should be discoverable"

    addon_root = ADDON_ROOT
    assert pathlib.Path(spec_init.origin).resolve().parent == addon_root
    assert pathlib.Path(spec_init_gui.origin).resolve().parent == addon_root


def test_spring_package_shim_executes_init_module():
    spring = importlib.import_module("Spring")

    init_path = ADDON_ROOT / "Init.py"
    assert pathlib.Path(spring.__file__).resolve() == init_path
    assert spring.__spec__ is not None and pathlib.Path(spring.__spec__.origin).resolve() == init_path
    assert spring.__path__ == [str(ADDON_ROOT)]
    assert spring.__spec__.submodule_search_locations == [str(ADDON_ROOT)]

    for attribute in ("__title__", "__author__", "_add_compiled_library_path"):
        assert hasattr(spring, attribute), f"Spring shim should expose Init.py attribute {attribute!r}"


def test_spring_import_succeeds_when_only_repo_on_sys_path(monkeypatch, tmp_path):
    module_name = "Spring"
    sys.modules.pop(module_name, None)

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, "path", [str(ADDON_ROOT)])
    importlib.invalidate_caches()

    spring = importlib.import_module(module_name)
    init_path = ADDON_ROOT / "Init.py"

    assert pathlib.Path(spring.__file__).resolve() == init_path


def test_spring_import_succeeds_via_stub_package(monkeypatch, tmp_path):
    site_packages = tmp_path / "site-packages"
    installer.install_stub_package(site_packages, project_root=ADDON_ROOT)

    sys.modules.pop("Spring", None)
    monkeypatch.setattr(sys, "path", [str(site_packages)])
    importlib.invalidate_caches()

    spring = importlib.import_module("Spring")
    init_path = ADDON_ROOT / "Init.py"

    assert pathlib.Path(spring.__file__).resolve() == init_path
