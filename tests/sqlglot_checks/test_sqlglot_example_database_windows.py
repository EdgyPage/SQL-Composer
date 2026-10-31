"""sqlglot Composer's Example database works windows out as Hive does (Toolbox 7.2, ticket 10).

sqlglot's executor has no window functions, so the Example database works each one out itself,
from the rows the rest of the query gives. Each answer here is worked out by hand from
ops.job_runs's nine rows:

    run_id  job_id  status   duration_mins  dt
    95      1       SUCCESS  12             2026-09-23
    96      2       SUCCESS  18             2026-09-23
    97      3       FAILED   30             2026-09-23
    98      2       NULL     15             2026-09-23
    99      1       TEST      5             2026-09-23
    101     1       SUCCESS  10             2026-09-24
    102     2       FAILED   20             2026-09-24
    103     3       SUCCESS  30             2026-09-24
    104     1       SUCCESS  40             2026-09-24
"""

from __future__ import annotations

import pytest

from sqlglot_composer import (
    AS,
    FROM,
    SELECT,
    WHERE,
    derived,
    descending,
    equals,
    example_database,
    lag,
    row_number,
    run_query,
    statement,
    window,
)
from sqlglot_composer.example_database import job_runs


def by_run(hive: str, column: str) -> dict[int, object]:
    """Each run's value of `column`, by its run_id, NULL as None."""
    found = example_database.query(hive)
    return {int(run): (None if value != value or value is None else value)
            for run, value in zip(found.run_id, found[column])}


JOB_IN_RUN_ORDER = "PARTITION BY r.job_id ORDER BY r.run_id"


@pytest.mark.parametrize(("calculation", "wanted"), [
    pytest.param("ROW_NUMBER() OVER (PARTITION BY r.job_id ORDER BY r.run_id DESC)",
                 {104: 1, 101: 2, 99: 3, 95: 4, 102: 1, 98: 2, 96: 3, 103: 1, 97: 2},
                 id="row_number"),
    pytest.param("RANK() OVER (ORDER BY r.duration_mins DESC)",
                 {104: 1, 97: 2, 103: 2, 102: 4, 96: 5, 98: 6, 95: 7, 101: 8, 99: 9},
                 id="rank_skips_after_a_tie"),
    pytest.param("DENSE_RANK() OVER (ORDER BY r.duration_mins DESC)",
                 {104: 1, 97: 2, 103: 2, 102: 3, 96: 4, 98: 5, 95: 6, 101: 7, 99: 8},
                 id="dense_rank_doesnt"),
    pytest.param("NTILE(4) OVER (ORDER BY r.run_id)",
                 {95: 1, 96: 1, 97: 1, 98: 2, 99: 2, 101: 3, 102: 3, 103: 4, 104: 4},
                 id="ntile_gives_the_first_parts_a_row_more"),
    pytest.param(f"LAG(r.duration_mins, 1) OVER ({JOB_IN_RUN_ORDER})",
                 {95: None, 99: 12, 101: 5, 104: 10, 96: None, 98: 18, 102: 15, 97: None,
                  103: 30}, id="lag"),
    pytest.param(f"LAG(r.duration_mins, 2, 0) OVER ({JOB_IN_RUN_ORDER})",
                 {95: 0, 99: 0, 101: 12, 104: 5, 96: 0, 98: 0, 102: 18, 97: 0, 103: 0},
                 id="lag_two_back_with_a_default"),
    pytest.param(f"LEAD(r.status, 1) OVER ({JOB_IN_RUN_ORDER})",
                 {95: "TEST", 99: "SUCCESS", 101: "SUCCESS", 104: None, 96: None, 98: "FAILED",
                  102: None, 97: "SUCCESS", 103: None}, id="lead"),
    pytest.param(f"FIRST_VALUE(r.status) OVER ({JOB_IN_RUN_ORDER} ROWS BETWEEN UNBOUNDED "
                 "PRECEDING AND UNBOUNDED FOLLOWING)",
                 {95: "SUCCESS", 99: "SUCCESS", 101: "SUCCESS", 104: "SUCCESS", 96: "SUCCESS",
                  98: "SUCCESS", 102: "SUCCESS", 97: "FAILED", 103: "FAILED"},
                 id="first_value"),
    pytest.param(f"LAST_VALUE(r.status) OVER ({JOB_IN_RUN_ORDER} ROWS BETWEEN UNBOUNDED "
                 "PRECEDING AND UNBOUNDED FOLLOWING)",
                 {95: "SUCCESS", 99: "SUCCESS", 101: "SUCCESS", 104: "SUCCESS", 96: "FAILED",
                  98: "FAILED", 102: "FAILED", 97: "SUCCESS", 103: "SUCCESS"},
                 id="last_value_of_the_whole_group"),
    pytest.param(f"LAST_VALUE(r.status) OVER ({JOB_IN_RUN_ORDER})",
                 {95: "SUCCESS", 99: "TEST", 101: "SUCCESS", 104: "SUCCESS", 96: "SUCCESS",
                  98: None, 102: "FAILED", 97: "FAILED", 103: "SUCCESS"},
                 id="last_value_up_to_the_row_as_hive_leaves_it"),
    pytest.param(f"SUM(r.duration_mins) OVER ({JOB_IN_RUN_ORDER} ROWS BETWEEN UNBOUNDED "
                 "PRECEDING AND CURRENT ROW)",
                 {95: 12, 99: 17, 101: 27, 104: 67, 96: 18, 98: 33, 102: 53, 97: 30, 103: 60},
                 id="a_running_total"),
    pytest.param(f"SUM(r.duration_mins) OVER ({JOB_IN_RUN_ORDER} ROWS BETWEEN 1 PRECEDING "
                 "AND CURRENT ROW)",
                 {95: 12, 99: 17, 101: 15, 104: 50, 96: 18, 98: 33, 102: 35, 97: 30, 103: 60},
                 id="a_moving_total"),
    pytest.param("SUM(r.duration_mins) OVER (PARTITION BY r.job_id)",
                 {95: 67, 99: 67, 101: 67, 104: 67, 96: 53, 98: 53, 102: 53, 97: 60, 103: 60},
                 id="a_groups_total"),
    pytest.param("SUM(r.duration_mins) OVER (ORDER BY r.dt)",
                 {95: 80, 96: 80, 97: 80, 98: 80, 99: 80, 101: 180, 102: 180, 103: 180,
                  104: 180}, id="ordered_with_no_rows_counts_each_rows_ties_as_hive_does"),
    pytest.param("COUNT(*) OVER (PARTITION BY r.job_id)",
                 {95: 4, 99: 4, 101: 4, 104: 4, 96: 3, 98: 3, 102: 3, 97: 2, 103: 2},
                 id="count_rows"),
    pytest.param("COUNT(r.status) OVER (PARTITION BY r.job_id)",
                 {95: 4, 99: 4, 101: 4, 104: 4, 96: 2, 98: 2, 102: 2, 97: 2, 103: 2},
                 id="count_leaves_out_null"),
    pytest.param("AVG(r.duration_mins) OVER ()",
                 dict.fromkeys([95, 96, 97, 98, 99, 101, 102, 103, 104], 20.0),
                 id="average_of_every_row"),
    pytest.param("MIN(r.duration_mins) OVER (PARTITION BY r.job_id)",
                 {95: 5, 99: 5, 101: 5, 104: 5, 96: 15, 98: 15, 102: 15, 97: 30, 103: 30},
                 id="min"),
    pytest.param("MAX(r.duration_mins) OVER (PARTITION BY r.job_id)",
                 {95: 40, 99: 40, 101: 40, 104: 40, 96: 20, 98: 20, 102: 20, 97: 30, 103: 30},
                 id="max"),
    pytest.param("ROW_NUMBER() OVER (PARTITION BY r.job_id ORDER BY r.status, r.run_id)",
                 {98: 1, 102: 2, 96: 3, 95: 1, 101: 2, 104: 3, 99: 4, 97: 1, 103: 2},
                 id="null_first_ascending"),
    pytest.param("ROW_NUMBER() OVER (PARTITION BY r.job_id ORDER BY r.status DESC, "
                 "r.run_id)",
                 {96: 1, 102: 2, 98: 3, 99: 1, 95: 2, 101: 3, 104: 4, 103: 1, 97: 2},
                 id="null_last_descending"),
    pytest.param("ROW_NUMBER() OVER (PARTITION BY r.job_id ORDER BY r.status NULLS LAST, "
                 "r.run_id)",
                 {102: 1, 96: 2, 98: 3, 95: 1, 101: 2, 104: 3, 99: 4, 97: 1, 103: 2},
                 id="nulls_last_as_written"),
    pytest.param(f"SUM(r.duration_mins) OVER ({JOB_IN_RUN_ORDER} ROWS BETWEEN CURRENT ROW "
                 "AND 1 FOLLOWING)",
                 {95: 17, 99: 15, 101: 50, 104: 40, 96: 33, 98: 35, 102: 20, 97: 60, 103: 30},
                 id="rows_after_the_row"),
    pytest.param("SUM(r.duration_mins) OVER (ORDER BY r.dt RANGE BETWEEN CURRENT ROW AND "
                 "UNBOUNDED FOLLOWING)",
                 {95: 180, 96: 180, 97: 180, 98: 180, 99: 180, 101: 100, 102: 100, 103: 100,
                  104: 100}, id="range_to_the_end_counts_the_rows_tied_with_it"),
])
def test_each_window_is_worked_out_as_hive_does(calculation: str,
                                               wanted: dict[int, object]) -> None:
    hive = f"SELECT r.run_id, {calculation} AS x FROM ops.job_runs AS r"
    assert by_run(hive, "x") == wanted


def test_a_window_inside_a_calculation() -> None:
    hive = (f"SELECT r.run_id, r.duration_mins - LAG(r.duration_mins, 1) OVER "
            f"({JOB_IN_RUN_ORDER}) AS change FROM ops.job_runs AS r WHERE r.job_id = 1")
    assert by_run(hive, "change") == {95: None, 99: -7, 101: 5, 104: 30}


def test_a_window_sees_only_the_rows_where_leaves() -> None:
    hive = (f"SELECT r.run_id, ROW_NUMBER() OVER ({JOB_IN_RUN_ORDER}) AS n "
            "FROM ops.job_runs AS r WHERE r.dt = '2026-09-24'")
    assert by_run(hive, "n") == {101: 1, 104: 2, 102: 1, 103: 1}


def test_a_window_over_groups_reads_their_sums() -> None:
    found = example_database.query(
        "SELECT r.job_id, SUM(r.duration_mins) AS minutes, RANK() OVER (ORDER BY "
        "SUM(r.duration_mins) DESC) AS place FROM ops.job_runs AS r GROUP BY r.job_id")
    assert found.set_index("job_id").to_dict() == {"minutes": {1: 67, 2: 53, 3: 60},
                                                    "place": {1: 1, 2: 3, 3: 2}}


def test_order_by_and_limit_come_after_the_window() -> None:
    found = example_database.query(
        "SELECT r.run_id, ROW_NUMBER() OVER (ORDER BY r.run_id) AS n FROM ops.job_runs AS r "
        "ORDER BY n DESC LIMIT 2")
    assert found.values.tolist() == [[104, 9], [103, 8]]


def test_a_star_beside_a_window() -> None:
    found = example_database.query(
        "SELECT r.*, ROW_NUMBER() OVER (ORDER BY r.run_id) AS n FROM ops.job_runs AS r")
    assert list(found.columns) == ["run_id", "job_id", "status", "duration_mins",
                                   "avg_retry_secs", "dt", "n"]
    assert found.n.tolist() == list(range(1, 10))


def test_the_newest_of_each_group_through_a_query_in_brackets() -> None:
    found = example_database.query(
        "SELECT * FROM (SELECT r.run_id, r.job_id, ROW_NUMBER() OVER (PARTITION BY r.job_id "
        "ORDER BY r.run_id DESC) AS n FROM ops.job_runs AS r) ranked WHERE ranked.n = 1")
    assert sorted(found.run_id) == [102, 103, 104]


def test_a_statement_with_a_window_runs() -> None:
    """The newest run of each job, as Latest row of each group shows it: through a Derived
    table."""
    numbered = derived("numbered", statement(
        SELECT(job_runs.run_id, job_runs.job_id,
               AS(row_number(PARTITION_BY=job_runs.job_id,
                             ORDER_BY=descending(job_runs.run_id)),
                  "newest_first")),
        FROM(job_runs, reads_all_partitions=True)))
    newest = statement(SELECT(numbered.job_id, numbered.run_id), FROM(numbered),
                       WHERE(equals(numbered.newest_first, 1)))
    assert run_query(newest, example_database.query).set_index("job_id").run_id.to_dict() == {
        1: 104, 2: 102, 3: 103}
    before = statement(SELECT(job_runs.run_id, AS(lag(job_runs.duration_mins, over=window(
        PARTITION_BY=job_runs.job_id, ORDER_BY=job_runs.run_id)), "before")),
        FROM(job_runs, reads_all_partitions=True), WHERE(equals(job_runs.job_id, 3)))
    found = run_query(before, example_database.query).set_index("run_id").before
    assert found.isna()[97] and found[103] == 30


@pytest.mark.parametrize(("calculation", "missing"), [
    ("SUM(r.duration_mins) OVER (ORDER BY r.run_id RANGE BETWEEN 1 PRECEDING AND CURRENT ROW)",
     "window over RANGE with a number of rows, such as RANGE BETWEEN 1 PRECEDING AND "
     "CURRENT ROW; window(rows=...) writes ROWS BETWEEN, which it has"),
    ("PERCENT_RANK() OVER (ORDER BY r.run_id)", "window function PERCENT_RANK"),
    ("COUNT(DISTINCT r.job_id) OVER ()", "COUNT(DISTINCT ...) over a window"),
    ("FIRST_VALUE(r.status) IGNORE NULLS OVER (ORDER BY r.run_id)",
     "IGNORE NULLS or RESPECT NULLS in a window"),
])
def test_a_window_it_cant_work_out_is_refused_plainly(calculation: str, missing: str) -> None:
    with pytest.raises(RuntimeError) as refused:
        example_database.query(f"SELECT r.run_id, {calculation} AS x FROM ops.job_runs AS r")
    message = str(refused.value)
    assert (f"The Example database can't run this Hive: its executor has no {missing}."
            in message)
    assert "to_hive(...)" in message


def test_ntile_of_no_parts_is_refused_as_hive_refuses_it() -> None:
    with pytest.raises(RuntimeError, match=r"NTILE\(0\) splits each group into no parts"):
        example_database.query("SELECT r.run_id, NTILE(0) OVER (ORDER BY r.run_id) AS x "
                               "FROM ops.job_runs AS r")
