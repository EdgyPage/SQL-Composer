"""The code path scored on every Excel task (Toolbox 8.9, ticket 14; ADR 0016: "Both paths,
equal").

The Copilot path is scored by `tools/excel_eval.py` on its 124 tasks; the code path is scored
by the same scorer on the same tasks, and every miss is a bug. The code path's answer is what
`project.convert` keeps of a workbook, written as file 15's Output: the map, then a block per
final (`reply_of`). Ticket 04's tests score the formula tasks and ticket 05's the query and
total tasks; this scores the pivot tasks, X85 to X124, and holds that the three together are
every task.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import closing

import pytest
from test_workbook_hive import FORMULA_TASKS, reply_of
from test_workbook_power_query import QUERY_TASKS

import excel_eval
import formula_workbook
from excel_eval_tasks import BY_ID, TASKS
from sqlglot_composer import workbook_hive
from sqlglot_composer.workbook_reader import read_workbook

PIVOT_TASKS = tuple(task.id for task in TASKS if task.workbook.pivots)
# Misses left for ticket 18, which leaves every grand total and subtotal out of a pivot's
# table (the user, 2026-11-19), so PC3's total-level finals go: X92's and X120's map says PC3's
# calculated item "added into this total", where file 20 and the tasks say "added into the
# total" (ticket 14's Answer). Each fails here until ticket 18 changes the tasks.
HELD = {"X92": "PC3's mark at a total level: ticket 18's", "X120": "the same as X92's"}


def _held(task_id: str) -> object:
    if task_id in HELD:
        return pytest.param(task_id, marks=pytest.mark.xfail(reason=HELD[task_id],
                                                             strict=True))
    return task_id


@pytest.fixture(scope="module")
def hive() -> Iterator[sqlite3.Connection]:
    with closing(excel_eval.stand_in_hive()) as connection:
        yield connection


@pytest.mark.parametrize("task_id", [_held(task_id) for task_id in PIVOT_TASKS])
def test_each_pivot_task_of_the_excel_evaluation_passes_its_scorer(
        task_id: str, hive: sqlite3.Connection) -> None:
    task = BY_ID[task_id]
    book = read_workbook(formula_workbook.saved(task.workbook))
    reply = reply_of(workbook_hive.workbook_hive(book), book)
    score = excel_eval.score(task, reply, hive, excel_eval.reference_rows(hive, task))
    assert score.passed, (score.note, score.unnamed, score.invented, reply)


def test_the_code_path_is_scored_on_every_excel_task() -> None:
    scored = [*FORMULA_TASKS, *QUERY_TASKS, *PIVOT_TASKS]
    assert sorted(scored) == sorted(task.id for task in TASKS)
    assert len(scored) == len(set(scored)) == 124
    assert len(PIVOT_TASKS) == 40
