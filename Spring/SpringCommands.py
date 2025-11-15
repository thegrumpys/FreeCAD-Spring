import FreeCAD as App
import FreeCADGui as Gui

from .SpringTools import (
    create_compression_spring,
    create_extension_spring,
    create_torsion_spring,
)


class _CreateSpringCommand:
    def __init__(self, label, icon, creator, description):
        self.label = label
        self.icon = icon
        self.creator = creator
        self.description = description

    def GetResources(self):
        return {
            "MenuText": self.label,
            "ToolTip": self.description,
            "Pixmap": self.icon,
        }

    def Activated(self):
        document = App.ActiveDocument
        if document is None:
            document = App.newDocument()
        obj = self.creator(document)
        if Gui.Up and obj is not None:
            Gui.ActiveDocument.setEdit(obj.Name)

    def IsActive(self):
        return True


_REGISTERED = False


def setup_commands():
    global _REGISTERED
    if _REGISTERED:
        return

    Gui.addCommand(
        "Spring_CreateCompressionSpring",
        _CreateSpringCommand(
            "Compression Spring",
            ":/Spring/CompressionSpring.svg",
            create_compression_spring,
            "Create a compression spring feature",
        ),
    )

    Gui.addCommand(
        "Spring_CreateExtensionSpring",
        _CreateSpringCommand(
            "Extension Spring",
            ":/Spring/ExtensionSpring.svg",
            create_extension_spring,
            "Create an extension spring with hooks",
        ),
    )

    Gui.addCommand(
        "Spring_CreateTorsionSpring",
        _CreateSpringCommand(
            "Torsion Spring",
            ":/Spring/TorsionSpring.svg",
            create_torsion_spring,
            "Create a torsion spring with arms",
        ),
    )

    _REGISTERED = True

