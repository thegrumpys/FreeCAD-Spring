# Init.py
__title__ = "Spring Workbench"
__author__ = "thegrumpys"
__version__ = "0.1.0"
__url__ = "https://SpringDesignSoftware.org"

import platform
import sys
from pathlib import Path

_PLATFORM_DIR_MAP = {
    "Linux": "Linux",
    "Darwin": "Mac",
    "Windows": "Windows",
}

def _add_compiled_library_path() -> None:
    repo_root = Path(__file__).resolve().parent
    platform_key = platform.system()
    target_dir_name = _PLATFORM_DIR_MAP.get(platform_key)
    if not target_dir_name:
        return
    candidate = repo_root / "lib" / target_dir_name
    search_roots = [candidate]

    pointer_file = candidate / ".springcpp-path"
    if pointer_file.is_file():
        try:
            raw = pointer_file.read_text(encoding="utf-8")
        except OSError:
            raw = ""
        for line in raw.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            pointer_path = Path(stripped)
            if not pointer_path.is_absolute():
                pointer_path = (candidate / pointer_path).resolve()
            search_roots.append(pointer_path)

    added = set()
    for root in search_roots:
        if not root.is_dir():
            continue
        resolved = root.resolve()
        key = str(resolved)
        if key in added:
            continue
        sys.path.insert(0, key)
        added.add(key)

_add_compiled_library_path()

try:
    import SpringCpp  # type: ignore  # noqa: F401
except ImportError:
    pass
