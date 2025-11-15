#include "TorsionSpringFeature.h"

#include <BRep_Builder.hxx>
#include <BRepPrimAPI_MakeCylinder.hxx>
#include <Precision.hxx>
#include <TopoDS_Compound.hxx>
#include <TopoDS_Shape.hxx>
#include <gp_Ax2.hxx>
#include <gp_Dir.hxx>
#include <gp_Pnt.hxx>

#include <cmath>

using namespace Spring;

PROPERTY_SOURCE(Spring::TorsionSpringFeature, Spring::SpringFeature)

TorsionSpringFeature::TorsionSpringFeature()
{
    ArmLength.setValue(10.0);
    ArmAngle.setValue(90.0);
}

void TorsionSpringFeature::registerClass()
{
    if (!TorsionSpringFeature::getClassTypeId().isDerivedFrom(SpringFeature::getClassTypeId())) {
        TorsionSpringFeature::getClassTypeId();
    }
}

SpringKind TorsionSpringFeature::kind() const
{
    return SpringKind::Torsion;
}

TopoDS_Shape TorsionSpringFeature::augmentShape(const TopoDS_Shape& coil) const
{
    const double armLen = ArmLength.getValue();

    if (armLen <= Precision::Confusion()) {
        return coil;
    }

    const double wireRad = wireRadius();
    const double baseRadius = coilRadius() + wireRad;
    const double height = coilHeight();
    const double angleRad = ArmAngle.getValue() * (M_PI / 180.0);

    BRep_Builder builder;
    TopoDS_Compound compound;
    builder.MakeCompound(compound);
    builder.Add(compound, coil);

    gp_Ax2 firstAxis(gp_Pnt(baseRadius, 0.0, 0.0), gp_Dir(1.0, 0.0, 0.0));
    builder.Add(compound, BRepPrimAPI_MakeCylinder(firstAxis, wireRad, armLen).Shape());

    gp_Pnt secondOrigin(baseRadius * std::cos(angleRad), baseRadius * std::sin(angleRad), height);
    gp_Dir secondDir(std::cos(angleRad), std::sin(angleRad), 0.0);
    gp_Ax2 secondAxis(secondOrigin, secondDir);
    builder.Add(compound, BRepPrimAPI_MakeCylinder(secondAxis, wireRad, armLen).Shape());

    return compound;
}

