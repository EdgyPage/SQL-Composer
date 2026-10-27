"""The Copilot evaluation's tasks and scorer (Toolbox 7.2, ticket 12).

Every task's reference answer passes; a wrong answer of each kind fails on the check meant to
catch it; and an answers file made from the template reads back as it was written.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import copilot_eval
import pytest
from copilot_eval_tasks import BY_ID, OBJECTIVES, TASKS, Task


def fenced(code: str) -> str:
    return f"Here it is:\n\n```python\n{code}```\n"


def test_three_tasks_for_each_objective_two_to_tune_on_and_one_held_out() -> None:
    assert len(BY_ID) == len(TASKS) == 30
    assert Counter(task.split for task in TASKS) == {"dev": 20, "held_out": 10}
    for objective in OBJECTIVES:
        splits = sorted(task.split for task in TASKS if task.objective == objective)
        assert splits == ["dev", "dev", "held_out"], objective
    assert sum(task.trap for task in TASKS) == 6


@pytest.fixture(scope="module")
def references() -> list[copilot_eval.Score]:
    return copilot_eval.scored({task.id: fenced(task.reference) for task in TASKS})


def test_every_reference_answer_passes(references: list[copilot_eval.Score]) -> None:
    failed = [(one.task, one.note) for one in references if not one.passed]
    assert failed == []
    assert not any(one.star or one.unrun or one.needless for one in references)


T07 = BY_ID["T07"].reference

# A wrong answer of each kind, the task it answers, and the check it must fail on.
CONTROLS = [
    pytest.param("T07", "No code, just words.", "found", id="no_code"),
    pytest.param("T07", fenced("s = statement(SELECT(job_runs.run_id)"), "parses",
                 id="not_python"),
    pytest.param("T07", fenced(T07.replace("SELECT, WHERE", "SELECT, WHERE, select_columns")),
                 "invented", id="an_invented_name"),
    pytest.param("T01", fenced(BY_ID["T01"].reference.replace(
        "rows = run_query(s, query)", "rows = run_query(s, send=query)")), "invented",
                 id="send_as_before_7_0"),
    pytest.param("T07", fenced(T07.replace(
        'between(job_runs.dt, "2026-09-23", "2026-09-24"), ', "")), "builds",
                 id="no_partition_bound"),
    pytest.param("T07", fenced(T07.replace('equals(job_runs.status, "FAILED")',
                                           'job_runs.status == "FAILED"')), "builds",
                 id="python_equals"),
    pytest.param("T26", fenced(BY_ID["T26"].reference.replace("    LIMIT(3),\n", "")),
                 "builds", id="order_by_without_limit"),
    pytest.param("T07", fenced(T07.replace("FROM(job_runs)",
                                           "FROM(job_runs, reads_all_partitions=True)")),
                 "needless", id="an_opt_out_not_needed"),
    pytest.param("T07", fenced(T07.replace('"FAILED"', '"SUCCESS"')), "correct",
                 id="other_rows"),
    pytest.param("T07", fenced("import os\n" + T07), "builds", id="an_import_not_allowed"),
    pytest.param("T04", fenced(BY_ID["T04"].reference.replace('"job_id", "dt"]', '"job_id"]')),
                 "correct", id="another_key"),
    pytest.param("T16", fenced(BY_ID["T16"].reference.replace("INSERT_OVERWRITE",
                                                              "INSERT_INTO")),
                 "correct", id="adds_where_it_should_replace"),
    pytest.param("T05", fenced(
        "from sqlglot_composer import check_key\nfrom references.ops__jobs import jobs\n"
        "from warehouse import query\n\nv = check_key(jobs, query=query)\n"),
                 "correct", id="checks_another_tables_key"),
    pytest.param("T23", fenced(
        "from sqlglot_composer import FROM, SELECT, compare_hive, statement, to_hive\n"
        "from references.ops__jobs import jobs\n\n"
        "s0 = statement(SELECT(jobs.job_id, jobs.job_name), FROM(jobs))\n"
        "v = compare_hive(s0, to_hive(s0))\n"), "correct", id="compares_it_with_itself"),
    pytest.param("T07", fenced("import typing\ntyping.sys.modules\n" + T07), "builds",
                 id="a_module_reached_through_an_allowed_one"),
    pytest.param("T07", fenced("import pandas as pd\npd.read_csv('rows.csv')\n" + T07),
                 "builds", id="a_pandas_reader"),
]


@pytest.fixture(scope="module")
def controls() -> list[copilot_eval.Score]:
    return copilot_eval.scored_pairs([param.values[:2] for param in CONTROLS])


@pytest.mark.parametrize(("task", "reply", "check"), CONTROLS)
def test_a_wrong_answer_fails_on_the_check_meant_to_catch_it(
        controls: list[copilot_eval.Score], task: str, reply: str, check: str) -> None:
    result = next(one for one, param in zip(controls, CONTROLS) if param.values[1] == reply)
    assert not result.passed, result
    if check in ("invented", "needless"):
        assert getattr(result, check), result
    else:
        assert not getattr(result, check), result
        earlier = copilot_eval.CHECKS[:copilot_eval.CHECKS.index(check)]
        assert all(getattr(result, one) for one in earlier), result


def test_a_star_import_fails_though_its_statement_is_right() -> None:
    reply = fenced("from sqlglot_composer import *\n" + T07.split("\n", 1)[1])
    [result] = copilot_eval.scored({"T07": reply})
    assert result.star and result.correct and not result.passed


def test_an_answer_that_doesnt_run_what_was_asked_fails() -> None:
    reply = fenced(BY_ID["T01"].reference.replace("rows = run_query(s, query)\n", ""))
    [result] = copilot_eval.scored({"T01": reply})
    assert result.unrun and result.correct and not result.passed


def test_while_answers_run_nothing_is_written_outside_their_folder(tmp_path: Path) -> None:
    inside, outside = tmp_path / "inside", tmp_path / "outside.txt"
    inside.mkdir()
    with copilot_eval.answers_kept_in(inside):
        (inside / "fine.txt").write_text("kept", encoding="utf-8")
        with pytest.raises(PermissionError, match="may not write"):
            outside.write_text("refused", encoding="utf-8")
    outside.write_text("written once the answers have run", encoding="utf-8")
    assert (inside / "fine.txt").read_text(encoding="utf-8") == "kept"


def test_the_template_reads_back_with_a_heading_and_no_answer_for_each_task() -> None:
    header, replies = copilot_eval.read_answers(copilot_eval.template("held_out"))
    assert set(header) == {"date", "arm", "model", "files"}
    assert list(replies) == [task.id for task in TASKS if task.split == "held_out"]
    assert all(copilot_eval.answer_code(reply) is None for reply in replies.values())


def test_the_last_python_block_of_a_reply_is_its_answer() -> None:
    reply = "First:\n```python\na = 1\n```\nThen:\n```\nb = 2\n```\nAnd text.\n```text\nc\n```"
    assert copilot_eval.answer_code(reply) == "b = 2\n"


@pytest.mark.parametrize("task", TASKS, ids=lambda task: task.id)
def test_a_prompt_gives_the_context_and_says_what_to_assign(task: Task) -> None:
    text = copilot_eval.prompt(task)
    assert task.request in text
    assert copilot_eval.CONTRACT[copilot_eval.GIVES[task.kind]] in text
    for name in task.tables:
        assert f"from references.ops__{name} import {name}" in text


def test_a_result_row_names_the_run_and_each_check(references: list[copilot_eval.Score]
                                                   ) -> None:
    row = copilot_eval.results_row({"date": "2026-10-27", "files": "abc", "model": "haiku",
                                    "arm": "C"}, "dev", references)
    assert row.startswith("| 2026-10-27 | abc | haiku | C | dev | 100 | 100 | 100 |")


def test_the_baseline_shares_the_readmes_opening_within_the_limit() -> None:
    text = copilot_eval.baseline_text()
    assert len(text) <= copilot_eval.LIMIT
    assert text.startswith("# sqlglot Composer")
    assert copilot_eval.README_TEMPLATE.read_text(encoding="utf-8").startswith(text)


def test_a_proxy_message_shares_the_arms_text_then_asks_each_task() -> None:
    tasks = [task for task in TASKS if task.split == "dev"]
    alone = copilot_eval.proxy_message("A0", tasks)
    shared = copilot_eval.proxy_message("A1", tasks)
    assert "pasted this as their first message" not in alone
    assert copilot_eval.baseline_text() in shared
    assert all(f"## {task.id}\n\n{copilot_eval.prompt(task)}" in alone for task in tasks)


def test_arm_c_takes_the_tasks_of_one_objective() -> None:
    with pytest.raises(ValueError, match="one objective"):
        copilot_eval.proxy_message("C", [BY_ID["T01"], BY_ID["T07"]])
