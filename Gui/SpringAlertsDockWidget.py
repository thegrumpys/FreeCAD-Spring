"""Dock widget for inspecting alerts on Spring objects."""

from __future__ import annotations

import html
import re

import FreeCAD
import FreeCADGui

try:
    from PySide2 import QtCore, QtWidgets
except ImportError:
    from PySide import QtCore, QtGui as QtWidgets

_active_dock = None
_selection_observer = None


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


def _object_from_selection(doc_name, obj_name):
    try:
        document = FreeCAD.getDocument(doc_name)
        return document.getObject(obj_name)
    except Exception:
        return None


def _has_alerts_interface(obj) -> bool:
    if obj is None:
        return False
    if any(hasattr(obj, attr) for attr in ("Alerts", "SpringAlerts", "AlertErrors", "AlertWarnings", "AlertInfos")):
        return True
    proxy = getattr(obj, "Proxy", None)
    return proxy is not None and hasattr(proxy, "getAlerts")


class _SpringAlertsSelectionObserver:
    def addSelection(self, doc, obj, sub, pnt):  # noqa: N802 - FreeCAD callback name
        selected = _object_from_selection(doc, obj)
        if _active_dock is not None and _has_alerts_interface(selected):
            _active_dock.set_object(selected)


def _ensure_selection_observer():
    global _selection_observer

    if _selection_observer is not None:
        return

    observer = _SpringAlertsSelectionObserver()
    try:
        FreeCADGui.Selection.addObserver(observer)
    except Exception:
        return
    _selection_observer = observer


class SpringAlertsWidget:
    """Widget for inspecting alerts on the selected spring."""

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

    def set_object(self, obj):
        if _same_object(self.obj, obj):
            self.refresh()
            return
        self._restore_color()
        self.obj = obj
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


class SpringAlertsDockWidget(QtWidgets.QDockWidget):
    """Non-modal FreeCAD dock for spring alerts."""

    def __init__(self, obj, parent=None):
        super().__init__("Spring Alerts", parent)
        self.alerts_widget = SpringAlertsWidget(obj)
        self.setObjectName("SpringAlertsDockWidget")
        self.setWidget(self.alerts_widget.form)
        self.setAllowedAreas(
            QtCore.Qt.LeftDockWidgetArea
            | QtCore.Qt.RightDockWidgetArea
            | QtCore.Qt.BottomDockWidgetArea
        )

    def set_object(self, obj):
        self.alerts_widget.set_object(obj)

    def refresh(self):
        self.alerts_widget.refresh()

    def restore_color(self):
        self.alerts_widget._restore_color()

    def closeEvent(self, event):  # noqa: N802 - Qt callback name
        global _active_dock

        self.restore_color()
        if _active_dock is self:
            _active_dock = None
        super().closeEvent(event)


def show_dock_for_object(obj, activate=True):
    global _active_dock

    if not _has_alerts_interface(obj):
        return None

    _ensure_selection_observer()

    if _active_dock is not None:
        _active_dock.set_object(obj)
        _active_dock.show()
        if activate:
            _active_dock.raise_()
            _active_dock.activateWindow()
        return _active_dock

    main_window = FreeCADGui.getMainWindow()
    dock = SpringAlertsDockWidget(obj, main_window)
    main_window.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)
    dock.show()
    if activate:
        dock.raise_()
        try:
            dock.activateWindow()
        except Exception:
            pass
    _active_dock = dock
    return dock


def refresh_dock_if_visible(obj=None):
    if _active_dock is None:
        return
    if obj is not None and not _same_object(_active_dock.alerts_widget.obj, obj):
        return
    _active_dock.refresh()


def restore_dock_color():
    if _active_dock is not None:
        _active_dock.restore_color()
