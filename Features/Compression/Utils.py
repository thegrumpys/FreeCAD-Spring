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

def spring_solid(meanDiameter, wireDiameter, totalCoils, endType, freeLength, transitionCoils=1.0):
    print("\n=== spring_solid DEBUG START ===")
    print(f"meanDiameter={meanDiameter}, wireDiameter={wireDiameter}, totalCoils={totalCoils}, endType={endType}, freeLength={freeLength}")

    # ===== BASIC PARAMETERS =====
    R = meanDiameter / 2.0
    closedPitch = wireDiameter
    activeCoils = totalCoils - 2.0
    middlePitch = (freeLength - 2 * closedPitch - 2 * transitionCoils * (closedPitch + wireDiameter) / 2.0) / activeCoils

    print(f"closedPitch={closedPitch:.3f}, middlePitch={middlePitch:.3f}, meanRadius={R}")

    # ===== PROFILE CIRCLE (on X-Z plane) =====
    profile_center = Vector(R, 0, 0)
    profile_radius = wireDiameter / 2.0
    profile_edge = Part.makeCircle(profile_radius, profile_center, Vector(0, 1, 0))
    profile_wire = Part.Wire(profile_edge)
    print(f"profile: Center={profile_center}, Radius={profile_radius}")

    # ===== HELIX BUILDER =====
    doc = FreeCAD.activeDocument() or FreeCAD.newDocument("SpringSolidTest")
    edges = []
    zpos = 0.0

    colors = [
        (1.0, 0.0, 0.0),   # bottom closed
        (1.0, 0.5, 0.0),   # bottom transition
        (1.0, 1.0, 0.0),   # middle
        (0.0, 1.0, 0.0),   # top transition
        (0.0, 0.5, 1.0),   # top closed
    ]

    def add_segment(label, pitch, coils, height, radius, startZ, reverse=False, color=(1,1,1)):
        abs_height = abs(height)
        lefthand = bool(reverse)
        print(f"  Create {label}: pitch={pitch:.3f}, coils={coils:.1f}, height={height:.3f}, startZ={startZ:.3f}, reverse={reverse}, lefthand={lefthand}")
        try:
            helix = Part.makeHelix(pitch, abs_height, radius, 0, lefthand)
            helix.Placement = FreeCAD.Placement(Vector(0, 0, startZ), Rotation(Vector(0, 0, 1), 0))
            z_end = startZ + abs_height

            e = helix.Edges[0]
            s, t = e.Vertexes[0].Point, e.Vertexes[-1].Point
            print(f"    start={s}, end={t}, Δz={t.z - s.z:.3f}")

            obj = doc.addObject("Part::Feature", label.replace(" ", "_"))
            obj.Shape = helix
            obj.ViewObject.ShapeColor = color

            return e, z_end
        except Exception as ex:
            print(f"    ⚠️ makeHelix failed for {label}: {ex}")
            return None, startZ

    # ===== BUILD SEQUENCE =====
    edge, zpos = add_segment("Bottom Closed", closedPitch, 1.0, closedPitch, R, zpos, reverse=False, color=colors[0]); edges.append(edge)
    edge, zpos = add_segment("Bottom Transition", (closedPitch + middlePitch) / 2, transitionCoils, (closedPitch + middlePitch) / 2, R, zpos, reverse=False, color=colors[1]); edges.append(edge)
    edge, zpos = add_segment("Middle", middlePitch, activeCoils, activeCoils * middlePitch, R, zpos, reverse=False, color=colors[2]); edges.append(edge)
    edge, zpos = add_segment("Top Transition", (closedPitch + middlePitch) / 2, transitionCoils, (closedPitch + middlePitch) / 2, R, zpos, reverse=False, color=colors[3]); edges.append(edge)
    edge, zpos = add_segment("Top Closed", closedPitch, 1.0, closedPitch, R, zpos, reverse=False, color=colors[4]); edges.append(edge)

    # ===== COMBINE INTO WIRE =====
    print("\n=== Assembling helixWire ===")
    try:
        helixWire = Part.Wire([e for e in edges if e])
        print("✅ helixWire built successfully")
    except Exception as ex:
        print(f"⚠️ Wire build failed: {ex}")
        return None

    # ===== SWEEP PROFILE ALONG WIRE =====
    print("\n=== Sweep profile along helix wire ===")
    try:
        compressionSpring = profile_wire.makePipeShell([helixWire])
        compressionSpring.setMode(True)
        compressionSpring.build()
        compressionSpring.makeSolid()
        springShape = compressionSpring.shape()
        print("✅ compressionSpring solid built successfully")
    except Exception as ex:
        print(f"⚠️ Sweep failed: {ex}")
        springShape = helixWire.makePipe(profile_wire)

    # ===== ADD TO VIEW =====
    obj = doc.addObject("Part::Feature", "CompressionSpring")
    obj.Shape = springShape
    obj.ViewObject.ShapeColor = (0.8, 0.8, 0.8)
    print("✅ compressionSpring displayed in FreeCAD view")

    # ===== GROUND ENDS (optional) =====
    if "ground" in endType.lower():
        print("\n=== Create Ground Cutter Boxes ===")
        cutter_size = 2 * (R + wireDiameter)
        bottomCutter = Part.makeBox(cutter_size, cutter_size, wireDiameter, Vector(-R, -R, 0))
        topCutter = bottomCutter.copy()
        topCutter.Placement.Base.z = zpos - wireDiameter
        springShape = springShape.cut(bottomCutter).cut(topCutter)
        obj.Shape = springShape
        print("✅ Ground ends applied")

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
