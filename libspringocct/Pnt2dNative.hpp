// SPDX-License-Identifier: BSD-3-Clause
#pragma once

#include <gp_Pnt2d.hxx>
#include <TopoDS_Shape.hxx>

// Compute the distance between two 2D points.
double Distance2d(const gp_Pnt2d& first, const gp_Pnt2d& second);

TopoDS_Shape compression_spring_solid(
    double outer_diameter_in,
    double wire_diameter_in,
    double free_length_in,
    double total_coils,
    int end_type,
    double level_of_detail
);
