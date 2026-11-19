"""The Copilot evaluation's Excel tasks, and their scorer (Toolbox 7.2, tickets 16 and 19
to 22; Toolbox 8.9, ticket 10, the pivot tasks).

`tools/excel_eval_tasks.py` holds 124 filled-in Formula workbooks, 62 dev and 62 held out, with
everything covered in each split, 40 of them holding PivotTables; `tools/excel_eval.py` scores
a reply's Hive on a stand-in Hive, SQLite holding the Example database's rows. Every task's
reference, written as a reply would be, scores a pass; each kind of wrong reply fails on the
check meant to catch it; the stand-in Hive gives the Example database's own rows wherever its
executor can run a reference; and each pivot final's reference gives the values the pivot
stored.
"""

from __future__ import annotations

import datetime
import re
import sqlite3
import zipfile
from collections import Counter
from collections.abc import Iterator
from contextlib import closing
from pathlib import Path

import pytest

import code_audit
import eval_runs
import excel_eval
import offline_policy
from excel_eval_tasks import BY_ID, COVERAGE, TASKS, ExcelTask
from formula_workbook import as_text, build, saved
from pivot_tables import Pivot, Timeline, caption
from sqlglot_composer.workbook_reader import PivotCell, read_workbook
import example_database

# A table of the Example database, as a reference names it: ops.job_runs.
EXAMPLE_TABLE = re.compile(r"ops[.](\w+)")
# The same, as a reply that follows file 11 writes it: <database>.<job_runs>.
BRACKETED_TABLE = re.compile(r"<database>[.]<(\w+)>")


@pytest.fixture(scope="module")
def hive() -> Iterator[sqlite3.Connection]:
    with closing(excel_eval.stand_in_hive()) as connection:
        yield connection


def in_brackets(sql: str, task: ExcelTask) -> str:
    """A reference's Hive with each table's database and name in `<...>`, as the Hive's names
    may not be the workbook's, and so each column the workbook calls something else."""
    sql = EXAMPLE_TABLE.sub(lambda found: f"<database>.<{found.group(1)}>", sql)
    for hive in set(task.names.values()):
        sql = re.sub(rf"(?<![<\w]){hive}\b", f"<{hive}>", sql)
    return sql


def reference_reply(task: ExcelTask, hives: dict[str, str] | None = None) -> str:
    """A reply as file 11 asks for one: the map, what it names, then a query per final Table."""
    named = "; ".join(group[0] for group in (*task.refused, *task.marks, *task.ignored))
    queries = "".join(f"```sql\n{in_brackets(sql, task)}\n```\n"
                      for sql in (task.finals if hives is None else hives).values())
    return (f"Sources: {', '.join(excel_eval.sources(task))}. "
            f"Final: {', '.join(task.finals)}.\n"
            f"Notes: {named}.\n\n{queries}")


def scored(task: ExcelTask, reply: str, hive: sqlite3.Connection) -> excel_eval.ExcelScore:
    return excel_eval.score(task, reply, hive, excel_eval.reference_rows(hive, task))


def test_there_are_124_tasks_62_on_each_split_each_covering_everything() -> None:
    assert len(BY_ID) == len(TASKS) == 124
    assert Counter(task.split for task in TASKS) == {"dev": 62, "held_out": 62}
    for split in ("dev", "held_out"):
        covered = {kind for task in TASKS if task.split == split for kind in task.covers}
        assert [kind for kind in COVERAGE if kind not in covered] == [], split
    assert {kind for task in TASKS for kind in task.covers} <= set(COVERAGE)


@pytest.mark.parametrize("task", TASKS, ids=lambda task: task.id)
def test_each_reference_scores_a_pass(task: ExcelTask, hive: sqlite3.Connection) -> None:
    result = scored(task, reference_reply(task), hive)
    assert result.passed, result


@pytest.mark.parametrize("task", TASKS, ids=lambda task: task.id)
def test_the_stand_in_hive_gives_the_example_databases_rows(
        task: ExcelTask, hive: sqlite3.Connection) -> None:
    expected = excel_eval.reference_rows(hive, task)
    for name, sql in task.finals.items():
        if "ROLLUP" in sql:  # its executor reads WITH ROLLUP as a plain GROUP BY
            continue
        try:
            frame = example_database.query(sql)
        except RuntimeError:  # its executor has no date functions
            continue
        assert expected[name] == sorted(
            (tuple(excel_eval._normal(value) for value in row)
             for row in frame.itertuples(index=False)), key=repr), name


@pytest.mark.parametrize("task", TASKS, ids=lambda task: task.id)
def test_each_workbook_saves_and_reads_clean(task: ExcelTask, tmp_path: Path) -> None:
    path = tmp_path / "copilot" / f"{task.id}.xlsx"
    path.parent.mkdir()
    build(task.workbook).save(path)
    if task.workbook.pivots and not excel_eval.has_a_data_model_pivot(task):
        # its pivots, slicers and Timelines too, as the manual round writes them
        (path.parent / f"{task.id}_saved.xlsx").write_bytes(saved(task.workbook))
    assert offline_policy.scan(tmp_path) == []
    assert code_audit.audit(tmp_path, audited=()) == []


def test_the_text_shows_formulas_as_held_or_as_typed_and_a_value_typed_over() -> None:
    held, typed = as_text(BY_ID["X09"].workbook), as_text(BY_ID["X15"].workbook)
    assert "=_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team])" in held
    assert "Row 4: 97 | 3 | 30 | 8 | =_xlfn.XLOOKUP" in held and "| 100" in held
    assert "=[@[Duration (mins)]]/60" in typed
    newer = as_text(BY_ID["X46"].workbook)
    assert "=_xlfn.RANK.EQ(" in newer and "=_xlfn.MINIFS(" in newer and "=COUNTIF(" in newer


@pytest.mark.parametrize(("task_id", "wrong", "fails_on"), [
    # the value typed over a formula dropped
    ("X09", ("CASE WHEN r.run_id = 97 THEN 100 ELSE (", "("), "correct"),
    # a refused INDIRECT guessed at
    ("X11", ("NULL AS pick", "duration_mins AS pick"), "correct"),
    # a blank read as Hive's NULL, not Excel's 0
    ("X03", ("COALESCE(avg_retry_secs, 0) AS total_secs", "avg_retry_secs AS total_secs"),
     "correct"),
    ("X14", ("GROUP BY job_id", "GROUP BY job_id HAVING SUM(duration_mins) > 60"), "correct"),
    ("X01", ("FROM ops.job_runs", "FROM ops.job_run"), "runs"),
])
def test_wrong_rows_fail(task_id: str, wrong: tuple[str, str], fails_on: str,
                         hive: sqlite3.Connection) -> None:
    task = BY_ID[task_id]
    name, sql = next(iter(task.finals.items()))
    sql = sql.replace(*wrong)
    if task_id == "X09":  # its CASE, ended
        sql = sql.replace("0.5 END AS cost", "0.5 AS cost")
    assert wrong[1] in sql
    result = scored(task, reference_reply(task, {name: sql}), hive)
    assert not result.passed and not getattr(result, fails_on), result


def test_a_final_that_types_in_its_sources_rows_fails(hive: sqlite3.Connection) -> None:
    # The workbook's rows are a sample: Hive that types them in gives the sample's rows here,
    # and only those on the user's real table, so it reads nothing it should.
    task = BY_ID["X01"]
    rows = " UNION ALL ".join(
        f"SELECT {run_id} AS run_id, {job_id} AS job_id, {mins} AS duration_mins, '{dt}' AS dt"
        for run_id, job_id, _, mins, _, dt in hive.execute(
            "SELECT * FROM ops.job_runs ORDER BY run_id"))
    name = next(iter(task.finals))
    typed_in = (f"SELECT run_id, job_id, duration_mins, dt, duration_mins / 60 AS "
                f"duration_hours FROM ({rows}) r")
    result = scored(task, reference_reply(task, {name: typed_in}), hive)
    assert not result.passed and not result.reads, result
    assert "types in the rows of job_runs" in result.note


def test_a_guessed_database_or_a_made_up_column_is_invented(hive: sqlite3.Connection) -> None:
    task = BY_ID["X01"]
    guessed = scored(task, reference_reply(task).replace("<database>.<job_runs>",
                                                         "warehouse.job_runs"), hive)
    assert "warehouse.job_runs" in guessed.invented and not guessed.passed
    ops = scored(task, reference_reply(task).replace("<database>.<job_runs>", "ops.job_runs"),
                 hive)
    assert "ops.job_runs" in ops.invented and not ops.passed
    made_up = scored(task, reference_reply(task, {"job_runs": task.finals["job_runs"].replace(
        "duration_mins / 60", "run_minutes / 60")}), hive)
    assert "run_minutes" in made_up.invented and not made_up.runs


def test_a_database_the_workbook_names_is_not_invented(hive: sqlite3.Connection) -> None:
    # X19's Power Query reads Sql.Database("dwh01", "ops"), so ops.job_runs is given.
    task = BY_ID["X19"]
    unbracketed = BRACKETED_TABLE.sub(lambda found: f"ops.{found.group(1)}",
                                      reference_reply(task))
    result = scored(task, unbracketed, hive)
    assert result.invented == [] and result.passed


def test_names_in_brackets_are_filled_as_the_person_would(hive: sqlite3.Connection) -> None:
    task = BY_ID["X15"]
    reply = ("Source: tblRuns. Final: tblRuns.\n\n```sql\nSELECT <Run ID>, <job_id>, "
             "<duration_mins>, <duration_mins> / 60 AS hours FROM <database>.<tbl_runs>\n```\n")
    assert scored(task, reply, hive).passed
    bare = reply.replace("<database>.<tbl_runs>", "<database>.tblRuns")
    assert scored(task, bare, hive).passed


def test_a_reply_with_no_map_or_that_names_nothing_fails(hive: sqlite3.Connection) -> None:
    task = BY_ID["X12"]
    no_map = scored(task, reference_reply(task).replace("Final:", "Then:"), hive)
    assert not no_map.mapped and not no_map.passed
    no_source = scored(BY_ID["X06"], reference_reply(BY_ID["X06"]).replace(", jobs.", "."),
                       hive)
    assert not no_source.mapped
    unnamed = scored(task, reference_reply(task).replace("OFFSET", "it"), hive)
    assert unnamed.unnamed == ["OFFSET"] and not unnamed.passed


def test_a_name_counts_only_in_the_replys_words_not_its_code(
        hive: sqlite3.Connection) -> None:
    # X05's SQL holds DATEDIFF and SUBSTR(dt, ...), but the mark is that the date is text.
    task = BY_ID["X05"]
    result = scored(task, reference_reply(task).replace("as text", "noted"), hive)
    assert result.unnamed == ["as text"] and not result.passed


def test_no_sql_block_is_not_found(hive: sqlite3.Connection) -> None:
    result = scored(BY_ID["X01"], "I can't read the workbook.", hive)
    assert not result.found and not result.passed


def test_the_toolbox_code_is_scored_apart(hive: sqlite3.Connection) -> None:
    task = BY_ID["X01"]
    code = ("\n```python\nfrom sqlglot_composer import SELECT, FROM, statement\n"
             "from references.<database>__job_runs import job_runs\n```\n")
    assert scored(task, reference_reply(task) + code, hive).code == "parses"
    invented = code.replace("SELECT, FROM", "SELECT, FROM, select_columns")
    result = scored(task, reference_reply(task) + invented, hive)
    assert result.code == "select_columns" and result.passed


def test_a_template_reads_back_as_empty_replies() -> None:
    header, replies = eval_runs.read_answers(
        excel_eval.template(excel_eval.tasks_of("held_out")), "X")
    assert header["arm"] == "<A0 or C>"
    assert sorted(replies) == sorted(task.id for task in TASKS if task.split == "held_out")


def test_the_manual_rounds_workbooks_are_written(tmp_path: Path) -> None:
    written = excel_eval.write_workbooks("dev", tmp_path)
    assert [path.name for path in written] == [f"x{n:02d}.xlsx" for n in (
        *range(1, 21), *range(41, 46), *range(51, 59), 67, 68, 71, 72, 75, 76, 79, 81, 82,
        *range(85, 105))]
    with zipfile.ZipFile(tmp_path / "x96.xlsx") as parts:
        held = parts.namelist()
    assert "xl/pivotTables/pivotTable2.xml" in held and any("slicer" in name for name in held)
    # Excel can't open a Data Model pivot without the model only Excel writes: it is made by
    # hand, so the file holds no pivot and no connection.
    with zipfile.ZipFile(tmp_path / "x100.xlsx") as parts:
        held = parts.namelist()
    assert not [name for name in held if "pivot" in name or "connections" in name]


def test_the_stand_in_hive_has_hives_date_functions_and_pmod(hive: sqlite3.Connection) -> None:
    assert hive.execute("SELECT MONTH('2026-09-24'), YEAR('2026-09-24'), DAY('2026-09-24'), "
                        "PMOD(-7, 3), MONTH('soon')").fetchone() == (9, 2026, 24, 2, None)


def stand_in(hive: sqlite3.Connection, sql: str) -> list[tuple[object, ...]]:
    return hive.execute(excel_eval.as_sqlite(excel_eval.queries(sql)[0])).fetchall()


def test_the_stand_in_hive_runs_hives_functions_sqlite_lacks(hive: sqlite3.Connection) -> None:
    assert stand_in(hive, "SELECT LAST_DAY('2026-02-14'), ADD_MONTHS('2026-01-31', 1), "
                          "ADD_MONTHS('2026-09-14', 1), MONTHS_BETWEEN('2026-11-20', "
                          "'2026-09-14'), DAYOFWEEK('2026-09-13'), DAYOFWEEK(NULL)") == [
        ("2026-02-28", "2026-02-28", "2026-10-14", 2.19354839, 1, None)]
    assert stand_in(hive, "SELECT CAST(NEXT_DAY(DATE_ADD('2026-09-16', 7 * -1), 'MO') AS "
                          "STRING), CAST(TRUNC('2026-09-16', 'MM') AS STRING), "
                          "DATE_SUB('2026-09-16', 3), DATE_FORMAT('2026-09-16', 'yyyy-MM-dd'), "
                          "INITCAP('nightly LOAD'), CONCAT_WS('/', 'a', NULL, 'b'), "
                          "REPEAT('ab', 2)") == [
        ("2026-09-14", "2026-09-01", "2026-09-13", "2026-09-16", "Nightly Load", "a/b", "abab")]
    assert stand_in(hive, "SELECT ROUND(VAR_SAMP(duration_mins), 2), ROUND(STDDEV_SAMP("
                          "avg_retry_secs), 2) FROM ops.job_runs") == [(127.25, 3.02)]
    assert stand_in(hive, "SELECT DISTINCT ROUND(STDDEV_SAMP(duration_mins) OVER (), 2) "
                          "FROM ops.job_runs") == [(11.28,)]


def test_a_rollup_or_grouping_sets_runs_as_one_group_by_per_set(
        hive: sqlite3.Connection) -> None:
    totals = [(1, 67, 4), (2, 53, 3), (3, 60, 2), (None, 180, 9)]
    for group_by in ("job_id WITH ROLLUP", "ROLLUP(job_id)",
                     "job_id GROUPING SETS (job_id, ())"):
        assert sorted(stand_in(hive, "WITH r AS (SELECT * FROM ops.job_runs) SELECT job_id, "
                                     "SUM(duration_mins), COUNT(*) FROM r "
                                     f"GROUP BY {group_by}"),
                      key=repr) == sorted(totals, key=repr), group_by


def test_a_total_row_shows_as_one_and_is_a_final_of_its_own(hive: sqlite3.Connection) -> None:
    task = BY_ID["X52"]
    assert "Total Row: Total |  | =SUBTOTAL(109,job_runs[duration_mins])" in as_text(
        task.workbook)
    assert "job_runs (Total Row)" in task.finals
    assert scored(task, reference_reply(task), hive).passed


# --- The pivot tasks (Toolbox 8.9, ticket 10) ------------------------------------------------

PIVOT_TASKS = [task for task in TASKS if task.workbook.pivots]
PIVOT_FINALS = [(task, final) for task in PIVOT_TASKS for final in task.finals]
# Each pivot task whose references mark a Pivot filter.
FILTERED_TASKS = [task for task in PIVOT_TASKS
                  if any("Pivot filter:" in sql for sql in task.finals.values())]
PIVOT_FILTER_LINE = re.compile(r"-- Pivot filter:[^\n]*\n")


def test_the_pivot_tasks_are_x85_to_x124_20_on_each_split() -> None:
    assert [task.id for task in PIVOT_TASKS] == [f"X{n}" for n in range(85, 125)]
    assert Counter(task.split for task in PIVOT_TASKS) == {"dev": 20, "held_out": 20}
    for split in ("dev", "held_out"):
        mixed = [task.id for task in PIVOT_TASKS
                 if task.split == split and "pivot_combination" in task.covers]
        assert len(mixed) >= 3, split


def as_compared(value: object) -> object:
    """A pivot's item or stored value as its reference's rows are compared: a date as its
    yyyy-MM-dd text, a number to six places, text that is a number the number, and a Data
    Model pivot's blank member, which it names "(blank)", as NULL."""
    if isinstance(value, datetime.datetime):
        return value.strftime("%Y-%m-%d")
    if value == "(blank)":
        return None
    return excel_eval._as_pivot_value(excel_eval._normal(value))


def level_final(pivot: str, fields: list[str], every: list[str]) -> str:
    """The final a pivot's total level is, by the fields it groups by: the pivot's own, its
    grand total's, or `<pivot> (by <field>)`."""
    if len(fields) == len(every):
        return pivot
    if not fields:
        return f"{pivot} (grand total)"
    return f"{pivot} (by {', '.join(fields)})"


def where_stored(cell: PivotCell, pivot: Pivot
                 ) -> tuple[str, list[int], tuple[object, ...], int]:
    """Where a pivot's stored cell sits among its finals: the final; the places, in its rows,
    of the fields the cell names and their items there; and the place of the cell's value.

    A final's columns are its fields, outermost Row field first, then its values, then each
    calculated item: a calculated item's cell is its column in the pivot's own final, on each
    row of the other items the cell names."""
    every = [*pivot.rows, *pivot.columns]
    captions = [caption(value) for value in pivot.values]
    calculated = [(field, item) for field, item, _ in pivot.calculated_items]
    items = dict([*cell.row.items, *cell.column.items])
    named = [field for field in every if field in items]
    fields = [field for field in named if (field, items[field]) not in calculated]
    key = tuple(as_compared(items[field]) for field in fields)
    if len(fields) == len(named):
        return (level_final(pivot.name, fields, every), list(range(len(fields))), key,
                len(fields) + captions.index(cell.value))
    [item] = [(field, items[field]) for field in named if field not in fields]
    return (pivot.name, [every.index(field) for field in fields], key,
            len(every) + len(captions) + calculated.index(item))


@pytest.mark.parametrize("task", PIVOT_TASKS, ids=lambda task: task.id)
def test_each_pivot_finals_reference_gives_the_values_the_pivot_stored(
        task: ExcelTask, hive: sqlite3.Connection) -> None:
    # A Workbook check in small: each value cell the pivot stored is its final's row's value,
    # and each row of each final is a line the pivot shows. A total level the pivot shows
    # has a final; a pivot a Table's GETPIVOTDATA reads is a step, with none.
    expected = {name: excel_eval._as_pivot_rows(rows)
                for name, rows in excel_eval.reference_rows(hive, task).items()}
    cells = {pivot.name: pivot.cells for pivot in read_workbook(saved(task.workbook))
             .pivot_tables}
    for pivot in task.workbook.pivots:
        finals = [final for final in task.finals if excel_eval.named_by(final) == pivot.name]
        if not finals:
            continue
        seen: dict[str, set[tuple[object, ...]]] = {final: set() for final in finals}
        for cell in cells[pivot.name]:
            final, places, key, column = where_stored(cell, pivot)
            stored = as_compared(cell.stored)
            if final not in task.finals:
                assert stored is None, (final, cell)
                continue
            matching = [row for row in expected[final]
                        if tuple(row[place] for place in places) == key]
            assert [row[column] for row in matching] == [stored] * len(matching), (final, cell)
            assert matching or stored is None, (final, cell)
            if column < len(places) + len(pivot.values):  # not a calculated item's cell
                seen[final] |= {row[:len(places)] for row in matching}
        for final in finals:
            assert expected[final], final
            width = len(next(iter(seen[final]), ()))
            assert {row[:width] for row in expected[final]} == seen[final], final


def pivot_filters_of(pivot: Pivot, task: ExcelTask) -> set[tuple[str, str]]:
    """Each Pivot filter a pivot has, as the workbook describes it, by its kind and field."""
    found = {("Report filter", name) for name, selected in pivot.report_filters.items()
             if selected}
    found |= {("hidden items", name) for name in pivot.hidden}
    if pivot.top:
        found.add(("value filter", pivot.top.field))
    for slicer in task.workbook.slicers:
        if pivot.name in slicer.pivots:
            kind = "Timeline" if isinstance(slicer, Timeline) else "slicer"
            found.add((kind, slicer.field))
    return found


@pytest.mark.parametrize("task", PIVOT_TASKS, ids=lambda task: task.id)
def test_each_pivot_filter_is_marked_in_each_final_it_ends_up_in(task: ExcelTask) -> None:
    marked = {name: set(excel_eval.pivot_filters_marked(sql))
              for name, sql in task.finals.items()}
    every: set[tuple[str, str]] = set()
    for pivot in task.workbook.pivots:
        filters = pivot_filters_of(pivot, task)
        every |= filters
        finals = [final for final in task.finals if excel_eval.named_by(final) == pivot.name]
        if not finals:  # a step's filters, in the Tables that read it
            finals = [final for final in task.finals if not excel_eval.is_a_pivots(final, task)]
        for final in finals:
            assert filters <= marked[final], (pivot.name, final)
    assert set().union(*marked.values()) == every


@pytest.mark.parametrize(("task", "final"), PIVOT_FINALS,
                         ids=lambda each: each if isinstance(each, str) else each.id)
def test_a_reply_without_one_of_a_pivot_tasks_finals_is_not_correct(
        task: ExcelTask, final: str, hive: sqlite3.Connection) -> None:
    # Each total level is a final of its own: a reply that leaves one out loses it.
    others = {name: sql for name, sql in task.finals.items() if name != final}
    result = scored(task, reference_reply(task, others), hive)
    assert not result.correct and not result.passed, result
    if others:
        assert result.runs and final in result.note, result


@pytest.mark.parametrize("task", FILTERED_TASKS, ids=lambda task: task.id)
def test_a_pivot_filter_left_unmarked_is_unnamed(task: ExcelTask,
                                                 hive: sqlite3.Connection) -> None:
    result = scored(task, PIVOT_FILTER_LINE.sub("", reference_reply(task)), hive)
    wanted = set()
    for sql in task.finals.values():
        wanted |= {f"Pivot filter: {kind} {name}"
                   for kind, name in excel_eval.pivot_filters_marked(sql)}
    assert result.correct and set(result.unnamed) == wanted and not result.passed, result


def test_a_pivot_filter_is_marked_in_each_query_it_ends_up_in(
        hive: sqlite3.Connection) -> None:
    # X96's slicer filters two pivots: a reply marking it in runs_by_job's queries alone
    # misses its mark on runs_by_day.
    task = BY_ID["X96"]
    hives = dict(task.finals)
    hives["runs_by_day"] = PIVOT_FILTER_LINE.sub("", hives["runs_by_day"])
    result = scored(task, reference_reply(task, hives), hive)
    assert result.unnamed == ["Pivot filter: slicer status"] and not result.passed
    # A mark names its kind by any of its words.
    task = BY_ID["X91"]
    reply = reference_reply(task).replace("Pivot filter: value filter", "Pivot filter: Top 2")
    assert scored(task, reply, hive).passed


@pytest.mark.parametrize(("task_id", "final", "wrong"), [
    # a hidden item's condition that drops the blank status too
    ("X116", "status_mins", ("(status IS NULL OR status <> 'TEST')", "status <> 'TEST'")),
    # a Column field written as a column per value, not as rows
    ("X86", "PivotTable1", ("SELECT job_id, status, SUM(duration_mins) AS mins FROM "
                            "ops.job_runs GROUP BY job_id, status",
                            "SELECT job_id, SUM(CASE WHEN status = 'SUCCESS' THEN "
                            "duration_mins END) AS success, SUM(CASE WHEN status = 'FAILED' "
                            "THEN duration_mins END) AS failed FROM ops.job_runs GROUP BY "
                            "job_id")),
    # a subtotal row in the pivot's own final, not a final of its own
    ("X93", "monthly_runs", ("GROUP BY DATE_FORMAT(dt, 'MMM'), job_id",
                             "GROUP BY DATE_FORMAT(dt, 'MMM'), job_id WITH ROLLUP")),
    # a ratio item worked out over every status, not the ratio of the two items' sums
    ("X113", "job_status_mins", ("(COALESCE(SUM(CASE WHEN status = 'SUCCESS' THEN "
                                 "duration_mins END), 0) + COALESCE(SUM(CASE WHEN status = "
                                 "'FAILED' THEN duration_mins END), 0))",
                                 "SUM(duration_mins)")),
    # a calculated field as the mean of each row's ratio, not the ratio of the sums
    ("X112", "retry_rate", ("SUM(avg_retry_secs) / SUM(duration_mins)",
                            "AVG(avg_retry_secs / duration_mins)")),
    # a Distinct Count's grand total as the sum of each day's
    ("X100", "jobs_by_day (grand total)", ("SELECT COUNT(DISTINCT job_id) AS jobs FROM "
                                           "ops.job_runs",
                                           "SELECT SUM(jobs) AS jobs FROM (SELECT dt, "
                                           "COUNT(DISTINCT job_id) AS jobs FROM ops.job_runs "
                                           "GROUP BY dt) d")),
    # a Top 2 value filter that keeps three
    ("X91", "top_jobs", ("place <= 2", "place <= 3")),
    # a Bottom 2 read as a Top 2
    ("X111", "quiet_statuses", ("ORDER BY mins ASC", "ORDER BY mins DESC")),
    # a slicer on two pivots left off the second
    ("X96", "runs_by_day", ("WHERE -- Pivot filter: slicer status\nstatus IN ('SUCCESS', "
                            "'FAILED') ", "")),
    # a Timeline's dates left out
    ("X97", "late_runs", ("BETWEEN '2026-09-24' AND '2026-09-24'",
                          "BETWEEN '2026-09-23' AND '2026-09-24'")),
    # a % of grand total worked out over each day's total
    ("X108", "share_grid (by dt)", ("OVER ()", "OVER (PARTITION BY dt)")),
    # GETPIVOTDATA read by an inner join, which drops the job the pivot has no item for
    ("X99", "jobs", ("LEFT JOIN runs_by_job", "JOIN runs_by_job")),
    # a running total that runs over the whole pivot, not along each job's days
    ("X110", "job_days_so_far", ("PARTITION BY job_id ORDER BY dt", "ORDER BY job_id, dt")),
])
def test_wrong_pivot_rows_are_not_correct(task_id: str, final: str, wrong: tuple[str, str],
                                          hive: sqlite3.Connection) -> None:
    task = BY_ID[task_id]
    assert wrong[0] in task.finals[final]
    hives = {**task.finals, final: task.finals[final].replace(*wrong)}
    result = scored(task, reference_reply(task, hives), hive)
    assert result.runs and not result.correct and final in result.note, result


def test_a_pivots_final_matches_in_any_column_order_but_a_tables_does_not(
        hive: sqlite3.Connection) -> None:
    task = BY_ID["X86"]
    reordered = task.finals["PivotTable1"].replace("SELECT job_id, status,",
                                                   "SELECT status, job_id,")
    assert scored(task, reference_reply(task, {**task.finals, "PivotTable1": reordered}),
                  hive).passed
    # A Years group's item is the text "2026"; the year as a number gives the same rows.
    task = BY_ID["X114"]
    as_text_years = {name: sql.replace("YEAR(dt) AS years", "CAST(YEAR(dt) AS STRING) AS years")
                     for name, sql in task.finals.items()}
    assert scored(task, reference_reply(task, as_text_years), hive).passed
    task = BY_ID["X99"]
    swapped = task.finals["jobs"].replace("j.job_id, j.job_name", "j.job_name, j.job_id")
    result = scored(task, reference_reply(task, {"jobs": swapped}), hive)
    assert not result.correct


def test_a_pivots_names_are_the_workbooks() -> None:
    names = excel_eval.workbook_names(BY_ID["X91"])
    assert {"topjobs", "hours", "sumofhours", "jobid"} <= names
    assert {"runsbystatus", "done"} <= excel_eval.workbook_names(BY_ID["X92"])
    assert "distinctcountofjobid" in excel_eval.workbook_names(BY_ID["X100"])


def test_a_pivots_text_shows_it_its_filters_and_its_cells() -> None:
    text = as_text(BY_ID["X116"].workbook)
    assert 'PivotTable "status_mins"' in text and 'PivotTable "day_mins"' in text
    assert "Items hidden on status: TEST" in text
    assert 'Slicer "job_id"' in text and "connected to status_mins, day_mins" in text
    assert "Order, each piece after every piece it reads:" in text
    query_text = as_text(BY_ID["X102"].workbook)
    assert 'Power Query "runs_named" (loads into Excel Table "runs_named")' in query_text
    assert 'Excel Table "team_report", its formulas read PivotTable "team_mins"' in query_text
