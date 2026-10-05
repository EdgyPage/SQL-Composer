"""Worked examples of common jobs: each Statement's result checked against pandas.

Each check reads the Example database's rows directly, not through its send, so it doesn't
rely on sqlglot's executor, the thing it checks.
"""

from __future__ import annotations

import pandas as pd
import pytest

from conftest import example_rows
from sqlglot_composer import example_database, run
from statements import (
    groups_and_top_n,
    jobs_that_never_ran,
    labels_and_counts,
    lists_and_text,
    step_by_step,
)


def runs() -> pd.DataFrame:
    """Every run on the two days the examples read."""
    found = example_rows("job_runs")
    return found[found.dt.between("2026-09-23", "2026-09-24")]


def result(s) -> list[dict]:
    return run(s, send=example_database.send).to_dict("records")


# --- jobs_that_never_ran --------------------------------------------------------------------


@pytest.mark.needs_example_database
def test_the_anti_join_finds_the_job_with_no_runs() -> None:
    jobs = example_rows("jobs")
    never = jobs[~jobs.job_id.isin(runs().job_id)]
    assert result(jobs_that_never_ran.jobs_that_never_ran()) == (
        never[["job_id", "job_name"]].to_dict("records"))
    assert list(never.job_name) == ["cache_warm"]


@pytest.mark.needs_example_database
def test_the_semi_join_lists_each_job_that_ran_once() -> None:
    jobs = example_rows("jobs")
    ran = jobs[jobs.job_id.isin(runs().job_id)]
    found = result(jobs_that_never_ran.jobs_that_ran())
    assert sorted(found, key=lambda row: row["job_id"]) == (
        ran[["job_id", "job_name"]].to_dict("records"))


# --- labels_and_counts ----------------------------------------------------------------------


@pytest.mark.needs_example_database
def test_labels_fill_null_and_split_by_length() -> None:
    expected = pd.DataFrame({
        "run_id": runs().run_id,
        "status": runs().status.fillna("RUNNING"),
        "length": ["long" if m > 20 else "short" for m in runs().duration_mins],
    })
    assert result(labels_and_counts.labelled_runs()) == expected.to_dict("records")


@pytest.mark.needs_example_database
def test_one_row_per_job_with_a_count_of_each_outcome() -> None:
    found = runs().assign(
        succeeded=runs().status.eq("SUCCESS"),
        failed=runs().status.eq("FAILED"),
        still_running=runs().status.isna(),
    )
    expected = found.groupby("job_id")[["succeeded", "failed", "still_running"]].sum()
    assert result(labels_and_counts.outcomes_per_job()) == (
        expected.reset_index().to_dict("records"))


@pytest.mark.needs_example_database
def test_each_jobs_failed_runs_as_a_percent_of_its_runs() -> None:
    per_job = runs().assign(failed=runs().status.eq("FAILED")).groupby("job_id").failed
    expected = (per_job.sum() * 100.0 / per_job.size()).rename("failed_percent")
    assert result(labels_and_counts.failed_share_per_job()) == (
        expected.reset_index().to_dict("records"))
    assert [row["failed_percent"] for row in expected.reset_index().to_dict("records")] == [
        0.0, 100.0 / 3, 50.0]


# --- groups_and_top_n -----------------------------------------------------------------------


@pytest.mark.needs_example_database
def test_distinct_counts_having_and_top_n() -> None:
    assert sorted(row["team"] for row in result(groups_and_top_n.teams())) == sorted(
        example_rows("jobs").team.unique())

    per_job = runs().groupby("job_id").agg(runs=("run_id", "size"),
                                            days_with_runs=("dt", "nunique"))
    assert result(groups_and_top_n.runs_and_days_per_job()) == (
        per_job.reset_index().to_dict("records"))

    busy = per_job[per_job.runs >= 3][["runs"]]
    assert result(groups_and_top_n.busy_jobs()) == busy.reset_index().to_dict("records")

    minutes = runs().groupby("job_id").duration_mins.sum().nlargest(2)
    assert result(groups_and_top_n.two_longest_running_jobs()) == [
        {"job_id": job, "minutes": total} for job, total in minutes.items()]


# --- lists_and_text -------------------------------------------------------------------------


@pytest.mark.needs_example_database
@pytest.mark.parametrize(
    ("statement", "keep"),
    [
        ("runs_of_listed_jobs", lambda r: r.job_id.isin([1, 3])),
        # NOT IN drops the run still going (status NULL), unlike pandas' ~isin.
        ("runs_that_did_not_pass",
         lambda r: r.status.notna() & ~r.status.isin(["TEST", "SUCCESS"])),
        ("runs_to_check", lambda r: r.status.eq("FAILED") | r.status.isna()),
    ],
)
def test_lists_and_either_condition(statement: str, keep) -> None:
    kept = runs()[keep(runs())]
    found = result(getattr(lists_and_text, statement)())
    assert [row["run_id"] for row in found] == list(kept.run_id)


@pytest.mark.needs_example_database
def test_the_still_running_run_is_dropped_by_not_in_and_kept_by_is_null() -> None:
    dropped = [row["run_id"] for row in result(lists_and_text.runs_that_did_not_pass())]
    kept = [row["run_id"] for row in result(lists_and_text.runs_to_check())]
    assert 98 not in dropped and 98 in kept


@pytest.mark.needs_example_database
def test_text_matching_takes_underscore_as_itself() -> None:
    jobs = example_rows("jobs")
    names = jobs.job_name
    kept = jobs[names.str.startswith("invoice") | names.str.contains("_build", regex=False)]
    assert result(lists_and_text.jobs_by_name()) == (
        kept[["job_id", "job_name"]].to_dict("records"))


# --- step_by_step ---------------------------------------------------------------------------


@pytest.mark.needs_example_database
def test_each_step_reads_the_one_before_it() -> None:
    per_job = runs().groupby("job_id").agg(runs=("run_id", "size"),
                                            minutes=("duration_mins", "sum"))
    assert result(step_by_step.minutes_per_job()) == per_job.reset_index().to_dict("records")

    teams = per_job.join(example_rows("jobs").set_index("job_id").team)
    per_team = teams.groupby("team")[["runs", "minutes"]].sum().reset_index()
    found = sorted(result(step_by_step.minutes_per_team()), key=lambda row: row["team"])
    assert found == per_team.to_dict("records")

    busy = per_team[per_team.minutes >= 100][["team", "minutes"]]
    assert result(step_by_step.busy_teams()) == busy.to_dict("records")
    assert list(busy.team) == ["finance"]
