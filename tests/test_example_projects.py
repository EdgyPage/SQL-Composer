"""The Example projects in `example_projects/`: generated files that are current, Statements
that build, SELECTs that run, and a README that names every file.

Each project is written again by `tools/example_project.py` into a temporary folder and
compared with the committed one, file by file, line endings aside. In Spark Composer's run it
is written for Spark Composer, and compared with the committed project named for it.

The project's scripts import their own folders, such as `table_references`, as a notebook
started in the project's folder does. The Worked examples have folders of the same names, so
the project's modules are imported with its folder first on the path, then put away again.
"""

from __future__ import annotations

import datetime
import importlib
import inspect
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest

import editions
import example_project
from conftest import ROOT, edition, example_rows, toolbox_module
from sqlglot_composer import example_database, run, to_hive

STARTER = ROOT / "example_projects" / "starter"
EXAMPLES = ("example_1_daily_job_runs", "example_2_alerts_per_job", "example_3_team_day")
# The steps each example offers, in the order they are sent.
STEPS = ("create", "preview", "write_day", "backfill")
DAYS = ("2026-09-23", "2026-09-24")
# What each step's day parameters are given, by name.
ARGUMENTS = {"day": DAYS[-1], "first_day": DAYS[0], "last_day": DAYS[-1]}
TOP_NAMES = ("table_references", "building_blocks", "statements", "run_pipeline")
INSERT = "INSERT OVERWRITE TABLE"


def _is_the_projects(module: str) -> bool:
    return module.split(".")[0] in TOP_NAMES


def _module_names(folder: Path) -> list[str]:
    """Each script of the project, as the module a notebook in its folder imports."""
    return [relative.removesuffix(".py").replace("/", ".")
            for relative in example_project.project_files(folder) if relative.endswith(".py")]


@pytest.fixture(scope="module")
def starter() -> dict:
    """The starter project's modules by name, such as "statements.example_1_daily_job_runs"."""
    put_away = {name: sys.modules.pop(name) for name in list(sys.modules)
                if _is_the_projects(name)}
    sys.path.insert(0, str(STARTER))
    try:
        yield {name: importlib.import_module(name) for name in _module_names(STARTER)}
    finally:
        sys.path.remove(str(STARTER))
        for name in [name for name in sys.modules if _is_the_projects(name)]:
            del sys.modules[name]
        sys.modules.update(put_away)


def example(starter: dict, name: str):
    return starter[f"statements.{name}"]


def statements_in(result) -> list:
    """The Statements a step returns: one, or a list such as by_day gives."""
    return result if isinstance(result, list) else [result]


def statement_functions(module) -> dict[str, list]:
    """Each function a script defines that returns Statements, by name, with what it returns
    when its day parameters are given the days in DAYS."""
    statement_type = toolbox_module("clauses").Statement
    found = {}
    for name, function in vars(module).items():
        if not callable(function) or getattr(function, "__module__", "") != module.__name__:
            continue
        given = {parameter: ARGUMENTS[parameter]
                 for parameter in inspect.signature(function).parameters}
        built = [s for s in statements_in(function(**given)) if isinstance(s, statement_type)]
        if built:
            found[name] = built
    return found


def without_the_write(hive: str) -> str:
    """A write's Hive with its INSERT OVERWRITE line left out: the SELECT it saves."""
    return "\n".join(line for line in hive.splitlines() if not line.startswith(INSERT))


# --- The generated files ---------------------------------------------------------------------


def write_project(into: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ROOT / "tools" / "example_project.py"), "--project", "starter",
         "--edition", edition().option, "--into", str(into)],
        capture_output=True, text=True, check=False,
    )


def test_the_committed_project_is_what_the_generator_writes(tmp_path: Path) -> None:
    into = tmp_path / "starter"
    written = write_project(into)
    assert written.returncode == 0, written.stderr
    committed = example_project.project_files(STARTER)
    assert example_project.project_files(into) == committed
    stale = [relative for relative in committed
             if (into / relative).read_text(encoding="utf-8")
             != editions.named_for(edition(), (STARTER / relative).read_text(encoding="utf-8"))]
    assert stale == [], (
        f"{stale} differ from what the generator writes: run python tools/example_project.py"
    )


def test_the_generator_refuses_a_folder_that_holds_anything(tmp_path: Path) -> None:
    (tmp_path / "notes.txt").write_text("mine", encoding="utf-8")
    written = write_project(tmp_path)
    assert written.returncode == 2
    assert "isn't an empty folder" in written.stderr
    assert [path.name for path in tmp_path.iterdir()] == ["notes.txt"]


def test_the_generated_table_references_have_no_todo_left() -> None:
    for relative in example_project.generated("starter"):
        text = (STARTER / relative).read_text(encoding="utf-8")
        assert "TODO:" not in text and "TODO check" not in text, relative
        assert text.count(example_project.BY_HAND) == 2, relative  # the key and does_not_add_up


def test_filling_in_refuses_a_table_reference_without_its_todo_line() -> None:
    filling = example_project.FILLED_IN["starter"]["ops.jobs"]
    with pytest.raises(example_project.TodoMissing, match="has 0 lines starting"):
        example_project.filled_in('"""ops.jobs - the jobs."""\n', "ops.jobs", filling)


def test_the_generated_table_references_match_the_example_database(starter: dict) -> None:
    for table in ("jobs", "job_runs", "run_alerts"):
        written = getattr(starter[f"table_references.{table}"], table)
        held = getattr(example_database, table)
        assert written._columns == held._columns, table
        assert written._key == held._key, table
        assert written._date_partition == held._date_partition, table
        assert written._does_not_add_up == held._does_not_add_up, table


# --- The Statements ----------------------------------------------------------------------------


def test_each_example_has_every_step(starter: dict) -> None:
    for name in EXAMPLES:
        missing = [step for step in STEPS if not callable(getattr(example(starter, name), step,
                                                                  None))]
        assert missing == [], f"{name} has no {missing}"


def test_only_a_preview_has_a_day_already_filled_in(starter: dict) -> None:
    """A write is never sent for a day nobody chose; a preview of the Example database's last
    day may be."""
    for name in EXAMPLES:
        module = example(starter, name)
        for step in ("write_day", "backfill"):
            parameters = inspect.signature(getattr(module, step)).parameters.values()
            assert all(p.default is inspect.Parameter.empty for p in parameters), f"{name}.{step}"
        assert inspect.signature(module.preview).parameters["day"].default == DAYS[-1]


def test_every_statement_function_builds(starter: dict) -> None:
    built = {name: statement_functions(example(starter, name)) for name in EXAMPLES}
    for name, functions in built.items():
        assert set(STEPS) <= set(functions), name
        for function, statements in functions.items():
            assert all(to_hive(s) for s in statements), f"{name}.{function}"


@pytest.mark.parametrize("name", EXAMPLES)
@pytest.mark.parametrize("day", DAYS)
def test_preview_is_the_select_write_day_sends(starter: dict, name: str, day: str) -> None:
    module = example(starter, name)
    assert without_the_write(to_hive(module.write_day(day))) == to_hive(module.preview(day))


@pytest.mark.parametrize("name", EXAMPLES)
def test_backfill_writes_each_day_as_write_day_does(starter: dict, name: str) -> None:
    module = example(starter, name)
    firsts = [line for s in module.backfill(*DAYS) for line in to_hive(s).splitlines()
              if line.startswith(INSERT)]
    assert firsts == [next(line for line in to_hive(module.write_day(day)).splitlines()
                           if line.startswith(INSERT)) for day in DAYS]


def test_example_2_reads_job_runs_from_the_day_before_in_both_writes(starter: dict) -> None:
    module = example(starter, EXAMPLES[1])
    assert "job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'" in to_hive(
        module.write_day("2026-09-24"))
    for s in module.backfill(*DAYS):
        assert "job_runs.dt BETWEEN '2026-09-22' AND '2026-09-24'" in to_hive(s)


def test_example_3_reads_both_saved_tables_and_the_jobs(starter: dict) -> None:
    hive = to_hive(example(starter, EXAMPLES[2]).preview())
    assert "FROM mart.daily_job_runs AS daily_job_runs" in hive
    assert "LEFT JOIN mart.alerts_per_job AS alerts_per_job" in hive
    assert "JOIN ops.jobs AS jobs" in hive


def runs_on(day: str) -> pd.DataFrame:
    """Each job's runs, failed runs and minutes on the day, in pandas."""
    runs = example_rows("job_runs")
    runs = runs[runs.dt == day].assign(failed=lambda rows: rows.status == "FAILED")
    return (runs.groupby("job_id")
            .agg(runs=("run_id", "size"), failed_runs=("failed", "sum"),
                 minutes=("duration_mins", "sum"))
            .reset_index())


def alerts_on(day: str) -> pd.DataFrame:
    """Each job's alerts and high alerts raised on the day, each alert joined to its run from
    the day before or the day, in pandas."""
    runs = example_rows("job_runs")
    alerts = example_rows("run_alerts")
    days = [(datetime.date.fromisoformat(day) - datetime.timedelta(days=1)).isoformat(), day]
    joined = alerts[alerts.dt == day].merge(runs[runs.dt.isin(days)][["run_id", "job_id"]],
                                            on="run_id")
    joined = joined.assign(high=lambda rows: rows.severity == "high")
    return (joined.groupby("job_id").agg(alerts=("alert_id", "size"), high_alerts=("high", "sum"))
            .reset_index())


def team_totals(daily: pd.DataFrame, alerts: pd.DataFrame | None = None) -> pd.DataFrame:
    """Each team's sums of the jobs' rows, in pandas, with 0 alerts for a job with none."""
    teams = example_rows("jobs")[["job_id", "team"]]
    rows = daily.merge(teams, on="job_id")
    columns = ["runs", "failed_runs", "minutes"]
    if alerts is not None:
        rows = rows.merge(alerts, on="job_id", how="left")
        columns += ["alerts", "high_alerts"]
    return rows.groupby("team")[columns].sum().reset_index()


def same(got: pd.DataFrame, expected: pd.DataFrame) -> None:
    pd.testing.assert_frame_equal(got.reset_index(drop=True).astype("int64", errors="ignore"),
                                  expected.reset_index(drop=True).astype("int64",
                                                                          errors="ignore"),
                                  check_dtype=False)


@pytest.mark.needs_example_database
@pytest.mark.parametrize("day", DAYS)
def test_example_1_previews_each_jobs_runs(starter: dict, day: str) -> None:
    got = run(example(starter, EXAMPLES[0]).preview(day), send=example_database.send)
    same(got, runs_on(day))


@pytest.mark.needs_example_database
@pytest.mark.parametrize("day", DAYS)
def test_example_2_previews_each_jobs_alerts(starter: dict, day: str) -> None:
    got = run(example(starter, EXAMPLES[1]).preview(day), send=example_database.send)
    same(got, alerts_on(day))


@pytest.mark.needs_example_database
@pytest.mark.parametrize("name", EXAMPLES[:2])
def test_each_day_of_a_backfill_saves_what_its_preview_shows(starter: dict, name: str) -> None:
    module = example(starter, name)
    for day, write in zip(DAYS, module.backfill(*DAYS)):
        saved = example_database.send(without_the_write(to_hive(write)))
        same(saved, run(module.preview(day), send=example_database.send))


@pytest.mark.needs_example_database
@pytest.mark.parametrize("day", DAYS)
def test_example_3_groups_each_teams_runs_from_job_runs(starter: dict, day: str) -> None:
    got = run(example(starter, EXAMPLES[2]).team_runs_from_job_runs(day),
              send=example_database.send)
    same(got, team_totals(runs_on(day)))


def rows_as_select(rows: pd.DataFrame, day: str) -> str:
    """Hive that gives the rows, and the day as dt, standing in for a Saved table's day."""
    def value(x) -> str:
        return f"'{x}'" if isinstance(x, str) else str(int(x))

    selects = [", ".join(f"{value(x)} AS {column}" for column, x in
                         [*zip(rows.columns, row), ("dt", day)])
               for row in rows.itertuples(index=False)]
    assert selects, "a Saved table standing in with no rows"
    return " UNION ALL ".join(f"SELECT {select}" for select in selects)


@pytest.mark.needs_example_database
@pytest.mark.parametrize("day", DAYS)
def test_example_3_previews_each_teams_day_from_what_examples_1_and_2_save(
        starter: dict, day: str) -> None:
    """The Saved tables only a warehouse holds are stood in for by the rows examples 1 and 2
    preview for the day, as written into example 3's Hive."""
    daily = run(example(starter, EXAMPLES[0]).preview(day), send=example_database.send)
    alerts = run(example(starter, EXAMPLES[1]).preview(day), send=example_database.send)
    hive = to_hive(example(starter, EXAMPLES[2]).preview(day))
    for table, rows in (("daily_job_runs", daily), ("alerts_per_job", alerts)):
        saved = f"mart.{table} AS {table}"
        assert hive.count(saved) == 1, table
        hive = hive.replace(saved, f"({rows_as_select(rows, day)}) AS {table}")
    same(example_database.send(hive), team_totals(daily, alerts))


@pytest.mark.needs_example_database
def test_every_select_on_the_example_databases_tables_runs(starter: dict) -> None:
    """Each SELECT a step returns runs, unless it reads a Saved table, which only a warehouse
    holds."""
    ran = []
    for name in EXAMPLES:
        for function, statements in statement_functions(example(starter, name)).items():
            for s in statements:
                if s._ddl is None and s._write is None and "mart." not in to_hive(s):
                    run(s, send=example_database.send)
                    ran.append(f"{name}.{function}")
    assert ran == [f"{EXAMPLES[0]}.preview", f"{EXAMPLES[1]}.preview",
                   f"{EXAMPLES[2]}.team_runs_from_job_runs"]


# --- run_pipeline.py ---------------------------------------------------------------------------


def test_the_steps_put_each_writer_before_its_readers(starter: dict) -> None:
    hive = [to_hive(s) for s in starter["run_pipeline"].steps(DAYS[-1])]
    writes = [i for i, text in enumerate(hive) if INSERT in text]
    creates = [i for i, text in enumerate(hive) if text.startswith("CREATE TABLE")]
    assert max(creates) < min(writes)
    written = {i: text.split(f"{INSERT} ")[1].split()[0] for i, text in
               enumerate(hive) if i in writes}
    for i, table in written.items():
        readers = [j for j in writes
                   if j != i and (f"FROM {table} " in hive[j] or f"JOIN {table} " in hive[j])]
        assert readers or table == "mart.team_day", f"nothing reads {table}"
        assert all(j > i for j in readers), f"{table} is read before it is written"


def test_the_dry_run_prints_every_steps_hive_under_its_name(starter: dict, capsys) -> None:
    pipeline = starter["run_pipeline"]
    pipeline.dry_run(DAYS[-1])
    printed = capsys.readouterr().out
    steps = pipeline.steps(DAYS[-1])
    names = ["create_daily_job_runs", "create_alerts_per_job", "create_team_day",
             "write_daily_job_runs", "write_alerts_per_job", "write_team_day"]
    assert len(steps) == len(names)
    for position, (name, s) in enumerate(zip(names, steps), start=1):
        assert f"-- {position} of {len(steps)}: {name}\n{to_hive(s)};" in printed


def test_send_all_sends_every_step_in_order(starter: dict) -> None:
    pipeline = starter["run_pipeline"]
    sent = []
    pipeline.send_all(sent.append, DAYS[-1])
    assert sent == [to_hive(s) for s in pipeline.steps(DAYS[-1])]


# --- The README --------------------------------------------------------------------------------


def test_the_readme_names_every_file_and_step() -> None:
    readme = (STARTER / "README.md").read_text(encoding="utf-8")
    unnamed = [relative for relative in example_project.project_files(STARTER)
               if f"`{relative}`" not in readme]
    unnamed += [step for step in STEPS if f"`{step}(" not in readme]
    assert unnamed == []
