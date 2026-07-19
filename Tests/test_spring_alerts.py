import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace


def _load_core_utils(monkeypatch):
    monkeypatch.setitem(sys.modules, "FreeCAD", types.ModuleType("FreeCAD"))
    module_path = Path(__file__).resolve().parents[1] / "Features" / "Utils.py"
    spec = importlib.util.spec_from_file_location("spring_core_utils", module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _spring(**overrides):
    values = {
        "WireDiameter": 2.8,
        "OutsideDiameterAtFree": 28.0,
        "CoilsTotal": 4.5,
        "CoilsInactive": 4.0,
        "CoilsActive": 0.5,
        "LengthAtFree": 30.0,
        "LengthAtSolid": 100.0,
        "SpringIndex": 9.0,
        "EndType": "DoubleClosed",
        "AlertErrors": [],
        "AlertWarnings": [],
        "AlertInfos": [],
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_primary_alert_pass_ignores_stale_solid_length(monkeypatch):
    core_utils = _load_core_utils(monkeypatch)
    spring = _spring(LengthAtSolid=100.0)

    core_utils.update_basic_alerts(spring, include_derived=False)

    assert "Free length must not be less than solid length." not in spring.AlertErrors


def test_derived_alert_pass_uses_refreshed_solid_length(monkeypatch):
    core_utils = _load_core_utils(monkeypatch)
    spring = _spring(LengthAtSolid=15.4)

    core_utils.update_basic_alerts(spring)

    assert spring.AlertErrors == []
    assert "Active coils are less than 1." in spring.AlertWarnings
