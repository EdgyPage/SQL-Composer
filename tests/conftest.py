"""The test setup every Toolbox test shares.

The tests run against one Edition of the Toolbox, chosen with `--edition`; for now SQL Composer
is the only choice, and the default. Nothing here imports the Toolbox or its library when the
file is loaded, so the Edition is chosen before any Toolbox module is.

Today is pinned to 2026-09-25, the day after the Example database's last day, so
`last_n_days(job_runs.dt, 2)` covers both of its days and every emitted date is fixed. The
load limits are switched off again after each test, since `set_load_limits` changes them for
the whole session.

A test marked `needs_example_database` runs a query on the Example database, and skips where it
can't, saying why. `--example-database required`, as CI passes it, turns that skip into a failure.
"""

from __future__ import annotations

import datetime
import importlib
import re
from pathlib import Path

import pandas as pd
import pytest

import editions

ROOT = Path(__file__).resolve().parent.parent
TODAY = datetime.date(2026, 9, 25)
EDITION_CHOICES = {"sqlglot": editions.SQL_COMPOSER}
_chosen = {"edition": editions.SQL_COMPOSER, "example_database": "optional"}


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--edition", choices=sorted(EDITION_CHOICES), default="sqlglot",
                     help="the Edition of the Toolbox to test")
    parser.addoption("--example-database", choices=["optional", "required"], default="optional",
                     help="required: a test that needs the Example database fails where it "
                     "can't run a query, instead of skipping")


def pytest_configure(config: pytest.Config) -> None:
    _chosen["edition"] = EDITION_CHOICES[config.getoption("--edition")]
    _chosen["example_database"] = config.getoption("--example-database")


def pytest_report_header(config: pytest.Config) -> str:
    return f"Edition: {edition().product} ({edition().folder}/)"


def edition() -> editions.Edition:
    """The Edition these tests run against."""
    return _chosen["edition"]


def toolbox_folder() -> Path:
    """The folder of the Edition these tests run against."""
    return ROOT / edition().folder


def toolbox_module(name: str = ""):
    """The Edition's package, or one of its files by name, such as "conditions"."""
    return importlib.import_module(f"{edition().folder}.{name}" if name else edition().folder)


def in_edition(text: str) -> str:
    """`text`, which names SQL Composer, as the Edition under test would say it."""
    return text


def example_database_cannot_run() -> str | None:
    """Why the Example database can't run a query here, or None when it can."""
    import sqlglot

    found = re.match(r"(\d+)\.(\d+)\.(\d+)", sqlglot.__version__)
    if (tuple(int(n) for n in found.groups()) if found else (0, 0, 0)) < (30, 19, 0):
        return "the Example database runs queries only on sqlglot 30.19.0 or newer"
    return None


def skip_unless_the_example_database_runs() -> None:
    """Skip the test where the Example database can't run a query, or fail if it's required."""
    reason = example_database_cannot_run()
    if reason is None:
        return
    if _chosen["example_database"] == "required":
        pytest.fail(f"--example-database required, but {reason}")
    pytest.skip(reason)


def example_rows(table: str) -> pd.DataFrame:
    """One Example database table as a DataFrame, for the Worked examples' pandas checks.

    It reads the rows the Example database holds directly, not through its send, so a pandas
    check doesn't rely on the engine it checks.
    """
    reference, rows = toolbox_module("example_database")._TABLES[table]
    return pd.DataFrame(rows, columns=list(reference._columns))


@pytest.fixture(autouse=True)
def needs_example_database(request: pytest.FixtureRequest) -> None:
    if request.node.get_closest_marker("needs_example_database"):
        skip_unless_the_example_database_runs()


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(toolbox_module("conditions"), "today", lambda: TODAY)


@pytest.fixture(autouse=True)
def no_load_limits():
    yield
    toolbox_module().set_load_limits()
