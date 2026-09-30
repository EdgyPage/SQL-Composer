"""The test setup every Toolbox test shares.

The tests run against one Edition of the Toolbox, chosen with `--edition`: `sqlglot` for SQL
Composer, the default, or `spark` for Spark Composer. Nothing here imports the Toolbox or sqlglot
when the file is loaded, so the Edition is chosen before any Toolbox module is. In Spark
Composer's run, `import sql_composer` gives Spark Composer's modules and sqlglot can't be imported
at all (`editions.use`), so the same tests run unchanged. Each run names its Edition at the end,
so a run of the wrong one can't pass unnoticed.

Today is pinned to 2026-09-25, the day after the Example database's last day, so
`last_n_days(job_runs.dt, 2)` covers both of its days and every emitted date is fixed. The
load limits are switched off again after each test, since `set_load_limits` changes them for
the whole session.

Each run collects the shared tests directly in `tests/` and its own Edition's folder,
`tests/sqlglot_edition/` or `tests/spark_edition/`; SQL Composer's run also collects the repo's own
checks in `tests/repo/`, which run once.

A test marked `needs_example_database` runs a query on the Example database, and skips where it
can't, saying why. `--example-database required` turns that skip into a failure, for a CI job
whose Example database must run.
"""

from __future__ import annotations

import datetime
import html
import importlib
import re
from pathlib import Path
from types import ModuleType

import pandas as pd
import pytest

import editions

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"
TODAY = datetime.date(2026, 9, 25)
# The repo's own checks, run once, in SQL Composer's run.
REPO_FOLDER = "repo"
# What this run was given: its Edition, and whether its Example database must run.
_chosen: dict = {}


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--edition", choices=sorted(editions.BY_OPTION),
                     default=editions.SQL_COMPOSER.option,
                     help="the Edition of the Toolbox to test: sqlglot for SQL Composer, "
                     "spark for Spark Composer")
    parser.addoption("--example-database", choices=["optional", "required"], default="optional",
                     help="required: a test that needs the Example database fails where it "
                     "can't run a query, instead of skipping")


def pytest_configure(config: pytest.Config) -> None:
    _chosen["edition"] = editions.BY_OPTION[config.getoption("--edition")]
    _chosen["example_database"] = config.getoption("--example-database")
    editions.use(_chosen["edition"])


def folders_left_out(config: pytest.Config) -> set[str]:
    """The folders of tests this run doesn't collect: the other Edition's, and the repo's."""
    chosen = config.getoption("--edition")
    left_out = {edition.tests_folder for option, edition in editions.BY_OPTION.items()
                if option != chosen}
    if chosen != "sqlglot":
        left_out.add(REPO_FOLDER)
    return left_out


def pytest_ignore_collect(collection_path: Path, config: pytest.Config) -> bool | None:
    if collection_path.parent == TESTS and collection_path.name in folders_left_out(config):
        return True
    return None


def pytest_collection_modifyitems(config: pytest.Config, items: list) -> None:
    """Stop a run given a folder its Edition doesn't collect, rather than run the wrong one."""
    named = sorted({item.path.parent.name for item in items
                    if item.path.parent.parent == TESTS
                    and item.path.parent.name in folders_left_out(config)})
    if named:
        raise pytest.UsageError(f"tests/{named[0]}/ doesn't run with --edition "
                                f"{config.getoption('--edition')}.")


def pytest_report_header(config: pytest.Config) -> str:
    return f"Edition: {edition().product} ({edition().folder}/)"


def pytest_terminal_summary(terminalreporter) -> None:
    terminalreporter.write_line(f"Edition tested: {edition().product} ({edition().folder}/)")


def edition() -> editions.Edition:
    """The Edition these tests run against."""
    return _chosen["edition"]


def in_this_edition(sql_composer, spark_composer):
    """What a test expects where the two Editions write different Hive on purpose.

    Each such place is one of `DECLARED_DIFFERENCES` in `tools/editions.py`.
    """
    return spark_composer if edition() is editions.SPARK_COMPOSER else sql_composer


def toolbox_folder() -> Path:
    """The folder of the Edition these tests run against."""
    return ROOT / edition().folder


def toolbox_module(name: str = "") -> ModuleType:
    """The Edition's folder, imported, or one of its files by name, such as "conditions"."""
    return importlib.import_module(f"{edition().folder}.{name}" if name else edition().folder)


def example_database_cannot_run() -> str | None:
    """Why the Example database can't run a query here, or None when it can: its Edition says."""
    return toolbox_module("engine").example_database_cannot_run()


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
    check doesn't rely on the send it checks.
    """
    reference, rows = toolbox_module("example_database")._TABLES[table]
    return pd.DataFrame(rows, columns=list(reference._columns))


def import_stop(what: str, why: str, fix: str) -> str:
    """The last line of the Edition's import stop: the four parts, with no opt-out."""
    return (
        f"ImportError: {edition().folder} stopped on import:"
        f"\n  What happened:  {what}"
        f"\n  Why it matters: {why}"
        f"\n  Usual fix:      {fix}"
        "\n  Opt-out:        none - this one can't be switched off."
    )


def page_text(html_text: str) -> str:
    """What a reader sees: the tags taken out, entities read, and runs of spaces made one."""
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html_text, flags=re.DOTALL)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", text)).split())


def gallery_entries() -> dict[str, tuple[str, str]]:
    """Each entry on the Edition's Example gallery, by its id: its title and all its text."""
    found = re.findall(r'<section class="entry" id="([^"]+)">(.*?)</section>',
                       (toolbox_folder() / "examples.html").read_text(encoding="utf-8"),
                       re.DOTALL)
    return {
        entry_id: (page_text(re.search(r"<h3>(.*?)</h3>", body, re.DOTALL).group(1)),
                   page_text(body))
        for entry_id, body in found
    }


@pytest.fixture(autouse=True)
def skip_without_the_example_database(request: pytest.FixtureRequest) -> None:
    if request.node.get_closest_marker("needs_example_database"):
        skip_unless_the_example_database_runs()


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(toolbox_module("conditions"), "today", lambda: TODAY)


@pytest.fixture(autouse=True)
def no_load_limits():
    yield
    toolbox_module().set_load_limits()
