"""Utilities specific to compression springs."""

from __future__ import annotations

import FreeCAD, Part, math

from .. import Utils as CoreUtils

from FreeCAD import Vector, Rotation

#    ["matnam",        "astm_fs",   "fedspec","Density",  "ee",   "gg", "kh","t010","t400","pte1","pte2","pte3","pte4","pte6","pte7","pte8","ptb1","ptb2","ptb3","ptb4","ptb6","ptb7","ptb8", "ptb1sr", "ptb1nosr", "ptb2sr", "ptb3sr", "silf", "sihf", "sisr", "wire_dia_filename", "od_free_filename", "dumyc", "longnam"],
#    ["MUSIC_WIRE",      "A228",    "QQW-470",  0.00786, 207.0, 79.293, 1.00,  2.55,  1.38,    50,    36,    33,    30,    42,    39,    36,    75,    51,    47,    45,     0,     0,     0,       85,        100,       53,       50, 188.92, 310.28, 399.91, "wire_dia_metric",   "od_free_metric",       1,   "Music Wire  (all coatings) -                     ASTM A-228 "],

MUSIC_WIRE_MATERIAL_TYPE = "MUSIC_WIRE"
MUSIC_WIRE_ASTM_FS = "A228"
MUSIC_WIRE_FEDSPEC = "QQW-470"
MUSIC_WIRE_DENSITY = 0.00786
MUSIC_WIRE_ELASTIC_MODULUS = 207.0  # Pascals
MUSIC_WIRE_SHEAR_MODULUS = 79.293e9  # Pascals
MUSIC_WIRE_HOT_FACTOR_KH = 1.0  # Ratio
MUSIC_WIRE_T010 = 2.55
MUSIC_WIRE_T400 = 1.38
MUSIC_WIRE_PTE1 = 50
MUSIC_WIRE_PTE2 = 36
MUSIC_WIRE_PTE3 = 33
MUSIC_WIRE_PTE4 = 30
MUSIC_WIRE_PTE6 = 42
MUSIC_WIRE_PTE7 = 39
MUSIC_WIRE_PTE8 = 36
MUSIC_WIRE_PTB1 = 75
MUSIC_WIRE_PTB2 = 51
MUSIC_WIRE_PTB3 = 47
MUSIC_WIRE_PTB4 = 45
MUSIC_WIRE_PTB6 = 0
MUSIC_WIRE_PTB7 = 0
MUSIC_WIRE_PTB8 = 0
MUSIC_WIRE_PTB1SR = 85
MUSIC_WIRE_PTB1NOSR = 100
MUSIC_WIRE_PTB2SR = 53
MUSIC_WIRE_PTB3SR = 50
MUSIC_WIRE_SILF = 188.92
MUSIC_WIRE_SIHF = 310.28
MUSIC_WIRE_SISR = 399.91

_EPSILON = 1.0e-6

# Utils.py
import math
import FreeCAD
import Part
from FreeCAD import Vector, Rotation

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _make_profile_circle(meanRadius: float, wireDiameter: float):
    # profile circle on XZ plane (center @ (meanRadius,0,0)), radius = wire/2
    center = Vector(meanRadius, 0, 0)
    wireRadius = wireDiameter / 2.0
    circle = Part.Circle(center, Vector(0,1,0), wireRadius)  # normal +Y => circle lies in XZ plane
    edge = Part.Edge(circle)
    wire = Part.Wire(edge)
    print(f"  profile: Center={center}, wireRadius={wireRadius}")
    print(f"  profileEdge={edge}, profileWire={wire}")
    return edge, wire

def _add_segment(label, pitch, coils, height, radius, startZ, lefthand=False, color=(1,1,1)):
    """Build one helix segment, placed so it starts at z = startZ, always growing +Z by abs(height)."""
    abs_height = abs(height)
    print(f"    Create {label}: pitch={pitch:.3f}, coils={coils:.3f}, height={height:.3f}, startZ={startZ:.3f}, lefthand={lefthand}")
    try:
        helix = Part.makeHelix(pitch, abs_height, radius, 0, lefthand)
        helix.Placement = FreeCAD.Placement(Vector(0,0,startZ), Rotation(Vector(0,0,1), 0))
        e = helix.Edges[0]
        s, t = e.Vertexes[0].Point, e.Vertexes[-1].Point
        print(f"      start={s}, end={t}, Δz={t.z - s.z:.3f}")
        return e, startZ + abs_height, helix
    except Exception as ex:
        print(f"      ⚠️ makeHelix failed ({label}): {ex}")
        return None, startZ, None

def _assemble_wire(edges):
    """Robust wire assembly with join & tolerance."""
    edges = [e for e in edges if e is not None]
    print("\n=== Edge Endpoints Before Wire Assembly ===")
    for i, e in enumerate(edges):
        s, t = e.Vertexes[0].Point, e.Vertexes[-1].Point
        print(f"  edge[{i}] start={s}, end={t}")
    print("\nAssembling helixWire from edges...")

    # Try join first
    joined = Part.__sortEdges__(edges)
    if joined and len(joined) == 1 and isinstance(joined[0], Part.Wire):
        print("  ✅ helixWire built via __sortEdges__ join")
        return joined[0]

    # Fallback plain constructor
    try:
        w = Part.Wire(edges)
        print(f"  ✅ helixWire built: {w}")
        return w
    except Exception as ex:
        print(f"  ⚠️ Wire build failed: {ex}")
        raise

def _grind_planes_and_cut(shape, z_bottom, z_top, wireDiameter, show_debug=True):
    """
    Apply 'ground' to ends: cut with two horizontal planes (normal +Z).
    We cut a *tiny* amount: thickness ~ 1.5 * wireDiameter so ends are closed.
    """
    print("\n=== Create Ground Planes ===")
    doc = FreeCAD.activeDocument()
    if doc is None:
        show_debug = False  # no scene to show

    # Large squares in XY, placed at z planes, then extruded a little
    # Bottom: keep z >= 0 plane
    bottom_face = Part.makePlane(50*wireDiameter, 50*wireDiameter, Vector(-25*wireDiameter, -25*wireDiameter, z_bottom))
    bottom_solid = bottom_face.extrude(Vector(0,0,-wireDiameter))
    # Top: keep z <= z_top plane (cut from above)
    top_face = Part.makePlane(50*wireDiameter, 50*wireDiameter, Vector(-25*wireDiameter, -25*wireDiameter, z_top))
    top_solid = top_face.extrude(Vector(0,0,wireDiameter))

    if show_debug:
        Part.show(bottom_solid)
        Part.show(top_solid)
        b = doc.addObject("Part::Feature", "BottomGrindPlane")
        b.Shape = bottom_face
        b.ViewObject.Transparency = 70
        b.ViewObject.ShapeColor = (1.0, 0.2, 0.2)
        t = doc.addObject("Part::Feature", "TopGrindPlane")
        t.Shape = top_face
        t.ViewObject.Transparency = 70
        t.ViewObject.ShapeColor = (0.2, 1.0, 0.2)

    # Cut: trim below 0 and above z_top
    print("  Cutting bottom with small slab...")
    shape = shape.cut(bottom_solid)
    print("  Cutting top with small slab...")
    shape = shape.cut(top_solid)

    return shape

# ------------------------------------------------------------
# Main entry
# ------------------------------------------------------------

import FreeCAD, Part, math
from FreeCAD import Vector, Rotation

def spring_solid(meanDiameter, wireDiameter, totalCoils, inactiveCoils, endType, freeLength):
    print("\n=== spring_solid DEBUG START ===")

    # ---- Parameters ----
    meanRadius = meanDiameter / 2.0
    end_str = (endType or "").strip().lower()
    closed_bottom_coils = inactiveCoils / 2.0
    closed_top_coils = inactiveCoils - closed_bottom_coils
    transition_bottom = 1.0 if closed_bottom_coils > 0 else 0.0
    transition_top = 1.0 if closed_top_coils > 0 else 0.0
    transition_count = transition_bottom + transition_top
    activeCoils = max(totalCoils - inactiveCoils, 0.0)
    isGround = "ground" in end_str

    closedPitch = wireDiameter
    const_height = (
        closedPitch * (closed_bottom_coils + closed_top_coils)
        + transition_count * closedPitch * 0.5
    )
    middlePitch_den = activeCoils + transition_count * 0.5
    if middlePitch_den <= _EPSILON:
        middlePitch = closedPitch
    else:
        middlePitch = (freeLength - const_height) / middlePitch_den
        if middlePitch <= _EPSILON:
            middlePitch = closedPitch

    print(f"   meanDiameter={meanDiameter}, wireDiameter={wireDiameter}, totalCoils={totalCoils}, endType={endType}, freeLength={freeLength}")
    print(
        f"   closed_bottom={closed_bottom_coils}, closed_top={closed_top_coils}, transitions={transition_count}, "
        f"inactiveCoils={inactiveCoils}, activeCoils={activeCoils}, isGround={isGround}"
    )
    print(f"   meanRadius(meanRadius)={meanRadius}")
    print(f"   closedPitch={closedPitch:.3f}, middlePitch={middlePitch:.3f}")

    # ---- Profile circle (on X-Z plane) ----
    profile_radius = wireDiameter / 2.0
    profile_center = Vector(meanRadius, 0, 0)
    print(f"   profile: Center={profile_center}, Radius={profile_radius}")

    # ---- Helix builder ----
    def add_segment(label, pitch, coils, height, radius, startZ, angle, reverse=False):
        abs_height = abs(height)
        lefthand = bool(reverse)

        print(f"     Create {label}: pitch={pitch:.3f}, coils={coils:.3f}, height={height:.3f}, startZ={startZ:.3f}, angle={math.degrees(angle):.3f}°, lefthand={lefthand}")

        try:
            helix = Part.makeHelix(pitch, abs_height, radius, 0, lefthand)
            deg_angle = math.degrees(angle)
            if abs(deg_angle) > _EPSILON:
                helix.rotate(Vector(0, 0, 0), Vector(0, 0, 1), deg_angle)
            if abs(startZ) > _EPSILON:
                helix.translate(Vector(0, 0, startZ))
            z_end = startZ + abs_height

            e = helix.Edges[0]
            s, t = e.Vertexes[0].Point, e.Vertexes[-1].Point
            print(f"       start={s}, end={t}, Δz={t.z - s.z:.3f}")
            if e.isNull():
                print("       ❌ Edge is null – helix creation failed silently")
                return None, startZ, angle

            delta_angle = coils * 2.0 * math.pi
            if lefthand:
                delta_angle *= -1.0
            next_angle = angle + delta_angle
            return e, z_end, next_angle
        except Exception as ex:
            print(f"       ⚠️ makeHelix failed: {ex}")
            return None, startZ, angle

    # ---- Build helix segments ----
    zpos = 0.0
    angle = 0.0
    edges = []

    if closed_bottom_coils > 0:
        edge, zpos, angle = add_segment("Bottom Closed", closedPitch, closed_bottom_coils, closed_bottom_coils * closedPitch, meanRadius, zpos, angle)
        edges.append(edge)
        if transition_bottom:
            transition_height = transition_bottom * (closedPitch + middlePitch) / 2.0
            edge, zpos, angle = add_segment("Bottom Transition", (closedPitch + middlePitch) / 2.0, transition_bottom, transition_height, meanRadius, zpos, angle)
            edges.append(edge)

    if activeCoils > _EPSILON:
        edge, zpos, angle = add_segment("Middle", middlePitch, activeCoils, activeCoils * middlePitch, meanRadius, zpos, angle)
        edges.append(edge)

    if closed_top_coils > 0:
        if transition_top:
            transition_height = transition_top * (closedPitch + middlePitch) / 2.0
            edge, zpos, angle = add_segment("Top Transition", (closedPitch + middlePitch) / 2.0, transition_top, transition_height, meanRadius, zpos, angle)
            edges.append(edge)
        edge, zpos, angle = add_segment("Top Closed", closedPitch, closed_top_coils, closed_top_coils * closedPitch, meanRadius, zpos, angle)
        edges.append(edge)

    missing = [i for i,e in enumerate(edges) if e is None]
    if missing:
        print(f"   ❌ Missing helix segments at indices {missing}; aborting sweep")
        return None

    print("\n=== Edge Endpoints Before Wire Assembly ===")
    for i,e in enumerate(edges):
        if e:
            s,t = e.Vertexes[0].Point, e.Vertexes[-1].Point
            print(f"   edge[{i}] start={s}, end={t}")
        else:
            print(f"   edge[{i}] is None")

    # ---- Build path wire ----
    helixWire = _assemble_wire(edges)
    print(f"\n   ✅ helixWire built: {helixWire}")
    print(f"      isNull={helixWire.isNull()}, isClosed={helixWire.isClosed()}, length={helixWire.Length if not helixWire.isNull() else 0:.3f}")
    if hasattr(helixWire, "check"):
        print("      Wire.check():")
        check_result = helixWire.check()
        if check_result:
            for line in str(check_result).splitlines():
                print("        " + line)
        else:
            print("        (no issues reported)")
    try:
        print(f"      First vertex: {helixWire.Vertexes[0].Point}, Last vertex: {helixWire.Vertexes[-1].Point}")
    except Exception as ex:
        print(f"      ⚠️ Unable to access wire vertices: {ex}")

    # ---- Build sweep profile aligned to helix start ----
    helix_edge = helixWire.Edges[0]
    u0 = helix_edge.FirstParameter
    start_pt = helix_edge.valueAt(u0)
    tangent = helix_edge.tangentAt(u0)
    if isinstance(tangent, tuple):
        tangent = tangent[0]
    tangent.normalize()

    try:
        profileEdge = Part.makeCircle(profile_radius, start_pt, tangent)
        profileWire = Part.Wire(profileEdge)
    except Exception as ex:
        print(f"   ❌ Failed to create profile circle: {ex}")
        return None
    print(f"   profileEdge={profileEdge}, profileWire={profileWire}")

    # ---- Sweep circle along wire ----
    print("\n=== Sweep profile along helix wire ===")
    print("\n=== Sweep along helix (helixWire.makePipeShell) ===")
    try:
        springShape = helixWire.makePipeShell([profileWire], True, True)
    except Exception as ex:
        print(f"   ❌ makePipeShell raised exception: {ex}")
        return None
    if springShape.ShapeType == "Shell":
        try:
            springShape = Part.makeSolid(springShape)
            print("   ✅ Converted pipe shell to solid via Part.makeSolid")
        except Exception as ex:
            print(f"   ⚠️ Part.makeSolid failed on pipe shell: {ex}")
    if hasattr(springShape, "ShapeType"):
        print(f"   makePipe result ShapeType = {springShape.ShapeType}")
    else:
        print(f"   ⚠️ makePipe returned non-shape type: {type(springShape)}")

    try:
        st = springShape.ShapeType
    except Exception as ex:
        print(f"   ⚠️ Unable to query ShapeType: {ex}")
        st = None
    print(f"   makePipe result ShapeType={st}")
    if hasattr(springShape, "Faces"):
        print(f"   Face count={len(springShape.Faces)}, Shell count={len(springShape.Shells)}, Solid count={len(springShape.Solids)}")
    if hasattr(springShape, "BoundBox"):
        bb = springShape.BoundBox
        print(f"   BoundBox: X[{bb.XMin:.3f}, {bb.XMax:.3f}] Y[{bb.YMin:.3f}, {bb.YMax:.3f}] Z[{bb.ZMin:.3f}, {bb.ZMax:.3f}]")
    if hasattr(springShape, "isClosed"):
        print(f"   isClosed={springShape.isClosed()}")
    if hasattr(springShape, "Volume"):
        print(f"   Volume={springShape.Volume if st == 'Solid' else 'n/a'}")

    # === Grind flat ends (restore old behavior) ===
    if isGround:
        print("=== Create Ground Planes & Cut ===")
        springShape = _grind_planes_and_cut(springShape, z_bottom=0.0, z_top=zpos, wireDiameter=wireDiameter, show_debug=False)
    else:
        print("Skipping grinding; endType is not ground")

    # === Convert to solid if possible ===
    print("=== Solidify ===")
    try:
        # If grinding returned a Compound, extract the shell
        if springShape.ShapeType == "Compound":
            print("   Extracting shell from Compound...")
            shells = [s for s in springShape.Solids] + [s for s in springShape.Shells]
            if shells:
                springShape = shells[0]
                print("   ✅ Using shell for solidification")
            else:
                print("   ⚠️ No solids or shells found in compound")

        # Attempt solidification
        shapetype = getattr(springShape, "ShapeType", None)
        if shapetype == "Solid":
            print("   ✅ Already a solid shape")
        elif shapetype == "Shell":
            try:
                springShape = Part.Solid(springShape)
                print("   ✅ Converted shell to solid via Part.Solid")
            except Exception as ex:
                print(f"   ⚠️ Part.Solid conversion failed: {ex}")
                try:
                    springShape = springShape.makeSolid()
                    print("   ✅ Fallback shell.makeSolid succeeded")
                except Exception as ex_shell:
                    print(f"   ❌ Shell solidification failed: {ex_shell}")
        else:
            try:
                springShape = springShape.makeSolid()
                print("   ✅ makeSolid succeeded")
            except Exception as ex:
                print(f"   ⚠️ makeSolid() failed: {ex}")
                # fallback: try shape fixing & sewing (if available)
                shape_fix_module = getattr(Part, "ShapeFix", None)
                if shape_fix_module and hasattr(shape_fix_module, "ShapeFix_Shape") and hasattr(Part, "BRepBuilderAPI_Sewing"):
                    try:
                        fixer = shape_fix_module.ShapeFix_Shape(springShape)
                        fixed = fixer.Shape()
                        sewer = Part.BRepBuilderAPI_Sewing()
                        sewer.Add(fixed)
                        sewer.Perform()
                        sewed = sewer.SewedShape()
                        springShape = sewed.makeSolid()
                        print("   ✅ Sewing + makeSolid succeeded")
                    except Exception as ex2:
                        print(f"   ❌ Solidification fallback failed: {ex2}")
                else:
                    print("   ❌ Solidification fallback unavailable: ShapeFix tools not present")

    except Exception as all_ex:
        print(f"❌ Solidification process error: {all_ex}")

    if springShape is None:
        print("❌ springShape is None after processing")
    else:
        st_final = getattr(springShape, "ShapeType", None)
        print(f"   Final ShapeType={st_final}")
        if hasattr(springShape, "Faces"):
            print(f"   Final faces={len(springShape.Faces)} shells={len(springShape.Shells)} solids={len(springShape.Solids)}")
        if hasattr(springShape, "isClosed"):
            try:
                print(f"   Final isClosed={springShape.isClosed()}")
            except Exception as ex:
                print(f"   ⚠️ Final isClosed check failed: {ex}")

    print("=== spring_solid DEBUG END ===")
    return springShape

def end_type_index(end_type) -> int:
    return _enum_index("Compression", "EndType", end_type)

def _enum_value(selection):
    """Return the active enumeration value from a property selection."""

    if isinstance(selection, (list, tuple)):
        return selection[0] if selection else None
#    print(f"[_enum_value] selection={selection}")
    return selection

def _enum_index(enum_type: str, name: str, selection) -> int:
    """Return the 1-based index of an enumeration selection."""

    value = _enum_value(selection)
#    print(f"[_enum_index] value={value}");
    if value is None:
#        print(f"[_enum_index] return 0");
        return 0

    try:
        _header, rows, _mtime = CoreUtils.load_enum_table(enum_type, name)
#        print(f"[_enum_index] _header={_header} rows={rows} _mtime={_mtime}");
    except Exception:
#        print(f"[_enum_index] return 0");
        return 0

    options = [row[0] for row in rows]
#    print(f"_enum_index options={options}");
    try:
#        print(f"[_enum_index] options.index(value)+1={options.index(value)+1}");
        return options.index(value) + 1
    except ValueError:
#        print(f"[_enum_index] return 0");
        return 0

def update_globals(obj) -> None:
    """Update global properties based on the object's global properties."""
#
#    print(f"[update_globals] obj.PropCalcMethod={obj.PropCalcMethod}");
#    print(f"[update_globals] obj.LifeCategory={obj.LifeCategory}");
#    print(f"[update_globals] obj.EndType={obj.EndType}");

    prop_calc_method_index = _enum_index("Compression", "PropCalcMethod", getattr(obj, "PropCalcMethod", None))
    match prop_calc_method_index:
        case 1: # Prop_Calc_Method = 1 - Use values from material table
            obj.MaterialType = MUSIC_WIRE_MATERIAL_TYPE
            obj.ASTMFedSpec = MUSIC_WIRE_ASTM_FS + "/" + MUSIC_WIRE_FEDSPEC
            if obj.HotFactorKh < 1.0:
                obj.Process = "Hot Wound"
            else :
                obj.Process = "Cold Coiled"
            obj.Density = MUSIC_WIRE_DENSITY
            obj.TorsionModulus =  MUSIC_WIRE_SHEAR_MODULUS
            obj.tensile_010 =  1000 * MUSIC_WIRE_T010
            tensile_400 = 1000 * MUSIC_WIRE_T400
            life_category_index = _enum_index("Compression", "LifeCategory", getattr(obj, "LifeCategory", None))
#            print(f"[update_globals] life_category_index={life_category_index}")
            match life_category_index:
                case 1 | 5:
                    obj.PercentTensileEndurance = MUSIC_WIRE_PTE1
                case 2:
                    obj.PercentTensileEndurance = MUSIC_WIRE_PTE2
                case 3:
                    obj.PercentTensileEndurance = MUSIC_WIRE_PTE3
                case 4:
                    obj.PercentTensileEndurance = MUSIC_WIRE_PTE4
                case 6:
                    obj.PercentTensileEndurance = MUSIC_WIRE_PTE6
                case 7:
                    obj.PercentTensileEndurance = MUSIC_WIRE_PTE7
                case 8:
                    obj.PercentTensileEndurance = MUSIC_WIRE_PTE8
            obj.PercentTensileStatic = MUSIC_WIRE_PTE1
            obj.const_term = math.log10(obj.tbase010);
            obj.slope_term = (tensile_400 - obj.tensile_010) / (math.log10(obj.tbase400) - obj.const_term);
            obj.Tensile = obj.slope_term * (math.log10(obj.WireDiameter) - obj.const_term) + obj.tensile_010;
            obj.StressLimitEndurance = obj.Tensile * obj.PercentTensileEndurance / 100.0;
            obj.StressLimitStatic = obj.Tensile * obj.PercentTensileStatic / 100.0;
            end_type_index = _enum_index("Compression", "EndType", getattr(obj, "EndType", None))
            match end_type_index:
                case 1 | 2 | 3 | 4 | 5 | 6:
                    obj.setEditorMode("CoilsInactive", 1) # Visible R/O
                    obj.setEditorMode("AddCoilsAtSolid", 1) # Visible R/O
                case _: # user specified
                    obj.setEditorMode("CoilsInactive", 0) # Visible R/W
                    obj.setEditorMode("AddCoilsAtSolid", 0) # Visible R/W
            obj.setEditorMode("MaterialType", 0) # Visible R/W
            obj.setEditorMode("ASTMFedSpec", 0) # Visible R/W
            obj.setEditorMode("Process", 0) # Visible R/W
            obj.setEditorMode("LifeCategory", 0) # Visible R/W
            obj.setEditorMode("Density", 1) # Visible R/O
            obj.setEditorMode("TorsionModulus", 1) # Visible R/O
            obj.setEditorMode("HotFactorKh", 1) # Visible R/O
            obj.setEditorMode("Tensile", 1) # Visible R/O
            obj.setEditorMode("PercentTensileEndurance", 1) # Visible R/O
            obj.setEditorMode("PercentTensileStatic", 1) # Visible R/O
            obj.setEditorMode("StressLimitEndurance", 1) # Visible R/O
            obj.setEditorMode("StressLimitStatic", 1) # Visible R/O
        case 2: # Prop_Calc_Method = 2 - Specify Tensile, %_Tensile_Stat & %_Tensile_Endur
            pass #tbd
        case 3: # Prop_Calc_Method = 3 - Specify Stress_Lim_Stat & Stress_Lim_Endur
            pass #tbd

#def cyclelife_calculation(material_type, life_category, spring_type, tensile, stress_at_deflection1, stress_at_deflection1) -> float:
#    var i
#    var j
#    var pntc
#    var sterm
#    var temp
#    var idxoffset
#    var snx = [
#    var sny = [7.0, 6.0, 5.0, 4.0 // Powers of 10: 10,000,000, 1,000,000, 100,000, 10,000 cycles
#    var m_tab
#    var result
#    if (Material_File === "mat_metric.json") {
#        m_tab = require('../mat_metric.json')
#    } else {
#        m_tab = require('../mat_us.json')
#    }
#    if (st_code === 3) {
#        temp = tensile
#    } else {
#        temp = 0.67 * tensile
#    }
#    const smallnum = 1.0e-7
#    var temp_stress_1 = temp - stress_1
#    if (temp_stress_1 < smallnum) temp_stress_1 = smallnum
#    var temp_stress_2 = temp - stress_2
#    if (temp_stress_2 < smallnum) temp_stress_2 = smallnum
#    var ratio = temp_stress_2 / temp_stress_1
#    pntc = stress_2 - stress_1 * ratio
#    if (pntc < smallnum) pntc = smallnum
#    if (cl_idx < 5) { // Is Life Catagory Not Peened?
#        j = 0
#    } else { // Else Shot Peened
#        j = 3
#    }
#    for (i = 0 i <= 3 i++) {
#        idxoffset = 3 - i + j
#        if (j > 0 && idxoffset === 3) { // If Shot Peened and
#            idxoffset = 0
#        }
#        if (st_code === 3) { // Is it Torsion?
#            snx[i = 0.01 * m_tab[mat_idx[mo.ptb1+idxoffset * tensile
#        } else {
#            snx[i = 0.01 * m_tab[mat_idx[mo.pte1+idxoffset * tensile
#        }
#    }
#    if (pntc < snx[0) { // Is point after the table?
#        sterm = (sny[1 - sny[0) / (snx[1 - snx[0)
#        temp = sterm * (pntc - snx[0) + sny[0
#        result =  Math.pow(10.0, temp)
#        return(result)
#    }
#    // Look for the point in the table
#    for (i = 1 i <= 3 i++) {
#        if (pntc < snx[i) {
#          j = i - 1
#          sterm = (sny[i - sny[j) / (snx[i - snx[j)
#          temp = sterm * (pntc - snx[j) + sny[j
#          result = Math.pow(10.0, temp)
#          return result
#        }
#    }
#    sterm = (sny[3 - sny[2) / (snx[3 - snx[2)
#    temp = sterm * (pntc - snx[3) + sny[3
#    result =  Math.pow(10.0, temp)
#    return result

def update_properties(obj) -> None:
    """Update properties based on the object's properties."""

    obj.MeanDiameterAtFree = obj.OutsideDiameterAtFree - obj.WireDiameter
    obj.InsideDiameterAtFree = obj.MeanDiameterAtFree - obj.WireDiameter
    obj.SpringIndex = (obj.MeanDiameterAtFree / obj.WireDiameter)
    kc = (4.0 * obj.SpringIndex - 1.0) / (4.0 * obj.SpringIndex - 4.0)
    ks = kc + 0.615 / obj.SpringIndex
    obj.CoilsActive = obj.CoilsTotal - obj.CoilsInactive
    end_type_index = _enum_index("Compression", "EndType", getattr(obj, "EndType", None))
#    print(f"[update_properties] end_type_index={end_type_index}")
    match end_type_index:
        case 1: # Open
            obj.Pitch = (obj.LengthAtFree - obj.WireDiameter) / obj.CoilsActive
        case 2: # Open & Ground
            obj.Pitch = obj.LengthAtFree / obj.CoilsTotal
        case 3: # Closed
            obj.Pitch = (obj.LengthAtFree - 3.0 * obj.WireDiameter) / obj.CoilsActive
        case 4: # Closed & Ground
            obj.Pitch = (obj.LengthAtFree - 2.0 * obj.WireDiameter) / obj.CoilsActive
        case 5: # Tapered Closed & Ground
            obj.Pitch = (obj.LengthAtFree - 1.5 * obj.WireDiameter) / obj.CoilsActive
        case 6: # Pig-tail
            obj.Pitch = (obj.LengthAtFree - 2.0 * obj.WireDiameter) / obj.CoilsActive
        case _: # User Specified
            obj.Pitch = (obj.LengthAtFree - (obj.CoilsInactive + 1.0) * obj.WireDiameter) / obj.CoilsActive
    temp = obj.SpringIndex * obj.SpringIndex
    obj.Rate = obj.HotFactorKh * (obj.TorsionModulus / 1.0e6) * obj.MeanDiameterAtFree / (8.0 * obj.CoilsActive * temp * temp)
    obj.Deflection1 = obj.ForceAtDeflection1 / obj.Rate
    obj.Deflection2 = obj.ForceAtDeflection2 / obj.Rate
    obj.LengthAtDeflection1 = obj.LengthAtFree - obj.Deflection1
    obj.LengthAtDeflection2 = obj.LengthAtFree - obj.Deflection2
    obj.LengthStroke = obj.LengthAtDeflection1 - obj.LengthAtDeflection2
    obj.Slenderness = obj.LengthAtFree / obj.MeanDiameterAtFree
    obj.LengthAtSolid = obj.WireDiameter * (obj.CoilsTotal + obj.AddCoilsAtSolid)
    obj.ForceAtSolid = obj.Rate * (obj.LengthAtFree - obj.LengthAtSolid)
    s_f = ks * 8.0 * obj.MeanDiameterAtFree / (math.pi * obj.WireDiameter * obj.WireDiameter * obj.WireDiameter)
    obj.StressAtDeflection1 = s_f * obj.ForceAtDeflection1
    obj.StressAtDeflection2 = s_f * obj.ForceAtDeflection2
    obj.StressAtSolid = s_f * obj.ForceAtSolid
    prop_calc_method_index = _enum_index("Compression", "PropCalcMethod", getattr(obj, "PropCalcMethod", None))
#    print(f"[update_properties] prop_calc_method_index={prop_calc_method_index}")
    if prop_calc_method_index == 1:
        obj.Tensile = obj.slope_term * (math.log10(obj.WireDiameter) - obj.const_term) + obj.tensile_010
    if prop_calc_method_index <= 2:
        obj.StressLimitEndurance = obj.Tensile * obj.PercentTensileEndurance / 100.0
        obj.StressLimitStatic  = obj.Tensile * obj.PercentTensileStatic  / 100.0
    if obj.StressAtDeflection2 > 0.0:
        obj.FactorOfSafetyAtDeflection2 = obj.StressLimitStatic / obj.StressAtDeflection2
    else:
        obj.FactorOfSafetyAtDeflection2 = 1.0
    if obj.StressAtSolid > 0.0:
        obj.FactorOfSafetyAtSolid = obj.StressLimitStatic / obj.StressAtSolid
    else:
        obj.FactorOfSafetyAtSolid = 1.0
    stress_average = (obj.StressAtDeflection1 + obj.StressAtDeflection2) / 2.0
    stress_range = (obj.StressAtDeflection2 - obj.StressAtDeflection1) / 2.0
    se2 = obj.StressLimitEndurance / 2.0
#    print(f"[update_properties] kc={kc}")
#    print(f"[update_properties] stress_average={stress_average}")
#    print(f"[update_properties] stress_range={stress_range}")
#    print(f"[update_properties] se2={se2}")
#    print(f"[update_properties] obj.StressLimitStatic={obj.StressLimitStatic}")
    obj.FactorOfSafetyAtCycleLife =  obj.StressLimitStatic / (kc * stress_range * (obj.StressLimitStatic - se2) / se2 + stress_average)
    if prop_calc_method_index == 1: # and obj.Material_Type != 0
#        obj.CycleLife = cyclelife_calculation(obj.MaterialType, obj.LifeCategory, 1, obj.Tensile, obj.StressAtDeflection1, obj.StressAtDeflection2)
        obj.CycleLife = 0.0
    else:
        obj.CycleLife = 0.0
    sq1 = obj.LengthAtFree
    sq2 = obj.CoilsTotal * math.pi * obj.MeanDiameterAtFree
    wire_len_t = math.sqrt(sq1 * sq1 + sq2 * sq2)
    end_type_index = _enum_index("Compression", "EndType", getattr(obj, "EndType", None))
#    print(f"[update_properties] end_type_index={end_type_index}")
    if end_type_index == 5: # Tapered_C&G
        wire_len_t = wire_len_t - 3.926 * obj.WireDiameter
    obj.Weight = obj.Density * (math.pi * obj.WireDiameter * obj.WireDiameter / 4.0) * wire_len_t
    if obj.LengthAtFree > obj.LengthAtSolid:
        obj.PercentAvailableDeflection = 100.0 * obj.Deflection2 / (obj.LengthAtFree - obj.LengthAtSolid)
        if obj.LengthAtFree < obj.LengthAtSolid + obj.WireDiameter:
            temp = 100.0 * obj.Deflection2 / obj.WireDiameter + 10000.0 * (obj.LengthAtSolid + obj.WireDiameter - obj.LengthAtFree)
            if temp < obj.PercentAvailableDeflection:
                obj.PercentAvailableDeflection = temp
    else:
        obj.PercentAvailableDeflection = 100.0 * obj.Deflection2 / obj.WireDiameter + 10000.0 * (obj.LengthAtSolid + obj.WireDiameter - obj.LengthAtFree)
    obj.Energy = 0.5 * obj.Rate * (obj.Deflection2 * obj.Deflection2 - obj.Deflection1 * obj.Deflection1)

    #=====================================
