try:
    import FreeCADGui
except ImportError:
    FreeCADGui = None


class ViewProviderSpring:
    def __init__(self, vobj):
        if FreeCADGui is None or vobj is None:
            return
        self.Object = vobj.Object
        vobj.Proxy = self

    def attach(self, vobj):
        self.Object = vobj.Object

    def updateData(self, fp, prop):
        pass

    def getDisplayModes(self, obj):
        return ["Shaded"]

    def getDefaultDisplayMode(self):
        return "Shaded"

    def getDisplayValue(self, prop):
        """Return a formatted string for display in the Property Editor."""
#        FreeCAD.Console.PrintMessage(f"[ViewProviderSpring.getDisplayValue] prop={prop}\n")
        if prop == "TorsionModulus" or prop == "ElasticModulus":
            val = getattr(self.Object, prop)
            return f"{val:.6e}"  # always scientific notation
        # Fallback: let FreeCAD handle all other properties normally
        return None

    def setDisplayMode(self, mode):
        return mode

    def setEdit(self, vobj, mode=0):
        return False

    def unsetEdit(self, vobj, mode=0):
        return False

    def doubleClicked(self, vobj):
        if FreeCADGui is None:
            return False
        try:
            from Gui import SpringAlertsDockWidget
        except Exception:
            return False
        SpringAlertsDockWidget.show_dock_for_object(vobj.Object)
        return True

    def onChanged(self, vobj, prop):
        pass

    def __getstate__(self):
        return None

    def __setstate__(self, state):
        return None
