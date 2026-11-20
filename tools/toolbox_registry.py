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
and `imports_outside` lists every import that breaks it. One file is loaded from outside the
folder, alone: the workbook reader, `WORKBOOK_READER`, which `WORKBOOK_READER_LOADED_BY` loads
by the folder's path (Toolbox 8.9, ticket 01), so it may import nothing but the standard
library.
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
# converting.py reads someone else's Hive with it, for a Conversion (Toolbox 7.2, ticket 05),
# workbook_hive.py, workbook_formulas.py, workbook_power_query.py and workbook_totals.py write a
# Formula workbook's Hive as its trees, with workbook_pivot_hive.py writing its PivotTables',
# lean_hive.py keeps any query's CTEs lean (Toolbox 8.9, tickets 04 to 06), and
# pivot_filters.py reads the Pivot filters Hive marks (ticket 07); hive_executor.py runs Hive
# on sqlglot's own executor, on this computer, and workbook_check.py runs a workbook's finals
# on it, the Workbook check (ticket 09).
LIBRARY_FILES = ("writing.py", "engine.py", "converting.py", "workbook_hive.py",
                 "workbook_formulas.py", "workbook_power_query.py", "workbook_totals.py",
                 "workbook_pivot_hive.py", "lean_hive.py", "pivot_filters.py",
                 "hive_executor.py", "workbook_check.py")
PYTHON_FILES = ("__init__.py", "admin.py", "calculations.py", "checks.py", "clauses.py",
                "decisions.py",
                "comparisons.py", "conditions.py", "converting.py", "describe.py",
                "effective_logic.py", "engine.py", "hive_executor.py",
                "html_page.py", "joins.py",
                "keys.py", "kinds.py", "lean_hive.py", "lineage.py", "lineage_difference.py",
                "lineage_state.py", "notebooks.py", "pivot_filters.py", "project.py",
                "project_files.py", "project_lineage.py", "project_templates.py", "public.py",
                "python_steps.py",
                "refusals.py", "run_values.py", "running.py", "scheduled_runs.py",
                "script_tags.py", "shared.py",
                "stacking.py", "tables.py",
                "trees.py",
                "unchecked.py", "upgrades.py", "upkeep.py", "windows.py",
                "workbook_check.py", "workbook_conversion.py", "workbook_formula_reader.py",
                "workbook_formulas.py",
                "workbook_hive.py",
                "workbook_m_reader.py", "workbook_pivot_hive.py", "workbook_power_query.py",
                "workbook_totals.py", "workbook_reader.py", "workflows.py", "writing.py")
# The workbook reader (Toolbox 8.9, ticket 01; ADR 0016), the one reader of an Excel workbook,
# and the one file outside the folder that loads it. That file writes a workbook as text for a
# Copilot chat with nothing but Python, so it loads the reader alone, by the folder's path,
# never through the Toolbox's __init__.py, which checks sqlglot: the reader may import the
# standard library alone, and nothing of its own folder.
WORKBOOK_READER = "workbook_reader.py"
WORKBOOK_READER_LOADED_BY = "copilot/workbook_text.py"
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
    """What a Toolbox file may import besides the standard library and its own folder: the
    workbook reader, nothing, nor its own folder."""
    if file_name == WORKBOOK_READER:
        return frozenset()
    if file_name in LIBRARY_FILES:
        return SHARED_IMPORTS | {LIBRARY}
    return SHARED_IMPORTS


def imports_outside(folder: Path) -> list[str]:
    """Each import in the Toolbox's folder that `may_import` refuses, as
    "<file> imports <name>", and each import of its own folder in the workbook reader, which is
    loaded alone, as "workbook_reader.py imports .<name>"."""
    found = []
    for path in sorted(folder.glob("*.py")):
        allowed = sys.stdlib_module_names | may_import(path.name) | {"__future__"}
        found += [f"{path.name} imports {name}" for name in _imported(path)
                  if name.split(".")[0] not in allowed]
        if path.name == WORKBOOK_READER:
            found += [f"{path.name} imports {name}" for name in _imported_relatively(path)]
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


def _imported_relatively(path: Path) -> list[str]:
    """Every module a file imports from its own folder, relatively, such as ".shared"."""
    names = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.level > 0:
            names.append("." * node.level + (node.module or ""))
    return names
