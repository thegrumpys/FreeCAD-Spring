// SPDX-License-Identifier: BSD-3-Clause
#pragma once

#include <gp_Pnt2d.hxx>
#include <TopoDS_Shape.hxx>

// Compute the distance between two 2D points.
double Distance2d(const gp_Pnt2d& first, const gp_Pnt2d& second);

int compression_spring_solid();
