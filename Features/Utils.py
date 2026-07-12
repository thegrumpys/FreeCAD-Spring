import FreeCAD
import sys, os, json, math, time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

def add_property(obj, name, default, typ="App::PropertyFloat", group="Spring", mode=0):
    """Safely add a FreeCAD property if it doesn't already exist."""
#    FreeCAD.Console.PrintMessage(f"[add_property] obj={obj} name={name} default={default} typ={typ} group={group} mode={mode}\n")
    if not hasattr(obj, name):
        obj.addProperty(typ, name, group, "")
        if default is not None:
            setattr(obj, name, default)
        obj.setEditorMode(name, mode)
        
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
#    FreeCAD.Console.PrintMessage(f"[load_enum_table] type_name={type_name} enum_name={enum_name}\n")
    global _ENUM_CACHE

    # If cached, return immediately
    if enum_name in _ENUM_CACHE:
#        print(f"[load_enum_table] _ENUM_CACHE[enum_name]={_ENUM_CACHE[enum_name]}")
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
#        FreeCAD.Console.PrintMessage(f"[enum_loader] Reloaded {enum_name} (modified)\n")

    except Exception as e:
#        FreeCAD.Console.PrintError(f"[enum_loader] Failed to load {enum_name}: {e}\n")
        header, rows = [], []
        _ENUM_CACHE[enum_name] = (header, rows, mtime)
#
#    print(f"[load_enum_table] header={header} rows={rows} mtime={mtime}")
    return header, rows, mtime


def enum_selection_value(selection):
    """Return the active enumeration value from a property selection."""

    if isinstance(selection, (list, tuple)):
        selection = selection[0] if selection else None
#    print(f"[enum_selection_value] selection={selection}")
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
#    print(f"[apply_enum_property_values] obj={obj} enum_type={enum_type} name={name} selection={selection}")

    header, rows, _mtime = load_enum_table(enum_type, name)
    if len(header) <= 1:
        return  # no secondary columns

    selected = enum_selection_value(selection if selection is not None else getattr(obj, name, None))
    if selected is None:
        return

    for row in rows:
        if not row:
#            print(f"[apply_enum_property_values] not row continue")
            continue
        if row[0] != selected:
#            print(f"[apply_enum_property_values] row[0] != selected continue")
            continue
        for key, value in zip(header[1:], row[1:]):
#            print(f"[apply_enum_property_values] key={key} value={value} hasattr()={hasattr(obj, key)}")
            if hasattr(obj, key):
#                print(f"[apply_enum_property_values] setattr obj={obj} key={key} value={value}")
                setattr(obj, key, value)
        break

def clear_enum_cache():
    """Clear all cached enumeration data (for dev/debug use)."""
#    FreeCAD.Console.PrintMessage(f"[clear_enum_cache]"+"\n")
    global _ENUM_CACHE
    _ENUM_CACHE.clear()
#    FreeCAD.Console.PrintMessage(f"[clear_enum_cache] Cache cleared\n")
    
def reload_enum(fp, type_name, name):
    """
    Rebuild a single enumeration property from its JSON definition.
    Keeps the current value if it is still valid.
    """
#    FreeCAD.Console.PrintMessage(f"[reload_enum] fp={fp} type_name={type_name} name={name}\n")

    _header, rows, _mtime = load_enum_table(type_name, name)
    if not rows:
#        FreeCAD.Console.PrintWarning(f"[reload_enum] No data for {name}\n")
        return

    enum_values = [r[0] for r in rows]
#    print(f"[reload_enum] enum_values={enum_values}")
    current = getattr(fp, name, None)
#    print(f"[reload_enum] current={current}")
    setattr(fp, name, enum_values)

    # Restore previous selection if still valid
    if current in enum_values:
#        print(f"[reload_enum] setattr fp={fp} name={name} current={current}")
        setattr(fp, name, current)
    else:
#        print(f"[reload_enum] setattr fp={fp} name={name} enum_values[0]={enum_values[0]}")
        setattr(fp, name, enum_values[0])
#
#    FreeCAD.Console.PrintMessage(f"[reload_enum] {name} reloaded with {len(enum_values)} enum_values={enum_values}\n")

def ensure_alert_properties(obj) -> None:
    """Add hidden alert storage properties to a spring object."""

    add_property(obj, "AlertErrors", [], "App::PropertyStringList", "Alerts", 2)
    add_property(obj, "AlertWarnings", [], "App::PropertyStringList", "Alerts", 2)
    add_property(obj, "AlertInfos", [], "App::PropertyStringList", "Alerts", 2)


def set_alerts(obj, errors=None, warnings=None, infos=None) -> None:
    """Store current alerts on the object without requiring GUI code."""

    ensure_alert_properties(obj)
    obj.AlertErrors = list(errors or [])
    obj.AlertWarnings = list(warnings or [])
    obj.AlertInfos = list(infos or [])


def raise_for_alert_errors(obj) -> None:
    """Raise when object-owned alerts contain fatal errors."""

    errors = [str(error) for error in getattr(obj, "AlertErrors", [])]
    if errors:
        raise ValueError("; ".join(errors))


def recompute_for_alert_state(obj) -> None:
    """Let FreeCAD update its native object error marker for alert errors."""

    try:
        has_errors = bool(list(getattr(obj, "AlertErrors", [])))
    except Exception:
        has_errors = False

    try:
        is_valid = obj.isValid()
    except Exception:
        is_valid = True

    if has_errors or not is_valid:
        try:
            obj.recompute()
        except Exception:
            pass


def update_basic_alerts(obj) -> None:
    """Populate generic spring alerts that are independent of display code."""

    has_errors = False
    errors = []
    warnings = []

    try:
        wire_diameter = float(getattr(obj, "WireDiameter"))
    except (AttributeError, TypeError, ValueError):
        wire_diameter = None
        warnings.append("Wire diameter input is incomplete.")

    try:
        outside_diameter = float(getattr(obj, "OutsideDiameterAtFree"))
    except (AttributeError, TypeError, ValueError):
        outside_diameter = None
        warnings.append("Outside diameter input is incomplete.")

    if wire_diameter is not None and wire_diameter <= 0.0:
        has_errors = True
        errors.append("Wire diameter must be greater than zero.")
    if outside_diameter is not None and wire_diameter is not None and outside_diameter <= 2.0 * wire_diameter:
        has_errors = True
        errors.append("Outside diameter must be greater than two wire diameters.")

    try:
        coils_total = float(getattr(obj, "CoilsTotal"))
        if coils_total < 1.0:
            has_errors = True
            errors.append("Total coils must be at least one.")
    except (AttributeError, TypeError, ValueError):
        coils_total = None
        warnings.append("Total coils input is incomplete.")

    try:
        coils_inactive = float(getattr(obj, "CoilsInactive"))
    except (AttributeError, TypeError, ValueError):
        coils_inactive = None

    if coils_total is not None and coils_inactive is not None and (
        coils_inactive < 0.0 or coils_inactive > coils_total
    ):
        has_errors = True
        errors.append("Inactive coils must be between zero and total coils.")

    try:
        coils_active = float(getattr(obj, "CoilsActive"))
        if coils_active < 1.0:
            warnings.append("Active coils are less than 1.")
    except (AttributeError, TypeError, ValueError):
        pass

    try:
        length_at_free = float(getattr(obj, "LengthAtFree"))
        if wire_diameter is not None and length_at_free <= wire_diameter:
            has_errors = True
            errors.append("Free length must be greater than wire diameter.")
    except (AttributeError, TypeError, ValueError):
        length_at_free = None
        warnings.append("Free length input is incomplete.")

    try:
        length_at_solid = float(getattr(obj, "LengthAtSolid"))
    except (AttributeError, TypeError, ValueError):
        length_at_solid = None

    if length_at_free is not None and length_at_solid is not None and length_at_free < length_at_solid:
        has_errors = True
        errors.append("Free length must not be less than solid length.")

    try:
        spring_index = float(getattr(obj, "SpringIndex"))
        end_type = getattr(obj, "EndType", None)
        if isinstance(end_type, (list, tuple)):
            end_type = end_type[0] if end_type else None
        if str(end_type) in ("PigtailClosed", "PigtailClosed&Ground") and spring_index <= 4.0:
            has_errors = True
            errors.append("Pigtail ends require a spring index greater than 4 for radial clearance")
        if spring_index < 4.0 or spring_index > 25.0:
            warnings.append("Spring index is outside the recommended range of 4 to 25. Manufacturing may be difficult.")
    except (AttributeError, TypeError, ValueError):
        pass

    set_alerts(obj, errors=errors if has_errors else [], warnings=warnings)


def refresh_alert_panel_for(obj) -> None:
    """Refresh the alerts dock if it is open."""

    try:
        from Gui import SpringAlertsDockWidget
    except Exception:
        return
    try:
        SpringAlertsDockWidget.refresh_dock_if_visible(obj)
    except Exception:
        pass
