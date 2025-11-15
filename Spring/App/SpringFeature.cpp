#include "SpringFeature.h"

#include <Base/Console.h>
#include <Base/Exception.h>

#include <BRepBuilderAPI_MakeEdge.hxx>
#include <BRepBuilderAPI_MakeWire.hxx>
#include <BRepOffsetAPI_MakePipe.hxx>
#include <GC_MakeCircle.hxx>
#include <Geom_Circle.hxx>
#include <Precision.hxx>
#include <Standard_Failure.hxx>
#include <TopoDS.hxx>
#include <TopoDS_Edge.hxx>
#include <TopoDS_Shape.hxx>
#include <TopoDS_Wire.hxx>
#include <gp_Ax2.hxx>
#include <gp_Circ.hxx>
#include <gp_Dir.hxx>
#include <gp_Pnt.hxx>

#include <Mod/Part/App/TopoShape.h>

using namespace Spring;

PROPERTY_SOURCE(Spring::SpringFeature, Part::Feature)

SpringFeature::SpringFeature()
{
    ADD_PROPERTY_TYPE(CoilDiameter, (10.0), "Spring", App::Prop_None, "Overall coil diameter");
    ADD_PROPERTY_TYPE(WireDiameter, (1.0), "Spring", App::Prop_None, "Wire diameter");
    ADD_PROPERTY_TYPE(Pitch, (2.0), "Spring", App::Prop_None, "Pitch between coils");
    ADD_PROPERTY_TYPE(ActiveCoils, (10.0), "Spring", App::Prop_None, "Number of active coils");
    ADD_PROPERTY_TYPE(LeftHanded, (false), "Spring", App::Prop_None, "Left handed winding");
    ADD_PROPERTY_TYPE(StartLength, (0.0), "Spring", App::Prop_None, "Additional length at start");
    ADD_PROPERTY_TYPE(EndLength, (0.0), "Spring", App::Prop_None, "Additional length at end");
    ADD_PROPERTY_TYPE(ArmLength, (5.0), "Spring", App::Prop_None, "Length of torsion arms");
    ADD_PROPERTY_TYPE(ArmAngle, (90.0), "Spring", App::Prop_None, "Relative angle of torsion arms");

    CoilDiameter.setConstraints(0.1, 10000.0);
    WireDiameter.setConstraints(0.01, 1000.0);
    Pitch.setConstraints(0.1, 1000.0);
    ActiveCoils.setConstraints(0.25, 1000.0);
    StartLength.setConstraints(0.0, 1000.0);
    EndLength.setConstraints(0.0, 1000.0);
    ArmLength.setConstraints(0.0, 1000.0);
    ArmAngle.setConstraints(-360.0, 360.0);
}

void SpringFeature::registerClass()
{
    if (!SpringFeature::getClassTypeId().isDerivedFrom(Part::Feature::getClassTypeId())) {
        SpringFeature::getClassTypeId();
    }
}

void SpringFeature::onChanged(const App::Property* prop)
{
    Part::Feature::onChanged(prop);

    if (prop == &CoilDiameter || prop == &WireDiameter || prop == &Pitch ||
        prop == &ActiveCoils || prop == &StartLength || prop == &EndLength ||
        prop == &ArmLength || prop == &ArmAngle) {
        recomputeFeature();
    }
}

int SpringFeature::execute()
{
    try {
        TopoDS_Shape coil = buildCoil();
        TopoDS_Shape finalShape = augmentShape(coil);
        Shape.setValue(finalShape);
    } catch (const Standard_Failure& e) {
        Base::Console().Error("Failed to build spring geometry: %s\n", e.GetMessageString());
        Shape.setValue(TopoDS_Shape());
        return 1;
    } catch (const Base::Exception& e) {
        Base::Console().Error("Failed to build spring geometry: %s\n", e.what());
        Shape.setValue(TopoDS_Shape());
        return 1;
    }

    return 0;
}

TopoDS_Shape SpringFeature::augmentShape(const TopoDS_Shape& coil) const
{
    return coil;
}

double SpringFeature::coilRadius() const
{
    const double radius = std::max(Precision::Confusion(), 0.5 * CoilDiameter.getValue());
    return std::max(radius - wireRadius(), Precision::Confusion());
}

double SpringFeature::wireRadius() const
{
    return std::max(Precision::Confusion(), 0.5 * WireDiameter.getValue());
}

double SpringFeature::coilHeight() const
{
    return std::max(Precision::Confusion(), ActiveCoils.getValue() * coilPitch());
}

double SpringFeature::coilPitch() const
{
    return std::max(Precision::Confusion(), Pitch.getValue());
}

bool SpringFeature::isLeftHanded() const
{
    return LeftHanded.getValue();
}

TopoDS_Shape SpringFeature::buildCoil() const
{
    const double radius = coilRadius();
    const double pitch = coilPitch();
    const double height = coilHeight();
    const bool leftHanded = isLeftHanded();
    const double wireRad = wireRadius();

    Part::TopoShape helix = Part::TopoShape::makeHelix(pitch, height, radius, 0.0, leftHanded);
    TopoDS_Wire path = TopoDS::Wire(helix.getShape());

    gp_Ax2 profileAxis(gp_Pnt(radius + wireRad, 0.0, 0.0), gp_Dir(0, 1, 0));
    gp_Circ circle(profileAxis, wireRad);
    TopoDS_Edge profileEdge = BRepBuilderAPI_MakeEdge(circle);
    TopoDS_Wire profileWire = BRepBuilderAPI_MakeWire(profileEdge);

    BRepOffsetAPI_MakePipe pipe(path, profileWire);
    pipe.Build();

    if (!pipe.IsDone()) {
        throw Base::RuntimeError("Failed to sweep spring profile");
    }

    return pipe.Shape();
}

