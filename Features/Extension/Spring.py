import FreeCAD
from pathlib import Path

from .. import Utils as CoreUtils
from ..ViewProviderSpring import ViewProviderSpring
from . import Utils as SpringUtils

class ExtensionSpring:
    def __init__(self, obj):
        CoreUtils.add_property(obj, "OutsideDiameterAtFree", 20.0, "App::PropertyFloat", "Independent")
        CoreUtils.add_property(obj, "WireDiameter", 2.0, "App::PropertyFloat", "Independent")
        CoreUtils.add_property(obj, "CoilsTotal", 10, "App::PropertyFloat", "Independent")
        CoreUtils.add_property(obj, "LengthAtFree", 25.0, "App::PropertyFloat", "Independent")

        CoreUtils.add_property(obj, "Pitch", 2.5, "App::PropertyFloat", "Dependent")
        obj.setEditorMode("Pitch", 1)
        CoreUtils.add_property(obj, "Rate", 0.0, "App::PropertyFloat", "Dependent")
        obj.setEditorMode("Rate", 1)

#        CoreUtils.add_property(obj, "EndType", "", "App::PropertyEnumeration", "Global")
        CoreUtils.add_property(obj, "CoilsInactive", 0.0, "App::PropertyFloat", "Global")
        obj.setEditorMode("CoilsInactive", 1)
        CoreUtils.add_property(obj, "EndDiameter", 0.0, "App::PropertyFloat", "Global")
        obj.setEditorMode("EndDiameter", 1)
        CoreUtils.add_property(obj, "HookDeflectionAllowance", 0.0, "App::PropertyFloat", "Global")
        obj.setEditorMode("HookDeflectionAllowance", 1)
        CoreUtils.add_property(obj, "TorsionModulus", SpringUtils.MUSIC_WIRE_SHEAR_MODULUS, "App::PropertyFloat", "Global")

        obj.Proxy = self
        ViewProviderSpring(obj.ViewObject)
        SpringUtils.update_globals(obj)
        SpringUtils.update_properties(obj)

    def execute(self, obj):
        radius = obj.OutsideDiameterAtFree / 2.0
        wire_radius = obj.WireDiameter / 2.0
        end_type_selection = getattr(obj, "EndType", None)
        end_type = CoreUtils.enum_selection_value(end_type_selection)
        obj.Shape = SpringUtils.spring_solid(
            0,
            end_type,
            radius,
            obj.LengthAtFree,
            wire_radius,
            getattr(obj, "CoilsTotal", None),
        )
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
    obj = doc.addObject("Part::FeaturePython", "ExtensionSpring")
    ExtensionSpring(obj)
    doc.recompute()
    return obj
