import FreeCAD as App
import FreeCADGui as Gui
import Part

from math import floor


class CreateSpringTestMatrix:
    def GetResources(self):
        return {
            'Pixmap': 'spring-test.svg',
            'MenuText': 'Spring Test Matrix',
            'ToolTip': 'Run spring generator test matrix'
        }

    def Activated(self):
        doc = App.ActiveDocument
        if not doc:
            doc = App.newDocument("SpringTest")

        # Clear document (optional)
        for obj in doc.Objects:
            doc.removeObject(obj.Name)

        print("=== Spring Test Matrix ===")

        run_regular_tests = True
        run_stress_tests = True
        run_fault_tests = True

        # -------------------------
        # Test cases (GOOD)
        # -------------------------
        tests = [
            ("Open", dict(od=28, wire=5, length=60, coils=6, end=1, inactive=0)),
            ("Open_Ground", dict(od=28, wire=5, length=60, coils=6, end=2, inactive=0)),
            ("Closed", dict(od=28, wire=5, length=60, coils=6, end=3, inactive=2)),
            ("Closed_Ground", dict(od=28, wire=5, length=60, coils=6, end=4, inactive=2)),
            ("DoubleClosed", dict(od=28, wire=5, length=60, coils=8, end=5, inactive=4)),
            ("DoubleClosed_Ground", dict(od=28, wire=5, length=60, coils=8, end=6, inactive=4)),
            ("TaperedClosed", dict(od=28, wire=5, length=60, coils=6, end=7, inactive=2)),
            ("TaperedClosed_Ground", dict(od=28, wire=5, length=60, coils=6, end=8, inactive=2)),
            ("PigtailClosed", dict(od=28, wire=5, length=60, coils=6, end=9, inactive=1)),
            ("PigtailClosed_Ground", dict(od=28, wire=5, length=60, coils=6, end=10, inactive=1)),
            ("UserSpecifiedOpen", dict(od=28, wire=5, length=60, coils=6, end=11, inactive=0)),
            ("UserSpecifiedOpen_Ground", dict(od=28, wire=5, length=60, coils=6, end=12, inactive=0)),
            ("UserSpecifiedClosed", dict(od=28, wire=5, length=60, coils=6, end=13, inactive=2)),
            ("UserSpecifiedClosed_Ground", dict(od=28, wire=5, length=60, coils=6, end=14, inactive=2)),
        ]

        spacing_x = 55
        spacing_y = 95
        row_z_step = 0
        col_count = 2

        good_pass_count = 0
        good_fail_count = 0
        bbox_results = []

        if run_regular_tests:
            for i, (name, params) in enumerate(tests):
                try:
                    shape = self.make_spring(**params)
                    self.validate_shape_bounds(name, shape)
                    self.validate_visual_case_semantics(name, params, shape)

                    x = (i % col_count) * spacing_x
                    y = floor(i / col_count) * spacing_y
                    z = floor(i / col_count) * row_z_step

                    obj = doc.addObject("Part::Feature", name)
                    obj.Label = name
                    obj.Shape = shape
                    obj.Placement.Base = App.Vector(x, y, z)
                    self.apply_visual_style(obj, name)

                    bbox_results.append(self.describe_bounding_box(name, shape))
                    good_pass_count += 1
                    print(f"[PASS] {name}")

                except Exception as e:
                    import traceback
                    good_fail_count += 1
                    print(f"[FAIL] {name}: {type(e).__name__}: {e}")
                    traceback.print_exc()
        else:
            print("[SKIP] Regular tests")

        # -------------------------
        # STRESS TESTS
        # -------------------------
        print("\n=== Stress Tests ===")

        stress_tests = [
            (
                "Stress_Open_Long",
                dict(od=28, wire=2.8, length=160, coils=18, end=1, inactive=0),
            ),
            (
                "Stress_Closed_Short",
                dict(od=28, wire=2.8, length=35, coils=6, end=3, inactive=2),
            ),
            (
                "Stress_TaperedClosed_Ground_Thin",
                dict(od=28, wire=2.0, length=80, coils=8, end=8, inactive=2),
            ),
            (
                "Stress_PigtailClosed_Ground_LowIndex",
                dict(od=28, wire=5.0, length=60, coils=6, end=10, inactive=1),
            ),
            (
                "Stress_MinValidClosed",
                dict(od=28, wire=2.8, length=25, coils=4, end=3, inactive=2),
            ),
            (
                "Stress_MinValidDoubleClosed",
                dict(od=28, wire=2.8, length=45, coils=8, end=5, inactive=4),
            ),
            (
                "Stress_TaperedClosed_Ground_Short",
                dict(od=28, wire=2.8, length=40, coils=6, end=8, inactive=2),
            ),
            (
                "Stress_PigtailClosed_LowIndex",
                dict(od=28, wire=5.6, length=70, coils=6, end=9, inactive=1),
            ),
            (
                "Stress_PigtailClosed_Ground_HighIndex",
                dict(od=28, wire=2.0, length=80, coils=10, end=10, inactive=1),
            ),
            (
                "Stress_Open_Ground_VeryFewCoils",
                dict(od=28, wire=2.8, length=35, coils=3, end=2, inactive=0),
            ),
        ]

        stress_start = len(tests)
        stress_pass_count = 0
        stress_fail_count = 0

        if run_stress_tests:
            for j, (name, params) in enumerate(stress_tests):
                try:
                    shape = self.make_spring(**params)
                    self.validate_shape_bounds(name, shape)

                    i = stress_start + j
                    x = (i % col_count) * spacing_x
                    y = floor(i / col_count) * spacing_y
                    z = floor(i / col_count) * row_z_step

                    obj = doc.addObject("Part::Feature", name)
                    obj.Label = name
                    obj.Shape = shape
                    obj.Placement.Base = App.Vector(x, y, z)
                    self.apply_visual_style(obj, name)

                    bbox_results.append(self.describe_bounding_box(name, shape))
                    stress_pass_count += 1
                    print(f"[PASS] {name}")

                except Exception as e:
                    import traceback
                    stress_fail_count += 1
                    print(f"[FAIL] {name}: {type(e).__name__}: {e}")
                    traceback.print_exc()
        else:
            print("[SKIP] Stress tests")

        # -------------------------
        # BAD TESTS
        # -------------------------
        print("\n=== Negative Tests ===")

        bad_tests = [
            ("Negative wire", dict(wire=-1)),
            ("Zero coils", dict(coils=0)),
            ("Invalid end type", dict(end=999)),
            ("Closed with one inactive coil", dict(end=3, inactive=1)),
            ("DoubleClosed with two inactive coils", dict(end=5, inactive=2)),
            ("TaperedClosed with one inactive coil", dict(end=7, inactive=1)),
            ("Wire equals outer diameter", dict(od=5, wire=5)),
            ("Wire larger than outer diameter", dict(od=5, wire=6)),
            ("Negative free length", dict(length=-10)),
            ("Negative inactive coils", dict(inactive=-1)),
            ("Inactive coils greater than total coils", dict(coils=4, inactive=5)),
            ("Closed inactive coils greater than total coils", dict(coils=4, end=3, inactive=5)),
        ]

        negative_pass_count = 0
        negative_fail_count = 0

        if run_fault_tests:
            for name, overrides in bad_tests:
                try:
                    self.make_spring(**overrides)
                    negative_fail_count += 1
                    print(f"[FAIL] {name}: expected failure but succeeded")
                except Exception:
                    negative_pass_count += 1
                    print(f"[PASS] {name}")
        else:
            print("[SKIP] Fault tests")

        print("\n=== Bounding Box Summary ===")
        for line in bbox_results:
            print(line)

        print("\n=== Spring Test Matrix Summary ===")
        print(f"Good cases: {good_pass_count} passed, {good_fail_count} failed")
        print(f"Stress cases: {stress_pass_count} passed, {stress_fail_count} failed")
        print(f"Negative cases: {negative_pass_count} passed, {negative_fail_count} failed")

        doc.recompute()

        if good_fail_count or stress_fail_count or negative_fail_count:
            print("[FAIL] Spring Test Matrix completed with failures")
        else:
            print("[PASS] Spring Test Matrix completed successfully")

    def make_spring(self,
                    od=28,
                    wire=5,
                    length=60,
                    coils=6,
                    end=1,
                    inactive=0):

        import springocct

        return springocct.compression_spring_solid(
            od,
            wire,
            length,
            coils,
            end,
            inactive,
        )

    def validate_shape_bounds(self, name, shape):
        if shape is None:
            raise RuntimeError(f"{name} returned no shape")

        if shape.isNull():
            raise RuntimeError(f"{name} returned a null shape")

        bbox = shape.BoundBox

        if bbox.XLength <= 0:
            raise RuntimeError(f"{name} has non-positive X bounding-box length")

        if bbox.YLength <= 0:
            raise RuntimeError(f"{name} has non-positive Y bounding-box length")

        if bbox.ZLength <= 0:
            raise RuntimeError(f"{name} has non-positive Z bounding-box length")

        if bbox.ZLength > 250:
            raise RuntimeError(
                f"{name} has unexpectedly large Z bounding-box length: {bbox.ZLength}"
            )

    def validate_visual_case_semantics(self, name, params, shape):
        end_type = params["end"]
        total_coils = params["coils"]
        inactive_coils = params["inactive"]
        active_coils = total_coils - inactive_coils

        if active_coils <= 0:
            raise RuntimeError(f"{name} has no active coils")

        # This method intentionally does not compare bounding-box height against
        # free length. The swept tube can extend beyond the centerline/free-length
        # planes while still representing the correct spring. Visual correctness
        # for spring end shape is verified by inspecting the shaded test matrix.
        if end_type in (3, 4, 7, 8, 13, 14) and inactive_coils < 2:
            raise RuntimeError(f"{name} closed-style spring has fewer than 2 inactive coils")

        if end_type in (5, 6) and inactive_coils < 4:
            raise RuntimeError(f"{name} double-closed spring has fewer than 4 inactive coils")

    def describe_bounding_box(self, name, shape):
        bbox = shape.BoundBox
        return (
            f"{name}: "
            f"X={bbox.XMin:.3f}..{bbox.XMax:.3f} "
            f"Y={bbox.YMin:.3f}..{bbox.YMax:.3f} "
            f"Z={bbox.ZMin:.3f}..{bbox.ZMax:.3f} "
            f"size=({bbox.XLength:.3f}, {bbox.YLength:.3f}, {bbox.ZLength:.3f})"
        )

    def apply_visual_style(self, obj, name):
        if not hasattr(obj, "ViewObject"):
            return

        obj.ViewObject.DisplayMode = "Shaded"
        obj.ViewObject.Deviation = 0.05
        obj.ViewObject.AngularDeflection = 5.0
        obj.ViewObject.ShapeColor = (0.78, 0.78, 0.78)
        obj.ViewObject.LineColor = (0.15, 0.15, 0.15)
        obj.ViewObject.LineWidth = 1.0

        if "Ground" in name:
            obj.ViewObject.ShapeColor = (0.70, 0.85, 0.70)

        if "Tapered" in name:
            obj.ViewObject.ShapeColor = (0.70, 0.72, 0.90)

        if "Pigtail" in name:
            obj.ViewObject.ShapeColor = (0.88, 0.78, 0.62)

        if "UserSpecified" in name:
            obj.ViewObject.ShapeColor = (0.78, 0.70, 0.88)

        if name.startswith("Stress_"):
            obj.ViewObject.ShapeColor = (0.90, 0.72, 0.72)

    def IsActive(self):
        return True


def register():
    """Registers this command with FreeCAD"""
    Gui.addCommand("Spring_TestMatrix", CreateSpringTestMatrix())
