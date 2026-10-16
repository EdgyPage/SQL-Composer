"""A write into a Saved table with no days (date_partition=None): written whole.

INSERT_OVERWRITE replaces the whole table and INSERT_INTO adds to it, with no PARTITION, the
SELECT giving the table's columns in its order. Every other check of a write still applies;
what only makes sense one day at a time refuses such a table, saying what to do instead.
"""

from __future__ import annotations

import pytest

from sqlglot_composer import (
    AS,
    FROM,
    GROUP_BY,
    INSERT_INTO,
    INSERT_OVERWRITE,
    JOIN,
    SELECT,
    SELECT_DISTINCT,
    UNION,
    WHERE,
    GuardRefused,
    LoadRefused,
    Table,
    between,
    by_day,
    count_rows,
    derived,
    create_table,
    equals,
    export_lineage,
    rollup,
    set_load_limits,
    show_hive,
    statement,
    to_hive,
)
from composer_core.example_database import job_runs, jobs

DAYS = between(job_runs.dt, "2026-09-23", "2026-09-24")

job_teams = Table("mart.job_teams", columns={"team": "string", "job_id": "bigint"},
                  date_partition=None, key=["job_id"], location="/data/your_team/tables")
"""Each job's team, with no days: written whole each time."""

team_runs = Table("mart.team_runs", columns={"team": "string", "runs": "bigint"},
                  date_partition=None, key=["team"], location="/data/your_team/tables")
"""Each team's runs over the days read, with no days."""


def teams() -> object:
    return statement(INSERT_OVERWRITE(job_teams), SELECT_DISTINCT(jobs.job_id, jobs.team),
                     FROM(jobs))


# --- What it writes --------------------------------------------------------------------------


def test_insert_overwrite_writes_the_whole_table_in_its_column_order() -> None:
    assert to_hive(teams()) == (
        "INSERT OVERWRITE TABLE mart.job_teams\n"
        "SELECT DISTINCT\n"
        "  jobs.team,\n"
        "  jobs.job_id\n"
        "FROM ops.jobs AS jobs")


def test_insert_into_adds_to_the_whole_table() -> None:
    s = statement(INSERT_INTO(job_teams), SELECT_DISTINCT(jobs.job_id, jobs.team), FROM(jobs))
    assert to_hive(s).startswith("INSERT INTO mart.job_teams\nSELECT DISTINCT\n")


def test_a_write_with_no_days_may_read_several_days_of_a_dated_table() -> None:
    s = statement(INSERT_OVERWRITE(team_runs), SELECT(jobs.team, AS(count_rows(), "runs")),
                  FROM(job_runs), JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
                  WHERE(DAYS), GROUP_BY(jobs.team))
    hive = to_hive(s)
    assert hive.startswith("INSERT OVERWRITE TABLE mart.team_runs\nSELECT\n")
    assert "job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'" in hive


def test_a_stack_writes_the_whole_table() -> None:
    each = [statement(SELECT(jobs.team, jobs.job_id), FROM(jobs),
                      WHERE(equals(jobs.team, team))) for team in ("data", "finance")]
    both = derived("both", UNION(*each))
    s = statement(INSERT_OVERWRITE(job_teams, unproven_key=True), SELECT(both.team, both.job_id),
                  FROM(both))
    hive = to_hive(s)
    assert "UNION" in hive and "INSERT OVERWRITE TABLE mart.job_teams\nSELECT\n" in hive


def test_show_hive_and_create_table_take_it() -> None:
    assert show_hive(teams()).startswith("INSERT OVERWRITE TABLE mart.job_teams")
    assert "PARTITIONED BY" not in to_hive(create_table(job_teams))


# --- Every other check still applies --------------------------------------------------------


def test_the_key_check_still_applies() -> None:
    with pytest.raises(GuardRefused, match="unproven_key=True"):
        statement(INSERT_OVERWRITE(job_teams), SELECT(jobs.team, job_runs.job_id),
                  FROM(job_runs), JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
                  WHERE(DAYS))
    every_run = statement(INSERT_OVERWRITE(job_teams, unproven_key=True),
                          SELECT(jobs.team, job_runs.job_id), FROM(job_runs),
                          JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)), WHERE(DAYS))
    assert to_hive(every_run).startswith("INSERT OVERWRITE TABLE mart.job_teams")


def test_a_dated_table_it_reads_still_needs_its_days_bounded() -> None:
    with pytest.raises(LoadRefused, match="job_runs.dt"):
        statement(INSERT_OVERWRITE(team_runs), SELECT(jobs.team, AS(count_rows(), "runs")),
                  FROM(job_runs), JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
                  GROUP_BY(jobs.team))


def test_the_dates_cap_still_applies() -> None:
    set_load_limits(dates=1)
    try:
        s = statement(INSERT_OVERWRITE(team_runs), SELECT(jobs.team, AS(count_rows(), "runs")),
                      FROM(job_runs), JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
                      WHERE(DAYS), GROUP_BY(jobs.team))
        with pytest.raises(LoadRefused):
            to_hive(s)
    finally:
        set_load_limits()


def test_subtotals_are_still_refused() -> None:
    with pytest.raises(ValueError, match="subtotal"):
        to_hive(statement(INSERT_OVERWRITE(team_runs),
                          SELECT(jobs.team, AS(count_rows(), "runs")), FROM(jobs),
                          GROUP_BY(rollup(jobs.team))))


def test_its_columns_must_still_line_up() -> None:
    with pytest.raises(GuardRefused, match="team"):
        to_hive(statement(INSERT_OVERWRITE(job_teams), SELECT_DISTINCT(jobs.job_id),
                          FROM(jobs)))


# --- What works one day at a time refuses it ------------------------------------------------


def test_by_day_refuses_a_write_with_no_days() -> None:
    s = statement(INSERT_OVERWRITE(team_runs), SELECT(jobs.team, AS(count_rows(), "runs")),
                  FROM(job_runs), JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
                  WHERE(DAYS), GROUP_BY(jobs.team))
    with pytest.raises(ValueError, match="mart.team_runs, which has no Date partition") as refused:
        by_day(s)
    assert "run(s, send=...)" in str(refused.value)


# --- Lineage ---------------------------------------------------------------------------------


def test_lineage_draws_a_write_with_no_days(tmp_path) -> None:
    html_file, markdown_file = export_lineage(teams(), to=tmp_path / "l.html")
    text = markdown_file.read_text(encoding="utf-8")
    assert "mart.job_teams" in text and "one day at a time" not in text
    assert "the whole Saved table mart.job_teams" in text
    assert "day written" not in text.split("```mermaid", 1)[1].split("```", 1)[0]


def test_lineage_of_a_write_with_no_days_refused_by_the_dates_cap(tmp_path) -> None:
    # by_day can't help a write with no days, so lineage doesn't suggest it.
    set_load_limits(dates=1)
    try:
        s = statement(INSERT_OVERWRITE(team_runs), SELECT(jobs.team, AS(count_rows(), "runs")),
                      FROM(job_runs), JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
                      WHERE(DAYS), GROUP_BY(jobs.team))
        with pytest.raises(LoadRefused):
            export_lineage(s, to=tmp_path / "l.html")
    finally:
        set_load_limits()
