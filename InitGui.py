# SPDX-License-Identifier: LGPL-2.1-or-later

# Spring gui init module
# (c) 2001 Juergen Riegel LGPL


class SpringWorkbench(Workbench):
    "Spring workbench object"

    MenuText = "Spring"
    ToolTip = "Spring workbench"

    def Initialize(self):
        # load the module
        import SpringGui

    def GetClassName(self):
        return "SpringGui::Workbench"


Gui.addWorkbench(SpringWorkbench())
