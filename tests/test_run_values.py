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

import pytest
from conftest import forget_the_projects_modules, toolbox_module

from sqlglot_composer import (
    FROM,
    SELECT,
    WHERE,
    at_most,
    between,
    example_database,
    hive_function,
    project,
    run_query,
    script_tag,
    statement,
    tag_text,
    to_hive,
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
    assert ("from building_blocks.run_values import period_end  # a Run value, for TAGS"
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
