import FreeCAD
from pathlib import Path

from .. import Utils as CoreUtils
from ..ViewProviderSpring import ViewProviderSpring
from . import Utils as SpringUtils

class CompressionSpring:
    def __init__(self, obj):
#        FreeCAD.Console.PrintMessage(f"[CompressionSpring.__init__] self={self} obj={obj}\n")
        CoreUtils.add_property(obj, "OutsideDiameterAtFree", 28, "App::PropertyFloat", "Independent")
        CoreUtils.add_property(obj, "WireDiameter", 2.8, "App::PropertyFloat", "Independent")
        CoreUtils.add_property(obj, "LengthAtFree", 80.0, "App::PropertyFloat", "Independent")
        CoreUtils.add_property(obj, "CoilsTotal", 10.0, "App::PropertyFloat", "Independent")
        CoreUtils.add_property(obj, "ForceAtDeflection1", 50.0, "App::PropertyFloat", "Independent")
        CoreUtils.add_property(obj, "ForceAtDeflection2", 190.0, "App::PropertyFloat", "Independent")

        CoreUtils.add_property(obj, "MeanDiameterAtFree", 0.0, "App::PropertyFloat", "Dependent", 1)
        CoreUtils.add_property(obj, "CoilsActive", 0.0, "App::PropertyFloat", "Dependent", 1)
        CoreUtils.add_property(obj, "Pitch", 0.0, "App::PropertyFloat", "Dependent", 1)
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
        CoreUtils.add_property(obj, "FactorOfSafetyAtCycleLife", 0.0, "App::PropertyFloat", "Dependent", 1)
        CoreUtils.add_property(obj, "CycleLife", 0.0, "App::PropertyFloat", "Dependent", 1)
        CoreUtils.add_property(obj, "PercentAvailableDeflection", 0.0, "App::PropertyFloat", "Dependent", 1)
        CoreUtils.add_property(obj, "Energy", 0.0, "App::PropertyFloat", "Dependent", 1)

        CoreUtils.add_property(obj, "SpringType", "Compression", "App::PropertyString", "Global")
        CoreUtils.add_property(obj, "PropCalcMethod", None, "App::PropertyEnumeration", "Global")
        CoreUtils.add_property(obj, "MaterialType", SpringUtils.MUSIC_WIRE_MATERIAL_TYPE, "App::PropertyString", "Global")
        CoreUtils.add_property(obj, "ASTMFedSpec", SpringUtils.MUSIC_WIRE_ASTM_FS + "/" + SpringUtils.MUSIC_WIRE_FEDSPEC, "App::PropertyString", "Global")
        CoreUtils.add_property(obj, "Process", "Cold Coiled", "App::PropertyString", "Global")
        CoreUtils.add_property(obj, "MaterialFile", "", "App::PropertyString", "Global", 2) # hidden
        CoreUtils.add_property(obj, "LifeCategory", None, "App::PropertyEnumeration", "Global")
        CoreUtils.add_property(obj, "Density", SpringUtils.MUSIC_WIRE_DENSITY, "App::PropertyFloat", "Global", 1)
        CoreUtils.add_property(obj, "TorsionModulus", SpringUtils.MUSIC_WIRE_SHEAR_MODULUS, "App::PropertyFloat", "Global", 1)
        CoreUtils.add_property(obj, "HotFactorKh", SpringUtils.MUSIC_WIRE_HOT_FACTOR_KH, "App::PropertyFloat", "Global", 1)
        CoreUtils.add_property(obj, "Tensile", 0.0, "App::PropertyFloat", "Global", 1)
        CoreUtils.add_property(obj, "PercentTensileEndurance", 0.0, "App::PropertyFloat", "Global", 1)
        CoreUtils.add_property(obj, "PercentTensileStatic", 0.0, "App::PropertyFloat", "Global", 1)
        CoreUtils.add_property(obj, "StressLimitEndurance", 0.0, "App::PropertyFloat", "Global", 1)
        CoreUtils.add_property(obj, "StressLimitStatic", 0.0, "App::PropertyFloat", "Global", 1)
        CoreUtils.add_property(obj, "EndType", None, "App::PropertyEnumeration", "Global")
        CoreUtils.add_property(obj, "CoilsInactive", 0.0, "App::PropertyFloat", "Global")
        CoreUtils.add_property(obj, "AddCoilsAtSolid", 0.0, "App::PropertyFloat", "Global")
        CoreUtils.add_property(obj, "CatalogName", "", "App::PropertyString", "Global", 2) # hidden
        CoreUtils.add_property(obj, "CatalogNumber", "", "App::PropertyString", "Global", 2) # hidden
        CoreUtils.add_property(obj, "tbase010", 0.254, "App::PropertyFloat", "Global", 2)  # hidden # set value = 0.010
        CoreUtils.add_property(obj, "tbase400", 10.160, "App::PropertyFloat", "Global", 2)  # hidden # set value = 0.400
        CoreUtils.add_property(obj, "const_term", 0.0, "App::PropertyFloat", "Global", 2) # hidden
        CoreUtils.add_property(obj, "slope_term", 0.0, "App::PropertyFloat", "Global", 2) # hidden
        CoreUtils.add_property(obj, "tensile_010", 1000.0 * SpringUtils.MUSIC_WIRE_T010, "App::PropertyFloat", "Global", 2) # hidden

        # Changing a primary property could set one or more secondary properties
        CoreUtils.reload_enum(obj, "Compression", "PropCalcMethod")
        CoreUtils.apply_enum_property_values(obj, "Compression", "PropCalcMethod")
        CoreUtils.reload_enum(obj, "Compression", "LifeCategory")
        CoreUtils.apply_enum_property_values(obj, "Compression", "LifeCategory")
        CoreUtils.reload_enum(obj, "Compression", "EndType")
        CoreUtils.apply_enum_property_values(obj, "Compression", "EndType")

        obj.Proxy = self
        ViewProviderSpring(obj.ViewObject)
        SpringUtils.update_globals(obj)
        SpringUtils.update_properties(obj)

    def execute(self, obj):
#        FreeCAD.Console.PrintMessage(f"[CompressionSpring.execute] self={self} obj={obj}\n")

        print("\nExecuting CompressionSpring Feature...")
        spring = SpringUtils.spring_solid(
            meanDiameter=28.0,
            wireDiameter=2.8,
            totalCoils=10.0,
            endType="closed & ground",
            freeLength=80.0
        )
        Part.show(spring)
        FreeCAD.ActiveDocument.ActiveObject.Label = "CompressionSpring"
        print("Compression spring solid created and displayed successfully.")

#        radius = obj.OutsideDiameterAtFree / 2.0
#        wire_radius = obj.WireDiameter / 2.0
#        end_type_selection = getattr(obj, "EndType", None)
#        end_type_index = SpringUtils.end_type_index(end_type_selection)
#        obj.Shape = SpringUtils.spring_solid(
#            end_type_index,
#            radius,
#            obj.LengthAtFree,
#            wire_radius,
#            getattr(obj, "CoilsTotal", None),
#            getattr(obj, "CoilsInactive", None),
#        )
        SpringUtils.update_globals(obj)
        SpringUtils.update_properties(obj)

    def onChanged(self, obj, prop):
#        FreeCAD.Console.PrintMessage(f"[CompressionSpring.onChanged] self={self} obj={obj} prop={prop}\n")
        if prop == "PropCalcMethod":
            selection = CoreUtils.enum_selection_value(getattr(obj, "PropCalcMethod", None))
            CoreUtils.apply_enum_property_values(obj, "Compression", "PropCalcMethod", selection)
            SpringUtils.update_globals(obj)
            SpringUtils.update_properties(obj)
        if prop == "LifeCategory":
            selection = CoreUtils.enum_selection_value(getattr(obj, "LifeCategory", None))
            CoreUtils.apply_enum_property_values(obj, "Compression", "LifeCategory", selection)
            SpringUtils.update_globals(obj)
            SpringUtils.update_properties(obj)
        if prop == "EndType":
            selection = CoreUtils.enum_selection_value(getattr(obj, "EndType", None))
            CoreUtils.apply_enum_property_values(obj, "Compression", "EndType", selection)
            SpringUtils.update_globals(obj)
            SpringUtils.update_properties(obj)

def make():
#    FreeCAD.Console.PrintMessage(f"[make]\n")
    doc = FreeCAD.ActiveDocument
    if doc is None:
        return None
    obj = doc.addObject("Part::FeaturePython", "CompressionSpring")
    CompressionSpring(obj)
    doc.recompute()
    return obj
