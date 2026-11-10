"""The Project's lineage and its loops, by hand: Toolbox 8.6, ticket 07.

"make the lineage tracking a manual process. I don't want to have this happen every time a
scheduled run executes" (the map's Q17). project.export_project_lineage draws every Saved
table, an arrow from each table to each that reads it, and the Scheduled runs writing each,
a table two runs write marked and a loop drawn red; it builds each run from its notebook,
sending nothing. project.check reports a loop among the Project's tables. Both are cells of
admin/scheduled_runs.ipynb, which start() makes.
"""

from __future__ import annotations

import datetime
from pathlib import Path

import pytest
from conftest import run_admin_notebook, toolbox_module

from sqlglot_composer import notebooks, project, set_admin_log
from sqlglot_composer.project_templates import SCHEDULED_RUN

NOW = datetime.datetime(2026, 11, 9, 9, 30, 0)
STEM = "20261109-093000-project"

# Each Table notebook's logic cell, by its table: mart.team_jobs reads ops.jobs, outside the
# Project; mart.teams reads mart.team_jobs; mart.team_count reads mart.teams.
TABLES = '''
from sqlglot_composer import (FROM, GROUP_BY, INSERT_OVERWRITE, SELECT, AS, Table, count_rows,
                              run_value, statement, WHERE, at_least)
from sqlglot_composer.example_database import jobs

team_jobs = Table("mart.team_jobs", columns={"job_id": "bigint", "team": "string"},
                  location="/data/your_team/mart.db/team_jobs")
teams = Table("mart.teams", columns={"team": "string", "jobs": "bigint"},
              location="/data/your_team/mart.db/teams")
team_count = Table("mart.team_count", columns={"teams": "bigint"},
                   location="/data/your_team/mart.db/team_count")
'''
LOGIC = {
    "mart.team_jobs": TABLES + '''

def first_job() -> int:
    return 1


def write():
    return statement(INSERT_OVERWRITE(team_jobs), SELECT(jobs.job_id, jobs.team), FROM(jobs),
                     WHERE(at_least(jobs.job_id, run_value(first_job))))
''',
    "mart.teams": TABLES + '''

def write():
    return statement(INSERT_OVERWRITE(teams), SELECT(team_jobs.team, AS(count_rows(), "jobs")),
                     FROM(team_jobs), GROUP_BY(team_jobs.team))


def busiest():
    return statement(SELECT(teams.team, teams.jobs), FROM(teams))
''',
    "mart.team_count": TABLES + '''

def write():
    return statement(INSERT_OVERWRITE(team_count), SELECT(AS(count_rows(), "teams")),
                     FROM(teams))
''',
}
# mart.team_jobs's write, reading mart.teams, which reads it: a loop.
LOOPING = TABLES + '''

def write():
    return statement(INSERT_OVERWRITE(team_jobs), SELECT(AS(teams.jobs, "job_id"), teams.team),
                     FROM(teams))
'''
# A Scheduled run's # scheduled cell: mart.teams' busiest(), whose writes the build adds.
BUSIEST = '''# scheduled
def statements():
    return {"busiest": project.load("mart.teams").busiest()}
'''
# admin/scheduled_runs.ipynb's connect cell, given a connection that keeps each Hive sent.
RECORDING = '''from warehouse import connect

SENT = []


class Recording:
    def query(self, hive: str) -> None:
        SENT.append(hive)

    def execute(self, hive: str) -> None:
        SENT.append(hive)


connect(Recording())'''
# A Scheduled run's cells, counting every cell as Jupyter does: its parameters, its
# # scheduled cell and its Build cell.
PARAMETERS_CELL, SCHEDULED_CELL, BUILD_CELL = 2, 4, 5


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A Project with three Table folders, each reading the one before, worked in from
    admin/, as admin/scheduled_runs.ipynb is."""
    monkeypatch.setattr(toolbox_module("unchecked"), "now", lambda: NOW)
    set_admin_log()
    monkeypatch.chdir(tmp_path)
    project.start()
    for name, logic in LOGIC.items():
        template = name.replace(".", "_")
        (tmp_path / "admin" / "templates" / f"{template}.py").write_text(
            f"# %%\n# logic\n{logic}", encoding="utf-8")
        project.new_table(name, template=template)
    monkeypatch.chdir(tmp_path / "admin")
    return tmp_path


def new_run(root: Path, name: str, scheduled: str = BUSIEST, build: str = "") -> Path:
    """A Scheduled run, its # scheduled cell `scheduled`, and its Build cell `build` if given:
    its notebook."""
    project.new_scheduled_run(name)
    notebook = root / "scheduled_runs" / name / f"{name}.ipynb"
    notebooks.write_cell_text(notebook, SCHEDULED_CELL, scheduled)
    if build:
        notebooks.write_cell_text(notebook, BUILD_CELL, build)
    return notebook


def make_a_loop(root: Path) -> None:
    """mart.team_jobs's logic made to read mart.teams, which reads it."""
    notebooks.write_notebook(root / "tables" / "mart__team_jobs" / "mart__team_jobs.ipynb",
                             [("code", f"# logic\n{LOOPING}")])


def files(root: Path) -> dict[str, str]:
    """Every file of the Project, by its path, as text: to tell nothing changed."""
    return {path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
            for path in sorted(root.rglob("*")) if path.is_file()}


def exported(root: Path) -> tuple[str, str]:
    """The lineage export_project_lineage wrote: the HTML page, then its Markdown twin."""
    folder = root / "admin" / "lineage"
    return ((folder / f"{STEM}.html").read_text(encoding="utf-8"),
            (folder / f"{STEM}.md").read_text(encoding="utf-8"))


def one_line(report: project.ProjectReport) -> str:
    """A report's lines as one line, as a reader reads them."""
    return " ".join(repr(report).split())


# --- check ------------------------------------------------------------------------------------


def test_check_reports_a_loop_naming_each_table_and_its_logic_cell(started: Path) -> None:
    make_a_loop(started)
    before = files(started)
    report = repr(project.check())
    assert ("A loop among your tables: mart.team_jobs reads mart.teams; mart.teams reads "
            "mart.team_jobs. So none of them can be written first") in " ".join(report.split())
    assert "  mart.team_jobs: tables/mart__team_jobs/mart__team_jobs.ipynb" in report
    assert "  mart.teams: tables/mart__teams/mart__teams.ipynb" in report
    # mart.team_count only waits on the loop: it isn't in it.
    assert "mart.team_count:" not in report
    assert files(started) == before


def test_check_says_nothing_of_a_loop_when_there_is_none(started: Path) -> None:
    assert "loop" not in repr(project.check())


def test_check_passes_over_a_table_whose_logic_isnt_filled_in_yet(started: Path) -> None:
    project.new_table("mart.not_yet")  # the saved_table Template, its <...> left
    make_a_loop(started)
    report = repr(project.check())
    assert "A loop among your tables" in report
    assert "mart.not_yet" not in report


def test_check_names_a_table_whose_logic_fails_on_a_line(started: Path) -> None:
    spelt_wrong = LOGIC["mart.teams"].replace("FROM(team_jobs)", "FROM(team_job)")
    notebooks.write_notebook(started / "tables" / "mart__teams" / "mart__teams.ipynb",
                             [("code", f"# logic\n{spelt_wrong}")])
    report = repr(project.check())
    # Passed over in looking for a loop, but named, with what stops it, on one line.
    passed_over = [line for line in report.splitlines() if "mart.teams" in line]
    assert passed_over == [
        "Passed over, as its logic doesn't load: mart.teams: name 'team_job' is not defined"]


# --- export_project_lineage -------------------------------------------------------------------


def test_the_lineage_draws_every_table_and_an_arrow_to_each_that_reads_it(
        started: Path) -> None:
    report = one_line(project.export_project_lineage())
    assert report == (f"Wrote admin/lineage/{STEM}.html and its Markdown twin, {STEM}.md: 4 "
                      "tables and 0 Scheduled runs.")
    page, markdown = exported(started)
    assert "| `ops.jobs` | read, not written here | mart.team_jobs | - |" in markdown
    assert "| `mart.teams` | Table folder | mart.team_count | - |" in markdown
    # Each table's box, by its place in name order, and an arrow from each read.
    ids = {"mart.team_count": "n0", "mart.team_jobs": "n1", "mart.teams": "n2",
           "ops.jobs": "n3"}
    for read, written in [("ops.jobs", "mart.team_jobs"), ("mart.team_jobs", "mart.teams"),
                          ("mart.teams", "mart.team_count")]:
        assert f"  {ids[read]} --> {ids[written]}" in markdown
    assert markdown.count(" --> ") == 3
    assert page.count('<path class="e"') == 3
    assert page.count('<g class="n ') == 4
    assert "<script" not in page
    assert "A loop among your tables" not in markdown
    assert '<p class="loopnote">' not in page


def test_each_run_writing_a_table_is_named_on_it_and_two_mark_it(started: Path) -> None:
    new_run(started, "weekly")
    new_run(started, "daily", scheduled='''# scheduled
def statements():
    return {"count": project.load("mart.team_count").write()}
''')
    report = one_line(project.export_project_lineage())
    assert ("Written by more than one Scheduled run, marked: mart.team_jobs, by weekly and "
            "daily.") in report
    assert "Written by more than one Scheduled run, marked: mart.teams, by weekly and daily." \
        in report
    page, markdown = exported(started)
    assert "| `mart.teams` | Table folder | mart.team_count | weekly, daily ⚠ |" in markdown
    assert "| `mart.team_count` | Table folder | - | daily |" in markdown
    assert "<br/><small>written by weekly and daily</small>" in markdown
    assert '<g class="n folder shared"' in page
    # Each run's Statements, in the order it sends them, headed as the build heads them.
    weekly = markdown.split("### weekly")[1].split("###")[0]
    assert weekly.split("What it sends, in order:")[1].split() == [
        "-", "1", "of", "3:", "mart.team_jobs", "(read", "by", "mart.teams)",
        "-", "2", "of", "3:", "mart.teams", "(read", "by", "busiest)",
        "-", "3", "of", "3:", "busiest"]


def test_a_loop_is_drawn_red_and_its_tables_listed_at_the_top(started: Path) -> None:
    make_a_loop(started)
    report = one_line(project.export_project_lineage())
    assert ("A loop, drawn red: mart.team_jobs and mart.teams. project.check() names the "
            "logic cell to mend.") in report
    page, markdown = exported(started)
    top = markdown.split("## Graph")[0]
    assert "A loop among your tables: mart.team_jobs and mart.teams." in top
    assert ('<p class="loopnote">A loop among your tables: mart.team_jobs and '
            "mart.teams.") in page
    assert page.count('<path class="e loop"') == 2
    assert page.count(" loop\" transform") == 2
    assert "  linkStyle " in markdown


def test_a_run_left_as_its_template_made_it_is_shown_not_raised(started: Path) -> None:
    project.new_scheduled_run("weekly")
    report = one_line(project.export_project_lineage())
    assert ("Not built, as the page shows: weekly: project.export_project_lineage(): cell 4 of "
            "scheduled_runs/weekly/weekly.ipynb isn't Python yet, at its line ") in report
    _, markdown = exported(started)
    weekly = markdown.split("### weekly")[1]
    assert weekly.lstrip().startswith("Not built, so nothing it writes is drawn:")
    assert "Fill in every <...> in the code cells of scheduled_runs/weekly/weekly.ipynb" in (
        " ".join(weekly.split()))


def test_a_table_folder_whose_logic_doesnt_load_is_shown_not_raised(started: Path) -> None:
    project.new_table("mart.not_yet")
    report = one_line(project.export_project_lineage())
    assert "Passed over, as its logic doesn't load: mart.not_yet: project.load(" in report
    page, markdown = exported(started)
    assert "## Table folders passed over" in markdown
    assert "its logic doesn&#x27;t load" in page


def test_nothing_is_sent_and_no_other_file_changes(started: Path) -> None:
    new_run(started, "weekly")
    before = files(started)
    notebook = started / "admin" / "scheduled_runs.ipynb"
    code = [text for kind, text in notebooks.read_cells(notebook) if kind == "code"]
    # Its connect cell given a connection that keeps what it is sent, and a last cell
    # checking it was sent nothing.
    code[1] = RECORDING
    run_admin_notebook(notebook, [*code, "assert SENT == [], SENT"])
    after = files(started)
    assert sorted(set(after) - set(before)) == [f"admin/lineage/{STEM}.html",
                                                f"admin/lineage/{STEM}.md"]
    assert {path: text for path, text in after.items() if path in before} == before


# --- A run built from outside its notebook ----------------------------------------------------


def test_a_run_is_built_with_its_defaults_and_its_build_cells_keywords(started: Path) -> None:
    notebook = new_run(started, "weekly", build=(
        '# Build\nbuilt = project.build_run(statements, run_values={"first_job": FIRST}, '
        'leave_out=[])'))
    notebooks.write_cell_text(notebook, PARAMETERS_CELL,
                              '# parameters\nSTART_FROM: str = ""\nFIRST: int = 7\n')
    built_run_of = toolbox_module("project_lineage").built_run_of
    built, printed = built_run_of(started, "weekly", "the test")
    assert [step.name for step in built.steps] == ["mart.team_jobs", "mart.teams", "busiest"]
    assert "  FIRST = 7" in printed
    assert "  first_job = 7" in printed
    assert "jobs.job_id >= 7" in printed


def test_a_run_built_leaves_out_what_its_build_cell_leaves_out(started: Path) -> None:
    new_run(started, "weekly", build=(
        '# Build\nbuilt = project.build_run(statements, leave_out=["mart.teams"])'))
    built, _ = toolbox_module("project_lineage").built_run_of(started, "weekly", "the test")
    assert [step.name for step in built.steps] == ["busiest"]


def test_a_run_with_no_build_cell_is_refused(started: Path) -> None:
    new_run(started, "weekly", build="# Build\n# nothing here")
    with pytest.raises(ValueError, match=r"no cell of scheduled_runs/weekly/weekly\.ipynb "
                                         r"after its # scheduled cell calls "
                                         r"project\.build_run"):
        toolbox_module("project_lineage").built_run_of(started, "weekly", "the test")


def test_only_the_imports_of_the_cells_above_are_run(started: Path) -> None:
    notebook = new_run(started, "weekly")
    cells = notebooks.read_cells(notebook)
    setup = cells[2][1] + '\nraise RuntimeError("the setup cell ran")\n'
    notebooks.write_cell_text(notebook, 3, setup)
    built, _ = toolbox_module("project_lineage").built_run_of(started, "weekly", "the test")
    assert built.steps[-1].name == "busiest"


def test_a_name_defined_above_the_scheduled_cell_is_refused_saying_to_move_it(
        started: Path) -> None:
    notebook = new_run(started, "weekly", scheduled='''# scheduled
def statements():
    return {"busiest": project.load(TABLE).busiest()}
''')
    cells = notebooks.read_cells(notebook)
    notebooks.write_cell_text(notebook, 3, cells[2][1] + '\nTABLE = "mart.teams"\n')
    with pytest.raises(NameError) as refused:
        toolbox_module("project_lineage").built_run_of(started, "weekly", "the test")
    message = " ".join(str(refused.value).split())
    assert ("the test: the # scheduled cell of scheduled_runs/weekly/weekly.ipynb needs "
            "TABLE, which a cell above it defines") in message
    assert "only the imports of the cells above # scheduled are run" in message
    assert "Move TABLE into the # scheduled cell" in message


def test_a_name_defined_nowhere_is_raised_as_python_raises_it(started: Path) -> None:
    new_run(started, "weekly", scheduled='''# scheduled
def statements():
    return {"busiest": project.load(NOWHERE).busiest()}
''')
    with pytest.raises(NameError, match="^name 'NOWHERE' is not defined$"):
        toolbox_module("project_lineage").built_run_of(started, "weekly", "the test")


# --- admin/scheduled_runs.ipynb ---------------------------------------------------------------


def test_start_makes_the_scheduled_runs_notebook_and_its_calls_run(started: Path) -> None:
    notebook = started / "admin" / "scheduled_runs.ipynb"
    code = [text for kind, text in notebooks.read_cells(notebook) if kind == "code"]
    assert any("project.check()" in text for text in code)
    assert any("project.export_project_lineage()" in text for text in code)
    run_admin_notebook(notebook)
    assert (started / "admin" / "lineage" / f"{STEM}.html").is_file()


def test_start_run_again_adds_the_notebook_to_an_older_project(
        started: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (started / "admin" / "scheduled_runs.ipynb").unlink()
    monkeypatch.chdir(started)
    assert one_line(project.start()) == (
        "This folder is a Project already. Added what it lacked: admin/scheduled_runs.ipynb.")


def test_no_scheduled_run_exports_the_lineage() -> None:
    assert "export_project_lineage" not in SCHEDULED_RUN
    assert "check()" not in SCHEDULED_RUN
