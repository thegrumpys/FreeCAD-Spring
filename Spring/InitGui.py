class TestWorkbench:
    """Minimal FreeCAD-style workbench placeholder."""

    def Activated(self):  # noqa: N802 FreeCAD naming convention
        from . import Init

        print("TestWorkbench activated. Example point description:")
        print(Init.describe_point(1.0, 2.0))

    def GetClassName(self):  # noqa: N802
        return "Gui::PythonWorkbench"


FreeCADGui = None  # Only to satisfy potential imports during documentation builds.
