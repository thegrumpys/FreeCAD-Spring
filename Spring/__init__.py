"""Compatibility package that executes the workbench's Init module."""
from __future__ import annotations

import pathlib
import sys

from . import _bootstrap


def _bootstrap_package() -> None:
    module = sys.modules[__name__]
    if not hasattr(module, "__file__"):
        module.__file__ = str(pathlib.Path(__file__).resolve())
    _bootstrap.load_init_module(module)


_bootstrap_package()
