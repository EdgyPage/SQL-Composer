"""The four other Workflows' steps, each known done from the Project's files where it can be,
none fiddling. Toolbox 8.0, ticket 18.

new_table: make each Table folder; fill in its Table reference; write its logic, done once
its Statement loads; check its rows with preview(); create and write each in dev.
change_a_saved_table: write the Admin statement, done once the change cell names one; read its
Hive; send it; run the check its report names.
"""

from __future__ import annotations

import datetime
import sys
from collections.abc import Iterator
from pathlib import Path

import pandas as pd
import pytest
from conftest import toolbox_module

from sqlglot_composer import project, set_admin_log

NOW = datetime.datetime(2026, 10, 31, 9, 30, 0)
TABLE = "mart.daily_runs"
REFERENCE = '''"""mart.daily_runs - one row per job."""
from sqlglot_composer import Table

daily_runs = Table(
    "mart.daily_runs",
    columns={"job_id": "bigint", "team": "string"},
    location="/data/team/mart.db/daily_runs",
)
'''
LOGIC = '''# logic
from sqlglot_composer import FROM, INSERT_OVERWRITE, SELECT, Statement, statement
from sqlglot_composer.example_database import jobs
from references.mart__daily_runs import daily_runs

PARTITIONED_BY = []


def preview() -> Statement:
    """Each job's team."""
    return statement(SELECT(jobs.job_id, jobs.team), FROM(jobs))


def write() -> Statement:
    """Save each job's team."""
    return statement(INSERT_OVERWRITE(daily_runs), SELECT(jobs.job_id, jobs.team), FROM(jobs))
'''
workflows = toolbox_module("workflows")
notebooks = toolbox_module("notebooks")


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A started Project, left off Python's path afterwards with its modules."""
    monkeypatch.setattr(toolbox_module("unchecked"), "now", lambda: NOW)
    monkeypatch.setattr(sys, "path", list(sys.path))
    set_admin_log()
    monkeypatch.chdir(tmp_path)
    project.start()
    yield tmp_path
    for name in [name for name in sys.modules
                 if name.split(".")[0] in ("references", "building_blocks", "warehouse")]:
        del sys.modules[name]


def logic_written(root: Path, logic: str) -> None:
    """Fill in the table's Table reference, and its notebook's logic cell with `logic`."""
    (root / "references" / "mart__daily_runs.py").write_text(REFERENCE, encoding="utf-8")
    path = root / "tables" / "mart__daily_runs" / "mart__daily_runs.ipynb"
    cells = [(kind, logic if text.startswith("# logic") else text)
             for kind, text in notebooks.read_cells(path)]
    path.write_bytes(notebooks.notebook_bytes(cells))


def test_new_tables_logic_step_is_done_once_its_preview_builds(started: Path) -> None:
    project.new_table(TABLE)
    inputs = {"TABLES": [TABLE]}
    assert not workflows.every_preview_builds(started, inputs)
    logic_written(started, LOGIC.replace("SELECT(jobs.job_id, jobs.team)", "SELECT(jobs.nope)"))
    assert not workflows.every_preview_builds(started, inputs)
    logic_written(started, LOGIC)
    assert workflows.every_preview_builds(started, inputs)


def test_new_table_checks_its_rows_with_preview_before_it_writes() -> None:
    names = [step.name for step in workflows.NEW_TABLE.steps]
    assert names.index("Check each table's rows with preview(), which writes nothing") < (
        names.index("Create and write each in dev"))
    preview = next(step for step in workflows.NEW_TABLE.steps if step.reads_only)
    assert "run_query(project.load(table).preview(), query)" in preview.call


def test_the_change_is_written_once_the_change_cell_names_an_admin_statement(
        started: Path) -> None:
    path = started / "admin" / "workflows" / "change_a_saved_table" / (
        "change_a_saved_table.ipynb")
    inputs = {"TABLE": ["mart.daily_runs"]}
    assert not workflows.change_written(started, inputs)
    commented = [(kind, text.replace("change = admin.drop_partitions(table, where=...)",
                                     "# change = admin.drop_partitions(table)"))
                 for kind, text in notebooks.read_cells(path)]
    path.write_bytes(notebooks.notebook_bytes(commented))
    assert not workflows.change_written(started, inputs)
    # A call on several lines, as a formatter writes one.
    cells = [(kind, text.replace("# change = admin.drop_partitions(table)",
                                 "change = admin.drop_partitions(\n    table,\n"
                                 '    where=less_than(table.dt, "2026-09-01"),\n)'))
             for kind, text in commented]
    path.write_bytes(notebooks.notebook_bytes(cells))
    assert workflows.change_written(started, inputs)


def test_the_check_is_run_before_the_send_from_the_hive_show_hive_prints() -> None:
    steps = workflows.CHANGE_A_SAVED_TABLE.steps
    assert "run the check its Check first line names" in steps[1].name
    assert steps[-1].name.startswith("Send it, then any check after it")
    assert steps[0].done is workflows.change_written
    assert "project.table_reference(TABLE)" in steps[0].call


def test_the_check_its_check_first_line_names_has_a_cell_that_reads_it() -> None:
    # Ticket 21 (W5-1, W5-3): step 2 named a SHOW PARTITIONS no cell ran, and the README's
    # chart called it a step that only prints.
    step = workflows.CHANGE_A_SAVED_TABLE.steps[1]
    assert step.kind == workflows.PERMISSION
    assert step.call.startswith("show_hive(change)\n")
    assert step.call.endswith('\nprint(query("SHOW PARTITIONS " + TABLE))')
    assert '`"DESCRIBE FORMATTED "` for `admin.drop_table`' in step.action


def test_run_workflow_reads_the_check_a_change_names_first() -> None:
    from sqlglot_composer import Table, admin, equals

    daily_runs = Table("mart.daily_runs", partitioned_by=["dt"],
                       columns={"job_id": "bigint", "dt": "string"},
                       location="/data/team/mart.db/daily_runs")
    change = admin.drop_partitions(daily_runs, where=equals(daily_runs.dt, "2026-09-24"))
    asked = []

    def query(hive: str) -> pd.DataFrame:
        asked.append(hive)
        return pd.DataFrame({"partition": ["dt=2026-09-23", "dt=2026-09-24"]})

    said = workflows.show_the_change({}, workflows.Calls(query, None, change=change))
    assert asked == ["SHOW PARTITIONS mart.daily_runs"]
    assert said[0].startswith("-- admin.drop_partitions(mart.daily_runs")
    assert "SHOW PARTITIONS mart.daily_runs:" in said
    assert any("dt=2026-09-24" in line for line in said)
    dry = workflows.show_the_change({}, workflows.Calls(query, None, dry_run=True,
                                                        change=change))
    assert dry[-1] == "would read: SHOW PARTITIONS mart.daily_runs"
    assert len(asked) == 1, "a dry run read through query"
    dropped = workflows.show_the_change({}, workflows.Calls(query, None,
                                                            change=admin.drop_table(daily_runs)))
    assert asked[-1] == "DESCRIBE FORMATTED mart.daily_runs"
    assert "DESCRIBE FORMATTED mart.daily_runs:" in dropped


def test_a_table_reference_is_written_once_its_columns_are_with_its_docstring_unchanged(
        started: Path) -> None:
    project.new_table(TABLE)
    inputs = {"TABLES": [TABLE]}
    path = started / "references" / "mart__daily_runs.py"
    text = path.read_text(encoding="utf-8")
    assert not workflows.every_reference_from_logic(started, inputs)
    code_starts = text.index("from sqlglot_composer import Table")
    filled = REFERENCE[REFERENCE.index("from sqlglot_composer import Table"):]
    path.write_text(text[:code_starts] + filled, encoding="utf-8")
    assert "<COLUMNS>" in path.read_text(encoding="utf-8")  # its docstring still says it
    assert workflows.every_reference_from_logic(started, inputs)


def test_reference_from_logic_writes_the_columns_preview_gives(started: Path) -> None:
    project.new_table(TABLE)
    path = started / "references" / "mart__daily_runs.py"
    as_new_table_wrote_it = path.read_text(encoding="utf-8")
    logic_written(started, LOGIC)
    path.write_text(as_new_table_wrote_it, encoding="utf-8")
    said = repr(project.reference_from_logic(TABLE))
    assert "Wrote references/mart__daily_runs.py from its logic: job_id and team." in said
    written = (started / "references" / "mart__daily_runs.py").read_text(encoding="utf-8")
    assert '"job_id": "bigint",' in written and '"team": "string",' in written
    # Ticket 21: each TODO line it leaves is named, by its line.
    assert ("mart.daily_runs: 2 TODO lines left in references/mart__daily_runs.py, which wait "
            "on nothing: fill each in when you like.\n"
            "  line 1: mart.daily_runs - TODO: say in one line what one row is.\n"
            "  line ") in said
    assert "does_not_add_up=[],  # TODO: columns that are averages" in said


def test_reference_from_logic_says_a_key_it_proposes_is_from_the_logic(started: Path) -> None:
    # Ticket 21 (W2-2): a table new_table made from a Template has no query, so its Key is
    # proposed from its logic, not "from its query".
    project.new_table(TABLE)
    path = started / "references" / "mart__daily_runs.py"
    as_new_table_wrote_it = path.read_text(encoding="utf-8")
    logic_written(started, LOGIC.replace("SELECT(jobs.job_id, jobs.team), FROM(jobs)",
                                         "SELECT(jobs.job_id, jobs.team), FROM(jobs), "
                                         "GROUP_BY(jobs.job_id, jobs.team)")
                  .replace("import FROM,", "import FROM, GROUP_BY,"))
    path.write_text(as_new_table_wrote_it, encoding="utf-8")
    said = repr(project.reference_from_logic(TABLE))
    assert "Its Key, proposed from its logic: job_id." in said
    assert "from its query" not in said
    written = path.read_text(encoding="utf-8")
    assert '    key=["job_id"],  # proposed from its logic; if it is wrong' in written
    assert "from its query" not in written
    # Proposed from its logic, it is made, and an answer still changes it.
    answered = repr(project.write_decisions({TABLE: {"key": ["job_id", "team"]}}))
    assert "Wrote 1 answer" in answered
    assert '    key=["job_id", "team"],\n' in path.read_text(encoding="utf-8")


def test_reference_from_logic_keeps_one_whose_columns_you_wrote(started: Path) -> None:
    project.new_table(TABLE)
    logic_written(started, LOGIC)
    (started / "references" / "mart__daily_runs.py").write_text(REFERENCE.replace(
        "one row per job", "TODO: say in one line what one row is"), encoding="utf-8")
    said = repr(project.reference_from_logic(TABLE))
    assert "Kept references/mart__daily_runs.py" in said
    # Ticket 21 (W3-2, W3-3): the TODO lines it keeps are named, to fill in.
    assert ("mart.daily_runs: 1 TODO line left in references/mart__daily_runs.py, which waits "
            "on nothing: fill it in when you like.\n"
            '  line 1: mart.daily_runs - TODO: say in one line what one row is.') in said


def test_a_step_no_file_tells_of_says_so(started: Path) -> None:
    path = started / "admin" / "workflows" / "change_a_saved_table" / (
        "change_a_saved_table.ipynb")
    cells = [(kind, text.replace("TABLE = ''", 'TABLE = "mart.daily_runs"')
              .replace("change = admin.drop_partitions(table, where=...)",
                       "change = admin.drop_table(table)"))
             for kind, text in notebooks.read_cells(path)]
    path.write_bytes(notebooks.notebook_bytes(cells))
    said = repr(project.check())
    assert "2. Print its Hive" in said
    assert "No file tells when it is done" in said


# --- What stops blocking (Toolbox 8.1, ticket 05) -------------------------------------------


def test_a_step_that_only_reads_waits_on_nothing_and_is_named_beside_the_next(
        started: Path) -> None:
    notebook = started / "admin" / "workflows" / "new_table" / "new_table.ipynb"
    notebook.write_text(notebook.read_text(encoding="utf-8").replace(
        "TABLES = []", "TABLES = ['mart.daily_runs']"), encoding="utf-8")
    workflows = toolbox_module("workflows")
    workflow = workflows.NEW_TABLE
    preview = next(step for step in workflow.steps if step.reads_only)
    after = workflow.steps[workflow.steps.index(preview) + 1]
    assert workflows.read_before(workflow, after) is preview
    # Its logic loads, as a filled-in notebook's does: preview is passed over.
    inputs = workflows.given_inputs(started, workflow)
    skipped = workflows.next_step(started, workflow, inputs)
    assert skipped is not preview


def test_a_todo_line_left_is_counted_and_waits_on_nothing(started: Path) -> None:
    # Toolbox 8.5, ticket 08: a table with no column named like an id keeps its first line's.
    project.add_references("ops.team_notes", query=toolbox_module("example_database").query)
    said = repr(project.write_decisions({"ops.team_notes": {"key": None}}))
    assert ("ops.team_notes: 1 TODO line left in references/ops__team_notes.py, which waits "
            "on nothing: fill it in when you like.\n  line 1: ") in said
    assert "Each Decision of ops.team_notes is made." in said


@pytest.mark.parametrize("workflow", workflows.WORKFLOWS,
                         ids=lambda workflow: workflow.name)
def test_each_step_s_text_cell_says_its_goal_action_and_when_it_is_done(
        workflow: object) -> None:
    # Toolbox 8.2, 18: each step's text cell is written to docs/agents/instruction-rules.md, so
    # a step left without its goal, action or done-when would write "Goal: ." unnoticed.
    for step in workflow.steps:
        assert step.goal and step.action and step.done_when, step.name
