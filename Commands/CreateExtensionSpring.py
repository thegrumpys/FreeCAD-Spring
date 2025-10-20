import FreeCADGui as Gui
from Features.Extension import Spring as ExtensionSpring

class CreateExtensionSpring:
    """Command to create a parametric extension spring"""

    def GetResources(self):
        """Defines icon, tooltip, and menu text"""
        return {
            "Pixmap": "extension.svg",  # must exist in Resources/icons/
            "MenuText": "Extension Spring",
            "ToolTip": "Create a parametric extension spring",
        }

    def Activated(self):
        """What happens when user clicks the command"""
        ExtensionSpring.make()

    def IsActive(self):
        """Enable only when a document is active"""
        return Gui.ActiveDocument is not None

def register():
    """Registers this command with FreeCAD"""
    Gui.addCommand("Spring_CreateExtensionSpring", CreateExtensionSpring())
