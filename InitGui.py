# SPDX-License-Identifier: LGPL-2.1-or-later

# Sprung gui init module
# (c) 2001 Juergen Riegel
# License LGPL


class SprungWorkbench(Workbench):
    "Sprung workbench object"

    Icon = FreeCAD.getResourceDir() + "Mod/Sprung/Resources/icons/SprungWorkbench.svg"
    MenuText = "Sprung"
    ToolTip = "Sprung workbench"

    def Initialize(self):
        # load the module
        import SprungGui

        self.appendToolbar("Sprung", ["Sprung_HelloWorld"])
        self.appendMenu("Sprung", ["Sprung_HelloWorld"])

    def GetClassName(self):
        return "Gui::PythonWorkbench"


Gui.addWorkbench(SprungWorkbench())
