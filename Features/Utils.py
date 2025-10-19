import FreeCAD, Part
import sys, os, json, math, time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

SPRING_PREFERENCES_PATH = "User parameter:BaseApp/Preferences/Mod/Spring"

def _spring_preferences() -> FreeCAD.ParamGet:
    """Return the ParamGet instance for the Spring preference group."""

    return FreeCAD.ParamGet(SPRING_PREFERENCES_PATH)

def preference_int(name: str, default: int) -> int:
    """Read an integer preference value with a fallback default."""

    return _spring_preferences().GetInt(name, default)

def preference_float(name: str, default: float) -> float:
    """Read a floating-point preference value with a fallback default."""

    return _spring_preferences().GetFloat(name, default)

def preference_bool(name: str, default: bool) -> bool:
    """Read a boolean preference value with a fallback default."""

    return _spring_preferences().GetBool(name, default)

def add_property(obj, name, default, typ="App::PropertyFloat", group="Spring", mode=0):
    """Safely add a FreeCAD property if it doesn't already exist."""
    FreeCAD.Console.PrintMessage(f"[add_property] obj={obj} name={name} default={default} typ={typ} group={group} mode={mode}\n")
    if not hasattr(obj, name):
        obj.addProperty(typ, name, group, "")
        if default is not None:
            setattr(obj, name, default)
        obj.setEditorMode(name, mode)
        
def helix_solid(radius, pitch, height, wire_radius):
    """Create a helical solid (coil) from geometric parameters."""
    FreeCAD.Console.PrintMessage(f"[helix_solid] radius={radius} pitch={pitch} height={height} wire_radius={wire_radius}\n")
    helix = Part.makeHelix(pitch, height, radius)
    helix_wire = helix if isinstance(helix, Part.Wire) else Part.Wire([helix])
    helix_edge = helix_wire.Edges[0]

    u0 = helix_edge.FirstParameter
    start_pt = helix_edge.valueAt(u0)
    tangent = helix_edge.tangentAt(u0)
    if isinstance(tangent, tuple):
        tangent = tangent[0]
    tangent.normalize()

    circle = Part.makeCircle(wire_radius, start_pt, tangent)
    circle_wire = Part.Wire(circle)

    try:
        sweep = helix_wire.makePipeShell([circle_wire], True, True)
        if sweep.ShapeType == "Shell":
            sweep = Part.makeSolid(sweep)
    except Exception:
        sweep = Part.makeCylinder(wire_radius, height)

    return sweep

def spring_coils(height, pitch):
    """Number of coils based on total height and pitch."""
    return height / pitch

def spring_wire_length(mean_diameter, pitch, coils):
    """Length of wire forming the helix."""
    return math.sqrt((math.pi * mean_diameter)**2 + pitch**2) * coils

def spring_solid_length(wire_diameter, coils):
    """Total length when fully compressed."""
    return wire_diameter * (coils + 1)
        
_ENUM_CACHE = {}  # { name: (header, rows, mtime) }

def load_enum_table(type_name, enum_name):
    """
    Load <enum_name>.json once and return (header, rows).
    Cached after first load for performance.
    """
    FreeCAD.Console.PrintMessage(f"[load_enum_table] type_name={type_name} enum_name={enum_name}\n")
    global _ENUM_CACHE

    # If cached, return immediately
    if enum_name in _ENUM_CACHE:
        print(f"[load_enum_table] _ENUM_CACHE[enum_name]={_ENUM_CACHE[enum_name]}")
        return _ENUM_CACHE[enum_name]

    # Locate JSON relative to this script
    base_dir = os.path.dirname(__file__)
    path = os.path.join(base_dir, f"./{type_name}/{enum_name}.json")
    path = os.path.abspath(path)
    mtime = os.path.getmtime(path) if os.path.exists(path) else 0

    try:
        with open(path, "r") as f:
            data = json.load(f)

        header, rows = data[0], data[1:]
        _ENUM_CACHE[enum_name] = (header, rows, mtime)
        FreeCAD.Console.PrintMessage(f"[enum_loader] Reloaded {enum_name} (modified)\n")

    except Exception as e:
        FreeCAD.Console.PrintError(f"[enum_loader] Failed to load {enum_name}: {e}\n")
        header, rows = [], []
        _ENUM_CACHE[enum_name] = (header, rows, mtime)

    print(f"[load_enum_table] header={header} rows={rows} mtime={mtime}")
    return header, rows, mtime


def enum_selection_value(selection):
    """Return the active enumeration value from a property selection."""

    if isinstance(selection, (list, tuple)):
        selection = selection[0] if selection else None
    print(f"[enum_selection_value] selection={selection}")
    return selection


def apply_enum_property_values(obj, enum_type: str, name: str, selection=None) -> None:
    """
    Apply secondary column values from an enumeration table to the object.

    Parameters
    ----------
    obj: FreeCAD object whose properties should be updated.
    enum_type_name: Directory name containing the enum JSON file (e.g. "Compression").
    name: Base name of the enum JSON file (e.g. "EndType").
    selection: Optional explicit selection value. If omitted the current property
        value from ``obj`` is used.
    """

    header, rows, _mtime = load_enum_table(enum_type, name)
    if len(header) <= 1:
        return  # no secondary columns

    selected = enum_selection_value(selection if selection is not None else getattr(obj, name, None))
    if selected is None:
        return

    for row in rows:
        if not row:
            continue
        if row[0] != selected:
            continue
        for key, value in zip(header[1:], row[1:]):
            if hasattr(obj, key):
                setattr(obj, key, value)
        break

def clear_enum_cache():
    """Clear all cached enumeration data (for dev/debug use)."""
    FreeCAD.Console.PrintMessage(f"[clear_enum_cache]"+"\n")
    global _ENUM_CACHE
    _ENUM_CACHE.clear()
    FreeCAD.Console.PrintMessage(f"[clear_enum_cache] Cache cleared\n")
    
def reload_enum(fp, type_name, name):
    """
    Rebuild a single enumeration property from its JSON definition.
    Keeps the current value if it is still valid.
    """
    FreeCAD.Console.PrintMessage(f"[reload_enum] fp={fp} type_name={type_name} name={name}\n")

    _header, rows, _mtime = load_enum_table(type_name, name)
    if not rows:
        FreeCAD.Console.PrintWarning(f"[reload_enum] No data for {name}\n")
        return

    enum_values = [r[0] for r in rows]
    print(f"[reload_enum] enum_values={enum_values}")
    current = getattr(fp, name, None)
    print(f"[reload_enum] current={current}")
    setattr(fp, name, enum_values)

    # Restore previous selection if still valid
    if current in enum_values:
        setattr(fp, name, current)
    else:
        setattr(fp, name, enum_values[0])

    FreeCAD.Console.PrintMessage(f"[reload_enum] {name} reloaded with {len(enum_values)} enum_values={enum_values}\n")
