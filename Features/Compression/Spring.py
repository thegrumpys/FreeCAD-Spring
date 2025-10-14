import FreeCAD
from pathlib import Path

from .. import Utils as CoreUtils
from ..ViewProviderSpring import ViewProviderSpring
from . import Utils as SpringUtils

class CompressionSpring:
    def __init__(self, obj):
#        FreeCAD.Console.PrintMessage("CompressionSpring.__init__"+" self="+str(self)+" obj="+str(obj)+"\n")
        CoreUtils.add_property(obj, "OutsideDiameterAtFree", 28, "App::PropertyFloat", "Independent")
        CoreUtils.add_property(obj, "WireDiameter", 2.8, "App::PropertyFloat", "Independent")
        CoreUtils.add_property(obj, "LengthAtFree", 80.0, "App::PropertyFloat", "Independent")
        CoreUtils.add_property(obj, "CoilsTotal", 10.0, "App::PropertyFloat", "Independent")
        CoreUtils.add_property(obj, "ForceAtDeflection1", 50.0, "App::PropertyFloat", "Independent")
        CoreUtils.add_property(obj, "ForceAtDeflection2", 190.0, "App::PropertyFloat", "Independent")

        CoreUtils.add_property(obj, "MeanDiameter", 0.0, "App::PropertyFloat", "Dependent", 1)
        CoreUtils.add_property(obj, "CoilsActive", 0.0, "App::PropertyFloat", "Dependent", 1)
        CoreUtils.add_property(obj, "Rate", 0.0, "App::PropertyFloat", "Dependent", 1)
        CoreUtils.add_property(obj, "Deflection1", 0.0, "App::PropertyFloat", "Dependent", 1)
        CoreUtils.add_property(obj, "Deflection2", 0.0, "App::PropertyFloat", "Dependent", 1)
        CoreUtils.add_property(obj, "LengthAtDeflection1", 0.0, "App::PropertyFloat", "Dependent", 1)
        CoreUtils.add_property(obj, "LengthAtDeflection2", 0.0, "App::PropertyFloat", "Dependent", 1)
        CoreUtils.add_property(obj, "LengthStroke", 0.0, "App::PropertyFloat", "Dependent", 1)
        CoreUtils.add_property(obj, "LengthAtSolid", 0.0, "App::PropertyFloat", "Dependent", 1)
        CoreUtils.add_property(obj, "Slenderness", 0.0, "App::PropertyFloat", "Dependent", 1)
        CoreUtils.add_property(obj, "InsideDiameterAtFree", 0.0, "App::PropertyFloat", "Dependent", 1)
        CoreUtils.add_property(obj, "Weight", 0.0, "App::PropertyFloat", "Dependent", 1)
        CoreUtils.add_property(obj, "SpringIndex", 0.0, "App::PropertyFloat", "Dependent", 1)
        CoreUtils.add_property(obj, "ForceAtFree", 0.0, "App::PropertyFloat", "Dependent", 1)
        CoreUtils.add_property(obj, "ForceAtSolid", 0.0, "App::PropertyFloat", "Dependent", 1)
        CoreUtils.add_property(obj, "StressAtDeflection1", 0.0, "App::PropertyFloat", "Dependent", 1)
        CoreUtils.add_property(obj, "StressAtDeflection2", 0.0, "App::PropertyFloat", "Dependent", 1)
        CoreUtils.add_property(obj, "StressAtSolid", 0.0, "App::PropertyFloat", "Dependent", 1)
        CoreUtils.add_property(obj, "FactorOfSafetyAtDeflection2", 0.0, "App::PropertyFloat", "Dependent", 1)
        CoreUtils.add_property(obj, "FactorOfSafetyAtSolid", 0.0, "App::PropertyFloat", "Dependent", 1)
        CoreUtils.add_property(obj, "FactorOfSafetyCycleLife", 0.0, "App::PropertyFloat", "Dependent", 1)
        CoreUtils.add_property(obj, "CycleLife", 0.0, "App::PropertyFloat", "Dependent", 1)
        CoreUtils.add_property(obj, "PercentAvailableDeflection", 0.0, "App::PropertyFloat", "Dependent", 1)
        CoreUtils.add_property(obj, "Energy", 0.0, "App::PropertyFloat", "Dependent", 1)

        CoreUtils.add_property(obj, "SpringType", "Compression", "App::PropertyString", "Global")
        CoreUtils.add_property(obj, "PropCalcMethod", None, "App::PropertyEnumeration", "Global")
        CoreUtils.reload_enum(obj, "Compression", "PropCalcMethod")
        CoreUtils.add_property(obj, "MaterialType", SpringUtils.MUSIC_WIRE_MATERIAL_TYPE, "App::PropertyString", "Global")
        CoreUtils.add_property(obj, "ASTMFedSpec", SpringUtils.MUSIC_WIRE_ASTM_FS + "/" + SpringUtils.MUSIC_WIRE_FEDSPEC, "App::PropertyString", "Global")
        CoreUtils.add_property(obj, "Process", "Cold Coiled", "App::PropertyString", "Global")
        CoreUtils.add_property(obj, "MaterialFile", "", "App::PropertyString", "Global", 2) # hidden
        CoreUtils.add_property(obj, "LifeCategory", None, "App::PropertyEnumeration", "Global")
        CoreUtils.reload_enum(obj, "Compression", "LifeCategory")
        CoreUtils.add_property(obj, "Density", SpringUtils.MUSIC_WIRE_DENSITY, "App::PropertyFloat", "Global")
        CoreUtils.add_property(obj, "TorsionModulus", SpringUtils.MUSIC_WIRE_SHEAR_MODULUS, "App::PropertyFloat", "Global")
        CoreUtils.add_property(obj, "HotFactorKh", SpringUtils.MUSIC_WIRE_HOT_FACTOR_KH, "App::PropertyFloat", "Global")
        CoreUtils.add_property(obj, "Tensile", 0.0, "App::PropertyFloat", "Global")
        CoreUtils.add_property(obj, "PercentTensileEndurance", 0.0, "App::PropertyFloat", "Global")
        CoreUtils.add_property(obj, "PercentTensileStatic", 0.0, "App::PropertyFloat", "Global")
        CoreUtils.add_property(obj, "StressLimitEndurance", 0.0, "App::PropertyFloat", "Global")
        CoreUtils.add_property(obj, "StressLimitStatic", 0.0, "App::PropertyFloat", "Global")
        CoreUtils.add_property(obj, "EndType", None, "App::PropertyEnumeration", "Global")
        CoreUtils.reload_enum(obj, "Compression", "EndType")
        CoreUtils.add_property(obj, "CoilsInactive", 0.0, "App::PropertyFloat", "Global")
        CoreUtils.add_property(obj, "AddCoilsAtSolid", 0.0, "App::PropertyFloat", "Global")
        CoreUtils.add_property(obj, "CatalogName", "", "App::PropertyString", "Global")
        CoreUtils.add_property(obj, "CatalogNumber", "", "App::PropertyString", "Global")
        CoreUtils.add_property(obj, "tbase010", 0.0, "App::PropertyFloat", "Global")
        CoreUtils.add_property(obj, "tbase400", 0.0, "App::PropertyFloat", "Global")
        CoreUtils.add_property(obj, "const_term", 0.0, "App::PropertyFloat", "Global")
        CoreUtils.add_property(obj, "slope_term", 0.0, "App::PropertyFloat", "Global")
        CoreUtils.add_property(obj, "tensile_010", 1000.0 * SpringUtils.MUSIC_WIRE_T010, "App::PropertyFloat", "Global")

        obj.Proxy = self
        ViewProviderSpring(obj.ViewObject)
        SpringUtils.update_globals(obj)
        SpringUtils.update_properties(obj)

    def execute(self, obj):
#        FreeCAD.Console.PrintMessage("CompressionSpring.execute"+" self="+str(self)+" obj="+str(obj)+"\n")
        radius = obj.OutsideDiameterAtFree / 2.0
        wire_radius = obj.WireDiameter / 2.0
        pitch = (obj.LengthAtFree - obj.WireDiameter) / obj.CoilsActive # Depends upon EndType - this is for "Open"
        obj.Shape = CoreUtils.helix_solid(radius, pitch, obj.LengthAtFree, wire_radius)
        SpringUtils.update_globals(obj)
        SpringUtils.update_properties(obj)

    def onChanged(self, obj, prop):
#        FreeCAD.Console.PrintMessage("CompressionSpring.execute"+" self="+str(self)+" obj="+str(obj)+"\n")
        if prop == "EndType":
            selection = getattr(obj, "EndType", None)
            if isinstance(selection, (list, tuple)):
                selection = selection[0] if selection else None
                SpringUtils.update_globals(obj)
                SpringUtils.update_properties(obj)


def make():
#    FreeCAD.Console.PrintMessage("make"+"\n")
    doc = FreeCAD.ActiveDocument
    if doc is None:
        return None
    obj = doc.addObject("Part::FeaturePython", "CompressionSpring")
    CompressionSpring(obj)
    doc.recompute()
    return obj
