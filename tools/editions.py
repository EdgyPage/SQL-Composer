"""The two Editions of the Toolbox, defined once for every tool and test on `dev`.

sqlglot Composer (`sqlglot_composer/`) writes its Hive with sqlglot. Spark Composer
(`spark_composer/`) writes almost the same Hive itself and runs it on Spark. Both run the code
in `composer_core/`, the Composer core, which is written once. Each Toolbox file is one of:

- a core file, in `composer_core/`: every function a user calls, the import self-check, and
  `CHANGES.md`;
- an Edition file, written by hand in each Edition's folder: `__init__.py` checks both folders
  and plugs the other two into the core, `writing.py` turns a Statement into Hive, and
  `engine.py` checks the library and runs the Example database;
- a page each Edition's folder holds: the Example gallery, which `tools/example_gallery.py`
  writes, and the how-to page, which `tools/how_to_page.py` writes.

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


SQLGLOT_COMPOSER = Edition("sqlglot_composer", "sqlglot Composer", "sqlglot",
                           library_files=("writing.py", "engine.py"), option="sqlglot")
SPARK_COMPOSER = Edition("spark_composer", "Spark Composer", "pyspark",
                         library_files=("engine.py",), stdlib_only_files=("writing.py",),
                         option="spark")
EDITIONS = {edition.folder: edition for edition in (SQLGLOT_COMPOSER, SPARK_COMPOSER)}
# Each Edition by its `--edition` name.
BY_OPTION = {edition.option: edition for edition in EDITIONS.values()}

# The Editions the export ships to `main`: both, from 3.0.
EXPORTED = (SQLGLOT_COMPOSER, SPARK_COMPOSER)

# The Composer core: the folder both Editions run, and its files.
CORE = "composer_core"
CORE_PRODUCT = "Composer core"
CORE_FILES = ("__init__.py", "calculations.py", "checks.py", "clauses.py", "conditions.py",
              "edition.py", "example_database.py", "lineage.py", "public.py", "refusals.py",
              "running.py", "tables.py", "trees.py", "CHANGES.md")
EDITION_FILES = ("__init__.py", "writing.py", "engine.py")
# The functions each Edition file offers the shared files, and the dev tools and tests
# (example_database_cannot_run), with their parameters: both Editions' copies have exactly
# these. Either may have more of its own.
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
# The sqlglot whose layout Spark Composer's writing.py copies, which
# tests/repo/test_edition_parity.py holds equal to the sqlglot pin in requirements-dev.txt.
LAYOUT_MIRRORS_SQLGLOT = "30.19.0"


@dataclass(frozen=True)
class Difference:
    """One place the two Editions differ on purpose: in the Hive they write, or in a refusal.

    `why` says it in plain words, for the README. `sqlglot_composer` and `spark_composer` are
    the same piece of what each Edition shows, its Hive or its refusal, as the golden corpus
    shows it in one of `cases`, the ids of the golden cases the difference explains.
    `spark_composer_adds` is True for text Spark Composer adds to sqlglot Composer's Hive, which
    its readable_text leaves out. tests/repo/test_edition_parity.py holds that the two goldens
    differ in no other case, that each listed case really differs, and that with what Spark
    Composer adds left out, a case differs only if a row that adds nothing lists it. `title`
    names what differs, for the README's list.
    """

    title: str
    why: str
    sqlglot_composer: str
    spark_composer: str
    cases: tuple[str, ...]
    spark_composer_adds: bool = False


# Each place the two Editions differ on purpose.
DECLARED_DIFFERENCES = {
    "division": Difference(
        title="Dividing by something that could be 0.",
        why="With ANSI mode on (Spark's setting for following the SQL standard strictly), Spark "
        "4's default, Spark stops the whole query with an error when it divides by 0, where Hive "
        "gives NULL. So Spark Composer writes x / y as x / NULLIF(y, 0): NULLIF(y, 0) is NULL "
        "when y is 0, so that row gets NULL, as in Hive. A divisor that is a number other than 0 "
        "is written as it is.",
        sqlglot_composer="SUM(job_runs.duration_mins) / COUNT(*)",
        spark_composer="SUM(job_runs.duration_mins) / NULLIF(COUNT(*), 0)",
        cases=("edge:brackets:nested", "edge:brackets:aggregates",
               "worked:labels_and_counts:failed_share_per_job"),
        spark_composer_adds=True,
    ),
    "float": Difference(
        title="A Python float.",
        why="Spark reads a number such as 0.5 as a DECIMAL, an exact decimal that pandas gets as "
        "a Decimal, where Hive reads a DOUBLE, SQL's float. So Spark Composer writes a Python "
        "float, such as 0.5, as 0.5D: the D marks a DOUBLE, and doesn't mean days. A very small "
        "or very large float, which the Toolbox writes with an e, such as 1e-05, is a DOUBLE "
        "already.",
        sqlglot_composer="COALESCE(job_runs.avg_retry_secs, 0.1)",
        spark_composer="COALESCE(job_runs.avg_retry_secs, 0.1D)",
        cases=("worked:nan_in_a_list:fixed", "edge:calculations:values",
               "worked:labels_and_counts:failed_share_per_job"),
        spark_composer_adds=True,
    ),
    "hive_function": Difference(
        title="A hive_function call.",
        why="sqlglot Composer writes a hive_function call as sqlglot reads it back: sometimes by "
        "another name that does the same, such as COALESCE for nvl, and sometimes with an "
        "argument changed, such as a date_format pattern 'YYYY-MM' written 'yyyy-MM'. Spark "
        "Composer writes the call as you gave it, its name in capitals. So write 'yyyy' for the "
        "year in a date_format pattern: YYYY is the year a week belongs to, which Spark refuses "
        "in a pattern. And hive_function counts the arguments of the functions on its own list "
        "in both Editions; for any other function, sqlglot Composer refuses a call sqlglot can't "
        "build, and Spark Composer writes it, for Spark to refuse when it runs, as it does nvl2 "
        "with 1 argument, or to run, as it does unix_timestamp with none.",
        sqlglot_composer="COALESCE(job_runs.status, 'none')",
        spark_composer="NVL(job_runs.status, 'none')",
        cases=("edge:hive_function:nvl", "edge:hive_function:nvl2",
               "edge:hive_function:regexp_extract", "edge:hive_function:date_format",
               "edge:hive_function:substr", "edge:hive_function:instr"),
    ),
}


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


# --- Naming the other Edition -----------------------------------------------------------------


class SwapRefused(ValueError):
    """Text couldn't be made to name the other Edition with certainty."""


# Any spelling of either Edition's folder or product name.
SQLGLOT_COMPOSER_NAME = re.compile(r"sqlglot[\W_]*composer", re.IGNORECASE)
# sqlglot Composer's name before 4.0, as SQL Composer or sql_composer.
OLD_NAME = re.compile(r"(?<![A-Za-z])sql[\W_]*composer", re.IGNORECASE)
SPARK_COMPOSER_NAME = re.compile(r"spark[\W_]*composer", re.IGNORECASE)
# The libraries the Composer core may not name, since only one Edition has each.
LIBRARIES = ("sqlglot", "pyspark")


def libraries_named(text: str) -> list[str]:
    """Which Edition's library a Composer core file names, other than in the name of sqlglot
    Composer, which the core's docstrings use."""
    return [word for word in LIBRARIES
            if re.search(rf"{word}(?![_ ]composer)", text, re.IGNORECASE)]


def named_for(edition: Edition, text: str, where: str = "The text") -> str:
    """Text written for sqlglot Composer, such as a Worked example, naming `edition` instead.

    Text that would still name sqlglot Composer another way, as sqlglot-Composer, is refused,
    and so is its name from before 4.0, SQL Composer, which the swap would leave as it is.
    """
    swapped = _whole_word(SQLGLOT_COMPOSER.folder).sub(edition.folder, text)
    swapped = _whole_word(SQLGLOT_COMPOSER.product).sub(edition.product, swapped)
    left = sorted(set(OLD_NAME.findall(swapped)))
    if edition is not SQLGLOT_COMPOSER:
        left += sorted(set(SQLGLOT_COMPOSER_NAME.findall(swapped)))
    if left:
        raise SwapRefused(f"{where} would be left naming {', '.join(left)}.")
    return swapped


def _whole_word(name: str) -> re.Pattern:
    return re.compile(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])")


# --- Running the same tests and tools against Spark Composer ------------------------------------


class _OnlyTheAlias(importlib.abc.MetaPathFinder):
    """Refuses any `sqlglot_composer.*` module the alias doesn't hold, rather than load the real
    one."""

    def find_spec(self, fullname, path, target=None):
        if _in_sqlglot_composer(fullname):
            raise ImportError(f"{fullname} isn't part of the Spark run's alias: only Spark "
                              "Composer's own modules stand in for sqlglot Composer's.")
        return None


def use(edition: Edition) -> None:
    """Make `import sqlglot_composer` give `edition`'s folder, and make sqlglot unimportable.

    The shared tests and the Worked examples say `from sqlglot_composer import ...`; in Spark
    Composer's run that is Spark Composer's folder, and its own writing.py and engine.py stand
    in for sqlglot Composer's. The Composer core is the same for both, so it needs no alias. It
    must run before anything imports sqlglot_composer. For sqlglot Composer it does nothing.
    """
    if edition is SQLGLOT_COMPOSER:
        return
    if any(_in_sqlglot_composer(name) for name in sys.modules):
        raise RuntimeError("editions.use: sqlglot_composer is already imported, so the run would "
                           "mix the two Editions. Choose the Edition before any Toolbox import.")
    sys.modules["sqlglot"] = None  # any `import sqlglot` now fails loudly
    for module in toolbox_modules():
        own = edition.folder + module.removeprefix("sqlglot_composer")
        sys.modules[module] = importlib.import_module(own)
    sys.meta_path.insert(0, _OnlyTheAlias())


def _in_sqlglot_composer(module: str) -> bool:
    return module == "sqlglot_composer" or module.startswith("sqlglot_composer.")


def toolbox_modules() -> list[str]:
    """The name of every module of an Edition's folder, as `sqlglot_composer` and its files."""
    return ["sqlglot_composer"] + [f"sqlglot_composer.{name.removesuffix('.py')}"
                                   for name in EDITION_FILES if name != "__init__.py"]


def edition_on_command_line(arguments: list[str]) -> Edition:
    """The Edition a tool's command line asks for: --edition sqlglot, the default, or spark."""
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--edition", choices=sorted(BY_OPTION), default=SQLGLOT_COMPOSER.option)
    known, _ = parser.parse_known_args(arguments[1:])
    return BY_OPTION[known.edition]
