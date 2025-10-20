import FreeCADGui as Gui
from Features.Torsion import Spring as TorsionSpring

class CreateTorsionSpring:
    """Command to create a parametric torsion spring"""

    def GetResources(self):
        """Defines icon, tooltip, and menu text"""
        return {
            "Pixmap": "torsion.svg",  # must exist in Resources/icons/
            "MenuText": "Torsion Spring",
            "ToolTip": "Create a parametric torsion spring",
        }


    def Activated(self):
        """What happens when user clicks the command"""
        TorsionSpring.make()

    def IsActive(self):
        """Enable only when a document is active"""
        return Gui.ActiveDocument is not None

def register():
    """Registers this command with FreeCAD"""
    Gui.addCommand("Spring_CreateTorsionSpring", CreateTorsionSpring())
