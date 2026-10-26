"""Checking a Conversion (Toolbox 7.2, ticket 08): a Statement compared with the Hive it was
converted from, by its Hive with compare_hive and by its rows with compare_with_original.

compare_hive reads both with sqlglot and writes them out one way, so what doesn't change the
query doesn't count; compare_with_original sends one query through `query` that matches the
rows of both on every column.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from pathlib import Path

import pandas as pd
import pytest

from sqlglot_composer import (
    AS,
    FROM,
    GROUP_BY,
    INSERT_OVERWRITE,
    LEFT_JOIN,
    SELECT,
    WHERE,
    Condition,
    Statement,
    Table,
    all_columns,
    any_of,
    compare_hive,
    compare_with_original,
    count_rows,
    derived,
    equals,
    example_database,
    explain,
    hive_function,
    is_null,
    not_equals,
    set_load_limits,
    statement,
    unchecked_column,
)
from sqlglot_composer.example_database import job_runs, jobs

DAY = "2026-09-24"


def runs_on(day: str = DAY) -> Statement:
    return statement(SELECT(job_runs.run_id, job_runs.status), FROM(job_runs),
                     WHERE(equals(job_runs.dt, day)))


# --- compare_hive ----------------------------------------------------------------------------


@pytest.mark.parametrize("original", [
    pytest.param("SELECT job_runs.run_id, job_runs.status FROM ops.job_runs AS job_runs "
                 f"WHERE job_runs.dt = '{DAY}'", id="the_same_text_on_one_line"),
    pytest.param(f"select RUN_ID, `status`\n  from OPS.JOB_RUNS\n where (dt = '{DAY}');",
                 id="case_backticks_brackets_and_a_semicolon"),
    pytest.param(f"SELECT r.run_id, r.status -- the runs\nFROM ops.job_runs r WHERE r.dt = '{DAY}'",
                 id="a_short_name_for_the_table_and_a_comment"),
    pytest.param(f"SELECT r.run_id AS run_id, r.status FROM ops.job_runs AS r "
                 f"WHERE r.dt = '{DAY}'", id="as_with_the_columns_own_name"),
])
def test_what_doesnt_change_the_query_doesnt_count(original: str) -> None:
    verdict = compare_hive(runs_on(), original)
    assert verdict.ok, verdict
    assert repr(verdict) == ("The Statement's Hive and the original are the same query, once "
                             "both are written out the same way.")


def test_an_insert_is_compared_by_the_select_it_writes() -> None:
    original = ("WITH day_runs AS (SELECT run_id, status FROM ops.job_runs WHERE dt = "
                f"'{DAY}')\nINSERT OVERWRITE TABLE mart.day_runs PARTITION (dt = '{DAY}')\n"
                "SELECT d.run_id, d.status FROM day_runs d")
    day_runs = derived("day_runs", runs_on())
    converted = statement(SELECT(day_runs.run_id, day_runs.status), FROM(day_runs))
    assert compare_hive(converted, original).ok



@pytest.mark.parametrize("original", [
    pytest.param("SELECT day_runs.run_id, day_runs.status FROM (SELECT run_id, status FROM "
                 f"ops.job_runs WHERE dt = '{DAY}') day_runs", id="a_subquery_in_from"),
    pytest.param(f"SELECT * FROM (SELECT run_id, status FROM ops.job_runs WHERE dt = '{DAY}') "
                 "day_runs", id="a_star_over_it"),
])
def test_a_subquery_in_from_is_the_derived_table_it_writes(original: str) -> None:
    """A Derived table is written as a WITH; the original's subquery in FROM is the same."""
    day_runs = derived("day_runs", runs_on())
    converted = statement(SELECT(*all_columns(day_runs)), FROM(day_runs))
    assert compare_hive(converted, original).ok, compare_hive(converted, original)


def test_a_subquery_in_a_join_is_the_derived_table_it_writes() -> None:
    day_runs = derived("day_runs", statement(
        SELECT(job_runs.job_id, AS(count_rows(), "runs")), FROM(job_runs),
        WHERE(equals(job_runs.dt, DAY)), GROUP_BY(job_runs.job_id)))
    converted = statement(SELECT(jobs.team, day_runs.runs), FROM(jobs),
                          LEFT_JOIN(day_runs, ON=equals(day_runs.job_id, jobs.job_id)))
    original = ("SELECT j.team, day_runs.runs FROM ops.jobs j LEFT JOIN (SELECT job_id, "
                f"COUNT(*) AS runs FROM ops.job_runs WHERE dt = '{DAY}' GROUP BY job_id) "
                "day_runs ON day_runs.job_id = j.job_id")
    assert compare_hive(converted, original).ok, compare_hive(converted, original)
    assert not compare_hive(converted, original.replace(DAY, FIRST_DAY)).ok

def test_inner_outer_and_the_case_of_a_function_dont_count() -> None:
    converted = statement(
        SELECT(job_runs.run_id, jobs.team, AS(hive_function("nvl", job_runs.status, "-"),
                                              "status")),
        FROM(job_runs), LEFT_JOIN(jobs, ON=equals(job_runs.job_id, jobs.job_id)),
        WHERE(equals(job_runs.dt, DAY)))
    original = ("SELECT r.run_id, j.team, Nvl(r.status, '-') AS status FROM ops.job_runs r "
                "LEFT OUTER JOIN ops.jobs j ON r.job_id = j.job_id WHERE r.dt = '2026-09-24'")
    assert compare_hive(converted, original).ok, compare_hive(converted, original)


def test_a_bracket_that_changes_the_order_counts() -> None:
    converted = statement(SELECT(job_runs.run_id, AS((job_runs.duration_mins + 1) * 2, "x")),
                          FROM(job_runs), WHERE(equals(job_runs.dt, DAY)))
    same = f"SELECT run_id, ((duration_mins + 1)) * 2 AS x FROM ops.job_runs WHERE dt = '{DAY}'"
    other = f"SELECT run_id, duration_mins + 1 * 2 AS x FROM ops.job_runs WHERE dt = '{DAY}'"
    assert compare_hive(converted, same).ok
    assert not compare_hive(converted, other).ok


def test_the_load_limits_automatic_limit_isnt_compared() -> None:
    set_load_limits(rows=1000)
    assert compare_hive(runs_on(), f"SELECT run_id, status FROM ops.job_runs WHERE dt = '{DAY}'"
                        ).ok


def test_where_one_ends_first_it_says_so() -> None:
    verdict = compare_hive(runs_on(), "SELECT run_id, status FROM ops.job_runs")
    assert repr(verdict).endswith("  line 5, in the Statement: WHERE\n"
                                  "  line 5, in the original:  (nothing: it ends after line 4)")


def test_a_verdict_is_true_only_when_ok() -> None:
    """`if compare_hive(...)` reads as it says: a Verdict whose ok is False is false."""
    assert bool(compare_hive(runs_on(), f"SELECT run_id, status FROM ops.job_runs "
                                        f"WHERE dt = '{DAY}'")) is True
    assert bool(compare_hive(runs_on(), "SELECT run_id FROM ops.job_runs")) is False


SET_LINES = "SET hive.exec.dynamic.partition=true;\nset hive.exec.parallel = true;\n"


def test_set_lines_before_the_query_are_passed_over() -> None:
    """Inherited Hive often starts with SET lines, which set the session, not the rows."""
    original = f"{SET_LINES}SELECT run_id, status FROM ops.job_runs WHERE dt = '{DAY}';"
    assert compare_hive(runs_on(), original).ok
    insert = (f"{SET_LINES}INSERT OVERWRITE TABLE mart.day_runs PARTITION (dt = '{DAY}')\n"
              f"SELECT run_id, status FROM ops.job_runs WHERE dt = '{DAY}'")
    assert compare_hive(runs_on(), insert).ok


def test_set_lines_are_passed_over_when_comparing_the_rows_too() -> None:
    original = f"{SET_LINES}{ORIGINAL}"
    verdict = compare_with_original(not_tests(is_null(job_runs.status)), original,
                                    query=example_database.query, partition={"dt": FIRST_DAY})
    assert verdict.ok, verdict


@pytest.mark.parametrize("original, said", [
    pytest.param("SELECT FROM WHERE (", "sqlglot can't read the original as Hive",
                 id="unreadable"),
    pytest.param(f"{SET_LINES}SELECT run_id FROM ops.job_runs;\nSELECT 1",
                 "the original holds 2 statements besides its SET lines, where one query goes",
                 id="two_queries_after_set_lines"),
    pytest.param("INSERT OVERWRITE TABLE mart.x SELECT 1;\nSELECT run_id FROM ops.job_runs",
                 "the original holds 2 statements", id="an_insert_and_a_select"),
    pytest.param("DROP TABLE ops.jobs", "the original isn't a query that gives rows: it is a "
                 "DROP statement", id="not_a_query"),
    pytest.param("  ", "original is empty text", id="empty"),
    pytest.param(None, "original is a NoneType", id="none"),
])
def test_an_original_that_isnt_one_query_is_refused(original: object, said: str) -> None:
    with pytest.raises((ValueError, TypeError)) as refused:
        compare_hive(runs_on(), original)
    assert said in str(refused.value)
    assert "Usual fix:" in str(refused.value)
    assert not re.search(r"(?<!\.)\.\.(?!\.)", str(refused.value))  # no full stop doubled
    assert "<Token" not in str(refused.value)  # sqlglot's own name for a word it read


def test_what_isnt_a_statement_that_reads_is_refused() -> None:
    with pytest.raises(TypeError, match="compare_hive was given"):
        compare_hive("SELECT 1", "SELECT 1")
    with pytest.raises(ValueError, match="explain.*which gives no rows to compare"):
        compare_hive(explain(runs_on()), "SELECT 1")


def test_the_first_line_that_differs_is_shown_from_each() -> None:
    verdict = compare_hive(runs_on(), "SELECT run_id, status FROM ops.job_runs "
                                      "WHERE dt = '2026-09-23'")
    assert not verdict.ok
    assert repr(verdict) == (
        "The Statement's Hive and the original differ, once both are written out the same "
        "way: lines 1 to 5 match, and line 6 differs.\n"
        "  line 4, in both:          FROM ops.job_runs\n"
        "  line 5, in both:          WHERE\n"
        "  line 6, in the Statement: dt = '2026-09-24'\n"
        "  line 6, in the original:  dt = '2026-09-23'")


def test_an_extra_column_shows_the_lines_before_it() -> None:
    """The lines before the one that differs show where it is, as an extra column's comma
    would mislead alone."""
    verdict = compare_hive(runs_on(), f"SELECT run_id, status, dt FROM ops.job_runs "
                                      f"WHERE dt = '{DAY}'")
    assert repr(verdict) == (
        "The Statement's Hive and the original differ, once both are written out the same "
        "way: lines 1 and 2 match, and line 3 differs.\n"
        "  line 1, in both:          SELECT\n"
        "  line 2, in both:          run_id,\n"
        "  line 3, in the Statement: status\n"
        "  line 3, in the original:  status,")


# --- compare_with_original -------------------------------------------------------------------

FIRST_DAY = "2026-09-23"
# The runs of every day but the TEST runs, those still running (status NULL) kept.
ORIGINAL = "SELECT run_id, status, dt FROM ops.job_runs WHERE COALESCE(status, '') <> 'TEST'"


def not_tests(*kept: Condition) -> Statement:
    """The runs of every day but the TEST runs; with `kept`, those it keeps too."""
    not_a_test = not_equals(job_runs.status, "TEST")
    return statement(SELECT(job_runs.run_id, job_runs.status, job_runs.dt),
                     FROM(job_runs, reads_all_partitions=True),
                     WHERE(any_of(not_a_test, *kept) if kept else not_a_test))


def sent_through(answer: Callable[[str], pd.DataFrame], sent: list[str]
                 ) -> Callable[[str], pd.DataFrame]:
    """A query that keeps each Hive it is given in `sent`, then answers it with `answer`."""
    def query(hive: str) -> pd.DataFrame:
        sent.append(hive)
        return answer(hive)
    return query


def test_the_same_rows_match_null_with_null() -> None:
    sent = []
    verdict = compare_with_original(not_tests(is_null(job_runs.status)), ORIGINAL,
                                    query=sent_through(example_database.query, sent),
                                    partition={"dt": FIRST_DAY})
    assert verdict.ok
    assert repr(verdict) == ("The Statement and the original give the same rows where "
                             "dt = '2026-09-23': 4 rows each.")
    assert len(sent) == 1


def test_rows_in_one_and_not_the_other_are_counted_and_shown() -> None:
    verdict = compare_with_original(not_tests(), ORIGINAL, query=example_database.query,
                                    partition={"dt": FIRST_DAY})
    assert not verdict.ok
    assert repr(verdict) == (
        "The Statement and the original give different rows where dt = '2026-09-23'.\n"
        "  The Statement gives 3 rows, and the original 4.\n"
        "  0 rows are in the Statement and not in the original, and 1 row is in the original "
        "and not in the Statement.\n"
        "The rows that differ, at most 5 from each, with how many times each gives them:\n"
        " run_id status         dt  in_statement  in_original\n"
        "     98   None 2026-09-23             0            1")


def test_a_row_is_counted_as_many_times_as_it_comes() -> None:
    twice = f"{ORIGINAL} UNION ALL {ORIGINAL}"
    verdict = compare_with_original(not_tests(is_null(job_runs.status)), twice,
                                    query=example_database.query, partition={"dt": FIRST_DAY})
    assert not verdict.ok
    text = repr(verdict)
    assert "The Statement gives 4 rows, and the original 8." in text
    assert "0 rows are in the Statement and not in the original, and 4 rows are" in text
    assert "     95 SUCCESS 2026-09-23             1            2" in text


def test_every_partition_is_compared_when_asked_and_said() -> None:
    verdict = compare_with_original(not_tests(is_null(job_runs.status)), ORIGINAL,
                                    query=example_database.query, reads_all_partitions=True)
    assert repr(verdict) == ("The Statement and the original give the same rows, in every "
                             "Partition: 8 rows each.")


def test_a_statement_reading_no_partitioned_table_needs_no_partition() -> None:
    teams = statement(SELECT(jobs.job_id, jobs.team), FROM(jobs))
    verdict = compare_with_original(teams, "SELECT job_id, team FROM ops.jobs",
                                    query=example_database.query)
    assert repr(verdict) == "The Statement and the original give the same rows: 4 rows each."


def test_derived_tables_of_one_name_on_both_sides_are_kept_apart() -> None:
    day = derived("day_runs", not_tests(is_null(job_runs.status)))
    converted = statement(SELECT(day.run_id, day.status, day.dt), FROM(day))
    original = ("WITH day_runs AS (SELECT run_id, status, dt FROM ops.job_runs "
                "WHERE status = 'TEST') SELECT run_id, status, dt FROM day_runs")
    sent = []
    verdict = compare_with_original(converted, original,
                                    query=sent_through(example_database.query, sent),
                                    partition={"dt": FIRST_DAY})
    assert "The Statement gives 4 rows, and the original 1." in repr(verdict)
    assert sent[0].startswith("WITH")
    assert sent[0].count("WITH") == 1  # Hive takes no WITH inside another


def test_a_partitioned_read_with_no_partition_is_refused() -> None:
    with pytest.raises(ValueError) as refused:
        compare_with_original(not_tests(), ORIGINAL, query=example_database.query)
    message = str(refused.value)
    assert "the Statement reads ops.job_runs, which is partitioned, and nothing says which " \
           "Partitions to compare" in message
    assert 'partition={"dt": ...}' in message
    assert "reads_all_partitions=True" in message


@pytest.mark.parametrize("partition, error, said, fix", [
    pytest.param({"day": FIRST_DAY}, ValueError, "names 'day', which is neither a column the "
                 "Statement gives nor a partition column",
                 "Name a column the Statement gives: run_id, status and dt", id="unknown_column"),
    pytest.param(["dt"], TypeError, "partition= is a dict", 'Write it like partition={"dt": '
                 "...}", id="not_a_dict"),
    pytest.param({}, ValueError, 'partition={}) names no column', 'as in partition={"dt": ...}',
                 id="empty"),
    pytest.param({"dt": None}, ValueError, "gives dt None, not a value", "Give dt a value",
                 id="none"),
])
def test_a_wrong_partition_is_refused(partition: object, error: type[Exception],
                                      said: str, fix: str) -> None:
    with pytest.raises(error) as refused:
        compare_with_original(not_tests(), ORIGINAL, query=example_database.query,
                              partition=partition)
    assert said in str(refused.value)
    assert fix in str(refused.value).split("Usual fix:")[1]


def test_columns_that_arent_the_statements_are_refused_naming_both() -> None:
    sent = []
    with pytest.raises(ValueError) as refused:
        compare_with_original(not_tests(), "SELECT run_id, dt, status FROM ops.job_runs",
                              query=sent_through(example_database.query, sent),
                              partition={"dt": FIRST_DAY})
    message = str(refused.value)
    assert "the Statement gives run_id, status and dt, and the original run_id, dt and " \
           "status" in message
    assert sent == []


def test_a_star_or_an_unnamed_calculation_is_named_as_hive_names_it() -> None:
    with pytest.raises(ValueError, match=r"the original run_id, job_id, status, duration_mins, "
                                         r"avg_retry_secs and dt"):
        compare_with_original(not_tests(), "SELECT * FROM ops.job_runs",
                              query=example_database.query, partition={"dt": FIRST_DAY})
    with pytest.raises(ValueError, match=r"the original run_id, _c1 and dt"):
        compare_with_original(not_tests(), "SELECT run_id, upper(status), dt FROM ops.job_runs",
                              query=example_database.query, partition={"dt": FIRST_DAY})



def test_a_star_over_a_table_the_statement_doesnt_read_is_still_refused() -> None:
    """Its columns are known only from a Table reference the Statement reads."""
    with pytest.raises(ValueError) as refused:
        compare_with_original(not_tests(), "SELECT * FROM ops.jobs",
                              query=example_database.query, partition={"dt": FIRST_DAY})
    message = str(refused.value)
    assert "and the original *." in message
    assert ("it reads a table the Statement doesn't, so the Toolbox doesn't know its columns. "
            "List them in place of the *.") in message


@pytest.mark.parametrize("original", [
    pytest.param("SELECT * FROM ops.job_runs WHERE COALESCE(status, '') <> 'TEST'",
                 id="a_table_the_statement_reads"),
    pytest.param("SELECT r.* FROM ops.job_runs r WHERE COALESCE(r.status, '') <> 'TEST'",
                 id="its_short_name_dot_star"),
    pytest.param("SELECT * FROM (SELECT * FROM ops.job_runs WHERE COALESCE(status, '') <> "
                 "'TEST') kept", id="a_subquery_of_the_original"),
    pytest.param("WITH kept AS (SELECT * FROM ops.job_runs WHERE COALESCE(status, '') <> "
                 "'TEST') SELECT * FROM kept", id="a_derived_table_of_the_original"),
])
def test_an_original_that_gives_star_is_compared_by_the_columns_it_reads(original: str
                                                                          ) -> None:
    every_column = statement(SELECT(*all_columns(job_runs)), FROM(job_runs,
                                                                reads_all_partitions=True),
                             WHERE(any_of(not_equals(job_runs.status, "TEST"),
                                          is_null(job_runs.status))))
    verdict = compare_with_original(every_column, original, query=example_database.query,
                                    partition={"dt": FIRST_DAY})
    assert repr(verdict) == ("The Statement and the original give the same rows where "
                             "dt = '2026-09-23': 4 rows each.")

def test_it_needs_your_query() -> None:
    with pytest.raises(TypeError, match="compare_with_original needs query="):
        compare_with_original(not_tests(), ORIGINAL, partition={"dt": FIRST_DAY})


def test_a_query_that_gives_back_too_few_columns_is_refused() -> None:
    with pytest.raises(ValueError, match="gave back 1 column"):
        compare_with_original(not_tests(), ORIGINAL, partition={"dt": FIRST_DAY},
                              query=lambda hive: pd.DataFrame({"x": [1]}))


def test_a_partition_that_names_no_partition_column_is_refused() -> None:
    """partition= on a column no table is partitioned by would still read every Partition."""
    runs = statement(SELECT(job_runs.run_id, job_runs.status, job_runs.dt),
                     FROM(job_runs, reads_all_partitions=True))
    original = "SELECT run_id, status, dt FROM ops.job_runs"
    with pytest.raises(ValueError, match=r"partition= names status, by which none of them is "
                       "partitioned"):
        compare_with_original(runs, original, query=example_database.query,
                              partition={"status": "FAILED"})


# --- A Statement that picks its own Partitions ------------------------------------------------
# runs_on() reads job_runs where dt = DAY, and doesn't give dt: partition= names dt, a partition
# column of the table it reads, and applies to the reads of that table on both sides.

UNBOUNDED = "SELECT run_id, status FROM ops.job_runs"


def test_partition_may_name_a_partition_column_the_statement_doesnt_give() -> None:
    sent = []
    verdict = compare_with_original(runs_on(), UNBOUNDED, partition={"dt": DAY},
                                    query=sent_through(example_database.query, sent))
    assert verdict.ok, verdict
    assert repr(verdict) == ("The Statement and the original give the same rows, reading "
                             "ops.job_runs where dt = '2026-09-24': 4 rows each.")
    # Each side reads only that Partition of ops.job_runs: the original too, which alone
    # would read every one.
    one_line = " ".join(sent[0].split()).replace("( ", "(").replace(" )", ")")
    assert one_line.count("(SELECT * FROM ops.job_runs WHERE dt = '2026-09-24')") == 2, sent[0]


def test_a_write_into_one_partition_is_compared_by_that_partition() -> None:
    saved = Table("mart.day_runs", columns={"run_id": "bigint", "status": "string",
                                            "dt": "string"},
                  partitioned_by=["dt"], location="/data/your_team/mart.db/day_runs")
    write = statement(INSERT_OVERWRITE(saved, partition={"dt": DAY}),
                      SELECT(job_runs.run_id, job_runs.status), FROM(job_runs),
                      WHERE(equals(job_runs.dt, DAY)))
    assert compare_with_original(write, UNBOUNDED, query=example_database.query,
                                 partition={"dt": DAY}).ok


def test_a_statement_that_picks_its_own_partition_is_told_to_name_that_column() -> None:
    with pytest.raises(ValueError) as refused:
        compare_with_original(runs_on(), UNBOUNDED, query=example_database.query)
    fix = usual_fix(refused)
    assert 'partition={"dt": ...}' in fix
    assert "run_id" not in fix and "status" not in fix


def test_every_partition_isnt_said_where_the_statement_picks_its_own() -> None:
    verdict = compare_with_original(
        runs_on(), f"{UNBOUNDED} WHERE dt = '{DAY}'", reads_all_partitions=True,
        query=lambda hive: pd.DataFrame([[4, 4, 0, 0, None, None, None, None]]))
    assert verdict.ok
    assert repr(verdict) == ("The Statement and the original give the same rows, each in the "
                             "Partitions its own conditions pick: 4 rows each.")


def test_a_name_neither_given_nor_a_partition_column_lists_both() -> None:
    with pytest.raises(ValueError) as refused:
        compare_with_original(runs_on(), UNBOUNDED, query=example_database.query,
                              partition={"job_id": 1})
    message = str(refused.value)
    assert "names 'job_id', which is neither a column the Statement gives nor a partition " \
           "column of a table it reads" in message
    assert "run_id and status; or a partition column of a table it reads: dt" in message


def test_reading_no_partitioned_table_a_name_must_be_a_column_it_gives() -> None:
    teams = statement(SELECT(jobs.job_id, jobs.team), FROM(jobs))
    with pytest.raises(ValueError) as refused:
        compare_with_original(teams, "SELECT job_id, team FROM ops.jobs",
                              query=example_database.query, partition={"owner": "ana"})
    assert "names 'owner', which isn't a column the Statement gives" in str(refused.value)
    assert usual_fix(refused).strip() == "Name a column the Statement gives: job_id and team."


def test_where_is_refused_pointing_to_partition() -> None:
    with pytest.raises(TypeError) as refused:
        compare_with_original(runs_on(), UNBOUNDED, query=example_database.query,
                              where=equals(job_runs.dt, DAY))
    assert "compare_with_original was given where=" in str(refused.value)
    assert 'partition={"dt": ...}' in usual_fix(refused)


def usual_fix(refused: pytest.ExceptionInfo) -> str:
    return str(refused.value).split("Usual fix:")[1].split("Opt-out:")[0]


def test_unchecked_pieces_are_named_and_the_comparison_logged(tmp_path: Path) -> None:
    from sqlglot_composer import set_admin_log

    log = tmp_path / "admin_log.md"
    set_admin_log(log)
    try:
        runs = statement(
            SELECT(job_runs.run_id, AS(unchecked_column("{minutes} DIV 15",
                                                        minutes=job_runs.duration_mins), "q"),
                   job_runs.dt),
            FROM(job_runs),
            WHERE(equals(job_runs.dt, DAY)),
        )
        original = f"SELECT run_id, duration_mins DIV 15 AS q, dt FROM ops.job_runs WHERE dt = '{DAY}'"
        said = repr(compare_with_original(runs, original, query=example_database.query,
                                          partition={"dt": DAY}))
    finally:
        set_admin_log()
    assert said.splitlines()[-1] == (
        "The Statement holds Hive written by hand, which the Toolbox can't look inside: "
        'unchecked_column("{minutes} DIV 15", minutes=job_runs.duration_mins). The rows '
        "match, so it gives what the original gives here.")
    assert ("Statement with an Unchecked expression, compared with the original by "
            "compare_with_original") in log.read_text(encoding="utf-8")


def test_where_the_rows_differ_the_unchecked_line_says_to_check_that_hive_first() -> None:
    runs = statement(
        SELECT(job_runs.run_id, AS(unchecked_column("{minutes} DIV 15",
                                                    minutes=job_runs.duration_mins), "q")),
        FROM(job_runs), WHERE(equals(job_runs.dt, DAY)))
    differ = pd.DataFrame([[4, 3, 1, 0, 101, 0, 1, 0]])
    said = repr(compare_with_original(runs, "SELECT run_id, duration_mins DIV 15 AS q FROM "
                                      f"ops.job_runs WHERE dt = '{DAY}'", partition={"dt": DAY},
                                      query=lambda hive: differ))
    assert said.splitlines()[-1].endswith(
        "minutes=job_runs.duration_mins). Check that Hive first: the Toolbox can't trace a "
        "difference inside it.")
