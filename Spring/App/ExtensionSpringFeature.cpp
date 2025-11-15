#include "ExtensionSpringFeature.h"

#include <BRep_Builder.hxx>
#include <BRepPrimAPI_MakeCylinder.hxx>
#include <Precision.hxx>
#include <TopoDS_Compound.hxx>
#include <TopoDS_Shape.hxx>
#include <gp_Ax2.hxx>
#include <gp_Dir.hxx>
#include <gp_Pnt.hxx>

using namespace Spring;

PROPERTY_SOURCE(Spring::ExtensionSpringFeature, Spring::SpringFeature)

ExtensionSpringFeature::ExtensionSpringFeature()
{
    StartLength.setValue(5.0);
    EndLength.setValue(5.0);
}

void ExtensionSpringFeature::registerClass()
{
    if (!ExtensionSpringFeature::getClassTypeId().isDerivedFrom(SpringFeature::getClassTypeId())) {
        ExtensionSpringFeature::getClassTypeId();
    }
}

SpringKind ExtensionSpringFeature::kind() const
{
    return SpringKind::Extension;
}

TopoDS_Shape ExtensionSpringFeature::augmentShape(const TopoDS_Shape& coil) const
{
    const double startLen = StartLength.getValue();
    const double endLen = EndLength.getValue();
    const double wireRad = wireRadius();

    if (startLen <= Precision::Confusion() && endLen <= Precision::Confusion()) {
        return coil;
    }

    BRep_Builder builder;
    TopoDS_Compound compound;
    builder.MakeCompound(compound);
    builder.Add(compound, coil);

    if (startLen > Precision::Confusion()) {
        gp_Ax2 startAxis(gp_Pnt(0.0, 0.0, -startLen), gp_Dir(0.0, 0.0, 1.0));
        builder.Add(compound, BRepPrimAPI_MakeCylinder(startAxis, wireRad, startLen).Shape());
    }

    if (endLen > Precision::Confusion()) {
        gp_Ax2 endAxis(gp_Pnt(0.0, 0.0, coilHeight()), gp_Dir(0.0, 0.0, 1.0));
        builder.Add(compound, BRepPrimAPI_MakeCylinder(endAxis, wireRad, endLen).Shape());
    }

    return compound;
}

