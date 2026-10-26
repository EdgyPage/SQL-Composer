"""first_match and mapped: an if/else chain, or a lookup on one column, as one CASE.

Toolbox 7.2, ticket 04. A Conversion writes them for the Hive's if/else chains, and the user
writes them by hand: first_match for a chain of conditions, the first that holds winning, and
mapped for a lookup of one column's values.
"""

from __future__ import annotations

import datetime
from pathlib import Path

import pandas as pd
import pytest

from conftest import example_rows
from sqlglot_composer import (
    AS,
    FROM,
    SELECT,
    WHERE,
    GuardRefused,
    Statement,
    average_of,
    between,
    equals,
    example_database,
    export_lineage,
    first_match,
    is_null,
    mapped,
    more_than,
    run_query,
    statement,
    sum_of,
    to_hive,
)
from sqlglot_composer.example_database import job_runs


def test_first_match_writes_one_case_the_first_condition_that_holds_winning() -> None:
    length = first_match([(more_than(job_runs.duration_mins, 60), "very long"),
                          (more_than(job_runs.duration_mins, 20), "long")],
                         otherwise="short")
    assert repr(length) == ("CASE WHEN job_runs.duration_mins > 60 THEN 'very long' "
                            "WHEN job_runs.duration_mins > 20 THEN 'long' ELSE 'short' END")


def test_first_match_with_no_otherwise_writes_no_else() -> None:
    failed = first_match([(equals(job_runs.status, "FAILED"), 1)])
    assert repr(failed) == "CASE WHEN job_runs.status = 'FAILED' THEN 1 END"


def test_mapped_writes_a_case_on_its_column() -> None:
    label = mapped(job_runs.status, {"FAILED": "Failed", "SUCCESS": "Passed"},
                   otherwise="Other")
    assert repr(label) == ("CASE job_runs.status WHEN 'FAILED' THEN 'Failed' "
                           "WHEN 'SUCCESS' THEN 'Passed' ELSE 'Other' END")


def test_mapped_with_no_otherwise_writes_no_else() -> None:
    assert repr(mapped(job_runs.job_id, {1: "nightly"})) == (
        "CASE job_runs.job_id WHEN 1 THEN 'nightly' END")


def labelled_runs() -> Statement:
    return statement(
        SELECT(job_runs.run_id,
               AS(first_match([(is_null(job_runs.status), "running"),
                               (more_than(job_runs.duration_mins, 20), "long")],
                              otherwise="short"), "length"),
               AS(mapped(job_runs.status, {"FAILED": "Failed", "SUCCESS": "Passed"}),
                  "outcome")),
        FROM(job_runs),
        WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
    )


def test_both_write_their_case_in_a_statement() -> None:
    """to_hive reads its Hive back and writes it again, so this is also Hive that reads back
    the same, the simple CASE of mapped included."""
    assert to_hive(labelled_runs()) == (
        "SELECT\n"
        "  job_runs.run_id,\n"
        "  CASE\n"
        "    WHEN job_runs.status IS NULL\n"
        "    THEN 'running'\n"
        "    WHEN job_runs.duration_mins > 20\n"
        "    THEN 'long'\n"
        "    ELSE 'short'\n"
        "  END AS length,\n"
        "  CASE job_runs.status WHEN 'FAILED' THEN 'Failed' WHEN 'SUCCESS' THEN 'Passed' END"
        " AS outcome\n"
        "FROM ops.job_runs AS job_runs\n"
        "WHERE\n"
        "  job_runs.dt BETWEEN '2026-09-23' AND '2026-09-24'")


def test_lineage_traces_every_column_either_reads_and_shows_the_call(tmp_path: Path) -> None:
    """Its conditions' columns, its values' columns and, for mapped, the column it looks up."""
    minutes = statement(
        SELECT(job_runs.run_id,
               AS(first_match([(is_null(job_runs.status), job_runs.avg_retry_secs)],
                              otherwise=job_runs.duration_mins), "minutes"),
               AS(mapped(job_runs.job_id, {1: job_runs.status}, otherwise="other"),
                  "label")),
        FROM(job_runs),
        WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
    )
    _, markdown = export_lineage(minutes, to=tmp_path / "lineage.html")
    report = markdown.read_text(encoding="utf-8")
    assert ("minutes.minutes = first_match([(is_null(job_runs.status), job_runs.avg_retry_secs)],"
            " otherwise=job_runs.duration_mins)\n"
            # In the order a breadth-first walk of the CASE finds them, as for any calculation.
            "├─ ops.job_runs.duration_mins  (int)\n"
            "├─ ops.job_runs.avg_retry_secs  (double)\n"
            "└─ ops.job_runs.status  (string)\n") in report
    assert ('minutes.label = mapped(job_runs.job_id, {1: job_runs.status}, otherwise="other")\n'
            "├─ ops.job_runs.job_id  (bigint)\n"
            "└─ ops.job_runs.status  (string)\n") in report


def test_a_none_key_is_refused_as_equals_refuses_none() -> None:
    """NULL equals nothing, so CASE status WHEN NULL would never match: the Guard equals runs."""
    with pytest.raises(GuardRefused, match=r"mapped\(job_runs.status, \.\.\.\) compares with None"):
        mapped(job_runs.status, {None: "running"})


def test_a_value_may_be_none_and_otherwise_none_writes_no_else() -> None:
    """None as a value is NULL, which goes with a value of any type."""
    assert repr(first_match([(equals(job_runs.status, "FAILED"), None),
                             (is_null(job_runs.status), 0)])) == (
        "CASE WHEN job_runs.status = 'FAILED' THEN NULL WHEN job_runs.status IS NULL THEN 0 END")


def test_values_of_the_same_family_mix() -> None:
    """A float beside an int, or a date beside a string, both stand in one column."""
    assert repr(mapped(job_runs.status, {"FAILED": 0.5}, otherwise=1)) == (
        "CASE job_runs.status WHEN 'FAILED' THEN 0.5 ELSE 1 END")
    assert repr(first_match([(equals(job_runs.status, "FAILED"), datetime.date(2026, 9, 24))],
                            otherwise=job_runs.dt)) == (
        "CASE WHEN job_runs.status = 'FAILED' THEN '2026-09-24' ELSE job_runs.dt END")


def test_it_adds_up_unless_a_value_doesnt() -> None:
    """As if_else: a CASE over an average is no total to add up again."""
    average = average_of(job_runs.duration_mins)
    with pytest.raises(GuardRefused, match="which is an average"):
        sum_of(first_match([(equals(job_runs.status, "FAILED"), average)], otherwise=0))
    assert repr(sum_of(mapped(job_runs.status, {"FAILED": job_runs.duration_mins}))) == (
        "SUM(CASE job_runs.status WHEN 'FAILED' THEN job_runs.duration_mins END)")


@pytest.mark.needs_example_database
def test_the_first_condition_that_holds_wins_and_an_unmatched_row_is_null() -> None:
    runs = example_rows("job_runs")
    runs = runs[runs.dt.between("2026-09-23", "2026-09-24")]
    # Worked out by hand in pandas: a running row is "running" whatever its minutes.
    length = ["running" if pd.isna(status) else "long" if minutes > 20 else "short"
              for status, minutes in zip(runs.status, runs.duration_mins)]
    outcome = [{"FAILED": "Failed", "SUCCESS": "Passed"}.get(status) for status in runs.status]
    found = run_query(labelled_runs(), example_database.query)
    assert list(found.run_id) == list(runs.run_id)
    assert list(found.length) == length
    assert [None if pd.isna(value) else value for value in found.outcome] == outcome
    # The Example database has runs of each kind, so each branch is taken.
    assert {"running", "long", "short"} <= set(length)
    assert None in outcome and "Failed" in outcome and "Passed" in outcome
