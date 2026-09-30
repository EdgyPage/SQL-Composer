"""The two Editions, as `tools/editions.py` defines them for every tool and test on `dev`.

The registry is the one place that says which Editions exist, which files each folder holds and
what each file may import, and `swap()` is how SQL Composer's shared files become Spark
Composer's. A swap that can't be sure it changed every name, and nothing else, refuses.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

import editions
from editions import SPARK_COMPOSER, SQL_COMPOSER, SwapRefused, may_import, swap

ROOT = Path(__file__).resolve().parents[2]


def test_each_edition_has_its_folder_product_and_library() -> None:
    assert list(editions.EDITIONS) == ["sql_composer", "spark_composer"]
    assert (SQL_COMPOSER.product, SQL_COMPOSER.library) == ("SQL Composer", "sqlglot")
    assert (SPARK_COMPOSER.product, SPARK_COMPOSER.library) == ("Spark Composer", "pyspark")
    assert editions.EXPORTED == (SQL_COMPOSER, SPARK_COMPOSER)


def test_every_file_in_the_sql_composer_folder_is_classified() -> None:
    classified = set(editions.SHARED_FILES + editions.EDITION_FILES + editions.VERBATIM_FILES
                     + editions.PAGES)
    present = {path.name for path in (ROOT / "sql_composer").iterdir()
               if path.name != "__pycache__"}
    assert present - classified == set()


def test_a_shared_file_swaps_both_names() -> None:
    text = '"""SQL Composer: see sql_composer.refusals."""\nfrom sql_composer import run\n'
    assert swap(text, "running.py") == (
        '"""Spark Composer: see spark_composer.refusals."""\nfrom spark_composer import run\n'
    )


def test_a_copy_is_never_swapped_again() -> None:
    copy = swap("import sql_composer  # SQL Composer\n", "tables.py")
    with pytest.raises(SwapRefused, match="only one Edition"):
        swap(copy, "tables.py")


@pytest.mark.parametrize("text", [
    "# see SQL-Composer on GitHub\n",
    "import sql_composer_x\n",
    "# two SQL Composers\n",
    "# sqlcomposer\n",
    "# SQL - Composer\n",
])
def test_a_name_the_swap_cant_be_sure_of_is_refused(text: str) -> None:
    with pytest.raises(SwapRefused, match="left"):
        swap(text, "tables.py")


@pytest.mark.parametrize("text", ["# written by sqlglot\n", "# unlike Spark Composer\n"])
def test_a_shared_file_naming_what_only_one_edition_has_is_refused(text: str) -> None:
    with pytest.raises(SwapRefused, match="only one Edition"):
        swap(text, "tables.py")


def test_a_python_file_that_wont_parse_after_the_swap_is_refused() -> None:
    with pytest.raises(SwapRefused, match="parse"):
        swap("def (\n", "tables.py")


def test_a_file_that_isnt_shared_is_refused() -> None:
    with pytest.raises(SwapRefused, match="writing.py"):
        swap("x = 1\n", "writing.py")
    with pytest.raises(SwapRefused, match="notes.txt"):
        swap("x\n", "notes.txt")


def test_a_verbatim_file_is_copied_unchanged_but_may_not_name_an_edition() -> None:
    assert swap("## 2.1\n\n- Plain words.\n", "CHANGES.md") == "## 2.1\n\n- Plain words.\n"
    with pytest.raises(SwapRefused, match="neither Edition.*sql_composer"):
        swap("Copy the sql_composer folder.\n", "CHANGES.md")
    with pytest.raises(SwapRefused, match="neither Edition.*Spark Composer"):
        swap("New in Spark Composer.\n", "CHANGES.md")


def test_the_alias_refuses_once_sql_composer_is_imported() -> None:
    import sql_composer  # noqa: F401 - this run has already imported it

    before = dict(sys.modules)
    with pytest.raises(RuntimeError, match="sql_composer is already imported"):
        editions.use(SPARK_COMPOSER)
    assert sys.modules == before


@pytest.mark.parametrize(("arguments", "folder"), [
    (["tool.py"], "sql_composer"),
    (["tool.py", "--edition", "spark"], "spark_composer"),
    (["tool.py", "--edition=spark"], "spark_composer"),
    (["tool.py", "--edition", "sqlglot"], "sql_composer"),
])
def test_a_tool_takes_its_edition_from_its_command_line(arguments, folder) -> None:
    assert editions.edition_on_command_line(arguments).folder == folder


def test_a_tool_refuses_an_edition_it_doesnt_know() -> None:
    with pytest.raises(SystemExit):
        editions.edition_on_command_line(["tool.py", "--edition", "hive"])


def test_what_each_file_may_import() -> None:
    assert may_import(SPARK_COMPOSER, "tables.py") == {"pandas", "numpy"}
    assert may_import(SPARK_COMPOSER, "writing.py") == set()
    assert may_import(SPARK_COMPOSER, "engine.py") == {"pandas", "numpy", "pyspark"}
    assert may_import(SQL_COMPOSER, "writing.py") == {"pandas", "numpy", "sqlglot"}
    assert may_import(SQL_COMPOSER, "engine.py") == {"pandas", "numpy", "sqlglot"}
    assert may_import(SQL_COMPOSER, "refusals.py") == {"pandas", "numpy"}


def test_no_shared_file_may_import_either_library() -> None:
    for edition in (SQL_COMPOSER, SPARK_COMPOSER):
        for name in editions.SHARED_FILES:
            assert may_import(edition, name) == {"pandas", "numpy"}


def test_an_import_a_file_may_not_make_is_listed(tmp_path: Path) -> None:
    folder = tmp_path / "spark_composer"
    folder.mkdir()
    (folder / "writing.py").write_text("import re\nimport pandas\nfrom . import trees\n")
    (folder / "tables.py").write_text("import numpy\nimport sqlglot.exp\n")
    assert editions.imports_outside(folder) == ["tables.py imports sqlglot.exp",
                                                "writing.py imports pandas"]


def test_no_canonical_shared_file_names_what_only_one_edition_has() -> None:
    found = {name: editions.forbidden_words((ROOT / "sql_composer" / name).read_text("utf-8"))
             for name in editions.SHARED_FILES}
    assert {name: words for name, words in found.items() if words} == {}
