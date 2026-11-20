"""Each Pivot filter is a Decision of its table (Toolbox 8.9, ticket 08; CONTEXT.md's Pivot
filter).

A table made from a PivotTable that leaves rows out holds PIVOT_FILTERS in its Table
reference, one line per filter, kept as converted ("keep") until answered. Its other answers
keep every slice instead: "fold", the filtered column part of what one row is; "batch", one
batch per value, the table partitioned on the column, the value a Script tag a Run value
answers; and "tables", a table per value, `<table>_<value>`. Each table's checklist says what
the table shows and how many tables a table per value makes, layer by layer, "at least" as
many as the PivotTable's cache holds; a Copilot `.hql` alone holds no cache, so its count
isn't known. The user's words: "emphasize how many different tables it would create. a
filter with 100 conditions would make 100 tables, but the higher layer filter may have only
3, which is manageable." Each answer gives the table it says, rows checked on the Example
database.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import test_convert_workbooks as workbooks_converted
from test_convert_workbooks import COPILOT_PIVOT, DEV, checklist, converted, decide

import example_database
from sqlglot_composer import project, run_execute, run_query, to_hive
from sqlglot_composer.pivot_filters import (
    pivot_filter_keys,
    pivot_filter_note,
    table_slices,
    tables_counted,
)
from sqlglot_composer.workbook_pivot_hive import (
    HIDDEN_ITEMS,
    SLICER,
    TIMELINE,
    ConvertedPivotFilter,
)

PIVOT = f"{DEV}.pivot"
STATUSES = ("FAILED", "SUCCESS", "TEST", None)
# The convert tests' fixtures: each workbook of each kind, and a started Project.
books = workbooks_converted.books
started = workbooks_converted.started


def rows_of(table: str) -> pd.DataFrame:
    """The rows a table's preview() gives on the Example database, in a fixed order."""
    found = run_query(project.load(table).preview(), example_database.query)
    return found.sort_values(list(found.columns)).reset_index(drop=True)


def rows_of_hive(hive: str) -> pd.DataFrame:
    """The rows Hive gives on the Example database, in a fixed order."""
    found = example_database.query(hive)
    return found.sort_values(list(found.columns)).reset_index(drop=True)


def reference(root: Path, table: str) -> str:
    return (root / "references" / f"{table.replace('.', '__')}.py").read_text(
        encoding="utf-8")


def same_rows(table: str, hive: str) -> None:
    """Assert a table's preview gives the rows `hive` gives, column by column."""
    mine, theirs = rows_of(table), rows_of_hive(hive)
    assert list(mine.columns) == list(theirs.columns)
    pd.testing.assert_frame_equal(mine, theirs, check_dtype=False)


# --- The Decision, as convert asks it ------------------------------------------------------


def test_each_pivot_filter_is_a_decision_kept_as_converted(started: Path,
                                                           books: dict[str, bytes]) -> None:
    report = converted(started, books, "slicer")
    assert ("Kept each Pivot filter as converted, a Decision of its table: mart_dev.pivot, "
            "where the slicer on status keeps FAILED and SUCCESS;") in report
    assert ('            "status": "keep",  # the slicer on status keeps FAILED and SUCCESS: a '
            'table per value makes at least 4 tables; or "fold", "batch" or "tables", as its '
            "checklist says") in report
    assert ('    "status": "keep",  # TODO: proposed: the slicer on status keeps FAILED and '
            "SUCCESS: a table per value makes at least 4 tables") in reference(started, PIVOT)
    opened = checklist(started, "pivot").split("## Notes")[0]
    assert ('- pivot_filters: status: the slicer on status keeps FAILED and SUCCESS: a table '
            'per value makes at least 4 tables: "keep" keeps it as converted; "fold", "batch" '
            'or "tables" keeps every slice instead, as its checklist says') in opened
    assert "pivot_filters: status" in repr(project.check())


def test_the_checklist_translates_what_the_table_shows_and_each_answer(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    notes = checklist(started, "pivot").split("## Notes")[1]
    assert ("Pivot filter status, a Decision: mart_dev.pivot shows sum_of_duration_mins by "
            "job_id, where the slicer on status keeps FAILED and SUCCESS, as the workbook was "
            'last saved. "keep", proposed, keeps that alone.') in notes
    assert ('"fold": status becomes part of what one row is, a column of mart_dev.pivot and of '
            "its GROUP BY: still 1 table, a row for each job_id and status.") in notes
    assert ('"batch": one batch per value: mart_dev.pivot is partitioned on status, and each '
            "write inserts one status's slice, the value of STATUS, a Run value you answer "
            'under "tags": still 1 table, at least 4 Partitions.') in notes
    assert ('"tables": a table per value, each mart_dev.pivot for one status, named '
            "mart_dev.pivot_<value>, such as mart_dev.pivot_failed: status: at least 4 tables, "
            "from the values the PivotTable's cache held when the workbook was saved. A "
            "handful of tables, such as 3, is manageable; a hundred is a reason to \"fold\" or "
            '"batch" instead.') in notes
    # A grand total shows its values over every row.
    assert ("mart_dev.pivot_grand_total shows sum_of_duration_mins over every row"
            in checklist(started, "pivot_grand_total"))


def test_keep_makes_the_decision_and_leaves_the_table_as_converted(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    hive = (started / "tables" / f"{DEV}__pivot" / "conversion" / "in_dev.hql").read_text(
        encoding="utf-8")
    decide({PIVOT: {"pivot_filters": {"status": "keep"}}})
    assert "pivot_filters" not in checklist(started, "pivot").split("## Notes")[0]
    assert ('    "status": "keep",  # the slicer on status keeps FAILED and SUCCESS'
            in reference(started, PIVOT))
    assert (started / "tables" / f"{DEV}__pivot" / "conversion" / "in_dev.hql").read_text(
        encoding="utf-8") == hive
    same_rows(PIVOT, "SELECT job_id, SUM(duration_mins) AS sum_of_duration_mins FROM "
                     "ops.job_runs WHERE status IN ('FAILED', 'SUCCESS') GROUP BY job_id")


def test_proposed_keeps_it_as_keep_does(started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    decide({PIVOT: {"pivot_filters": {"status": "proposed"}}})
    assert '    "status": "keep",  # the slicer' in reference(started, PIVOT)


# --- Each answer, the table it gives on the Example database -------------------------------


def test_fold_drops_the_condition_and_puts_its_column_in_the_grain(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    report = decide({PIVOT: {"pivot_filters": {"status": "fold"}}})
    assert ("mart_dev.pivot: wrote its logic, its Table reference and its conversion/ Hive "
            "again for its Pivot filters' answers: status is part of what one row is."
            ) in report
    same_rows(PIVOT, "SELECT job_id, status, SUM(duration_mins) AS sum_of_duration_mins FROM "
                     "ops.job_runs GROUP BY job_id, status")
    text = reference(started, PIVOT)
    assert '        "status": "string",' in text
    assert 'key=["job_id", "status"],  # proposed from its query' in text
    assert "WHERE" not in to_hive(project.load(PIVOT).preview())


def test_batch_partitions_the_table_and_writes_one_slice_a_run_value_gives(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    decide({PIVOT: {"pivot_filters": {"status": "batch"}}})
    text = reference(started, PIVOT)
    assert 'partitioned_by=["status"],' in text
    assert '"STATUS": "<PARM=\\"STATUS\\"/>",  # inside quotes.' in text
    # The value each write inserts is a Script tag's, a Decision until answered.
    assert "tags: STATUS" in repr(project.check())
    decide({PIVOT: {"tags": {"STATUS": "FAILED"},
                    "location": "/data/team/mart_dev.db/pivot"}})
    same_rows(PIVOT, "SELECT job_id, SUM(duration_mins) AS sum_of_duration_mins FROM "
                     "ops.job_runs WHERE status = 'FAILED' GROUP BY job_id")
    write = to_hive(project.load(PIVOT).write())
    assert "INSERT OVERWRITE TABLE mart_dev.pivot PARTITION(status = 'FAILED')" in write


def test_a_batch_tables_compare_reads_its_latest_partition_against_its_query(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    decide({PIVOT: {"pivot_filters": {"status": "batch"}}})
    # Its query gives every batch's rows, each status's.
    query = (started / "tables" / f"{DEV}__pivot" / "conversion" / "statement.hql").read_text(
        encoding="utf-8")
    assert "WHERE" not in query and "status" in query
    every_batch = ("SELECT job_id, SUM(duration_mins) AS sum_of_duration_mins, status FROM "
                   "ops.job_runs GROUP BY job_id, status")

    def warehouse(hive: str) -> pd.DataFrame:
        """The Example database, with the dev table holding two batches, as written."""
        if hive.startswith("SHOW PARTITIONS"):
            return pd.DataFrame({"partition": ["status=FAILED", "status=SUCCESS"]})
        return example_database.query(hive.replace(PIVOT, f"({every_batch})"))

    report = repr(project.compare_batch("book", query=warehouse, tables=PIVOT))
    assert f"{PIVOT}: passed, on status = 'SUCCESS'" in report


def test_tables_makes_a_table_per_value_each_holding_its_slice(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    report = decide({PIVOT: {"pivot_filters": {"status": "tables"}}})
    made = [f"{PIVOT}_{name}" for name in ("failed", "success", "test", "blank")]
    assert project.batch_tables("book")[:4] == made
    assert f"Renamed {PIVOT} to {PIVOT}_failed, for its Pivot filters' answers." in report
    assert not (started / "tables" / f"{DEV}__pivot").exists()
    for table, value in zip(made, STATUSES, strict=True):
        condition = "status IS NULL" if value is None else f"status = '{value}'"
        same_rows(table, "SELECT job_id, SUM(duration_mins) AS sum_of_duration_mins FROM "
                         f"ops.job_runs WHERE {condition} GROUP BY job_id")
        assert ("Made by its Pivot filters' answers: this table holds the rows of status "
                in checklist(started, table.split(".")[1]))
        # Each is a table of its own: its own name, its own folder to place.
        assert f'NAME = "{table.split(".")[1]}"' in reference(started, table) or (
            "NAME =" not in reference(started, table))


def test_a_table_per_value_holds_its_own_location_and_answers_of_its_own(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    decide({PIVOT: {"pivot_filters": {"status": "tables"},
                    "location": "/data/team/mart_dev.db/pivot"}})
    assert 'location="/data/team/mart_dev.db/pivot",' in reference(started, f"{PIVOT}_failed")
    assert "location=None,  # TODO:" in reference(started, f"{PIVOT}_success")
    assert "location:" in repr(project.check())


# --- Answering again -----------------------------------------------------------------------


def test_answering_again_changes_it_back(started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    decide({PIVOT: {"pivot_filters": {"status": "fold"}}})
    decide({PIVOT: {"pivot_filters": {"status": "keep"}}})
    same_rows(PIVOT, "SELECT job_id, SUM(duration_mins) AS sum_of_duration_mins FROM "
                     "ops.job_runs WHERE status IN ('FAILED', 'SUCCESS') GROUP BY job_id")
    assert '"status": "string"' not in reference(started, PIVOT)


def test_answering_a_table_per_value_again_makes_it_one_table(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    decide({PIVOT: {"pivot_filters": {"status": "tables"}}})
    report = decide({f"{PIVOT}_success": {"pivot_filters": {"status": "fold"}}})
    assert f"Renamed {PIVOT}_success to {PIVOT}, for its Pivot filters' answers." in report
    assert f"its Pivot filters' answers no longer make {PIVOT}_failed." in report
    assert project.batch_tables("book")[0] == PIVOT
    assert not [table for table in project.batch_tables("book") if "pivot_" in table
                and "grand_total" not in table]
    same_rows(PIVOT, "SELECT job_id, status, SUM(duration_mins) AS sum_of_duration_mins FROM "
                     "ops.job_runs GROUP BY job_id, status")


def test_a_name_and_pivot_filters_answered_at_once_rename_then_rewrite(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    decide({PIVOT: {"name": "runs_by_job", "pivot_filters": {"status": "fold"}},
            f"{PIVOT}_grand_total": {"pivot_filters": {"status": "fold"}}})
    same_rows(f"{DEV}.runs_by_job", "SELECT job_id, status, SUM(duration_mins) AS "
                                    "sum_of_duration_mins FROM ops.job_runs GROUP BY job_id, "
                                    "status")
    # Its grand total, renamed with it, is one row per status now.
    same_rows(f"{DEV}.runs_by_job_grand_total", "SELECT status, SUM(duration_mins) AS "
                                                "sum_of_duration_mins FROM ops.job_runs "
                                                "GROUP BY status")


def test_a_table_created_in_dev_keeps_its_pivot_filters(started: Path,
                                                        books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    decide({PIVOT: {"pivot_filters": {"status": "keep"},
                    "location": "/data/team/mart_dev.db/pivot"}})
    run_execute(project.load(PIVOT).create(), example_database.execute)
    with pytest.raises(ValueError, match="is created in dev already"):
        decide({PIVOT: {"pivot_filters": {"status": "fold"}}})


@pytest.mark.parametrize(("answer", "why"), [
    ({"region": "fold"}, "region is no Pivot filter of mart_dev.pivot"),
    ({"status": "split"}, 'give "keep", "fold", "batch" or "tables", not \'split\''),
])
def test_an_answer_no_pivot_filter_takes_is_refused_and_nothing_written(
        started: Path, books: dict[str, bytes], answer: dict[str, str], why: str) -> None:
    converted(started, books, "slicer")
    with pytest.raises(ValueError, match=why):
        decide({PIVOT: {"pivot_filters": answer}})
    assert "TODO: proposed: the slicer" in reference(started, PIVOT)


def test_a_table_with_no_pivot_filter_refuses_an_answer(started: Path,
                                                        books: dict[str, bytes]) -> None:
    converted(started, books, "pivot")
    with pytest.raises(ValueError, match="has no Pivot filter to decide"):
        decide({PIVOT: {"pivot_filters": {"status": "fold"}}})


# --- A value filter, and a script's Pivot filter -------------------------------------------


def test_a_value_filter_folds_to_every_item_and_has_nothing_to_batch(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "top")
    assert ('the value filter on job_id keeps the top 2 job_id by Sum of duration_mins: "keep" '
            'or "fold" alone') in reference(started, PIVOT)
    with pytest.raises(ValueError, match="a value filter keeps items by their rank"):
        decide({PIVOT: {"pivot_filters": {"job_id": "tables"}}})
    decide({PIVOT: {"pivot_filters": {"job_id": "fold"}}})
    same_rows(PIVOT, "SELECT job_id, SUM(duration_mins) AS sum_of_duration_mins FROM "
                     "ops.job_runs GROUP BY job_id")


def test_a_scripts_pivot_filter_says_its_count_isnt_known_and_why(started: Path) -> None:
    (started / "copilot.hql").write_text(COPILOT_PIVOT, encoding="utf-8")
    project.convert("pivot", files=["copilot.hql"], query=example_database.query,
                    database="ops")
    notes = checklist(started, "pivot")
    assert ("how many isn't known, as its Hive came from a script, and Hive holds no "
            "PivotTable's cache of the values status takes") in notes
    assert ("the slicer on status keeps FAILED and SUCCESS: how many values status has isn't "
            "known") in reference(started, PIVOT)
    with pytest.raises(ValueError, match="how many values status takes isn't known"):
        project.write_decisions({PIVOT: {"pivot_filters": {"status": "tables"}}})
    # Folding needs no count.
    project.write_decisions({PIVOT: {"pivot_filters": {"status": "fold"}}})
    same_rows(PIVOT, "SELECT job_id, status, SUM(duration_mins) AS sum_of_duration_mins FROM "
                     "ops.job_runs GROUP BY job_id, status")


# --- Two layers ---------------------------------------------------------------------------

TWO_LAYERS = [
    ConvertedPivotFilter("t", SLICER, "Region", ("East",), ("East", "West", "North")),
    ConvertedPivotFilter("t", HIDDEN_ITEMS, "Site", (),
                         tuple(f"site {number}" for number in range(100))),
]


def test_each_layer_counts_its_tables_and_the_layers_together() -> None:
    keyed = pivot_filter_keys(TWO_LAYERS)
    assert tables_counted(keyed) == ("Region: at least 3 tables; Site: at least 100; Region "
                                     "and Site: at least 300")
    slices = table_slices("mart_dev.t", keyed, {"Region": "tables", "Site": "tables"})
    assert len(slices) == 300
    assert slices["mart_dev.t_east_site_0"] == {"Region": "East", "Site": "site 0"}
    assert list(table_slices("mart_dev.t", keyed, {"Region": "tables"})) == [
        "mart_dev.t_east", "mart_dev.t_west", "mart_dev.t_north"]


def test_a_workbook_with_two_layers_counts_each_and_both(started: Path,
                                                        books: dict[str, bytes]) -> None:
    converted(started, books, "timeline")
    notes = checklist(started, "pivot")
    assert ("status: at least 4 tables; dt: at least 2; status and dt: at least 8, from the "
            "values the PivotTable's cache held") in notes
    assert notes.count("Pivot filter ") >= 2


def test_two_layers_answered_each_its_own_way(started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "timeline")
    decide({PIVOT: {"pivot_filters": {"status": "fold", "dt": "tables"}}})
    made = [table for table in project.batch_tables("book")
            if table.startswith(f"{PIVOT}_2026")]
    assert made == [f"{PIVOT}_2026_09_23", f"{PIVOT}_2026_09_24"]
    for table, day in zip(made, ("2026-09-23", "2026-09-24"), strict=True):
        # Its share of a column's total, a sum over a sum, is Hive the Toolbox's logic keeps
        # as it is: the rows of the Hive the answers wrote are checked.
        stem = table.replace(".", "__")
        hive = (started / "tables" / stem / "conversion" / "statement.hql").read_text(
            encoding="utf-8")
        assert "status <> 'TEST'" not in hive
        expected = rows_of_hive(
            "SELECT job_id, status, SUM(duration_mins) / SUM(SUM(duration_mins)) OVER "
            "(PARTITION BY status) AS sum_of_duration_mins FROM ops.job_runs "
            f"WHERE dt = '{day}' GROUP BY job_id, status")
        pd.testing.assert_frame_equal(rows_of_hive(hive.rstrip().rstrip(";")), expected,
                                      check_dtype=False)


def test_a_note_names_a_timelines_layer_by_its_days() -> None:
    timeline = ConvertedPivotFilter("t", TIMELINE, "dt", (), ("2026-09-23", "2026-09-24"))
    note = pivot_filter_note("mart_dev.t", "dt", {"dt": timeline},
                             "SELECT job_id, COUNT(*) AS runs FROM ops.job_runs WHERE dt "
                             "BETWEEN '2026-09-23' AND '2026-09-24' /* Pivot filter: "
                             "Timeline dt */ GROUP BY job_id")
    assert "such as mart_dev.t_2026_09_23: dt: at least 2 tables" in note


# --- check() and promotion ----------------------------------------------------------------


def test_promotion_waits_on_a_pivot_filter_left_open(started: Path,
                                                     books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    databases = started / "admin" / "databases.py"
    databases.write_text(databases.read_text(encoding="utf-8")
                         .replace('"<PROD_DATABASE>"', '"mart"'), encoding="utf-8")
    with pytest.raises(ValueError, match="has a Decision open, pivot_filters: status"):
        project.promote([PIVOT])
