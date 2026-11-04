"""Script tags: a <PARM="NAME"/> in Hive someone else wrote, NAME any name the program that ran
it gave it, which that program filled in before Hive read it. Toolbox 8.3.

Ticket 02: a Conversion reads past each tag where a value goes, bare or inside quotes, and the
tag's place in the logic reads TAGS, what each tag stands for: script_tag(TAGS["NAME"]) for a
bare one, TAGS["NAME"] itself for one inside quotes. A tag of another shape, or where no value
goes, stops the Conversion, naming its line.
"""

from __future__ import annotations

import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import forget_the_projects_modules, toolbox_module

from sqlglot_composer import (
    FROM,
    SELECT,
    WHERE,
    at_most,
    compare_hive,
    example_database,
    project,
    script_tag,
    statement,
    to_hive,
)

converting = toolbox_module("converting")
notebooks = toolbox_module("notebooks")
script_tags = toolbox_module("script_tags")

BARE = ("INSERT OVERWRITE TABLE mart.daily_close PARTITION (dt)\n"
        "SELECT r.job_id, COUNT(*) AS runs, r.dt FROM ops.job_runs r\n"
        'WHERE r.dt <= <PARM="PERIOD_END"/> GROUP BY r.job_id, r.dt;')
QUOTED = ("INSERT OVERWRITE TABLE mart.daily_close PARTITION (dt)\n"
          "SELECT r.job_id, COUNT(*) AS runs, r.dt FROM ops.job_runs r\n"
          """WHERE r.dt <= '<PARM="run_month_2"/>' GROUP BY r.job_id, r.dt;""")
# A bare tag, with another name, in a staging table's CREATE ... AS, and the same tag twice.
STAGING = ("CREATE TEMPORARY TABLE long_runs AS\n"
           "SELECT r.job_id, r.dt FROM ops.job_runs r\n"
           'WHERE r.duration_mins >= <PARM="MinMins"/>;')
TWICE = ("INSERT OVERWRITE TABLE mart.daily_close PARTITION (dt)\n"
         "SELECT r.job_id, COUNT(*) AS runs, r.dt FROM ops.job_runs r\n"
         'WHERE r.dt >= <PARM="PERIOD_END"/> AND r.dt <= <PARM="PERIOD_END"/>\n'
         "GROUP BY r.job_id, r.dt;")
COLUMNS = {"ops.job_runs": ["run_id", "job_id", "status", "duration_mins", "avg_retry_secs",
                            "dt"]}


def _statement_of(text: str) -> converting.BatchStatement:
    (statement_read,) = converting.batch_statements([("daily.hql", text)], "ops")
    return statement_read


def _logic_of(text: str) -> str:
    return converting.convert_query(text, COLUMNS.get, "ops").logic()


# --- Reading the Hive -----------------------------------------------------------------------


@pytest.mark.parametrize("text", [BARE, QUOTED, TWICE], ids=["bare", "quoted", "twice"])
def test_a_statement_with_a_tag_reads_as_the_table_it_writes(text: str) -> None:
    read = _statement_of(text)
    assert read.kind == converting.INSERT
    assert read.table == "mart.daily_close"
    assert read.reads == ["ops.job_runs"]


def test_a_staging_tables_tag_reads_too() -> None:
    read = _statement_of(STAGING)
    assert read.kind == converting.CREATE_AS
    assert read.reads == ["ops.job_runs"]


@pytest.mark.parametrize("text, where", [
    ('SELECT * FROM <PARM="SRC"/>', "where a table's name goes"),
    ('SELECT * FROM ops.<PARM="SRC"/>', "where a table's name goes"),
    ('SELECT r.<PARM="COL"/> FROM ops.job_runs r', "where a column's name goes"),
    ('SELECT r.run_id AS <PARM="OUT"/> FROM ops.job_runs r', "where a column's name goes"),
    ('SELECT r.run_id FROM ops.job_runs r WHERE <PARM="COND"/>',
     "where a whole condition goes"),
    ('SELECT r.run_id FROM ops.job_runs r WHERE r.dt = 1 AND (<PARM="COND"/>)',
     "where a whole condition goes"),
], ids=["table", "database's table", "column", "alias", "condition", "a condition in AND"])
def test_a_tag_where_no_value_goes_is_refused_naming_its_line(text: str, where: str) -> None:
    with pytest.raises(converting.ConversionRefused) as refused:
        converting.batch_statements([("daily.hql", "SET x=1;\n" + text)], "ops")
    assert "daily.hql, line 2 has <PARM=" in str(refused.value)
    assert where in str(refused.value)


@pytest.mark.parametrize("text", [
    "SELECT * FROM ops.job_runs r WHERE r.dt <= <PARM='PERIOD_END'/>",
    'SELECT * FROM ops.job_runs r WHERE r.dt <= <PARM = "PERIOD_END" />',
    'SELECT * FROM ops.job_runs r WHERE r.dt <= <parm="PERIOD_END"/>',
    "SELECT * FROM ops.job_runs r WHERE r.dt <= '<PARM NAME=\"X\"/>'",
], ids=["single quotes", "spaces", "lower case", "another shape inside quotes"])
def test_text_that_starts_as_a_tag_but_isnt_one_is_refused(text: str) -> None:
    with pytest.raises(converting.ConversionRefused,
                       match="daily.hql, line 1 has text starting <PARM"):
        converting.batch_statements([("daily.hql", text)], "ops")


def test_a_tag_in_a_comment_is_passed_over() -> None:
    read = _statement_of('-- <PARM="OLD"/> was here\n' + BARE)
    assert read.table == "mart.daily_close"
    assert [tag.name for tag in script_tags.tags_in(read.text)] == ["PERIOD_END"]


# --- The logic --------------------------------------------------------------------------------


def test_a_bare_tags_place_is_script_tag_of_its_tags_entry() -> None:
    logic = _logic_of(TWICE)
    assert logic.count('script_tag(TAGS["PERIOD_END"])') == 2
    assert 'TAGS = {\n    "PERIOD_END": "<PARM=\\"PERIOD_END\\"/>",  # bare' in logic


def test_a_quoted_tags_place_is_its_tags_entry_as_a_string() -> None:
    logic = _logic_of(QUOTED)
    assert 'at_most(r.dt, TAGS["run_month_2"])' in logic
    assert '    "run_month_2": "<PARM=\\"run_month_2\\"/>",  # inside quotes' in logic


def test_a_tag_inside_a_longer_string_is_read_into_it() -> None:
    logic = _logic_of("SELECT r.run_id FROM ops.job_runs r "
                      """WHERE r.dt = '2026-<PARM="Month"/>-01'""")
    assert 'equals(r.dt, "2026-" + TAGS["Month"] + "-01")' in logic


def test_a_tag_compared_first_is_compared_as_its_column_is() -> None:
    logic = _logic_of('SELECT r.run_id FROM ops.job_runs r WHERE <PARM="START"/> <= r.dt')
    assert 'at_least(r.dt, script_tag(TAGS["START"]))' in logic


def test_a_tags_name_keeps_its_case() -> None:
    converted = converting.convert_query(
        'SELECT r.run_id FROM ops.job_runs r WHERE r.duration_mins >= <PARM="MinMins_2"/>',
        COLUMNS.get, "ops")
    assert converted.tag_is_quoted == {"MinMins_2": False}


def test_each_tag_is_a_finding_at_its_line() -> None:
    converted = converting.convert_query(TWICE.rstrip(";"), COLUMNS.get, "ops")
    found = [finding for finding in converted.findings if finding.kind == "tag"]
    assert [finding.line for finding in found] == [3]
    assert '<PARM="PERIOD_END"/>, a Script tag, bare.' in found[0].text


def test_one_name_bare_and_inside_quotes_in_one_table_is_refused() -> None:
    with pytest.raises(converting.ConversionRefused, match="both bare and inside quotes"):
        converting.convert_query("SELECT r.run_id FROM ops.job_runs r WHERE "
                                 """r.dt <= <PARM="END"/> AND r.status <> '<PARM="END"/>'""",
                                 COLUMNS.get, "ops")


def test_a_quoted_tag_in_a_piece_kept_as_hive_reads_its_tags_entry_into_the_text() -> None:
    logic = _logic_of("SELECT r.run_id FROM ops.job_runs r "
                      """WHERE r.status RLIKE '<PARM="PATTERN"/>'""")
    assert """unchecked_condition("{status} RLIKE '" + TAGS["PATTERN"] + "'",""" in logic


def test_a_bare_tag_in_an_in_list_binds_its_column_as_a_value_there_would() -> None:
    # is_in takes plain values, so the list stays Hive, an Unchecked condition binding the same
    # column: the table, what it reads, its Key and its Lineage are as with a value.
    converted = converting.convert_query(
        'SELECT r.job_id FROM ops.job_runs r WHERE r.job_id IN (1, <PARM="Job_2"/>)',
        COLUMNS.get, "ops")
    logic = converted.logic()
    assert ('unchecked_condition("{job_id} IN (1, {parm_job_2})", job_id=r.job_id, '
            'parm_job_2=script_tag(TAGS["Job_2"]))') in logic
    assert converted.tables == ["ops.job_runs"]


@pytest.mark.parametrize("where", [
    'r.duration_mins >= COALESCE(<PARM="Job_2"/>, 0)',
    'r.duration_mins >= <PARM="Job_2"/> + 1',
], ids=["function", "arithmetic"])
def test_a_bare_tag_among_values_converts_as_a_value_there_would(where: str) -> None:
    text = ("INSERT OVERWRITE TABLE mart.daily_close PARTITION (dt)\n"
            "SELECT r.job_id, COUNT(*) AS runs, r.dt FROM ops.job_runs r\n"
            f"WHERE {where} GROUP BY r.job_id, r.dt")
    with_value = converting.convert_query(text.replace('<PARM="Job_2"/>', "7"), COLUMNS.get,
                                          "ops")
    with_tag = converting.convert_query(text, COLUMNS.get, "ops")
    assert with_tag.logic().replace('script_tag(TAGS["Job_2"])', "7").split("def rows")[1] \
        == with_value.logic().split("def rows")[1]
    assert with_tag.tables == with_value.tables


@pytest.mark.parametrize("text", [
    "-- <PARM was here\n" + BARE,
    "/* <parm notes */\n" + BARE,
    BARE.replace("r.dt <= ", "r.duration_mins < parm_count AND r.dt <= "),
], ids=["line comment", "block comment", "a less than"])
def test_text_like_a_tag_in_a_comment_or_a_less_than_is_no_tag(text: str) -> None:
    assert _statement_of(text).table == "mart.daily_close"


def test_a_bare_tag_in_a_piece_kept_as_hive_is_its_placeholder() -> None:
    logic = _logic_of('SELECT r.run_id FROM ops.job_runs r WHERE r.dt = 1 AND '
                      'r.status RLIKE <PARM="PATTERN"/>')
    assert 'parm_pattern=script_tag(TAGS["PATTERN"])' in logic


def test_the_saved_tables_logic_imports_tags_from_its_table_reference() -> None:
    converted = converting.convert_query(BARE.rstrip(";"), COLUMNS.get, "ops")
    logic = converting.saved_table_logic(converted.logic(), "mart_dev.daily_close_mart",
                                         "daily_close_mart", converted.write,
                                         converted.static_partition)
    assert "TAGS = {" not in logic
    assert ("from references.mart_dev__daily_close_mart import daily_close_mart, TAGS"
            in logic)
    assert 'at_most(r.dt, script_tag(TAGS["PERIOD_END"]))' in logic


# --- A batch with tags, converted -----------------------------------------------------------


@pytest.fixture
def started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """A started Project, its DEV filled in, left off Python's path afterwards with its
    modules, which a convert puts there."""
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.chdir(tmp_path)
    project.start()
    databases = tmp_path / "admin" / "databases.py"
    databases.write_text(databases.read_text(encoding="utf-8")
                         .replace('"<DEV_DATABASE>"', '"mart_dev"'), encoding="utf-8")
    yield tmp_path
    forget_the_projects_modules()


def test_a_batch_with_tags_makes_each_table_reading_tags_from_its_reference(
        started: Path) -> None:
    (started / "close.hql").write_text(STAGING + "\n" + TWICE.replace(
        "FROM ops.job_runs r", "FROM long_runs r") + "\nDROP TABLE long_runs;\n",
        encoding="utf-8")
    report = repr(project.convert("closing", files=["close.hql"],
                                  query=example_database.query, database="ops"))
    assert "mart_dev.daily_close_mart" in report
    stem = "mart_dev__daily_close_mart"
    reference = (started / "references" / f"{stem}.py").read_text(encoding="utf-8")
    # The staging table is folded in, so its tag is the reader's too.
    assert '    "MinMins": "<PARM=\\"MinMins\\"/>",  # bare' in reference
    assert '    "PERIOD_END": "<PARM=\\"PERIOD_END\\"/>",  # bare' in reference
    cells = notebooks.read_cells(started / "tables" / stem / f"{stem}.ipynb")
    logic = next(text for kind, text in cells if kind == "code" and text.startswith("# logic"))
    assert f"from references.{stem} import daily_close_mart, TAGS" in logic
    scan = (started / "tables" / stem / "conversion" / "scan.md").read_text(encoding="utf-8")
    # Each tag at its script's line: the staging table's on line 3, the reader's on line 6.
    assert 'close.hql, line 3: <PARM="MinMins"/>, a Script tag, bare. Answer its value' in scan
    assert 'close.hql, line 6: <PARM="PERIOD_END"/>, a Script tag, bare.' in scan
    assert "the same query" in scan
    in_dev = (started / "tables" / stem / "conversion" / "in_dev.hql").read_text(
        encoding="utf-8")
    assert '<= <PARM="PERIOD_END"/>' in in_dev
    script = (started / "admin" / "workflows" / "convert" / "closing" / "scripts" / "close.hql")
    assert '<PARM="MinMins"/>' in script.read_text(encoding="utf-8")


def test_a_staging_tables_tag_is_a_tag_of_each_table_it_is_folded_into(started: Path) -> None:
    second = TWICE.replace("mart.daily_close", "mart.weekly_close")
    (started / "close.hql").write_text(
        STAGING + "\n" + TWICE.replace("FROM ops.job_runs r", "FROM long_runs r") + "\n"
        + second.replace("FROM ops.job_runs r", "FROM long_runs r") + "\n", encoding="utf-8")
    project.convert("closing", files=["close.hql"], query=example_database.query,
                    database="ops")
    for stem in ("mart_dev__daily_close_mart", "mart_dev__weekly_close_mart"):
        reference = (started / "references" / f"{stem}.py").read_text(encoding="utf-8")
        assert '    "MinMins": "<PARM=\\"MinMins\\"/>",  # bare' in reference


def test_new_tables_query_with_a_tag_reads_it_too(started: Path) -> None:
    project.add_references(["ops.job_runs"], query=example_database.query)
    query = 'SELECT r.run_id, r.job_id\nFROM ops.job_runs r\nWHERE r.dt = <PARM="Day_1"/>'
    project.new_table("mart_dev.failed_jobs", queries={"failed_jobs": query})
    reference = (started / "references" / "mart_dev__failed_jobs.py").read_text(
        encoding="utf-8")
    assert '    "Day_1": "<PARM=\\"Day_1\\"/>",  # bare' in reference
    scan = (started / "tables" / "mart_dev__failed_jobs" / "conversion" / "scan.md").read_text(
        encoding="utf-8")
    assert 'line 3: <PARM="Day_1"/>, a Script tag, bare.' in scan


def test_a_tag_where_no_value_goes_stops_the_batch_naming_its_line(started: Path) -> None:
    (started / "close.hql").write_text(
        'INSERT OVERWRITE TABLE mart.daily_close SELECT * FROM <PARM="SRC"/>;',
        encoding="utf-8")
    with pytest.raises(ValueError,
                       match=r"close.hql, line 1 has <PARM=\"SRC\"/> where a table's name"):
        project.convert("closing", files=["close.hql"], query=example_database.query,
                        database="ops")


# --- Hive written back ---------------------------------------------------------------------


def test_hive_written_from_the_tree_keeps_each_tag_as_written() -> None:
    read = _statement_of(BARE)
    written = converting.insert_hive(read, {"mart.daily_close": "mart_dev.daily_close_mart"},
                                     "ops", overwrite=False)
    assert 'r.dt <= <PARM="PERIOD_END"/>' in written


def test_compare_hive_reads_a_bare_tag_in_the_original() -> None:
    runs = example_database.job_runs
    built = statement(SELECT(runs.run_id), FROM(runs),
                      WHERE(at_most(runs.dt, script_tag('<PARM="PERIOD_END"/>'))))
    original = 'SELECT run_id FROM ops.job_runs WHERE dt <= <PARM="PERIOD_END"/>'
    assert compare_hive(built, original)


# --- script_tag -----------------------------------------------------------------------------


def test_script_tag_writes_an_answer_as_given() -> None:
    runs = example_database.job_runs
    built = statement(SELECT(runs.run_id), FROM(runs),
                      WHERE(at_most(runs.dt, script_tag("${hivevar:period_end}"))))
    assert "job_runs.dt <= ${hivevar:period_end}" in to_hive(built)


def test_script_tag_holds_a_partition_column_to_a_value() -> None:
    runs = example_database.job_runs
    rows = statement(SELECT(runs.run_id), FROM(runs),
                     WHERE(at_most(runs.dt, script_tag("'2026-09-23'"))))
    assert "dt <= '2026-09-23'" in to_hive(rows)


@pytest.mark.parametrize("text, why", [
    ("r.dt", "it names a column"),
    ("1, 2", "it isn't one value"),
    ("(SELECT 1)", "it isn't one value"),
])
def test_script_tag_refuses_what_isnt_one_value(text: str, why: str) -> None:
    with pytest.raises(ValueError, match=why):
        script_tag(text)


def test_script_tag_refuses_what_isnt_text() -> None:
    with pytest.raises(TypeError, match="not the Hive a Script tag stands for"):
        script_tag(None)


# --- The tag Decision (ticket 03) -------------------------------------------------------------


def test_a_hive_variable_no_set_line_sets_is_named_when_written(started: Path) -> None:
    (started / "close.hql").write_text(BARE + "\n", encoding="utf-8")
    project.convert("closing", files=["close.hql"], query=example_database.query,
                    database="ops")
    said = repr(project.write_decisions(
        {"mart_dev.daily_close_mart": {"tags": {"PERIOD_END": "'${hivevar:period_end}'"}}}))
    assert "Wrote 1 answer into references/mart_dev__daily_close_mart.py." in said
    assert ("tags: PERIOD_END is ${hivevar:period_end}, but no SET line of its scripts sets "
            "hivevar:period_end") in said


def test_a_tag_answered_is_what_the_logic_writes_where_the_tag_stood(started: Path) -> None:
    (started / "close.hql").write_text(QUOTED + "\n", encoding="utf-8")
    project.convert("closing", files=["close.hql"], query=example_database.query,
                    database="ops")
    project.write_decisions({"mart_dev.daily_close_mart": {
        "location": "/data/team/mart_dev.db/daily_close", "tags": {"run_month_2": "2026-09"}}})
    hive = to_hive(project.load("mart_dev.daily_close_mart").write())
    assert "r.dt <= '2026-09'" in hive


def test_a_hive_variable_a_set_line_sets_is_named_as_sent_first(started: Path) -> None:
    (started / "close.hql").write_text("SET hivevar:period_end=2026-09-23;\n" + BARE + "\n",
                                       encoding="utf-8")
    project.convert("closing", files=["close.hql"], query=example_database.query,
                    database="ops")
    said = repr(project.write_decisions(
        {"mart_dev.daily_close_mart": {"tags": {"PERIOD_END": "'${hivevar:period_end}'"}}}))
    assert ("tags: PERIOD_END is ${hivevar:period_end}, which Hive fills in from the SET "
            "hivevar:period_end line of its scripts") in said
