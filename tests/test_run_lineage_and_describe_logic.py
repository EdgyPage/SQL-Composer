"""A run's lineage and Hive, and describe_logic, by hand: Toolbox 8.6, ticket 08.

"make the lineage tracking a manual process" (the map's Q17): project.export_run_lineage
builds one Scheduled run as its notebook's defaults give it, sending nothing, and writes its
lineage into its folder, named by the time and the run; project.export_run_hive writes its
built Hive, in order, headed as the build prints it, into <name>.hql beside its notebook, to
read, never to edit (Q23). project.describe_logic prints each named table's logic functions,
their signatures and their docstrings' first sentences, to paste into Copilot (Q25). Each is a
cell of admin/scheduled_runs.ipynb.
"""

from __future__ import annotations

import contextlib
import io
from pathlib import Path

import pytest
from conftest import run_admin_notebook, toolbox_module
from test_project_lineage import LOGIC, NOW, RECORDING, files, new_run, one_line

from sqlglot_composer import notebooks, project, set_admin_log

STEM = "20261109-093000-weekly"
# mart.teams' logic, with Session settings sent before its writes.
WITH_SETTINGS = LOGIC["mart.teams"].replace(
    "from sqlglot_composer.example_database import jobs",
    "from sqlglot_composer import hive_settings\n"
    "from sqlglot_composer.example_database import jobs") + '''

def session_settings():
    return hive_settings("map_joins")
'''
# A Table notebook's logic cell for describe_logic: hints, defaults and docstrings, an
# imported function and one defined inside another.
DESCRIBED = '''
import datetime

from sqlglot_composer import (AS, FROM, INSERT_OVERWRITE, SELECT, Statement, Table,
                              count_rows, statement)
from sqlglot_composer.example_database import jobs

team_days = Table("mart.team_days", columns={"team": "string", "jobs": "bigint"},
                  location="/data/your_team/mart.db/team_days")


def write() -> Statement:
    """Step 3, every run: each team's jobs, counted
    on the day it runs. More of what it does.

    And a paragraph after."""
    return statement(INSERT_OVERWRITE(team_days), SELECT(jobs.team, AS(count_rows(), "jobs")),
                     FROM(jobs))


def week_totals(week_start: datetime.date, day: str = "mon", *teams: str) -> Statement:
    """Each team's jobs in the week from week_start."""

    def inner() -> None:
        """Not one of the cell's own functions."""

    return statement(SELECT(team_days.team), FROM(team_days))


def no_docstring(day):
    return day


async def fetched(day: str) -> str:
    """The rows fetched for a day, at the cell's top level as an async def."""
    return day
'''


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A Project with three Table folders, each reading the one before, worked in from
    admin/, as admin/scheduled_runs.ipynb is."""
    monkeypatch.setattr(toolbox_module("unchecked"), "now", lambda: NOW)
    set_admin_log()
    monkeypatch.chdir(tmp_path)
    project.start()
    tables = {**LOGIC, "mart.team_days": DESCRIBED}
    for name, logic in tables.items():
        template = name.replace(".", "_")
        (tmp_path / "admin" / "templates" / f"{template}.py").write_text(
            f"# %%\n# logic\n{logic}", encoding="utf-8")
        project.new_table(name, template=template)
    monkeypatch.chdir(tmp_path / "admin")
    return tmp_path


def run_folder(root: Path, name: str = "weekly") -> Path:
    """A Scheduled run's folder."""
    return root / "scheduled_runs" / name


def built_and_printed(root: Path, name: str = "weekly") -> str:
    """What the run's build prints, as its Build cell builds it."""
    return toolbox_module("project_lineage").built_run_of(root, name, "the test")[1]


# --- export_run_lineage -----------------------------------------------------------------------


def test_a_runs_lineage_goes_in_its_folder_named_by_the_time_and_the_run(
        started: Path) -> None:
    new_run(started, "weekly")
    report = one_line(project.export_run_lineage("weekly"))
    assert report == (
        f"Wrote scheduled_runs/weekly/lineage/{STEM}.html and its Markdown twin, {STEM}.md: "
        "the lineage of 3 Statements, mart.team_jobs, mart.teams and busiest, built as its "
        "Build cell builds them, with the defaults of its # parameters cell, sending nothing.")
    folder = run_folder(started) / "lineage"
    page = (folder / f"{STEM}.html").read_text(encoding="utf-8")
    markdown = (folder / f"{STEM}.md").read_text(encoding="utf-8")
    assert "<title>Lineage: the Scheduled run weekly</title>" in page
    assert markdown.startswith("# Lineage: the Scheduled run weekly\n\nMade by "
                               '`project.export_run_lineage("weekly")`.')
    assert ('Made by project.export_run_lineage("weekly") on 2026-11-09 09:30, from your '
            "scripts at commit ") in markdown
    # Each Statement the run sends, the writes its build adds among them.
    for name in ("mart.team_jobs", "mart.teams", "busiest"):
        assert f"## {name}" in markdown


def test_a_runs_session_settings_are_in_the_footer(started: Path) -> None:
    notebook = started / "tables" / "mart__teams" / "mart__teams.ipynb"
    notebooks.write_notebook(notebook, [("code", f"# logic\n{WITH_SETTINGS}")])
    new_run(started, "weekly")
    project.export_run_lineage("weekly")
    markdown = (run_folder(started) / "lineage" / f"{STEM}.md").read_text(encoding="utf-8")
    assert "Session settings sent before these Statements, one line at a time (map_joins)" in (
        markdown)


def test_what_makes_no_column_from_another_is_left_out_and_named(started: Path) -> None:
    new_run(started, "weekly", scheduled='''# scheduled
from sqlglot_composer import Table, create_table

teams = Table("mart.teams", columns={"team": "string", "jobs": "bigint"},
              location="/data/your_team/mart.db/teams")


def statements():
    return {"make": create_table(teams, may_exist=True),
            "busiest": project.load("mart.teams").busiest()}
''')
    report = one_line(project.export_run_lineage("weekly"))
    assert ("Not drawn, as it makes no column from another: make, create_table(...)'s "
            "Statement, which creates a table.") in report


def test_a_list_of_runs_writes_each_ones_lineage(started: Path) -> None:
    new_run(started, "weekly")
    new_run(started, "daily")
    report = one_line(project.export_run_lineage(["weekly", "daily"]))
    assert "scheduled_runs/weekly/lineage/" in report
    assert "scheduled_runs/daily/lineage/" in report
    assert (run_folder(started, "daily") / "lineage" / "20261109-093000-daily.md").is_file()


def test_a_run_that_doesnt_build_is_refused_as_the_build_refuses_it(started: Path) -> None:
    project.new_scheduled_run("weekly")  # its <...> left
    with pytest.raises(ValueError, match=r"cell 4 of scheduled_runs/weekly/weekly\.ipynb "
                                         r"isn't Python yet"):
        project.export_run_lineage("weekly")


def test_a_name_with_no_scheduled_run_is_refused_naming_close_ones(started: Path) -> None:
    new_run(started, "weekly")
    with pytest.raises(FileNotFoundError) as refused:
        project.export_run_lineage("weeky")
    message = " ".join(str(refused.value).split())
    assert 'project.export_run_lineage("weeky"): there is no Scheduled run named "weeky"' in (
        message)
    assert "Did you mean weekly?" in message


# --- export_run_hive --------------------------------------------------------------------------


def test_a_runs_hive_is_written_beside_its_notebook_headed_as_the_build_prints_it(
        started: Path) -> None:
    notebook = started / "tables" / "mart__teams" / "mart__teams.ipynb"
    notebooks.write_notebook(notebook, [("code", f"# logic\n{WITH_SETTINGS}")])
    new_run(started, "weekly")
    report = one_line(project.export_run_hive("weekly"))
    assert report == (
        "Wrote scheduled_runs/weekly/weekly.hql: the Hive of 3 Statements, in the order the "
        "run sends them, built as its Build cell builds them, with the defaults of its "
        "# parameters cell, sending nothing. It is to read, never to edit: the notebook "
        "builds its Hive again each time it runs.")
    text = (run_folder(started) / "weekly.hql").read_text(encoding="utf-8")
    header, _, steps = text.partition("\n\n-- 1 of 3: ")
    assert header.startswith("-- The Hive of the Scheduled run weekly, generated by")
    assert all(line.startswith("--") for line in header.splitlines())
    assert "never to edit" in " ".join(header.split())
    # What the build printed before the first Statement: the parameters as used.
    assert "-- Parameters, as this run uses them:\n--   START_FROM = \"\"" in header
    # Each Statement as the build prints it, its Session settings where it prints them.
    printed = built_and_printed(started)
    for heading in ("-- 1 of 3: mart.team_jobs (read by mart.teams)",
                    "-- 2 of 3: mart.teams (read by busiest)", "-- 3 of 3: busiest"):
        assert heading in text
        piece = text.split(heading)[1].split("\n\n-- ")[0]
        assert piece.strip() in printed
    assert "-- 2 of 3: mart.teams (read by busiest)\n" in text
    teams = text.split("-- 2 of 3: mart.teams (read by busiest)\n")[1]
    assert teams.index("SET ") < teams.index("INSERT OVERWRITE TABLE mart.teams")


def test_a_runs_hive_written_again_is_the_same_text(started: Path) -> None:
    new_run(started, "weekly")
    project.export_run_hive("weekly")
    first = (run_folder(started) / "weekly.hql").read_text(encoding="utf-8")
    project.export_run_hive("weekly")
    assert (run_folder(started) / "weekly.hql").read_text(encoding="utf-8") == first


def test_a_name_with_no_scheduled_run_is_refused_by_export_run_hive(started: Path) -> None:
    with pytest.raises(FileNotFoundError, match="there is no Scheduled run named"):
        project.export_run_hive("weekly")


# --- describe_logic ---------------------------------------------------------------------------


def test_describe_logic_gives_each_function_its_hints_and_first_sentence(
        started: Path) -> None:
    report = repr(project.describe_logic("mart.team_days"))
    assert report == "\n".join([
        '# mart.team_days: project.load("mart.team_days"), from the # logic cell of '
        "tables/mart__team_days/mart__team_days.ipynb",
        "def write() -> Statement:",
        '    """Step 3, every run: each team\'s jobs, counted on the day it runs."""',
        "def week_totals(week_start: datetime.date, day: str='mon', *teams: str) -> "
        "Statement:",
        '    """Each team\'s jobs in the week from week_start."""',
        "def no_docstring(day):",
        "    ...  # no docstring",
        "async def fetched(day: str) -> str:",
        '    """The rows fetched for a day, at the cell\'s top level as an async def."""',
    ])


def test_describe_logic_leaves_out_what_the_cell_imports(started: Path) -> None:
    report = repr(project.describe_logic("mart.team_days"))
    assert "count_rows" not in report
    assert "inner" not in report


def test_describe_logic_takes_a_list_each_table_in_turn(started: Path) -> None:
    report = repr(project.describe_logic(["mart.teams", "mart.team_days"]))
    teams, team_days = report.split("\n\n")
    assert teams.startswith("# mart.teams: ")
    assert "def busiest():" in teams
    assert team_days.startswith("# mart.team_days: ")


def test_describe_logic_sends_nothing_and_changes_no_file(started: Path) -> None:
    before = files(started)
    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):
        project.describe_logic("mart.teams")
    assert files(started) == before
    assert printed.getvalue() == ""


def test_a_name_with_no_table_folder_is_refused_naming_close_ones(started: Path) -> None:
    with pytest.raises(FileNotFoundError) as refused:
        project.describe_logic(["mart.teams", "mart.team"])
    message = " ".join(str(refused.value).split())
    assert ('project.describe_logic(["mart.teams", "mart.team"]): there is no Table folder '
            'named "mart.team"') in message
    assert "Did you mean mart.teams" in message


def test_a_name_close_to_none_is_refused_naming_each_table_folder(started: Path) -> None:
    with pytest.raises(FileNotFoundError) as refused:
        project.describe_logic("ops.something_else")
    message = " ".join(str(refused.value).split())
    assert ("Check the name: the Table folders are mart.team_count, mart.team_days, "
            "mart.team_jobs and mart.teams.") in message


def test_a_logic_cell_that_isnt_python_yet_is_refused_as_load_refuses_it(
        started: Path) -> None:
    project.new_table("mart.not_yet")
    with pytest.raises(ValueError, match=r'project\.describe_logic\("mart\.not_yet"\): the '
                                         r"logic cell of .* isn't Python yet"):
        project.describe_logic("mart.not_yet")


# --- admin/scheduled_runs.ipynb ---------------------------------------------------------------


def test_the_scheduled_runs_notebook_makes_each_run_named_in_new_runs(started: Path) -> None:
    notebook = started / "admin" / "scheduled_runs.ipynb"
    code = [text for kind, text in notebooks.read_cells(notebook) if kind == "code"]
    names = [index for index, text in enumerate(code) if text.startswith("NEW_RUNS = []")]
    assert len(names) == 1
    assert "project.new_scheduled_run(NEW_RUNS)" in code[names[0]]
    code[1] = RECORDING
    code[names[0]] = code[names[0]].replace("NEW_RUNS = []", 'NEW_RUNS = ["daily"]', 1)
    run_admin_notebook(notebook, code[:names[0] + 1])
    assert (run_folder(started, "daily") / "daily.ipynb").is_file()


def test_the_scheduled_runs_notebook_runs_each_by_hand_and_sends_nothing(started: Path) -> None:
    new_run(started, "weekly")
    notebook = started / "admin" / "scheduled_runs.ipynb"
    code = [text for kind, text in notebooks.read_cells(notebook) if kind == "code"]
    names = [index for index, text in enumerate(code) if text.startswith("RUNS = []")]
    assert len(names) == 1
    for call in ("project.export_run_lineage(RUNS)", "project.export_run_hive(RUNS)",
                 "project.describe_logic(TABLES)"):
        assert any(call in text for text in code), call
    code[1] = RECORDING
    code[names[0]] = code[names[0]].replace("RUNS = []", 'RUNS = ["weekly"]', 1).replace(
        "TABLES = []", 'TABLES = ["mart.teams"]', 1)
    before = files(started)
    run_admin_notebook(notebook, [*code, "assert SENT == [], SENT"])
    added = sorted(set(files(started)) - set(before))
    assert added == ["admin/lineage/20261109-093000-project.html",
                     "admin/lineage/20261109-093000-project.md",
                     f"scheduled_runs/weekly/lineage/{STEM}.html",
                     f"scheduled_runs/weekly/lineage/{STEM}.md",
                     "scheduled_runs/weekly/weekly.hql"]
