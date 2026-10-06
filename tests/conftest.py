"""The test setup every Toolbox test shares.

The tests run against one Edition of the Toolbox, chosen with `--edition`: `sqlglot` for sqlglot
Composer, the default, or `spark` for Spark Composer. Nothing here imports the Toolbox or
sqlglot when the file is loaded, so the Edition is chosen before any Toolbox module is. In Spark
Composer's run, `import sqlglot_composer` gives Spark Composer's modules and sqlglot can't be
imported at all (`editions.use`), so the same tests run unchanged. Each run names its Edition at
the end, so a run of the wrong one can't pass unnoticed.

Today is pinned to 2026-09-25, the day after the Example database's last day, so
`last_n_days(job_runs.dt, 2)` covers both of its days and every emitted date is fixed. The
load limits are switched off again after each test, since `set_load_limits` changes them for
the whole session.

Each run collects the shared tests directly in `tests/` and its own Edition's folder,
`tests/sqlglot_edition/` or `tests/spark_edition/`; sqlglot Composer's run also collects the
repo's own checks in `tests/repo/`, which run once.

A test marked `needs_example_database` runs a query on the Example database. Where this computer
can't run one, because something it needs is missing or its Spark couldn't start, the test
skips, saying why; whether it can is asked once a run, by sending it one query. Anything else
that stops that query is a bug, and fails the test. `--example-database required` turns every
such skip into a failure too, for a CI job whose Example database must run.
"""

from __future__ import annotations

import contextlib
import datetime
import html
import importlib
import inspect
import re
import sys
from pathlib import Path
from types import ModuleType

import pandas as pd
import pytest

import editions

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"
TODAY = datetime.date(2026, 9, 25)
# The repo's own checks, run once, in sqlglot Composer's run.
REPO_FOLDER = "repo"
# What this run was given: its Edition, and whether its Example database must run.
_chosen: dict = {}


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption("--edition", choices=sorted(editions.BY_OPTION),
                     default=editions.SQLGLOT_COMPOSER.option,
                     help="the Edition of the Toolbox to test: sqlglot for sqlglot Composer, "
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


def in_this_edition(sqlglot_composer, spark_composer):
    """What a test expects where the two Editions write different Hive on purpose.

    Each such place is one of `DECLARED_DIFFERENCES` in `tools/editions.py`.
    """
    return spark_composer if edition() is editions.SPARK_COMPOSER else sqlglot_composer


def toolbox_folder() -> Path:
    """The folder of the Edition these tests run against."""
    return ROOT / edition().folder


def toolbox_module(name: str = "") -> ModuleType:
    """The Edition's folder, imported, or one of the Toolbox's files by name, such as
    "conditions": the Edition's own writing or engine, or else the Composer core's."""
    if not name:
        return importlib.import_module(edition().folder)
    toolbox_module()  # the Edition is imported first, so its files are plugged in
    if f"{name}.py" in editions.EDITION_FILES:
        return importlib.import_module(f"{edition().folder}.{name}")
    return importlib.import_module(f"{editions.CORE}.{name}")


# Whether the Example database answered the one query each run sends it, and if not, why.
_ANSWERED: dict = {}
# What an Example database whose Spark couldn't start says: that is about this computer, so its
# tests are skipped. Anything else the one query raises is a bug, and fails them.
_DIDNT_START = ("quit while it was starting", "didn't start within")


def example_database_cannot_run() -> str | None:
    """Why the Example database can't run a query here, or None when it can.

    Its Edition says what it lacks. Then, once a run, it is sent one query, so an Example
    database that can't answer, such as a Spark that can't start, gives every test one reason
    rather than each test a wait of its own. Whether that reason is a bug is kept too.
    """
    reason = toolbox_module("engine").example_database_cannot_run()
    if reason is not None:
        return reason
    if "reason" not in _ANSWERED:
        try:
            toolbox_module("example_database").send("SELECT job_id FROM ops.jobs")
            _ANSWERED["reason"] = None
        except RuntimeError as error:
            said = re.search(r"What happened:\s*(.+)", str(error))
            _ANSWERED["reason"] = ("the Example database didn't answer: "
                                   + (said.group(1) if said else str(error).strip()))
            _ANSWERED["bug"] = not any(phrase in str(error) for phrase in _DIDNT_START)
    return _ANSWERED["reason"]


def skip_unless_the_example_database_runs() -> None:
    """Skip the test where the Example database can't run a query, or fail if that's a bug.

    Where it is required, as in CI, it fails whatever the reason.
    """
    reason = example_database_cannot_run()
    if reason is None:
        return
    if _chosen["example_database"] == "required":
        pytest.fail(f"--example-database required, but {reason}")
    if _ANSWERED.get("bug"):
        pytest.fail(reason)
    pytest.skip(reason)


def example_rows(table: str) -> pd.DataFrame:
    """One Example database table as a DataFrame, for the Worked examples' pandas checks.

    It reads the rows the Example database holds directly, not through its send, so a pandas
    check doesn't rely on the send it checks.
    """
    reference, rows = toolbox_module("example_database")._TABLES[table]
    return pd.DataFrame(rows, columns=list(reference._columns))


@contextlib.contextmanager
def project_on_the_path(folder: Path, top_names: tuple[str, ...]):
    """Import a project's scripts as a notebook started in `folder` does, by their own folder
    names, such as table_references.

    The Worked examples have folders of the same names, so any module of those names is put
    away first, `folder` goes first on the path, and afterwards the project's modules are put
    away and the others put back.
    """
    def is_the_projects(module: str) -> bool:
        return module.split(".")[0] in top_names

    put_away = {name: sys.modules.pop(name) for name in list(sys.modules)
                if is_the_projects(name)}
    sys.path.insert(0, str(folder))
    try:
        yield
    finally:
        sys.path.remove(str(folder))
        for name in [name for name in sys.modules if is_the_projects(name)]:
            del sys.modules[name]
        sys.modules.update(put_away)


# The line a write's Hive starts with, before the SELECT it saves.
INSERT = "INSERT OVERWRITE TABLE"


def without_the_write(hive: str) -> str:
    """A write's Hive with its INSERT OVERWRITE line left out: the SELECT it saves."""
    return "\n".join(line for line in hive.splitlines() if not line.startswith(INSERT))


def value_as_hive(x) -> str:
    if x is None or (isinstance(x, float) and pd.isna(x)):
        return "NULL"
    return f"'{x}'" if isinstance(x, str) else str(int(x))


def standing_in(hive: str, saved: dict[str, pd.DataFrame]) -> str:
    """The Hive with each Saved table, by its name in mart., stood in for by rows, each row
    holding its own day as dt, for a Statement that reads a Saved table only a warehouse
    holds."""
    for table, rows in saved.items():
        selects = [", ".join(f"{value_as_hive(x)} AS {column}"
                             for column, x in zip(rows.columns, row))
                   for row in rows.itertuples(index=False)]
        assert selects, f"mart.{table} standing in with no rows"
        named = f"mart.{table} AS {table}"
        assert hive.count(named) == 1, table
        union = " UNION ALL ".join(f"SELECT {select}" for select in selects)
        hive = hive.replace(named, f"({union}) AS {table}")
    return hive


# --- Example projects and Templates ------------------------------------------------------------

TEMPLATES = ROOT / "templates"
# A Template's "Copy it to:" line: the place in the user's project it is copied to.
COPY_IT_TO = re.compile(r"^Copy it to: (\S+\.py)", re.MULTILINE)
# A Template's placeholder, such as <TABLE>: the name in the brackets is its group.
PLACEHOLDER = re.compile(r"<([A-Z][A-Z0-9_]*)>")


def template_id(path: Path) -> str:
    """A Template by its set and file name, such as "starter/saved_table.py"."""
    return f"{path.parent.name}/{path.name}"


def statements_in(result) -> list:
    """The Statements a function gives: one, a list or a dict of them, or a Building block's
    Derived table, read whole by a Statement."""
    toolbox = toolbox_module()
    statement_type = toolbox_module("clauses").Statement
    values = (result.values() if isinstance(result, dict)
              else result if isinstance(result, list) else [result])
    found = []
    for value in values:
        if isinstance(value, statement_type):
            found.append(value)
        elif isinstance(value, toolbox.Table) and value._statement is not None:
            found.append(toolbox.statement(toolbox.SELECT(toolbox.all_columns(value)),
                                           toolbox.FROM(value)))
    return found


def functions_given(module, given: dict) -> dict[str, list]:
    """Each function the module defines whose parameters `given` names, by name, with the
    Statements it gives when they are given those values. A function with a parameter `given`
    doesn't name, such as column_name(column), is left out, and so is one that gives no
    Statement."""
    found = {}
    for name, function in vars(module).items():
        if not inspect.isfunction(function) or function.__module__ != module.__name__:
            continue
        parameters = inspect.signature(function).parameters
        if not set(parameters) <= set(given):
            continue
        built = statements_in(function(**{parameter: given[parameter]
                                          for parameter in parameters}))
        if built:
            found[name] = built
    return found


def is_a_select_on_the_example_database(s) -> bool:
    """Whether the Example database can run a Statement: a SELECT, not a create or a write,
    reading only the Example database's tables, which are all in ops., and so no Saved table,
    which only a warehouse holds."""
    hive = toolbox_module().to_hive(s)
    if hive.startswith("CREATE") or INSERT in hive:
        return False
    read = re.findall(r"\b(?:FROM|JOIN) (\w+)\.\w+", hive)
    return all(database == "ops" for database in read)


def every_day(first_day: str, last_day: str) -> list[str]:
    """Each day from first_day to last_day, both included, written like "2026-09-24"."""
    first = datetime.date.fromisoformat(first_day)
    days = (datetime.date.fromisoformat(last_day) - first).days
    return [(first + datetime.timedelta(days=n)).isoformat() for n in range(days + 1)]


def previewed_days(module, days) -> pd.DataFrame:
    """What the module's preview shows for each of the days on the Example database, with the
    day as dt: the rows a Saved table its write fills would hold."""
    toolbox = toolbox_module()
    return pd.concat([toolbox.run(module.preview(day), send=toolbox.example_database.send)
                      .assign(dt=day) for day in days], ignore_index=True)


def import_stop(what: str, why: str, fix: str, folder: str | None = None) -> str:
    """The last line of an import stop: the four parts, with no opt-out. It names the Edition's
    folder, or `folder`, such as composer_core, when that is the one that stopped."""
    return (
        f"ImportError: {folder or edition().folder} stopped on import:"
        f"\n  What happened:  {what}"
        f"\n  Why it matters: {why}"
        f"\n  Usual fix:      {fix}"
        "\n  Opt-out:        none - this one can't be switched off."
    )


def page_text(html_text: str) -> str:
    """What a reader sees: the tags taken out, entities read, and runs of spaces made one."""
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html_text, flags=re.DOTALL)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", text)).split())


def gallery_sections(folder: Path) -> dict[str, str]:
    """Each entry on the Example gallery in an Edition's folder, by its id: its HTML."""
    page = (folder / "examples.html").read_text(encoding="utf-8")
    return dict(re.findall(r'<section class="entry" id="([^"]+)">(.*?)</section>', page,
                           re.DOTALL))


def gallery_entries() -> dict[str, tuple[str, str]]:
    """Each entry on the Edition's Example gallery, by its id: its title and all its text."""
    return {
        entry_id: (page_text(re.search(r"<h3>(.*?)</h3>", body, re.DOTALL).group(1)),
                   page_text(body))
        for entry_id, body in gallery_sections(toolbox_folder()).items()
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
