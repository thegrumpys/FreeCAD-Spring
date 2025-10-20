"""Tests ensuring the workbench entry points are importable."""

import importlib.util
import pathlib
import sys

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
