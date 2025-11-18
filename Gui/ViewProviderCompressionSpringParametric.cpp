// SPDX-License-Identifier: LGPL-2.1-or-later

/***************************************************************************
 *   Copyright (c) 2004 Jürgen Riegel <juergen.riegel@web.de>              *
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


#include <QMenu>

#include "ViewProviderCompressionSpringParametric.h"

using namespace SpringGui;

PROPERTY_SOURCE(SpringGui::ViewProviderCompressionSpringParametric, PartGui::ViewProviderPrimitive)

ViewProviderCompressionSpringParametric::ViewProviderCompressionSpringParametric()
{
    sPixmap = "Spring_CompressionSpring_Parametric";
    extension.initExtension(this);
}

ViewProviderCompressionSpringParametric::~ViewProviderCompressionSpringParametric() = default;

std::vector<std::string> ViewProviderCompressionSpringParametric::getDisplayModes() const
{
    std::vector<std::string> StrList;
    StrList.emplace_back("Wireframe");
    StrList.emplace_back("Points");

    return StrList;
}

void ViewProviderCompressionSpringParametric::setupContextMenu(QMenu* menu, QObject* receiver, const char* member)
{
    PartGui::ViewProviderPrimitive::setupContextMenu(menu, receiver, member);
}
