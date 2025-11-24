// SPDX-License-Identifier: BSD-3-Clause
#pragma once

#include <TopoDS_Shape.hxx>

TopoDS_Shape compression_spring_solid(
    double outer_diameter,
    double wire_diameter,
    double free_length,
    double total_coils,
    double inactive_coils,
    int end_type
);
