#include <BRepAlgoAPI_Cut.hxx>
#include <BRepAlgoAPI_Fuse.hxx>
#include <BRepBuilderAPI_MakeEdge.hxx>
#include <BRepBuilderAPI_MakeFace.hxx>
#include <BRepBuilderAPI_MakeWire.hxx>
#include <BRepBuilderAPI_Transform.hxx>
#include <BRepLib.hxx>
#include <BRepMesh_IncrementalMesh.hxx>
#include <BRepOffsetAPI_MakePipeShell.hxx>
#include <BRepPrimAPI_MakeBox.hxx>
#include <BRepTools.hxx>
#include <ElCLib.hxx>
#include <GCE2d_MakeArcOfCircle.hxx>
#include <GCE2d_MakeLine.hxx>
#include <Geom_CylindricalSurface.hxx>
#include <Geom_Plane.hxx>
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
#include <Geom2dAPI_PointsToBSpline.hxx>
#include <gp_Ax2d.hxx>
#include <gp_Circ.hxx>
#include <gp_Circ2d.hxx>
#include <gp_Lin2d.hxx>
#include <gp_Pnt2d.hxx>
#include <iostream>
#include <StlAPI_Writer.hxx>
#include <TColgp_Array1OfPnt2d.hxx>
#include <TopoDS_Edge.hxx>
#include <TopoDS_Face.hxx>
#include <TopoDS_Shape.hxx>
#include <TopoDS_Wire.hxx>

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
   std::cout << "========== MakeTangentialArcOrLine DEBUG ==========\n";

    std::cout << "Input P1 = " << P1 << "\n";
    std::cout << "Input L1 = " << L1 << "\n";
    std::cout << "Input P2 = " << P2 << "\n";
    std::cout << "Input L2 = " << L2 << "\n\n";

    // Directions
    gp_Dir2d d1 = L1.Direction();
    gp_Dir2d d2 = L2.Direction();

    std::cout << "d1 = (" << d1.X() << ", " << d1.Y() << ")\n";
    std::cout << "d2 = (" << d2.X() << ", " << d2.Y() << ")\n";

    double cross = d1.X() * d2.Y() - d1.Y() * d2.X();
    std::cout << "cross(d1,d2) = " << cross << "\n";

    // Parallel case
    if (std::abs(cross) < parallelTol)
    {
        std::cout << "LINES PARALLEL → returning straight segment\n";

        Handle(Geom2d_Line) gline = new Geom2d_Line(P1, d1);

        Standard_Real u1 = ElCLib::Parameter(gline->Lin2d(), P1);
        Standard_Real u2 = ElCLib::Parameter(gline->Lin2d(), P2);

        std::cout << "u1 = " << u1 << "  u2 = " << u2 << "\n";
        std::cout << "===================================================\n";

        return new Geom2d_TrimmedCurve(gline, u1, u2);
    }

    // Normals
    gp_Dir2d n1(-d1.Y(), d1.X());
    gp_Dir2d n2(-d2.Y(), d2.X());

    std::cout << "n1 = (" << n1.X() << ", " << n1.Y() << ")\n";
    std::cout << "n2 = (" << n2.X() << ", " << n2.Y() << ")\n";

    // Solve P1 + t*n1 = P2 + s*n2
    double A11 = n1.X();
    double A12 = -n2.X();
    double A21 = n1.Y();
    double A22 = -n2.Y();

    double B1 = P2.X() - P1.X();
    double B2 = P2.Y() - P1.Y();

    std::cout << "A11=" << A11 << "  A12=" << A12 << "\n";
    std::cout << "A21=" << A21 << "  A22=" << A22 << "\n";
    std::cout << "B1=" << B1 << "  B2=" << B2 << "\n";

    double det = A11 * A22 - A12 * A21;
    std::cout << "det = " << det << "\n";

    if (std::abs(det) < parallelTol)
    {
        std::cout << "DEGENERATE: normals nearly parallel\n";
        std::cout << "===================================================\n";
        return nullptr;
    }

    double invDet = 1.0 / det;
    double t = ( B1 * A22 - B2 * A12 ) * invDet;
    double s = ( A11 * B2 - A21 * B1 ) * invDet;

    std::cout << "t = " << t << "\n";
    std::cout << "s = " << s << "\n";

    // Center
    double Cx = P1.X() + t * n1.X();
    double Cy = P1.Y() + t * n1.Y();
    gp_Pnt2d Center(Cx, Cy);

    std::cout << "Center = " << Center << "\n";

    // Radius from P1
    double dx1 = P1.X() - Cx;
    double dy1 = P1.Y() - Cy;
    double R1 = std::sqrt(dx1*dx1 + dy1*dy1);

    // Radius from P2
    double dx2 = P2.X() - Cx;
    double dy2 = P2.Y() - Cy;
    double R2 = std::sqrt(dx2*dx2 + dy2*dy2);

    std::cout << "R1 (center->P1) = " << R1 << "\n";
    std::cout << "R2 (center->P2) = " << R2 << "\n";
    std::cout << "ΔR = " << std::abs(R1 - R2) << "\n";

    // Build circle
    gp_Ax2d axis(Center, gp_Dir2d(1.0, 0.0)); 
    gp_Circ2d circ(axis, R1);
    Handle(Geom2d_Circle) geomCirc = new Geom2d_Circle(circ);

    // Parameters
    Standard_Real u1 = ElCLib::Parameter(circ, P1);
    Standard_Real u2 = ElCLib::Parameter(circ, P2);

    std::cout << "u1 = " << u1 << "\n";
    std::cout << "u2 = " << u2 << "\n";

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
    
    std::cout << "Corrected u1 = " << u1 << "\n";
    std::cout << "Corrected u2 = " << u2 << "\n";
    std::cout << "Corrected Δu = " << (u2 - u1) << "\n";

    Handle(Geom2d_TrimmedCurve) arc =
        new Geom2d_TrimmedCurve(geomCirc, u1, u2);

    std::cout << "Arc created. Evaluated End: "
              << arc->Value(u2) << "\n";

    std::cout << "===================================================\n";
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

TopoDS_Shape compression_spring_solid(
    double outer_diameter,
    double wire_diameter,
    double free_length,
    double total_coils,
    double inactive_coils,
    int end_type)
{

    std::cout << "Starting compression_spring_solid" << std::endl;

    TopoDS_Shape compressionSpring;
    try {
        // End Type Table
        enum End_Types {    // [ "End_Type","Inactive_Coils","Add_Coils@Solid" ],
            Open = 1,       // 1 [ "Open",           0.0,       1.0],
            Open_Ground,   // 2 [ "Open&Ground",    1.0,       0.0],
            Closed,        // 3 [ "Closed",         2.0,       1.0],
            Closed_Ground, // 4 [ "Closed&Ground",  2.0,       0.0],
            Tapered_C_G,   // 5 [ "Tapered_C&G",    2.0,      -0.5],
            Pig_tail,      // 6 [ "Pig-tail",       2.0,       0.0],
            User_Specified,// 7 [ "User_Specified", 0.0,       0.0]
        };

        Standard_Real OD_Free = outer_diameter;
        Standard_Real Wire_Dia = wire_diameter;
        Standard_Real L_Free = free_length;
        Standard_Real Coils_T = total_coils;
        Standard_Integer End_Type = end_type;
        std::cout << "OD_Free=" << OD_Free << std::endl;
        std::cout << "Wire_Dia=" << Wire_Dia << std::endl;
        std::cout << "L_Free=" << L_Free << std::endl;
        std::cout << "Coils_T=" << Coils_T << std::endl;
        std::cout << "End_Type=" << End_Type << std::endl;
        std::cout << std::endl;

        Standard_Real Mean_Dia = OD_Free - Wire_Dia;
        Standard_Real Coils_A = Coils_T - inactive_coils;
        std::cout << "Mean_Dia=" << Mean_Dia << std::endl;
        std::cout << "Coils_A=" << Coils_A << std::endl;
        std::cout << std::endl;

//        Standard_Real LevelOfDetail = level_of_detail; // Level of Detail
//        Standard_Real LinearDeflection = Mean_Dia/LevelOfDetail;
//        std::cout << "LevelOfDetail=" << LevelOfDetail << std::endl;
//        std::cout << "LinearDeflection=" << LinearDeflection << std::endl;
//        std::cout << std::endl;

        Standard_Real profileRadius = Wire_Dia / 2.0;
        Standard_Real helixRadius = Mean_Dia / 2.0;
        std::cout << "profileRadius=" << profileRadius << std::endl;
        std::cout << "helixRadius=" << helixRadius << std::endl;
        std::cout << std::endl;

        Standard_Real closedHelixCoils = (Coils_T - Coils_A) / 2.0; // Split between top and bottom
        Standard_Real closedHelixPitch = Wire_Dia;
        Standard_Real closedHelixHypotenuse = sqrt((2.0 * M_PI * 2.0 * M_PI) + (closedHelixPitch * closedHelixPitch));
        Standard_Real closedHelixHeight = closedHelixCoils * closedHelixPitch;
        std::cout << "closedHelixCoils=" << closedHelixCoils << std::endl;
        std::cout << "closedHelixPitch=" << closedHelixPitch << std::endl;
        std::cout << "closedHelixHypotenuse=" << closedHelixHypotenuse << std::endl;
        std::cout << "closedHelixHeight=" << closedHelixHeight << std::endl;

        Standard_Real transitionTurns = 0.5;
        std::cout << "transitionTurns=" << transitionTurns << std::endl;
        std::cout << std::endl;

        Standard_Real middleHelixCoils = Coils_A;
//        if (Coils_T - Coils_A > 0.0) {
//            middleHelixCoils -= 2.0 * maxTransitionCoils;
//        }
        Standard_Real middleHelixPitch;
        switch (End_Type) {
            case End_Types::Open:
                middleHelixPitch = (L_Free - Wire_Dia) / Coils_A;
                break;
            case End_Types::Open_Ground:
                middleHelixPitch = L_Free / Coils_T;
                break;
            case End_Types::Closed:
               middleHelixPitch =
                    (L_Free - 3.0 * closedHelixCoils * closedHelixPitch -
                     transitionTurns * closedHelixPitch) /
                    (Coils_A + transitionTurns);
                break;
            case End_Types::Closed_Ground:
                middleHelixPitch =
                    (L_Free - 2.0 * closedHelixCoils * closedHelixPitch -
                     transitionTurns * closedHelixPitch) /
                    (Coils_A + transitionTurns);
                break;
            case End_Types::Tapered_C_G:
                middleHelixPitch = (L_Free - 1.5 * Wire_Dia)  / Coils_A;
                break;
            case End_Types::Pig_tail:
                middleHelixPitch = (L_Free - 2.0 * Wire_Dia)  / Coils_A;
                break;
            case End_Types::User_Specified:
                middleHelixPitch = (L_Free - (Coils_T - Coils_A + 1) * Wire_Dia)  / Coils_A;
                break;
        }
        Standard_Real middleHelixHypotenuse = sqrt((2.0 * M_PI * 2.0 * M_PI) + (middleHelixPitch * middleHelixPitch));
        Standard_Real middleHelixHeight = middleHelixCoils * middleHelixPitch;
        std::cout << "middleHelixCoils=" << middleHelixCoils << std::endl;
        std::cout << "middleHelixPitch=" << middleHelixPitch << std::endl;
        std::cout << "middleHelixHypotenuse=" << middleHelixHypotenuse << std::endl;
        std::cout << "middleHelixHeight=" << middleHelixHeight << std::endl;
        std::cout << std::endl;

        Standard_Real closedToMiddleTransitionHeight = transitionTurns *
            (closedHelixPitch + 0.5 * (middleHelixPitch - closedHelixPitch));
        Standard_Real middleToClosedTransitionHeight = transitionTurns *
            (middleHelixPitch + 0.5 * (closedHelixPitch - middleHelixPitch));
        std::cout << "closedToMiddleTransitionHeight=" << closedToMiddleTransitionHeight << std::endl;
        std::cout << "middleToClosedTransitionHeight=" << middleToClosedTransitionHeight << std::endl;
        std::cout << std::endl;

        Handle(Geom_Plane) plane = new Geom_Plane(gp_Ax3 ()); // Debugging tool
//        Standard_Boolean brep_result;
        
        /* ******************* */
        /* Create Profile Face */
        /* ******************* */

        std::cout << "Profile Face" << std::endl;
        gp_Ax2 anAxis;
        anAxis.SetDirection(gp_Dir(0.0, -2. * M_PI, -closedHelixPitch));
        anAxis.SetLocation(gp_Pnt(helixRadius, 0.0, 0.0));
        gp_Circ profileCircle(anAxis, profileRadius);
        TopoDS_Edge profileEdge = BRepBuilderAPI_MakeEdge(profileCircle).Edge();
        TopoDS_Wire profileWire = BRepBuilderAPI_MakeWire(profileEdge).Wire();
        TopoDS_Face profileFace = BRepBuilderAPI_MakeFace(profileWire).Face();

        /* ************************** */
        /* Create Cylindrical Surface */
        /* ************************** */

        gp_Ax2 helixOrigin(gp_Pnt(0.0, 0.0, 0.0), gp_Dir(0.0, 0.0, 1.0));
        Handle(Geom_CylindricalSurface) helixCylinder = new Geom_CylindricalSurface(helixOrigin, helixRadius);
        std::cout << std::endl;

        Standard_Real u = 0.0;
        Standard_Real v = 0.0;
        std::cout << "at Begin u=" << u << " v=" << v << std::endl;

        /* ******************* */
        /* Create Bottom Helix */
        /* ******************* */

        TopoDS_Edge planeBottomHelixEdge;
        TopoDS_Edge planeBottomTransitionEdge;
        TopoDS_Edge bottomHelixEdge;
        TopoDS_Edge bottomTransitionEdge;
        if (End_Type == End_Types::Closed || End_Type == End_Types::Closed_Ground) {
            // Create Bottom Helix
            std::cout << "Create Bottom Helix" << std::endl;
            gp_Pnt2d bottomHelixP1(u, v);
            std::cout << "bottomHelixP1=" << bottomHelixP1 << std::endl; // @@@ DUMP @@@
            gp_Pnt2d bottomHelixP2(u + closedHelixCoils * 2. * M_PI, v + closedHelixCoils * closedHelixPitch);
            std::cout << "bottomHelixP2=" << bottomHelixP2 << std::endl; // @@@ DUMP @@@
            Handle(Geom2d_Line) bottomHelixLine = GCE2d_MakeLine(bottomHelixP1, bottomHelixP2);
            std::cout << "bottomHelixLine=" << bottomHelixLine << std::endl; // @@@ DUMP @@@
            Handle(Geom2d_TrimmedCurve) bottomHelixSegment = new Geom2d_TrimmedCurve(bottomHelixLine, ElCLib::Parameter(bottomHelixLine->Lin2d(), bottomHelixP1), ElCLib::Parameter(bottomHelixLine->Lin2d(), bottomHelixP2));
            std::cout << "bottomHelixSegment=" << bottomHelixSegment << std::endl; // @@@ DUMP @@@
            bottomHelixEdge = BRepBuilderAPI_MakeEdge(bottomHelixSegment, helixCylinder).Edge();
//            std::cout << "Write bottomHelixEdge="; BRepTools::Dump(bottomHelixEdge, std::cout); std::cout << std::endl; // @@@ DUMP @@@
            BRepLib::BuildCurve3d(bottomHelixEdge);

//            planeBottomHelixEdge = BRepBuilderAPI_MakeEdge(bottomHelixLine, plane, 0.0, closedHelixCoils * closedHelixHypotenuse).Edge();
//            brep_result = BRepTools::Write(bottomHelixEdge, "bottomHelixEdge.brep", Standard_False, Standard_False, TopTools_FormatVersion_VERSION_1);
//            std::cout << "Write bottomHelixEdge brep_result=" << (brep_result==true ? "success" : "fail") << std::endl;
//            brep_result = BRepTools::Write(planeBottomHelixEdge, "planeBottomHelixEdge.brep", Standard_False, Standard_False, TopTools_FormatVersion_VERSION_1);
//            std::cout << "Write planeBottomHelixEdge brep_result=" << (brep_result==true ? "success" : "fail") << std::endl;
            u += closedHelixCoils * 2.0 * M_PI;
            v += closedHelixCoils * closedHelixPitch;
            std::cout << "after Bottom Helix u=" << u << " v=" << v << std::endl;
            std::cout << std::endl;

            // Create Bottom Transition
            std::cout << "Create Bottom Transition" << std::endl;
            Handle(Geom2d_BSplineCurve) bottomTransitionCurve =
                MakeCubicEaseTransition(gp_Pnt2d(u, v),
                                        transitionTurns,
                                        closedHelixPitch,
                                        middleHelixPitch);
            Handle(Geom2d_TrimmedCurve) bottomTransitionSegment =
                new Geom2d_TrimmedCurve(bottomTransitionCurve,
                                        bottomTransitionCurve->FirstParameter(),
                                        bottomTransitionCurve->LastParameter());
            std::cout << "bottomTransitionSegment=" << bottomTransitionSegment << std::endl; // @@@ DUMP @@@
            bottomTransitionEdge = BRepBuilderAPI_MakeEdge(bottomTransitionSegment, helixCylinder).Edge();
//            std::cout << "Write bottomTransitionEdge="; BRepTools::Dump(bottomTransitionEdge, std::cout); // @@@ DUMP @@@
            BRepLib::BuildCurve3d(bottomTransitionEdge);

//            planeBottomTransitionEdge = BRepBuilderAPI_MakeEdge(bottomTransitionSegment, plane).Edge();
//            brep_result = BRepTools::Write(bottomTransitionEdge, "bottomTransitionEdge.brep", Standard_False, Standard_False, TopTools_FormatVersion_VERSION_1);
//            std::cout << "Write bottomTransitionEdge brep_result=" << (brep_result==true ? "success" : "fail") << std::endl;
//            brep_result = BRepTools::Write(planeBottomTransitionEdge, "planeBottomTransitionEdge.brep", Standard_False, Standard_False, TopTools_FormatVersion_VERSION_1);
//            std::cout << "Write planeBottomTransitionEdge brep_result=" << (brep_result==true ? "success" : "fail") << std::endl;
            u += transitionTurns * 2.0 * M_PI;
            v += closedToMiddleTransitionHeight;
            std::cout << "after Bottom Transition u=" << u << " v=" << v << std::endl;
            std::cout << std::endl;
        }

        /* ******************* */
        /* Create Middle Helix */
        /* ******************* */

        TopoDS_Edge middleHelixEdge;
//        Standard_Real middleHelixZ;
//        if (End_Type == End_Types::Closed || End_Type == End_Types::Closed_Ground) {
//            std::cout << "Create Middle Helix at Closed Height" << std::endl;
//            middleHelixZ = closedHelixHeight + closedTransitionHeight + middleTransitionHeight;
//        } else {
//            std::cout << "Create Middle Helix at 0.0" << std::endl;
//            middleHelixZ = 0.0;
//        }
        gp_Pnt2d middleHelixP1(u, v);
        std::cout << "middleHelixP1=" << middleHelixP1 << std::endl; // @@@ DUMP @@@
        gp_Pnt2d middleHelixP2(u + middleHelixCoils * 2. * M_PI, v + middleHelixCoils * middleHelixPitch);
        std::cout << "middleHelixP2=" << middleHelixP2 << std::endl; // @@@ DUMP @@@
        Handle(Geom2d_Line) middleHelixLine = GCE2d_MakeLine(middleHelixP1, middleHelixP2);
        std::cout << "middleHelixLine=" << middleHelixLine << std::endl; // @@@ DUMP @@@
        Handle(Geom2d_TrimmedCurve) middleHelixSegment = new Geom2d_TrimmedCurve(middleHelixLine, ElCLib::Parameter(middleHelixLine->Lin2d(), middleHelixP1), ElCLib::Parameter(middleHelixLine->Lin2d(), middleHelixP2));
        std::cout << "middleHelixSegment=" << middleHelixSegment << std::endl; // @@@ DUMP @@@
        middleHelixEdge = BRepBuilderAPI_MakeEdge(middleHelixSegment, helixCylinder).Edge();
//        std::cout << "Write middleHelixEdge="; BRepTools::Dump(middleHelixEdge, std::cout); // @@@ DUMP @@@
        BRepLib::BuildCurve3d(middleHelixEdge);

//        TopoDS_Edge planeMiddleHelixEdge = BRepBuilderAPI_MakeEdge(middleHelixSegment, plane, 0.0, middleHelixCoils * middleHelixHypotenuse).Edge();
//        brep_result = BRepTools::Write(middleHelixEdge, "middleHelixEdge.brep", Standard_False, Standard_False, TopTools_FormatVersion_VERSION_1);
//        std::cout << "Write middleHelixEdge brep_result=" << (brep_result==true ? "success" : "fail") << std::endl;
//        brep_result = BRepTools::Write(planeMiddleHelixEdge, "planeMiddleHelixEdge.brep", Standard_False, Standard_False, TopTools_FormatVersion_VERSION_1);
//        std::cout << "Write planeMiddleHelixEdge brep_result=" << (brep_result==true ? "success" : "fail") << std::endl;
        u += middleHelixCoils * 2.0 * M_PI;
        v += middleHelixCoils * middleHelixPitch;
        std::cout << "after Middle Helix u=" << u << " v=" << v << std::endl;
        std::cout << std::endl;

        /* **************** */
        /* Create Top Helix */
        /* **************** */

        TopoDS_Edge topHelixEdge;
        TopoDS_Edge topTransitionEdge;
        TopoDS_Edge planeTopHelixEdge;
        TopoDS_Edge planeTopTransitionEdge;
        if (End_Type == End_Types::Closed || End_Type == End_Types::Closed_Ground) {
            
            // Create Top Transition
            std::cout << "Create Top Transition" << std::endl;
            Handle(Geom2d_BSplineCurve) topTransitionCurve =
                MakeCubicEaseTransition(gp_Pnt2d(u, v),
                                        transitionTurns,
                                        middleHelixPitch,
                                        closedHelixPitch);
            Handle(Geom2d_TrimmedCurve) topTransitionSegment =
                new Geom2d_TrimmedCurve(topTransitionCurve,
                                        topTransitionCurve->FirstParameter(),
                                        topTransitionCurve->LastParameter());
            std::cout << "topTransitionSegment=" << topTransitionSegment << std::endl; // @@@ DUMP @@@
            topTransitionEdge = BRepBuilderAPI_MakeEdge(topTransitionSegment, helixCylinder).Edge();
//            std::cout << "Write topTransitionEdge="; BRepTools::Dump(topTransitionEdge, std::cout); // @@@ DUMP @@@
            BRepLib::BuildCurve3d(topTransitionEdge);
            
//            planeTopTransitionEdge = BRepBuilderAPI_MakeEdge(topTransitionSegment, plane).Edge();
//            brep_result = BRepTools::Write(topTransitionEdge, "topTransitionEdge.brep", Standard_False, Standard_False, TopTools_FormatVersion_VERSION_1);
//            std::cout << "Write topTransitionEdge brep_result=" << (brep_result==true ? "success" : "fail") << std::endl;
//            brep_result = BRepTools::Write(planeTopTransitionEdge, "planeTopTransitionEdge.brep", Standard_False, Standard_False, TopTools_FormatVersion_VERSION_1);
//            std::cout << "Write planeTopTransitionEdge brep_result=" << (brep_result==true ? "success" : "fail") << std::endl;
            u += transitionTurns * 2.0 * M_PI;
            v += middleToClosedTransitionHeight;
            std::cout << "after Top Transition u=" << u << " v=" << v << std::endl;
            std::cout << std::endl;

            // Create Top Helix
            std::cout << "Create Top Helix" << std::endl;
            gp_Pnt2d topHelixP1(u, v);
            std::cout << "topHelixP1=" << topHelixP1 << std::endl; // @@@ DUMP @@@
            gp_Pnt2d topHelixP2(u + closedHelixCoils * 2. * M_PI, v + closedHelixCoils * closedHelixPitch);
            std::cout << "topHelixP2=" << topHelixP2 << std::endl; // @@@ DUMP @@@
            Handle(Geom2d_Line) topHelixLine = GCE2d_MakeLine(topHelixP1, topHelixP2);
            std::cout << "topHelixLine=" << topHelixLine << std::endl; // @@@ DUMP @@@
            Handle(Geom2d_TrimmedCurve) topHelixSegment = new Geom2d_TrimmedCurve(topHelixLine, ElCLib::Parameter(topHelixLine->Lin2d(), topHelixP1), ElCLib::Parameter(topHelixLine->Lin2d(), topHelixP2));
            std::cout << "topHelixSegment=" << topHelixSegment << std::endl; // @@@ DUMP @@@
            topHelixEdge = BRepBuilderAPI_MakeEdge(topHelixSegment, helixCylinder).Edge();
//            std::cout << "Write topHelixEdge="; BRepTools::Dump(topHelixEdge, std::cout); std::cout << std::endl; // @@@ DUMP @@@
            BRepLib::BuildCurve3d(topHelixEdge);

//            planeTopHelixEdge = BRepBuilderAPI_MakeEdge(topHelixLine, plane, 0.0, closedHelixCoils * closedHelixHypotenuse).Edge();
//            brep_result = BRepTools::Write(topHelixEdge, "topHelixEdge.brep", Standard_False, Standard_False, TopTools_FormatVersion_VERSION_1);
//            std::cout << "Write topHelixEdge brep_result=" << (brep_result==true ? "success" : "fail") << std::endl;
//            brep_result = BRepTools::Write(planeTopHelixEdge, "planeTopHelixEdge.brep", Standard_False, Standard_False, TopTools_FormatVersion_VERSION_1);
//            std::cout << "Write planeTopHelixEdge brep_result=" << (brep_result==true ? "success" : "fail") << std::endl;
            u += closedHelixCoils * 2.0 * M_PI;
            v += closedHelixCoils * closedHelixPitch;
            std::cout << "after Top Helix u=" << u << " v=" << v << std::endl;
            std::cout << std::endl;
        }

        /* ******************************** */
        /* Create Helix Wire and Helix Pipe */
        /* ******************************** */

        TopoDS_Wire helixWire;
        if (End_Type == End_Types::Closed || End_Type == End_Types::Closed_Ground) {
            std::cout << "Create Helix Wire from Bottom, Bottom Transition, Middle, Top Transition and Top Helix" << std::endl;
            BRepBuilderAPI_MakeWire makeWire = BRepBuilderAPI_MakeWire();
            makeWire.Add(bottomHelixEdge);
            makeWire.Add(bottomTransitionEdge);
            makeWire.Add(middleHelixEdge);
            makeWire.Add(topTransitionEdge);
            makeWire.Add(topHelixEdge);
            helixWire = makeWire.Wire();
        } else {
            std::cout << "Create Helix Wire from Middle Helix" << std::endl;
            helixWire = BRepBuilderAPI_MakeWire(middleHelixEdge).Wire();
        }
        std::cout << "Create Helix Pipe" << std::endl;
        BRepOffsetAPI_MakePipeShell helixPipe(helixWire);
        helixPipe.SetTransitionMode(BRepBuilderAPI_RoundCorner);
        helixPipe.Add(profileWire, Standard_False, Standard_True);
        helixPipe.Build();
        Standard_Boolean flag = helixPipe.MakeSolid();
        std::cout << "MakeSolid flag=" << (flag==true ? "success" : "fail") << std::endl;

        /* ******************** */
        /* Create Ground Cutter */
        /* ******************** */

        TopoDS_Shape helixCutter;
        if (End_Type == End_Types::Open_Ground || End_Type == End_Types::Closed_Ground) {
            // Create Bottom Cutter Box
            std::cout << "Create Bottom Cutter Box" << std::endl;
            BRepPrimAPI_MakeBox bottomHelixBox(OD_Free, OD_Free, Wire_Dia);
            const TopoDS_Shape& bottomHelixCutter = bottomHelixBox.Shape();
            gp_Trsf bottomTrsf;
            bottomTrsf.SetTranslation(gp_Vec(-OD_Free/2.0, -OD_Free/2.0, -Wire_Dia));
            TopoDS_Shape bottomHelixCutterTransformed = BRepBuilderAPI_Transform(bottomHelixCutter, bottomTrsf);
//            std::cout << "Write bottomHelixCutterTransformed="; BRepTools::Dump(bottomHelixCutterTransformed, std::cout); std::cout << std::endl; // @@@ DUMP @@@

            // Create Top Cutter Box
            std::cout << "Create Top Cutter Box" << std::endl;
            BRepPrimAPI_MakeBox topHelixBox(OD_Free, OD_Free, Wire_Dia);
            const TopoDS_Shape& topHelixCutter = bottomHelixBox.Shape();
            gp_Trsf topTrsf;
            topTrsf.SetTranslation(gp_Vec(-OD_Free/2.0, -OD_Free/2.0, L_Free));
            TopoDS_Shape topHelixCutterTransformed = BRepBuilderAPI_Transform(topHelixCutter, topTrsf);
//            std::cout << "Write topHelixCutterTransformed="; BRepTools::Dump(topHelixCutterTransformed, std::cout); std::cout << std::endl; // @@@ DUMP @@@

            // Fuse Bottom and Top Cutter Boxes
            helixCutter = BRepAlgoAPI_Fuse(bottomHelixCutterTransformed, topHelixCutterTransformed);
            std::cout << std::endl;
        }

        /* *********************************************************** */
        /* Form Compression Spring from Helix Pipe minus Helix Cutters */
        /* *********************************************************** */

        if (End_Type == End_Types::Open_Ground || End_Type == End_Types::Closed_Ground) {
            // Cut Bottom and Top Cutter Boxes from Total Helix Pipe
            std::cout << "Create Compression Spring from Helix Pipe minus Cutters" << std::endl;
            compressionSpring = BRepAlgoAPI_Cut(helixPipe, helixCutter);
        } else {
            std::cout << "Create Compression Spring from Helix Pipe directly" << std::endl;
            compressionSpring = helixPipe;
        }

        if (End_Type == End_Types::Open || End_Type == End_Types::Closed) {
            std::cout << "Translate Open/Closed spring by +0.5*Wire_Dia in Z" << std::endl;
            gp_Trsf centerOffset;
            centerOffset.SetTranslation(gp_Vec(0.0, 0.0, 0.5 * Wire_Dia));
            compressionSpring = BRepBuilderAPI_Transform(compressionSpring, centerOffset);
        }

        /* *********************** */
        /* Mesh Compression Spring */
        /* *********************** */

//        std::cout << "Mesh Compression Spring" << std::endl;
//        BRepMesh_IncrementalMesh mesh(compressionSpring, LinearDeflection, Standard_False, 0.5, Standard_False );
//        Standard_Integer status = mesh.GetStatusFlags();
//        std::cout << "Mesh status=" << status << std::endl;

        /* *************************** */
        /* Generate BREP and STL Files */
        /* *************************** */

//        std::cout << "Generate Compression Spring BREP File" << std::endl;
//        brep_result = BRepTools::Write(compressionSpring, "compressionSpring.brep", Standard_False, Standard_False, TopTools_FormatVersion_VERSION_1);
//        std::cout << "compressionSpring brep_result=" << (brep_result==true ? "success" : "fail") << std::endl;
        
//        std::cout << "Generate Compression Spring STL File" << std::endl;
//        StlAPI_Writer writer;
//        Standard_Boolean result;
//        result = writer.Write(compressionSpring, "compressionSpring.stl");
//        std::cout << "Write result=" << (result==true ? "success" : "fail") << std::endl;
        
    } catch(Standard_Failure &err) {
        std::cout << "Standard_Failure &err=" << err << std::endl;
    } catch(int &err) {
        std::cout << "int &err=" << err << std::endl;
    }

    std::cout << "Ending compression_spring_solid" << std::endl;
    return compressionSpring;
}
