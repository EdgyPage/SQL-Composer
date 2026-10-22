"""A write into a Saved table with no partitioned_by=: written whole.

INSERT_OVERWRITE replaces the whole table and INSERT_INTO adds to it, with no PARTITION, the
SELECT giving the table's columns in its order. Every other check of a write still applies,
and a table someone else owns, which such a write would empty, is refused.
"""

from __future__ import annotations

from pathlib import Path

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
    Statement,
    Table,
    between,
    count_rows,
    create_table,
    derived,
    equals,
    export_lineage,
    lag,
    rollup,
    show_hive,
    statement,
    to_hive,
    window,
)
from sqlglot_composer.example_database import job_runs, jobs

DAYS = between(job_runs.dt, "2026-09-23", "2026-09-24")

job_teams = Table("mart.job_teams", columns={"team": "string", "job_id": "bigint"},
                  key=["job_id"], location="/data/your_team/mart.db/job_teams")
"""Each job's team, unpartitioned: written whole each time."""

team_runs = Table("mart.team_runs", columns={"team": "string", "runs": "bigint"},
                  key=["team"], location="/data/your_team/mart.db/team_runs")
"""Each team's runs over the days read, unpartitioned."""


def teams() -> Statement:
    return statement(INSERT_OVERWRITE(job_teams), SELECT_DISTINCT(jobs.job_id, jobs.team),
                     FROM(jobs))


def runs_per_team() -> Statement:
    return statement(INSERT_OVERWRITE(team_runs), SELECT(jobs.team, AS(count_rows(), "runs")),
                     FROM(job_runs), JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
                     WHERE(DAYS), GROUP_BY(jobs.team))


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


def test_a_write_into_an_unpartitioned_table_may_read_several_days_of_a_partitioned_one(
) -> None:
    hive = to_hive(runs_per_team())
    assert hive.startswith("INSERT OVERWRITE TABLE mart.team_runs\nSELECT\n")
    assert "job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'" in hive


def test_a_window_over_several_days_may_be_written_into_it() -> None:
    with_before = derived("with_before", statement(
        SELECT(job_runs.job_id, job_runs.dt,
               AS(lag(job_runs.duration_mins, over=window(PARTITION_BY=job_runs.job_id,
                                                          ORDER_BY=job_runs.run_id)), "before")),
        FROM(job_runs), WHERE(DAYS)))
    s = statement(INSERT_OVERWRITE(job_teams, unproven_key=True),
                  SELECT(AS(with_before.job_id, "job_id"), AS(with_before.dt, "team")),
                  FROM(with_before), WHERE(equals(with_before.dt, "2026-09-24")))
    assert to_hive(s).splitlines()[-1] == "  with_before.dt = '2026-09-24'"


def test_a_stack_writes_the_whole_table() -> None:
    each = [statement(SELECT(jobs.team, jobs.job_id), FROM(jobs),
                      WHERE(equals(jobs.team, team))) for team in ("data", "finance")]
    both = derived("both", UNION(*each))
    s = statement(INSERT_OVERWRITE(job_teams, unproven_key=True), SELECT(both.team, both.job_id),
                  FROM(both))
    hive = to_hive(s)
    assert "UNION" in hive and "INSERT OVERWRITE TABLE mart.job_teams\nSELECT\n" in hive


def test_show_hive_prints_no_session_setting_and_create_table_no_partitions() -> None:
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


def test_a_partitioned_table_it_reads_still_needs_a_partition_column_filtered() -> None:
    with pytest.raises(LoadRefused, match="job_runs.dt"):
        statement(INSERT_OVERWRITE(team_runs), SELECT(jobs.team, AS(count_rows(), "runs")),
                  FROM(job_runs), JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
                  GROUP_BY(jobs.team))


def test_subtotals_are_still_refused() -> None:
    with pytest.raises(ValueError, match="subtotal"):
        to_hive(statement(INSERT_OVERWRITE(team_runs),
                          SELECT(jobs.team, AS(count_rows(), "runs")), FROM(jobs),
                          GROUP_BY(rollup(jobs.team))))


def test_its_columns_must_still_line_up() -> None:
    with pytest.raises(GuardRefused, match="team"):
        to_hive(statement(INSERT_OVERWRITE(job_teams), SELECT_DISTINCT(jobs.job_id),
                          FROM(jobs)))


def test_an_unpartitioned_table_that_isnt_one_of_your_saved_tables_is_refused() -> None:
    # Written whole, a table someone else owns would lose every row it holds.
    theirs = Table("ops.job_teams", columns={"team": "string", "job_id": "bigint"},
                   key=["job_id"])
    for write in (INSERT_OVERWRITE, INSERT_INTO):
        with pytest.raises(ValueError, match="isn't one of your Saved tables"):
            write(theirs)


# --- Lineage ---------------------------------------------------------------------------------


def test_lineage_draws_a_write_into_an_unpartitioned_table(tmp_path: Path) -> None:
    html_file, markdown_file = export_lineage(teams(), to=tmp_path / "l.html")
    text = markdown_file.read_text(encoding="utf-8")
    assert "the whole Saved table mart.job_teams" in text
    assert "day" not in text.split("```mermaid", 1)[1].split("```", 1)[0]


def test_lineage_draws_a_write_that_reads_every_partition(tmp_path: Path) -> None:
    unbounded = statement(INSERT_OVERWRITE(team_runs), SELECT(jobs.team, AS(count_rows(), "runs")),
                          FROM(job_runs, reads_all_partitions=True),
                          JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
                          GROUP_BY(jobs.team))
    html_file, _ = export_lineage(unbounded, to=tmp_path / "l.html")
    assert html_file.exists()
