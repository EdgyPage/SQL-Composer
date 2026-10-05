"""Spark Composer stands alone: nothing of sqlglot Composer's folder, and nothing of sqlglot, is loaded.

Each test first imports every Toolbox module, every Worked example and the tools, as the shared
tests do, so a stray import anywhere shows here, whatever order the tests run in.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import editions

ROOT = Path(__file__).resolve().parents[2]


def _loaded():
    for module in editions.toolbox_modules():
        importlib.import_module(module)
    for folder in ("statements", "building_blocks", "table_references"):
        for path in sorted((ROOT / "worked_examples" / folder).glob("*.py")):
            importlib.import_module(f"{folder}.{path.stem}")
    for tool in ("example_gallery", "hive_corpus"):
        importlib.import_module(tool)
    return [(name, module) for name, module in list(sys.modules.items()) if module is not None]


def test_no_module_from_sqlglot_composers_folder_is_loaded() -> None:
    folder = ROOT / "sqlglot_composer"
    loaded = sorted(name for name, module in _loaded()
                    if getattr(module, "__file__", None)
                    and Path(module.__file__).resolve().parent == folder)
    assert loaded == []


def test_no_sqlglot_module_is_loaded() -> None:
    assert sorted(name for name, _ in _loaded() if name.split(".")[0] == "sqlglot") == []
