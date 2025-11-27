#include <BRepAlgoAPI_Fuse.hxx>
#include <BRepAlgoAPI_Cut.hxx>
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
#include <GCE2d_MakeLine.hxx>
#include <GCE2d_MakeArcOfCircle.hxx>
#include <Geom2d_TrimmedCurve.hxx>
#include <Geom2d_Circle.hxx>
#include <Geom2d_Line.hxx>
#include <Geom_CylindricalSurface.hxx>
#include <Geom_Plane.hxx>
#include <StlAPI_Writer.hxx>
#include <TopoDS_Edge.hxx>
#include <TopoDS_Wire.hxx>
#include <TopoDS_Face.hxx>
#include <TopoDS_Shape.hxx>
#include <gp_Circ2d.hxx>
#include <gp_Circ.hxx>
#include <iostream>

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

inline std::ostream& operator<<(std::ostream& os,
                                const Handle(Geom2d_TrimmedCurve)& C)
{
    if (C.IsNull()) {
        os << "Geom2d_TrimmedCurve(NULL)";
        return os;
    }

    // End-point evaluation (guaranteed to exist)
    gp_Pnt2d P1 = C->Value(C->FirstParameter());
    gp_Pnt2d P2 = C->Value(C->LastParameter());

    os << "Geom2d_TrimmedCurve(P1=" << P1
       << ", P2=" << P2;

    // Extract basis curve (you verified this exists)
    Handle(Geom2d_Curve) base = C->BasisCurve();

    // Case 1: Underlying circle
    if (Handle(Geom2d_Circle) circ = Handle(Geom2d_Circle)::DownCast(base)) {
        os << ", Circle=" << circ->Circ2d();
    }
    // Case 2: Underlying line
    else if (Handle(Geom2d_Line) line = Handle(Geom2d_Line)::DownCast(base)) {
        os << ", Line=" << line->Lin2d();   // you have operator<< for gp_Lin2d
    }
    // Case 3: Something else (Bezier, BSpline, ellipse, etc.)
    else {
        os << ", BasisCurve=NonCircleNonLine";
    }

    os << ")";
    return os;
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
        std::cout << std::endl;

        Standard_Real maxTransitionCoils = 0.5;
        std::cout << "maxTransitionCoils=" << maxTransitionCoils << std::endl;
        std::cout << std::endl;

        Standard_Real middleHelixCoils = Coils_A;
        if (Coils_T - Coils_A > 0.0) {
            middleHelixCoils -= 2.0 * maxTransitionCoils;
        }
        Standard_Real middleHelixPitch = (L_Free - Wire_Dia * (Coils_T - Coils_A)) / Coils_A;
        Standard_Real middleHelixHypotenuse = sqrt((2.0 * M_PI * 2.0 * M_PI) + (middleHelixPitch * middleHelixPitch));
        Standard_Real middleHelixHeight = middleHelixCoils * middleHelixPitch;
        std::cout << "middleHelixCoils=" << middleHelixCoils << std::endl;
        std::cout << "middleHelixPitch=" << middleHelixPitch << std::endl;
        std::cout << "middleHelixHypotenuse=" << middleHelixHypotenuse << std::endl;
        std::cout << "middleHelixHeight=" << middleHelixHeight << std::endl;
        std::cout << std::endl;

        Standard_Real middleTransitionCoils = maxTransitionCoils / 2;
        Standard_Real closedTransitionCoils = middleTransitionCoils * middleHelixHypotenuse / closedHelixHypotenuse;
        Standard_Real temp_middleTransitionCoils = middleTransitionCoils * maxTransitionCoils / (middleTransitionCoils + closedTransitionCoils); // scale them to max
        Standard_Real temp_closedTransitionCoils = closedTransitionCoils * maxTransitionCoils / (middleTransitionCoils + closedTransitionCoils);
        middleTransitionCoils = temp_middleTransitionCoils;
        closedTransitionCoils = temp_closedTransitionCoils;

        Standard_Real closedTransitionHypotenuse = closedTransitionCoils * closedHelixHypotenuse;
        Standard_Real closedTransitionHeight = closedTransitionCoils * closedHelixPitch;
        std::cout << "closedTransitionCoils=" << closedTransitionCoils << std::endl;
        std::cout << "closedTransitionHypotenuse=" << closedTransitionHypotenuse << std::endl;
        std::cout << "closedTransitionHeight=" << closedTransitionHeight << std::endl;
        std::cout << std::endl;

        Standard_Real middleTransitionHypotenuse = closedTransitionHypotenuse; // They must match
        Standard_Real middleTransitionHeight = closedTransitionCoils * closedHelixPitch + middleTransitionCoils * middleHelixPitch;
        std::cout << "middleTransitionCoils=" << middleTransitionCoils << std::endl;
        std::cout << "middleTransitionHypotenuse=" << middleTransitionHypotenuse << std::endl;
        std::cout << "middleTransitionHeight=" << middleTransitionHeight << std::endl;
        std::cout << std::endl;

        Standard_Real cutterWidth = OD_Free;
        Standard_Real cutterHeight = L_Free;
        std::cout << "cutterWidth=" << cutterWidth << std::endl;
        std::cout << "cutterHeight=" << cutterHeight << std::endl;
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
            gp_Pnt2d bottomHelixP2(u + 2. * M_PI, v + closedHelixPitch);
            Handle(Geom2d_Line) bottomHelixLine = GCE2d_MakeLine(bottomHelixP1, bottomHelixP2);
            std::cout << "bottomHelixLine=" << bottomHelixLine << std::endl; // @@@ DUMP @@@
            Handle(Geom2d_TrimmedCurve) bottomHelixSegment = new Geom2d_TrimmedCurve(bottomHelixLine, ElCLib::Parameter(bottomHelixLine->Lin2d(), bottomHelixP1), ElCLib::Parameter(bottomHelixLine->Lin2d(), bottomHelixP2));
            std::cout << "bottomHelixSegment=" << bottomHelixSegment << std::endl; // @@@ DUMP @@@
            bottomHelixEdge = BRepBuilderAPI_MakeEdge(bottomHelixSegment, helixCylinder).Edge();
//            std::cout << "Write bottomHelixEdge="; BRepTools::Dump(bottomHelixEdge, std::cout); std::cout << std::endl;std::cout << 
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
            gp_Pnt2d bottomTransitionP1(u, v);
            gp_Pnt2d bottomTransitionP2(u + closedTransitionCoils * 2.0 * M_PI + middleTransitionCoils * 2.0 * M_PI, v + closedTransitionCoils * closedHelixPitch + middleTransitionCoils * middleHelixPitch);
            Handle(Geom2d_TrimmedCurve) bottomTransitionSegment = GCE2d_MakeArcOfCircle(bottomTransitionP1, gp_Vec2d(gp_Dir2d(2. * M_PI, closedHelixPitch)), bottomTransitionP2);
            std::cout << "bottomTransitionSegment=" << bottomTransitionSegment << std::endl; // @@@ DUMP @@@
            bottomTransitionEdge = BRepBuilderAPI_MakeEdge(bottomTransitionSegment, helixCylinder).Edge();
//            std::cout << "Write bottomTransitionEdge="; BRepTools::Dump(bottomTransitionEdge, std::cout); // @@@ DUMP @@@
            BRepLib::BuildCurve3d(bottomTransitionEdge);

//            planeBottomTransitionEdge = BRepBuilderAPI_MakeEdge(bottomTransitionLine, plane).Edge();
//            brep_result = BRepTools::Write(bottomTransitionEdge, "bottomTransitionEdge.brep", Standard_False, Standard_False, TopTools_FormatVersion_VERSION_1);
//            std::cout << "Write bottomTransitionEdge brep_result=" << (brep_result==true ? "success" : "fail") << std::endl;
//            brep_result = BRepTools::Write(planeBottomTransitionEdge, "planeBottomTransitionEdge.brep", Standard_False, Standard_False, TopTools_FormatVersion_VERSION_1);
//            std::cout << "Write planeBottomTransitionEdge brep_result=" << (brep_result==true ? "success" : "fail") << std::endl;
            u += closedTransitionCoils * 2.0 * M_PI + middleTransitionCoils * 2.0 * M_PI;
            v += closedTransitionCoils * closedHelixPitch + middleTransitionCoils * middleHelixPitch;
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
        gp_Pnt2d middleHelixP2(u + 2. * M_PI, v + middleHelixPitch);
        Handle(Geom2d_Line) middleHelixLine = GCE2d_MakeLine(middleHelixP1, middleHelixP2);
        std::cout << "middleHelixLine=" << middleHelixLine << std::endl; // @@@ DUMP @@@
        Handle(Geom2d_TrimmedCurve) middleHelixSegment = new Geom2d_TrimmedCurve(middleHelixLine, ElCLib::Parameter(middleHelixLine->Lin2d(), middleHelixP1), ElCLib::Parameter(middleHelixLine->Lin2d(), middleHelixP2));
        std::cout << "middleHelixSegment=" << middleHelixSegment << std::endl; // @@@ DUMP @@@
        middleHelixEdge = BRepBuilderAPI_MakeEdge(middleHelixSegment, helixCylinder, 0.0, middleHelixCoils * middleHelixHypotenuse).Edge();
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
            gp_Pnt2d topTransitionP1(u + middleTransitionCoils * 2.0 * M_PI + closedTransitionCoils * 2.0 * M_PI, v + middleTransitionCoils * middleHelixPitch + closedTransitionCoils * closedHelixPitch);
            gp_Pnt2d topTransitionP2(u, v);
            Handle(Geom2d_TrimmedCurve) topTransitionSegment = GCE2d_MakeArcOfCircle(topTransitionP1, gp_Vec2d(gp_Dir2d(-2. * M_PI, -closedHelixPitch)), topTransitionP2);
            std::cout << "topTransitionSegment=" << topTransitionSegment << std::endl; // @@@ DUMP @@@
            topTransitionEdge = BRepBuilderAPI_MakeEdge(topTransitionSegment, helixCylinder).Edge();
//            std::cout << "Write topTransitionEdge="; BRepTools::Dump(topTransitionEdge, std::cout); // @@@ DUMP @@@
            BRepLib::BuildCurve3d(topTransitionEdge);
            
//            planeTopTransitionEdge = BRepBuilderAPI_MakeEdge(topTransitionLine, plane).Edge();
//            brep_result = BRepTools::Write(topTransitionEdge, "topTransitionEdge.brep", Standard_False, Standard_False, TopTools_FormatVersion_VERSION_1);
//            std::cout << "Write topTransitionEdge brep_result=" << (brep_result==true ? "success" : "fail") << std::endl;
//            brep_result = BRepTools::Write(planeTopTransitionEdge, "planeTopTransitionEdge.brep", Standard_False, Standard_False, TopTools_FormatVersion_VERSION_1);
//            std::cout << "Write planeTopTransitionEdge brep_result=" << (brep_result==true ? "success" : "fail") << std::endl;
            u += middleTransitionCoils * 2.0 * M_PI + closedTransitionCoils * 2.0 * M_PI;
            v += middleTransitionCoils * middleHelixPitch + closedTransitionCoils * closedHelixPitch;
            std::cout << "after Top Transition u=" << u << " v=" << v << std::endl;
            std::cout << std::endl;

            // Create Top Helix
            std::cout << "Create Top Helix" << std::endl;
            gp_Pnt2d topHelixP1(u, v);
            gp_Pnt2d topHelixP2(u + 2. * M_PI, v + closedHelixPitch);
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
            BRepPrimAPI_MakeBox bottomHelixBox(cutterWidth, cutterWidth, closedHelixPitch);
            const TopoDS_Shape& bottomHelixCutter = bottomHelixBox.Shape();
            gp_Trsf bottomTrsf;
            bottomTrsf.SetTranslation(gp_Vec(-cutterWidth/2.0, -cutterWidth/2.0, -closedHelixPitch));
            TopoDS_Shape bottomHelixCutterTransformed = BRepBuilderAPI_Transform(bottomHelixCutter, bottomTrsf);

            // Create Top Cutter Box
            std::cout << "Create Top Cutter Box" << std::endl;
            BRepPrimAPI_MakeBox topHelixBox(cutterWidth, cutterWidth, closedHelixPitch);
            const TopoDS_Shape& topHelixCutter = bottomHelixBox.Shape();
            gp_Trsf topTrsf;
            topTrsf.SetTranslation(gp_Vec(-cutterWidth/2.0, -cutterWidth/2.0, cutterHeight));
            TopoDS_Shape topHelixCutterTransformed = BRepBuilderAPI_Transform(topHelixCutter, topTrsf);

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
