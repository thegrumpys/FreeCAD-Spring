# SPDX-License-Identifier: LGPL-2.1-or-later

# FreeCAD tools of the Spring workbench
# (c) 2001 Juergen Riegel
# License LGPL

import FreeCAD, FreeCADGui

try:
    import springarea
except ImportError as exc:
    springarea = None
    FreeCAD.Console.PrintError(f"springarea unavailable: {exc}\n")

try:
    import springocct
except ImportError as exc:
    springocct = None
    FreeCAD.Console.PrintError(f"springocct unavailable: {exc}\n")


class CmdHelloWorld:
    def Activated(self):
        FreeCAD.Console.PrintMessage("Hello, World!\n")
        self._exercise_springarea()
        self._exercise_springocct()

    def IsActive(self):
        return True

    def _exercise_springarea(self):
        if springarea is None:
            FreeCAD.Console.PrintError("springarea not available; skipping springarea checks.\n")
            return

        point = springarea.Point(3.0, 4.0)
        length = point.length()
        FreeCAD.Console.PrintMessage(f"springarea Point length: {length}\n")

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

    def GetResources(self):
        return {
            "Pixmap": "freecad",
            "MenuText": "Hello World",
            "ToolTip": "Print Hello World",
        }


FreeCADGui.addCommand("Spring_HelloWorld", CmdHelloWorld())
