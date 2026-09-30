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

import argparse
import ast
import importlib
import importlib.abc
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
    # What `--edition` calls it, for pytest and the tools; its own tests are in
    # tests/<option>_edition/.
    option: str = ""

    @property
    def tests_folder(self) -> str:
        return f"{self.option}_edition"


SQL_COMPOSER = Edition("sql_composer", "SQL Composer", "sqlglot",
                       library_files=("writing.py", "engine.py"), option="sqlglot")
SPARK_COMPOSER = Edition("spark_composer", "Spark Composer", "pyspark",
                         library_files=("engine.py",), stdlib_only_files=("writing.py",),
                         option="spark")
EDITIONS = {edition.folder: edition for edition in (SQL_COMPOSER, SPARK_COMPOSER)}
# Each Edition by its `--edition` name.
BY_OPTION = {edition.option: edition for edition in EDITIONS.values()}

# The Editions the export ships to `main`: both, from 3.0.
EXPORTED = (SQL_COMPOSER, SPARK_COMPOSER)

SHARED_FILES = ("__init__.py", "calculations.py", "clauses.py", "conditions.py",
                "example_database.py", "lineage.py", "refusals.py", "running.py", "tables.py",
                "trees.py")
EDITION_FILES = ("writing.py", "engine.py")
# The functions each Edition file offers the shared files, with their parameters: both
# Editions' copies have exactly these. Either may have more of its own.
EDITION_INTERFACE = {
    "writing.py": {
        "hive_text": ["node"],
        "hive_statement": ["node"],
        "readable_text": ["node"],
        "read_back": ["text"],
        "check_writable_call": ["name", "args", "call"],
        "describe_text": ["name"],
        "show_partitions_text": ["name"],
    },
    "engine.py": {
        "check_installed": [],
        "example_database_cannot_run": [],
        "run_query": ["text", "tables"],
    },
}
VERBATIM_FILES = ("CHANGES.md",)
PAGES = ("examples.html",)

# What every Toolbox file may import, besides the standard library and its own folder.
SHARED_IMPORTS = frozenset({"pandas", "numpy"})
# The sqlglot whose layout Spark Composer's writing.py copies, which
# tests/repo/test_edition_parity.py holds equal to the sqlglot pin in requirements-dev.txt.
LAYOUT_MIRRORS_SQLGLOT = "30.19.0"


@dataclass(frozen=True)
class Difference:
    """One place the two Editions differ on purpose: in the Hive they write, or in a refusal.

    `why` says it in plain words, for the README. `sql_composer` and `spark_composer` are the
    same piece of what each Edition shows, its Hive or its refusal, as the golden corpus shows it
    in one of `cases`, the ids of the golden cases the difference explains. `spark_composer_adds` is True
    for text Spark Composer adds to SQL Composer's Hive, which its readable_text leaves out.
    tests/repo/test_edition_parity.py holds that the two goldens differ in no other case, that
    each listed case really differs, and that with what Spark Composer adds left out, a case
    differs only if a row that adds nothing lists it. `title` names what differs, for the
    README's list.
    """

    title: str
    why: str
    sql_composer: str
    spark_composer: str
    cases: tuple[str, ...]
    spark_composer_adds: bool = False


# Each place the two Editions differ on purpose.
DECLARED_DIFFERENCES = {
    "division": Difference(
        title="Dividing by a column.",
        why="Spark stops the whole query with an error when it divides by 0, where Hive gives "
        "NULL. So Spark Composer writes x / y as x / NULLIF(y, 0): NULLIF(y, 0) is NULL when "
        "y is 0, so that row gets NULL, as in Hive. A divisor that is a number other than 0 is "
        "written as it is.",
        sql_composer="SUM(job_runs.duration_mins) / COUNT(*)",
        spark_composer="SUM(job_runs.duration_mins) / NULLIF(COUNT(*), 0)",
        cases=("edge:brackets:nested", "edge:brackets:aggregates",
               "worked:labels_and_counts:failed_share_per_job"),
        spark_composer_adds=True,
    ),
    "float": Difference(
        title="A Python float.",
        why="Spark reads 0.5 as a DECIMAL, an exact decimal that pandas gets as a Decimal, "
        "where Hive reads a DOUBLE, SQL's float. So Spark Composer writes a Python float as "
        "0.5D: the D marks a DOUBLE, and doesn't mean days. A number written with e, such as "
        "1e-05, is a DOUBLE already.",
        sql_composer="COALESCE(job_runs.avg_retry_secs, 0.1)",
        spark_composer="COALESCE(job_runs.avg_retry_secs, 0.1D)",
        cases=("worked:nan_in_a_list:fixed", "edge:calculations:values",
               "worked:labels_and_counts:failed_share_per_job"),
        spark_composer_adds=True,
    ),
    "hive_function": Difference(
        title="A hive_function call.",
        why="SQL Composer has sqlglot read a hive_function call back, and writes the call as "
        "sqlglot does: sometimes by another name that does the same, such as COALESCE for nvl, "
        "and sometimes with an argument changed, such as a date_format pattern 'YYYY-MM' "
        "written 'yyyy-MM', which isn't the same: YYYY is the year a week belongs to. Spark "
        "Composer has no sqlglot, so it writes the call by the name and the arguments it was "
        "given. And for a function hive_function's own list doesn't count, SQL Composer refuses "
        "a call sqlglot can't build, which Spark Composer writes as given. Spark refuses some of "
        "these when it runs, such as nvl2 with 1 argument, and runs others, such as "
        "unix_timestamp with none or approx_count_distinct with 2.",
        sql_composer="COALESCE(job_runs.status, 'none')",
        spark_composer="NVL(job_runs.status, 'none')",
        cases=("edge:hive_function:nvl", "edge:hive_function:nvl2",
               "edge:hive_function:regexp_extract", "edge:hive_function:date_format",
               "edge:hive_function:substr", "edge:hive_function:instr"),
    ),
}


def may_import(edition: Edition, file_name: str) -> frozenset:
    """What a file of `edition`'s folder may import besides the standard library and itself."""
    if file_name in edition.stdlib_only_files:
        return frozenset()
    if file_name in edition.library_files:
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
    swapped = named_for(SPARK_COMPOSER, text, file_name)
    if file_name.endswith(".py"):
        try:
            ast.parse(swapped)
        except SyntaxError as error:
            raise SwapRefused(f"{file_name} doesn't parse after the swap: {error}") from error
    return swapped


def named_for(edition: Edition, text: str, where: str = "The text") -> str:
    """Text written for SQL Composer, such as a Worked example, naming `edition` instead.

    Text that would still name SQL Composer another way, as SQL-Composer, is refused.
    """
    swapped = _whole_word(SQL_COMPOSER.folder).sub(edition.folder, text)
    swapped = _whole_word(SQL_COMPOSER.product).sub(edition.product, swapped)
    left = sorted(set(SQL_COMPOSER_NAME.findall(swapped))) if edition is not SQL_COMPOSER else []
    if left:
        raise SwapRefused(f"{where} would be left naming {', '.join(left)}.")
    return swapped


def _verbatim(text: str, file_name: str) -> str:
    named = SQL_COMPOSER_NAME.search(text) or SPARK_COMPOSER_NAME.search(text)
    if named:
        raise SwapRefused(f"{file_name} is copied unchanged, so it may name neither Edition, "
                          f"and it names {named[0]}.")
    return text


def _whole_word(name: str) -> re.Pattern:
    return re.compile(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])")


# --- Running the same tests and tools against Spark Composer ------------------------------------


class _OnlyTheAlias(importlib.abc.MetaPathFinder):
    """Refuses any `sql_composer.*` module the alias doesn't hold, rather than load the real one."""

    def find_spec(self, fullname, path, target=None):
        if _in_sql_composer(fullname):
            raise ImportError(f"{fullname} isn't part of the Spark run's alias: only Spark "
                              "Composer's own modules stand in for SQL Composer's.")
        return None


def use(edition: Edition) -> None:
    """Make `import sql_composer` give `edition`'s modules, and make sqlglot unimportable.

    The shared tests and the Worked examples say `from sql_composer import ...`; in Spark
    Composer's run each of those names is Spark Composer's. It must run before anything imports
    sql_composer. For SQL Composer it does nothing.
    """
    if edition is SQL_COMPOSER:
        return
    if any(_in_sql_composer(name) for name in sys.modules):
        raise RuntimeError("editions.use: sql_composer is already imported, so the run would "
                           "mix the two Editions. Choose the Edition before any Toolbox import.")
    sys.modules["sqlglot"] = None  # any `import sqlglot` now fails loudly
    for module in toolbox_modules():
        own = edition.folder + module.removeprefix("sql_composer")
        sys.modules[module] = importlib.import_module(own)
    sys.meta_path.insert(0, _OnlyTheAlias())


def _in_sql_composer(module: str) -> bool:
    return module == "sql_composer" or module.startswith("sql_composer.")


def toolbox_modules() -> list[str]:
    """The name of every module of an Edition's folder, as `sql_composer` and its files."""
    return ["sql_composer"] + [f"sql_composer.{name.removesuffix('.py')}"
                               for name in SHARED_FILES + EDITION_FILES if name != "__init__.py"]


def edition_on_command_line(arguments: list[str]) -> Edition:
    """The Edition a tool's command line asks for: --edition sqlglot, the default, or spark."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--edition", choices=sorted(BY_OPTION), default=SQL_COMPOSER.option)
    known, _ = parser.parse_known_args(arguments[1:])
    return BY_OPTION[known.edition]
