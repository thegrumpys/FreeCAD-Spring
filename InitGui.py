import os
import FreeCADGui as Gui

# --- Safe way to get this file's directory even if __file__ is undefined ---
try:
    MODULE_PATH = os.path.dirname(__file__)
except NameError:
    import inspect
    MODULE_PATH = os.path.dirname(inspect.getfile(inspect.currentframe()))

Gui.addIconPath(os.path.join(MODULE_PATH, "Resources", "icons"))

class SpringWorkbench(Gui.Workbench):
    MenuText = "Spring"
    ToolTip = "Design compression, extension, and torsion springs"
    Icon = "workbench.svg"

    def Initialize(self):
        # Import command modules *here*, so they're always defined when activating
        from Commands import (
            CreateCompressionSpring,
            CreateExtensionSpring,
            CreateTorsionSpring,
            DisplaySpringInfo,
        )
        from Preferences.SpringPreferencePage import SpringPreferencePage

        # Register commands
        CreateCompressionSpring.register()
        CreateExtensionSpring.register()
        CreateTorsionSpring.register()
        DisplaySpringInfo.register()

        # Build toolbar/menu
        self.list = [
            "Spring_CreateCompressionSpring",
            "Spring_CreateExtensionSpring",
            "Spring_CreateTorsionSpring",
            "Spring_DisplaySpringInfo",
        ]
        self.appendToolbar("Spring", self.list)
        self.appendMenu("Spring", self.list)

    def GetClassName(self):
        return "Gui::PythonWorkbench"

Gui.addWorkbench(SpringWorkbench())
