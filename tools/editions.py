"""The two Editions of the Toolbox, defined once for every tool and test on `dev`.

SQL Composer (`sql_composer/`) writes its Hive with sqlglot. Spark Composer (`spark_composer/`)
writes the same Hive itself and runs it on Spark. A file in either folder is one of four kinds:

- a shared file, written by hand in `sql_composer/` and copied into `spark_composer/` by
  `swap()`, with the package and product names changed and nothing else;
- an Edition file, written by hand in each folder: `writing.py` turns a Statement into Hive,
  and `engine.py` checks the library and runs the Example database;
- a verbatim file, copied unchanged, so it may name neither Edition;
- a page, which each Edition generates for itself.

What a file may import besides the standard library and its own package is in `may_import`.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Edition:
    package: str
    product: str
    library: str


SQL_COMPOSER = Edition("sql_composer", "SQL Composer", "sqlglot")
SPARK_COMPOSER = Edition("spark_composer", "Spark Composer", "pyspark")
EDITIONS = {edition.package: edition for edition in (SQL_COMPOSER, SPARK_COMPOSER)}

# The Editions the export ships to `main`. Spark Composer joins them in 3.0.
EXPORTED = ("sql_composer",)

SHARED_FILES = ("__init__.py", "calculations.py", "clauses.py", "conditions.py",
                "example_database.py", "lineage.py", "refusals.py", "running.py", "tables.py",
                "trees.py")
EDITION_FILES = ("writing.py", "engine.py")
VERBATIM_FILES = ("CHANGES.md",)
PAGES = ("examples.html",)

# What every Toolbox file may import, besides the standard library and its own package.
SHARED_IMPORTS = frozenset({"pandas", "numpy"})
# The Edition files that may also import their Edition's library. Spark Composer's writing.py
# may not: it writes Hive on its own.
LIBRARY_FILES = {"sql_composer": ("writing.py", "engine.py"), "spark_composer": ("engine.py",)}
# SQL Composer's shared files that still import sqlglot. Tickets 10-13 of the PySpark work move
# it into writing.py and engine.py, emptying this list.
STILL_IMPORTING_SQLGLOT = ("__init__.py", "calculations.py", "clauses.py", "conditions.py",
                           "example_database.py", "lineage.py", "running.py", "tables.py")

# The sqlglot the Spark printer copies its layout from; a test holds it equal to the pin.
LAYOUT_MIRRORS_SQLGLOT = "30.19.0"
# Each place the two Editions' Hive may differ, with its reason. Empty until the Spark printer.
DECLARED_DIFFERENCES: list[dict] = []


def may_import(edition: Edition, file_name: str) -> frozenset:
    """What a file of `edition`'s folder may import besides the standard library and itself."""
    if file_name in LIBRARY_FILES[edition.package]:
        return SHARED_IMPORTS | {edition.library}
    if edition is SQL_COMPOSER and file_name in STILL_IMPORTING_SQLGLOT:
        return SHARED_IMPORTS | {edition.library}
    return SHARED_IMPORTS


# --- Making Spark Composer's copy of a shared file ------------------------------------------


class SwapRefused(ValueError):
    """A shared file couldn't be copied into Spark Composer's folder with certainty."""


# A name the swap would leave behind: any spelling of SQL Composer's package or product.
LEFTOVER = re.compile(r"sql[\W_]{0,2}composer", re.IGNORECASE)
# Either Edition's name, which a verbatim file may not hold.
EITHER_EDITION = re.compile(r"(sql|spark)[\W_]{0,2}composer", re.IGNORECASE)
# The libraries a shared file may not name: each belongs to one Edition.
LIBRARIES = ("sqlglot", "pyspark")


def _whole_word(name: str) -> re.Pattern:
    return re.compile(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])")


def swap(text: str, file_name: str) -> str:
    """Spark Composer's copy of one of SQL Composer's shared or verbatim files."""
    if file_name not in SHARED_FILES + VERBATIM_FILES:
        raise SwapRefused(f"{file_name} is not a shared or verbatim file, so it isn't copied.")
    named = [library for library in LIBRARIES if library in text.lower()]
    if named and file_name in SHARED_FILES:
        raise SwapRefused(f"{file_name} names {', '.join(named)}, which only one Edition has.")
    swapped = text
    if file_name in SHARED_FILES:
        swapped = _whole_word(SQL_COMPOSER.package).sub(SPARK_COMPOSER.package, swapped)
        swapped = _whole_word(SQL_COMPOSER.product).sub(SPARK_COMPOSER.product, swapped)
    if file_name in VERBATIM_FILES and EITHER_EDITION.search(text):
        raise SwapRefused(f"{file_name} is copied unchanged, so it may name neither Edition, "
                          f"and it names {EITHER_EDITION.search(text)[0]}.")
    left = sorted(set(LEFTOVER.findall(swapped)))
    if left:
        raise SwapRefused(f"{file_name} would be left naming {', '.join(left)}.")
    if file_name.endswith(".py"):
        try:
            ast.parse(swapped)
        except SyntaxError as error:
            raise SwapRefused(f"{file_name} doesn't parse after the swap: {error}") from error
    return swapped
