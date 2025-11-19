# SPDX-License-Identifier: LGPL-2.1-or-later

# FreeCAD tools of the Spring workbench
# (c) 2001 Juergen Riegel
# License LGPL

import FreeCAD, FreeCADGui
import springarea


class CmdHelloWorld:
    def Activated(self):
        FreeCAD.Console.PrintMessage("Hello, World!\n")
        p = area.Point(3.0, 4.0)
        print(p.length())   # prints 5.0

    def IsActive(self):
        return True

    def GetResources(self):
        return {
            "Pixmap": "freecad",
            "MenuText": "Hello World",
            "ToolTip": "Print Hello World",
        }


FreeCADGui.addCommand("Spring_HelloWorld", CmdHelloWorld())
