"""Bootstrap the Spring workbench package.

FreeCAD expects the workbench's entry points to live in ``Spring.Init`` and
``Spring.InitGui``.  When the add-on is cloned into ``Mod/FreeCAD-Spring`` the
package directory is still ``Spring/``, but the helper modules remain one level
up (``Init.py`` and ``InitGui.py``).  Python only searches the package directory
for submodules by default, so those entry points are missed and the workbench
fails to register.

By extending ``__path__`` with the add-on root we tell the import system to also
look in the parent directory for submodules.  That allows
``import Spring.InitGui`` to succeed no matter whether the containing folder is
named ``Spring`` or ``FreeCAD-Spring``.
"""

from __future__ import annotations

from pathlib import Path

# ``__path__`` is defined by the import machinery when the package is created.
# Convert it to a list so we can append to it even if the default implementation
# returned an importer-specific object.
__path__ = list(__path__)  # type: ignore[name-defined]

_ROOT = Path(__file__).resolve().parent.parent
_ROOT_STR = str(_ROOT)
if _ROOT_STR not in __path__:
    __path__.append(_ROOT_STR)

del _ROOT, _ROOT_STR

