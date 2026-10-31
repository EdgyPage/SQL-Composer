"""The Toolbox's folder, `sqlglot_composer/`, defined once for every tool and test on `dev`.

From 6.0 the Toolbox is this one folder (ADR 0008 and ADR 0009). It holds every function a user
calls, the import self-check, `writing.py`, which writes a Statement as Hive with sqlglot,
`engine.py`, which checks sqlglot and runs the Example database, two pages: the Example
gallery, which `tools/example_gallery.py` writes, and the how-to page, which
`tools/how_to_page.py` writes, and `version.txt`, the one place its version is written.

What a file may import besides the standard library and its own folder is `may_import`'s answer,
and `imports_outside` lists every import that breaks it.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

FOLDER = "sqlglot_composer"
PRODUCT = "sqlglot Composer"
LIBRARY = "sqlglot"
# The only files that may import sqlglot: writing.py writes Hive with it, engine.py checks it
# and runs the Example database on it, and converting.py reads someone else's Hive with it,
# for a Conversion (Toolbox 7.2, ticket 05).
LIBRARY_FILES = ("writing.py", "engine.py", "converting.py")
PYTHON_FILES = ("__init__.py", "admin.py", "calculations.py", "checks.py", "clauses.py",
                "comparisons.py", "conditions.py", "converting.py", "describe.py", "engine.py",
                "example_database.py", "joins.py",
                "keys.py", "kinds.py", "lineage.py", "notebooks.py", "project.py",
                "project_files.py", "project_templates.py", "public.py", "python_steps.py",
                "refusals.py", "running.py", "shared.py", "stacking.py", "tables.py",
                "trees.py",
                "unchecked.py", "upgrades.py", "upkeep.py", "windows.py", "writing.py")
PAGES = ("examples.html", "how_to.html")
# The one file that says which Toolbox version the folder is (ADR 0013). On dev it holds the
# version alone; the export adds when it was exported, from which commit, and each file's hash.
VERSION_FILE = "version.txt"
FILES = PYTHON_FILES + PAGES + (VERSION_FILE,)

# What every Toolbox file may import, besides the standard library and its own folder.
SHARED_IMPORTS = frozenset({"pandas", "numpy"})


def may_import(file_name: str) -> frozenset[str]:
    """What a Toolbox file may import besides the standard library and its own folder."""
    if file_name in LIBRARY_FILES:
        return SHARED_IMPORTS | {LIBRARY}
    return SHARED_IMPORTS


def imports_outside(folder: Path) -> list[str]:
    """Each import in the Toolbox's folder that `may_import` refuses, as
    "<file> imports <name>"."""
    found = []
    for path in sorted(folder.glob("*.py")):
        allowed = sys.stdlib_module_names | may_import(path.name) | {"__future__"}
        found += [f"{path.name} imports {name}" for name in _imported(path)
                  if name.split(".")[0] not in allowed]
    return found


def _imported(path: Path) -> list[str]:
    """Every module a file imports by name; its own folder's, imported relatively, aren't
    listed."""
    names = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            names.append(node.module or "")
    return names
