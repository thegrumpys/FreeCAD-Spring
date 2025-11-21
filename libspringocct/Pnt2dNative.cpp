// SPDX-License-Identifier: BSD-3-Clause

#include "Pnt2dNative.hpp"

#include <gp_Pnt2d.hxx>

double Distance2d(const gp_Pnt2d& first, const gp_Pnt2d& second)
{
    return first.Distance(second);
}
