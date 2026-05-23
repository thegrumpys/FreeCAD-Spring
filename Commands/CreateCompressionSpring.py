import FreeCADGui as Gui
from Features.Compression import Spring as CompressionSpring

class CreateCompressionSpring:
    """Command to create a parametric compression spring"""

    def GetResources(self):
        """Defines icon, tooltip, and menu text"""
        return {
            "Pixmap": "compression.svg",  # must exist in Resources/icons/
            "MenuText": "Compression Spring",
            "ToolTip": "Create a parametric compression spring",
        }

    def Activated(self):
        """What happens when user clicks the command"""
        CompressionSpring.make()

        # Fit view to show the newly created spring
        if Gui.ActiveDocument and Gui.ActiveDocument.ActiveView:
            Gui.ActiveDocument.ActiveView.fitAll()

    def IsActive(self):
        """Enable only when a document is active"""
        return Gui.ActiveDocument is not None

def register():
    """Registers this command with FreeCAD"""
    Gui.addCommand("Spring_CreateCompressionSpring", CreateCompressionSpring())
