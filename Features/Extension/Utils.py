"""Utilities specific to extension springs."""

from __future__ import annotations

import FreeCAD
import Part

MUSIC_WIRE_SHEAR_MODULUS = 79.3e9  # Pascals

_EPSILON = 1.0e-6


def _pipe_from_wire(wire: Part.Wire, wire_radius: float, fallback_height: float) -> Part.Shape:
    if wire is None or not wire.Edges:
        return Part.makeCylinder(wire_radius, max(fallback_height, _EPSILON))

    helix_edge = wire.Edges[0]
    u0 = helix_edge.FirstParameter
    start_pt = helix_edge.valueAt(u0)
    tangent = helix_edge.tangentAt(u0)
    if isinstance(tangent, tuple):
        tangent = tangent[0]
    tangent.normalize()

    circle = Part.makeCircle(wire_radius, start_pt, tangent)
    circle_wire = Part.Wire(circle)

    try:
        sweep = wire.makePipeShell([circle_wire], True, True)
        if sweep.ShapeType == "Shell":
            sweep = Part.makeSolid(sweep)
    except Exception:
        sweep = Part.makeCylinder(wire_radius, max(fallback_height, _EPSILON))

    return sweep


def spring_solid(
    end_type_index,
    end_type,
    radius: float,
    pitch: float,
    height: float,
    wire_radius: float,
    *_ignored,
    **_ignored_kwargs,
) -> Part.Shape:
    """Create the solid geometry for an extension spring."""

    safe_pitch = pitch if abs(pitch) > _EPSILON else (_EPSILON if pitch >= 0 else -_EPSILON)
    helix = Part.makeHelix(safe_pitch, height, radius)
    helix_wire = helix if isinstance(helix, Part.Wire) else Part.Wire([helix])
    return _pipe_from_wire(helix_wire, wire_radius, height)

def _as_float(value, default):
    try:
        candidate = getattr(value, "Value", value)
        return float(candidate)
    except (TypeError, ValueError):
        return float(default)

def update_globals(obj) -> None:
    """Update global properties based on the object's global properties."""

def update_properties(obj) -> None:
    """Update properties based on the object's properties."""

    rate = 0.0

    try:
        outer = float(obj.OutsideDiameterAtFree)
        wire = float(obj.WireDiameter)
        coils = float(obj.CoilsTotal)
        shear_modulus = _as_float(getattr(obj, "TorsionModulus", MUSIC_WIRE_SHEAR_MODULUS), MUSIC_WIRE_SHEAR_MODULUS)
    except (AttributeError, TypeError, ValueError):
        obj.Rate = rate
        return

    mean_diameter = outer - wire
    if mean_diameter <= 0.0 or wire <= 0.0 or coils <= 0.0 or shear_modulus <= 0.0:
        obj.Rate = rate
        return

    wire_m = wire / 1000.0
    mean_m = mean_diameter / 1000.0
    rate_n_per_m = (shear_modulus * wire_m**4) / (8.0 * coils * (mean_m**3))
    rate = rate_n_per_m / 1000.0
    obj.Rate = rate
