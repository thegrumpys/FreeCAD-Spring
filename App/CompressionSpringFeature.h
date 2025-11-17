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

#ifndef SPRING_COMPRESSIONSPRINGFEATURE_H
#define SPRING_COMPRESSIONSPRINGFEATURE_H

#include <SpringGlobal.h>

#include <Mod/Part/App/PrimitiveFeature.h>

namespace Spring
{

class SpringExport CompressionSpring : public Part::Primitive
{
    PROPERTY_HEADER_WITH_OVERRIDE(Spring::CompressionSpring);

public:
    CompressionSpring();

    App::PropertyLength Pitch;
    App::PropertyLength Radius;
    App::PropertyAngle Angle;
    App::PropertyQuantityConstraint SegmentLength;
    App::PropertyEnumeration LocalCoord;
    App::PropertyEnumeration Style;
    App::PropertyIntegerConstraint CoilCount;
    App::PropertyLength Height;
    App::PropertyLength Length;

    App::DocumentObjectExecReturn* execute() override;
    short mustExecute() const override;
    const char* getViewProviderName() const override
    {
        return "PartGui::ViewProviderHelixParametric";
    }

protected:
    void onChanged(const App::Property* prop) override;

private:
    static const char* LocalCSEnums[];
    static const char* StyleEnums[];
};

}  // namespace Spring

#endif  // SPRING_COMPRESSIONSPRINGFEATURE_H
