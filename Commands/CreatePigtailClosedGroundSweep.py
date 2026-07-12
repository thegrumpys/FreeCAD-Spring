import FreeCAD as App
import FreeCADGui as Gui
import Part
import math
import os
import traceback


class CreatePigtailClosedGroundSweep:
    def GetResources(self):
        return {
            "Pixmap": "pigtail-sweep.svg",
            "MenuText": "Pigtail C&G Sweep",
            "ToolTip": "Generate pigtail closed and ground springs from 5 to 25 total coils",
        }

    def Activated(self):
        doc = App.newDocument("PigtailClosedGroundSweep")

        print("=== Pigtail Closed & Ground Coil Sweep ===")
        self.print_debug_environment()

        od = 28.0
        wire = 2.8
        length = 80.0
        end_type = 10
        inactive = 2

        col_count = 4
        spacing_x = 52.0
        spacing_y = 115.0
        passed = 0
        failed = 0

        for index, coils in enumerate(range(5, 26)):
            x = (index % col_count) * spacing_x
            y = (index // col_count) * spacing_y
            placement = App.Vector(x, y, 0.0)
            label = f"PigtailClosedGround_Coils_{coils:02d}"

            self.add_reference_cylinder(doc, label, od, length, placement)

            try:
                print(
                    f"[CASE] {label}: od={od} wire={wire} length={length} "
                    f"coils={coils} end_type={end_type} inactive={inactive}"
                )
                shape = self.make_spring(od, wire, length, coils, end_type, inactive)
                raw_summary = self.validate_shape(label, shape, length, "raw")
                obj = doc.addObject("Part::Feature", label)
                obj.Label = label
                obj.Shape = shape
                obj.Placement.Base = placement
                self.apply_spring_style(obj)
                document_summary = self.validate_shape(label, obj.Shape, length, "document")

                passed += 1
                print(f"[PASS] {label}: raw={raw_summary}; document={document_summary}")
            except Exception as exc:
                failed += 1
                print(f"[FAIL] {label}: {type(exc).__name__}: {exc}")
                if self.tracebacks_enabled():
                    traceback.print_exc()

        doc.recompute()

        if Gui.ActiveDocument and Gui.ActiveDocument.ActiveView:
            Gui.ActiveDocument.ActiveView.fitAll()

        print("=== Pigtail Closed & Ground Coil Sweep Summary ===")
        print(f"Generated: {passed} passed, {failed} failed")

    def make_spring(self, od, wire, length, coils, end_type, inactive):
        import springocct

        return springocct.compression_spring_solid(
            od,
            wire,
            length,
            coils,
            end_type,
            inactive,
        )

    def print_debug_environment(self):
        keys = (
            "SPRING_DEBUG_ALL",
            "SPRING_DEBUG_BASIC",
            "SPRING_DEBUG_SWEEP",
            "SPRING_DEBUG_GROUNDING",
            "SPRING_DEBUG_PIGTAIL",
            "SPRING_DEBUG_TAPERED",
        )
        values = ", ".join(f"{key}={os.environ.get(key, '<unset>')}" for key in keys)
        print(f"[DEBUG_ENV_PYTHON] {values}")

        try:
            import springocct

            if hasattr(springocct, "debug_environment"):
                print(f"[DEBUG_ENV_CPP] {springocct.debug_environment()}")
            else:
                print("[DEBUG_ENV_CPP] springocct.debug_environment unavailable")
        except Exception as exc:
            print(f"[DEBUG_ENV_CPP] unavailable: {type(exc).__name__}: {exc}")

    def tracebacks_enabled(self):
        value = os.environ.get("SPRING_SWEEP_TRACEBACKS", "")
        return value not in ("", "0", "false", "FALSE", "off", "OFF", "no", "NO")

    def add_reference_cylinder(self, doc, label, od, length, placement):
        cylinder = doc.addObject("Part::Feature", f"{label}_Reference")
        cylinder.Label = f"{label}_Reference"
        cylinder.Shape = Part.makeCylinder(od / 2.0, length)
        cylinder.Placement.Base = placement

        if hasattr(cylinder, "ViewObject"):
            cylinder.ViewObject.DisplayMode = "Shaded"
            cylinder.ViewObject.ShapeColor = (0.72, 0.82, 0.92)
            cylinder.ViewObject.Transparency = 78
            cylinder.ViewObject.LineColor = (0.05, 0.05, 0.05)
            cylinder.ViewObject.LineWidth = 1.0

    def validate_shape(self, label, shape, length, source):
        if shape is None:
            raise RuntimeError(f"{label} returned no shape")
        if shape.isNull():
            raise RuntimeError(f"{label} returned a null shape")

        bbox = shape.BoundBox
        values = (
            bbox.XMin,
            bbox.XMax,
            bbox.YMin,
            bbox.YMax,
            bbox.ZMin,
            bbox.ZMax,
            bbox.XLength,
            bbox.YLength,
            bbox.ZLength,
        )
        if any(not math.isfinite(value) for value in values):
            raise RuntimeError(f"{label} {source} shape returned a non-finite bounding box: {self.describe_bounding_box(shape)}")
        if bbox.XLength <= 0.0 or bbox.YLength <= 0.0 or bbox.ZLength <= 0.0:
            raise RuntimeError(f"{label} {source} shape returned an empty bounding box: {self.describe_bounding_box(shape)}")

        tolerance = 0.01
        warnings = []
        if bbox.ZMin < -tolerance:
            warnings.append(f"below ground by {-bbox.ZMin:.3f}")
        if bbox.ZMax > length + tolerance:
            warnings.append(f"above free length by {bbox.ZMax - length:.3f}")
        if abs(bbox.ZLength - length) > tolerance:
            warnings.append(f"z length differs from free length by {bbox.ZLength - length:.3f}")
        summary = self.describe_bounding_box(shape)
        if warnings:
            print(f"[WARN] {label} {source}: {', '.join(warnings)}; {summary}")
        return summary

    def apply_spring_style(self, obj):
        if not hasattr(obj, "ViewObject"):
            return

        obj.ViewObject.DisplayMode = "Shaded"
        obj.ViewObject.Deviation = 0.05
        obj.ViewObject.AngularDeflection = 5.0
        obj.ViewObject.ShapeColor = (0.88, 0.78, 0.62)
        obj.ViewObject.LineColor = (0.15, 0.15, 0.15)
        obj.ViewObject.LineWidth = 1.0

    def describe_bounding_box(self, shape):
        bbox = shape.BoundBox
        return (
            f"Z={bbox.ZMin:.3f}..{bbox.ZMax:.3f} "
            f"size=({bbox.XLength:.3f}, {bbox.YLength:.3f}, {bbox.ZLength:.3f})"
        )

    def IsActive(self):
        return True


def register():
    Gui.addCommand("Spring_PigtailClosedGroundSweep", CreatePigtailClosedGroundSweep())
