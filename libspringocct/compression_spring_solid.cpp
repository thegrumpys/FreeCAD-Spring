#include <BRepAlgoAPI_Cut.hxx>
#include <BRepAlgoAPI_Common.hxx>
#include <BRepBuilderAPI_MakeEdge.hxx>
#include <BRepBuilderAPI_MakeWire.hxx>
#include <BRepBuilderAPI_Transform.hxx>
#include <BRepLib.hxx>
#include <BRepMesh_IncrementalMesh.hxx>
#include <BRepOffsetAPI_MakePipeShell.hxx>
#include <BRepPrimAPI_MakeBox.hxx>
#include <ElCLib.hxx>
#include <GCE2d_MakeArcOfCircle.hxx>
#include <GCE2d_MakeLine.hxx>
#include <Geom_CylindricalSurface.hxx>
#include <Geom2d_BezierCurve.hxx>
#include <Geom2d_BSplineCurve.hxx>
#include <Geom2d_Circle.hxx>
#include <Geom2d_Curve.hxx>
#include <Geom2d_Ellipse.hxx>
#include <Geom2d_Hyperbola.hxx>
#include <Geom2d_Line.hxx>
#include <Geom2d_OffsetCurve.hxx>
#include <Geom2d_Parabola.hxx>
#include <Geom2d_TrimmedCurve.hxx>
#include <Geom2dConvert.hxx>
#include <Geom2dConvert_CompCurveToBSplineCurve.hxx>
#include <Geom2dAPI_PointsToBSpline.hxx>
#include <Geom_BSplineCurve.hxx>
#include <Geom_Curve.hxx>
#include <GeomAPI_PointsToBSpline.hxx>
#include <GeomConvert_CompCurveToBSplineCurve.hxx>
#include <Precision.hxx>
#include <Standard_Failure.hxx>
#include <gp_Ax2d.hxx>
#include <gp_Circ.hxx>
#include <gp_Circ2d.hxx>
#include <gp_Lin2d.hxx>
#include <gp_Pnt2d.hxx>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <algorithm>
#include <cmath>
#include <limits>
#include <TColgp_Array1OfPnt2d.hxx>
#include <TColgp_Array1OfPnt.hxx>
#include <TopAbs.hxx>
#include <TopExp_Explorer.hxx>
#include <TopoDS.hxx>
#include <TopoDS_Edge.hxx>
#include <TopoDS_Solid.hxx>
#include <TopoDS_Shape.hxx>
#include <TopoDS_Wire.hxx>
#include <BRepCheck_Analyzer.hxx>
#include <BRepGProp.hxx>
#include <GProp_GProps.hxx>
#include <Bnd_Box.hxx>
#include <BRepBndLib.hxx>
#include "SpringWireRadiusLaw.hpp"
// -----------------------------------------------------------------------------
// Spring diagnostics
// -----------------------------------------------------------------------------
// Production builds are quiet by default. The verbose diagnostics that were used
// while stabilizing the end-type geometry are intentionally retained, but they are
// now opt-in compile-time diagnostics instead of unconditional console output.
//
// Enable everything:
//   -DSPRING_DEBUG_ALL=1
//
// Or enable narrower families:
//   -DSPRING_DEBUG_BASIC=1
//   -DSPRING_DEBUG_SWEEP=1
//   -DSPRING_DEBUG_GROUNDING=1
//   -DSPRING_DEBUG_PIGTAIL=1
//   -DSPRING_DEBUG_TAPERED=1
#ifndef SPRING_DEBUG_ALL
#define SPRING_DEBUG_ALL 0
#endif

#ifndef SPRING_DEBUG_BASIC
#define SPRING_DEBUG_BASIC 0
#endif

#ifndef SPRING_DEBUG_SWEEP
#define SPRING_DEBUG_SWEEP 0
#endif

#ifndef SPRING_DEBUG_GROUNDING
#define SPRING_DEBUG_GROUNDING 0
#endif

#ifndef SPRING_DEBUG_PIGTAIL
#define SPRING_DEBUG_PIGTAIL 0
#endif

#ifndef SPRING_DEBUG_TAPERED
#define SPRING_DEBUG_TAPERED 0
#endif

namespace {
class SpringNullBuffer : public std::streambuf
{
public:
    int overflow(int c) override
    {
        return c;
    }
};

inline std::ostream& SpringNullStream()
{
    static SpringNullBuffer buffer;
    static std::ostream stream(&buffer);
    return stream;
}

inline std::ostream& SpringDebugStream()
{
#if SPRING_DEBUG_ALL || SPRING_DEBUG_BASIC || SPRING_DEBUG_SWEEP || SPRING_DEBUG_GROUNDING || SPRING_DEBUG_PIGTAIL || SPRING_DEBUG_TAPERED
    return std::cout;
#else
    return SpringNullStream();
#endif
}

inline bool SpringDebugBasicEnabled()
{
#if SPRING_DEBUG_ALL || SPRING_DEBUG_BASIC
    return true;
#else
    return false;
#endif
}

inline bool SpringDebugSweepEnabled()
{
#if SPRING_DEBUG_ALL || SPRING_DEBUG_SWEEP
    return true;
#else
    return false;
#endif
}

inline bool SpringDebugGroundingEnabled()
{
#if SPRING_DEBUG_ALL || SPRING_DEBUG_GROUNDING
    return true;
#else
    return false;
#endif
}

inline bool SpringDebugPigtailEnabled()
{
#if SPRING_DEBUG_ALL || SPRING_DEBUG_PIGTAIL
    return true;
#else
    return false;
#endif
}

inline bool SpringDebugTaperedEnabled()
{
#if SPRING_DEBUG_ALL || SPRING_DEBUG_TAPERED
    return true;
#else
    return false;
#endif
}

constexpr Standard_Real kTaperAmount = 0.5;
constexpr Standard_Real kDefaultTransitionTurns = 0.5;
constexpr Standard_Real kPigtailTargetRadiusFactor = 0.5;
constexpr Standard_Real kPigtailHighSpringIndex = 7.0;
constexpr Standard_Real kPigtailLowSpringIndex = 4.5;
constexpr Standard_Real kPigtailHighIndexEndCoils = 0.65;
constexpr Standard_Real kPigtailLowIndexEndCoils = 0.25;
constexpr Standard_Real kPigtailLowIndexTransitionTurns = 1.0;
}

#define SPRING_DEBUG_STREAM SpringDebugStream()

static void DumpShapeState(const std::string& name, const TopoDS_Shape& S)
{
    if (!SpringDebugBasicEnabled()) { return; }
    SPRING_DEBUG_STREAM << "---- Shape State: " << name << " ----" << std::endl;

    if (S.IsNull()) {
        SPRING_DEBUG_STREAM << "Shape is NULL" << std::endl;
        return;
    }

    SPRING_DEBUG_STREAM << "ShapeType=" << (int)S.ShapeType() << std::endl;

    BRepCheck_Analyzer ana(S);
    SPRING_DEBUG_STREAM << "IsValid=" << (ana.IsValid() ? "TRUE" : "FALSE") << std::endl;

    GProp_GProps props;
    BRepGProp::VolumeProperties(S, props);
    SPRING_DEBUG_STREAM << "Volume=" << props.Mass() << std::endl;

    Bnd_Box box;
    BRepBndLib::Add(S, box);
    Standard_Real xmin, ymin, zmin, xmax, ymax, zmax;
    box.Get(xmin, ymin, zmin, xmax, ymax, zmax);
    SPRING_DEBUG_STREAM << "BoundingBox: "
              << xmin << "," << ymin << "," << zmin
              << " → "
              << xmax << "," << ymax << "," << zmax << std::endl;

    SPRING_DEBUG_STREAM << "-------------------------------------" << std::endl;
}

static void DumpPipeShellState(const std::string& name,
                               BRepOffsetAPI_MakePipeShell& pipe)
{
    if (!SpringDebugSweepEnabled()) { return; }
    SPRING_DEBUG_STREAM << "---- PipeShell State: " << name << " ----" << std::endl;

    SPRING_DEBUG_STREAM << "IsDone=" << (pipe.IsDone() ? "TRUE" : "FALSE") << std::endl;

    TopoDS_Shape S = pipe.Shape();
    if (S.IsNull()) {
        SPRING_DEBUG_STREAM << "Pipe shape is NULL" << std::endl;
        SPRING_DEBUG_STREAM << "----------------------------------------" << std::endl;
        return;
    }

    BRepCheck_Analyzer ana(S);
    SPRING_DEBUG_STREAM << "TopologyValid=" << (ana.IsValid() ? "TRUE" : "FALSE") << std::endl;

    GProp_GProps props;
    BRepGProp::VolumeProperties(S, props);
    SPRING_DEBUG_STREAM << "ShellVolume=" << props.Mass() << std::endl;

    Bnd_Box box;
    BRepBndLib::Add(S, box);
    Standard_Real xmin,ymin,zmin,xmax,ymax,zmax;
    box.Get(xmin,ymin,zmin,xmax,ymax,zmax);
    SPRING_DEBUG_STREAM << "BBoxZ=" << zmin << " → " << zmax << std::endl;

    SPRING_DEBUG_STREAM << "----------------------------------------" << std::endl;
}

static Standard_Real SafeVolume(const TopoDS_Shape& S)
{
    if (S.IsNull()) {
        return 0.0;
    }

    GProp_GProps props;
    BRepGProp::VolumeProperties(S, props);
    return props.Mass();
}

static TopoDS_Shape KeepLargestSolid(const TopoDS_Shape& shape)
{
    if (shape.IsNull()) {
        return shape;
    }

    TopoDS_Solid largestSolid;
    Standard_Real largestVolume = -1.0;
    Standard_Integer solidCount = 0;

    for (TopExp_Explorer explorer(shape, TopAbs_SOLID); explorer.More(); explorer.Next()) {
        const TopoDS_Solid solid = TopoDS::Solid(explorer.Current());
        const Standard_Real volume = SafeVolume(solid);
        ++solidCount;
        if (volume > largestVolume) {
            largestVolume = volume;
            largestSolid = solid;
        }
    }

    if (solidCount <= 1 || largestSolid.IsNull()) {
        return shape;
    }

    SPRING_DEBUG_STREAM << "Keeping largest solid from " << solidCount
                        << " solids after pigtail grounding; volume="
                        << largestVolume << std::endl;
    return largestSolid;
}

static std::string ShapeSummary(const TopoDS_Shape& shape)
{
    if (shape.IsNull()) {
        return "shape=null";
    }

    Standard_Integer solidCount = 0;
    for (TopExp_Explorer explorer(shape, TopAbs_SOLID); explorer.More(); explorer.Next()) {
        ++solidCount;
    }

    Bnd_Box box;
    BRepBndLib::Add(shape, box);
    Standard_Real xmin, ymin, zmin, xmax, ymax, zmax;
    box.Get(xmin, ymin, zmin, xmax, ymax, zmax);

    std::ostringstream summary;
    summary << "shapeType=" << static_cast<int>(shape.ShapeType())
            << " solids=" << solidCount
            << " volume=" << SafeVolume(shape)
            << " bbox=("
            << xmin << "," << ymin << "," << zmin
            << " -> "
            << xmax << "," << ymax << "," << zmax
            << ")";
    return summary.str();
}

static TopoDS_Shape CutShape(
    const TopoDS_Shape& base,
    const TopoDS_Shape& tool,
    const char* label,
    const Standard_Real fuzzyValue = 0.0)
{
    BRepAlgoAPI_Cut cut(base, tool);
    if (fuzzyValue > 0.0) {
        cut.SetFuzzyValue(fuzzyValue);
    }
    cut.Build();
    if (!cut.IsDone()) {
        throw std::runtime_error(
            std::string(label) +
            " failed: base " +
            ShapeSummary(base) +
            "; tool " +
            ShapeSummary(tool)
        );
    }

    TopoDS_Shape result = cut.Shape();
    if (result.IsNull()) {
        throw std::runtime_error(
            std::string(label) +
            " produced a null shape: base " +
            ShapeSummary(base) +
            "; tool " +
            ShapeSummary(tool)
        );
    }
    return result;
}

static TopoDS_Shape CommonShape(
    const TopoDS_Shape& base,
    const TopoDS_Shape& tool,
    const char* label,
    const Standard_Real fuzzyValue = 0.0)
{
    BRepAlgoAPI_Common common(base, tool);
    if (fuzzyValue > 0.0) {
        common.SetFuzzyValue(fuzzyValue);
    }
    common.Build();
    if (!common.IsDone()) {
        throw std::runtime_error(
            std::string(label) +
            " failed: base " +
            ShapeSummary(base) +
            "; tool " +
            ShapeSummary(tool)
        );
    }

    TopoDS_Shape result = common.Shape();
    if (result.IsNull()) {
        throw std::runtime_error(
            std::string(label) +
            " produced a null shape: base " +
            ShapeSummary(base) +
            "; tool " +
            ShapeSummary(tool)
        );
    }
    return result;
}

static void DumpBBox(const std::string& name, const TopoDS_Shape& S)
{
    if (!SpringDebugGroundingEnabled()) { return; }
    SPRING_DEBUG_STREAM << "---- BBox: " << name << " ----" << std::endl;

    if (S.IsNull()) {
        SPRING_DEBUG_STREAM << "Shape is NULL" << std::endl;
        SPRING_DEBUG_STREAM << "---------------------------" << std::endl;
        return;
    }

    Bnd_Box box;
    BRepBndLib::Add(S, box);

    Standard_Real xmin, ymin, zmin, xmax, ymax, zmax;
    box.Get(xmin, ymin, zmin, xmax, ymax, zmax);

    SPRING_DEBUG_STREAM << "xmin=" << xmin << " ymin=" << ymin << " zmin=" << zmin << std::endl;
    SPRING_DEBUG_STREAM << "xmax=" << xmax << " ymax=" << ymax << " zmax=" << zmax << std::endl;
    SPRING_DEBUG_STREAM << "dx=" << (xmax - xmin)
              << " dy=" << (ymax - ymin)
              << " dz=" << (zmax - zmin) << std::endl;
    SPRING_DEBUG_STREAM << "---------------------------" << std::endl;
}

static void DumpBBoxOverlap(const std::string& aName,
                            const TopoDS_Shape& A,
                            const std::string& bName,
                            const TopoDS_Shape& B)
{
    if (!SpringDebugGroundingEnabled()) { return; }
    SPRING_DEBUG_STREAM << "---- BBox Overlap: " << aName << " vs " << bName << " ----" << std::endl;

    if (A.IsNull() || B.IsNull()) {
        SPRING_DEBUG_STREAM << "One or both shapes are NULL" << std::endl;
        SPRING_DEBUG_STREAM << "----------------------------------------------" << std::endl;
        return;
    }

    Bnd_Box boxA;
    Bnd_Box boxB;
    BRepBndLib::Add(A, boxA);
    BRepBndLib::Add(B, boxB);

    Standard_Real axmin, aymin, azmin, axmax, aymax, azmax;
    Standard_Real bxmin, bymin, bzmin, bxmax, bymax, bzmax;
    boxA.Get(axmin, aymin, azmin, axmax, aymax, azmax);
    boxB.Get(bxmin, bymin, bzmin, bxmax, bymax, bzmax);

    const Standard_Real ox =
        std::max(0.0, std::min(axmax, bxmax) - std::max(axmin, bxmin));
    const Standard_Real oy =
        std::max(0.0, std::min(aymax, bymax) - std::max(aymin, bymin));
    const Standard_Real oz =
        std::max(0.0, std::min(azmax, bzmax) - std::max(azmin, bzmin));

    SPRING_DEBUG_STREAM << "overlapX=" << ox
              << " overlapY=" << oy
              << " overlapZ=" << oz << std::endl;

    SPRING_DEBUG_STREAM << "----------------------------------------------" << std::endl;
}

static void DumpCutDelta(const std::string& name,
                         const TopoDS_Shape& beforeShape,
                         const TopoDS_Shape& afterShape)
{
    if (!SpringDebugGroundingEnabled()) { return; }
    const Standard_Real beforeVol = SafeVolume(beforeShape);
    const Standard_Real afterVol = SafeVolume(afterShape);

    SPRING_DEBUG_STREAM << "---- Cut Delta: " << name << " ----" << std::endl;
    SPRING_DEBUG_STREAM << "beforeVolume=" << beforeVol << std::endl;
    SPRING_DEBUG_STREAM << "afterVolume=" << afterVol << std::endl;
    SPRING_DEBUG_STREAM << "removedVolume=" << (beforeVol - afterVol) << std::endl;

    if (beforeVol > 0.0) {
        SPRING_DEBUG_STREAM << "removedFraction=" << ((beforeVol - afterVol) / beforeVol) << std::endl;
    }

    SPRING_DEBUG_STREAM << "--------------------------------" << std::endl;
}


inline gp_Pnt
UVTo3D(
    const Standard_Real u,
    const Standard_Real v,
    const Standard_Real helixRadius,
    const Standard_Real zShift);

inline Standard_Real
SmoothStep01(const Standard_Real sIn);

static gp_Pnt CurvePoint3DVariableRadius(const Handle(Geom2d_Curve)& curve2d,
                                        const Standard_Real t,
                                        const Standard_Real startRadius,
                                        const Standard_Real endRadius,
                                        const Standard_Real zShift)
{
    const Standard_Real t0 = curve2d->FirstParameter();
    const Standard_Real t1 = curve2d->LastParameter();
    Standard_Real s = 0.0;
    if (std::abs(t1 - t0) > Precision::Confusion()) {
        s = (t - t0) / (t1 - t0);
    }
    const gp_Pnt2d uv = curve2d->Value(t);
    const Standard_Real localRadius = startRadius + (endRadius - startRadius) * SmoothStep01(s);
    return UVTo3D(uv.X(), uv.Y(), localRadius, zShift);
}

static void DumpCurvePairClearance(const std::string& name,
                                   const Handle(Geom2d_Curve)& curveA,
                                   const Standard_Real aStartRadius,
                                   const Standard_Real aEndRadius,
                                   const Handle(Geom2d_Curve)& curveB,
                                   const Standard_Real bStartRadius,
                                   const Standard_Real bEndRadius,
                                   const Standard_Real zShift,
                                   const Standard_Real wireDia,
                                   const Standard_Integer samplesA = 80,
                                   const Standard_Integer samplesB = 160,
                                   const Standard_Real aTrimStart = 0.0,
                                   const Standard_Real aTrimEnd = 1.0,
                                   const Standard_Real bTrimStart = 0.0,
                                   const Standard_Real bTrimEnd = 1.0)
{
    if (!SpringDebugPigtailEnabled()) { return; }
    SPRING_DEBUG_STREAM << "---- Curve Pair Clearance: " << name << " ----" << std::endl;

    if (curveA.IsNull() || curveB.IsNull()) {
        SPRING_DEBUG_STREAM << "One or both curves are NULL" << std::endl;
        SPRING_DEBUG_STREAM << "----------------------------------------------" << std::endl;
        return;
    }

    const Standard_Integer nA = (samplesA < 2) ? 2 : samplesA;
    const Standard_Integer nB = (samplesB < 2) ? 2 : samplesB;

    const Standard_Real a0 = curveA->FirstParameter();
    const Standard_Real a1 = curveA->LastParameter();
    const Standard_Real b0 = curveB->FirstParameter();
    const Standard_Real b1 = curveB->LastParameter();

    const Standard_Real aa0 = a0 + (a1 - a0) * aTrimStart;
    const Standard_Real aa1 = a0 + (a1 - a0) * aTrimEnd;
    const Standard_Real bb0 = b0 + (b1 - b0) * bTrimStart;
    const Standard_Real bb1 = b0 + (b1 - b0) * bTrimEnd;

    Standard_Real minDist = std::numeric_limits<Standard_Real>::max();
    Standard_Real bestTa = aa0;
    Standard_Real bestTb = bb0;
    gp_Pnt bestPa;
    gp_Pnt bestPb;

    for (Standard_Integer ia = 0; ia < nA; ++ia) {
        const Standard_Real sa = static_cast<Standard_Real>(ia) / static_cast<Standard_Real>(nA - 1);
        const Standard_Real ta = aa0 + (aa1 - aa0) * sa;
        const gp_Pnt pa = CurvePoint3DVariableRadius(curveA, ta, aStartRadius, aEndRadius, zShift);

        for (Standard_Integer ib = 0; ib < nB; ++ib) {
            const Standard_Real sb = static_cast<Standard_Real>(ib) / static_cast<Standard_Real>(nB - 1);
            const Standard_Real tb = bb0 + (bb1 - bb0) * sb;
            const gp_Pnt pb = CurvePoint3DVariableRadius(curveB, tb, bStartRadius, bEndRadius, zShift);
            const Standard_Real dist = pa.Distance(pb);
            if (dist < minDist) {
                minDist = dist;
                bestTa = ta;
                bestTb = tb;
                bestPa = pa;
                bestPb = pb;
            }
        }
    }

    SPRING_DEBUG_STREAM << "minCenterlineDistance=" << minDist << std::endl;
    SPRING_DEBUG_STREAM << "wireDia=" << wireDia << std::endl;
    SPRING_DEBUG_STREAM << "clearanceMinusWireDia=" << (minDist - wireDia) << std::endl;
    SPRING_DEBUG_STREAM << "bestTa=" << bestTa << " bestTb=" << bestTb << std::endl;
    SPRING_DEBUG_STREAM << "pointA=(" << bestPa.X() << ", " << bestPa.Y() << ", " << bestPa.Z() << ")" << std::endl;
    SPRING_DEBUG_STREAM << "pointB=(" << bestPb.X() << ", " << bestPb.Y() << ", " << bestPb.Z() << ")" << std::endl;
    if (minDist <= wireDia) {
        SPRING_DEBUG_STREAM << "WARNING: sampled centerline clearance <= wire diameter; possible self-intersection or ill-formed end region" << std::endl;
    }

    SPRING_DEBUG_STREAM << "----------------------------------------------" << std::endl;
}

static void DumpPigtailEndClearanceDiagnostics(const Handle(Geom2d_TrimmedCurve)& bottomHelixSegment,
                                               const Handle(Geom2d_TrimmedCurve)& bottomTransitionSegment,
                                               const Handle(Geom2d_TrimmedCurve)& middleHelixSegment,
                                               const Handle(Geom2d_TrimmedCurve)& topTransitionSegment,
                                               const Handle(Geom2d_TrimmedCurve)& topHelixSegment,
                                               const Standard_Real helixRadius,
                                               const Standard_Real endHelixRadius,
                                               const Standard_Real zShift,
                                               const Standard_Real wireDia)
{
    if (!SpringDebugPigtailEnabled()) { return; }
    SPRING_DEBUG_STREAM << "---- Pigtail End Clearance Diagnostics ----" << std::endl;

    DumpCurvePairClearance("bottomHelix vs middleHelix",
                           bottomHelixSegment,
                           endHelixRadius,
                           endHelixRadius,
                           middleHelixSegment,
                           helixRadius,
                           helixRadius,
                           zShift,
                           wireDia);

    DumpCurvePairClearance("topHelix vs middleHelix",
                           topHelixSegment,
                           endHelixRadius,
                           endHelixRadius,
                           middleHelixSegment,
                           helixRadius,
                           helixRadius,
                           zShift,
                           wireDia);

    DumpCurvePairClearance("bottomTransition(inner) vs middleHelix(after start)",
                           bottomTransitionSegment,
                           endHelixRadius,
                           helixRadius,
                           middleHelixSegment,
                           helixRadius,
                           helixRadius,
                           zShift,
                           wireDia,
                           80,
                           160,
                           0.0,
                           0.85,
                           0.15,
                           1.0);

    DumpCurvePairClearance("topTransition(inner) vs middleHelix(before end)",
                           topTransitionSegment,
                           helixRadius,
                           endHelixRadius,
                           middleHelixSegment,
                           helixRadius,
                           helixRadius,
                           zShift,
                           wireDia,
                           80,
                           160,
                           0.15,
                           1.0,
                           0.0,
                           0.85);

    SPRING_DEBUG_STREAM << "-------------------------------------------" << std::endl;
}
inline std::ostream& operator<<(std::ostream& os, const gp_Pnt2d& P)
{
    os << "gp_Pnt2d(X=" << P.X() << ", Y=" << P.Y() << ")";
    return os;
}

inline std::ostream& operator<<(std::ostream& os, const gp_Vec2d& V)
{
    os << "gp_Vec2d(X=" << V.X() << ", Y=" << V.Y() << ")";
    return os;
}

inline std::ostream& operator<<(std::ostream& os, const gp_Dir2d& D)
{
    os << "gp_Dir2d(X=" << D.X() << ", Y=" << D.Y() << ")";
    return os;
}

inline std::ostream& operator<<(std::ostream& os, const gp_Lin2d& L)
{
    os << "gp_Lin2d(Location=" << L.Location()
       << ", Direction=" << L.Direction() << ")";
    return os;
}

inline std::ostream& operator<<(std::ostream& os, const gp_Circ2d& C)
{
    os << "gp_Circ2d(Center=" << C.Location()
       << ", Radius=" << C.Radius()
       << ")";
    return os;
}

inline std::ostream& operator<<(std::ostream& os,
                                const Handle(Geom2d_Line)& L)
{
    if (L.IsNull()) {
        os << "Geom2d_Line(NULL)";
        return os;
    }

    // Extract the underlying gp_Lin2d
    gp_Lin2d gl = L->Lin2d();

    os << "Geom2d_Line(" << gl << ")";

    return os;
}

std::ostream& operator<<(std::ostream& os, const Handle(Geom2d_TrimmedCurve)& c)
{
    if (c.IsNull()) {
        os << "Geom2d_TrimmedCurve(NULL)";
        return os;
    }

    os << "Geom2d_TrimmedCurve(";

    // Endpoints
    gp_Pnt2d p1 = c->StartPoint();
    gp_Pnt2d p2 = c->EndPoint();
    os << "P1=" << p1 << ", P2=" << p2 << ", ";

    // Underlying basis
    Handle(Geom2d_Curve) base = c->BasisCurve();

    // ------------ LINE ------------
    if (Handle(Geom2d_Line) L = Handle(Geom2d_Line)::DownCast(base)) {
        gp_Lin2d ln = L->Lin2d();
        os << "Line=" << ln;
    }

    // ------------ CIRCLE ------------
    else if (Handle(Geom2d_Circle) C = Handle(Geom2d_Circle)::DownCast(base)) {
        gp_Circ2d cc = C->Circ2d();
        os << "Circle(center=" << cc.Location()
           << ", R=" << cc.Radius() << ")";
    }

    // ------------ ELLIPSE ------------
    else if (Handle(Geom2d_Ellipse) E = Handle(Geom2d_Ellipse)::DownCast(base)) {
        os << "Ellipse(center=" << E->Location()
           << ", Major=" << E->MajorRadius()
           << ", Minor=" << E->MinorRadius() << ")";
    }

    // ------------ PARABOLA ------------
    else if (Handle(Geom2d_Parabola) P = Handle(Geom2d_Parabola)::DownCast(base)) {
        os << "Parabola(Location=" << P->Location()
           << ", Focal=" << P->Focal()
           << ", Focus=" << P->Focus()
           << ", Directrix=" << P->Directrix()
           << ")";
    }

    // ------------ HYPERBOLA ------------
    else if (Handle(Geom2d_Hyperbola) H = Handle(Geom2d_Hyperbola)::DownCast(base)) {
        os << "Hyperbola(center=" << H->Location()
           << ", Major=" << H->MajorRadius()
           << ", Minor=" << H->MinorRadius() << ")";
    }

    // ------------ BEZIER ------------
    else if (Handle(Geom2d_BezierCurve) BZ = Handle(Geom2d_BezierCurve)::DownCast(base)) {
        os << "BezierCurve(Poles=" << BZ->NbPoles() << ")";
    }

    // ------------ BSPLINE ------------
    else if (Handle(Geom2d_BSplineCurve) BS = Handle(Geom2d_BSplineCurve)::DownCast(base)) {

        os << "BSplineCurve(";

        os << "Degree=" << BS->Degree()
           << ", Poles=" << BS->NbPoles()
           << ", Knots=" << BS->NbKnots()
           << ", Rational=" << (BS->IsRational() ? "true" : "false")
           << ", Trim=[" << c->FirstParameter() << "," << c->LastParameter() << "]";

        // Poles
        os << ", PoleList=[";
        for (int i=1; i <= BS->NbPoles(); ++i) {
            os << BS->Pole(i);
            if (i < BS->NbPoles()) os << ",";
        }
        os << "]";

        // Weights
        if (BS->IsRational()) {
            os << ", WeightList=[";
            for (int i=1; i <= BS->NbPoles(); ++i) {
                os << BS->Weight(i);
                if (i < BS->NbPoles()) os << ",";
            }
            os << "]";
        }

        // Knots + Multiplicities
        os << ", KnotList=[";
        for (int i=1; i <= BS->NbKnots(); ++i) {
            os << "(" << BS->Knot(i)
               << ", mult=" << BS->Multiplicity(i) << ")";
            if (i < BS->NbKnots()) os << ",";
        }
        os << "]";

        os << ")";
    }

    // ------------ OFFSET CURVE ------------
    else if (Handle(Geom2d_OffsetCurve) OC = Handle(Geom2d_OffsetCurve)::DownCast(base)) {
        os << "OffsetCurve(Offset=" << OC->Offset()
           << ", BaseCurveType=";

        Handle(Geom2d_Curve) sub = OC->BasisCurve();
        if (Handle(Geom2d_Line)::DownCast(sub)) os << "Line";
        else if (Handle(Geom2d_Circle)::DownCast(sub)) os << "Circle";
        else if (Handle(Geom2d_BSplineCurve)::DownCast(sub)) os << "BSpline";
        else os << "Other";

        os << ")";
    }

    // ------------ UNKNOWN / OTHER ------------
    else {
        os << "BasisCurve=UnknownType";
    }

    os << ")";
    return os;
}

// Returns an arc tangent at P1 and P2.
// If L1 and L2 are parallel, returns a straight segment instead.
// Returns NULL only if something numerically degenerates.
inline Handle(Geom2d_TrimmedCurve)
MakeTangentialArcOrLine(const gp_Pnt2d& P1,
                        const gp_Lin2d& L1,
                        const gp_Pnt2d& P2,
                        const gp_Lin2d& L2,
                        const Standard_Real parallelTol = 1e-12)
{
    SPRING_DEBUG_STREAM << "========== MakeTangentialArcOrLine DEBUG ==========\n";

    SPRING_DEBUG_STREAM << "Input P1 = " << P1 << "\n";
    SPRING_DEBUG_STREAM << "Input L1 = " << L1 << "\n";
    SPRING_DEBUG_STREAM << "Input P2 = " << P2 << "\n";
    SPRING_DEBUG_STREAM << "Input L2 = " << L2 << "\n\n";

    // Directions
    gp_Dir2d d1 = L1.Direction();
    gp_Dir2d d2 = L2.Direction();

    SPRING_DEBUG_STREAM << "d1 = (" << d1.X() << ", " << d1.Y() << ")\n";
    SPRING_DEBUG_STREAM << "d2 = (" << d2.X() << ", " << d2.Y() << ")\n";

    double cross = d1.X() * d2.Y() - d1.Y() * d2.X();
    SPRING_DEBUG_STREAM << "cross(d1,d2) = " << cross << "\n";

    // Parallel case
    if (std::abs(cross) < parallelTol)
    {
        SPRING_DEBUG_STREAM << "LINES PARALLEL → returning straight segment\n";

        Handle(Geom2d_Line) gline = new Geom2d_Line(P1, d1);

        Standard_Real u1 = ElCLib::Parameter(gline->Lin2d(), P1);
        Standard_Real u2 = ElCLib::Parameter(gline->Lin2d(), P2);

        SPRING_DEBUG_STREAM << "u1 = " << u1 << "  u2 = " << u2 << "\n";
        SPRING_DEBUG_STREAM << "===================================================\n";

        return new Geom2d_TrimmedCurve(gline, u1, u2);
    }

    // Normals
    gp_Dir2d n1(-d1.Y(), d1.X());
    gp_Dir2d n2(-d2.Y(), d2.X());

    SPRING_DEBUG_STREAM << "n1 = (" << n1.X() << ", " << n1.Y() << ")\n";
    SPRING_DEBUG_STREAM << "n2 = (" << n2.X() << ", " << n2.Y() << ")\n";

    // Solve P1 + t*n1 = P2 + s*n2
    double A11 = n1.X();
    double A12 = -n2.X();
    double A21 = n1.Y();
    double A22 = -n2.Y();

    double B1 = P2.X() - P1.X();
    double B2 = P2.Y() - P1.Y();

    SPRING_DEBUG_STREAM << "A11=" << A11 << "  A12=" << A12 << "\n";
    SPRING_DEBUG_STREAM << "A21=" << A21 << "  A22=" << A22 << "\n";
    SPRING_DEBUG_STREAM << "B1=" << B1 << "  B2=" << B2 << "\n";

    double det = A11 * A22 - A12 * A21;
    SPRING_DEBUG_STREAM << "det = " << det << "\n";

    if (std::abs(det) < parallelTol)
    {
        SPRING_DEBUG_STREAM << "DEGENERATE: normals nearly parallel\n";
        SPRING_DEBUG_STREAM << "===================================================\n";
        return nullptr;
    }

    double invDet = 1.0 / det;
    double t = ( B1 * A22 - B2 * A12 ) * invDet;
    double s = ( A11 * B2 - A21 * B1 ) * invDet;

    SPRING_DEBUG_STREAM << "t = " << t << "\n";
    SPRING_DEBUG_STREAM << "s = " << s << "\n";

    // Center
    double Cx = P1.X() + t * n1.X();
    double Cy = P1.Y() + t * n1.Y();
    gp_Pnt2d Center(Cx, Cy);

    SPRING_DEBUG_STREAM << "Center = " << Center << "\n";

    // Radius from P1
    double dx1 = P1.X() - Cx;
    double dy1 = P1.Y() - Cy;
    double R1 = std::sqrt(dx1*dx1 + dy1*dy1);

    // Radius from P2
    double dx2 = P2.X() - Cx;
    double dy2 = P2.Y() - Cy;
    double R2 = std::sqrt(dx2*dx2 + dy2*dy2);

    SPRING_DEBUG_STREAM << "R1 (center->P1) = " << R1 << "\n";
    SPRING_DEBUG_STREAM << "R2 (center->P2) = " << R2 << "\n";
    SPRING_DEBUG_STREAM << "ΔR = " << std::abs(R1 - R2) << "\n";

    // Build circle
    gp_Ax2d axis(Center, gp_Dir2d(1.0, 0.0));
    gp_Circ2d circ(axis, R1);
    Handle(Geom2d_Circle) geomCirc = new Geom2d_Circle(circ);

    // Parameters
    Standard_Real u1 = ElCLib::Parameter(circ, P1);
    Standard_Real u2 = ElCLib::Parameter(circ, P2);

    SPRING_DEBUG_STREAM << "u1 = " << u1 << "\n";
    SPRING_DEBUG_STREAM << "u2 = " << u2 << "\n";

    // Normalize so the arc uses the *shortest path*.
    double du = u2 - u1;

    // If |du| > π → OCCT would jump across 2π
    // Fix that by shifting into the nearest equivalent branch.
    if (du >  M_PI)
    {
        u2 -= 2.0 * M_PI;
        du = u2 - u1;
    }
    else if (du < -M_PI)
    {
        u2 += 2.0 * M_PI;
        du = u2 - u1;
    }

    // Now ensure increasing order (TrimmedCurve requires it)
    if (u2 < u1)
    {
        std::swap(u1, u2);
    }

    SPRING_DEBUG_STREAM << "Corrected u1 = " << u1 << "\n";
    SPRING_DEBUG_STREAM << "Corrected u2 = " << u2 << "\n";
    SPRING_DEBUG_STREAM << "Corrected Δu = " << (u2 - u1) << "\n";

    Handle(Geom2d_TrimmedCurve) arc =
        new Geom2d_TrimmedCurve(geomCirc, u1, u2);

    SPRING_DEBUG_STREAM << "Arc created. Evaluated End: "
              << arc->Value(u2) << "\n";

    SPRING_DEBUG_STREAM << "===================================================\n";
    return arc;
}

inline Handle(Geom2d_BSplineCurve)
MakeCubicEaseTransition(const gp_Pnt2d& start,
                        const Standard_Real transitionTurns,
                        const Standard_Real startPitch,
                        const Standard_Real endPitch,
                        const Standard_Integer samples = 16)
{
    const Standard_Real deltaPitch = endPitch - startPitch;
    const Standard_Integer clampedSamples = (samples < 2) ? 2 : samples;
    TColgp_Array1OfPnt2d points(1, clampedSamples + 1);

    for (Standard_Integer i = 0; i <= clampedSamples; ++i)
    {
        const Standard_Real s = static_cast<Standard_Real>(i) /
                                 static_cast<Standard_Real>(clampedSamples);
        const Standard_Real theta = start.X() +
            s * transitionTurns * 2.0 * M_PI;

        const Standard_Real blendIntegral = s * s * s - 0.5 * s * s * s * s;
        const Standard_Real height = start.Y() + transitionTurns *
            (startPitch * s + deltaPitch * blendIntegral);

        points.SetValue(i + 1, gp_Pnt2d(theta, height));
    }

    Geom2dAPI_PointsToBSpline builder(points);
    return builder.Curve();
}

inline gp_Pnt
UVTo3D(
    const Standard_Real u,
    const Standard_Real v,
    const Standard_Real helixRadius,
    const Standard_Real zShift)
{
    return gp_Pnt(
        helixRadius * std::cos(u),
        helixRadius * std::sin(u),
        zShift + v
    );
}

inline Standard_Real
SmoothStep01(const Standard_Real sIn)
{
    Standard_Real s = sIn;
    if (s < 0.0) s = 0.0;
    if (s > 1.0) s = 1.0;
    return s * s * s * (10.0 + s * (-15.0 + 6.0 * s));
}

inline Handle(Geom_BSplineCurve)
Make3DBSplineFrom2DCurveVariableRadius(
    const Handle(Geom2d_Curve)& curve2d,
    const Standard_Real startRadius,
    const Standard_Real endRadius,
    const Standard_Real zShift,
    const Standard_Integer samples = 64)
{
    const Standard_Integer n = (samples < 2) ? 2 : samples;
    const Standard_Real t0 = curve2d->FirstParameter();
    const Standard_Real t1 = curve2d->LastParameter();

    TColgp_Array1OfPnt pts(1, n);

    for (Standard_Integer i = 0; i < n; ++i) {
        const Standard_Real s =
            static_cast<Standard_Real>(i) /
            static_cast<Standard_Real>(n - 1);

        const Standard_Real t = t0 + s * (t1 - t0);
        const gp_Pnt2d uv = curve2d->Value(t);
        const Standard_Real localRadius = startRadius + (endRadius - startRadius) * SmoothStep01(s);
        pts.SetValue(i + 1, UVTo3D(uv.X(), uv.Y(), localRadius, zShift));
    }

    GeomAPI_PointsToBSpline builder(pts);
    return builder.Curve();
}

inline Handle(Geom_BSplineCurve)
MakeCombinedSpringSpine3D(
    const Handle(Geom2d_TrimmedCurve)& bottomHelixSegment,
    const Handle(Geom2d_TrimmedCurve)& bottomTransitionSegment,
    const Handle(Geom2d_TrimmedCurve)& middleHelixSegment,
    const Handle(Geom2d_TrimmedCurve)& topTransitionSegment,
    const Handle(Geom2d_TrimmedCurve)& topHelixSegment,
    const Standard_Real helixRadius,
    const Standard_Real endHelixRadius,
    const Standard_Real zShift)
{
    const Standard_Real tol = Precision::Confusion();

    Handle(Geom_BSplineCurve) bottomHelix3d =
        Make3DBSplineFrom2DCurveVariableRadius(bottomHelixSegment, endHelixRadius, endHelixRadius, zShift, 48);
    Handle(Geom_BSplineCurve) bottomTransition3d =
        Make3DBSplineFrom2DCurveVariableRadius(bottomTransitionSegment, endHelixRadius, helixRadius, zShift, 48);
    Handle(Geom_BSplineCurve) middleHelix3d =
        Make3DBSplineFrom2DCurveVariableRadius(middleHelixSegment, helixRadius, helixRadius, zShift, 128);
    Handle(Geom_BSplineCurve) topTransition3d =
        Make3DBSplineFrom2DCurveVariableRadius(topTransitionSegment, helixRadius, endHelixRadius, zShift, 48);
    Handle(Geom_BSplineCurve) topHelix3d =
        Make3DBSplineFrom2DCurveVariableRadius(topHelixSegment, endHelixRadius, endHelixRadius, zShift, 48);

    GeomConvert_CompCurveToBSplineCurve concat(bottomHelix3d);
    if (!concat.Add(bottomTransition3d, tol)) {
        throw Standard_Failure("Failed to concatenate bottomTransition3d");
    }
    if (!concat.Add(middleHelix3d, tol)) {
        throw Standard_Failure("Failed to concatenate middleHelix3d");
    }
    if (!concat.Add(topTransition3d, tol)) {
        throw Standard_Failure("Failed to concatenate topTransition3d");
    }
    if (!concat.Add(topHelix3d, tol)) {
        throw Standard_Failure("Failed to concatenate topHelix3d");
    }

    return concat.BSplineCurve();
}

inline TopoDS_Wire
MakeSectionAt3D(
    const Handle(Geom_Curve)& spine3d,
    const Standard_Real curveParam,
    const Standard_Real radius)
{
    gp_Pnt P;
    gp_Vec T;
    spine3d->D1(curveParam, P, T);

    if (T.Magnitude() <= gp::Resolution()) {
        throw Standard_Failure("MakeSectionAt3D: tangent is degenerate");
    }
    T.Normalize();

    gp_Vec radial(P.X(), P.Y(), 0.0);
    if (radial.Magnitude() <= gp::Resolution()) {
        radial = gp_Vec(1.0, 0.0, 0.0);
    }
    radial.Normalize();

    gp_Vec Xdir = radial - (radial.Dot(T)) * T;
    if (Xdir.Magnitude() <= gp::Resolution()) {
        gp_Vec axis(0.0, 0.0, 1.0);
        Xdir = axis.Crossed(T);
        if (Xdir.Magnitude() <= gp::Resolution()) {
            Xdir = gp_Vec(1.0, 0.0, 0.0);
        }
    }
    Xdir.Normalize();

    gp_Ax2 ax;
    ax.SetLocation(P);
    ax.SetDirection(gp_Dir(T));
    ax.SetXDirection(gp_Dir(Xdir));

    gp_Circ circle(ax, radius);
    return BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(circle).Edge()).Wire();
}

inline Handle(Geom2d_BSplineCurve)
MakeCombinedSpringSegmentExact(
    const Handle(Geom2d_TrimmedCurve)& bottomHelixSegment,
    const Handle(Geom2d_TrimmedCurve)& bottomTransitionSegment,
    const Handle(Geom2d_TrimmedCurve)& middleHelixSegment,
    const Handle(Geom2d_TrimmedCurve)& topTransitionSegment,
    const Handle(Geom2d_TrimmedCurve)& topHelixSegment)
{
    const Standard_Real tol = Precision::Confusion();

    Handle(Geom2d_BSplineCurve) bottomHelixBs =
        Geom2dConvert::CurveToBSplineCurve(bottomHelixSegment);

    Geom2dConvert_CompCurveToBSplineCurve concat(bottomHelixBs);

    if (!concat.Add(Geom2dConvert::CurveToBSplineCurve(bottomTransitionSegment), tol)) {
        throw Standard_Failure("Failed to concatenate bottomTransitionSegment");
    }
    if (!concat.Add(Geom2dConvert::CurveToBSplineCurve(middleHelixSegment), tol)) {
        throw Standard_Failure("Failed to concatenate middleHelixSegment");
    }
    if (!concat.Add(Geom2dConvert::CurveToBSplineCurve(topTransitionSegment), tol)) {
        throw Standard_Failure("Failed to concatenate topTransitionSegment");
    }
    if (!concat.Add(Geom2dConvert::CurveToBSplineCurve(topHelixSegment), tol)) {
        throw Standard_Failure("Failed to concatenate topHelixSegment");
    }

    return concat.BSplineCurve();
}

TopoDS_Wire MakeSectionAt(const Handle(Geom_CylindricalSurface)& helixCylinder, double helixRadius, double u, double v, double pitch, double radius)
{
    SPRING_DEBUG_STREAM << "MakeSectionAt" << " u=" << u << " v=" << v << " pitch=" << pitch << " radius=" << radius << std::endl;
    gp_Pnt P = helixCylinder->Value(u, v);
    gp_Vec T(-helixRadius * sin(u), helixRadius * cos(u), pitch / (2.0 * M_PI));
    T.Normalize();
    gp_Vec radial(cos(u), sin(u), 0.0);     // surface normal
    gp_Vec axis(0,0,1);                    // cylinder axis
    gp_Vec Xdir = radial;
    gp_Vec Ydir = axis.Crossed(radial);    // guaranteed orthogonal
    Ydir.Normalize();
    Xdir.Normalize();
    gp_Ax2 ax;
    ax.SetLocation(P);
    ax.SetDirection(gp_Dir(T));            // section plane normal
    ax.SetXDirection(gp_Dir(Xdir));
    gp_Circ circle(ax, radius);
    return BRepBuilderAPI_MakeWire(BRepBuilderAPI_MakeEdge(circle).Edge()).Wire();
}

static void DumpSurfaceCurveFrameAt(const std::string& name,
                                    const Handle(Geom2d_Curve)& curve2d,
                                    const Standard_Real param,
                                    const Standard_Real helixRadius,
                                    const Standard_Real zShift)
{
    if (curve2d.IsNull()) {
        SPRING_DEBUG_STREAM << "---- Surface Curve Frame: " << name << " ----" << std::endl;
        SPRING_DEBUG_STREAM << "Curve is NULL" << std::endl;
        SPRING_DEBUG_STREAM << "----------------------------------------------" << std::endl;
        return;
    }

    gp_Pnt2d uv;
    gp_Vec2d duv;
    curve2d->D1(param, uv, duv);

    gp_Pnt P = UVTo3D(uv.X(), uv.Y(), helixRadius, zShift);
    gp_Vec dPdu(-helixRadius * std::sin(uv.X()),
                 helixRadius * std::cos(uv.X()),
                 0.0);
    gp_Vec dPdv(0.0, 0.0, 1.0);
    gp_Vec T = duv.X() * dPdu + duv.Y() * dPdv;

    if (T.Magnitude() > gp::Resolution()) {
        T.Normalize();
    }

    gp_Vec radial(std::cos(uv.X()), std::sin(uv.X()), 0.0);
    if (radial.Magnitude() > gp::Resolution()) {
        radial.Normalize();
    }

    const Standard_Real horizontalTangent =
        std::sqrt(T.X() * T.X() + T.Y() * T.Y());
    const Standard_Real tangentAngleDeg =
        std::atan2(T.Z(), horizontalTangent) * 180.0 / M_PI;
    const Standard_Real pitchFromUV =
        (std::abs(duv.X()) > Precision::Confusion())
            ? (duv.Y() / duv.X()) * 2.0 * M_PI
            : 0.0;

    SPRING_DEBUG_STREAM << "---- Surface Curve Frame: " << name << " ----" << std::endl;
    SPRING_DEBUG_STREAM << "param=" << param << std::endl;
    SPRING_DEBUG_STREAM << "uv=(" << uv.X() << ", " << uv.Y() << ")" << std::endl;
    SPRING_DEBUG_STREAM << "duv=(" << duv.X() << ", " << duv.Y() << ")" << std::endl;
    SPRING_DEBUG_STREAM << "P=(" << P.X() << ", " << P.Y() << ", " << P.Z() << ")" << std::endl;
    SPRING_DEBUG_STREAM << "T=(" << T.X() << ", " << T.Y() << ", " << T.Z() << ")" << std::endl;
    SPRING_DEBUG_STREAM << "radial=(" << radial.X() << ", " << radial.Y() << ", " << radial.Z() << ")" << std::endl;
    SPRING_DEBUG_STREAM << "TdotZ=" << T.Z() << std::endl;
    SPRING_DEBUG_STREAM << "tangentAngleDeg=" << tangentAngleDeg << std::endl;
    SPRING_DEBUG_STREAM << "pitchFromUV=" << pitchFromUV << std::endl;
    SPRING_DEBUG_STREAM << "----------------------------------------------" << std::endl;
}

static void DumpSurfaceCurveZExtrema(const std::string& name,
                                     const Handle(Geom2d_Curve)& curve2d,
                                     const Standard_Real helixRadius,
                                     const Standard_Real zShift,
                                     const Standard_Real profileRadius,
                                     Handle(SpringWireRadiusLaw)& radiusLaw,
                                     const Standard_Real u0,
                                     const Standard_Real u5,
                                     const Standard_Integer samples = 160)
{
    SPRING_DEBUG_STREAM << "---- Surface Curve Z Extrema: " << name << " ----" << std::endl;

    if (curve2d.IsNull()) {
        SPRING_DEBUG_STREAM << "Curve is NULL" << std::endl;
        SPRING_DEBUG_STREAM << "----------------------------------------------" << std::endl;
        return;
    }

    const Standard_Integer n = (samples < 2) ? 2 : samples;
    const Standard_Real p0 = curve2d->FirstParameter();
    const Standard_Real p1 = curve2d->LastParameter();

    Standard_Real minZ = std::numeric_limits<Standard_Real>::max();
    Standard_Real maxZ = -std::numeric_limits<Standard_Real>::max();
    Standard_Real minCenterZ = 0.0;
    Standard_Real maxCenterZ = 0.0;
    Standard_Real minVerticalRadius = 0.0;
    Standard_Real maxVerticalRadius = 0.0;
    Standard_Real minScale = 0.0;
    Standard_Real maxScale = 0.0;
    Standard_Real minU = 0.0;
    Standard_Real maxU = 0.0;
    Standard_Real minV = 0.0;
    Standard_Real maxV = 0.0;
    Standard_Real minTz = 0.0;
    Standard_Real maxTz = 0.0;

    for (Standard_Integer i = 0; i < n; ++i) {
        const Standard_Real a =
            static_cast<Standard_Real>(i) /
            static_cast<Standard_Real>(n - 1);
        const Standard_Real param = p0 + (p1 - p0) * a;

        gp_Pnt2d uv;
        gp_Vec2d duv;
        curve2d->D1(param, uv, duv);

        gp_Vec dPdu(-helixRadius * std::sin(uv.X()),
                     helixRadius * std::cos(uv.X()),
                     0.0);
        gp_Vec dPdv(0.0, 0.0, 1.0);
        gp_Vec T = duv.X() * dPdu + duv.Y() * dPdv;
        if (T.Magnitude() > gp::Resolution()) {
            T.Normalize();
        }

        Standard_Real s = 0.0;
        if (std::abs(u5 - u0) > Precision::Confusion()) {
            s = (uv.X() - u0) / (u5 - u0);
        }

        Standard_Real scale = 1.0;
        if (!radiusLaw.IsNull()) {
            scale = radiusLaw->Value(s);
        }

        const Standard_Real localRadius = profileRadius * scale;
        const Standard_Real verticalRadius =
            localRadius * std::sqrt(std::max(0.0, 1.0 - T.Z() * T.Z()));
        const Standard_Real centerZ = zShift + uv.Y();
        const Standard_Real lowZ = centerZ - verticalRadius;
        const Standard_Real highZ = centerZ + verticalRadius;

        if (lowZ < minZ) {
            minZ = lowZ;
            minCenterZ = centerZ;
            minVerticalRadius = verticalRadius;
            minScale = scale;
            minU = uv.X();
            minV = uv.Y();
            minTz = T.Z();
        }
        if (highZ > maxZ) {
            maxZ = highZ;
            maxCenterZ = centerZ;
            maxVerticalRadius = verticalRadius;
            maxScale = scale;
            maxU = uv.X();
            maxV = uv.Y();
            maxTz = T.Z();
        }
    }

    SPRING_DEBUG_STREAM << "minZ=" << minZ << std::endl;
    SPRING_DEBUG_STREAM << "minZCenter=" << minCenterZ
              << " minZVerticalRadius=" << minVerticalRadius
              << " minZScale=" << minScale
              << " minZU=" << minU
              << " minZV=" << minV
              << " minZTangentZ=" << minTz << std::endl;
    SPRING_DEBUG_STREAM << "maxZ=" << maxZ << std::endl;
    SPRING_DEBUG_STREAM << "maxZCenter=" << maxCenterZ
              << " maxZVerticalRadius=" << maxVerticalRadius
              << " maxZScale=" << maxScale
              << " maxZU=" << maxU
              << " maxZV=" << maxV
              << " maxZTangentZ=" << maxTz << std::endl;
    SPRING_DEBUG_STREAM << "----------------------------------------------" << std::endl;
}

static void DumpSurfaceMappedEndDiagnostics(const Handle(Geom2d_TrimmedCurve)& bottomHelixSegment,
                                            const Handle(Geom2d_TrimmedCurve)& bottomTransitionSegment,
                                            const Handle(Geom2d_TrimmedCurve)& topTransitionSegment,
                                            const Handle(Geom2d_TrimmedCurve)& topHelixSegment,
                                            const Standard_Real helixRadius,
                                            const Standard_Real zShift,
                                            const Standard_Real profileRadius,
                                            Handle(SpringWireRadiusLaw)& radiusLaw,
                                            const Standard_Real u0,
                                            const Standard_Real u5,
                                            const Standard_Real L_Free)
{
    if (!SpringDebugTaperedEnabled()) { return; }
    SPRING_DEBUG_STREAM << "---- Surface-Mapped End Diagnostics ----" << std::endl;
    SPRING_DEBUG_STREAM << "Expected ground planes: bottomZ=0 topZ=" << L_Free << std::endl;
    SPRING_DEBUG_STREAM << "This diagnostic samples the 2D surface-mapped end curves before boolean cutting." << std::endl;
    SPRING_DEBUG_STREAM << "It estimates local section Z-extents from the curve tangent and SpringWireRadiusLaw." << std::endl;
    SPRING_DEBUG_STREAM << "-----------------------------------------" << std::endl;

    if (!bottomHelixSegment.IsNull()) {
        DumpSurfaceCurveFrameAt("bottomHelix start", bottomHelixSegment, bottomHelixSegment->FirstParameter(), helixRadius, zShift);
        DumpSurfaceCurveFrameAt("bottomHelix end", bottomHelixSegment, bottomHelixSegment->LastParameter(), helixRadius, zShift);
        DumpSurfaceCurveZExtrema("bottomHelix", bottomHelixSegment, helixRadius, zShift, profileRadius, radiusLaw, u0, u5);
    }

    if (!bottomTransitionSegment.IsNull()) {
        DumpSurfaceCurveFrameAt("bottomTransition start", bottomTransitionSegment, bottomTransitionSegment->FirstParameter(), helixRadius, zShift);
        DumpSurfaceCurveFrameAt("bottomTransition end", bottomTransitionSegment, bottomTransitionSegment->LastParameter(), helixRadius, zShift);
        DumpSurfaceCurveZExtrema("bottomTransition", bottomTransitionSegment, helixRadius, zShift, profileRadius, radiusLaw, u0, u5);
    }

    if (!topTransitionSegment.IsNull()) {
        DumpSurfaceCurveFrameAt("topTransition start", topTransitionSegment, topTransitionSegment->FirstParameter(), helixRadius, zShift);
        DumpSurfaceCurveFrameAt("topTransition end", topTransitionSegment, topTransitionSegment->LastParameter(), helixRadius, zShift);
        DumpSurfaceCurveZExtrema("topTransition", topTransitionSegment, helixRadius, zShift, profileRadius, radiusLaw, u0, u5);
    }

    if (!topHelixSegment.IsNull()) {
        DumpSurfaceCurveFrameAt("topHelix start", topHelixSegment, topHelixSegment->FirstParameter(), helixRadius, zShift);
        DumpSurfaceCurveFrameAt("topHelix end", topHelixSegment, topHelixSegment->LastParameter(), helixRadius, zShift);
        DumpSurfaceCurveZExtrema("topHelix", topHelixSegment, helixRadius, zShift, profileRadius, radiusLaw, u0, u5);
    }

    SPRING_DEBUG_STREAM << "-----------------------------------------" << std::endl;
}

TopoDS_Shape compression_spring_solid(
    double outer_diameter,
    double wire_diameter,
    double free_length,
    double total_coils,
    int end_type,
    double inactive_coils)
{

    SPRING_DEBUG_STREAM << "Starting compression_spring_solid" << std::endl;

    TopoDS_Shape compressionSpring;
    try {
        // End Type Table
        enum End_Types {
            Open = 1,
            Open_Ground,
            Closed,
            Closed_Ground,
            DoubleClosed,
            DoubleClosed_Ground,
            TaperedClosed,
            TaperedClosed_Ground,
            PigtailClosed,
            PigtailClosed_Ground,
            UserSpecifiedOpen,
            UserSpecifiedOpen_Ground,
            UserSpecifiedClosed,
            UserSpecifiedClosed_Ground,
        };
        const Standard_Real r = kTaperAmount; // Taper_Amount

        Standard_Real OD_Free = outer_diameter;
        Standard_Real Wire_Dia = wire_diameter;
        Standard_Real L_Free = free_length;
        Standard_Real Coils_T = total_coils;
        SPRING_DEBUG_STREAM << "Independent: OD_Free=" << OD_Free << std::endl;
        SPRING_DEBUG_STREAM << "Independent: Wire_Dia=" << Wire_Dia << std::endl;
        SPRING_DEBUG_STREAM << "Independent: L_Free=" << L_Free << std::endl;
        SPRING_DEBUG_STREAM << "Independent: Coils_T=" << Coils_T << std::endl;
        SPRING_DEBUG_STREAM << std::endl;

        Standard_Integer End_Type = end_type;
        Standard_Real Coils_I = inactive_coils;
        SPRING_DEBUG_STREAM << "Global: End_Type=" << End_Type << std::endl;
        SPRING_DEBUG_STREAM << "Global: Coils_I=" << Coils_I << std::endl;
        SPRING_DEBUG_STREAM << std::endl;

        if (Wire_Dia <= 0.0) {
            throw Standard_Failure("Wire_diameter must be positive");
        }
        if (OD_Free <= Wire_Dia) {
            throw Standard_Failure("Outer_diameter must be greater than wire_diameter");
        }
        if (L_Free <= 0.0) {
            throw Standard_Failure("Free_length must be positive");
        }
        if (Coils_T <= 0.0) {
            throw Standard_Failure("Total_coils must be positive");
        }
        if (Coils_I < 0.0 || Coils_I > Coils_T) {
            throw Standard_Failure("Inactive_coils must be between zero and total_coils");
        }
        if (End_Type < End_Types::Open || End_Type > End_Types::UserSpecifiedClosed_Ground) {
            throw Standard_Failure("Invalid end_type");
        }
        if ((End_Type == End_Types::Closed ||
             End_Type == End_Types::Closed_Ground ||
             End_Type == End_Types::TaperedClosed ||
             End_Type == End_Types::TaperedClosed_Ground ||
             End_Type == End_Types::UserSpecifiedClosed ||
             End_Type == End_Types::UserSpecifiedClosed_Ground) &&
            Coils_I < 2.0) {
          throw Standard_Failure("Closed-style spring ends require at least 2 inactive coil");
        }
        if ((End_Type == End_Types::DoubleClosed ||
             End_Type == End_Types::DoubleClosed_Ground) &&
            Coils_I < 4.0) {
          throw Standard_Failure("Double-closed spring ends require at least 4 inactive coils");
        }
        Standard_Real active_coils = Coils_T - Coils_I;
        if (active_coils <= 0) {
          throw Standard_Failure("Active coils must be greater than zero.");
        }

        Standard_Real Mean_Dia = OD_Free - Wire_Dia;
        Standard_Real Coils_A = Coils_T - Coils_I;
        SPRING_DEBUG_STREAM << "Dependent: Mean_Dia=" << Mean_Dia << std::endl;
        SPRING_DEBUG_STREAM << "Dependent: Coils_A=" << Coils_A << std::endl;
        SPRING_DEBUG_STREAM << std::endl;


        Standard_Real profileRadius = Wire_Dia / 2.0;
        Standard_Real nominalScale = 1.0;
        Standard_Real profileRadius2 = profileRadius;
        Standard_Real endScale = nominalScale;
        if (End_Type == End_Types::TaperedClosed || End_Type == End_Types::TaperedClosed_Ground) {
            profileRadius2 = profileRadius * r;
            endScale = r;
        }
        SPRING_DEBUG_STREAM << "profileRadius=" << profileRadius << " profileRadius2=" << profileRadius2 << std::endl;
        SPRING_DEBUG_STREAM << "nominalScale=" << nominalScale << " endScale=" << endScale << std::endl;
        Standard_Real helixRadius = Mean_Dia / 2.0;
        const Standard_Boolean hasPigtailEnd =
            (End_Type == End_Types::PigtailClosed) ||
            (End_Type == End_Types::PigtailClosed_Ground);

        Standard_Real closedHelixCoils = (Coils_T - Coils_A) / 2.0; // Split between top and bottom
        Standard_Real closedHelixPitch = Wire_Dia;
        if (End_Type == End_Types::TaperedClosed || End_Type == End_Types::TaperedClosed_Ground) {
            closedHelixPitch = profileRadius + profileRadius2;
        }

        // Pigtail-specific end controls are kept isolated here.
        Standard_Real endHelixRadius = helixRadius;
        Standard_Real endHelixCoils = closedHelixCoils;
        Standard_Real endHelixPitch = closedHelixPitch;
        Standard_Real pigtailTargetRadius = helixRadius * kPigtailTargetRadiusFactor; // one-half of the middle diameter => half of middle mean radius
        Standard_Real transitionTurns = kDefaultTransitionTurns;
        if (hasPigtailEnd) {
            const Standard_Real springIndex = Mean_Dia / Wire_Dia;

            endHelixRadius = pigtailTargetRadius;
            if (endHelixRadius <= 0.0) {
                throw Standard_Failure("Pigtail end radius became non-positive");
            }

            // Keep the previously working baseline for higher spring index,
            // clamp the lowest-index region, and use a quadratic in the middle band
            // so the pigtail curl shortens gently at first and then more aggressively
            // as spring index falls toward the failure region.
            if (springIndex >= kPigtailHighSpringIndex) {
                endHelixCoils = kPigtailHighIndexEndCoils;
            } else if (springIndex <= kPigtailLowSpringIndex) {
                endHelixCoils = kPigtailLowIndexEndCoils;
            } else {
                const Standard_Real x = kPigtailHighSpringIndex - springIndex;  // x in [0, 2.5]
                endHelixCoils = kPigtailHighIndexEndCoils - 0.07 * x - 0.036 * x * x;
            }

            // Thicker / lower-index springs also need more room for the transition back
            // out to the body diameter.
            if (springIndex >= kPigtailHighSpringIndex) {
                transitionTurns = kDefaultTransitionTurns;
            } else if (springIndex <= kPigtailLowSpringIndex) {
                transitionTurns = kPigtailLowIndexTransitionTurns;
            } else {
                transitionTurns = kDefaultTransitionTurns +
                    (kPigtailHighSpringIndex - springIndex) *
                    ((kPigtailLowIndexTransitionTurns - kDefaultTransitionTurns) /
                     (kPigtailHighSpringIndex - kPigtailLowSpringIndex));
            }

            endHelixPitch = 0.0;   // planar curl at the end

            SPRING_DEBUG_STREAM << "springIndex=" << springIndex << std::endl;
            SPRING_DEBUG_STREAM << "adaptive endHelixCoils=" << endHelixCoils << std::endl;
            SPRING_DEBUG_STREAM << "adaptive transitionTurns=" << transitionTurns << std::endl;
        }
        SPRING_DEBUG_STREAM << "helixRadius=" << helixRadius << " endHelixRadius=" << endHelixRadius << std::endl;
        SPRING_DEBUG_STREAM << "endHelixCoils=" << endHelixCoils << " endHelixPitch=" << endHelixPitch << std::endl;
        SPRING_DEBUG_STREAM << std::endl;

        Standard_Real closedHelixHypotenuse = sqrt((2.0 * M_PI * 2.0 * M_PI) + (closedHelixPitch * closedHelixPitch));
        Standard_Real closedHelixHeight = closedHelixCoils * closedHelixPitch;
        SPRING_DEBUG_STREAM << "closedHelixCoils=" << closedHelixCoils << std::endl;
        SPRING_DEBUG_STREAM << "closedHelixPitch=" << closedHelixPitch << std::endl;
        SPRING_DEBUG_STREAM << "closedHelixHypotenuse=" << closedHelixHypotenuse << std::endl;
        SPRING_DEBUG_STREAM << "closedHelixHeight=" << closedHelixHeight << std::endl;

        SPRING_DEBUG_STREAM << "transitionTurns=" << transitionTurns << std::endl;
        SPRING_DEBUG_STREAM << std::endl;

        const Standard_Boolean hasGroundEnd =
            (End_Type == End_Types::Open_Ground) ||
            (End_Type == End_Types::Closed_Ground) ||
            (End_Type == End_Types::DoubleClosed_Ground) ||
            (End_Type == End_Types::TaperedClosed_Ground) ||
            (End_Type == End_Types::PigtailClosed_Ground) ||
            (End_Type == End_Types::UserSpecifiedOpen_Ground) ||
            (End_Type == End_Types::UserSpecifiedClosed_Ground);

        Standard_Real middleHelixPitch;
        const Standard_Boolean hasClosedEnd =
            (End_Type == End_Types::Closed) ||
            (End_Type == End_Types::Closed_Ground) ||
            (End_Type == End_Types::DoubleClosed) ||
            (End_Type == End_Types::DoubleClosed_Ground) ||
            (End_Type == End_Types::TaperedClosed) ||
            (End_Type == End_Types::TaperedClosed_Ground) ||
            (End_Type == End_Types::PigtailClosed) ||
            (End_Type == End_Types::PigtailClosed_Ground) ||
            (End_Type == End_Types::UserSpecifiedClosed && Coils_I > 0.0) ||
            (End_Type == End_Types::UserSpecifiedClosed_Ground && Coils_I > 0.0);

        Standard_Real middleHelixCoils = Coils_A;
        if (End_Type == End_Types::Open_Ground || End_Type == End_Types::UserSpecifiedOpen_Ground) {
          middleHelixCoils = Coils_T; // Special case
        } else if (hasPigtailEnd) {
          middleHelixCoils = Coils_T - 2.0 * endHelixCoils - 2.0 * transitionTurns;
        } else if (hasClosedEnd) {
          middleHelixCoils = Coils_A - 2.0 * transitionTurns;
        }

        if (middleHelixCoils <= 0.0) {
            throw Standard_Failure("Computed middle helix coil count must be positive");
        }
        if (middleHelixCoils + transitionTurns <= 0.0) {
            throw Standard_Failure("Computed middle pitch denominator must be positive");
        }

        switch (End_Type) {
            case End_Types::Open:
                middleHelixPitch = (L_Free - Wire_Dia) / Coils_A;
                break;
            case End_Types::Open_Ground:
                middleHelixPitch = L_Free / Coils_T;
                break;
            case End_Types::Closed:
                middleHelixPitch = (L_Free - (Coils_I + 1) * closedHelixPitch - transitionTurns * closedHelixPitch) / (middleHelixCoils + transitionTurns);
                break;
            case End_Types::Closed_Ground:
                middleHelixPitch = (L_Free - Coils_I * closedHelixPitch - transitionTurns * closedHelixPitch) / (middleHelixCoils + transitionTurns);
                break;
            case End_Types::DoubleClosed:
                middleHelixPitch = (L_Free - (Coils_I + 1) * closedHelixPitch - transitionTurns * closedHelixPitch) / (middleHelixCoils + transitionTurns);
                break;
            case End_Types::DoubleClosed_Ground:
                middleHelixPitch = (L_Free - Coils_I * closedHelixPitch - transitionTurns * closedHelixPitch) / (middleHelixCoils + transitionTurns);
                break;
            case End_Types::TaperedClosed:
                middleHelixPitch = (L_Free - ((9.0 + 3.0 * r) / 4.0) * closedHelixPitch - transitionTurns * closedHelixPitch) / (middleHelixCoils + transitionTurns);
                break;
            case End_Types::TaperedClosed_Ground:
                middleHelixPitch = (L_Free - Coils_I * closedHelixPitch - transitionTurns * closedHelixPitch) / (middleHelixCoils + transitionTurns);
                break;
            case End_Types::PigtailClosed:
                middleHelixPitch = (L_Free - Wire_Dia) / (middleHelixCoils + transitionTurns);
                break;
            case End_Types::PigtailClosed_Ground:
                middleHelixPitch = L_Free / (middleHelixCoils + transitionTurns);
                break;
            case End_Types::UserSpecifiedOpen:
            case End_Types::UserSpecifiedClosed:
                SPRING_DEBUG_STREAM << "L_Free=" << L_Free << std::endl;
                SPRING_DEBUG_STREAM << "Coils_I=" << Coils_I << std::endl;
                SPRING_DEBUG_STREAM << "closedHelixCoils=" << closedHelixCoils << std::endl;
                SPRING_DEBUG_STREAM << "closedHelixPitch=" << closedHelixPitch << std::endl;
                SPRING_DEBUG_STREAM << "transitionTurns=" << transitionTurns << std::endl;
                SPRING_DEBUG_STREAM << "Coils_A=" << Coils_A << std::endl;
                if (hasClosedEnd) { // Assume Closed
                    middleHelixPitch = (L_Free - (Coils_I + 1) * closedHelixPitch - transitionTurns * closedHelixPitch) / (middleHelixCoils + transitionTurns);
                } else { // Assume Open & Not Ground
                    middleHelixPitch = (L_Free - Wire_Dia) / Coils_A;
                }
                break;
            case End_Types::UserSpecifiedOpen_Ground:
            case End_Types::UserSpecifiedClosed_Ground:
                if (hasClosedEnd) { // Assume Closed & Ground
                    middleHelixPitch = (L_Free - Coils_I * closedHelixPitch - transitionTurns * closedHelixPitch) / (middleHelixCoils + transitionTurns);
                } else { // Assume Open & Ground
                    middleHelixPitch = L_Free / Coils_T;
                }
                break;
        }

        if (middleHelixPitch <= 0.0) {
            throw Standard_Failure("Computed middle helix pitch must be positive");
        }

        Standard_Real middleHelixHypotenuse = sqrt((2.0 * M_PI * 2.0 * M_PI) + (middleHelixPitch * middleHelixPitch));
        Standard_Real middleHelixHeight = middleHelixCoils * middleHelixPitch;
        SPRING_DEBUG_STREAM << "middleHelixCoils=" << middleHelixCoils << std::endl;
        SPRING_DEBUG_STREAM << "middleHelixPitch=" << middleHelixPitch << std::endl;
        SPRING_DEBUG_STREAM << "middleHelixHypotenuse=" << middleHelixHypotenuse << std::endl;
        SPRING_DEBUG_STREAM << "middleHelixHeight=" << middleHelixHeight << std::endl;
        SPRING_DEBUG_STREAM << std::endl;

        Standard_Real closedToMiddleTransitionHeight;
        Standard_Real middleToClosedTransitionHeight;
        if (hasPigtailEnd) {
            closedToMiddleTransitionHeight = 0.5 * transitionTurns * middleHelixPitch;
            middleToClosedTransitionHeight = 0.5 * transitionTurns * middleHelixPitch;
        } else {
            closedToMiddleTransitionHeight = transitionTurns * (closedHelixPitch + 0.5 * (middleHelixPitch - closedHelixPitch));
            middleToClosedTransitionHeight = transitionTurns * (middleHelixPitch + 0.5 * (closedHelixPitch - middleHelixPitch));
        }
        SPRING_DEBUG_STREAM << "closedToMiddleTransitionHeight=" << closedToMiddleTransitionHeight << std::endl;
        SPRING_DEBUG_STREAM << "middleToClosedTransitionHeight=" << middleToClosedTransitionHeight << std::endl;
        SPRING_DEBUG_STREAM << std::endl;

        /* ******************* */
        /* Create Profile Face */
        /* ******************* */

        double zShift = profileRadius2;
        if (hasGroundEnd) {
          zShift = 0.0; // No shift
        }

        SPRING_DEBUG_STREAM << "Profile Face" << std::endl;
        gp_Ax2 anAxis;
        anAxis.SetDirection(gp_Dir(0.0, -2. * M_PI, -closedHelixPitch));
        anAxis.SetLocation(gp_Pnt(helixRadius, 0.0, zShift));
        auto makeProfileWire = [&](Standard_Real radius) {
            gp_Circ profileCircle(anAxis, radius);
            TopoDS_Edge profileEdge = BRepBuilderAPI_MakeEdge(profileCircle).Edge();
            return BRepBuilderAPI_MakeWire(profileEdge).Wire();
        };
        TopoDS_Wire profileWire = makeProfileWire(profileRadius);

        /* ************************** */
        /* Create Cylindrical Surface */
        /* ************************** */

        gp_Ax2 helixOrigin(gp_Pnt(0.0, 0.0, zShift), gp_Dir(0.0, 0.0, 1.0));
        Handle(Geom_CylindricalSurface) helixCylinder = new Geom_CylindricalSurface(helixOrigin, helixRadius);
        SPRING_DEBUG_STREAM << std::endl;

        /* ******************* */
        /* Create Bottom Helix */
        /* ******************* */

        Standard_Real u0;
        Standard_Real u1;
        Standard_Real u2;
        Standard_Real u3;
        Standard_Real u4;
        Standard_Real u5;

        Standard_Real u_start = 0.0;
        Standard_Real v_start = 0.0;
        Standard_Real u = u_start;
        Standard_Real v = v_start;
        u0 = u;
        SPRING_DEBUG_STREAM << "at Begin u=" << u << " v=" << v << std::endl;

        Handle(Geom2d_TrimmedCurve) bottomHelixSegment;
        Handle(Geom2d_TrimmedCurve) bottomTransitionSegment;
        Handle(Geom2d_TrimmedCurve) middleHelixSegment;
        Handle(Geom2d_TrimmedCurve) topTransitionSegment;
        Handle(Geom2d_TrimmedCurve) topHelixSegment;

        if (hasClosedEnd) {
            // Create Bottom Helix
            SPRING_DEBUG_STREAM << "Create Bottom Helix" << std::endl;
            gp_Pnt2d bottomHelixP1(u, v);
            SPRING_DEBUG_STREAM << "bottomHelixP1=" << bottomHelixP1 << std::endl;
            gp_Pnt2d bottomHelixP2(u + endHelixCoils * 2. * M_PI, v + endHelixCoils * endHelixPitch);
            SPRING_DEBUG_STREAM << "bottomHelixP2=" << bottomHelixP2 << std::endl;
            Handle(Geom2d_Line) bottomHelixLine = GCE2d_MakeLine(bottomHelixP1, bottomHelixP2);
            SPRING_DEBUG_STREAM << "bottomHelixLine=" << bottomHelixLine << std::endl;
            bottomHelixSegment = new Geom2d_TrimmedCurve(bottomHelixLine, ElCLib::Parameter(bottomHelixLine->Lin2d(), bottomHelixP1), ElCLib::Parameter(bottomHelixLine->Lin2d(), bottomHelixP2));
            SPRING_DEBUG_STREAM << "bottomHelixSegment=" << bottomHelixSegment << std::endl;

            u += endHelixCoils * 2.0 * M_PI;
            v += endHelixCoils * endHelixPitch;
            u1 = u;
            SPRING_DEBUG_STREAM << "after Bottom Helix u=" << u << " v=" << v << std::endl;
            SPRING_DEBUG_STREAM << std::endl;

            // Create Bottom Transition
            SPRING_DEBUG_STREAM << "Create Bottom Transition" << std::endl;
            Handle(Geom2d_BSplineCurve) bottomTransitionCurve =
                MakeCubicEaseTransition(gp_Pnt2d(u, v),
                                        transitionTurns,
                                        hasPigtailEnd ? endHelixPitch : closedHelixPitch,
                                        middleHelixPitch);
            bottomTransitionSegment =
                new Geom2d_TrimmedCurve(bottomTransitionCurve,
                                        bottomTransitionCurve->FirstParameter(),
                                        bottomTransitionCurve->LastParameter());
            SPRING_DEBUG_STREAM << "bottomTransitionSegment=" << bottomTransitionSegment << std::endl;

            u += transitionTurns * 2.0 * M_PI;
            v += closedToMiddleTransitionHeight;
            u2 = u;
            SPRING_DEBUG_STREAM << "after Bottom Transition u=" << u << " v=" << v << std::endl;
            SPRING_DEBUG_STREAM << std::endl;
        }

        /* ******************* */
        /* Create Middle Helix */
        /* ******************* */

        gp_Pnt2d middleHelixP1(u, v);
        SPRING_DEBUG_STREAM << "middleHelixP1=" << middleHelixP1 << std::endl;
        gp_Pnt2d middleHelixP2(u + middleHelixCoils * 2. * M_PI, v + middleHelixCoils * middleHelixPitch);
        SPRING_DEBUG_STREAM << "middleHelixP2=" << middleHelixP2 << std::endl;
        Handle(Geom2d_Line) middleHelixLine = GCE2d_MakeLine(middleHelixP1, middleHelixP2);
        SPRING_DEBUG_STREAM << "middleHelixLine=" << middleHelixLine << std::endl;
        middleHelixSegment = new Geom2d_TrimmedCurve(middleHelixLine, ElCLib::Parameter(middleHelixLine->Lin2d(), middleHelixP1), ElCLib::Parameter(middleHelixLine->Lin2d(), middleHelixP2));
        SPRING_DEBUG_STREAM << "middleHelixSegment=" << middleHelixSegment << std::endl;

        u += middleHelixCoils * 2.0 * M_PI;
        v += middleHelixCoils * middleHelixPitch;
        u3 = u;
        SPRING_DEBUG_STREAM << "after Middle Helix u=" << u << " v=" << v << std::endl;
        SPRING_DEBUG_STREAM << std::endl;

        /* **************** */
        /* Create Top Helix */
        /* **************** */

        if (hasClosedEnd) {

            // Create Top Transition
            SPRING_DEBUG_STREAM << "Create Top Transition" << std::endl;
            Handle(Geom2d_BSplineCurve) topTransitionCurve =
                MakeCubicEaseTransition(gp_Pnt2d(u, v),
                                        transitionTurns,
                                        middleHelixPitch,
                                        hasPigtailEnd ? endHelixPitch : closedHelixPitch);
            topTransitionSegment =
                new Geom2d_TrimmedCurve(topTransitionCurve,
                                        topTransitionCurve->FirstParameter(),
                                        topTransitionCurve->LastParameter());
            SPRING_DEBUG_STREAM << "topTransitionSegment=" << topTransitionSegment << std::endl;

            u += transitionTurns * 2.0 * M_PI;
            v += middleToClosedTransitionHeight;
            u4 = u;
            SPRING_DEBUG_STREAM << "after Top Transition u=" << u << " v=" << v << std::endl;
            SPRING_DEBUG_STREAM << std::endl;

            // Create Top Helix
            SPRING_DEBUG_STREAM << "Create Top Helix" << std::endl;
            gp_Pnt2d topHelixP1(u, v);
            SPRING_DEBUG_STREAM << "topHelixP1=" << topHelixP1 << std::endl;
            gp_Pnt2d topHelixP2(u + endHelixCoils * 2. * M_PI, v + endHelixCoils * endHelixPitch);
            SPRING_DEBUG_STREAM << "topHelixP2=" << topHelixP2 << std::endl;
            Handle(Geom2d_Line) topHelixLine = GCE2d_MakeLine(topHelixP1, topHelixP2);
            SPRING_DEBUG_STREAM << "topHelixLine=" << topHelixLine << std::endl;
            topHelixSegment = new Geom2d_TrimmedCurve(topHelixLine, ElCLib::Parameter(topHelixLine->Lin2d(), topHelixP1), ElCLib::Parameter(topHelixLine->Lin2d(), topHelixP2));
            SPRING_DEBUG_STREAM << "topHelixSegment=" << topHelixSegment << std::endl;

            u += endHelixCoils * 2.0 * M_PI;
            v += endHelixCoils * endHelixPitch;
            u5 = u;
            SPRING_DEBUG_STREAM << "after Top Helix u=" << u << " v=" << v << std::endl;
            SPRING_DEBUG_STREAM << std::endl;
        }

        /* ******************************** */
        /* Create Helix Wire and Helix Pipe */
        /* ******************************** */

        TopoDS_Wire helixWire;
        TopoDS_Shape helixPipeShape;
        if (hasClosedEnd) {

            // Keep pigtail-specific behavior isolated here so the non-pigtail closed families
            // continue to use the proven surface-mapped path.
            if (hasPigtailEnd) {
                SPRING_DEBUG_STREAM << "Create Helix Wire from one exact combined 3D spine" << std::endl;
                Handle(Geom_BSplineCurve) combinedSpringSpine3d =
                    MakeCombinedSpringSpine3D(
                        bottomHelixSegment,
                        bottomTransitionSegment,
                        middleHelixSegment,
                        topTransitionSegment,
                        topHelixSegment,
                        helixRadius,
                        endHelixRadius,
                        zShift);
                TopoDS_Edge combinedSpringEdge =
                    BRepBuilderAPI_MakeEdge(combinedSpringSpine3d).Edge();
                helixWire = BRepBuilderAPI_MakeWire(combinedSpringEdge).Wire();

                // Make helixPipeShape here with varying profile radius from a law
                SPRING_DEBUG_STREAM << "Create Helix Pipe (single continuous sweep with SpringWireRadiusLaw)" << std::endl;
                BRepOffsetAPI_MakePipeShell pipe(helixWire);
                pipe.SetMode(Standard_True); // Frenet, or maybe gp_Dir(0, 0, 1)
                pipe.SetTransitionMode(BRepBuilderAPI_RoundCorner);

                // Use ONE nominal-radius profile, anchored at the start of the spring.
                // SpringWireRadiusLaw will scale this profile along the wire.
                TopoDS_Wire nominalProfile =
                    MakeSectionAt3D(
                        combinedSpringSpine3d,
                        combinedSpringSpine3d->FirstParameter(),
                        profileRadius);

                // --------------------------------------------------------------------
                // SpringWireRadiusLaw breakpoints
                //
                // These are normalized region boundaries for the single continuous
                // spring path. The law uses them to scale the wire profile smoothly
                // between tapered end regions and the nominal middle region.
                // --------------------------------------------------------------------
                SPRING_DEBUG_STREAM << "U-Values u0=" << u0 << " u1=" << u1 << " u2=" << u2 << " u3=" << u3 << " u4=" << u4 << " u5=" << u5 << std::endl;
                Standard_Real s0 = 0.0;
                Standard_Real s1 = (u1 - u0) / (u5 - u0);
                Standard_Real s2 = (u2 - u0) / (u5 - u0);
                Standard_Real s3 = (u3 - u0) / (u5 - u0);
                Standard_Real s4 = (u4 - u0) / (u5 - u0);
                Standard_Real s5 = 1.0;
                SPRING_DEBUG_STREAM << "Scale s0=" << s0 << " s1=" << s1 << " s2=" << s2 << " s3=" << s3 << " s4=" << s4 << " s5=" << s5 << std::endl;

                Handle(SpringWireRadiusLaw) radiusLaw = new SpringWireRadiusLaw(s0, s1, s2, s3, s4, s5, nominalScale /* nominal middle scale */, endScale /* for tapered half diameter / half radius relative to nominal profile */);

                auto dumpLaw = [&](const char* name, Standard_Real s)
                {
                    Standard_Real F, D, D2;
                    radiusLaw->D2(s, F, D, D2);
                    SPRING_DEBUG_STREAM << name
                              << "  s=" << s
                              << "  F=" << F
                              << "  D=" << D
                              << "  D2=" << D2
                              << std::endl;
                };

                dumpLaw("s0", s0);
                dumpLaw("mid01", 0.5 * (s0 + s1));
                dumpLaw("s1", s1);
                dumpLaw("mid12", 0.5 * (s1 + s2));
                dumpLaw("s2", s2);
                dumpLaw("mid23", 0.5 * (s2 + s3));
                dumpLaw("s3", s3);
                dumpLaw("mid34", 0.5 * (s3 + s4));
                dumpLaw("s4", s4);
                dumpLaw("mid45", 0.5 * (s4 + s5));
                dumpLaw("s5", s5);

                pipe.SetLaw(nominalProfile, radiusLaw, Standard_False /* WithContact*/, Standard_True /* WithCorrection */);

                pipe.Build();
                DumpPipeShellState("singlePipe after Build", pipe);
                Standard_Boolean flag = pipe.MakeSolid();
                SPRING_DEBUG_STREAM << "MakeSolid flag=" << (flag==true ? "success" : "fail") << std::endl;
                if (!flag) {
                    throw Standard_Failure("PipeShell MakeSolid failed");
                }
                DumpPipeShellState("singlePipe after MakeSolid", pipe);
                helixPipeShape = pipe.Shape();
                if (helixPipeShape.IsNull()) {
                    throw Standard_Failure("PipeShell produced a null shape");
                }
                DumpShapeState("helixPipeShape", helixPipeShape);
                {
                    Bnd_Box springBox;
                    BRepBndLib::Add(helixPipeShape, springBox);

                    Standard_Real xmin, ymin, zmin, xmax, ymax, zmax;
                    springBox.Get(xmin, ymin, zmin, xmax, ymax, zmax);

                    const Standard_Real bottomGroundStock = 0.0 - zmin;
                    const Standard_Real topGroundStock = zmax - L_Free;
                    const Standard_Real bodyInnerRadius = helixRadius - profileRadius;
                    const Standard_Real pigtailOuterRadius = endHelixRadius + profileRadius;
                    const Standard_Real pigtailClearance = bodyInnerRadius - pigtailOuterRadius;

                    SPRING_DEBUG_STREAM << "---- Grounding Diagnostics ----" << std::endl;
                    SPRING_DEBUG_STREAM << "bottomGroundStock=" << bottomGroundStock << std::endl;
                    SPRING_DEBUG_STREAM << "topGroundStock=" << topGroundStock << std::endl;
                    SPRING_DEBUG_STREAM << "bodyInnerRadius=" << bodyInnerRadius << std::endl;
                    SPRING_DEBUG_STREAM << "pigtailOuterRadius=" << pigtailOuterRadius << std::endl;
                    SPRING_DEBUG_STREAM << "pigtailClearance=" << pigtailClearance << std::endl;
                    SPRING_DEBUG_STREAM << "Wire_Dia=" << Wire_Dia
                              << " profileRadius=" << profileRadius
                              << " endHelixRadius=" << endHelixRadius
                              << " endHelixCoils=" << endHelixCoils
                              << " transitionTurns=" << transitionTurns
                              << " middleHelixPitch=" << middleHelixPitch << std::endl;

                    if (hasPigtailEnd) {
                        if (pigtailClearance <= 0.0) {
                            SPRING_DEBUG_STREAM << "WARNING: pigtailClearance <= 0, end loop may be too large for nesting" << std::endl;
                        }
                        if (bottomGroundStock <= 0.0) {
                            SPRING_DEBUG_STREAM << "WARNING: no bottom grind stock below z=0" << std::endl;
                        }
                        if (topGroundStock <= 0.0) {
                            SPRING_DEBUG_STREAM << "WARNING: no top grind stock above z=L_Free" << std::endl;
                        }
                    }

                    SPRING_DEBUG_STREAM << "-------------------------------" << std::endl;
                }

                DumpPigtailEndClearanceDiagnostics(
                    bottomHelixSegment,
                    bottomTransitionSegment,
                    middleHelixSegment,
                    topTransitionSegment,
                    topHelixSegment,
                    helixRadius,
                    endHelixRadius,
                    zShift,
                    Wire_Dia);
            } else {
                SPRING_DEBUG_STREAM << "Create Helix Wire from one exact combined spline edge" << std::endl;
                Handle(Geom2d_BSplineCurve) combinedSpringSegment =
                    MakeCombinedSpringSegmentExact(
                        bottomHelixSegment,
                        bottomTransitionSegment,
                        middleHelixSegment,
                        topTransitionSegment,
                        topHelixSegment);
                TopoDS_Edge combinedSpringEdge = BRepBuilderAPI_MakeEdge(combinedSpringSegment, helixCylinder).Edge();
                BRepLib::BuildCurve3d(combinedSpringEdge);
                helixWire = BRepBuilderAPI_MakeWire(combinedSpringEdge).Wire();

                // Make helixPipeShape here with varying profile radius from a law
                SPRING_DEBUG_STREAM << "Create Helix Pipe (single continuous sweep with SpringWireRadiusLaw)" << std::endl;
                BRepOffsetAPI_MakePipeShell pipe(helixWire);
                pipe.SetMode(Standard_True); // Frenet, or maybe gp_Dir(0, 0, 1)
                pipe.SetTransitionMode(BRepBuilderAPI_RoundCorner);

                // Use ONE nominal-radius profile, anchored at the start of the spring.
                // SpringWireRadiusLaw will scale this profile along the wire.
                TopoDS_Wire nominalProfile = MakeSectionAt(helixCylinder, helixRadius, u_start, v_start, closedHelixPitch, profileRadius);

                // --------------------------------------------------------------------
                // SpringWireRadiusLaw breakpoints
                //
                // These are normalized region boundaries for the single continuous
                // spring path. The law uses them to scale the wire profile smoothly
                // between tapered end regions and the nominal middle region.
                // --------------------------------------------------------------------
                SPRING_DEBUG_STREAM << "U-Values u0=" << u0 << " u1=" << u1 << " u2=" << u2 << " u3=" << u3 << " u4=" << u4 << " u5=" << u5 << std::endl;
                Standard_Real s0 = 0.0;
                Standard_Real s1 = (u1 - u0) / (u5 - u0);
                Standard_Real s2 = (u2 - u0) / (u5 - u0);
                Standard_Real s3 = (u3 - u0) / (u5 - u0);
                Standard_Real s4 = (u4 - u0) / (u5 - u0);
                Standard_Real s5 = 1.0;
                SPRING_DEBUG_STREAM << "Scale s0=" << s0 << " s1=" << s1 << " s2=" << s2 << " s3=" << s3 << " s4=" << s4 << " s5=" << s5 << std::endl;

                Handle(SpringWireRadiusLaw) radiusLaw = new SpringWireRadiusLaw(s0, s1, s2, s3, s4, s5, nominalScale /* nominal middle scale */, endScale /* for tapered half diameter / half radius relative to nominal profile */);

                auto dumpLaw = [&](const char* name, Standard_Real s)
                {
                    Standard_Real F, D, D2;
                    radiusLaw->D2(s, F, D, D2);
                    SPRING_DEBUG_STREAM << name
                              << "  s=" << s
                              << "  F=" << F
                              << "  D=" << D
                              << "  D2=" << D2
                              << std::endl;
                };

                dumpLaw("s0", s0);
                dumpLaw("mid01", 0.5 * (s0 + s1));
                dumpLaw("s1", s1);
                dumpLaw("mid12", 0.5 * (s1 + s2));
                dumpLaw("s2", s2);
                dumpLaw("mid23", 0.5 * (s2 + s3));
                dumpLaw("s3", s3);
                dumpLaw("mid34", 0.5 * (s3 + s4));
                dumpLaw("s4", s4);
                dumpLaw("mid45", 0.5 * (s4 + s5));
                dumpLaw("s5", s5);

                DumpSurfaceMappedEndDiagnostics(
                    bottomHelixSegment,
                    bottomTransitionSegment,
                    topTransitionSegment,
                    topHelixSegment,
                    helixRadius,
                    zShift,
                    profileRadius,
                    radiusLaw,
                    u0,
                    u5,
                    L_Free);

                pipe.SetLaw(nominalProfile, radiusLaw, Standard_False /* WithContact*/, Standard_True /* WithCorrection */);

                pipe.Build();
                DumpPipeShellState("singlePipe after Build", pipe);
                Standard_Boolean flag = pipe.MakeSolid();
                SPRING_DEBUG_STREAM << "MakeSolid flag=" << (flag==true ? "success" : "fail") << std::endl;
                if (!flag) {
                    throw Standard_Failure("PipeShell MakeSolid failed");
                }
                DumpPipeShellState("singlePipe after MakeSolid", pipe);
                helixPipeShape = pipe.Shape();
                if (helixPipeShape.IsNull()) {
                    throw Standard_Failure("PipeShell produced a null shape");
                }
                DumpShapeState("helixPipeShape", helixPipeShape);
                {
                    Bnd_Box springBox;
                    BRepBndLib::Add(helixPipeShape, springBox);

                    Standard_Real xmin, ymin, zmin, xmax, ymax, zmax;
                    springBox.Get(xmin, ymin, zmin, xmax, ymax, zmax);

                    const Standard_Real bottomGroundStock = 0.0 - zmin;
                    const Standard_Real topGroundStock = zmax - L_Free;
                    const Standard_Real bodyInnerRadius = helixRadius - profileRadius;
                    const Standard_Real pigtailOuterRadius = endHelixRadius + profileRadius;
                    const Standard_Real pigtailClearance = bodyInnerRadius - pigtailOuterRadius;

                    SPRING_DEBUG_STREAM << "---- Grounding Diagnostics ----" << std::endl;
                    SPRING_DEBUG_STREAM << "bottomGroundStock=" << bottomGroundStock << std::endl;
                    SPRING_DEBUG_STREAM << "topGroundStock=" << topGroundStock << std::endl;
                    SPRING_DEBUG_STREAM << "bodyInnerRadius=" << bodyInnerRadius << std::endl;
                    SPRING_DEBUG_STREAM << "pigtailOuterRadius=" << pigtailOuterRadius << std::endl;
                    SPRING_DEBUG_STREAM << "pigtailClearance=" << pigtailClearance << std::endl;
                    SPRING_DEBUG_STREAM << "Wire_Dia=" << Wire_Dia
                              << " profileRadius=" << profileRadius
                              << " endHelixRadius=" << endHelixRadius
                              << " endHelixCoils=" << endHelixCoils
                              << " transitionTurns=" << transitionTurns
                              << " middleHelixPitch=" << middleHelixPitch << std::endl;

                    if (hasPigtailEnd) {
                        if (pigtailClearance <= 0.0) {
                            SPRING_DEBUG_STREAM << "WARNING: pigtailClearance <= 0, end loop may be too large for nesting" << std::endl;
                        }
                        if (bottomGroundStock <= 0.0) {
                            SPRING_DEBUG_STREAM << "WARNING: no bottom grind stock below z=0" << std::endl;
                        }
                        if (topGroundStock <= 0.0) {
                            SPRING_DEBUG_STREAM << "WARNING: no top grind stock above z=L_Free" << std::endl;
                        }
                    }

                    SPRING_DEBUG_STREAM << "-------------------------------" << std::endl;
                }
            }
        } else {
            SPRING_DEBUG_STREAM << "Create Helix Wire from Middle Helix" << std::endl;
            TopoDS_Edge middleSpringEdge = BRepBuilderAPI_MakeEdge(middleHelixSegment, helixCylinder).Edge();
            BRepLib::BuildCurve3d(middleSpringEdge);
            helixWire = BRepBuilderAPI_MakeWire(middleSpringEdge).Wire();

            // Make helixPipeShape here with one profile
            BRepOffsetAPI_MakePipeShell helixPipe(helixWire);
            helixPipe.SetMode(Standard_True); // Frenet, or maybe gp_Dir(0, 0, 1)
            helixPipe.SetTransitionMode(BRepBuilderAPI_RoundCorner);
            helixPipe.Add(profileWire, Standard_False, Standard_True);
            helixPipe.Build();
            DumpPipeShellState("openPipe after Build", helixPipe);
            Standard_Boolean flag = helixPipe.MakeSolid();
            SPRING_DEBUG_STREAM << "MakeSolid flag=" << (flag==true ? "success" : "fail") << std::endl;
            if (!flag) {
                throw Standard_Failure("PipeShell MakeSolid failed");
            }
            DumpPipeShellState("openPipe after MakeSolid", helixPipe);
            helixPipeShape = helixPipe.Shape();
            if (helixPipeShape.IsNull()) {
                throw Standard_Failure("PipeShell produced a null shape");
            }
            DumpShapeState("openHelixPipeShape", helixPipeShape);
        }

        /* *********************************************************** */
        /* Form Compression Spring from Helix Pipe minus Helix Cutters */
        /* *********************************************************** */

        if (hasGroundEnd) {
            const Standard_Real grindExtra = 0.001 * Wire_Dia;

            // Create Bottom Cutter Box
            SPRING_DEBUG_STREAM << "Create Bottom Cutter Box" << std::endl;
            BRepPrimAPI_MakeBox bottomHelixBox(
                OD_Free * 2.0,
                OD_Free * 2.0,
                Wire_Dia * 2.0 + grindExtra);
            const TopoDS_Shape& bottomHelixCutter = bottomHelixBox.Shape();
            gp_Trsf bottomTrsf;
            bottomTrsf.SetTranslation(gp_Vec(-OD_Free, -OD_Free, -Wire_Dia * 2.0));
            TopoDS_Shape bottomHelixCutterTransformed = BRepBuilderAPI_Transform(bottomHelixCutter, bottomTrsf);
            DumpBBox("helixPipeShape", helixPipeShape);
            DumpBBox("bottomHelixCutterTransformed", bottomHelixCutterTransformed);
            DumpBBoxOverlap("helixPipeShape", helixPipeShape,
                            "bottomHelixCutterTransformed", bottomHelixCutterTransformed);

            // Create Top Cutter Box
            SPRING_DEBUG_STREAM << "Create Top Cutter Box" << std::endl;
            BRepPrimAPI_MakeBox topHelixBox(OD_Free * 2.0, OD_Free * 2.0, Wire_Dia * 2.0 + grindExtra);
            const TopoDS_Shape& topHelixCutter = topHelixBox.Shape();
            gp_Trsf topTrsf;
            topTrsf.SetTranslation(gp_Vec(-OD_Free, -OD_Free, L_Free + grindExtra));
            TopoDS_Shape topHelixCutterTransformed = BRepBuilderAPI_Transform(topHelixCutter, topTrsf);
            DumpBBox("topHelixCutterTransformed", topHelixCutterTransformed);
            DumpBBoxOverlap("helixPipeShape", helixPipeShape,
                            "topHelixCutterTransformed", topHelixCutterTransformed);

            SPRING_DEBUG_STREAM << std::endl;

            // Cut Bottom and Top Cutter Boxes from Total Helix Pipe
            SPRING_DEBUG_STREAM << "Create Compression Spring from Helix Pipe minus Cutters" << std::endl;

            const Standard_Real groundFuzzyValue = hasPigtailEnd ? 0.01 * Wire_Dia : 0.0;

            TopoDS_Shape cutAfterBottom = CutShape(
                helixPipeShape,
                bottomHelixCutterTransformed,
                "bottom ground cut",
                groundFuzzyValue);
            DumpShapeState("cutAfterBottom", cutAfterBottom);
            DumpCutDelta("bottom cut", helixPipeShape, cutAfterBottom);

            TopoDS_Shape cutAfterTop = CutShape(
                cutAfterBottom,
                topHelixCutterTransformed,
                "top ground cut",
                groundFuzzyValue);
            DumpShapeState("cutAfterTop", cutAfterTop);
            DumpCutDelta("top cut", cutAfterBottom, cutAfterTop);

            compressionSpring = hasPigtailEnd ? KeepLargestSolid(cutAfterTop) : cutAfterTop;
            if (hasPigtailEnd) {
                BRepPrimAPI_MakeBox groundEnvelopeBox(OD_Free * 2.0, OD_Free * 2.0, L_Free);
                const TopoDS_Shape& groundEnvelope = groundEnvelopeBox.Shape();
                gp_Trsf envelopeTrsf;
                envelopeTrsf.SetTranslation(gp_Vec(-OD_Free, -OD_Free, 0.0));
                TopoDS_Shape groundEnvelopeTransformed =
                    BRepBuilderAPI_Transform(groundEnvelope, envelopeTrsf);

                DumpBBox("groundEnvelopeTransformed", groundEnvelopeTransformed);
                DumpBBoxOverlap("compressionSpring before envelope clip", compressionSpring,
                                "groundEnvelopeTransformed", groundEnvelopeTransformed);

                compressionSpring = KeepLargestSolid(
                    CommonShape(
                        compressionSpring,
                        groundEnvelopeTransformed,
                        "pigtail ground envelope clip",
                        groundFuzzyValue));
            }
            DumpShapeState("compressionSpring after ground cleanup", compressionSpring);
        } else {
            SPRING_DEBUG_STREAM << "Create Compression Spring from Helix Pipe directly" << std::endl;
            compressionSpring = helixPipeShape;
        }

    } catch (const Standard_Failure& err) {
        const char* message = err.GetMessageString();
        throw std::runtime_error(
            message ? message : "OCCT Standard_Failure"
        );
    } catch (const std::exception& err) {
        throw std::runtime_error(
            std::string("std::exception: ") +
            err.what()
        );
    } catch (...) {
        throw std::runtime_error(
            "unknown C++ exception"
        );
    }

    if (compressionSpring.IsNull()) {
        throw Standard_Failure("Produced a null final shape");
    }

    BRepCheck_Analyzer finalAnalyzer(compressionSpring);
    if (!finalAnalyzer.IsValid()) {
        throw std::runtime_error(
            std::string("Produced an invalid final shape: ") +
            ShapeSummary(compressionSpring)
        );
    }

    SPRING_DEBUG_STREAM << "Ending compression_spring_solid" << std::endl;
    DumpShapeState("FINAL compressionSpring", compressionSpring);
    return compressionSpring;
}
