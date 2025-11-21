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

class MakeCompressionSpring:
    def Activated(self):
        if springocct is None:
            FreeCAD.Console.PrintError("springocct not available; skipping springocct checks.\n")
            return

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

    def IsActive(self):
        return True

    def GetResources(self):
        return {
            "Pixmap": "freecad",
            "MenuText": "Make Compression Spring",
            "ToolTip": "Make Compression Spring",
        }


FreeCADGui.addCommand("Spring_MakeCompressionSpring", MakeCompressionSpring())
