import FreeCAD, FreeCADGui
from PySide2 import QtWidgets
import csv, tempfile, os, datetime

from Spring.Features import Utils

class SpringInfoDialog(QtWidgets.QDialog):
    def __init__(self, objs):
        super().__init__()
        self.objs = objs
        self.setWindowTitle("Spring Info")
        layout = QtWidgets.QVBoxLayout(self)

        # --- Results area
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Name", "Outer Ø @ Free (mm)", "Wire Ø (mm)", "Pitch (mm)",
            "Length @ Free (mm)", "Total Coils", "Wire Len (mm)", "Rate (N/mm)"
        ])
        self._populate_table()
        layout.addWidget(self.table)

        # --- Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        export_btn = QtWidgets.QPushButton("Export CSV")
        export_btn.clicked.connect(self._export_csv)
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(export_btn)
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)

    # ------------------------------------------------------------
    def _populate_table(self):
        self.table.setRowCount(len(self.objs))
        for i, obj in enumerate(self.objs):
            outer_d = getattr(obj, "OutsideDiameterAtFree", 20.0)
            wire_d = getattr(obj, "WireDiameter", 2.0)
            inactive_coils = getattr(obj, "CoilsInactive", 2.0)
            length_free = getattr(obj, "LengthAtFree", 25.0)
            pitch = (length_free - inactive_coils) / wire_d
            total_coils = getattr(obj, "CoilsTotal", 25.0)
            wire_len = Utils.spring_wire_length(outer_d, pitch, coils)
            rate = getattr(obj, "Rate", 0.0)

            for j, val in enumerate([
                obj.Name, f"{outer_d:.2f}", f"{wire_d:.2f}",
                f"{pitch:.2f}", f"{length_free:.2f}", f"{total_coils:.2f}",
                f"{wire_len:.1f}", f"{rate:.3f}"
            ]):
                self.table.setItem(i, j, QtWidgets.QTableWidgetItem(val))

        self.table.resizeColumnsToContents()

    # ------------------------------------------------------------
    def _export_csv(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        default_path = os.path.join(tempfile.gettempdir(), f"SpringInfo_{timestamp}.csv")
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export Spring Info", default_path, "CSV files (*.csv)"
        )
        if not path:
            return

        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Name", "OutsideDiameterAtFree_mm", "WireDiameter_mm", "Pitch_mm",
                "LengthAtFree_mm", "Coils", "WireLength_mm", "SpringRate_N_per_mm"
            ])
            for i in range(self.table.rowCount()):
                writer.writerow([
                    self.table.item(i, c).text() for c in range(self.table.columnCount())
                ])

        QtWidgets.QMessageBox.information(
            self, "Spring Info", f"✅ Exported {self.table.rowCount()} springs to:\n{path}"
        )

    # ------------------------------------------------------------
    @staticmethod
    def show_for_selected():
        sel = FreeCADGui.Selection.getSelection()
        if not sel:
            QtWidgets.QMessageBox.warning(None, "Spring Info", "Please select one or more spring objects.")
            return
        dlg = SpringInfoDialog(sel)
        dlg.exec_()
