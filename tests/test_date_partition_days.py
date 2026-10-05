"""The days a Statement reads on a Date partition, seen through the Load limits and by_day."""

from __future__ import annotations

import re

import pytest

from sqlglot_composer import (
    FROM,
    INSERT_OVERWRITE,
    LoadRefused,
    SELECT,
    Table,
    WHERE,
    any_of,
    at_least,
    at_most,
    between,
    by_day,
    equals,
    is_in,
    is_not_in,
    less_than,
    more_than,
    not_equals,
    set_load_limits,
    statement,
    to_hive,
)
from composer_core.example_database import job_runs

dt = job_runs.dt


def reading(*conditions):
    return statement(SELECT(job_runs.run_id), FROM(job_runs), WHERE(*conditions))


def days_of(s) -> list[str]:
    """The day each of by_day's Statements reads, from the bound by_day writes last."""
    return [re.findall(r"job_runs\.dt = ('[^']*')", to_hive(day))[-1] for day in by_day(s)]


@pytest.mark.parametrize("day", ["2026-9-24", "2026-09-4", "26-09-24", " 2026-09-24"])
def test_a_day_must_be_written_exactly_like_the_date_format(day) -> None:
    with pytest.raises(ValueError, match="isn't a day written like '2026-09-"):
        statement(SELECT(job_runs.run_id), FROM(job_runs), WHERE(equals(job_runs.dt, day)))


@pytest.mark.parametrize("pattern", ["%d-%m-%Y", "%m/%d/%Y", "%Y%d%m", "%Y%m%dT", "%Ya%mb%d"])
def test_a_date_format_must_sort_as_text_year_first(pattern) -> None:
    with pytest.raises(ValueError, match="date_partition=None"):
        Table("ops.odd_days", columns={"dt": "string"}, date_partition="dt",
              date_format=pattern)


def test_a_letter_in_a_date_format_is_named() -> None:
    with pytest.raises(ValueError, match="besides %Y, %m, %d and separators: 'd', 't'"):
        Table("ops.odd_days", columns={"dt": "string"}, date_partition="dt",
              date_format="dt=%Y-%m-%d")


def test_a_day_python_reads_is_shown_as_it_should_be_written() -> None:
    with pytest.raises(ValueError, match="Write the day as '2026-09-24'"):
        equals(dt, "2026-9-24")


@pytest.mark.parametrize("pattern", ["%Y-%m-%d", "%Y%m%d", "%Y/%m/%d", "%Y_%m_%d", "%Y.%m.%d"])
def test_a_year_first_date_format_is_taken(pattern) -> None:
    Table("ops.days", columns={"dt": "string"}, date_partition="dt", date_format=pattern)


# --- Two bounds on one Date partition --------------------------------------------------------

TWO_BOUNDS = [
    pytest.param([at_least(dt, "2026-09-22"), at_most(dt, "2026-09-24")],
                 ["'2026-09-22'", "'2026-09-23'", "'2026-09-24'"], id="at_least_and_at_most"),
    pytest.param([more_than(dt, "2026-09-21"), less_than(dt, "2026-09-24")],
                 ["'2026-09-22'", "'2026-09-23'"], id="more_than_and_less_than"),
    pytest.param([is_in(dt, ["2026-09-20", "2026-09-23", "2026-09-24"]),
                  between(dt, "2026-09-21", "2026-09-30")],
                 ["'2026-09-23'", "'2026-09-24'"], id="a_list_and_a_range"),
    pytest.param([between(dt, "2026-09-22", "2026-09-24"), not_equals(dt, "2026-09-23")],
                 ["'2026-09-22'", "'2026-09-24'"], id="a_range_and_a_day_left_out"),
    pytest.param([is_in(dt, ["2026-09-22", "2026-09-23", "2026-09-24"]),
                  is_not_in(dt, ["2026-09-22", "2026-09-24"])],
                 ["'2026-09-23'"], id="a_list_and_days_left_out"),
    pytest.param([any_of(equals(dt, "2026-09-01"), between(dt, "2026-09-23", "2026-09-24"))],
                 ["'2026-09-01'", "'2026-09-23'", "'2026-09-24'"], id="a_day_or_a_range"),
    pytest.param([any_of(equals(dt, "2026-09-20"), at_least(dt, "2026-09-23")),
                  at_most(dt, "2026-09-24")],
                 ["'2026-09-20'", "'2026-09-23'", "'2026-09-24'"],
                 id="a_day_or_from_a_day_on_then_a_range"),
    pytest.param([any_of(is_not_in(dt, ["2026-09-23", "2026-09-24"]),
                         is_not_in(dt, ["2026-09-24", "2026-09-25"])),
                  between(dt, "2026-09-22", "2026-09-25")],
                 ["'2026-09-22'", "'2026-09-23'", "'2026-09-25'"],
                 id="days_left_out_by_both_sides_of_any_of"),
]


@pytest.mark.parametrize(("conditions", "days"), TWO_BOUNDS)
def test_by_day_reads_exactly_the_days_the_bounds_let_through(conditions, days) -> None:
    assert days_of(reading(*conditions)) == days


@pytest.mark.parametrize(("conditions", "days"), TWO_BOUNDS)
def test_the_dates_load_limit_counts_only_those_days(conditions, days) -> None:
    set_load_limits(dates=len(days))
    to_hive(reading(*conditions))
    if len(days) > 1:
        set_load_limits(dates=len(days) - 1)
        with pytest.raises(LoadRefused, match=f"reads {len(days)} days"):
            to_hive(reading(*conditions))


def test_a_day_left_out_is_never_written() -> None:
    daily = Table("mart.daily_runs", columns={"dt": "string", "run_id": "bigint"},
                  date_partition="dt")
    s = statement(INSERT_OVERWRITE(daily), SELECT(job_runs.run_id), FROM(job_runs),
                  WHERE(between(dt, "2026-09-22", "2026-09-24"), not_equals(dt, "2026-09-23")))
    written = [to_hive(day).splitlines()[0] for day in by_day(s)]
    assert written == ["INSERT OVERWRITE TABLE mart.daily_runs PARTITION(dt = '2026-09-22')",
                       "INSERT OVERWRITE TABLE mart.daily_runs PARTITION(dt = '2026-09-24')"]


def test_a_day_any_of_rules_out_is_never_written() -> None:
    daily = Table("mart.daily_runs", columns={"dt": "string", "run_id": "bigint"},
                  date_partition="dt")
    s = statement(INSERT_OVERWRITE(daily), SELECT(job_runs.run_id), FROM(job_runs),
                  WHERE(any_of(equals(dt, "2026-09-20"), at_least(dt, "2026-09-23")),
                        at_most(dt, "2026-09-24")))
    written = [re.findall(r"PARTITION\(dt = ('[^']*')\)", to_hive(day))[0] for day in by_day(s)]
    assert written == ["'2026-09-20'", "'2026-09-23'", "'2026-09-24'"]


def test_a_day_left_out_must_be_written_like_the_date_format_too() -> None:
    with pytest.raises(ValueError, match="isn't a day written like"):
        is_not_in(dt, ["2026-9-24"])


def test_by_day_refuses_a_where_that_leaves_no_day() -> None:
    with pytest.raises(ValueError, match="leaves no day of job_runs.dt to read"):
        by_day(reading(at_least(dt, "2026-09-24"), at_most(dt, "2026-09-20")))
    with pytest.raises(ValueError, match="leaves no day of job_runs.dt to read"):
        by_day(reading(equals(dt, "2026-09-24"), not_equals(dt, "2026-09-24")))
