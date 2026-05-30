import importlib
import sys
import types
from types import SimpleNamespace


def _load_compression_spring(monkeypatch):
    fake_freecad = types.ModuleType("FreeCAD")
    fake_freecad.Console = SimpleNamespace(PrintMessage=lambda *_args, **_kwargs: None)
    fake_freecad.Vector = lambda *args, **kwargs: (args, kwargs)
    fake_freecad.Rotation = lambda *args, **kwargs: (args, kwargs)

    monkeypatch.setitem(sys.modules, "FreeCAD", fake_freecad)
    monkeypatch.setitem(sys.modules, "Part", types.ModuleType("Part"))
    sys.modules.pop("Features.Compression.Spring", None)
    return importlib.import_module("Features.Compression.Spring")


def test_tight_spring_index_uses_fine_display_mesh(monkeypatch):
    spring_module = _load_compression_spring(monkeypatch)

    deviation, angular = spring_module._spring_index_view_quality_targets(2.93571)

    assert deviation == spring_module.MIN_VIEW_DEVIATION
    assert angular == spring_module.MIN_VIEW_ANGULAR_DEFLECTION


def test_view_quality_interpolates_back_to_defaults(monkeypatch):
    spring_module = _load_compression_spring(monkeypatch)

    deviation, angular = spring_module._spring_index_view_quality_targets(3.5)

    assert deviation == 0.275
    assert angular == 19.25


def test_apply_view_quality_sets_deviation_and_angular_deflection(monkeypatch):
    spring_module = _load_compression_spring(monkeypatch)
    view = SimpleNamespace(Deviation=0.5, AngularDeflection=28.5)
    obj = SimpleNamespace(SpringIndex=2.93929, ViewObject=view)

    spring_module._apply_spring_index_view_quality(obj)

    assert view.Deviation == spring_module.MIN_VIEW_DEVIATION
    assert view.AngularDeflection == spring_module.MIN_VIEW_ANGULAR_DEFLECTION
