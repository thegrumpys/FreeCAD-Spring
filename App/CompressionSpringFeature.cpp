// SPDX-License-Identifier: LGPL-2.1-or-later

/***************************************************************************
 *   Copyright (c) 2024 OpenAI                                            *
 *                                                                         *
 *   This file is part of the FreeCAD CAx development system.              *
 *                                                                         *
 *   This library is free software; you can redistribute it and/or         *
 *   modify it under the terms of the GNU Library General Public           *
 *   License as published by the Free Software Foundation; either          *
 *   version 2 of the License, or (at your option) any later version.      *
 *                                                                         *
 *   This library  is distributed in the hope that it will be useful,      *
 *   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
 *   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
 *   GNU Library General Public License for more details.                  *
 *                                                                         *
 *   You should have received a copy of the GNU Library General Public     *
 *   License along with this library; see the file COPYING.LIB. If not,    *
 *   write to the Free Software Foundation, Inc., 59 Temple Place,         *
 *   Suite 330, Boston, MA  02111-1307, USA                                *
 *                                                                         *
 ***************************************************************************/

#include "CompressionSpringFeature.h"

#include <climits>
#include <limits>

#include <BRepGProp.hxx>
#include <GProp_GProps.hxx>
#include <Precision.hxx>
#include <Standard_Failure.hxx>

#include <Base/Console.h>
#include <Base/Tools.h>

#include <Mod/Part/App/TopoShape.h>

namespace Spring
{
namespace
{
const App::PropertyQuantityConstraint::Constraints quantityRange
    = {0.0, std::numeric_limits<float>::max(), 0.1f};
const App::PropertyQuantityConstraint::Constraints apexRange = {-89.9, 89.9, 0.1};
const App::PropertyIntegerConstraint::Constraints coilRange = {1, INT_MAX, 1};
}  // namespace

PROPERTY_SOURCE(Spring::CompressionSpring, Part::Primitive)

const char* CompressionSpring::LocalCSEnums[] = {"Right-handed", "Left-handed", nullptr};
const char* CompressionSpring::StyleEnums[] = {"Old style", "New style", nullptr};

CompressionSpring::CompressionSpring()
{
    ADD_PROPERTY_TYPE(Pitch, (1.0), "Helix", App::Prop_None, "The pitch of the helix");
    Pitch.setConstraints(&quantityRange);
    ADD_PROPERTY_TYPE(Height, (2.0), "Helix", App::Prop_None, "The height of the helix");
    Height.setConstraints(&quantityRange);
    ADD_PROPERTY_TYPE(Radius, (1.0), "Helix", App::Prop_None, "The radius of the helix");
    Radius.setConstraints(&quantityRange);
    ADD_PROPERTY_TYPE(
        SegmentLength,
        (0.0),
        "Helix",
        App::Prop_None,
        "The number of turns per helix subdivision"
    );
    SegmentLength.setConstraints(&quantityRange);
    ADD_PROPERTY_TYPE(
        Angle,
        (0.0),
        "Helix",
        App::Prop_None,
        "If angle is != 0 a conical otherwise a cylindircal surface is used"
    );
    Angle.setConstraints(&apexRange);
    ADD_PROPERTY_TYPE(
        LocalCoord,
        (long(0)),
        "Coordinate System",
        App::Prop_None,
        "Orientation of the local coordinate system of the helix"
    );
    LocalCoord.setEnums(LocalCSEnums);
    ADD_PROPERTY_TYPE(
        Style,
        (long(0)),
        "Helix style",
        App::Prop_Hidden,
        "Old style creates incorrect and new style create correct helices"
    );
    Style.setEnums(StyleEnums);
    ADD_PROPERTY_TYPE(Length, (1.0), "Helix", App::Prop_None, "The length of the helix");
    Length.setReadOnly(true);
}

void CompressionSpring::onChanged(const App::Property* prop)
{
    if (!isRestoring()) {
        if (prop == &Pitch || prop == &Height || prop == &Radius || prop == &Angle
            || prop == &LocalCoord || prop == &Style || prop == &SegmentLength) {
            try {
                App::DocumentObjectExecReturn* ret = recompute();
                delete ret;
            }
            catch (...) {
            }
        }
    }
    Part::Primitive::onChanged(prop);
}

short CompressionSpring::mustExecute() const
{
    if (Pitch.isTouched()) {
        return 1;
    }
    if (Height.isTouched()) {
        return 1;
    }
    if (Radius.isTouched()) {
        return 1;
    }
    if (Angle.isTouched()) {
        return 1;
    }
    if (LocalCoord.isTouched()) {
        return 1;
    }
    if (Style.isTouched()) {
        return 1;
    }
    return Primitive::mustExecute();
}

App::DocumentObjectExecReturn* CompressionSpring::execute()
{
    try {
        Standard_Real myPitch = Pitch.getValue();
        Standard_Real myHeight = Height.getValue();
        Standard_Real myRadius = Radius.getValue();
        Standard_Real myAngle = Angle.getValue();
        Standard_Boolean myLocalCS = LocalCoord.getValue() ? Standard_True : Standard_False;
        Standard_Real mySegLen = SegmentLength.getValue();
        if (myPitch < Precision::Confusion()) {
            Standard_Failure::Raise("Pitch too small");
        }
        Standard_Real nbTurns = myHeight / myPitch;
        if (nbTurns > 1e4) {
            Standard_Failure::Raise("Number of turns too high (> 1e4)");
        }
        Standard_Real myRadiusTop = myRadius + myHeight * tan(Base::toRadians<double>(myAngle));

        this->Shape.setValue(
            Part::TopoShape().makeSpiralHelix(myRadius, myRadiusTop, myHeight, nbTurns, mySegLen, myLocalCS)
        );
        // props.Mass() may seem a strange way to get the Length, but
        // https://dev.opencascade.org/doc/refman/html/class_b_rep_g_prop.html#ab1d4bacc290bfaa8df13dd99ae7b8e70
        // confirms this.
        GProp_GProps props;
        BRepGProp::LinearProperties(Shape.getShape().getShape(), props);
        Length.setValue(props.Mass());
    }
    catch (Standard_Failure& e) {

        return new App::DocumentObjectExecReturn(e.GetMessageString());
    }

    return Primitive::execute();
}

}  // namespace Spring
