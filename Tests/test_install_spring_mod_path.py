from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts import install_spring_mod_path as installer


def test_discover_mod_directories_respects_environment(tmp_path: Path) -> None:
    mod_dir = tmp_path / "Mod"
    mod_dir.mkdir()

    env = os.environ.copy()
    env["FREECAD_HOME"] = str(mod_dir)

    discovered = installer.discover_mod_directories(env=env)

    assert discovered == [mod_dir.resolve()]


def test_discover_mod_directories_deduplicates_results(tmp_path: Path) -> None:
    mod_dir = tmp_path / "Mod"
    mod_dir.mkdir()

    env = os.environ.copy()
    env["FREECAD_HOME"] = os.pathsep.join([str(mod_dir), str(mod_dir)])

    discovered = installer.discover_mod_directories(env=env)

    assert discovered == [mod_dir.resolve()]


def test_discover_site_package_directories(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    system_site = tmp_path / "system-site"
    system_site.mkdir()
    user_site = tmp_path / "user-site"
    user_site.mkdir()
    purelib = tmp_path / "purelib"
    purelib.mkdir()
    platlib = tmp_path / "platlib"
    platlib.mkdir()

    monkeypatch.setattr(installer.site, "getsitepackages", lambda: [str(system_site)])
    monkeypatch.setattr(installer.site, "getusersitepackages", lambda: str(user_site))

    def fake_get_path(key: str) -> str | None:
        mapping = {
            "purelib": str(purelib),
            "platlib": str(platlib),
        }
        return mapping.get(key)

    monkeypatch.setattr(installer.sysconfig, "get_path", fake_get_path)

    discovered = installer.discover_site_package_directories()

    assert discovered == [
        system_site.resolve(),
        user_site.resolve(),
        purelib.resolve(),
        platlib.resolve(),
    ]


def test_discover_target_directories_merges_site_and_mod(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    site_packages = tmp_path / "env" / "site-packages"
    site_packages.mkdir(parents=True)
    monkeypatch.setattr(installer, "discover_site_package_directories", lambda: [site_packages])

    mod_dir = tmp_path / "Mod"
    mod_dir.mkdir()
    env = {"FREECAD_HOME": str(mod_dir)}

    result = installer.discover_target_directories(env=env)

    assert result == [site_packages.resolve(), mod_dir.resolve()]


def test_install_stub_package_creates_loader(tmp_path: Path) -> None:
    site_packages = tmp_path / "site-packages"

    written = installer.install_stub_package(site_packages, project_root=PROJECT_ROOT)

    spring_dir = site_packages / "Spring"
    expected = {
        spring_dir / installer.POINTER_FILENAME,
        spring_dir / "__init__.py",
        spring_dir / "_bootstrap.py",
        spring_dir / "Init.py",
        spring_dir / "InitGui.py",
    }

    assert set(written) == expected
    pointer_contents = (spring_dir / installer.POINTER_FILENAME).read_text(encoding="utf-8")
    assert pointer_contents.strip() == str(PROJECT_ROOT)

    second_run = installer.install_stub_package(site_packages, project_root=PROJECT_ROOT)
    assert second_run == []


def test_install_stub_package_skips_real_checkout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    target = tmp_path / "Mod"
    target.mkdir()

    spring_dir = target / "Spring"
    if hasattr(os, "symlink"):
        spring_dir.symlink_to(PROJECT_ROOT)
    else:
        pytest.skip("symlink support is required for this test")

    written = installer.install_stub_package(target, project_root=PROJECT_ROOT)
    assert written == []

