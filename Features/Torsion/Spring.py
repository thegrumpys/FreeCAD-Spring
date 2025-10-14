import FreeCAD
from pathlib import Path

from .. import Utils as CoreUtils
from ..ViewProviderSpring import ViewProviderSpring
from . import Utils as SpringUtils

class TorsionSpring:
    def __init__(self, obj):
        CoreUtils.add_property(obj, "OutsideDiameterAtFree", 20.0, "App::PropertyFloat", "Independent")
        CoreUtils.add_property(obj, "WireDiameter", 2.0, "App::PropertyFloat", "Independent")
        CoreUtils.add_property(obj, "CoilsTotal", 10.0, "App::PropertyFloat", "Independent")
        CoreUtils.add_property(obj, "LengthAtFree", 25.0, "App::PropertyFloat", "Independent")

        CoreUtils.add_property(obj, "Pitch", 2.5, "App::PropertyFloat", "Dependent")
        obj.setEditorMode("Pitch", 1)
        CoreUtils.add_property(obj, "Rate", 0.0, "App::PropertyFloat", "Dependent")
        obj.setEditorMode("Rate", 1)

#        CoreUtils.add_property(obj, "EndType", "", "App::PropertyEnumeration", "Global")
        CoreUtils.add_property(obj, "CoilsInactive", 0.0, "App::PropertyFloat", "Global")
        obj.setEditorMode("CoilsInactive", 1)
        CoreUtils.add_property(obj, "ElasticModulus", SpringUtils.MUSIC_WIRE_YOUNG_MODULUS, "App::PropertyFloat", "Global")

        obj.Proxy = self
        ViewProviderSpring(obj.ViewObject)
        SpringUtils.update_globals(obj)
        SpringUtils.update_properties(obj)

    def execute(self, obj):
        radius = obj.OutsideDiameterAtFree / 2.0
        wire_radius = obj.WireDiameter / 2.0
        obj.Shape = CoreUtils.helix_solid(radius, obj.Pitch, obj.LengthAtFree, wire_radius)
        SpringUtils.update_globals(obj)
        SpringUtils.update_properties(obj)

    def onChanged(self, obj, prop):
        if prop == "EndType":
            selection = getattr(obj, "EndType", None)
            if isinstance(selection, (list, tuple)):
                selection = selection[0] if selection else None
                SpringUtils.update_globals(obj)
                SpringUtils.update_properties(obj)

def make():
    doc = FreeCAD.ActiveDocument
    if doc is None:
        return None
    obj = doc.addObject("Part::FeaturePython", "TorsionSpring")
    TorsionSpring(obj)
    doc.recompute()
    return obj
