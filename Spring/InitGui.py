import FreeCAD as App
import FreeCADGui as Gui

from .Workbench import SpringWorkbench

App.Console.PrintLog("Loading Spring workbench (Gui)\n")

Gui.addWorkbench(SpringWorkbench())

