"""The Metric request evaluation: Copilot file 19 measured by three proxies (Toolbox 8.7,
ticket 11).

A stand-in user with a vague goal and a secret answer key is grilled by a proxy loaded with
file 19, which writes a Metric request; a stand-in chatbot, given only the Example database's
column descriptions, writes the column's Hive from it. The column passes when it gives the
key's numbers on the Example database. The baseline is the same chatbot given only the vague
goal.
"""

from __future__ import annotations

from pathlib import Path

import eval_memo
import metric_eval
import pytest
from metric_eval_tasks import BY_ID, TASKS, MetricTask

import example_database


def fenced(hive: str) -> str:
    return f"Here is the column:\n\n```sql\n{hive}\n```\n"


def test_there_are_six_tasks_four_dev_and_two_held_out() -> None:
    assert [task.id for task in TASKS] == ["M01", "M02", "M03", "M04", "M05", "M06"]
    assert sorted(task.split for task in TASKS) == ["dev"] * 4 + ["held_out"] * 2


def test_at_least_two_tasks_muddle_their_columns_and_one_brings_sample_rows() -> None:
    muddled = [task for task in TASKS if task.muddled]
    assert len(muddled) >= 2
    assert {task.muddled for task in muddled} == {"one asked, two meant",
                                                 "two asked, one meant"}
    assert any(task.sample_rows for task in TASKS)


@pytest.mark.parametrize("task", TASKS, ids=lambda task: task.id)
def test_each_reference_gives_the_keys_numbers(task: MetricTask) -> None:
    found = example_database.query(task.reference)
    assert list(found.columns) == list(task.key_columns)
    rows = [tuple(metric_eval.compared(value) for value in row)
            for row in found.itertuples(index=False)]
    assert sorted(rows, key=repr) == sorted(
        (tuple(metric_eval.compared(value) for value in row) for row in task.key_rows),
        key=repr)


@pytest.mark.parametrize("task", TASKS, ids=lambda task: task.id)
def test_a_chatbot_reply_holding_the_reference_passes(task: MetricTask) -> None:
    result = metric_eval.score(task, fenced(task.reference))
    assert (result.found, result.runs, result.correct, result.passed) == (True,) * 4


@pytest.mark.parametrize("task", TASKS, ids=lambda task: task.id)
def test_the_naive_reading_of_the_vague_goal_fails(task: MetricTask) -> None:
    result = metric_eval.score(task, fenced(task.naive))
    assert result.runs and not result.correct and not result.passed


def test_the_columns_names_order_and_extra_columns_dont_matter() -> None:
    hive = """SELECT
  100.0 * SUM(CASE WHEN status = 'FAILED' THEN 1 ELSE 0 END) / COUNT(*) AS rate,
  COUNT(*) AS finished, job_id AS job
FROM ops.job_runs WHERE status IN ('SUCCESS', 'FAILED') GROUP BY job_id"""
    assert metric_eval.score(BY_ID["M01"], fenced(hive)).passed


def test_a_rate_rounded_to_two_places_passes_and_to_one_fails() -> None:
    two = BY_ID["M03"].reference.replace("100.0 * SUM", "ROUND(100.0 * SUM").replace(
        "COUNT(*)\n", "COUNT(*), 2)\n")
    one = two.replace(", 2)\n", ", 1)\n")
    assert metric_eval.score(BY_ID["M03"], fenced(two)).passed
    assert not metric_eval.score(BY_ID["M03"], fenced(one)).passed


def test_the_last_sql_block_is_the_answer() -> None:
    reply = fenced(BY_ID["M01"].naive) + "\nOr, better:\n\n" + fenced(BY_ID["M01"].reference)
    assert metric_eval.score(BY_ID["M01"], reply).passed


REQUEST = """# Metric request: job failure rate

## Column: failure_rate_pct
1. What it is: the share of a job's finished runs that failed, as a percent.
2. Formula: failure_rate_pct = 100 x failed runs / finished runs
3. Quantities: failed runs: rows of ops.job_runs whose status is FAILED; finished runs: rows
   whose status is SUCCESS or FAILED.
4. One row per: job (job_id).
5. Days counted: every day ops.job_runs holds, as one total.
6. Left out: TEST runs, and runs still going (status NULL). Select only finished runs from
   the table.
7. Edge cases: a job with no finished runs is left out, so nothing divides by 0.
8. Worked example: job 2 has SUCCESS, FAILED and NULL: 100 x 1 / 2 = 50.
9. Open questions: none.
"""


def test_a_request_in_plain_words_and_maths_holds_no_sql() -> None:
    assert not metric_eval.holds_sql(REQUEST)


@pytest.mark.parametrize("sql", [
    "```sql\nSELECT 1\n```",
    "Formula: SELECT job_id, COUNT(*) FROM ops.job_runs",
    "failed: CASE WHEN status = 'FAILED' THEN 1 END",
    "per job: GROUP BY job_id",
], ids=["block", "select", "case", "group"])
def test_a_request_with_sql_in_it_holds_sql(sql: str) -> None:
    assert metric_eval.holds_sql(REQUEST + sql)


def test_a_request_has_each_of_the_nine_parts_in_each_column() -> None:
    assert metric_eval.missing_parts(REQUEST) == []
    second = "\n## Column: failed_runs\n1. What it is: how many failed.\n2. Formula: count\n"
    assert metric_eval.missing_parts(REQUEST + second) == [
        "failed_runs: Quantities", "failed_runs: One row per", "failed_runs: Days counted",
        "failed_runs: Left out", "failed_runs: Edge cases", "failed_runs: Worked example",
        "failed_runs: Open questions"]
    assert metric_eval.missing_parts("Here is what I understood.") == ["a column section"]
    noted = REQUEST.replace("8. Worked example:", "8. Worked example (made up, as none given):")
    assert metric_eval.missing_parts(noted) == []


def test_file_19_holds_no_sql_and_its_finished_section_has_the_nine_parts() -> None:
    text = metric_eval.FILE_19.read_text(encoding="utf-8")
    assert not metric_eval.holds_sql(text)
    finished = metric_eval.request_in(text.split("A finished section")[1]).split("```")[0]
    assert finished.startswith("# Metric request: on-time delivery")
    assert metric_eval.missing_parts(finished) == []


def test_the_request_is_read_from_copilots_last_message() -> None:
    message = "Thanks, that settles it.\n\n" + REQUEST + "\nShall I change anything?"
    assert metric_eval.request_in(message).startswith("# Metric request: job failure rate")
    assert metric_eval.request_in("Does a retried run count once or twice?") == ""


def test_a_request_in_a_text_block_is_read_without_its_fence() -> None:
    message = f"Here it is:\n\n```text\n{REQUEST}```\n\nShall I change anything?"
    assert metric_eval.request_in(message) == REQUEST


def test_the_chatbot_knows_each_tables_columns_and_descriptions_but_no_rows() -> None:
    text = metric_eval.column_descriptions()
    for name in ("ops.jobs", "ops.job_runs", "ops.run_alerts", "ops.scheduler_runs",
                 "ops.job_events", "ops.job_owners", "ops.region_costs",
                 "ops.region_budgets", "ops.team_notes"):
        assert f"`{name}`" in text
    assert "status string: SUCCESS / FAILED / TEST, NULL while running" in text
    assert "partitioned by region, dt" in text and "Key job_id, region, dt" in text
    assert "nightly_load" not in text and "2026-09-23" not in text


@pytest.mark.parametrize("task", TASKS, ids=lambda task: task.id)
def test_only_the_stand_in_user_sees_the_answer_key(task: MetricTask) -> None:
    user = metric_eval.user_message(task)
    assert task.opening in user and task.answer_key in user
    copilot = metric_eval.copilot_message(task)
    assert metric_eval.FILE_19.read_text(encoding="utf-8") in copilot
    assert task.opening in copilot and task.answer_key not in copilot
    for request in (None, REQUEST):
        chatbot = metric_eval.chatbot_message(task, request)
        assert metric_eval.column_descriptions() in chatbot
        assert task.answer_key not in chatbot and task.reference not in chatbot


def test_the_baseline_chatbot_gets_the_vague_goal_and_the_other_the_request_alone() -> None:
    task = BY_ID["M03"]
    assert task.opening in metric_eval.chatbot_message(task)
    with_request = metric_eval.chatbot_message(task, REQUEST)
    assert REQUEST in with_request and task.opening not in with_request


def test_a_held_out_task_grilled_with_file_19_is_kept_by_the_files_version() -> None:
    def key(task: str, arm: str) -> eval_memo.Key:
        return metric_eval.memo_key(task, "a reply", arm=arm, model="haiku", files="abc")
    assert key("M05", "C").files_version == "abc"
    assert key("M05", "A0").files_version == eval_memo.NO_FILES_VERSION
    assert key("M01", "C").files_version == eval_memo.NO_FILES_VERSION
    assert key("M01", "C").loaded_text_hash != key("M01", "A0").loaded_text_hash
    assert key("M01", "C").task_text_hash != key("M02", "C").task_text_hash


def grilled(task: MetricTask, request: str = REQUEST) -> str:
    """An arm C answer: the Metric request file 19 wrote, then the chatbot's reply to it."""
    return f"### Metric request\n\n{request}\n### Chatbot\n\n{fenced(task.reference)}"


def test_in_arm_c_a_request_holding_sql_or_no_request_fails_the_right_column() -> None:
    task = BY_ID["M01"]
    assert metric_eval.score_reply(task, grilled(task), "C").passed
    with_sql = metric_eval.score_reply(task, grilled(task, REQUEST + "GROUP BY job_id\n"), "C")
    assert with_sql.correct and with_sql.sql_in_request and not with_sql.passed
    no_request = metric_eval.score_reply(task, grilled(task, "I'll ask the chatbot.\n"), "C")
    assert no_request.correct and no_request.request_missing and not no_request.passed
    assert metric_eval.score_reply(task, fenced(task.reference), "A0").passed


def test_a_task_folders_turns_give_the_transcript_request_and_chatbot_message(
        tmp_path: Path) -> None:
    folder = tmp_path / "M01"
    metric_eval.write_task_messages(BY_ID["M01"], "C", folder)
    assert (folder / "user.md").read_text(encoding="utf-8") == metric_eval.user_message(
        BY_ID["M01"])
    (folder / "turn-01-copilot.md").write_text("Does a retried run count once or twice?",
                                              encoding="utf-8")
    (folder / "turn-01-user.md").write_text("Once.", encoding="utf-8")
    (folder / "turn-02-copilot.md").write_text("Thanks.\n\n" + REQUEST, encoding="utf-8")
    metric_eval.write_chatbot_message(folder)
    assert (folder / "request.md").read_text(encoding="utf-8") == REQUEST
    assert (folder / "chatbot-message.md").read_text(encoding="utf-8") == (
        metric_eval.chatbot_message(BY_ID["M01"], REQUEST))
    transcript = (folder / "transcript.md").read_text(encoding="utf-8")
    assert transcript.index("Copilot:\n\nDoes a retried") < transcript.index("User:\n\nOnce.")


def test_a_baseline_task_folder_holds_the_chatbot_message_alone(tmp_path: Path) -> None:
    metric_eval.write_task_messages(BY_ID["M02"], "A0", tmp_path / "M02")
    assert sorted(path.name for path in (tmp_path / "M02").iterdir()) == ["chatbot-message.md"]


def test_a_scored_round_is_recorded_and_kept_in_the_memo(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    run = tmp_path / "run"
    for task in (BY_ID["M01"], BY_ID["M02"]):
        (run / task.id).mkdir(parents=True)
        (run / task.id / "request.md").write_text(REQUEST, encoding="utf-8")
        (run / task.id / "chatbot.md").write_text(fenced(task.reference), encoding="utf-8")
    (run / "M02" / "chatbot.md").write_text(fenced(BY_ID["M02"].naive), encoding="utf-8")
    answers = tmp_path / "answers.md"
    memo, record = tmp_path / "memo", tmp_path / "results.md"
    record.write_text("# results\n", encoding="utf-8")
    assert metric_eval.main(["answers", str(run), "--arm", "C", "--model", "haiku",
                             "--files", "abc1234", "--memo-files", "-",
                             "--into", str(answers)]) == 0
    assert metric_eval.main(["score", str(answers), "--split", "dev", "--memo", str(memo),
                             "--record", str(record)]) == 0
    row = record.read_text(encoding="utf-8").splitlines()[-1]
    assert row.startswith("| ") and "| abc1234 | haiku | C | dev | 50 |" in row
    assert "M01:pass M02:fail" in row
    assert sorted(path.name[:12] for path in memo.iterdir()) == ["M01-C-haiku-",
                                                                 "M02-C-haiku-"]
    capsys.readouterr()
    assert metric_eval.main(["plan", "C", "--split", "dev", "--model", "haiku",
                             "--memo", str(memo)]) == 0
    plan = capsys.readouterr().out
    assert "M01: from the memo" in plan and "M03: ask: no reply kept" in plan
    assert metric_eval.main(["messages", "C", "--split", "dev", "--model", "haiku",
                             "--memo", str(memo), "--into", str(tmp_path / "next")]) == 0
    assert capsys.readouterr().out.strip() == "Wrote the messages of M03, M04."
    assert sorted(path.name for path in (tmp_path / "next").iterdir()) == ["M03", "M04"]


def test_a_reply_with_no_sql_block_or_hive_that_wont_run_fails_and_says_why() -> None:
    nothing = metric_eval.score(BY_ID["M01"], "I'd need to know more about your tables.")
    assert (nothing.found, nothing.passed) == (False, False)
    broken = metric_eval.score(BY_ID["M01"], fenced("SELECT job_id FROM ops.no_such_table"))
    assert (broken.found, broken.runs, broken.passed) == (True, False, False)
    assert "no_such_table" in broken.note
