"""Utilities for working with Spring features."""

from __future__ import annotations

import FreeCAD as App


_DEFAULTS = {
    "Compression": {
        "CoilDiameter": 12.0,
        "WireDiameter": 1.2,
        "Pitch": 1.6,
        "ActiveCoils": 8.0,
        "LeftHanded": False,
    },
    "Extension": {
        "CoilDiameter": 10.0,
        "WireDiameter": 1.0,
        "Pitch": 1.2,
        "ActiveCoils": 10.0,
        "StartLength": 6.0,
        "EndLength": 6.0,
        "LeftHanded": False,
    },
    "Torsion": {
        "CoilDiameter": 8.0,
        "WireDiameter": 0.9,
        "Pitch": 1.0,
        "ActiveCoils": 6.0,
        "ArmLength": 12.0,
        "ArmAngle": 90.0,
        "LeftHanded": False,
    },
}


def _ensure_document(document: App.Document | None) -> App.Document:
    if document is None:
        document = App.ActiveDocument
    if document is None:
        document = App.newDocument()
    return document


def _create_spring(document: App.Document, type_name: str, label: str, defaults: dict) -> App.DocumentObject:
    obj = document.addObject(type_name, document.getUniqueObjectName(label))
    for key, value in defaults.items():
        if hasattr(obj, key):
            setattr(obj, key, value)
    document.recompute()
    return obj


def create_compression_spring(document: App.Document | None = None):
    document = _ensure_document(document)
    return _create_spring(
        document,
        "Spring::CompressionSpringFeature",
        "CompressionSpring",
        _DEFAULTS["Compression"],
    )


def create_extension_spring(document: App.Document | None = None):
    document = _ensure_document(document)
    return _create_spring(
        document,
        "Spring::ExtensionSpringFeature",
        "ExtensionSpring",
        _DEFAULTS["Extension"],
    )


def create_torsion_spring(document: App.Document | None = None):
    document = _ensure_document(document)
    return _create_spring(
        document,
        "Spring::TorsionSpringFeature",
        "TorsionSpring",
        _DEFAULTS["Torsion"],
    )


def update_spring_properties(obj: App.DocumentObject, **properties):
    """Update the properties of a spring feature."""

    for name, value in properties.items():
        if hasattr(obj, name):
            setattr(obj, name, value)
    obj.Document.recompute()
    return obj

