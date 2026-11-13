"""Hivevars: a Script tag's place left for whatever runs the Hive to fill in, from a value
given at that moment. Toolbox 8.7, ticket 09.

"I want the script tag behavior to remain the same and be able to be written over by some
mechanism with the capability to replace hivevars at runtime." hivevar(NAME, default=...) is
one more answer to a tag, beside text and a Run value's function: the Hive holds
${hivevar:NAME} where the tag stood, quoted as the tag's value stood. The Toolbox sends
SET hivevar:NAME=<value> before each Statement holding it, the value its default, or what a
Scheduled run's hivevars= gives; its exports write no SET line, but a .hivevars file beside
the .hql, since Hive lets a SET in the script beat a value given on the command line.
"""

from __future__ import annotations

import datetime
import sys
from collections.abc import Iterator
from pathlib import Path

import pandas as pd
import pytest
from conftest import forget_the_projects_modules, toolbox_module

from sqlglot_composer import (
    FROM,
    INSERT_OVERWRITE,
    SELECT,
    WHERE,
    Statement,
    Table,
    at_most,
    compare_with_original,
    equals,
    export_hive,
    example_database,
    notebooks,
    project,
    set_admin_log,
    hivevar,
    latest_partition,
    run_execute,
    run_query,
    script_tag,
    show_hive,
    statement,
    tag_text,
    to_hive,
    unchecked_hive,
)

runs = example_database.job_runs
recent = Table("mart.recent_runs", columns={"run_id": "bigint"},
               location="/data/your_team/mart.db/recent_runs")


def period_end() -> datetime.date:
    """The Example database's last day."""
    return datetime.date(2026, 9, 24)


def read_up_to(value: object) -> str:
    """The Hive of a read whose WHERE holds dt to a bare Script tag's answer."""
    return to_hive(statement(SELECT(runs.run_id), FROM(runs),
                             WHERE(at_most(runs.dt, script_tag(value)))))


# --- In the Hive ----------------------------------------------------------------------------


@pytest.mark.parametrize(("default", "written"), [
    ("'2026-10-31'", "'${hivevar:PERIOD_END}'"),
    ("5", "${hivevar:PERIOD_END}"),
    (period_end, "'${hivevar:PERIOD_END}'"),
])
def test_a_bare_tags_hivevar_stands_quoted_as_its_default_stood(default: object,
                                                                 written: str) -> None:
    hive = read_up_to(hivevar("PERIOD_END", default=default))
    assert hive.endswith(f"job_runs.dt <= {written}")


def test_a_quoted_tags_hivevar_stands_inside_the_originals_quotes() -> None:
    assert "month " + tag_text(hivevar("RUN_MONTH", default="2026-09")) == (
        "month ${hivevar:RUN_MONTH}")
    assert tag_text(hivevar("DAY", default=period_end)) == "${hivevar:DAY}"


def test_a_bare_tag_in_text_kept_whole_stands_quoted_as_its_default_stood() -> None:
    assert tag_text(hivevar("PERIOD_END", default="'2026-09-24'"), quoted=False) == (
        "'${hivevar:PERIOD_END}'")
    assert tag_text(hivevar("DAYS", default="7"), quoted=False) == "${hivevar:DAYS}"


@pytest.mark.parametrize("name", ["PERIOD END", "1ST", "", 5])
def test_a_name_hive_cant_read_is_refused(name: object) -> None:
    with pytest.raises(ValueError, match="can't be a Hivevar's NAME"):
        hivevar(name, default="'2026-09-24'")


@pytest.mark.parametrize("default", [None, "", 5, datetime.date(2026, 9, 24)])
def test_a_default_neither_text_nor_a_function_is_refused(default: object) -> None:
    with pytest.raises(TypeError, match="for its default"):
        hivevar("PERIOD_END", default=default)


def test_a_bare_default_is_held_to_what_a_text_answer_is() -> None:
    with pytest.raises(ValueError, match="a date needs its own quotes"):
        read_up_to(hivevar("PERIOD_END", default="2026-09-24"))


def test_a_value_a_set_line_cant_hold_is_refused() -> None:
    with pytest.raises(ValueError, match="holds a ; or a line break"):
        tag_text(hivevar("NOTE", default="a;b"))


# --- Sent ------------------------------------------------------------------------------------


def a_write(answer: object) -> Statement:
    """A write whose WHERE holds dt to a bare Script tag's answer."""
    return statement(INSERT_OVERWRITE(recent), SELECT(runs.run_id), FROM(runs),
                     WHERE(at_most(runs.dt, script_tag(answer))))


def test_show_hive_prints_each_set_line_above_the_statement(
        capsys: pytest.CaptureFixture[str]) -> None:
    show_hive(a_write(hivevar("PERIOD_END", default="'2026-09-24'")))
    assert capsys.readouterr().out.splitlines()[:3] == [
        "-- Hivevars PERIOD_END: run_execute sends each SET line first, in a call of its own",
        "SET hivevar:PERIOD_END=2026-09-24;",
        "INSERT OVERWRITE TABLE mart.recent_runs"]


def test_show_hive_says_a_read_has_its_values_written_in_place(
        capsys: pytest.CaptureFixture[str]) -> None:
    show_hive(statement(SELECT(runs.run_id), FROM(runs), WHERE(equals(
        runs.dt, script_tag(hivevar("PERIOD_END", default="'2026-09-24'"))))))
    assert capsys.readouterr().out.splitlines()[:2] == [
        "-- Hivevars PERIOD_END: run_query writes each value in its place; elsewhere, send "
        "these SET lines first",
        "SET hivevar:PERIOD_END=2026-09-24;"]


def test_each_statement_sends_the_values_tag_text_worked_out_for_it() -> None:
    """Two tables' Hive text, each with a Hivevar PERIOD_END of its own default, both built
    before either is sent: each is sent with its own value."""
    text = ("INSERT OVERWRITE TABLE mart.recent_runs SELECT run_id FROM ops.job_runs "
            "WHERE dt <= ")
    first = unchecked_hive(text + tag_text(hivevar("PERIOD_END", default="'2026-09-24'"),
                                           quoted=False))
    second = unchecked_hive(text + tag_text(hivevar("PERIOD_END", default="'2026-10-31'"),
                                            quoted=False))
    sent: list[str] = []
    run_execute(first, sent.append)
    run_execute(second, sent.append)
    assert [line for line in sent if line.startswith("SET")] == [
        "SET hivevar:PERIOD_END=2026-09-24", "SET hivevar:PERIOD_END=2026-10-31"]


def test_run_execute_sends_each_set_line_first() -> None:
    sent: list[str] = []
    run_execute(a_write(hivevar("PERIOD_END", default=period_end)), sent.append)
    assert sent[0] == "SET hivevar:PERIOD_END=2026-09-24"
    assert sent[1].endswith("job_runs.dt <= '${hivevar:PERIOD_END}'")
    assert len(sent) == 2


def test_run_execute_sends_an_unchecked_statements_hivevar_first() -> None:
    sent: list[str] = []
    text = ("INSERT OVERWRITE TABLE mart.recent_runs SELECT run_id FROM ops.job_runs "
            "WHERE dt <= ")
    run_execute(unchecked_hive(text + tag_text(hivevar("DAY", default="'2026-09-23'"),
                                               quoted=False)), sent.append)
    assert sent == ["SET hivevar:DAY=2026-09-23", text + "'${hivevar:DAY}'"]


def test_a_statement_with_no_hivevar_is_sent_alone() -> None:
    sent: list[str] = []
    run_execute(a_write("'2026-09-24'"), sent.append)
    assert len(sent) == 1


def test_run_query_writes_each_value_in_its_place() -> None:
    sent: list[str] = []

    def query(hive: str) -> pd.DataFrame:
        sent.append(hive)
        return example_database.query(hive)

    rows = run_query(statement(SELECT(runs.run_id), FROM(runs),
                               WHERE(equals(runs.dt, script_tag(
                                   hivevar("PERIOD_END", default="'2026-09-24'"))))), query)
    assert sent[0].endswith("job_runs.dt = '2026-09-24'")
    assert len(rows) == len(run_query(statement(SELECT(runs.run_id), FROM(runs),
                                                WHERE(equals(runs.dt, "2026-09-24"))),
                                      example_database.query))


def test_compare_with_original_writes_each_value_in_its_place() -> None:
    sent: list[str] = []

    def query(hive: str) -> pd.DataFrame:
        sent.append(hive)
        return example_database.query(hive)

    ours = statement(SELECT(runs.run_id), FROM(runs), WHERE(equals(
        runs.dt, script_tag(hivevar("PERIOD_END", default="'2026-09-24'")))))
    verdict = compare_with_original(
        ours, "SELECT run_id FROM ops.job_runs WHERE dt = '2026-09-24'", query=query,
        partition={"dt": "2026-09-24"})
    assert "${hivevar" not in sent[0]
    assert verdict.ok


def test_a_function_default_that_fails_is_never_sent() -> None:
    def no_connection() -> datetime.date:
        raise ConnectionError("the warehouse can't be reached")

    sent: list[str] = []
    with pytest.warns(UserWarning):
        write = a_write(hivevar("PERIOD_END", default=no_connection))
    with pytest.raises(ValueError, match="holds a Run value that failed"):
        run_execute(write, sent.append)
    assert sent == []


# --- In the lineage --------------------------------------------------------------------------

lineage = toolbox_module("lineage")


def latest_day() -> datetime.date:
    """The latest day ops.job_runs holds, as a Run value's function in a Project reads it."""
    return latest_partition(runs.dt, example_database.query)


@pytest.mark.parametrize(("default", "name"), [
    ("'2026-09-24'", "hivevar PERIOD_END, default \"'2026-09-24'\""),
    (latest_day, "hivevar PERIOD_END, default test_hivevars.latest_day()"),
])
def test_a_hivevar_is_drawn_as_a_value_with_its_name_its_default_and_its_set_line(
        default: object, name: str) -> None:
    built = a_write(hivevar("PERIOD_END", default=default))
    graph = lineage.build_graph([(built, "recent")])
    (box,) = [box for box in graph.boxes.values() if box["group"] == lineage.RUN_VALUES]
    assert box["name"] == name
    assert box["type"] == "SET hivevar:PERIOD_END=2026-09-24"
    key = next(key for key, each in graph.boxes.items() if each is box)
    assert any(source == key and graph.boxes[target]["kind"] == "condition"
               for source, target, _ in graph.arrows)


def test_a_hivevars_run_value_default_draws_what_it_read() -> None:
    graph = lineage.build_graph([(a_write(hivevar("PERIOD_END", default=latest_day)),
                                  "recent")])
    key = next(key for key, box in graph.boxes.items() if box["group"] == lineage.RUN_VALUES)
    assert ("table:ops.job_runs.dt", key, "value") in graph.arrows


def test_a_statements_section_lists_its_hivevars_set_line_as_sent_before_it() -> None:
    built = a_write(hivevar("PERIOD_END", default="'2026-09-24'"))
    assert ("Hivevars PERIOD_END, sent before it: SET hivevar:PERIOD_END=2026-09-24"
            in lineage.settings_lines(built, []))


# --- Exported --------------------------------------------------------------------------------


@pytest.fixture
def beside_the_notebook(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """The folder you're working in, standing in for a notebook's: a test's own file isn't a
    notebook, so the calling file is told as none, as in a notebook Python can't name."""
    monkeypatch.setattr(toolbox_module("lineage"), "calling_file", lambda frame: None)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def lines_passed(path: Path) -> list[str]:
    """The lines of a .hivevars file a scheduler passes: each but its header's."""
    return [line for line in path.read_text(encoding="utf-8").splitlines()
            if not line.startswith("#")]


def test_the_export_holds_no_set_line_but_a_hivevars_file_beside_it(
        beside_the_notebook: Path) -> None:
    daily = a_write(hivevar("PERIOD_END", default=period_end))
    report = repr(export_hive(daily))
    hql = (beside_the_notebook / "daily.hql").read_text(encoding="utf-8")
    assert "SET hivevar" not in hql
    assert "job_runs.dt <= '${hivevar:PERIOD_END}'" in hql
    hivevars = beside_the_notebook / "daily.hivevars"
    assert lines_passed(hivevars) == ["--hivevar PERIOD_END=2026-09-24"]
    header = " ".join(line.removeprefix("# ") for line in
                      hivevars.read_text(encoding="utf-8").splitlines() if line.startswith("#"))
    assert "Hive lets a SET in the script beat a value given on its command line" in header
    assert report.endswith("Wrote daily.hivevars beside it, the value of each Hivevar its "
                           "Hive holds, PERIOD_END, as worked out now, for your scheduler to "
                           "pass to Hive.")
    assert b"\r\n" not in hivevars.read_bytes()


def test_a_value_the_shell_would_split_is_quoted(beside_the_notebook: Path) -> None:
    region = a_write(hivevar("REGION", default="'EMEA West'"))
    export_hive(region)
    assert lines_passed(beside_the_notebook / "region.hivevars") == [
        "--hivevar REGION='EMEA West'"]


def test_with_no_hivevar_the_file_from_before_is_deleted(beside_the_notebook: Path) -> None:
    daily = a_write(hivevar("PERIOD_END", default="'2026-09-24'"))
    export_hive(daily)
    daily = a_write("'2026-09-24'")
    report = repr(export_hive(daily))
    assert not (beside_the_notebook / "daily.hivevars").exists()
    assert report.endswith("Deleted daily.hivevars, which an export before this one wrote: "
                           "the Hive holds no Hivevar now.")


# --- A Scheduled run -------------------------------------------------------------------------

# This module's names stand for the Scheduled run notebook's: the parameters cell's START_FROM.
START_FROM = ""


@pytest.fixture
def weekly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A Project with a Scheduled run, weekly, whose folder the test works in."""
    monkeypatch.setitem(globals(), "START_FROM", "")
    set_admin_log()
    monkeypatch.chdir(tmp_path)
    project.start()
    project.new_scheduled_run("weekly")
    monkeypatch.chdir(tmp_path / "scheduled_runs" / "weekly")
    return tmp_path


def recent_runs() -> dict[str, object]:
    """A run's statements(): one write holding the Hivevar PERIOD_END."""
    return {"recent": a_write(hivevar("PERIOD_END", default="'2026-09-24'"))}


def test_the_build_prints_and_the_run_sends_each_set_line(
        weekly: Path, capsys: pytest.CaptureFixture[str]) -> None:
    built = project.build_run(recent_runs)
    printed = capsys.readouterr().out
    assert ("-- 1 of 1: mart.recent_runs\n"
            "-- Hivevars PERIOD_END: run_execute sends each SET line first, in a call of its "
            "own\nSET hivevar:PERIOD_END=2026-09-24;\n") in printed
    sent: list[str] = []
    built.run(example_database.query, sent.append)
    assert sent[0] == "SET hivevar:PERIOD_END=2026-09-24"
    assert sent[1].endswith("'${hivevar:PERIOD_END}'")


def test_hivevars_gives_one_another_value_by_its_name(
        weekly: Path, capsys: pytest.CaptureFixture[str]) -> None:
    built = project.build_run(recent_runs,
                              hivevars={"PERIOD_END": datetime.date(2026, 10, 31)})
    printed = capsys.readouterr().out
    assert ("Hivevars given by hivevars=, in place of each one's default:\n"
            "  PERIOD_END = datetime.date(2026, 10, 31)\n") in printed
    assert "SET hivevar:PERIOD_END=2026-10-31;" in printed
    sent: list[str] = []
    built.run(example_database.query, sent.append)
    assert sent[0] == "SET hivevar:PERIOD_END=2026-10-31"


@pytest.mark.parametrize("left_empty", [None, ""])
def test_a_parameter_left_empty_sends_the_default(
        weekly: Path, capsys: pytest.CaptureFixture[str], left_empty: object) -> None:
    project.build_run(recent_runs, hivevars={"PERIOD_END": left_empty})
    printed = capsys.readouterr().out
    assert "SET hivevar:PERIOD_END=2026-09-24;" in printed
    assert "so its default is sent" in printed


def test_a_parameters_date_text_is_read_as_that_date(
        weekly: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    """hivevars={"PERIOD_END": RUN_DATE} is written before the build reads RUN_DATE, so it
    holds the text the scheduler passed, "2026-10-31": a date, quoted where the tag stood."""
    path = weekly / "scheduled_runs" / "weekly" / "weekly.ipynb"
    notebooks.write_notebook(path, [("code", '# parameters\nimport datetime\n'
                                     'START_FROM: str = ""\n'
                                     "RUN_DATE: datetime.date | None = None")])
    monkeypatch.setitem(globals(), "RUN_DATE", "2026-10-31")
    built = project.build_run(recent_runs, hivevars={"PERIOD_END": globals()["RUN_DATE"]})
    printed = capsys.readouterr().out
    assert '  PERIOD_END = datetime.date(2026, 10, 31), read from "2026-10-31"\n' in printed
    assert "job_runs.dt <= '${hivevar:PERIOD_END}'" in printed
    sent: list[str] = []
    built.run(example_database.query, sent.append)
    assert sent[0] == "SET hivevar:PERIOD_END=2026-10-31"


def test_a_hivevars_value_that_cant_stand_there_is_refused_naming_hivevars(
        weekly: Path) -> None:
    for given in ("last week", ["2026-10-31"]):
        with pytest.raises(TypeError, match="hivevars= gives PERIOD_END .*, which can't stand "
                                            "where its tag stood") as refused:
            project.build_run(recent_runs, hivevars={"PERIOD_END": given})
        assert "In the Build cell's hivevars=, give PERIOD_END a datetime.date" in str(
            refused.value)


def test_a_hivevars_name_no_statement_uses_is_refused_naming_those_it_does(
        weekly: Path) -> None:
    with pytest.raises(ValueError, match="hivevars= names PERIOD_START, but no Statement of "
                                         "this run has a Hivevar by that name") as refused:
        project.build_run(recent_runs, hivevars={"PERIOD_START": "'2026-10-01'"})
    assert "Its Statements' Hivevars are PERIOD_END." in str(refused.value)


def scheduled_cell_written(folder: Path, defaults: list[str]) -> None:
    """The weekly run's # scheduled cell filled in and saved: a write of its own for each
    default, each holding a Hivevar PERIOD_END of that default."""
    writes = ", ".join(
        f"'recent_{place}': statement(INSERT_OVERWRITE(recent), SELECT(job_runs.run_id), "
        f"FROM(job_runs), WHERE(at_most(job_runs.dt, script_tag(hivevar('PERIOD_END', "
        f"default={default!r})))))" for place, default in enumerate(defaults))
    cell = ("# scheduled\nfrom sqlglot_composer import FROM, INSERT_OVERWRITE, SELECT, WHERE, "
            "Table, at_most, hivevar, script_tag, statement\n"
            "from sqlglot_composer.example_database import job_runs\n"
            "recent = Table('mart.recent_runs', columns={'run_id': 'bigint'}, "
            "location='/data/your_team/mart.db/recent_runs')\n\n"
            f"def statements():\n    return {{{writes}}}\n")
    cells = [(kind, cell if text.startswith("# scheduled") else text)
             for kind, text in notebooks.read_cells(folder / "weekly.ipynb")]
    notebooks.write_notebook(folder / "weekly.ipynb", cells)


def test_the_runs_export_writes_its_hivevars_beside_its_hive(weekly: Path) -> None:
    folder = weekly / "scheduled_runs" / "weekly"
    scheduled_cell_written(folder, ["'2026-09-24'"])
    report = repr(project.export_run_hive("weekly"))
    hql = (folder / "weekly.hql").read_text(encoding="utf-8")
    assert "SET hivevar" not in hql
    assert lines_passed(folder / "weekly.hivevars") == ["--hivevar PERIOD_END=2026-09-24"]
    assert "Wrote weekly.hivevars beside it" in report


def test_one_name_given_two_values_is_refused_before_any_file_is_written(weekly: Path) -> None:
    folder = weekly / "scheduled_runs" / "weekly"
    scheduled_cell_written(folder, ["'2026-09-24'", "'2026-10-31'"])
    with pytest.raises(ValueError, match="the Hivevar PERIOD_END is worked out as "
                                         "'2026-09-24' for one Statement and '2026-10-31'"):
        project.export_run_hive("weekly")
    assert not (folder / "weekly.hql").exists()


# --- Answered in the decisions cell ----------------------------------------------------------

BARE = ("INSERT OVERWRITE TABLE mart.daily_close PARTITION (dt)\n"
        "SELECT r.job_id, COUNT(*) AS runs, r.dt FROM ops.job_runs r\n"
        """WHERE r.dt <= <PARM="PERIOD_END"/> GROUP BY r.job_id, r.dt;\n""")
QUOTED = ("INSERT OVERWRITE TABLE mart.daily_close PARTITION (dt)\n"
          "SELECT r.job_id, COUNT(*) AS runs, r.dt FROM ops.job_runs r\n"
          """WHERE r.dt <= '<PARM="PERIOD_END"/>' GROUP BY r.job_id, r.dt;\n""")
RUN_VALUES = '''import datetime


def period_end() -> datetime.date:
    """The Example database's last day."""
    return datetime.date(2026, 9, 24)
'''
TABLE = "mart_dev.daily_close_mart"
REFERENCE = Path("references") / "mart_dev__daily_close_mart.py"


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A started Project, its DEV filled in, holding building_blocks/run_values.py."""
    monkeypatch.setattr(sys, "path", [str(tmp_path), *sys.path])
    monkeypatch.chdir(tmp_path)
    project.start()
    databases = tmp_path / "admin" / "databases.py"
    databases.write_text(databases.read_text(encoding="utf-8")
                         .replace('"<DEV_DATABASE>"', '"mart_dev"'), encoding="utf-8")
    (tmp_path / "building_blocks" / "run_values.py").write_text(RUN_VALUES, encoding="utf-8")
    yield tmp_path
    forget_the_projects_modules()
    sys.modules.pop("building_blocks.run_values", None)


def converted(root: Path, script: str) -> None:
    """The script converted, as the batch closing, into mart_dev.daily_close_mart."""
    (root / "close.hql").write_text(script, encoding="utf-8")
    project.convert("closing", files=["close.hql"], query=example_database.query,
                    database="ops")


def test_a_tag_answered_hivevar_is_written_into_its_reference(started: Path) -> None:
    converted(started, BARE)
    said = repr(project.write_decisions({TABLE: {
        "location": "/data/team/mart_dev.db/daily_close",
        "tags": {"PERIOD_END": hivevar("PERIOD_END", default="'2026-09-24'")}}}))
    assert f"Each Decision of {TABLE} is made." in said
    assert ("tags: PERIOD_END is the Hivevar PERIOD_END: the Toolbox sends "
            "SET hivevar:PERIOD_END=<value> before each Statement that holds it") in said
    reference = REFERENCE.read_text(encoding="utf-8")
    assert "from sqlglot_composer import hivevar  # for a Hivevar in TAGS" in reference
    assert ('    "PERIOD_END": hivevar("PERIOD_END", default="\'2026-09-24\'"),  #'
            in reference)
    assert "r.dt <= '${hivevar:PERIOD_END}'" in to_hive(project.load(TABLE).write())


def test_a_quoted_tag_answered_hivevar_with_a_run_value_imports_both(started: Path) -> None:
    from building_blocks.run_values import period_end as users_period_end

    converted(started, QUOTED)
    project.write_decisions({TABLE: {
        "location": "/data/team/mart_dev.db/daily_close",
        "tags": {"PERIOD_END": hivevar("PERIOD_END", default=users_period_end)}}})
    reference = REFERENCE.read_text(encoding="utf-8")
    assert "from building_blocks.run_values import period_end  # a Run value" in reference
    assert "from sqlglot_composer import hivevar  # for a Hivevar in TAGS" in reference
    assert '    "PERIOD_END": hivevar("PERIOD_END", default=period_end),  #' in reference
    write = project.load(TABLE).write()
    assert "r.dt <= '${hivevar:PERIOD_END}'" in to_hive(write)
    sent: list[str] = []
    run_execute(write, sent.append)
    assert sent[0] == "SET hivevar:PERIOD_END=2026-09-24"


def test_answered_again_with_text_drops_the_hivevar_import(started: Path) -> None:
    converted(started, BARE)
    project.write_decisions({TABLE: {
        "location": "/data/team/mart_dev.db/daily_close",
        "tags": {"PERIOD_END": hivevar("PERIOD_END", default="'2026-09-24'")}}})
    project.write_decisions({TABLE: {"tags": {"PERIOD_END": "'2026-09-23'"}}})
    reference = REFERENCE.read_text(encoding="utf-8")
    assert "import hivevar" not in reference
    assert "r.dt <= '2026-09-23'" in to_hive(project.load(TABLE).write())


def test_a_hivevar_whose_default_cant_stand_there_is_left_unwritten(started: Path) -> None:
    converted(started, QUOTED)
    said = repr(project.write_decisions({TABLE: {"tags": {
        "PERIOD_END": hivevar("PERIOD_END", default="'2026-09-24'")}}}))
    assert "tags: PERIOD_END stands inside quotes already, so its answer has none" in said
    assert "hivevar" not in REFERENCE.read_text(encoding="utf-8")


def test_the_convert_notebooks_decisions_cell_is_read_with_its_hivevar(started: Path) -> None:
    """The Workflow's run cells read DECISIONS without running the cell: hivevar(...), its
    default an imported Run value, is read as the Hivevar the cell would make."""
    workflows = toolbox_module("workflows")
    path = workflows.notebook_path(started, workflows.CONVERT)
    cell = ("from sqlglot_composer import hivevar\n"
            "from building_blocks.run_values import period_end\n"
            'DECISIONS = {"mart_dev.daily_close_mart": {"tags": {'
            '"PERIOD_END": hivevar("PERIOD_END", default=period_end)}}}\n')
    cells = [(kind, cell if text.startswith("DECISIONS =") else text)
             for kind, text in notebooks.read_cells(path)]
    notebooks.write_notebook(path, cells)
    read = workflows.given_inputs(started, workflows.CONVERT)
    answer = read["DECISIONS"]["mart_dev.daily_close_mart"]["tags"]["PERIOD_END"]
    assert repr(answer) == 'hivevar("PERIOD_END", default=period_end)'


def test_hivevar_is_written_back_as_python() -> None:
    assert repr(hivevar("PERIOD_END", default="'2026-09-24'")) == (
        "hivevar(\"PERIOD_END\", default=\"'2026-09-24'\")")
    assert repr(hivevar("PERIOD_END", default=period_end)) == (
        'hivevar("PERIOD_END", default=period_end)')
