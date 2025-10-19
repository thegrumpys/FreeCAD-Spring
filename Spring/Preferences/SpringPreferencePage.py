import FreeCAD, FreeCADGui
from PySide2 import QtWidgets

class SpringPreferencePage:
    PARAM_PATH = "User parameter:BaseApp/Preferences/Mod/Spring"

    INTEGER_PREFERENCES = (
        ("ioopt", "IO optimization mode", 3),
        ("maxit", "Maximum iterations", 600),
        ("weapon", "Weapon selection", 1),
        ("nmerit", "Merit function", 1),
    )

    FLOAT_PREFERENCES = (
        ("fix_wt", "Fix weight", 1.5),
        ("con_wt", "Constraint weight", 1.0),
        ("zero_wt", "Zero weight", 10.0),
        ("viol_wt", "Violation weight", 1.0),
        ("mfn_wt", "Merit function weight", 0.01),
        ("objmin", "Objective minimum", 0.00001),
        ("del", "Step size", 1.0),
        ("delmin", "Minimum step size", 0.0001),
        ("tol", "Tolerance", 0.0001),
        ("smallnum", "Small number threshold", 1.0e-07),
    )

    BOOLEAN_PREFERENCES = (
        ("show_units", "Show units", True),
        ("show_violations", "Show violations", True),
        ("enable_auto_fix", "Enable auto fix", True),
        ("enable_auto_search", "Enable auto search", True),
    )

    def __init__(self):
        self.form = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(self.form)
        self._int_controls = {}
        self._float_controls = {}
        self._bool_controls = {}

        for key, label, default in self.INTEGER_PREFERENCES:
            spin = QtWidgets.QSpinBox()
            spin.setRange(-999999, 999999)
            spin.setValue(default)
            self._int_controls[key] = spin
            layout.addRow(f"{label}:", spin)

        for key, label, default in self.FLOAT_PREFERENCES:
            spin = QtWidgets.QDoubleSpinBox()
            spin.setDecimals(8)
            spin.setRange(-1e9, 1e9)
            spin.setValue(default)
            self._float_controls[key] = spin
            layout.addRow(f"{label}:", spin)

        for key, label, default in self.BOOLEAN_PREFERENCES:
            checkbox = QtWidgets.QCheckBox()
            checkbox.setChecked(default)
            self._bool_controls[key] = checkbox
            layout.addRow(f"{label}:", checkbox)

    def saveSettings(self):
        params = FreeCAD.ParamGet(self.PARAM_PATH)
        for key, _, default in self.INTEGER_PREFERENCES:
            params.SetInt(key, self._int_controls[key].value())
        for key, _, default in self.FLOAT_PREFERENCES:
            params.SetFloat(key, self._float_controls[key].value())
        for key, _, default in self.BOOLEAN_PREFERENCES:
            params.SetBool(key, self._bool_controls[key].isChecked())

    def loadSettings(self):
        params = FreeCAD.ParamGet(self.PARAM_PATH)
        for key, _, default in self.INTEGER_PREFERENCES:
            self._int_controls[key].setValue(params.GetInt(key, default))
        for key, _, default in self.FLOAT_PREFERENCES:
            self._float_controls[key].setValue(params.GetFloat(key, default))
        for key, _, default in self.BOOLEAN_PREFERENCES:
            self._bool_controls[key].setChecked(params.GetBool(key, default))

FreeCADGui.addPreferencePage(SpringPreferencePage, "Spring")
