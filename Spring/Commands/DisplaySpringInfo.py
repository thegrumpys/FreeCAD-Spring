import FreeCADGui as Gui
from Spring.Dialogs.SpringInfoDialog import SpringInfoDialog

class DisplaySpringInfo:
    def GetResources(self):
        return {
            'Pixmap': 'SpringInfo.svg',
            'MenuText': 'Spring Info',
            'ToolTip': 'Show analytic spring information for the selected object'
        }

    def Activated(self):
        SpringInfoDialog.show_for_selected()

    def IsActive(self):
        return bool(Gui.Selection.getSelection())

def register():
    """Registers this command with FreeCAD"""
    Gui.addCommand("Spring_DisplaySpringInfo", DisplaySpringInfo())
