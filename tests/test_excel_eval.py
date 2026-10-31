"""The Copilot evaluation's Excel tasks, and their scorer (Toolbox 7.2, tickets 16 and 19
to 22).

`tools/excel_eval_tasks.py` holds 78 filled-in Formula workbooks, 39 dev and 39 held out, with
everything covered in each split; `tools/excel_eval.py` scores a reply's Hive on a stand-in
Hive, SQLite holding the Example database's rows. Every task's reference, written as a reply
would be, scores a pass; each kind of wrong reply fails on the check meant to catch it; and
the stand-in Hive gives the Example database's own rows wherever its executor can run a
reference.
"""

from __future__ import annotations

import re
import sqlite3
from collections import Counter
from pathlib import Path

import pytest

import code_audit
import excel_eval
import offline_policy
from excel_eval_tasks import BY_ID, COVERAGE, TASKS, ExcelTask
from formula_workbook import as_text, build
from sqlglot_composer import example_database

# A table of the Example database, as a reference names it: ops.job_runs.
EXAMPLE_TABLE = re.compile(r"ops[.](\w+)")
# The same, as a reply that follows file 11 writes it: <database>.<job_runs>.
BRACKETED_TABLE = re.compile(r"<database>[.]<(\w+)>")


@pytest.fixture(scope="module")
def hive() -> sqlite3.Connection:
    return excel_eval.stand_in_hive()


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
                      for sql in (hives or task.finals).values())
    return (f"Sources: {', '.join(excel_eval.sources(task))}. "
            f"Final: {', '.join(task.finals)}.\n"
            f"Notes: {named}.\n\n{queries}")


def scored(task: ExcelTask, reply: str, hive: sqlite3.Connection) -> excel_eval.ExcelScore:
    return excel_eval.score(task, reply, hive, excel_eval.reference_rows(hive, task))


def test_there_are_78_tasks_39_on_each_split_each_covering_everything() -> None:
    assert len(BY_ID) == len(TASKS) == 78
    assert Counter(task.split for task in TASKS) == {"dev": 39, "held_out": 39}
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
    header, replies = excel_eval.read_answers(excel_eval.template("held_out"))
    assert header["arm"] == "<A0 or C>"
    assert sorted(replies) == sorted(task.id for task in TASKS if task.split == "held_out")


def test_the_manual_rounds_workbooks_are_written(tmp_path: Path) -> None:
    written = excel_eval.write_workbooks("dev", tmp_path)
    assert [path.name for path in written] == [f"x{n:02d}.xlsx" for n in (
        *range(1, 21), *range(41, 46), *range(51, 59), 67, 68, 71, 72, 75, 76)]


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
