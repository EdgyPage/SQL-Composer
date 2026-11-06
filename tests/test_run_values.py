"""Run values: a function of the user's that gives what a Script tag stands for each time a
table's write is built, written into its Hive as plain text. Toolbox 8.4, ticket 05.

A Table reference's TAGS holds the function, which the decisions cell imports from the Project
and answers with; script_tag calls it for a bare tag, tag_text for one inside quotes. A
function that fails leaves its name in the Hive, with a Warning, so a dry run still shows the
rest; run_query and run_execute refuse to send it.
"""

from __future__ import annotations

import datetime
import sys
import warnings
from collections.abc import Iterator
from pathlib import Path

import pandas as pd
import pytest
from conftest import forget_the_projects_modules, toolbox_module

from sqlglot_composer import (
    AS,
    FROM,
    GROUP_BY,
    INSERT_INTO,
    INSERT_OVERWRITE,
    SELECT,
    WHERE,
    Table,
    at_least,
    at_most,
    between,
    count_rows,
    equals,
    example_database,
    hive_date,
    hive_function,
    latest_partition,
    project,
    run_query,
    run_value,
    script_tag,
    statement,
    tag_text,
    to_hive,
    today,
)

decisions = toolbox_module("decisions")
runs = example_database.job_runs


def period_end() -> datetime.date:
    """The Example database's last day."""
    return datetime.date(2026, 9, 24)


def no_connection() -> datetime.date:
    """A lookup whose warehouse can't be reached."""
    raise ConnectionError("the warehouse can't be reached")


def _window(value: object) -> str:
    return to_hive(statement(
        SELECT(runs.run_id), FROM(runs),
        WHERE(between(runs.dt, hive_function("date_sub", script_tag(value), 1),
                      script_tag(value)))))


# --- script_tag and tag_text ------------------------------------------------------------------


@pytest.mark.parametrize(("given", "written"), [
    (datetime.date(2026, 9, 24), "'2026-09-24'"),
    (datetime.datetime(2026, 9, 24, 6, 30), "'2026-09-24 06:30:00'"),
    (5, "5"),
    ("'2026-09-24'", "'2026-09-24'"),
    (True, "TRUE"),
])
def test_a_run_value_is_written_as_hive(given: object, written: str) -> None:
    def lookup() -> object:
        return given
    assert f"job_runs.dt <= {written}" in to_hive(statement(
        SELECT(runs.run_id), FROM(runs), WHERE(at_most(runs.dt, script_tag(lookup)))))


def test_a_run_value_bounds_the_partitions_read_and_runs() -> None:
    hive = _window(period_end)
    assert "BETWEEN DATE_ADD('2026-09-24', 1 * -1) AND '2026-09-24'" in hive
    assert len(example_database.query(hive)) == 9


def test_a_run_value_is_called_each_time_the_statement_is_built() -> None:
    days = iter(["'2026-09-23'", "'2026-09-24'"])

    def next_day() -> str:
        return next(days)
    assert "'2026-09-23'" in _window_once(next_day)
    assert "'2026-09-24'" in _window_once(next_day)


def _window_once(value: object) -> str:
    return to_hive(statement(SELECT(runs.run_id), FROM(runs),
                             WHERE(at_most(runs.dt, script_tag(value)))))


@pytest.mark.parametrize("given", [None, ["2026-09-24"], "5 - 3"])
def test_a_run_value_that_isnt_one_value_is_refused(given: object) -> None:
    def lookup() -> object:
        return given
    with pytest.raises((TypeError, ValueError), match="lookup"):
        script_tag(lookup)


def test_a_failed_run_value_shows_in_a_dry_run_and_is_never_sent() -> None:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        built = statement(SELECT(runs.run_id), FROM(runs),
                          WHERE(at_most(runs.dt, script_tag(no_connection))))
    assert "no_connection() raised ConnectionError: the warehouse can't be reached" in str(
        caught[0].message)
    assert "job_runs.dt <= `<no_connection() failed>`" in to_hive(built)
    with pytest.raises(ValueError, match="Nothing was sent: the Statement holds a Run value"):
        run_query(built, example_database.query)


def test_tag_text_calls_a_run_value_for_a_tag_inside_quotes() -> None:
    assert tag_text(period_end) == "2026-09-24"
    assert tag_text("2026-09") == "2026-09"
    with pytest.raises(ValueError, match="no_connection"):
        tag_text(no_connection)


# --- Answered in the decisions cell -----------------------------------------------------------

BARE = ("INSERT OVERWRITE TABLE mart.daily_close PARTITION (dt)\n"
        "SELECT r.job_id, COUNT(*) AS runs, r.dt FROM ops.job_runs r\n"
        'WHERE r.dt BETWEEN date_sub(<PARM="PERIOD_END"/>, 1) AND <PARM="PERIOD_END"/>\n'
        "GROUP BY r.job_id, r.dt;\n")
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


def _users_period_end() -> object:
    from building_blocks.run_values import period_end as imported
    return imported


@pytest.mark.parametrize(("script", "written"), [
    (BARE, "BETWEEN DATE_ADD('2026-09-24', 1 * -1) AND '2026-09-24'"),
    (QUOTED, "r.dt <= '2026-09-24'"),
], ids=["bare", "quoted"])
def test_a_tag_answered_with_a_function_is_written_into_its_reference(
        started: Path, script: str, written: str) -> None:
    (started / "close.hql").write_text(script, encoding="utf-8")
    project.convert("closing", files=["close.hql"], query=example_database.query,
                    database="ops")
    said = repr(project.write_decisions({TABLE: {
        "location": "/data/team/mart_dev.db/daily_close",
        "tags": {"PERIOD_END": _users_period_end()}}}))
    assert f"Each Decision of {TABLE} is made." in said
    reference = REFERENCE.read_text(encoding="utf-8")
    assert ("from building_blocks.run_values import period_end  # a Run value, for TAGS or SEED"
            in reference)
    assert '    "PERIOD_END": period_end,  #' in reference
    assert written in to_hive(project.load(TABLE).write())


def test_a_function_answered_again_with_text_drops_its_import(started: Path) -> None:
    (started / "close.hql").write_text(BARE, encoding="utf-8")
    project.convert("closing", files=["close.hql"], query=example_database.query,
                    database="ops")
    project.write_decisions({TABLE: {"location": "/data/team/mart_dev.db/daily_close",
                                     "tags": {"PERIOD_END": _users_period_end()}}})
    said = repr(project.write_decisions({TABLE: {"tags": {"PERIOD_END": "'2026-09-23'"}}}))
    assert "tags: PERIOD_END is '2026-09-23' now, in place of period_end" in said
    reference = REFERENCE.read_text(encoding="utf-8")
    assert "import period_end" not in reference
    assert "BETWEEN DATE_ADD('2026-09-23', 1 * -1)" in to_hive(project.load(TABLE).write())


def test_a_function_made_in_the_notebook_is_left_unwritten(started: Path) -> None:
    (started / "close.hql").write_text(BARE, encoding="utf-8")
    project.convert("closing", files=["close.hql"], query=example_database.query,
                    database="ops")
    said = repr(project.write_decisions({TABLE: {"tags": {
        "PERIOD_END": lambda: datetime.date(2026, 9, 24)}}}))
    assert "a function a Table reference can't import: write it in a file of the Project's" \
        in said
    assert "import" not in REFERENCE.read_text(encoding="utf-8").split("TAGS = {")[0][-200:]


# --- today, latest_partition and hive_date (ticket 06) ----------------------------------------


def test_today_is_utc_or_an_offset_from_it() -> None:
    # The tests' clock stands at noon, UTC, on 2026-09-25.
    assert today() == datetime.date(2026, 9, 25)
    assert today(utc_offset_hours=14) == datetime.date(2026, 9, 26)
    assert today(utc_offset_hours=-12.5) == datetime.date(2026, 9, 24)
    for wrong in (30, "-6", True):
        with pytest.raises(ValueError, match="isn't an offset from UTC"):
            today(utc_offset_hours=wrong)


def test_latest_partition_reads_show_partitions() -> None:
    assert latest_partition(runs.dt, example_database.query) == datetime.date(2026, 9, 24)


@pytest.mark.parametrize(("listed", "column", "latest"), [
    (["dt=2026-09-23/team=data", "dt=2026-09-24/team=web"], "team", "web"),
    (["batch_no=9", "batch_no=10"], "batch_no", 10),
    (["region=north%2Fwest", "region=east"], "region", "north/west"),
])
def test_latest_partition_reads_any_partition_column(listed: list[str], column: str,
                                                     latest: object) -> None:
    table = Table("ops.parts", columns={column: "string", "dt": "string", "team": "string"},
                  partitioned_by=[column])

    def query(hive: str) -> pd.DataFrame:
        assert hive == "SHOW PARTITIONS ops.parts"
        return pd.DataFrame({"partition": listed})
    assert latest_partition(getattr(table, column), query) == latest


def test_latest_partition_refuses_what_it_cant_read() -> None:
    with pytest.raises(ValueError, match="isn't a partition column of ops.job_runs"):
        latest_partition(runs.job_id, example_database.query)
    with pytest.raises(ValueError, match="holds no Partition yet"):
        latest_partition(runs.dt, lambda hive: pd.DataFrame({"partition": []}))


def test_hive_date_writes_a_date_in_quotes() -> None:
    assert hive_date(datetime.date(2026, 10, 31)) == "'2026-10-31'"
    with pytest.raises(TypeError, match="not a date"):
        hive_date("2026-10-31")


# --- Run values in lineage (ticket 07) --------------------------------------------------------

lineage = toolbox_module("lineage")


def latest_day() -> datetime.date:
    """The latest day ops.job_runs holds, as a Run value's function in a Project reads it."""
    return latest_partition(runs.dt, example_database.query)


def test_a_run_value_is_drawn_with_its_tag_its_function_and_its_value() -> None:
    TAGS = {"PERIOD_END": latest_day}  # noqa: N806 - as a converted table's logic names it
    built = statement(SELECT(runs.run_id), FROM(runs),
                      WHERE(at_most(runs.dt, script_tag(TAGS["PERIOD_END"]))))
    graph = lineage.build_graph([(built, "recent")])
    (box,) = [box for box in graph.boxes.values() if box["group"] == lineage.RUN_VALUES]
    assert box["name"] == "PERIOD_END = test_run_values.latest_day()"
    assert box["type"] == "gave '2026-09-24'"
    key = next(key for key, each in graph.boxes.items() if each is box)
    # The lookup read ops.job_runs.dt, so the page draws it into the Run value, and the Run
    # value into the condition it is part of.
    assert ("table:ops.job_runs.dt", key, "value") in graph.arrows
    assert any(source == key and graph.boxes[target]["kind"] == "condition"
               for source, target, _ in graph.arrows)


def test_a_run_value_of_a_statement_of_its_own_shows_its_name_and_value() -> None:
    built = statement(SELECT(runs.run_id), FROM(runs),
                      WHERE(at_most(runs.dt, script_tag(period_end))))
    graph = lineage.build_graph([(built, "recent")])
    (box,) = [box for box in graph.boxes.values() if box["group"] == lineage.RUN_VALUES]
    assert box["name"] == "test_run_values.period_end()"
    assert not [arrow for arrow in graph.arrows if arrow[1] in graph.boxes
                and graph.boxes[arrow[1]] is box]


# --- A Run value naming a Partition (Toolbox 8.4, ticket 15) ---------------------------------

# A Saved table written one day at a time, the day named in partition=.
DAILY = Table("mart.daily_counts", partitioned_by=["dt"], key=["job_id", "dt"],
              columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
              location="/data/your_team/mart.db/daily_counts")


def _daily_write(day: object) -> object:
    return statement(INSERT_OVERWRITE(DAILY, partition={"dt": day}),
                     SELECT(runs.job_id, AS(count_rows(), "runs")), FROM(runs),
                     WHERE(equals(runs.dt, day)), GROUP_BY(runs.job_id))


def test_partition_takes_a_script_tags_value_as_its_hive() -> None:
    TAGS = {"RUN_DAY": "'2026-09-24'"}  # noqa: N806 - as a converted table's logic names it
    hive = to_hive(_daily_write(script_tag(TAGS["RUN_DAY"])))
    assert "PARTITION(dt = '2026-09-24')" in hive


def test_a_run_value_naming_a_partition_is_drawn_into_the_column_it_fills() -> None:
    TAGS = {"RUN_DAY": latest_day}  # noqa: N806 - as a converted table's logic names it
    built = _daily_write(script_tag(TAGS["RUN_DAY"]))
    assert "PARTITION(dt = '2026-09-24')" in to_hive(built)
    graph = lineage.build_graph([(built, "daily")])
    keys = [key for key, box in graph.boxes.items() if box["group"] == lineage.RUN_VALUES]
    assert keys
    assert any((key, "table:mart.daily_counts.dt", "value") in graph.arrows for key in keys)


def test_partition_takes_a_run_values_day() -> None:
    hive = to_hive(_daily_write(run_value(period_end)))
    assert "PARTITION(dt = '2026-09-24')" in hive


def test_partition_refuses_a_day_moved_from_a_tag() -> None:
    # Hive's PARTITION(...) takes one value, not date_sub's call on one.
    moved = hive_function("date_sub", script_tag("'2026-09-24'"), 1)
    with pytest.raises(ValueError, match="not a value"):
        INSERT_OVERWRITE(DAILY, partition={"dt": moved})


@pytest.mark.parametrize("write", [INSERT_OVERWRITE, INSERT_INTO],
                         ids=["INSERT_OVERWRITE", "INSERT_INTO"])
def test_partition_still_refuses_a_column_that_reads_a_table(write: object) -> None:
    with pytest.raises(ValueError, match="gives dt the column job_runs.dt, not a value"):
        write(DAILY, partition={"dt": runs.dt})


# --- run_value: any function, traced ----------------------------------------------------------


def days_before(day: datetime.date, days: int) -> datetime.date:
    return day - datetime.timedelta(days=days)


def busiest_day() -> datetime.date:
    """The day of the most runs, from a Statement of its own."""
    rows = run_query(statement(SELECT(runs.dt, AS(count_rows(), "runs")), FROM(runs),
                               WHERE(between(runs.dt, "2026-09-23", "2026-09-24")),
                               GROUP_BY(runs.dt)), example_database.query)
    return datetime.date.fromisoformat(rows.sort_values("runs").iloc[-1]["dt"])


def test_run_value_writes_what_any_function_gives_and_bounds_a_partition() -> None:
    built = statement(SELECT(runs.run_id), FROM(runs),
                      WHERE(at_least(runs.dt, run_value(days_before, period_end(), 1))))
    assert "job_runs.dt >= '2026-09-23'" in to_hive(built)
    graph = lineage.build_graph([(built, "recent")])
    (box,) = [box for box in graph.boxes.values() if box["group"] == lineage.RUN_VALUES]
    assert box["name"] == ("test_run_values.days_before(datetime.date(2026, 9, 24), 1)")
    assert box["type"] == "gave '2026-09-23'"


def test_a_traced_function_that_runs_a_query_draws_the_tables_it_read() -> None:
    built = statement(SELECT(runs.run_id), FROM(runs),
                      WHERE(equals(runs.dt, run_value(busiest_day))))
    assert "job_runs.dt = '2026-09-23'" in to_hive(built)
    graph = lineage.build_graph([(built, "busiest")])
    key = next(key for key, box in graph.boxes.items() if box["group"] == lineage.RUN_VALUES)
    assert ("whole:ops.job_runs", key, "value") in graph.arrows


def test_run_value_refuses_what_isnt_a_function_or_gives_none() -> None:
    with pytest.raises(TypeError, match="not a function"):
        run_value(period_end())
    with pytest.raises(TypeError, match="gave None"):
        run_value(lambda: None)
