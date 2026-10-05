"""The Example projects in `example_projects/`: generated files that are current, Statements
that build, SELECTs that run, and a README that names every file.

Each project is written again by `tools/example_project.py` into a temporary folder and
compared with the committed one, file by file, line endings aside. In Spark Composer's run it
is written for Spark Composer, and compared with the committed project named for it.

The project's scripts import their own folders, such as `table_references`, as a notebook
started in the project's folder does. The Worked examples have folders of the same names, so
the project's modules are imported with its folder first on the path, then put away again.

The starter project's tests come first, then the intermediate project's. A SELECT that reads a
Saved table, which only a warehouse holds, runs with the Saved table stood in for by the rows
the Statement that writes it previews. One that sqlglot's executor can't run, such as one with
row_number or week_start, runs only in Spark Composer's run, and is skipped in sqlglot
Composer's with the reason.
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
from conftest import (
    INSERT, ROOT, edition, example_rows, project_on_the_path, standing_in, toolbox_module,
    without_the_write,
)
from sqlglot_composer import example_database, run, to_hive

STARTER = ROOT / "example_projects" / "starter"
INTERMEDIATE = ROOT / "example_projects" / "intermediate"
FOLDERS = {"starter": STARTER, "intermediate": INTERMEDIATE}
EXAMPLES = ("example_1_daily_job_runs", "example_2_alerts_per_job", "example_3_team_day")
# The steps each example offers, in the order they are sent.
STEPS = ("create", "preview", "write_day", "backfill")
DAYS = ("2026-09-23", "2026-09-24")
# What each step's day parameters are given, by name.
ARGUMENTS = {"day": DAYS[-1], "first_day": DAYS[0], "last_day": DAYS[-1]}
TOP_NAMES = ("table_references", "building_blocks", "statements", "run_pipeline", "settings")


def _module_names(folder: Path) -> list[str]:
    """Each script of the project, as the module a notebook in its folder imports."""
    return [relative.removesuffix(".py").replace("/", ".")
            for relative in example_project.project_files(folder) if relative.endswith(".py")]


def _imported(folder: Path):
    """The project's modules by name, imported with its folder first on the path, then put
    away again, and whatever modules of those names were there before put back."""
    with project_on_the_path(folder, TOP_NAMES):
        yield {name: importlib.import_module(name) for name in _module_names(folder)}


@pytest.fixture(scope="module")
def starter() -> dict:
    """The starter project's modules by name, such as "statements.example_1_daily_job_runs"."""
    yield from _imported(STARTER)


@pytest.fixture(scope="module")
def intermediate() -> dict:
    """The intermediate project's modules by name, such as "statements.quality_checks"."""
    yield from _imported(INTERMEDIATE)


def example(project: dict, name: str):
    return project[f"statements.{name}"]


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


# --- The generated files ---------------------------------------------------------------------


def write_project(into: Path, project: str = "starter") -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ROOT / "tools" / "example_project.py"), "--project", project,
         "--edition", edition().option, "--into", str(into)],
        capture_output=True, text=True, check=False,
    )


def test_every_example_project_has_a_folder() -> None:
    assert set(example_project.PROJECTS) == set(FOLDERS)


@pytest.mark.parametrize("project", example_project.PROJECTS)
def test_the_committed_project_is_what_the_generator_writes(tmp_path: Path, project: str) -> None:
    folder = FOLDERS[project]
    into = tmp_path / project
    written = write_project(into, project)
    assert written.returncode == 0, written.stderr
    committed = example_project.project_files(folder)
    assert example_project.project_files(into) == committed
    stale = [relative for relative in committed
             if (into / relative).read_text(encoding="utf-8")
             != editions.named_for(edition(), (folder / relative).read_text(encoding="utf-8"))]
    assert stale == [], (
        f"{stale} differ from what the generator writes: run "
        f"python tools/example_project.py --project {project}"
    )


def test_the_generator_refuses_a_folder_that_holds_anything(tmp_path: Path) -> None:
    (tmp_path / "notes.txt").write_text("mine", encoding="utf-8")
    written = write_project(tmp_path)
    assert written.returncode == 2
    assert "isn't an empty folder" in written.stderr
    assert [path.name for path in tmp_path.iterdir()] == ["notes.txt"]


@pytest.mark.parametrize("project", example_project.PROJECTS)
def test_the_generated_table_references_have_no_todo_left(project: str) -> None:
    fillings = example_project.FILLED_IN[project].values()
    for relative, filling in zip(example_project.generated(project), fillings, strict=True):
        text = (FOLDERS[project] / relative).read_text(encoding="utf-8")
        assert "TODO:" not in text and "TODO check" not in text, relative
        # the key and does_not_add_up, and the Date partition where it was a TODO too
        filled = 3 if "date_partition" in filling else 2
        assert text.count(example_project.BY_HAND) == filled, relative


def test_filling_in_refuses_a_table_reference_without_its_todo_line() -> None:
    filling = example_project.FILLED_IN["starter"]["ops.jobs"]
    with pytest.raises(example_project.TodoMissing, match="has 0 lines starting"):
        example_project.filled_in('"""ops.jobs - the jobs."""\n', "ops.jobs", filling)


def matches_the_example_databases(project: dict, tables: tuple[str, ...]) -> None:
    for table in tables:
        written = getattr(project[f"table_references.{table}"], table)
        held = getattr(example_database, table)
        assert written._columns == held._columns, table
        assert written._key == held._key, table
        assert written._date_partition == held._date_partition, table
        assert written._date_format == held._date_format, table
        assert written._does_not_add_up == held._does_not_add_up, table


def test_the_generated_table_references_match_the_example_database(starter: dict) -> None:
    matches_the_example_databases(starter, ("jobs", "job_runs", "run_alerts"))


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


# === The intermediate project ===================================================================

I_EXAMPLES = ("example_1_job_day_costs", "example_2_owner_as_of", "example_3_team_week")
# The steps each intermediate example offers, in the order they are sent.
I_STEPS = ("create", "preview", "write_days")
# Days to check: a team change (2026-09-18, report_build moves and fails), a retry (09-14), a
# run still going and a bill not yet in (09-24).
I_DAYS = ("2026-09-14", "2026-09-18", "2026-09-24")
WINDOW = ("2026-09-22", "2026-09-24")  # the last 3 days, as each run writes them
ALL_DAYS = ("2026-09-11", "2026-09-24")  # every day the Example database holds
# Why sqlglot Composer's Example database skips a SELECT.
NO_WINDOW_FUNCTIONS = ("sqlglot's executor has no window functions, so it can't run "
                       "row_number: Spark Composer's run checks it")
NO_WEEK_START = ("sqlglot's executor has no NEXT_DAY, so it can't run week_start: Spark "
                 "Composer's run checks it")


def skip_in_sqlglot_composer(reason: str) -> None:
    if edition() is editions.SQLGLOT_COMPOSER:
        pytest.skip(reason)


def i_arguments(intermediate: dict) -> dict:
    """What each intermediate step's parameters are given, by name."""
    return {"day": DAYS[-1], "first_day": WINDOW[0], "last_day": WINDOW[-1],
            "table": intermediate["settings"].REGION_COSTS}


def built_by(module, arguments: dict) -> dict[str, list]:
    """Each function a script defines that returns Statements, by name, with what it returns
    when its parameters are given `arguments`. A function with a parameter `arguments` doesn't
    name, such as quality_checks.column_name(column), builds no Statement, and is left
    out."""
    statement_type = toolbox_module("clauses").Statement
    found = {}
    for name, function in vars(module).items():
        if not inspect.isfunction(function) or function.__module__ != module.__name__:
            continue
        parameters = inspect.signature(function).parameters
        if not set(parameters) <= set(arguments):
            continue
        given = {parameter: arguments[parameter] for parameter in parameters}
        result = function(**given)
        values = result.values() if isinstance(result, dict) else statements_in(result)
        built = [s for s in values if isinstance(s, statement_type)]
        if built:
            found[name] = built
    return found


# --- The generated files and settings.py ---------------------------------------------------------


def test_the_intermediate_table_references_match_the_example_database(
        intermediate: dict) -> None:
    matches_the_example_databases(intermediate, ("job_events", "job_owners", "region_costs"))


def test_region_costs_names_its_date_partition_and_how_it_writes_days() -> None:
    text = (INTERMEDIATE / "table_references" / "region_costs.py").read_text(encoding="utf-8")
    assert '    date_partition="dt",\n    date_format="%Y%m%d",\n' in text
    assert "region, the first partition, holds no day" in text


def test_settings_name_each_tables_key_as_its_table_reference_does(intermediate: dict) -> None:
    checks = intermediate["statements.quality_checks"]
    tables = intermediate["settings"].TABLES_READ
    assert [table["name"] for table in tables] == list(checks.TABLE_REFERENCES)
    for table in tables:
        t = checks.TABLE_REFERENCES[table["name"]]
        assert t._name == table["name"]
        assert t._key == table["key"], table["name"]
        assert t._date_partition == table["date_partition"], table["name"]
        assert set(table["add_up"]) <= set(t._columns), table["name"]


def test_the_review_edit_is_refused_where_its_line_isnt(tmp_path: Path) -> None:
    edit = example_project.REVIEWED_EDIT["intermediate"]
    edited = tmp_path / edit["file"]
    edited.parent.mkdir(parents=True)
    edited.write_text('"""A Building block."""\n', encoding="utf-8")
    with pytest.raises(example_project.EditMissing, match="has 0 lines"):
        example_project.write_review_before_the_edit(tmp_path, edit)


def test_the_review_edit_is_the_one_the_readme_shows() -> None:
    edit = example_project.REVIEWED_EDIT["intermediate"]
    readme = (INTERMEDIATE / "README.md").read_text(encoding="utf-8")
    assert f"-{edit['before']}\n+{edit['after']}\n" in readme
    block = (INTERMEDIATE / edit["file"]).read_text(encoding="utf-8")
    assert block.count(edit["after"]) == 1


def test_the_lineage_review_differs_only_by_the_edit() -> None:
    """Spaces aside, the "after" file is the "before" file with the edited condition changed,
    in the Python and in the Hive."""
    before = (INTERMEDIATE / "lineage" / "review_before_edit.md").read_text(encoding="utf-8")
    after = (INTERMEDIATE / "lineage" / "review_after_edit.md").read_text(encoding="utf-8")
    edited = "".join(before.split())
    assert edited != "".join(after.split())
    for old, new in (('equals(job_events.event_type,"finish")',
                      'is_in(job_events.event_type,["finish","fail"])'),
                     ("job_events.event_type='finish'", "job_events.event_type IN('finish','fail')")):
        assert old in edited
        edited = edited.replace(old, "".join(new.split()))
    assert edited == "".join(after.split())
    team_days = after[after.index("## write_team_days"):]
    minutes = team_days[team_days.index("#### `minutes`"):].split("####")[1]
    assert 'where=is_in(job_events.event_type, ["finish", "fail"])' in minutes


# --- The Statements ----------------------------------------------------------------------------


def test_each_intermediate_example_has_every_step(intermediate: dict) -> None:
    for name in I_EXAMPLES:
        module = example(intermediate, name)
        missing = [step for step in I_STEPS if not callable(getattr(module, step, None))]
        assert missing == [], f"{name} has no {missing}"


def test_only_a_select_has_a_day_already_filled_in(intermediate: dict) -> None:
    """A write is never sent for a day nobody chose; a SELECT of the Example database's last
    day may be."""
    for name in I_EXAMPLES:
        module = example(intermediate, name)
        parameters = inspect.signature(module.write_days).parameters.values()
        assert all(p.default is inspect.Parameter.empty for p in parameters), name
        assert inspect.signature(module.preview).parameters["day"].default == DAYS[-1]


def test_every_intermediate_statement_function_builds(intermediate: dict) -> None:
    arguments = i_arguments(intermediate)
    for name in (*I_EXAMPLES, "quality_checks"):
        functions = built_by(example(intermediate, name), arguments)
        if name in I_EXAMPLES:
            assert set(I_STEPS) <= set(functions), name
        for function, statements in functions.items():
            assert all(to_hive(s) for s in statements), f"{name}.{function}"


@pytest.mark.parametrize("name", I_EXAMPLES)
def test_write_days_writes_each_day_once_oldest_first(intermediate: dict, name: str) -> None:
    writes = example(intermediate, name).write_days(*WINDOW)
    firsts = [to_hive(write).split(INSERT)[1].splitlines()[0] for write in writes]
    target = {"example_1_job_day_costs": "mart.job_day_costs",
              "example_2_owner_as_of": "mart.job_day_facts",
              "example_3_team_week": "mart.team_days"}[name]
    assert firsts == [f" {target} PARTITION(dt = '{day}')"
                      for day in ("2026-09-22", "2026-09-23", "2026-09-24")]


def test_example_1_reads_region_costs_days_its_own_way(intermediate: dict) -> None:
    hive = to_hive(example(intermediate, I_EXAMPLES[0]).write_days(*WINDOW)[0])
    assert "region_costs.dt = '20260922'" in hive
    assert "PARTITION(dt = '2026-09-22')" in hive


def test_example_3_reads_both_saved_tables(intermediate: dict) -> None:
    hive = to_hive(example(intermediate, I_EXAMPLES[2]).preview())
    assert "FROM mart.job_day_facts AS job_day_facts" in hive
    assert "LEFT JOIN mart.job_day_costs AS job_day_costs" in hive


def costs_on(day: str) -> pd.DataFrame:
    """Each job's cost on the day, every region added up, in pandas: NULL while no bill is in."""
    costs = example_rows("region_costs")
    costs = costs[costs.dt == day.replace("-", "")]
    return (costs.groupby("job_id")
            .agg(cost_cents=("cost_cents", lambda cents: cents.sum(min_count=1)))
            .reset_index())


def facts_on(day: str) -> pd.DataFrame:
    """Each job's events, runs and minutes on the day, with its team that day, in pandas."""
    events = example_rows("job_events")
    events = events[events.dt == day]
    ends = events.event_type.isin(["finish", "fail"])
    per_job = (events.assign(start=events.event_type == "start",
                             ended=events.minutes.where(ends, 0))
               .groupby("job_id")
               .agg(events=("event_id", "size"), runs=("start", "sum"), minutes=("ended", "sum"))
               .reset_index())
    owners = example_rows("job_owners")
    owners = owners[owners.dt == day][["job_id", "team"]]
    return per_job.merge(owners, on="job_id", how="left")[
        ["job_id", "team", "events", "runs", "minutes"]]


def team_day_on(day: str, with_costs: bool = True) -> pd.DataFrame:
    """Each team's events, runs, minutes and cost on the day, in pandas."""
    rows = facts_on(day)
    columns = ["events", "runs", "minutes"]
    if with_costs:
        rows = rows.merge(costs_on(day), on="job_id", how="left")
        columns.append("cost_cents")
    return (rows.groupby("team")[columns]
            .agg(lambda numbers: numbers.sum(min_count=1)).reset_index())


def newest_owners_on(day: str) -> pd.DataFrame:
    """Each job's team and owner in its newest snapshot from the 7 days up to the day."""
    owners = example_rows("job_owners")
    first_day = (datetime.date.fromisoformat(day) - datetime.timedelta(days=6)).isoformat()
    owners = owners[(owners.dt >= first_day) & (owners.dt <= day)]
    newest = owners.sort_values("dt").groupby("job_id").tail(1).sort_values("job_id")
    return newest[["job_id", "team", "owner", "dt"]]


@pytest.mark.needs_example_database
@pytest.mark.parametrize("day", I_DAYS)
def test_intermediate_example_1_previews_each_jobs_cost(intermediate: dict, day: str) -> None:
    got = run(example(intermediate, I_EXAMPLES[0]).preview(day), send=example_database.send)
    same(got, costs_on(day))


@pytest.mark.needs_example_database
@pytest.mark.parametrize("day", I_DAYS)
def test_intermediate_example_2_previews_each_jobs_day_with_its_team_then(
        intermediate: dict, day: str) -> None:
    got = run(example(intermediate, I_EXAMPLES[1]).preview(day), send=example_database.send)
    same(got, facts_on(day))


@pytest.mark.needs_example_database
def test_example_2_counts_report_builds_days_for_the_team_it_had_then(
        intermediate: dict) -> None:
    module = example(intermediate, I_EXAMPLES[1])
    teams = {day: run(module.preview(day), send=example_database.send).set_index("job_id")
             .team.get(3) for day in ("2026-09-14", "2026-09-18")}
    assert teams == {"2026-09-14": "data", "2026-09-18": "finance"}


@pytest.mark.needs_example_database
@pytest.mark.parametrize("name", I_EXAMPLES[:2])
def test_each_day_of_write_days_saves_what_its_preview_shows(
        intermediate: dict, name: str) -> None:
    module = example(intermediate, name)
    days = ("2026-09-22", "2026-09-23", "2026-09-24")
    for day, write in zip(days, module.write_days(*WINDOW), strict=True):
        saved = example_database.send(without_the_write(to_hive(write)))
        same(saved, run(module.preview(day), send=example_database.send))


@pytest.mark.needs_example_database
def test_each_day_of_example_3s_write_days_saves_what_its_preview_shows(
        intermediate: dict) -> None:
    """The Saved tables only a warehouse holds are stood in for, in both, by the rows examples
    1 and 2 preview for each day."""
    days = ("2026-09-22", "2026-09-23", "2026-09-24")
    saved = {"job_day_facts": previewed_days(example(intermediate, I_EXAMPLES[1]), days),
             "job_day_costs": previewed_days(example(intermediate, I_EXAMPLES[0]), days)}
    module = example(intermediate, I_EXAMPLES[2])
    for day, write in zip(days, module.write_days(*WINDOW), strict=True):
        written = example_database.send(standing_in(without_the_write(to_hive(write)), saved))
        previewed = example_database.send(standing_in(to_hive(module.preview(day)), saved))
        same(written, previewed)
        same(written, team_day_on(day))


@pytest.mark.needs_example_database
@pytest.mark.parametrize("day", I_DAYS)
def test_example_2_finds_each_jobs_newest_owner_without_row_number(
        intermediate: dict, day: str) -> None:
    module = example(intermediate, I_EXAMPLES[1])
    got = run(module.newest_owners_by_newest_day(day), send=example_database.send)
    same(got, newest_owners_on(day))


@pytest.mark.needs_example_database
@pytest.mark.parametrize("day", I_DAYS)
def test_example_2_finds_each_jobs_newest_owner_with_row_number(
        intermediate: dict, day: str) -> None:
    skip_in_sqlglot_composer(NO_WINDOW_FUNCTIONS)
    module = example(intermediate, I_EXAMPLES[1])
    got = run(module.newest_owners(day), send=example_database.send)
    same(got, newest_owners_on(day))


@pytest.mark.needs_example_database
@pytest.mark.parametrize("day", I_DAYS)
def test_example_3_groups_each_teams_day_from_job_events(intermediate: dict, day: str) -> None:
    got = run(example(intermediate, I_EXAMPLES[2]).team_day_from_job_events(day),
              send=example_database.send)
    same(got, team_day_on(day, with_costs=False))


def previewed_days(module, days) -> pd.DataFrame:
    """What the module's preview shows for each of the days, with the day as dt."""
    return pd.concat([run(module.preview(day), send=example_database.send).assign(dt=day)
                      for day in days], ignore_index=True)


@pytest.mark.needs_example_database
@pytest.mark.parametrize("day", I_DAYS)
def test_intermediate_example_3_previews_each_teams_day_from_both_saved_tables(
        intermediate: dict, day: str) -> None:
    """The Saved tables only a warehouse holds are stood in for by the rows examples 1 and 2
    preview for the day."""
    saved = {"job_day_facts": previewed_days(example(intermediate, I_EXAMPLES[1]), [day]),
             "job_day_costs": previewed_days(example(intermediate, I_EXAMPLES[0]), [day])}
    hive = standing_in(to_hive(example(intermediate, I_EXAMPLES[2]).preview(day)), saved)
    same(example_database.send(hive), team_day_on(day))


@pytest.mark.needs_example_database
def test_example_3_adds_each_teams_days_up_into_weeks(intermediate: dict) -> None:
    skip_in_sqlglot_composer(NO_WEEK_START)
    days = [(datetime.date(2026, 9, 11) + datetime.timedelta(days=n)).isoformat()
            for n in range(14)]
    team_days = pd.concat([team_day_on(day).assign(dt=day) for day in days], ignore_index=True)
    hive = standing_in(to_hive(example(intermediate, I_EXAMPLES[2]).week_totals(*ALL_DAYS)),
                       {"team_days": team_days})
    monday = pd.to_datetime(team_days.dt)
    monday = (monday - pd.to_timedelta(monday.dt.weekday, unit="D")).dt.strftime("%Y-%m-%d")
    expected = (team_days.assign(week=monday)
                .groupby(["week", "team"])[["events", "runs", "minutes", "cost_cents"]]
                .agg(lambda numbers: numbers.sum(min_count=1)).reset_index())
    got = example_database.send(hive).sort_values(["week", "team"])
    same(got, expected)
    week = expected[expected.week == "2026-09-14"].set_index("team").runs
    # report_build's run on 2026-09-14 counts for data, and its run on 09-18 for finance
    assert week.to_dict() == {"data": 7 + 1, "finance": 5 + 1}


# --- The quality checks --------------------------------------------------------------------------


def window_rows(table: str, day_column_compact: bool = False) -> pd.DataFrame:
    rows = example_rows(table)
    first, last = WINDOW
    if day_column_compact:
        first, last = first.replace("-", ""), last.replace("-", "")
    return rows[(rows.dt >= first) & (rows.dt <= last)]


@pytest.mark.needs_example_database
def test_the_quality_checks_find_what_pandas_finds(intermediate: dict) -> None:
    checks = intermediate["statements.quality_checks"].every_check(*WINDOW)
    for table in intermediate["settings"].TABLES_READ:
        name = table["name"]
        rows = window_rows(name.split(".")[1], day_column_compact=name == "ops.region_costs")
        repeated = run(checks[f"repeated_keys {name}"], send=example_database.send)
        assert list(repeated.columns) == [*table["key"], "times_seen"]
        assert len(repeated) == rows.duplicated(table["key"]).sum() == 0
        nulls = run(checks[f"null_counts {name}"], send=example_database.send)
        expected = rows.drop(columns="dt").isna().sum().add_prefix("null_").to_frame().T
        same(nulls, expected)
        per_day = run(checks[f"rows_per_day {name}"], send=example_database.send)
        expected = rows.groupby("dt").agg(row_count=("dt", "size"),
                                          **{c: (c, "sum") for c in table["add_up"]})
        same(per_day, expected.reset_index())


@pytest.mark.needs_example_database
def test_the_check_of_jobs_not_run_finds_what_pandas_finds(intermediate: dict) -> None:
    checks = intermediate["statements.quality_checks"]
    got = run(checks.jobs_not_run(*WINDOW), send=example_database.send)
    owners = window_rows("job_owners")
    ran = window_rows("job_events")[["job_id", "dt"]].drop_duplicates().assign(ran=True)
    expected = owners.merge(ran, on=["job_id", "dt"], how="left")
    expected = expected[expected.ran.isna()][["job_id", "team", "owner", "dt"]]
    same(got, expected.sort_values(["job_id", "dt"]))
    assert set(got.job_id) == {3, 4}  # report_build, on days it didn't run, and cache_warm


@pytest.mark.needs_example_database
def test_the_costs_saved_match_the_costs_billed(intermediate: dict) -> None:
    """mart.job_day_costs, which only a warehouse holds, is stood in for by what example 1
    previews for each day."""
    days = ("2026-09-22", "2026-09-23", "2026-09-24")
    saved = previewed_days(example(intermediate, I_EXAMPLES[0]), days)
    hive = to_hive(intermediate["statements.quality_checks"].costs_billed_and_saved(*WINDOW))
    got = example_database.send(standing_in(hive, {"job_day_costs": saved}))
    billed = window_rows("region_costs", day_column_compact=True).cost_cents.sum()
    same(got, pd.DataFrame({"cents_billed": [billed], "cents_saved": [billed]}))


@pytest.mark.needs_example_database
def test_every_intermediate_select_on_the_example_databases_tables_runs(
        intermediate: dict) -> None:
    """Each SELECT runs, unless it reads a Saved table, which only a warehouse holds, or holds
    what sqlglot's executor can't run."""
    ran = []
    arguments = i_arguments(intermediate)
    for name in (*I_EXAMPLES, "quality_checks"):
        for function, statements in built_by(example(intermediate, name), arguments).items():
            for s in statements:
                hive = to_hive(s)
                if s._ddl is not None or s._write is not None or "mart." in hive:
                    continue
                if edition() is editions.SQLGLOT_COMPOSER and "ROW_NUMBER" in hive:
                    continue  # NO_WINDOW_FUNCTIONS: Spark Composer's run runs it
                run(s, send=example_database.send)
                ran.append(f"{name}.{function}")
    expected = [f"{I_EXAMPLES[0]}.preview", f"{I_EXAMPLES[1]}.preview",
                f"{I_EXAMPLES[1]}.newest_owners", f"{I_EXAMPLES[1]}.newest_owners_by_newest_day",
                f"{I_EXAMPLES[2]}.team_day_from_job_events",
                *[f"quality_checks.{check}" for check in
                  ("repeated_keys", "null_counts", "rows_per_day")],
                # every check but costs_billed_and_saved, which reads a Saved table
                *["quality_checks.every_check"] * (3 * len(intermediate["settings"].TABLES_READ)
                                                   + 1),
                "quality_checks.jobs_not_run"]
    if edition() is editions.SQLGLOT_COMPOSER:
        expected.remove(f"{I_EXAMPLES[1]}.newest_owners")
    assert sorted(ran) == sorted(expected)


# --- run_pipeline.py ---------------------------------------------------------------------------


def test_the_intermediate_steps_put_each_writer_before_its_readers(intermediate: dict) -> None:
    pipeline = intermediate["run_pipeline"]
    hive = [to_hive(s) for s in pipeline.in_order(pipeline.steps(DAYS[-1]))]
    writes = [i for i, text in enumerate(hive) if INSERT in text]
    creates = [i for i, text in enumerate(hive) if text.startswith("CREATE TABLE")]
    assert max(creates) < min(writes)
    written = {i: (hive[i].split(f"{INSERT} ")[1].split()[0],
                   hive[i].split("PARTITION(dt = ")[1][:12]) for i in writes}
    for i, (table, day) in written.items():
        readers = [j for j in writes if j != i and written[j][1] == day
                   and (f"FROM {table} " in hive[j] or f"JOIN {table} " in hive[j])]
        assert readers or table == "mart.team_days", f"nothing reads {table} on {day}"
        assert all(j > i for j in readers), f"{table} on {day} is read before it is written"


def test_each_run_writes_the_last_3_days_and_a_backfill_every_day_asked(
        intermediate: dict) -> None:
    pipeline = intermediate["run_pipeline"]
    daily = [s for s in pipeline.in_order(pipeline.steps(DAYS[-1])) if INSERT in to_hive(s)]
    assert len(daily) == 3 * 3
    backfill = [s for s in pipeline.in_order(pipeline.steps(DAYS[-1], backfill_from=ALL_DAYS[0]))
                if INSERT in to_hive(s)]
    assert len(backfill) == 3 * 14
    assert "PARTITION(dt = '2026-09-11')" in to_hive(backfill[0])


def test_the_intermediate_dry_run_prints_every_steps_hive_under_its_name(
        intermediate: dict, capsys) -> None:
    pipeline = intermediate["run_pipeline"]
    pipeline.dry_run(DAYS[-1])
    printed = capsys.readouterr().out
    statements = pipeline.in_order(pipeline.steps(DAYS[-1]))
    names = ["create_job_day_costs", "create_job_day_facts", "create_team_days",
             *[f"{write}[{n}]" for write in
               ("write_job_day_costs", "write_job_day_facts", "write_team_days")
               for n in range(3)]]
    assert len(statements) == len(names)
    for position, (name, s) in enumerate(zip(names, statements), start=1):
        assert f"-- {position} of {len(statements)}: {name}\n{to_hive(s)};" in printed


def test_the_intermediate_send_all_sends_every_step_in_order(intermediate: dict) -> None:
    pipeline = intermediate["run_pipeline"]
    sent = []
    pipeline.send_all(sent.append, DAYS[-1])
    assert sent == [to_hive(s) for s in pipeline.in_order(pipeline.steps(DAYS[-1]))]


def test_check_all_runs_every_check_and_gathers_the_results(intermediate: dict) -> None:
    pipeline = intermediate["run_pipeline"]
    sent = []

    def send(hive: str) -> pd.DataFrame:
        sent.append(hive)
        return pd.DataFrame({"rows": [len(sent)]})

    results = pipeline.check_all(send, DAYS[-1])
    checks = intermediate["statements.quality_checks"].every_check(*WINDOW)
    assert list(results) == list(checks)
    assert sent == [to_hive(check) for check in checks.values()]


# --- The README --------------------------------------------------------------------------------


def test_the_intermediate_readme_names_every_file_and_step() -> None:
    readme = (INTERMEDIATE / "README.md").read_text(encoding="utf-8")
    unnamed = [relative for relative in example_project.project_files(INTERMEDIATE)
               if f"`{relative}`" not in readme]
    unnamed += [step for step in I_STEPS if f"`{step}(" not in readme]
    assert unnamed == []
