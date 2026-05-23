"""Task panel shown when editing a Spring object."""

from __future__ import annotations

import html
import re

import FreeCADGui

try:
    from PySide2 import QtCore, QtWidgets
except ImportError:
    from PySide import QtCore, QtGui as QtWidgets

_active_panel = None


def _linkify(message: str) -> str:
    escaped = html.escape(message)
    pattern = re.compile(r"(https?://[^\s<]+)")
    return pattern.sub(r'<a href="\1">\1</a>', escaped)


def _string_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value else []
    try:
        return [str(item) for item in value if str(item)]
    except TypeError:
        return [str(value)] if str(value) else []


def _normalise_alerts(value):
    alerts = {"errors": [], "warnings": [], "infos": []}
    if not value:
        return alerts

    if isinstance(value, dict):
        alerts["errors"] = _string_list(value.get("errors") or value.get("Errors") or value.get("error"))
        alerts["warnings"] = _string_list(value.get("warnings") or value.get("Warnings") or value.get("warning"))
        alerts["infos"] = _string_list(value.get("infos") or value.get("Info") or value.get("info"))
        return alerts

    if isinstance(value, (list, tuple)):
        for item in value:
            if isinstance(item, dict):
                level = str(item.get("level", item.get("severity", "warning"))).lower()
                message = item.get("message", item.get("text", ""))
                target = "warnings"
                if level.startswith("err"):
                    target = "errors"
                elif level.startswith("info"):
                    target = "infos"
                if message:
                    alerts[target].append(str(message))
            elif item:
                alerts["warnings"].append(str(item))
        return alerts

    alerts["warnings"].append(str(value))
    return alerts


def read_alerts_from_object(obj):
    """Read alert data owned by the spring object."""

    try:
        for attr in ("Alerts", "SpringAlerts"):
            if hasattr(obj, attr):
                alerts = _normalise_alerts(getattr(obj, attr))
                if any(alerts.values()):
                    return alerts

        if any(hasattr(obj, attr) for attr in ("AlertErrors", "AlertWarnings", "AlertInfos")):
            return {
                "errors": _string_list(getattr(obj, "AlertErrors", [])),
                "warnings": _string_list(getattr(obj, "AlertWarnings", [])),
                "infos": _string_list(getattr(obj, "AlertInfos", [])),
            }

        proxy = getattr(obj, "Proxy", None)
        if proxy is not None and hasattr(proxy, "getAlerts"):
            return _normalise_alerts(proxy.getAlerts(obj))
    except Exception as exc:
        return {
            "errors": [],
            "warnings": [f"Unable to read spring alerts: {exc}"],
            "infos": [],
        }

    return {"errors": [], "warnings": [], "infos": []}


def _same_object(left, right) -> bool:
    if left is right:
        return True
    if left is None or right is None:
        return False
    return (
        getattr(left, "Name", None) == getattr(right, "Name", None)
        and getattr(getattr(left, "Document", None), "Name", None)
        == getattr(getattr(right, "Document", None), "Name", None)
    )


class SpringAlertsTaskPanel:
    """FreeCAD task panel for inspecting alerts on the edited spring."""

    def __init__(self, obj):
        self.obj = obj
        self._original_shape_color = None
        self._original_shape_color_set = False
        self.form = QtWidgets.QWidget()
        self.form.setWindowTitle("")

        self._heading = QtWidgets.QLabel("Spring Alerts")
        self._title = QtWidgets.QLabel("")
        self._title.setWordWrap(True)
        self._title.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        self._counts = QtWidgets.QLabel("")
        self._counts.setWordWrap(True)
        self._counts.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

        self._tree = QtWidgets.QTreeWidget()
        self._tree.setHeaderHidden(True)
        self._tree.setRootIsDecorated(True)
        self._tree.setSelectionMode(QtWidgets.QAbstractItemView.NoSelection)

        layout = QtWidgets.QVBoxLayout(self.form)
        layout.addWidget(self._heading)
        layout.addWidget(self._title)
        layout.addWidget(self._counts)
        layout.addWidget(self._tree, 1)
        self.refresh()

    def refresh(self):
        self._tree.clear()

        label = getattr(self.obj, "Label", None) or getattr(self.obj, "Name", "Spring")
        name = getattr(self.obj, "Name", "")
        if name and name != label:
            self._title.setText(f"{label} ({name})")
        else:
            self._title.setText(str(label))

        alerts = read_alerts_from_object(self.obj)
        errors = alerts.get("errors", [])
        warnings = alerts.get("warnings", [])
        infos = alerts.get("infos", [])
        self._counts.setText(f"Errors: {len(errors)}    Warnings: {len(warnings)}    Info: {len(infos)}")
        self._update_error_color(bool(errors))

        self._add_group("Errors", errors)
        self._add_group("Warnings", warnings)
        self._add_group("Info", infos)
        self._tree.expandAll()

    def _add_group(self, title, messages):
        group = QtWidgets.QTreeWidgetItem([f"{title} ({len(messages)})"])
        self._tree.addTopLevelItem(group)

        if not messages:
            child = QtWidgets.QTreeWidgetItem(["No alerts"])
            group.addChild(child)
            return

        for message in messages:
            child = QtWidgets.QTreeWidgetItem([""])
            label = QtWidgets.QLabel(_linkify(str(message)))
            label.setWordWrap(True)
            label.setOpenExternalLinks(True)
            label.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
            label.setMargin(2)
            child.setSizeHint(0, label.sizeHint())
            group.addChild(child)
            self._tree.setItemWidget(child, 0, label)

    def getStandardButtons(self):
        return QtWidgets.QDialogButtonBox.Close

    def accept(self):
        self._close_edit_mode()
        return True

    def reject(self):
        self._close_edit_mode()
        return True

    def _close_edit_mode(self):
        global _active_panel

        self._restore_color()
        if _active_panel is self:
            _active_panel = None
        try:
            if FreeCADGui.ActiveDocument is not None:
                FreeCADGui.ActiveDocument.resetEdit()
        except Exception:
            FreeCADGui.Control.closeDialog()

    def _update_error_color(self, has_errors):
        vobj = getattr(self.obj, "ViewObject", None)
        if vobj is None or not hasattr(vobj, "ShapeColor"):
            return

        if not self._original_shape_color_set:
            self._original_shape_color = vobj.ShapeColor
            self._original_shape_color_set = True

        if has_errors:
            if len(self._original_shape_color) == 4:
                vobj.ShapeColor = (1.0, 0.0, 0.0, self._original_shape_color[3])
            else:
                vobj.ShapeColor = (1.0, 0.0, 0.0)
        else:
            self._restore_color()

    def _restore_color(self):
        if not self._original_shape_color_set:
            return

        vobj = getattr(self.obj, "ViewObject", None)
        if vobj is not None and hasattr(vobj, "ShapeColor"):
            vobj.ShapeColor = self._original_shape_color
        self._original_shape_color = None
        self._original_shape_color_set = False


def open_task_panel(obj):
    global _active_panel

    if _active_panel is not None:
        if _same_object(_active_panel.obj, obj):
            _active_panel.refresh()
            return _active_panel
        _active_panel._restore_color()
        _active_panel = None
        try:
            FreeCADGui.Control.closeDialog()
        except Exception:
            pass

    panel = SpringAlertsTaskPanel(obj)
    try:
        FreeCADGui.Control.showDialog(panel)
    except RuntimeError:
        FreeCADGui.Control.closeDialog()
        FreeCADGui.Control.showDialog(panel)
    _active_panel = panel
    return panel


def refresh_task_panel_if_visible(obj=None):
    if _active_panel is None:
        return
    if obj is not None and not _same_object(_active_panel.obj, obj):
        return
    _active_panel.refresh()


def restore_task_panel_color():
    global _active_panel

    if _active_panel is not None:
        _active_panel._restore_color()
        _active_panel = None
