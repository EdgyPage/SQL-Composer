"""The Example projects in `example_projects/`: Projects that are current, whose Table
notebooks' logic loads and writes each table, into the Partitions its rows fill, a Partition it
names, or whole, and whose rows give the numbers pandas gives for the same rows.

Each project is written again by `tools/example_project.py` into a temporary folder and
compared with the committed one, file by file, line endings aside. The rest runs on a copy of
each project, as a notebook in it runs: `project.load` reads each Table notebook's logic cell,
and `project.run_tables` orders and prints the writes. A preview that reads a Saved table,
which only a warehouse holds, runs with the Saved table stood in for by the rows the notebook
that writes it gives for the day.
"""

from __future__ import annotations

import csv
import datetime
import json
import re
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pytest

import example_project
from conftest import (
    ROOT,
    example_rows,
    previewed_days,
    run_admin_notebook,
    rows_of_days,
    standing_in,
    without_the_write,
)
from sqlglot_composer import (
    all_of,
    between,
    equals,
    example_database,
    project,
    run,
    set_admin_log,
    statement,
    to_hive,
)
from sqlglot_composer.project import TableLogic

DAY = "2026-09-24"
DAYS = ("2026-09-23", "2026-09-24")
I_DAYS = ("2026-09-14", "2026-09-18", "2026-09-24")


def write_project(into: Path, name: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(ROOT / "tools" / "example_project.py"), "--project", name,
         "--into", str(into)], capture_output=True, text=True, check=False)


@pytest.fixture(scope="module")
def projects(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Path]:
    """A copy of each Example project, so loading its notebooks writes nothing in the repo."""
    folder = tmp_path_factory.mktemp("example_projects")
    for name in example_project.PROJECTS:
        shutil.copytree(ROOT / "example_projects" / name, folder / name)
    return {name: folder / name for name in example_project.PROJECTS}


@pytest.fixture
def inside(projects: dict[str, Path], monkeypatch: pytest.MonkeyPatch) -> Callable[..., Path]:
    """Work in a project's admin/ folder, as its admin notebooks do."""
    set_admin_log()

    def go(name: str) -> Path:
        monkeypatch.chdir(projects[name] / "admin")
        return projects[name]

    return go


def logic(inside: Callable[..., Path], name: str, table: str) -> TableLogic:
    inside(name)
    return project.load(table)


def reading_the_day(inside: Callable[..., Path], table: str, day: str) -> TableLogic:
    """The logic of a starter notebook, its READS changed to read `day`, as a user changes it
    to write another day."""
    logic_of = logic(inside, "starter", table)
    jobs_runs, alerts = example_database.job_runs, example_database.run_alerts
    before = (datetime.date.fromisoformat(day) - datetime.timedelta(days=1)).isoformat()
    reads = {"mart.alerts_per_severity": equals(alerts.dt, day),
             "mart.daily_job_runs": equals(jobs_runs.dt, day),
             "mart.alerts_per_job": all_of(equals(alerts.dt, day),
                                           between(jobs_runs.dt, before, day))}
    logic_of.rows.__globals__["READS"] = reads[table]
    return logic_of


def day_rows(logic_of: TableLogic, day: str) -> pd.DataFrame:
    """The rows the table's write would save for the day, on the Example database, without
    their day, dt, the column each selects last, which holds the day alone."""
    rows = run(rows_of_days(logic_of, day, day), query=example_database.query)
    assert set(rows.pop("dt")) <= {day, day.replace("-", "")}
    return rows


# --- The committed projects -------------------------------------------------------------------


def test_every_example_project_has_a_folder() -> None:
    assert sorted(path.name for path in (ROOT / "example_projects").iterdir()) == sorted(
        example_project.PROJECTS)


@pytest.mark.parametrize("name", example_project.PROJECTS)
def test_the_committed_project_is_what_the_generator_writes(tmp_path: Path, name: str) -> None:
    done = write_project(tmp_path / name, name)
    assert done.returncode == 0, done.stderr
    committed = ROOT / "example_projects" / name
    assert example_project.project_files(tmp_path / name) == example_project.project_files(
        committed)
    for relative in example_project.project_files(committed):
        written = (tmp_path / name / relative).read_text(encoding="utf-8")
        assert written == (committed / relative).read_text(encoding="utf-8"), relative


def test_the_generator_refuses_a_folder_that_holds_anything(tmp_path: Path) -> None:
    (tmp_path / "mine.txt").write_text("mine", encoding="utf-8")
    done = write_project(tmp_path, "starter")
    assert done.returncode == 2
    assert "isn't an empty folder" in done.stderr
    assert [path.name for path in tmp_path.iterdir()] == ["mine.txt"]


def test_filling_in_refuses_a_table_reference_without_its_todo_line() -> None:
    filling = example_project.FILLED_IN["starter"]["ops.jobs"]
    with pytest.raises(example_project.TodoMissing, match="0 lines starting"):
        example_project.filled_in('"""ops.jobs - mine."""\n', "ops.jobs", filling)


@pytest.mark.parametrize("name", example_project.PROJECTS)
def test_a_project_has_no_todo_left_and_nothing_unregistered(
        inside: Callable[..., Path], name: str) -> None:
    root = inside(name)
    for path in (root / "references").glob("ops__*.py"):
        assert "# TODO" not in path.read_text(encoding="utf-8"), path.name
    assert repr(project.check()) == ("Every Table folder, Table reference and Building block is "
                                     "registered, and each one registered is there.")


@pytest.mark.parametrize("name", example_project.PROJECTS)
def test_each_building_block_was_made_by_new_block(name: str) -> None:
    """The Admin log shows new_block making each one, and the registry lists it."""
    root = ROOT / "example_projects" / name
    blocks = sorted(path.stem for path in (root / "building_blocks").glob("*.py"))
    assert blocks
    log = (root / "admin" / "admin_log.md").read_text(encoding="utf-8")
    for block in blocks:
        assert (f'- Call: `project.new_block("{block}")`\n'
                f"- Files: created building_blocks/{block}.py\n") in log
    with open(root / "admin" / "registry.csv", encoding="utf-8", newline="") as rows:
        assert sorted(row["table"] for row in csv.DictReader(rows)
                      if row["kind"] == "building_block") == blocks
    readme = " ".join((root / "README.md").read_text(encoding="utf-8").split())
    assert "project.new_block(" in readme
    assert "written by hand: no Project action" not in readme


@pytest.mark.needs_example_database
@pytest.mark.parametrize("name", example_project.PROJECTS)
def test_the_check_references_notebook_checks_each_table(
        projects: dict[str, Path], capsys: pytest.CaptureFixture[str], name: str) -> None:
    """Each ops table matches its Table reference, and the Saved tables, which only a warehouse
    holds, are reported as not found, as the starter README says."""
    set_admin_log()
    root = projects[name]
    capsys.readouterr()
    said = run_admin_notebook(root / "admin" / "check_references.ipynb", capsys=capsys)
    for table in example_project.FILLED_IN[name]:
        assert f"{table} matches its Table reference.\n" in said
    for table, _ in example_project.SAVED_TABLES[name]:
        assert f"{table}: DESCRIBE failed, so nothing was compared." in said
    if name == "starter":
        assert "ops.jobs: the key (job_id) holds.\n" in said
    else:
        assert "ops.team_notes has no Key, so there is no Key to check.\n" in said
        assert "ops.region_costs is partitioned by region and dt, so its Key" in said


@pytest.mark.needs_example_database
def test_the_check_references_notebooks_last_cell_checks_a_partitioned_tables_key(
        projects: dict[str, Path], capsys: pytest.CaptureFixture[str]) -> None:
    set_admin_log()
    notebook = projects["starter"] / "admin" / "check_references.ipynb"
    code = [text for kind, text in notebook_cells(notebook) if kind == "code"]
    last = "\n".join(line.removeprefix("# ") for line in code[-1].splitlines()
                     if line.startswith("# from") or line.startswith("# print"))
    capsys.readouterr()
    said = run_admin_notebook(notebook, [code[0], code[1].split("\n# The Reference")[0], last],
                              capsys=capsys)
    assert said == ("ops.job_runs matches its Table reference.\n"
                    "ops.job_runs: the key (run_id) holds where job_runs.dt = '2026-09-24'.\n")


def notebook_cells(path: Path) -> list[tuple[str, str]]:
    return [(cell["cell_type"], "".join(cell["source"]))
            for cell in json.loads(path.read_text(encoding="utf-8"))["cells"]]


@pytest.mark.parametrize("name", example_project.PROJECTS)
def test_each_table_has_its_lineage_named_by_the_time(name: str) -> None:
    for table, _ in example_project.SAVED_TABLES[name]:
        stem = table.replace(".", "__")
        folder = ROOT / "example_projects" / name / "tables" / stem / "lineage"
        assert sorted(path.name for path in folder.iterdir()) == [
            f"20260925-060000-{stem}.html", f"20260925-060000-{stem}.md"]


def test_a_tables_lineage_across_tables_draws_the_tables_it_reads() -> None:
    lineage = (ROOT / "example_projects" / "starter" / "tables" / "mart__team_day" / "lineage" /
               "20260925-060000-mart__team_day.md").read_text(encoding="utf-8")
    assert "ops.job_runs" in lineage and "mart.daily_job_runs" in lineage


def test_the_reference_sheet_lists_every_column_and_its_aliases() -> None:
    path = ROOT / "example_projects" / "starter" / "references" / "reference_sheet.csv"
    with open(path, encoding="utf-8", newline="") as sheet:
        rows = list(csv.DictReader(sheet))
    assert sorted({row["table"] for row in rows}) == [
        "mart.alerts_per_job", "mart.alerts_per_severity", "mart.daily_job_runs",
        "mart.team_day", "ops.job_runs", "ops.jobs", "ops.run_alerts"]
    # Each Saved table is partitioned by its day, dt, and nothing else.
    assert {(row["table"], row["column"]) for row in rows if row["partition"] == "yes"
            and row["table"].startswith("mart.")} == {
        ("mart.alerts_per_job", "dt"), ("mart.alerts_per_severity", "dt"),
        ("mart.daily_job_runs", "dt"), ("mart.team_day", "dt")}
    aliases = {(row["table"], row["column"]): row["aliases"] for row in rows if row["aliases"]}
    assert aliases == {("ops.job_runs", "duration_mins"): "minutes",
                       ("ops.job_runs", "status"): "failed (a condition)",
                       ("ops.run_alerts", "severity"): "high (a condition)"}


# --- Each Table notebook's logic ------------------------------------------------------------


# How each Saved table is written: the Partitions its rows fill, a Partition named, or whole.
WRITTEN = {"mart.budget_overruns": " PARTITION(region = 'eu')", "mart.job_notes": ""}


@pytest.mark.parametrize(("name", "table"), [
    (name, table) for name in example_project.PROJECTS
    for table, _ in example_project.SAVED_TABLES[name]])
def test_each_notebooks_logic_writes_its_table(
        inside: Callable[..., Path], name: str, table: str) -> None:
    logic_of = logic(inside, name, table)
    writes = logic_of.write()
    # A write() may give a list, a write per region: the first is the one preview() shows.
    written = to_hive(writes[0] if isinstance(writes, list) else writes)
    # Most fill dt from their rows; mart.budget_overruns names its region, and mart.job_notes,
    # which isn't partitioned, is written whole.
    partition = WRITTEN.get(table, " PARTITION(dt)")
    assert f"INSERT OVERWRITE TABLE {table}{partition}\n" in written
    # The preview is the SELECT the write sends.
    assert without_the_write(written) == to_hive(logic_of.preview())


def test_an_incremental_table_writes_its_last_3_days(inside: Callable[..., Path]) -> None:
    hive = to_hive(logic(inside, "intermediate", "mart.job_day_costs").write())
    # One write, its rows the last 3 days, each written into its own partition.
    assert hive.count("INSERT OVERWRITE TABLE") == 1
    assert re.search(r"BETWEEN '2026-?09-?22' AND '2026-?09-?24'", hive), hive


@pytest.mark.needs_example_database
def test_a_write_of_several_days_writes_each_day_what_a_write_of_the_day_writes(
        inside: Callable[..., Path]) -> None:
    """A write of several days is one write: the rows a write of each day alone saves, put
    together, which the Example database shows."""
    logic_of = logic(inside, "intermediate", "mart.job_day_facts")
    days = ["2026-09-22", "2026-09-23", DAY]
    write = to_hive(logic_of.write_days(days[0], days[-1]))
    assert "INSERT OVERWRITE TABLE mart.job_day_facts PARTITION(dt)\n" in write
    order = ["dt", "job_id"]
    same(example_database.query(without_the_write(write)).sort_values(order),
         previewed_days(logic_of, days).sort_values(order))


def test_a_write_per_region_names_each_regions_partition(inside: Callable[..., Path]) -> None:
    writes = logic(inside, "intermediate", "mart.budget_overruns").write()
    assert [to_hive(write).split("\n")[0] for write in writes] == [
        "INSERT OVERWRITE TABLE mart.budget_overruns PARTITION(region = 'eu')",
        "INSERT OVERWRITE TABLE mart.budget_overruns PARTITION(region = 'us')"]


@pytest.mark.parametrize(("name", "reader", "read"), [
    ("starter", "mart.team_day", ["mart.daily_job_runs"]),
    ("intermediate", "mart.team_days", ["mart.job_day_costs", "mart.job_day_facts"]),
])
def test_run_tables_prints_each_write_writers_first(
        inside: Callable[..., Path], capsys: pytest.CaptureFixture[str], name: str, reader: str,
        read: list[str]) -> None:
    inside(name)
    report = project.run_tables()
    headings = [line.split(": ", 1)[1] for line in capsys.readouterr().out.splitlines()
                if re.match(r"-- \d+ of \d+: ", line)]
    tables = [table for table, _ in example_project.SAVED_TABLES[name]]
    assert sorted(set(headings)) == sorted(tables)
    assert headings.index(reader) > max(len(headings) - 1 - headings[::-1].index(table)
                                        for table in read)
    assert "sent nothing" in repr(report)


# --- The numbers each preview gives, against pandas ------------------------------------------


def same(got: pd.DataFrame, expected: pd.DataFrame) -> None:
    pd.testing.assert_frame_equal(got.reset_index(drop=True).astype("int64", errors="ignore"),
                                  expected.reset_index(drop=True).astype("int64",
                                                                          errors="ignore"),
                                  check_dtype=False)


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
    return (joined.groupby("job_id")
            .agg(alerts=("alert_id", "size"), high_alerts=("high", "sum"))
            .reset_index())


def team_runs_on(day: str) -> pd.DataFrame:
    """Each team's runs, failed runs and minutes on the day, in pandas."""
    teams = example_rows("jobs")[["job_id", "team"]]
    return (runs_on(day).merge(teams, on="job_id")
            .groupby("team")[["runs", "failed_runs", "minutes"]].sum().reset_index())


def costs_on(day: str) -> pd.DataFrame:
    """Each job's cost on the day, every region added up, in pandas: NULL with no bill in."""
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
               .agg(events=("event_id", "size"), runs=("start", "sum"),
                    minutes=("ended", "sum"))
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


@pytest.mark.needs_example_database
@pytest.mark.parametrize("day", DAYS)
def test_daily_job_runs_previews_each_jobs_runs(inside: Callable[..., Path], day: str) -> None:
    same(day_rows(reading_the_day(inside, "mart.daily_job_runs", day), day),
         runs_on(day))


@pytest.mark.needs_example_database
@pytest.mark.parametrize("day", DAYS)
def test_alerts_per_job_previews_each_jobs_alerts(
        inside: Callable[..., Path], day: str) -> None:
    same(day_rows(reading_the_day(inside, "mart.alerts_per_job", day), day),
         alerts_on(day))


@pytest.mark.needs_example_database
@pytest.mark.parametrize("day", DAYS)
def test_alerts_per_severity_previews_each_severitys_alerts(
        inside: Callable[..., Path], day: str) -> None:
    alerts = example_rows("run_alerts")
    expected = (alerts[alerts.dt == day].groupby("severity")
                .agg(alerts=("alert_id", "size")).reset_index())
    same(day_rows(reading_the_day(inside, "mart.alerts_per_severity", day), day), expected)


@pytest.mark.needs_example_database
@pytest.mark.parametrize("day", DAYS)
def test_team_day_groups_each_teams_runs_from_job_runs(
        inside: Callable[..., Path], day: str) -> None:
    check = logic(inside, "starter", "mart.team_day").team_runs_from_job_runs(
        equals(example_database.job_runs.dt, day))
    same(run(check, query=example_database.query), team_runs_on(day))


@pytest.mark.needs_example_database
@pytest.mark.parametrize("day", I_DAYS)
def test_job_day_costs_previews_each_jobs_cost(inside: Callable[..., Path], day: str) -> None:
    same(day_rows(logic(inside, "intermediate", "mart.job_day_costs"), day), costs_on(day))


@pytest.mark.needs_example_database
@pytest.mark.parametrize("day", I_DAYS)
def test_job_day_facts_previews_each_jobs_day_with_its_team_then(
        inside: Callable[..., Path], day: str) -> None:
    same(day_rows(logic(inside, "intermediate", "mart.job_day_facts"), day), facts_on(day))


@pytest.mark.needs_example_database
def test_job_day_facts_counts_a_job_for_the_team_it_had_then(
        inside: Callable[..., Path]) -> None:
    logic_of = logic(inside, "intermediate", "mart.job_day_facts")
    teams = {day: day_rows(logic_of, day).set_index("job_id").team.get(3)
             for day in ("2026-09-14", "2026-09-18")}
    assert teams == {"2026-09-14": "data", "2026-09-18": "finance"}


@pytest.mark.needs_example_database
@pytest.mark.parametrize("day", I_DAYS)
def test_team_days_groups_each_teams_day_from_job_events(
        inside: Callable[..., Path], day: str) -> None:
    check = logic(inside, "intermediate", "mart.team_days").team_day_from_job_events(day)
    same(run(check, query=example_database.query), team_day_on(day, with_costs=False))


@pytest.mark.needs_example_database
@pytest.mark.parametrize("day", I_DAYS)
def test_team_days_previews_each_teams_day_from_both_saved_tables(
        inside: Callable[..., Path], day: str) -> None:
    """The Saved tables only a warehouse holds are stood in for by the rows their notebooks
    give for the day."""
    saved = {"job_day_facts": previewed_days(logic(inside, "intermediate",
                                                   "mart.job_day_facts"), [day]),
             "job_day_costs": previewed_days(logic(inside, "intermediate",
                                                   "mart.job_day_costs"), [day])}
    rows = rows_of_days(logic(inside, "intermediate", "mart.team_days"), day, day)
    got = example_database.query(standing_in(to_hive(rows), saved))
    assert set(got.pop("dt")) == {day}
    same(got, team_day_on(day))


@pytest.mark.needs_example_database
def test_the_quality_checks_find_no_repeated_event(inside: Callable[..., Path]) -> None:
    checks = logic(inside, "intermediate", "mart.job_events_checks")
    assert len(run(checks.repeated_keys(), query=example_database.query)) == 0
    events = example_rows("job_events")
    counted = run(checks.preview(), query=example_database.query)
    assert list(counted.row_count) == [len(events[events.dt == DAY])]


def overruns_in(region: str) -> pd.DataFrame:
    """Each job's budget in the region, its days of costs and the days over budget, over the
    Example database's 14 days, in pandas: a NULL cost is never over."""
    costs = example_rows("region_costs")
    budgets = example_rows("region_budgets")
    joined = costs[costs.region == region].merge(budgets[budgets.region == region][
        ["job_id", "budget_cents"]], on="job_id")
    joined = joined.assign(over=joined.cost_cents > joined.budget_cents)
    return (joined.groupby(["job_id", "budget_cents"])
            .agg(days=("dt", "size"), days_over=("over", "sum")).reset_index())


@pytest.mark.needs_example_database
@pytest.mark.parametrize("region", ["eu", "us"])
def test_budget_overruns_counts_each_jobs_days_over_budget(
        inside: Callable[..., Path], region: str) -> None:
    logic_of = logic(inside, "intermediate", "mart.budget_overruns")
    same(run(statement(*logic_of.rows(region)), query=example_database.query),
         overruns_in(region))


@pytest.mark.needs_example_database
def test_job_notes_puts_each_note_beside_each_job_its_team_owned_that_day(
        inside: Callable[..., Path]) -> None:
    got = run(logic(inside, "intermediate", "mart.job_notes").preview(),
              query=example_database.query)
    owners = example_rows("job_owners")
    expected = example_rows("team_notes").merge(
        owners, left_on=["team", "written_on"], right_on=["team", "dt"])
    expected = expected[["job_id", "team", "note", "written_on"]]
    order = ["job_id", "written_on", "note"]
    same(got.sort_values(order), expected.sort_values(order))
    # A note is about every job its team owned that day: report_build was data's until
    # 2026-09-18, so the note of 2026-09-15 names it beside nightly_load.
    assert sorted(got[got.written_on == "2026-09-15"].job_id) == [1, 3]
