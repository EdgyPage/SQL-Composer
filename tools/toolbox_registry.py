"""The Toolbox's folder, `sqlglot_composer/`, defined once for every tool and test on `dev`.

From 6.0 the Toolbox is this one folder (ADR 0008 and ADR 0009). It holds every function a user
calls, the import self-check, `writing.py`, which writes a Statement as Hive with sqlglot,
`engine.py`, which checks sqlglot, and `version.txt`, the one place its version is written.

The Example database is not in it: since Toolbox 8.7 (ticket 12) it is dev's alone, the package
`EXAMPLE_DATABASE` beside the folder, which no Toolbox file imports.

Nor are the pages (Toolbox 8.7, ticket 13): main's `docs/`, `DOCS`, holds them, written on dev
into `DOCS_ON_DEV`. They are the how-to page, which `tools/how_to_page.py` writes; the Example
gallery, `tools/example_gallery.py`'s; the Workflows overview, `tools/workflows_page.py`'s; and
the Example projects page, `tools/example_projects_page.py`'s, which links each Example
project's lineage pages, shipped beside it at `lineage_pages`' paths.

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
# Dev's Example database, beside the folder at the repo's top: never shipped, never imported by
# the Toolbox (Toolbox 8.7, ticket 12).
EXAMPLE_DATABASE = "example_database"
# The only files that may import sqlglot: writing.py writes Hive with it, engine.py checks it,
# and converting.py reads someone else's Hive with it, for a Conversion (Toolbox 7.2, ticket
# 05).
LIBRARY_FILES = ("writing.py", "engine.py", "converting.py")
PYTHON_FILES = ("__init__.py", "admin.py", "calculations.py", "checks.py", "clauses.py",
                "decisions.py",
                "comparisons.py", "conditions.py", "converting.py", "describe.py",
                "effective_logic.py", "engine.py",
                "html_page.py", "joins.py",
                "keys.py", "kinds.py", "lineage.py", "lineage_state.py", "notebooks.py",
                "project.py",
                "project_files.py", "project_lineage.py", "project_templates.py", "public.py",
                "python_steps.py",
                "refusals.py", "run_values.py", "running.py", "scheduled_runs.py",
                "script_tags.py", "shared.py",
                "stacking.py", "tables.py",
                "trees.py",
                "unchecked.py", "upgrades.py", "upkeep.py", "windows.py", "workflows.py",
                "writing.py")
# The one file that says which Toolbox version the folder is (ADR 0013). On dev it holds the
# version alone; the export adds when it was exported, from which commit, and each file's hash.
VERSION_FILE = "version.txt"
FILES = PYTHON_FILES + (VERSION_FILE,)

# Main's docs/ and where dev writes it: the pages a user reads in place of code (Toolbox 8.7,
# ticket 13). Dev's own docs/ holds its other files, which never ship.
DOCS = "docs"
DOCS_ON_DEV = "docs/main"
PAGES = ("examples.html", "example_projects.html", "how_to.html", "workflows.html")
# Dev's Example projects, which main doesn't hold: the Example projects page shows them, and
# their lineage pages ship beside it, in docs/example_projects/.
EXAMPLE_PROJECTS = "example_projects"


def lineage_pages(root: Path) -> dict[str, Path]:
    """Each Example project's lineage page under `root`, dev's checkout, by the path main's
    docs/ holds it at, such as example_projects/starter/tables/t/lineage/x.html, the same path
    as on dev, below docs/."""
    return {path.relative_to(root).as_posix(): path
            for path in sorted((root / EXAMPLE_PROJECTS).glob("*/**/lineage/*.html"))}

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
