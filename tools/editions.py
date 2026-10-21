"""The Toolbox's folders, defined once for every tool and test on `dev`.

sqlglot Composer (`sqlglot_composer/`) writes its Hive with sqlglot, and runs the code in
`composer_core/`, the Composer core. Spark Composer, the second Edition, was dropped in 6.0
(ADR 0008; the tag `last-spark-composer` holds it). Each Toolbox file is one of:

- a core file, in `composer_core/`: every function a user calls, the import self-check, and
  `CHANGES.md`;
- an Edition file, in `sqlglot_composer/`: `__init__.py` checks both folders and plugs the
  other two into the core, `writing.py` turns a Statement into Hive, and `engine.py` checks the
  library and runs the Example database;
- a page `sqlglot_composer/` holds: the Example gallery, which `tools/example_gallery.py`
  writes, and the how-to page, which `tools/how_to_page.py` writes.

What a file may import besides the standard library and its own folder is `may_import`'s answer,
and `imports_outside` lists every import that breaks it.
"""

from __future__ import annotations

import ast
import re
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Edition:
    folder: str
    product: str
    library: str
    # The Edition files that may import `library`.
    library_files: tuple[str, ...]
    # The Edition files that may import nothing but the standard library and their own folder.
    stdlib_only_files: tuple[str, ...] = ()
    # What its own tests' folder is named for: tests/<option>_edition/.
    option: str = ""

    @property
    def tests_folder(self) -> str:
        return f"{self.option}_edition"


SQLGLOT_COMPOSER = Edition("sqlglot_composer", "sqlglot Composer", "sqlglot",
                           library_files=("writing.py", "engine.py"), option="sqlglot")
EDITIONS = {SQLGLOT_COMPOSER.folder: SQLGLOT_COMPOSER}

# The Editions the export ships to `main`: sqlglot Composer alone, from 6.0.
EXPORTED = (SQLGLOT_COMPOSER,)

# The Composer core: the folder both Editions run, and its files.
CORE = "composer_core"
CORE_PRODUCT = "Composer core"
CORE_FILES = ("__init__.py", "admin.py", "calculations.py", "checks.py", "clauses.py",
              "conditions.py", "edition.py", "example_database.py", "joins.py", "keys.py",
              "lineage.py", "public.py", "refusals.py", "running.py", "stacking.py",
              "tables.py", "trees.py", "unchecked.py", "upkeep.py", "windows.py",
              "CHANGES.md")
EDITION_FILES = ("__init__.py", "writing.py", "engine.py")
# The functions each Edition file offers the shared files, and the dev tools and tests
# (example_database_cannot_run), with their parameters. It may have more of its own.
EDITION_INTERFACE = {
    "writing.py": {
        "hive_text": ["node"],
        "hive_statement": ["node"],
        "readable_text": ["node"],
        "read_back": ["text"],
        "check_writable_call": ["name", "args", "call"],
        "check_writable_type": ["text", "subject"],
    },
    "engine.py": {
        "check_installed": [],
        "example_database_cannot_run": [],
        "run_query": ["text", "tables"],
    },
}
PAGES = ("examples.html", "how_to.html")

# What every Toolbox file may import, besides the standard library and its own folder.
SHARED_IMPORTS = frozenset({"pandas", "numpy"})
def may_import(edition: Edition | None, file_name: str) -> frozenset:
    """What a Toolbox file may import besides the standard library and its own folder.

    `edition` is None for a file of the Composer core, which may import neither Edition nor
    either library. An Edition's files may import the core too.
    """
    if edition is None:
        return SHARED_IMPORTS
    if file_name in edition.stdlib_only_files:
        return frozenset({CORE})
    if file_name in edition.library_files:
        return SHARED_IMPORTS | {edition.library, CORE}
    return SHARED_IMPORTS | {CORE}


def imports_outside(folder: Path) -> list[str]:
    """Each import in a Toolbox folder that `may_import` refuses, as "<file> imports <name>"."""
    edition = None if folder.name == CORE else EDITIONS[folder.name]
    found = []
    for path in sorted(folder.glob("*.py")):
        allowed = sys.stdlib_module_names | may_import(edition, path.name) | {"__future__"}
        found += [f"{path.name} imports {name}" for name in _imported(path)
                  if name.split(".")[0] not in allowed]
    return found


def _imported(path: Path) -> list[str]:
    """Every module a file imports by name; its own folder's, imported relatively, aren't listed."""
    names = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            names += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0:
            names.append(node.module or "")
    return names


# The library the Composer core may not name: only sqlglot Composer's folder imports it.
LIBRARIES = ("sqlglot",)
# sqlglot Composer's name, in any spelling, which the core's docstrings may use.
SQLGLOT_COMPOSER_NAME = re.compile(r"sqlglot[\W_]*composer", re.IGNORECASE)


def libraries_named(text: str) -> list[str]:
    """Which Edition's library a Composer core file names, other than in the name of sqlglot
    Composer, which the core's docstrings use."""
    return [word for word in LIBRARIES
            if re.search(rf"{word}(?![_ ]composer)", text, re.IGNORECASE)]
