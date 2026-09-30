"""The two Editions of the Toolbox, defined once for every tool and test on `dev`.

SQL Composer (`sql_composer/`) writes its Hive with sqlglot. Spark Composer (`spark_composer/`)
writes almost the same Hive itself and runs it on Spark. A file in either folder is one of four
kinds:

- a shared file, written by hand in `sql_composer/` and copied into `spark_composer/` by
  `swap()`, with the folder and product names changed and nothing else;
- an Edition file, written by hand in each folder: `writing.py` turns a Statement into Hive,
  and `engine.py` checks the library and runs the Example database;
- a verbatim file, copied unchanged, so it may name neither Edition;
- the Example gallery page, which `tools/example_gallery.py` writes for each Edition.

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


SQL_COMPOSER = Edition("sql_composer", "SQL Composer", "sqlglot",
                       library_files=("writing.py", "engine.py"))
SPARK_COMPOSER = Edition("spark_composer", "Spark Composer", "pyspark",
                         library_files=("engine.py",), stdlib_only_files=("writing.py",))
EDITIONS = {edition.folder: edition for edition in (SQL_COMPOSER, SPARK_COMPOSER)}

# The Editions the export ships to `main`. Spark Composer joins them in 3.0.
EXPORTED = (SQL_COMPOSER,)

SHARED_FILES = ("__init__.py", "calculations.py", "clauses.py", "conditions.py",
                "example_database.py", "lineage.py", "refusals.py", "running.py", "tables.py",
                "trees.py")
EDITION_FILES = ("writing.py", "engine.py")
VERBATIM_FILES = ("CHANGES.md",)
PAGES = ("examples.html",)

# What every Toolbox file may import, besides the standard library and its own folder.
SHARED_IMPORTS = frozenset({"pandas", "numpy"})
# SQL Composer's shared files that still import sqlglot. Tickets 10-13 of the PySpark work move
# it into writing.py and engine.py, and ticket 13 empties this list.
STILL_IMPORTING_SQLGLOT = ("running.py", "tables.py")

# The sqlglot whose layout Spark Composer's writing.py copies. Ticket 18 of the PySpark work adds
# the test that holds it equal to the sqlglot pin in requirements-dev.txt.
LAYOUT_MIRRORS_SQLGLOT = "30.19.0"
# Each place the two Editions' Hive may differ, with its reason. Ticket 18 gives the rows their
# shape; there are none until Spark Composer's writing.py exists.
DECLARED_DIFFERENCES: tuple = ()


def may_import(edition: Edition, file_name: str) -> frozenset:
    """What a file of `edition`'s folder may import besides the standard library and itself."""
    if file_name in edition.stdlib_only_files:
        return frozenset()
    if file_name in edition.library_files or (
            edition is SQL_COMPOSER and file_name in STILL_IMPORTING_SQLGLOT):
        return SHARED_IMPORTS | {edition.library}
    return SHARED_IMPORTS


def imports_outside(folder: Path) -> list[str]:
    """Each import in an Edition's folder that `may_import` refuses, as "<file> imports <name>"."""
    edition = EDITIONS[folder.name]
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


# --- Making Spark Composer's copy of a shared file ------------------------------------------


class SwapRefused(ValueError):
    """A shared file couldn't be copied into Spark Composer's folder with certainty."""


# Any spelling of either Edition's folder or product name.
SQL_COMPOSER_NAME = re.compile(r"sql[\W_]*composer", re.IGNORECASE)
SPARK_COMPOSER_NAME = re.compile(r"spark[\W_]*composer", re.IGNORECASE)
# What a canonical shared file may not name, since only one Edition has it.
FORBIDDEN_IN_SHARED = ("sqlglot", "pyspark")


def forbidden_words(text: str) -> list[str]:
    """What a canonical shared file names that belongs to one Edition only."""
    found = [word for word in FORBIDDEN_IN_SHARED if word in text.lower()]
    return found + sorted(set(SPARK_COMPOSER_NAME.findall(text)))


def swap(text: str, file_name: str) -> str:
    """Spark Composer's copy of one of SQL Composer's shared or verbatim files."""
    if file_name in VERBATIM_FILES:
        return _verbatim(text, file_name)
    if file_name not in SHARED_FILES:
        raise SwapRefused(f"{file_name} is not a shared or verbatim file, so it isn't copied.")
    forbidden = forbidden_words(text)
    if forbidden:
        raise SwapRefused(f"{file_name} names {', '.join(forbidden)}, which only one Edition has.")
    swapped = _whole_word(SQL_COMPOSER.folder).sub(SPARK_COMPOSER.folder, text)
    swapped = _whole_word(SQL_COMPOSER.product).sub(SPARK_COMPOSER.product, swapped)
    left = sorted(set(SQL_COMPOSER_NAME.findall(swapped)))
    if left:
        raise SwapRefused(f"{file_name} would be left naming {', '.join(left)}.")
    if file_name.endswith(".py"):
        try:
            ast.parse(swapped)
        except SyntaxError as error:
            raise SwapRefused(f"{file_name} doesn't parse after the swap: {error}") from error
    return swapped


def _verbatim(text: str, file_name: str) -> str:
    named = SQL_COMPOSER_NAME.search(text) or SPARK_COMPOSER_NAME.search(text)
    if named:
        raise SwapRefused(f"{file_name} is copied unchanged, so it may name neither Edition, "
                          f"and it names {named[0]}.")
    return text


def _whole_word(name: str) -> re.Pattern:
    return re.compile(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])")
