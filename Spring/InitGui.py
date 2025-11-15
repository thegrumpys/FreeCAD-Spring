"""Legacy InitGui shim for FreeCAD discovery."""
from __future__ import annotations

from pathlib import Path

from . import _bootstrap

_bootstrap.exec_legacy_module(globals(), Path(__file__).resolve().parent, "InitGui.py")
