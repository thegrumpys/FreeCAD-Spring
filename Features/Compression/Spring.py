import importlib
import importlib.util
import sys

import FreeCAD, Part

from .. import Utils as CoreUtils
from ..ViewProviderSpring import ViewProviderSpring
from . import Utils as SpringUtils

try:
    import springocct
except ImportError as exc:
    springocct = None
    FreeCAD.Console.PrintError(f"springocct unavailable: {exc}\n")

def _log_console(message: str) -> None:
    FreeCAD.Console.PrintMessage(message)
    try:
        print(message, end="")
    except Exception:
        pass


_SPRINGCPP = sys.modules.get("SpringCpp")
if _SPRINGCPP is None:
    _spec = importlib.util.find_spec("SpringCpp")
    if _spec is not None:
        origin = getattr(_spec, "origin", None)
        locations = getattr(_spec, "submodule_search_locations", None)
        _log_console(
            f"[CompressionSpring] Importing SpringCpp binding for diagnostics. "
            f"origin={origin!r} locations={list(locations) if locations else None}\n"
        )
        try:
            _SPRINGCPP = importlib.import_module("SpringCpp")
        except ImportError as exc:
            _SPRINGCPP = None
            _log_console(
                f"[CompressionSpring] SpringCpp binding import failed. error={exc!r}\n"
            )
        else:
            module_file = getattr(_SPRINGCPP, "__file__", None)
            has_log = hasattr(_SPRINGCPP, "log_target_platform")
            _log_console(
                f"[CompressionSpring] SpringCpp binding import completed. "
                f"file={module_file!r} has_log_target_platform={has_log}\n"
            )
    else:
        preview_path = ":".join(sys.path[:5])
        _log_console(
            f"[CompressionSpring] SpringCpp binding not available. "
            f"First sys.path entries: {preview_path}\n"
        )
else:
    module_file = getattr(_SPRINGCPP, "__file__", None)
    _log_console(
        f"[CompressionSpring] SpringCpp binding already loaded; skipping import. "
        f"file={module_file!r}\n"
    )

if _SPRINGCPP is not None and not hasattr(_SPRINGCPP, "log_target_platform"):
    attrs = sorted(getattr(_SPRINGCPP, "__dict__", {}).keys())
    preview_attrs = ", ".join(attrs[:5])
    _log_console(
        f"[CompressionSpring] SpringCpp module loaded but missing 'log_target_platform'. "
        f"attrs sample: {preview_attrs}\n"
    )

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
        FreeCAD.Console.PrintMessage(f"[CompressionSpring.execute] self={self} obj={obj}\n")

        print("\nExecuting CompressionSpring Feature...")
        if _SPRINGCPP is not None and hasattr(_SPRINGCPP, "log_target_platform"):
            platform_name = _SPRINGCPP.log_target_platform()
            FreeCAD.Console.PrintMessage(
                f"[CompressionSpring.execute] SpringCpp target platform: {platform_name}\\n"
            )
        spring = springocct.compression_spring_solid(
            outer_diameter_in=1.1,
            wire_diameter_in=0.1055,
            free_length_in=3.25,
            total_coils=16.0,
            end_type=3, # Closed
            level_of_detail=20,
        )
        FreeCAD.Console.PrintMessage(
            "springocct compression_spring_solid: "
            f"return: {spring}\n"
        )
        obj.Shape = spring
        # FreeCAD.ActiveDocument.ActiveObject can be None when recomputing the object,
        # so set the label directly on the feature instead of assuming an active object.
        obj.Label = "CompressionSpring"
        print("Compression spring solid created and displayed successfully.")

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
