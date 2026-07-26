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
#    FreeCAD.Console.PrintError(f"springocct unavailable: {exc}\n")

# Display-only tessellation workaround.
#
# Tight compression springs can render with missing visual sections when FreeCAD's
# default Part view deviation is used. The generated BRep can still be valid; the
# failure is in the display mesh being too coarse for low spring-index geometry,
# especially around spring index 3. Keep the tighter mesh local to that region.
DEFAULT_VIEW_DEVIATION = 0.5
DEFAULT_VIEW_ANGULAR_DEFLECTION = 28.5
MIN_VIEW_QUALITY_SPRING_INDEX = 3.0
MAX_VIEW_QUALITY_SPRING_INDEX = 4.0
MIN_VIEW_DEVIATION = 0.05
MIN_VIEW_ANGULAR_DEFLECTION = 10.0

def _log_console(message: str) -> None:
#    FreeCAD.Console.PrintMessage(message)
    try:
        print(message, end="")
    except Exception:
        pass

def _spring_index_view_quality_targets(spring_index):
    if spring_index <= MIN_VIEW_QUALITY_SPRING_INDEX:
        return MIN_VIEW_DEVIATION, MIN_VIEW_ANGULAR_DEFLECTION
    if spring_index >= MAX_VIEW_QUALITY_SPRING_INDEX:
        return DEFAULT_VIEW_DEVIATION, DEFAULT_VIEW_ANGULAR_DEFLECTION

    index_span = MAX_VIEW_QUALITY_SPRING_INDEX - MIN_VIEW_QUALITY_SPRING_INDEX
    ratio = (spring_index - MIN_VIEW_QUALITY_SPRING_INDEX) / index_span
    return (
        MIN_VIEW_DEVIATION + ratio * (DEFAULT_VIEW_DEVIATION - MIN_VIEW_DEVIATION),
        MIN_VIEW_ANGULAR_DEFLECTION
        + ratio * (DEFAULT_VIEW_ANGULAR_DEFLECTION - MIN_VIEW_ANGULAR_DEFLECTION),
    )

def _as_float(value):
    try:
        return float(value)
    except Exception:
        return float(getattr(value, "Value"))

def _set_view_numeric_property(vobj, name, target):
    if not hasattr(vobj, name):
        return False

    try:
        current = _as_float(getattr(vobj, name))
    except Exception:
        return False

    if abs(current - target) <= 1e-9:
        return False

    setattr(vobj, name, target)
    return True

def _apply_spring_index_view_quality(obj):
    try:
        spring_index = float(getattr(obj, "SpringIndex", 0.0))
        vobj = obj.ViewObject
    except Exception:
        return

    target_deviation, target_angular = _spring_index_view_quality_targets(spring_index)
    changed_deviation = _set_view_numeric_property(vobj, "Deviation", target_deviation)
    changed_angular = _set_view_numeric_property(vobj, "AngularDeflection", target_angular)

    if changed_deviation or changed_angular:
        FreeCAD.Console.PrintMessage(
            "[Spring View] "
            f"SpringIndex={spring_index:g}; "
            f"Deviation={getattr(vobj, 'Deviation', None)} "
            f"AngularDeflection={getattr(vobj, 'AngularDeflection', None)}\n"
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
        CoreUtils.add_property(obj, "GrindAmount", 0.0, "App::PropertyFloat", "Global")
        CoreUtils.add_property(obj, "ClosedReduction", 0.0, "App::PropertyFloat", "Global")
        CoreUtils.add_property(obj, "CatalogName", "", "App::PropertyString", "Global", 2) # hidden
        CoreUtils.add_property(obj, "CatalogNumber", "", "App::PropertyString", "Global", 2) # hidden
        CoreUtils.add_property(obj, "tbase010", 0.254, "App::PropertyFloat", "Global", 2)  # hidden # set value = 0.010
        CoreUtils.add_property(obj, "tbase400", 10.160, "App::PropertyFloat", "Global", 2)  # hidden # set value = 0.400
        CoreUtils.add_property(obj, "const_term", 0.0, "App::PropertyFloat", "Global", 2) # hidden
        CoreUtils.add_property(obj, "slope_term", 0.0, "App::PropertyFloat", "Global", 2) # hidden
        CoreUtils.add_property(obj, "tensile_010", 1000.0 * SpringUtils.MUSIC_WIRE_T010, "App::PropertyFloat", "Global", 2) # hidden
        CoreUtils.ensure_alert_properties(obj)

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
        _apply_spring_index_view_quality(obj)
        CoreUtils.update_basic_alerts(obj)

    def execute(self, obj):
#        FreeCAD.Console.PrintMessage(f"[CompressionSpring.execute] self={self} obj={obj}\n")
        # Validate primary inputs first. Derived values still describe the
        # previous recompute at this point and must not reject the new inputs.
        CoreUtils.update_basic_alerts(obj, include_derived=False)
        CoreUtils.refresh_alert_panel_for(obj)
        CoreUtils.raise_for_alert_errors(obj)

        # Refresh dependent values before shape generation.  The OCCT sweep can
        # fail for otherwise valid inputs; derived properties such as
        # CoilsActive must still reflect the user's latest values in that case.
        SpringUtils.update_globals(obj)
        SpringUtils.update_properties(obj)
        _apply_spring_index_view_quality(obj)

        # Now validate the freshly calculated derived values, including solid
        # length, before asking OCCT to construct the shape.
        CoreUtils.update_basic_alerts(obj)
        CoreUtils.refresh_alert_panel_for(obj)
        CoreUtils.raise_for_alert_errors(obj)

        try:
            spring = springocct.compression_spring_solid(
                outer_diameter=obj.OutsideDiameterAtFree,
                wire_diameter=obj.WireDiameter,
                free_length=obj.LengthAtFree,
                total_coils=obj.CoilsTotal,
                end_type=SpringUtils.end_type_index(getattr(obj, "EndType", None)),
                inactive_coils=obj.CoilsInactive,
            )
        except Exception as e:
            raise
#        FreeCAD.Console.PrintMessage("springocct compression_spring_solid: " f"return: {spring}\n")
        obj.Shape = spring
#        print("Compression spring solid created and displayed successfully.")

        CoreUtils.update_basic_alerts(obj)
        CoreUtils.refresh_alert_panel_for(obj)

    def onChanged(self, obj, prop):
#        FreeCAD.Console.PrintMessage(f"[CompressionSpring.onChanged] self={self} obj={obj} prop={prop}\n")
        if prop in ("Shape", "AlertErrors", "AlertWarnings", "AlertInfos"):
            return
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
        CoreUtils.update_basic_alerts(obj)
        CoreUtils.refresh_alert_panel_for(obj)
        CoreUtils.recompute_for_alert_state(obj)

    def getAlerts(self, obj):
        CoreUtils.update_basic_alerts(obj)
        return {
            "errors": list(getattr(obj, "AlertErrors", [])),
            "warnings": list(getattr(obj, "AlertWarnings", [])),
            "infos": list(getattr(obj, "AlertInfos", [])),
        }

def make():
#    FreeCAD.Console.PrintMessage(f"[make]\n")
    doc = FreeCAD.ActiveDocument
    if doc is None:
        return None
    obj = doc.addObject("Part::FeaturePython", "CompressionSpring")
    CompressionSpring(obj)
    doc.recompute()
    return obj
