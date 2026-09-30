"""The Spark run tests Spark Composer: `sql_composer` is its alias, and sqlglot can't be imported.

If the alias failed, the shared tests would quietly test SQL Composer again; these fail instead.
"""

from __future__ import annotations

import importlib

import pytest

import sql_composer
from conftest import edition


def test_sql_composer_is_spark_composer() -> None:
    assert edition().folder == "spark_composer"
    assert sql_composer.__name__ == "spark_composer"
    assert sql_composer.VERSION.startswith("Spark Composer ")
    assert importlib.import_module("sql_composer.writing").__name__ == "spark_composer.writing"


def test_sqlglot_cant_be_imported() -> None:
    with pytest.raises(ImportError):
        importlib.import_module("sqlglot")


def test_a_module_the_alias_doesnt_hold_is_refused() -> None:
    with pytest.raises(ImportError, match="isn't part of the Spark run's alias"):
        importlib.import_module("sql_composer.nowhere")
