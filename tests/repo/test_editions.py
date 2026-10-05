"""The two Editions, as `tools/editions.py` defines them for every tool and test on `dev`.

The registry is the one place that says which Editions exist, which files the Composer core and
each Edition's folder hold, and what each file may import. `named_for()` makes text written for
sqlglot Composer, such as a Worked example, name Spark Composer instead; where it can't be sure
it changed every name, and nothing else, it refuses.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

import editions
from editions import SPARK_COMPOSER, SQLGLOT_COMPOSER, SwapRefused, may_import, named_for

ROOT = Path(__file__).resolve().parents[2]


def test_each_edition_has_its_folder_product_and_library() -> None:
    assert list(editions.EDITIONS) == ["sqlglot_composer", "spark_composer"]
    assert (SQLGLOT_COMPOSER.product, SQLGLOT_COMPOSER.library) == ("sqlglot Composer", "sqlglot")
    assert (SPARK_COMPOSER.product, SPARK_COMPOSER.library) == ("Spark Composer", "pyspark")
    assert editions.EXPORTED == (SQLGLOT_COMPOSER, SPARK_COMPOSER)


def test_every_file_in_each_toolbox_folder_is_classified() -> None:
    def present(folder: str) -> set[str]:
        return {path.name for path in (ROOT / folder).iterdir() if path.name != "__pycache__"}

    assert present(editions.CORE) - set(editions.CORE_FILES) == set()
    for edition in (SQLGLOT_COMPOSER, SPARK_COMPOSER):
        assert present(edition.folder) - set(editions.EDITION_FILES + editions.PAGES) == set()


def test_text_for_sqlglot_composer_is_named_for_spark_composer() -> None:
    text = '"""sqlglot Composer: see sqlglot_composer.run."""\nfrom sqlglot_composer import run\n'
    assert named_for(SPARK_COMPOSER, text) == (
        '"""Spark Composer: see spark_composer.run."""\nfrom spark_composer import run\n'
    )
    assert named_for(SQLGLOT_COMPOSER, text) == text


@pytest.mark.parametrize("text", [
    "# see sqlglot-Composer on GitHub\n",
    "import sqlglot_composer_x\n",
    "# two sqlglot Composers\n",
    "# sqlglotcomposer\n",
    "# sqlglot - Composer\n",
])
def test_a_name_the_swap_cant_be_sure_of_is_refused(text: str) -> None:
    with pytest.raises(SwapRefused, match="left"):
        named_for(SPARK_COMPOSER, text)


def test_the_alias_refuses_once_sqlglot_composer_is_imported() -> None:
    import sqlglot_composer  # noqa: F401 - this run has already imported it

    before = dict(sys.modules)
    with pytest.raises(RuntimeError, match="sqlglot_composer is already imported"):
        editions.use(SPARK_COMPOSER)
    assert sys.modules == before


@pytest.mark.parametrize(("arguments", "folder"), [
    (["tool.py"], "sqlglot_composer"),
    (["tool.py", "--edition", "spark"], "spark_composer"),
    (["tool.py", "--edition=spark"], "spark_composer"),
    (["tool.py", "--edition", "sqlglot"], "sqlglot_composer"),
])
def test_a_tool_takes_its_edition_from_its_command_line(arguments, folder) -> None:
    assert editions.edition_on_command_line(arguments).folder == folder


def test_a_tool_refuses_an_edition_it_doesnt_know() -> None:
    with pytest.raises(SystemExit):
        editions.edition_on_command_line(["tool.py", "--edition", "hive"])


def test_what_each_file_may_import() -> None:
    assert may_import(SPARK_COMPOSER, "writing.py") == {"composer_core"}
    assert may_import(SPARK_COMPOSER, "engine.py") == {"pandas", "numpy", "pyspark",
                                                        "composer_core"}
    assert may_import(SQLGLOT_COMPOSER, "writing.py") == {"pandas", "numpy", "sqlglot",
                                                      "composer_core"}
    assert may_import(SQLGLOT_COMPOSER, "engine.py") == {"pandas", "numpy", "sqlglot",
                                                     "composer_core"}
    assert may_import(SQLGLOT_COMPOSER, "__init__.py") == {"pandas", "numpy", "composer_core"}


def test_no_core_file_may_import_either_library_or_edition() -> None:
    for name in editions.CORE_FILES:
        assert may_import(None, name) == {"pandas", "numpy"}


def test_an_import_a_file_may_not_make_is_listed(tmp_path: Path) -> None:
    folder = tmp_path / "spark_composer"
    folder.mkdir()
    (folder / "writing.py").write_text("import re\nimport pandas\nfrom composer_core import trees\n")
    (folder / "engine.py").write_text("import numpy\nimport sqlglot.exp\n")
    assert editions.imports_outside(folder) == ["engine.py imports sqlglot.exp",
                                                "writing.py imports pandas"]
    core = tmp_path / "composer_core"
    core.mkdir()
    (core / "tables.py").write_text("import pandas\nimport spark_composer\nfrom . import trees\n")
    assert editions.imports_outside(core) == ["tables.py imports spark_composer"]


def test_no_core_file_names_either_library() -> None:
    found = {path.name: editions.libraries_named(path.read_text("utf-8"))
             for path in (ROOT / editions.CORE).glob("*.py")}
    assert {name: words for name, words in found.items() if words} == {}


def test_the_core_may_name_sqlglot_composer_but_not_sqlglot() -> None:
    assert editions.libraries_named("Write it with sqlglot_composer, as sqlglot Composer does.") == []
    assert editions.libraries_named("import sqlglot") == ["sqlglot"]
    assert editions.libraries_named("pyspark's DataFrame") == ["pyspark"]


@pytest.mark.parametrize("text", ["# from before 4.0, SQL Composer\n", "import sql_composer\n"])
def test_text_still_naming_the_name_from_before_4_0_is_refused(text: str) -> None:
    for edition in (SQLGLOT_COMPOSER, SPARK_COMPOSER):
        with pytest.raises(SwapRefused, match="left"):
            named_for(edition, text)
