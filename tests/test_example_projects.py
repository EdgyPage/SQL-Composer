"""The example projects in `example_projects/`: generated files that are current, Statements
that build, SELECTs that run, and a README that names every file.

Each project is written again by `tools/example_project.py` into a temporary folder and
compared with the committed one, file by file, line endings aside. In Spark Composer's run it
is written for Spark Composer, and compared with the committed project named for it.

The project's scripts import their own folders, such as `table_references`, as a notebook
started in the project's folder does. The Worked examples have folders of the same names, so
the project's modules are imported with its folder first on the path, then put away again.
"""

from __future__ import annotations

import importlib
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
STEPS = ("create", "look", "write_day", "backfill")
DAYS = ("2026-09-23", "2026-09-24")
TOP_NAMES = ("table_references", "building_blocks", "statements", "run_pipeline")


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


# --- The generated files ---------------------------------------------------------------------


def test_the_committed_project_is_what_the_generator_writes(tmp_path: Path) -> None:
    into = tmp_path / "starter"
    written = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "example_project.py"), "--level", "starter",
         "--edition", edition().option, "--into", str(into)],
        capture_output=True, text=True, check=False,
    )
    assert written.returncode == 0, written.stderr
    committed = example_project.project_files(STARTER)
    assert example_project.project_files(into) == committed
    stale = [relative for relative in committed
             if (into / relative).read_text(encoding="utf-8")
             != editions.named_for(edition(), (STARTER / relative).read_text(encoding="utf-8"))]
    assert stale == [], (
        f"{stale} differ from what the generator writes: run python tools/example_project.py"
    )


def test_the_generated_table_references_have_no_todo_left() -> None:
    for relative in example_project.generated("starter"):
        text = (STARTER / relative).read_text(encoding="utf-8")
        assert "TODO:" not in text and "TODO check" not in text, relative


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


def test_every_statement_function_builds(starter: dict) -> None:
    statement_type = toolbox_module("clauses").Statement
    built = 0
    for name in EXAMPLES:
        module = example(starter, name)
        for function in vars(module).values():
            if not callable(function) or getattr(function, "__module__", "") != module.__name__:
                continue
            for s in statements_in(function()):
                if isinstance(s, statement_type):
                    assert to_hive(s), f"{name}.{function.__name__}"
                    built += 1
    assert built >= len(EXAMPLES) * len(STEPS)


@pytest.mark.parametrize("name", EXAMPLES)
@pytest.mark.parametrize("day", DAYS)
def test_look_is_the_select_write_day_sends(starter: dict, name: str, day: str) -> None:
    module = example(starter, name)
    write = to_hive(module.write_day(day)).splitlines()
    write = [line for line in write if not line.startswith("INSERT OVERWRITE TABLE")]
    assert "\n".join(write) == to_hive(module.look(day))


@pytest.mark.parametrize("name", EXAMPLES)
def test_backfill_writes_each_day_as_write_day_does(starter: dict, name: str) -> None:
    module = example(starter, name)
    firsts = [line for s in module.backfill(*DAYS) for line in to_hive(s).splitlines()
              if line.startswith("INSERT OVERWRITE TABLE")]
    assert firsts == [next(line for line in to_hive(module.write_day(day)).splitlines()
                           if line.startswith("INSERT OVERWRITE TABLE")) for day in DAYS]


def expected_runs(day: str) -> pd.DataFrame:
    """Each job's runs, failed runs and minutes on the day, in pandas."""
    runs = example_rows("job_runs")
    runs = runs[runs.dt == day].assign(failed=lambda rows: rows.status == "FAILED")
    return (runs.groupby("job_id")
            .agg(runs=("run_id", "size"), failed_runs=("failed", "sum"),
                 minutes=("duration_mins", "sum"))
            .reset_index())


def expected_alerts(day: str) -> pd.DataFrame:
    """Each job's alerts and high alerts on the day, each alert joined to its run, in pandas."""
    runs = example_rows("job_runs")
    alerts = example_rows("run_alerts")
    joined = alerts[alerts.dt == day].merge(runs[runs.dt == day][["run_id", "job_id"]],
                                            on="run_id")
    joined = joined.assign(high=lambda rows: rows.severity == "high")
    return (joined.groupby("job_id").agg(alerts=("alert_id", "size"), high_alerts=("high", "sum"))
            .reset_index())


def same(got: pd.DataFrame, expected: pd.DataFrame) -> None:
    pd.testing.assert_frame_equal(got.reset_index(drop=True).astype("int64", errors="ignore"),
                                  expected.reset_index(drop=True).astype("int64",
                                                                          errors="ignore"),
                                  check_dtype=False)


@pytest.mark.needs_example_database
@pytest.mark.parametrize("day", DAYS)
def test_example_1_looks_at_each_jobs_runs(starter: dict, day: str) -> None:
    got = run(example(starter, EXAMPLES[0]).look(day), send=example_database.send)
    same(got, expected_runs(day))


@pytest.mark.needs_example_database
@pytest.mark.parametrize("day", DAYS)
def test_example_2_looks_at_each_jobs_alerts(starter: dict, day: str) -> None:
    got = run(example(starter, EXAMPLES[1]).look(day), send=example_database.send)
    same(got, expected_alerts(day))


@pytest.mark.needs_example_database
@pytest.mark.parametrize("day", DAYS)
def test_example_3_works_out_each_teams_runs_from_the_source(starter: dict, day: str) -> None:
    got = run(example(starter, EXAMPLES[2]).runs_from_the_source(day),
              send=example_database.send)
    teams = example_rows("jobs")[["job_id", "team"]]
    expected = (expected_runs(day).merge(teams, on="job_id").groupby("team")
                [["runs", "failed_runs", "minutes"]].sum().reset_index())
    same(got, expected)


@pytest.mark.needs_example_database
def test_every_select_on_the_example_databases_tables_runs(starter: dict) -> None:
    """Each SELECT a step returns runs, unless it reads a Saved table, which only a warehouse
    holds."""
    statement_type = toolbox_module("clauses").Statement
    ran = 0
    for name in EXAMPLES:
        module = example(starter, name)
        for function in vars(module).values():
            if not callable(function) or getattr(function, "__module__", "") != module.__name__:
                continue
            for s in statements_in(function()):
                if (isinstance(s, statement_type) and s._ddl is None and s._write is None
                        and "mart." not in to_hive(s)):
                    run(s, send=example_database.send)
                    ran += 1
    assert ran == 3  # example 1's and 2's look, and example 3's runs_from_the_source


# --- run_pipeline.py ---------------------------------------------------------------------------


def test_the_steps_put_each_writer_before_its_readers(starter: dict) -> None:
    hive = [to_hive(s) for s in starter["run_pipeline"].steps()]
    writes = [i for i, text in enumerate(hive) if "INSERT OVERWRITE TABLE" in text]
    creates = [i for i, text in enumerate(hive) if text.startswith("CREATE TABLE")]
    assert max(creates) < min(writes)
    written = {i: text.split("INSERT OVERWRITE TABLE ")[1].split()[0] for i, text in
               enumerate(hive) if i in writes}
    for i, table in written.items():
        readers = [j for j in writes
                   if j != i and (f"FROM {table} " in hive[j] or f"JOIN {table} " in hive[j])]
        assert readers or table == "mart.team_day", f"nothing reads {table}"
        assert all(j > i for j in readers), f"{table} is read before it is written"


def test_the_dry_run_prints_every_steps_hive(starter: dict, capsys) -> None:
    pipeline = starter["run_pipeline"]
    pipeline.dry_run()
    printed = capsys.readouterr().out
    steps = pipeline.steps()
    for position, s in enumerate(steps, start=1):
        assert f"-- {position} of {len(steps)}" in printed
        assert to_hive(s) + ";" in printed


def test_main_sends_every_step_in_order(starter: dict) -> None:
    pipeline = starter["run_pipeline"]
    sent = []
    pipeline.main(send=sent.append)
    assert sent == [to_hive(s) for s in pipeline.steps()]


# --- The README --------------------------------------------------------------------------------


def test_the_readme_names_every_file() -> None:
    readme = (STARTER / "README.md").read_text(encoding="utf-8")
    unnamed = [relative for relative in example_project.project_files(STARTER)
               if f"`{relative}`" not in readme]
    assert unnamed == []
