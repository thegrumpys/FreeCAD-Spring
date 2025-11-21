# SPDX-License-Identifier: LGPL-2.1-or-later

# FreeCAD tools of the Spring workbench
# (c) 2001 Juergen Riegel
# License LGPL

import FreeCAD, FreeCADGui

try:
    import springocct
except ImportError as exc:
    springocct = None
    FreeCAD.Console.PrintError(f"springocct unavailable: {exc}\n")


class CmdHelloWorld:
    def Activated(self):
        FreeCAD.Console.PrintMessage("Hello, World!\n")
        self._exercise_springocct()

    def IsActive(self):
        return True

    def _exercise_springocct(self):
        if springocct is None:
            FreeCAD.Console.PrintError("springocct not available; skipping springocct checks.\n")
            return

        first = springocct.Pnt2d(1.0, 2.0)
        second = first.translated(3.0, 4.0)
        dist_method = first.distance(second)
        dist_free = springocct.distance(first, second)
        FreeCAD.Console.PrintMessage(
            "springocct Pnt2d distances: method = "
            f"{dist_method}, free function = {dist_free}\n"
        )

        dir2d = springocct.Dir2d(1.0, 0.0)
        vec2d = springocct.Vec2d(0.5, -0.25)
        lin2d = springocct.Lin2d(first, dir2d)
        FreeCAD.Console.PrintMessage(
            f"springocct gp_Dir2d: {dir2d}, gp_Vec2d: {vec2d}, gp_Lin2d: {lin2d}\n"
        )

        origin = springocct.Pnt(0.0, 0.0, 0.0)
        point = springocct.Pnt(1.0, 2.0, 3.0)
        direction = springocct.Dir(0.0, 0.0, 1.0)
        x_direction = springocct.Dir(1.0, 0.0, 0.0)
        vector = springocct.Vec(origin, point)
        axis2 = springocct.Ax2(origin, direction, x_direction)
        axis3 = springocct.Ax3(origin, direction, x_direction)
        circle = springocct.Circ(axis2, 2.5)

        FreeCAD.Console.PrintMessage(
            "springocct 3D types: "
            f"gp_Pnt: {point}, gp_Dir: {direction}, gp_Vec: {vector}, gp_Ax2: {axis2}, "
            f"gp_Ax3: {axis3}, gp_Circ: {circle}\n"
        )

        value = springocct.compression_spring_solid(
            outer_diameter_in=1.1,
            wire_diameter_in=0.1055,
            free_length_in=3.25,
            total_coils=16.0,
            end_type=3, # Closed
            level_of_detail=20,
        )
        FreeCAD.Console.PrintMessage(
            "springocct compression_spring_solid: "
            f"return: {value}\n"
        )

    def GetResources(self):
        return {
            "Pixmap": "freecad",
            "MenuText": "Hello World",
            "ToolTip": "Print Hello World",
        }


FreeCADGui.addCommand("Spring_HelloWorld", CmdHelloWorld())
