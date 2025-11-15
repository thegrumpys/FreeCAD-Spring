import FreeCADGui as Gui

from . import SpringCommands


class SpringWorkbench(Gui.Workbench):
    """Workbench definition for the Spring tools."""

    MenuText = "Spring"
    ToolTip = "Tools for creating compression, extension, and torsion springs"
    Icon = ":/Spring/SpringWorkbench.svg"

    def Initialize(self):
        SpringCommands.setup_commands()
        self.commands = [
            "Spring_CreateCompressionSpring",
            "Spring_CreateExtensionSpring",
            "Spring_CreateTorsionSpring",
        ]
        self.appendToolbar("Spring", self.commands)
        self.appendMenu("Spring", self.commands)

    def GetClassName(self):
        return "Gui::PythonWorkbench"

    def Activated(self):
        pass

    def Deactivated(self):
        pass

