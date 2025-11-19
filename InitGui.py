# SPDX-License-Identifier: LGPL-2.1-or-later

# Spring gui init module
# (c) 2001 Juergen Riegel
# License LGPL


class SpringWorkbench(Workbench):
    "Spring workbench object"

    Icon = FreeCAD.getResourceDir() + "Mod/Spring/Resources/icons/SpringWorkbench.svg"
    MenuText = "Spring"
    ToolTip = "Spring workbench"

    def Initialize(self):
        # load the module
        import SpringGui

        self.appendToolbar("Spring", ["Spring_HelloWorld"])
        self.appendMenu("Spring", ["Spring_HelloWorld"])

    def GetClassName(self):
        return "Gui::PythonWorkbench"


Gui.addWorkbench(SpringWorkbench())
