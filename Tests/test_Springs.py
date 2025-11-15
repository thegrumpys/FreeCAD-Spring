import unittest
import math
import os
import tempfile
from types import SimpleNamespace

import pytest

try:  # pragma: no cover - exercised only when FreeCAD is unavailable
    import FreeCAD  # type: ignore
    import Part  # type: ignore
except ModuleNotFoundError as exc:  # pragma: no cover - depends on optional FreeCAD
    pytest.skip(f"FreeCAD runtime unavailable: {exc}", allow_module_level=True)

from Features.Compression import Spring as CompressionSpring
from Features.Compression import Utils as CompressionUtils
from Features.Extension import Spring as ExtensionSpring
from Features.Extension import Utils as ExtensionUtils
from Features.Torsion import Spring as TorsionSpring
from Features.Torsion import Utils as TorsionUtils

def _expected_compression_rate(outer_diameter, wire_diameter, coils):
    obj = SimpleNamespace(
        OutsideDiameterAtFree=outer_diameter,
        WireDiameter=wire_diameter,
        CoilsTotal=coils,
        TorsionModulus=CompressionUtils.MUSIC_WIRE_SHEAR_MODULUS,
        Rate=0.0,
    )
    CompressionUtils.update_properties(obj)
    return obj.Rate


def _expected_extension_rate(outer_diameter, wire_diameter, coils):
    obj = SimpleNamespace(
        OutsideDiameterAtFree=outer_diameter,
        WireDiameter=wire_diameter,
        CoilsTotal=coils,
        TorsionModulus=ExtensionUtils.MUSIC_WIRE_SHEAR_MODULUS,
        Rate=0.0,
    )
    ExtensionUtils.update_properties(obj)
    return obj.Rate


def _expected_torsion_rate(outer_diameter, wire_diameter, coils):
    obj = SimpleNamespace(
        OutsideDiameterAtFree=outer_diameter,
        WireDiameter=wire_diameter,
        CoilsTotal=coils,
        ElasticModulus=TorsionUtils.MUSIC_WIRE_YOUNG_MODULUS,
        Rate=0.0,
    )
    TorsionUtils.update_properties(obj)
    return obj.Rate


print("✅ test_Springs.py started")

# -----------------------------------------------------------------------------
# Utility helpers
# -----------------------------------------------------------------------------
def _export_shape(shape, name):
    """Export shape to temp folder as BREP + STEP."""
    tmpdir = os.path.join(tempfile.gettempdir(), "SpringTests")
    os.makedirs(tmpdir, exist_ok=True)
    brep_path = os.path.join(tmpdir, f"{name}.brep")
    step_path = os.path.join(tmpdir, f"{name}.stp")
    try:
        shape.exportBrep(brep_path)
        shape.exportStep(step_path)
        print(f"📦 Exported {name}: {brep_path}, {step_path}")
    except Exception as e:
        print(f"⚠️ Export failed for {name}: {e}")
    return tmpdir


def _check_shape_valid(shape):
    """Return True if solid is valid and watertight."""
    assert shape.isValid(), "Shape invalid"
    assert not shape.isNull(), "Shape is null"
    for face in shape.Faces:
        assert face.Surface is not None, "Face has no surface"
    return True


def _check_properties(obj, expect):
    """Verify that spring parameters match expectations."""
    for k, v in expect.items():
        if hasattr(obj, k):
            got = getattr(obj, k)
            if hasattr(got, "Value"):  # PropertyFloat or similar
                got = got.Value
            assert abs(got - v) < 1e-6 or isinstance(v, str), f"{k} mismatch: {got} != {v}"


# -----------------------------------------------------------------------------
# Test class
# -----------------------------------------------------------------------------
class TestSpring(unittest.TestCase):
    def setUp(self):
        self.doc = FreeCAD.newDocument("SpringTest")

    def tearDown(self):
        FreeCAD.closeDocument(self.doc.Name)

    def _analyze_spring(self, obj, expected):
        """General geometry and parametric checks."""
        s = obj.Shape
        self.assertTrue(_check_shape_valid(s))
        self.assertGreater(s.Volume, 0, "Volume should be positive")
        bb = s.BoundBox
        self.assertAlmostEqual(bb.ZLength, expected["LengthAtFree"], delta=max(1.0, expected["WireDiameter"] * 3))

        coils_calc = expected["LengthAtFree"] / expected["Pitch"]
        circumference = math.pi * expected["OutsideDiameterAtFree"]
        length_per_turn = math.sqrt(circumference ** 2 + expected["Pitch"] ** 2)
        total_length = coils_calc * length_per_turn
        self.assertGreater(total_length, 0)
        print(f"✅ {obj.Name}: coils={coils_calc:.2f}, wire≈{total_length:.1f} mm, volume={s.Volume:.1f}")

        _check_properties(obj, expected)
        _export_shape(s, obj.Name)

    # -------------------------------------------------------------------------
    # Tests
    # -------------------------------------------------------------------------
    def test_compression_spring(self):
        spring = CompressionSpring.make()
        self.doc.recompute()
        self._analyze_spring(spring, {
            "OutsideDiameterAtFree": 20.0,
            "WireDiameter": 2.0,
            "Pitch": 2.5,
            "LengthAtFree": 25.0,
            "CoilsTotal": 10.0,
            "TorsionModulus": CompressionUtils.MUSIC_WIRE_SHEAR_MODULUS,
            "Rate": _expected_compression_rate(20.0, 2.0, 10.0)
        })

    def test_extension_spring(self):
        spring = ExtensionSpring.make()
        self.doc.recompute()
        self._analyze_spring(spring, {
            "OutsideDiameterAtFree": 20.0,
            "WireDiameter": 2.0,
            "Pitch": 2.5,
            "LengthAtFree": 25.0,
            "CoilsTotal": 10.0,
            "TorsionModulus": ExtensionUtils.MUSIC_WIRE_SHEAR_MODULUS,
            "Rate": _expected_extension_rate(20.0, 2.0, 10.0)
        })

    def test_torsion_spring(self):
        spring = TorsionSpring.make()
        self.doc.recompute()
        self._analyze_spring(spring, {
            "OutsideDiameterAtFree": 20.0,
            "WireDiameter": 2.0,
            "Pitch": 2.5,
            "LengthAtFree": 25.0,
            "CoilsTotal": 10.0,
            "ElasticModulus": TorsionUtils.MUSIC_WIRE_YOUNG_MODULUS,
            "Rate": _expected_torsion_rate(20.0, 2.0, 10.0)
        })

    def test_end_type_secondary_properties(self):
        spring = CompressionSpring.make()
        self.doc.recompute()
        end_type = getattr(spring, "EndType", None)
        if isinstance(end_type, (list, tuple)):
            end_type = end_type[0] if end_type else None
        self.assertEqual(end_type, "Open")
        self.assertTrue(hasattr(spring, "CoilsInactive"))
        self.assertAlmostEqual(getattr(spring, "CoilsInactive", 0.0), 0.0)
        self.assertTrue(hasattr(spring, "AddCoilsAtSolid"))
        self.assertAlmostEqual(getattr(spring, "AddCoilsAtSolid", 0.0), 1.0)

        spring.EndType = "Closed"
        self.doc.recompute()
        self.assertAlmostEqual(getattr(spring, "CoilsInactive", 0.0), 2.0)
        self.assertAlmostEqual(getattr(spring, "AddCoilsAtSolid", 0.0), 1.0)

        spring.EndType = "Open&Ground"
        self.doc.recompute()
        self.assertAlmostEqual(getattr(spring, "CoilsInactive", 0.0), 0.0)
        self.assertAlmostEqual(getattr(spring, "AddCoilsAtSolid", 0.0), 0.0)

    def test_open_variants_have_no_closed_coils(self):
        spring = CompressionSpring.make()
        spring.CoilsTotal = 8.0
        spring.LengthAtFree = 24.0

        # Plain open ends
        spring.EndType = "Open"
        self.doc.recompute()
        shape = spring.Shape
        self.assertAlmostEqual(shape.BoundBox.ZLength, spring.LengthAtFree, places=6)

        # Open & Ground should behave the same with no additional inactive coils.
        spring.EndType = "Open&Ground"
        self.doc.recompute()
        shape = spring.Shape
        self.assertAlmostEqual(shape.BoundBox.ZLength, spring.LengthAtFree, places=6)

    def test_parametric_sweep(self):
        """Generate multiple springs across diameters/pitches to ensure robustness."""
        for d in [10.0, 15.0, 25.0]:
            for p in [1.5, 2.5, 3.5]:
                h = p * 10
                spring = CompressionSpring.make()
                spring.OutsideDiameterAtFree = d
                spring.Pitch = p
                spring.LengthAtFree = h
                self.doc.recompute()
                self._analyze_spring(spring, {
                    "OutsideDiameterAtFree": d,
                    "WireDiameter": 2.0,
                    "Pitch": p,
                    "LengthAtFree": h
                })

print("✅ Entering unittest.main() ...")
unittest.main(module=None, verbosity=2)
