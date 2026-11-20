"""Each Pivot filter is a Decision of its table (Toolbox 8.9, ticket 08; CONTEXT.md's Pivot
filter).

A table made from a PivotTable that leaves rows out holds PIVOT_FILTERS in its Table
reference, one line per filter, kept as converted ("keep") until answered. Its other answers
keep every value instead: "fold", the filtered column part of what one row is; "batch", one
table written one value at a time, each run its value, a Script tag whose answer is proposed;
and "tables", a table per value, `<table>_<value>`. Each table's line and checklist say how
many tables each answer makes, a table per value's layer by layer, "at least" as many as the
PivotTable's cache held, its values named; a Copilot `.hql` alone holds no cache, so its count
isn't known. The user's words: "emphasize how many different tables it would create. a
filter with 100 conditions would make 100 tables, but the higher layer filter may have only
3, which is manageable." Each answer gives the table it says, rows checked on the Example
database, and keeps the answers you gave that still fit, a Key among them.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import test_convert_workbooks as workbooks_converted
from test_convert_workbooks import COPILOT_PIVOT, DEV, checklist, converted, decide

import example_database
from sqlglot_composer import hivevar, project, run_execute, run_query, to_hive
from sqlglot_composer.pivot_filters import (
    answer_problem,
    layer_counts,
    layers_in_words,
    pivot_filter_keys,
    pivot_filter_note,
    table_slices,
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
# What the slicer's line says of each answer, as its Table reference, check() and the pasted
# DECISIONS say it.
SLICER_SAID = ('the slicer on status keeps FAILED and SUCCESS. "keep": 1 table, that '
               'selection; "fold": 1 table, every status; "batch": 1 table, a Partition per '
               'status; "tables": at least 4 tables, one per status the PivotTable\'s cache '
               "held (FAILED, SUCCESS, TEST and blank)")
BY_STATUS = ("SELECT job_id, status, SUM(duration_mins) AS sum_of_duration_mins FROM "
             "ops.job_runs GROUP BY job_id, status")
AS_CONVERTED = ("SELECT job_id, SUM(duration_mins) AS sum_of_duration_mins FROM ops.job_runs "
                "WHERE status IN ('FAILED', 'SUCCESS') GROUP BY job_id")


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


def key_line(root: Path, table: str) -> str:
    """A table's key= line, as its Table reference holds it."""
    return next(line for line in reference(root, table).split("\n")
                if line.startswith("    key="))


def same_rows(table: str, hive: str) -> None:
    """Assert a table's preview gives the rows `hive` gives, column by column."""
    mine, theirs = rows_of(table), rows_of_hive(hive)
    assert list(mine.columns) == list(theirs.columns)
    pd.testing.assert_frame_equal(mine, theirs, check_dtype=False)


# --- The Decision, as convert asks it ------------------------------------------------------


def test_each_pivot_filter_is_a_decision_kept_as_converted(started: Path,
                                                           books: dict[str, bytes]) -> None:
    report = converted(started, books, "slicer")
    assert ("Kept each Pivot filter as converted, so each of these tables holds only the rows "
            "the PivotTable's filter or slicer selected when the workbook was last saved: "
            "mart_dev.pivot, where the slicer on status keeps FAILED and SUCCESS;") in report
    assert ("Each is a Decision of its table, which can keep every value instead: answer "
            '"pivot_filters" in the decisions cell') in report
    assert (f'            "status": "keep",  # {SLICER_SAID[0].upper()}{SLICER_SAID[1:]}. Or '
            'answer "fold", "batch" or "tables", as its checklist says.') in report
    assert (f'    "status": "keep",  # TODO: proposed: {SLICER_SAID}'
            in reference(started, PIVOT))
    opened = checklist(started, "pivot").split("## Notes")[0]
    assert (f"- pivot_filters: status, a Pivot filter. {SLICER_SAID[0].upper()}"
            f'{SLICER_SAID[1:]}. Answer "keep" to keep its selection as converted, or "fold", '
            '"batch" or "tables" to keep every value instead, as its checklist says, in '
            "references/mart_dev__pivot.py") in opened
    assert "pivot_filters: status, a Pivot filter." in repr(project.check())


def test_the_checklist_translates_what_the_table_shows_and_each_answer(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    notes = checklist(started, "pivot").split("## Notes")[1]
    assert ("Pivot filter status, a Decision. What mart_dev.pivot shows: sum_of_duration_mins "
            "by job_id, only where the slicer on status keeps FAILED and SUCCESS, as the "
            'workbook was last saved. Its answers, each given as "pivot_filters": {"status": '
            '...}: "keep", proposed: 1 table, that selection alone.') in notes
    assert ('"fold": like dragging status from Filters to Rows in the PivotTable: 1 table, '
            "every status, status a column of mart_dev.pivot and part of what one row is, a "
            "row for each job_id and status.") in notes
    assert ('"batch": 1 table written one status at a time, each run writing its own '
            "status's rows: mart_dev.pivot is partitioned on status, a Partition per status "
            "(at least 4 Partitions), and the status each run writes is the Script tag STATUS, "
            'answered under "tags" with the Run value proposed there.') in notes
    assert ('"tables": like Excel\'s Show Report Filter Pages: a table per status, named '
            "mart_dev.pivot_<value>, such as mart_dev.pivot_failed: status: at least 4 tables "
            "(FAILED, SUCCESS, TEST and blank). A layer is each field the table is filtered "
            'on, and "at least" as these are the values the PivotTable\'s cache held when the '
            "workbook was saved: the warehouse may hold more.") in notes
    assert ('Which to pick: to tab through each status in a presentation, as with a slicer, '
            '"fold" keeps every status in one table to slice later; "batch" when each status '
            'is written on its own schedule; "tables" only for a handful; "keep" when one '
            "selection is all anyone needs. A handful of tables, such as 3, is manageable; a "
            'hundred is a reason to "fold" or "batch" instead.') in notes
    # A grand total shows its values over every row.
    assert ("What mart_dev.pivot_grand_total shows: sum_of_duration_mins over every row"
            in checklist(started, "pivot_grand_total"))


def test_keep_makes_the_decision_and_leaves_the_table_as_converted(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    hive = (started / "tables" / f"{DEV}__pivot" / "conversion" / "in_dev.hql").read_text(
        encoding="utf-8")
    decide({PIVOT: {"pivot_filters": {"status": "keep"}}})
    assert "pivot_filters" not in checklist(started, "pivot").split("## Notes")[0]
    assert f'    "status": "keep",  # {SLICER_SAID}' in reference(started, PIVOT)
    assert (started / "tables" / f"{DEV}__pivot" / "conversion" / "in_dev.hql").read_text(
        encoding="utf-8") == hive
    same_rows(PIVOT, AS_CONVERTED)


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
            "again for its Pivot filters' answers: every status, status part of what one row "
            "is.") in report
    same_rows(PIVOT, BY_STATUS)
    text = reference(started, PIVOT)
    assert '        "status": "string",' in text
    # Its Key was the Toolbox's proposal: it is proposed again from the new query.
    assert 'key=["job_id", "status"],  # proposed from its query' in text
    assert "WHERE" not in to_hive(project.load(PIVOT).preview())


def test_batch_partitions_the_table_and_proposes_the_value_each_run_writes(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    decide({PIVOT: {"pivot_filters": {"status": "batch"}}})
    text = reference(started, PIVOT)
    assert 'partitioned_by=["status"],' in text
    assert ('"STATUS": "<PARM=\\"STATUS\\"/>",  # inside quotes. Answer it with the value '
            'each run writes; proposed: hivevar("STATUS", default="FAILED")') in text
    # The value each run writes is a Script tag's, a Decision with an answer to accept.
    checked = repr(project.check())
    assert 'tags: STATUS, proposed hivevar("STATUS", default="FAILED"): accept it' in checked
    assert "from sqlglot_composer import hivevar  # for a Hivevar proposed below" in checked
    assert '"STATUS": hivevar("STATUS", default="FAILED"),  # proposed: keep it' in checked
    decide({PIVOT: {"tags": {"STATUS": "FAILED"},
                    "location": "/data/team/mart_dev.db/pivot"}})
    same_rows(PIVOT, "SELECT job_id, SUM(duration_mins) AS sum_of_duration_mins FROM "
                     "ops.job_runs WHERE status = 'FAILED' GROUP BY job_id")
    write = to_hive(project.load(PIVOT).write())
    assert "INSERT OVERWRITE TABLE mart_dev.pivot PARTITION(status = 'FAILED')" in write


def test_a_batch_answered_as_proposed_leaves_each_runs_value_to_the_warehouse(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    decide({PIVOT: {"pivot_filters": {"status": "batch"},
                    "location": "/data/team/mart_dev.db/pivot"}})
    decide({PIVOT: {"tags": {"STATUS": hivevar("STATUS", default="FAILED")}}})
    write = to_hive(project.load(PIVOT).write())
    assert "PARTITION(status = '${hivevar:STATUS}')" in write
    assert "status = '${hivevar:STATUS}'" in write.split("WHERE")[1]


def test_a_batch_of_days_proposes_the_run_value_of_the_latest_partition(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "timeline")
    decide({PIVOT: {"pivot_filters": {"dt": "batch"}}})
    assert ('Answer it with the value each run writes; proposed: latest_dt, from '
            'project.new_run_value("latest_dt", latest_partition="ops.job_runs.dt")'
            ) in reference(started, PIVOT)
    checked = repr(project.check())
    assert ('project.new_run_value("latest_dt", latest_partition="ops.job_runs.dt")\n'
            "from building_blocks.run_values import latest_dt  # its Run value\n"
            "DECISIONS = {") in checked
    assert '"DT": latest_dt,  # proposed: keep it to accept it' in checked


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
    assert (f"{PIVOT}: passed, on status = 'SUCCESS', the latest Partition {PIVOT} holds"
            in report)


def test_tables_makes_a_table_per_value_each_holding_its_slice(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    report = decide({PIVOT: {"pivot_filters": {"status": "tables"}}})
    made = [f"{PIVOT}_{name}" for name in ("failed", "success", "test", "blank")]
    assert project.batch_tables("book")[:4] == made
    assert (f"{PIVOT} became {PIVOT}_failed, the table of its first value, FAILED, and 3 more "
            f"tables were made beside it, one per value: {PIVOT}_success, {PIVOT}_test and "
            f"{PIVOT}_blank.") in report
    assert not (started / "tables" / f"{DEV}__pivot").exists()
    for table, value in zip(made, STATUSES, strict=True):
        condition = "status IS NULL" if value is None else f"status = '{value}'"
        same_rows(table, "SELECT job_id, SUM(duration_mins) AS sum_of_duration_mins FROM "
                         f"ops.job_runs WHERE {condition} GROUP BY job_id")
        assert ("Made by its Pivot filters' answers: this table holds the rows of status "
                in checklist(started, table.split(".")[1]))
        assert f'NAME = "{table.split(".")[1]}"  # for PivotTable1' in reference(started, table)


def test_a_table_per_value_holds_its_own_location_and_answers_of_its_own(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    decide({PIVOT: {"pivot_filters": {"status": "tables"},
                    "location": "/data/team/mart_dev.db/pivot"}})
    assert 'location="/data/team/mart_dev.db/pivot",' in reference(started, f"{PIVOT}_failed")
    assert "location=None,  # TODO:" in reference(started, f"{PIVOT}_success")
    assert "location:" in repr(project.check())


# --- A Key you answered, through each answer -------------------------------------------------


@pytest.mark.parametrize(("answer", "kept"), [("keep", True), ("tables", True),
                                              ("fold", False), ("batch", False)])
def test_a_key_you_answered_is_kept_unless_what_one_row_is_changes(
        started: Path, books: dict[str, bytes], answer: str, kept: bool) -> None:
    converted(started, books, "slicer")
    decide({PIVOT: {"key": ["job_id"], "pivot_filters": {"status": "keep"}}})
    decide({PIVOT: {"pivot_filters": {"status": answer}}})
    table = f"{PIVOT}_failed" if answer == "tables" else PIVOT
    if kept:
        assert key_line(started, table) == '    key=["job_id"],'
        return
    # job_id alone no longer names one row: the Key from its query is proposed, to accept.
    assert key_line(started, table) == (
        '    key=None,  # TODO: proposed ["job_id", "status"] from its query, as its Pivot '
        "filters' answers changed what one row is: accept it in the decisions cell")
    assert ('key: proposed ["job_id", "status"] from its query, as its Pivot filters\' answers '
            "changed what one row is: accept it") in repr(project.check())
    decide({PIVOT: {"key": "proposed"}})
    assert key_line(started, table) == '    key=["job_id", "status"],'


def test_a_key_that_still_fits_is_kept_through_a_fold(started: Path,
                                                      books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    decide({PIVOT: {"key": ["job_id", "status"]}})
    decide({PIVOT: {"pivot_filters": {"status": "fold"}}})
    assert key_line(started, PIVOT) == '    key=["job_id", "status"],'


def test_a_key_whose_columns_are_gone_is_proposed_again(started: Path,
                                                        books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    decide({PIVOT: {"pivot_filters": {"status": "fold"}}})
    decide({PIVOT: {"key": "proposed"}})
    decide({PIVOT: {"pivot_filters": {"status": "keep"}}})
    assert key_line(started, PIVOT).startswith('    key=None,  # TODO: proposed ["job_id"]')


# --- Answering again -----------------------------------------------------------------------


def test_answering_again_changes_it_back(started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    decide({PIVOT: {"pivot_filters": {"status": "fold"}}})
    decide({PIVOT: {"pivot_filters": {"status": "keep"}}})
    same_rows(PIVOT, AS_CONVERTED)
    assert '"status": "string"' not in reference(started, PIVOT)


def test_answering_a_table_per_value_again_makes_it_one_table(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    decide({PIVOT: {"pivot_filters": {"status": "tables"}}})
    report = decide({f"{PIVOT}_success": {"pivot_filters": {"status": "fold"}}})
    assert (f"{PIVOT}_success became {PIVOT} again, one table, as its Pivot filters' answers "
            "make no table per value now.") in report
    assert f"its Pivot filters' answers no longer make {PIVOT}_failed." in report
    assert project.batch_tables("book")[0] == PIVOT
    assert not [table for table in project.batch_tables("book") if "pivot_" in table
                and "grand_total" not in table]
    same_rows(PIVOT, BY_STATUS)


# --- Converting again, as after editing a script or the workbook -----------------------------

LOCATION_ROOT = "/data/team/dev"
# The rows each answer gives, by each table it makes.
ROWS_ANSWERED = {
    "keep": {PIVOT: AS_CONVERTED},
    "fold": {PIVOT: BY_STATUS},
    "batch": {PIVOT: "SELECT job_id, SUM(duration_mins) AS sum_of_duration_mins FROM "
                     "ops.job_runs WHERE status = 'FAILED' GROUP BY job_id"},
    "tables": {f"{PIVOT}_{name}": "SELECT job_id, SUM(duration_mins) AS sum_of_duration_mins "
                                  f"FROM ops.job_runs WHERE {condition} GROUP BY job_id"
               for name, condition in [("failed", "status = 'FAILED'"),
                                       ("success", "status = 'SUCCESS'"),
                                       ("test", "status = 'TEST'"),
                                       ("blank", "status IS NULL")]},
}


def placed_under_a_location_root(root: Path) -> None:
    """Fill in DEV's location_root, which places each table with no location of its own."""
    databases = root / "admin" / "databases.py"
    databases.write_text(databases.read_text(encoding="utf-8").replace(
        '"<DEV_LOCATION_ROOT>"', f'"{LOCATION_ROOT}"'), encoding="utf-8")


@pytest.mark.parametrize("answer", list(ROWS_ANSWERED))
def test_converting_again_keeps_each_answer_and_the_tables_it_made(
        started: Path, books: dict[str, bytes], answer: str) -> None:
    placed_under_a_location_root(started)
    converted(started, books, "slicer")
    decide({PIVOT: {"pivot_filters": {"status": answer}}})
    if answer == "batch":
        decide({PIVOT: {"tags": {"STATUS": "FAILED"}}})
    answered = project.batch_tables("book")
    converted(started, books, "slicer")
    assert project.batch_tables("book") == answered
    for table, hive in ROWS_ANSWERED[answer].items():
        text = reference(started, table)
        assert f'    "status": "{answer}",' in text
        # Each in its own folder, the first value's table too, not the converted table's.
        short = table.split(".")[1]
        assert f'    location="{LOCATION_ROOT}/{DEV}.db/{short}",' in text
        same_rows(table, hive)


def test_a_table_per_value_keeps_its_decision_through_converting_again(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    decide({PIVOT: {"pivot_filters": {"status": "tables"}}})
    converted(started, books, "slicer")
    assert f"{PIVOT}_success: pivot_filters" not in repr(project.check())
    decide({f"{PIVOT}_success": {"pivot_filters": {"status": "fold"}}})
    assert project.batch_tables("book")[0] == PIVOT
    same_rows(PIVOT, BY_STATUS)


def test_converting_again_keeps_each_location_answered(started: Path,
                                                       books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    decide({PIVOT: {"pivot_filters": {"status": "tables"}}})
    made = list(ROWS_ANSWERED["tables"])
    decide({table: {"location": f"/data/team/{table}"} for table in made})
    converted(started, books, "slicer")
    for table in made:
        assert f'    location="/data/team/{table}",' in reference(started, table)
    checked = repr(project.check())
    assert not [table for table in made if f"{table}: location" in checked]


def edited_in_dev(root: Path, table: str) -> None:
    """Change a table's conversion/in_dev.hql by hand, after its Pivot filters' answers wrote
    it."""
    path = root / "tables" / f"{table.replace('.', '__')}" / "conversion" / "in_dev.hql"
    path.write_text(path.read_text(encoding="utf-8") + "-- checked by hand\n",
                    encoding="utf-8")


def test_the_tables_per_value_outlive_an_edit_to_the_hive_the_answers_wrote(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    decide({PIVOT: {"pivot_filters": {"status": "tables"}}})
    answered = project.batch_tables("book")
    edited_in_dev(started, f"{PIVOT}_failed")
    converted(started, books, "slicer")
    assert project.batch_tables("book") == answered
    assert f"{PIVOT}_success: pivot_filters" not in repr(project.check())


def test_an_answer_given_again_on_hive_changed_since_says_to_convert_again_first(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    decide({PIVOT: {"pivot_filters": {"status": "tables"}}})
    edited_in_dev(started, f"{PIVOT}_failed")
    with pytest.raises(ValueError) as refused:
        decide({f"{PIVOT}_success": {"pivot_filters": {"status": "fold"}}})
    said = " ".join(str(refused.value).split())
    assert (f"{PIVOT}_success: pivot_filters: tables/{DEV}__pivot_failed/conversion/in_dev.hql "
            "is no longer the Hive its Pivot filters' answers wrote, and answering them again "
            "writes each table they made again from the Hive it was converted from, over that "
            "change: convert the batch again first, with overwrite=True") in said
    assert project.batch_tables("book")[0] == f"{PIVOT}_failed"
    # Converted again afresh, the Hive is the conversion's again, and the answer is written.
    project.convert("book", files=["runs.xlsx"], query=example_database.query,
                    database="ops", overwrite=True)
    decide({f"{PIVOT}_success": {"pivot_filters": {"status": "fold"}}})
    same_rows(PIVOT, BY_STATUS)


def test_a_name_and_pivot_filters_answered_at_once_rename_then_rewrite(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    decide({PIVOT: {"name": "runs_by_job", "pivot_filters": {"status": "fold"}},
            f"{PIVOT}_grand_total": {"pivot_filters": {"status": "fold"}}})
    same_rows(f"{DEV}.runs_by_job", BY_STATUS)
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


def test_a_filter_in_a_step_others_read_refuses_fold_and_batch_saying_what_to_do() -> None:
    slicer = ConvertedPivotFilter("t", SLICER, "status", ("FAILED",), STATUSES)
    hive = ("WITH failed AS (SELECT job_id, status, duration_mins FROM ops.job_runs WHERE "
            "status = 'FAILED' /* Pivot filter: slicer status */) SELECT job_id, "
            "SUM(duration_mins) AS minutes FROM failed GROUP BY job_id")
    for answer in ("fold", "batch"):
        assert answer_problem(hive, slicer, answer) == (
            "this filter sits in a step, a CTE that other parts of the query read too, so "
            "making status part of what one row is there would change their rows as well: "
            'answer "keep" or "tables", or move the filter out of the step in the Hive and '
            "convert it again")
    assert answer_problem(hive, slicer, "tables") is None


# --- A value filter, and a script's Pivot filter -------------------------------------------


def test_a_value_filter_folds_to_every_item_and_has_nothing_to_batch(
        started: Path, books: dict[str, bytes]) -> None:
    converted(started, books, "top")
    assert ('the value filter on job_id keeps the top 2 job_id by Sum of duration_mins. '
            '"keep": 1 table, those 2; "fold": 1 table, every job_id. A value filter has only '
            "these two answers") in reference(started, PIVOT)
    with pytest.raises(ValueError, match="a value filter keeps items by their rank among the "
                                         "rest, which changes as the rows do, so it has no "
                                         "fixed value to write a batch or a table for"):
        decide({PIVOT: {"pivot_filters": {"job_id": "tables"}}})
    decide({PIVOT: {"pivot_filters": {"job_id": "fold"}}})
    same_rows(PIVOT, "SELECT job_id, SUM(duration_mins) AS sum_of_duration_mins FROM "
                     "ops.job_runs GROUP BY job_id")


def test_a_scripts_pivot_filter_says_its_count_isnt_known_and_why(started: Path) -> None:
    (started / "copilot.hql").write_text(COPILOT_PIVOT, encoding="utf-8")
    project.convert("pivot", files=["copilot.hql"], query=example_database.query,
                    database="ops")
    notes = checklist(started, "pivot")
    assert ("how many isn't known, as its Hive came from a script, which holds no PivotTable "
            "cache of the values status takes") in notes
    assert ('"tables": a table per status, how many not known, as a script\'s Hive holds no '
            "PivotTable cache") in reference(started, PIVOT)
    with pytest.raises(ValueError, match="how many values status takes isn't known"):
        project.write_decisions({PIVOT: {"pivot_filters": {"status": "tables"}}})
    # Folding needs no count.
    project.write_decisions({PIVOT: {"pivot_filters": {"status": "fold"}}})
    same_rows(PIVOT, BY_STATUS)


# --- Two layers ---------------------------------------------------------------------------

TWO_LAYERS = [
    ConvertedPivotFilter("t", SLICER, "Region", ("East",), ("East", "West", "North")),
    ConvertedPivotFilter("t", HIDDEN_ITEMS, "Site", (),
                         tuple(f"site {number}" for number in range(100))),
]


def test_each_layer_counts_its_tables_and_the_layers_together() -> None:
    keyed = pivot_filter_keys(TWO_LAYERS)
    assert layer_counts(keyed) == [(["Region"], 3), (["Site"], 100), (["Region", "Site"], 300)]
    assert layers_in_words(keyed) == (
        "Region: at least 3 tables (East, West and North); Site: at least 100 tables (site 0, "
        "site 1, site 2, site 3, site 4 and 95 more); Region and Site together: at least 300 "
        "tables")
    slices = table_slices("mart_dev.t", keyed, {"Region": "tables", "Site": "tables"})
    assert len(slices) == 300
    assert slices["mart_dev.t_east_site_0"] == {"Region": "East", "Site": "site 0"}
    assert list(table_slices("mart_dev.t", keyed, {"Region": "tables"})) == [
        "mart_dev.t_east", "mart_dev.t_west", "mart_dev.t_north"]


def test_a_workbook_with_two_layers_counts_each_and_both(started: Path,
                                                        books: dict[str, bytes]) -> None:
    converted(started, books, "timeline")
    notes = checklist(started, "pivot")
    assert ("status: at least 4 tables (FAILED, SUCCESS, TEST and blank); dt: at least 2 "
            "tables (2026-09-23 and 2026-09-24); status and dt together: at least 8 tables. "
            "A layer is each field the table is filtered on") in notes
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
    assert ("such as mart_dev.t_2026_09_23: dt: at least 2 tables (2026-09-23 and "
            "2026-09-24)") in note


# --- check() and promotion ----------------------------------------------------------------


def test_promotion_waits_on_a_pivot_filter_left_open(started: Path,
                                                     books: dict[str, bytes]) -> None:
    converted(started, books, "slicer")
    databases = started / "admin" / "databases.py"
    databases.write_text(databases.read_text(encoding="utf-8")
                         .replace('"<PROD_DATABASE>"', '"mart"'), encoding="utf-8")
    with pytest.raises(ValueError, match="has a Decision open, pivot_filters: status"):
        project.promote([PIVOT])
