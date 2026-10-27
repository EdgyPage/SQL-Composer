"""The test setup every Toolbox test shares.

The tests run against the Toolbox, sqlglot Composer.

Today is pinned to 2026-09-25, the day after the Example database's last day, so
`last_n_days(job_runs.dt, 2)` covers both of its days and every emitted date is fixed. The
load limits are switched off again after each test, since `set_load_limits` changes them for
the whole session.

A run collects the shared tests directly in `tests/`, sqlglot Composer's own in
`tests/sqlglot_checks/`, and the repo's own checks in `tests/repo/`.

Every test runs under the offline trap, `offline_trap`, installed as this file loads: its Python
refuses any lookup or connection that would leave this computer.

No Python of the run, this one or one it starts, writes a `.pyc`. The code audit reads the
Toolbox's folder and the other folders that ship, `__pycache__` included, and a how-to's folder
would list a `__pycache__` its page doesn't show. Some computers set this already, and CI's
doesn't.
"""

from __future__ import annotations

import contextlib
import datetime
import html
import importlib
import inspect
import os
import re
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType
from typing import TYPE_CHECKING

import pandas as pd
import pytest

import toolbox_registry as registry
import offline_trap

# Only the hints name these: the Toolbox is imported through toolbox_module(), after the
# offline trap is in place, so its import self-check runs in its turn.
if TYPE_CHECKING:
    from sqlglot_composer.clauses import Statement
    from sqlglot_composer.project import TableLogic

# Every test, and every library a test calls, reaches nothing off this computer.
offline_trap.install()
# No .pyc, here or in a Python a test starts.
sys.dont_write_bytecode = True
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"

ROOT = Path(__file__).resolve().parent.parent
TESTS = ROOT / "tests"
TODAY = datetime.date(2026, 9, 25)
# The repo's own checks.
REPO_FOLDER = "repo"


# The Toolbox's folder and what its messages call it.
FOLDER, PRODUCT = registry.FOLDER, registry.PRODUCT


def toolbox_folder() -> Path:
    """The Toolbox's folder."""
    return ROOT / FOLDER


def toolbox_module(name: str = "") -> ModuleType:
    """The Toolbox's folder, imported, or one of its files by name, such as "conditions"."""
    if not name:
        return importlib.import_module(FOLDER)
    toolbox_module()  # the folder is imported first, so its import self-check runs first
    return importlib.import_module(f"{FOLDER}.{name}")


def example_rows(table: str) -> pd.DataFrame:
    """One Example database table as a DataFrame, for the Worked examples' pandas checks.

    It reads the rows the Example database holds directly, not through its query, so a pandas
    check doesn't rely on the query it checks.
    """
    reference, rows = toolbox_module("example_database")._TABLES[table]
    return pd.DataFrame(rows, columns=list(reference._columns))


@contextlib.contextmanager
def project_on_the_path(folder: Path, top_names: tuple[str, ...]) -> Iterator[None]:
    """Import a project's scripts as a notebook started in `folder` does, by their own folder
    names, such as references.

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


# The module an admin notebook's code cells are written into, to be run as Jupyter runs them.
NOTEBOOK_CELLS = "admin_notebook_cells"


def run_admin_notebook(notebook: Path, cells: list[str] | None = None,
                       capsys: pytest.CaptureFixture[str] | None = None) -> str:
    """Run an admin notebook's code cells, top to bottom, from its folder, admin/, as Jupyter
    runs them, and give back what they printed: `cells`, in their place, if given.

    The cells are written as one module beside the notebook's Project, in admin/, and
    imported: its first cell puts the Project on Python's path. Afterwards the path is as it
    was, and the Project's modules are put away, so another test can import its own.
    """
    if cells is None:
        cells = [text for kind, text in toolbox_module("notebooks").read_cells(notebook)
                 if kind == "code"]
    folder = notebook.parent
    (folder / f"{NOTEBOOK_CELLS}.py").write_text("\n\n".join(cells) + "\n", encoding="utf-8")
    with project_on_the_path(folder, ("references", "building_blocks", "warehouse",
                                      NOTEBOOK_CELLS)), contextlib.chdir(folder):
        path = list(sys.path)
        try:
            importlib.invalidate_caches()
            import admin_notebook_cells  # noqa: F401  runs the cells, in order
        finally:
            sys.path[:] = path
            (folder / f"{NOTEBOOK_CELLS}.py").unlink()
    return capsys.readouterr().out if capsys is not None else ""


# The line a write's Hive starts with, before the SELECT it saves.
INSERT = "INSERT OVERWRITE TABLE"


def without_the_write(hive: str) -> str:
    """A write's Hive with its INSERT OVERWRITE line left out: the SELECT it saves."""
    return "\n".join(line for line in hive.splitlines() if not line.startswith(INSERT))


def value_as_hive(x: object) -> str:
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



def statements_in(result: object) -> list[Statement]:
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


def functions_given(module: ModuleType, given: dict[str, object]) -> dict[str, list[Statement]]:
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


def is_a_select_on_the_example_database(s: Statement) -> bool:
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


def rows_of_days(module: TableLogic, first_day: str, last_day: str) -> Statement:
    """The SELECT the module's write would send for the days first_day to last_day: the
    clauses its rows() gives, which its preview() and write() share. A rows() that takes one
    day is given first_day; one that takes nothing reads its logic cell's DAY, which is set to
    first_day, the one day it writes, as a user changes it to write another."""
    toolbox = toolbox_module()
    parameters = inspect.signature(module.rows).parameters
    if not parameters:
        assert first_day == last_day, "a rows() that takes nothing writes one day"
        module.rows.__globals__["DAY"] = first_day
        return toolbox.statement(*module.rows())
    days = (first_day, last_day)[:len(parameters)]
    return toolbox.statement(*module.rows(*days))


def previewed_days(module: TableLogic, days: list[str]) -> pd.DataFrame:
    """What the module's rows() give for each of the days on the Example database, each row
    with its day as dt, the column it selects last: the rows a Saved table its write fills
    would hold."""
    toolbox = toolbox_module()
    return pd.concat([toolbox.run_query(rows_of_days(module, day, day),
                                        toolbox.example_database.query) for day in days],
                     ignore_index=True)


def import_stop(what: str, why: str, fix: str, folder: str | None = None) -> str:
    """The last line of an import stop: the four parts, with no opt-out. It names the Toolbox's
    folder, or `folder`, when that is the one that stopped."""
    return (
        f"ImportError: {folder or FOLDER} stopped on import:"
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
    """Each entry on the Example gallery in a Toolbox folder, by its id: its HTML."""
    page = (folder / "examples.html").read_text(encoding="utf-8")
    return dict(re.findall(r'<section class="entry" id="([^"]+)">(.*?)</section>', page,
                           re.DOTALL))


def gallery_entries() -> dict[str, tuple[str, str]]:
    """Each entry on the Example gallery, by its id: its title and all its text."""
    return {
        entry_id: (page_text(re.search(r"<h3>(.*?)</h3>", body, re.DOTALL).group(1)),
                   page_text(body))
        for entry_id, body in gallery_sections(toolbox_folder()).items()
    }


@pytest.fixture(autouse=True)
def fixed_today(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(toolbox_module("conditions"), "today", lambda: TODAY)


@pytest.fixture(autouse=True)
def no_load_limits() -> Iterator[None]:
    yield
    toolbox_module().set_load_limits()


@pytest.fixture(autouse=True)
def admin_log_where_it_starts(tmp_path_factory: pytest.TempPathFactory) -> Iterator[None]:
    """set_admin_log changes where the Admin log goes for the whole session, so each test
    starts with it in a folder of pytest's own, where an Admin statement a test runs logs
    without writing beside the tests, and ends with it beside the script or notebook that
    runs."""
    toolbox_module().set_admin_log(tmp_path_factory.mktemp("admin_log") / "admin_log.md")
    yield
    toolbox_module().set_admin_log()
