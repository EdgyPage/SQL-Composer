"""The Metric request evaluation: Copilot file 19 measured by two proxies and a requirements key
(Toolbox 8.7, tickets 11 and 17).

A stand-in user with a vague goal, the column definitions and a secret answer key is grilled by
a proxy loaded with file 19 and the definitions, which writes a Metric request. The request is
scored directly, by rules, for direction: every essential element of its task's requirements
key, more helpful elements than not, nothing invented, no number worked out, no SQL.
"""

from __future__ import annotations

import re
from pathlib import Path

import eval_memo
import metric_eval
import pytest
from metric_eval_tasks import BY_ID, TASKS, MetricTask, Required


def test_there_are_seventeen_tasks_twelve_dev_and_five_held_out() -> None:
    assert [task.id for task in TASKS] == [f"M{number:02}" for number in range(1, 18)]
    assert sorted(task.split for task in TASKS) == ["dev"] * 12 + ["held_out"] * 5


def test_the_tasks_muddle_columns_bring_rows_and_ask_for_what_the_data_cant_give() -> None:
    assert {task.muddled for task in TASKS if task.muddled} == {"one asked, two meant",
                                                                "two asked, one meant"}
    assert len([task for task in TASKS if task.sample_rows]) >= 3
    missing = [task for task in TASKS if task.missing]
    assert len(missing) >= 4
    assert {task.split for task in missing} == {"dev", "held_out"}


@pytest.mark.parametrize("task", TASKS, ids=lambda task: task.id)
def test_each_key_has_essential_and_helpful_elements(task: MetricTask) -> None:
    essential = [one.what for one in task.required if one.essential]
    assert "the grain and its conditions" in essential
    source = "the missing data named" if task.missing else "the quantities by their columns"
    assert source in essential
    assert any(not one.essential for one in task.required)


@pytest.mark.parametrize("task", TASKS, ids=lambda task: task.id)
def test_each_tasks_example_request_passes_with_every_element(task: MetricTask) -> None:
    result = metric_eval.score_request(task, task.example)
    assert result.passed, metric_eval.score_line(result)
    assert (result.essential_unmet, result.helpful_unmet, result.parts_missing) == ([], [], [])


def _without(request: str, required: Required) -> str:
    """A request with each of a requirement's patterns taken out of the text it reads."""
    if not required.part:
        for pattern in required.patterns:
            request = re.sub(pattern, "", request, flags=re.IGNORECASE)
        return request
    for _, body in metric_eval.sections(request):
        text = metric_eval.parts_of(body).get(required.part, "")
        stripped = text
        for pattern in required.patterns:
            stripped = re.sub(pattern, "", stripped, flags=re.IGNORECASE)
        request = request.replace(text, stripped)
    return request


@pytest.mark.parametrize("task", TASKS, ids=lambda task: task.id)
def test_each_element_taken_out_of_the_example_is_unmet(task: MetricTask) -> None:
    for required in task.required:
        if not required.absent:
            assert not metric_eval.meets(_without(task.example, required), required), (
                required.what)


@pytest.mark.parametrize("task", [task for task in TASKS if task.missing],
                         ids=lambda task: task.id)
def test_a_gap_neither_named_nor_fixed_fails(task: MetricTask) -> None:
    unnamed = re.sub(r"Missing data:[^\n]*", "", task.example)
    assert "the missing data named" in metric_eval.score_request(task, unnamed).essential_unmet
    unfixed = task.example.replace("Fix:", "And")
    assert "a fix suggested" in metric_eval.score_request(task, unfixed).essential_unmet


def test_a_request_mostly_right_passes_and_one_mostly_wrong_fails() -> None:
    task = BY_ID["M01"]
    rounded = task.example.replace("none. Not rounded.", "none.")
    one_short = metric_eval.score_request(task, rounded)
    assert one_short.passed and one_short.helpful_unmet == ["not rounded"]
    sparse = task.example
    for words in ("100 x ", "as a percent", "TEST runs; ", "every day ops.job_runs holds",
                  "counted once", "Not rounded.", "(status NULL)", "runs still going"):
        sparse = sparse.replace(words, "")
    result = metric_eval.score_request(task, sparse)
    assert result.holds_essential and not result.passed


def test_a_grain_without_its_condition_fails_whatever_else_it_holds() -> None:
    task = BY_ID["M01"]
    loose = task.example.replace("job (job_id) with at least one finished run.",
                                 "job (job_id).")
    result = metric_eval.score_request(task, loose)
    assert result.essential_unmet == ["the grain and its conditions"] and not result.passed


def test_an_invented_column_or_a_worked_number_always_fails() -> None:
    task = BY_ID["M06"]
    invented = task.example.replace("any severity,",
                                    "any severity, unless action_taken is set,")
    result = metric_eval.score_request(task, invented)
    assert result.invented == ["action_taken"] and not result.passed
    worked = task.example.replace("shows 0.", "shows 0. Job 1: 4 alerts / 3 runs = 1.33.")
    result = metric_eval.score_request(task, worked)
    assert result.worked == ["= 1.33."] and not result.passed


def test_a_fix_may_name_a_column_to_add_and_a_limit_is_no_worked_number() -> None:
    task = BY_ID["M14"]
    named = task.example.replace("add a raised-at time", "add a raised_at column")
    assert metric_eval.score_request(task, named).passed
    limits = "speed = slow if 20 <= average < 30; >= 30 very slow"
    assert metric_eval.worked_numbers(limits) == []


def test_an_invented_kind_of_alert_fails_m06() -> None:
    task = BY_ID["M06"]
    noisy = task.example.replace("alerts raised by finished runs /",
                                 "alerts closed with no action /")
    assert "no invented kind of alert" in metric_eval.score_request(task, noisy).essential_unmet
    fraction = task.example.replace("/ finished runs", "/ finished runs, a fraction")
    assert metric_eval.score_request(task, fraction).passed


def test_a_muddled_task_with_the_wrong_number_of_columns_fails() -> None:
    task = BY_ID["M02"]
    one_column = task.example.split("## Column: minutes")[0].replace(
        "rows of ops.job_runs,", "rows of ops.job_runs and their duration_mins,")
    result = metric_eval.score_request(task, one_column)
    assert result.essential_unmet == ["2 column sections"] and not result.passed


def test_sql_or_no_request_fails() -> None:
    task = BY_ID["M01"]
    assert not metric_eval.score_request(task, task.example + "GROUP BY job_id\n").passed
    nothing = metric_eval.score_request(task, "I'll ask the chatbot.")
    assert nothing.request_missing and not nothing.passed
    assert "no Metric request" in metric_eval.score_line(nothing)


REQUEST = BY_ID["M01"].example


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
        "failed_runs: Left out", "failed_runs: Edge cases", "failed_runs: How to check",
        "failed_runs: Open questions"]
    assert metric_eval.missing_parts("Here is what I understood.") == ["a column section"]
    noted = REQUEST.replace("8. How to check:", "8. How to check (on your rows):")
    assert metric_eval.missing_parts(noted) == []


def test_file_19_holds_no_sql_and_its_finished_request_works_out_no_number() -> None:
    text = metric_eval.FILE_19.read_text(encoding="utf-8")
    assert not metric_eval.holds_sql(text)
    finished = metric_eval.request_in(text.split("A finished request")[1])
    assert metric_eval.missing_parts(finished) == []
    assert metric_eval.worked_numbers(finished) == []
    assert metric_eval.request_form().startswith("# Metric request: <")


def test_the_request_is_read_from_copilots_last_message() -> None:
    message = "Thanks, that settles it.\n\n" + REQUEST + "\nShall I change anything?"
    assert metric_eval.request_in(message).startswith("# Metric request: job failure rate")
    assert metric_eval.request_in("Does a retried run count once or twice?") == ""


def test_a_request_in_a_text_block_is_read_without_its_fence() -> None:
    message = f"Here it is:\n\n```text\n{REQUEST}```\n\nShall I change anything?"
    assert metric_eval.request_in(message) == REQUEST


@pytest.mark.parametrize("task", TASKS, ids=lambda task: task.id)
def test_only_the_stand_in_user_sees_the_answer_key(task: MetricTask) -> None:
    user = metric_eval.user_message(task)
    assert task.opening in user and task.answer_key in user
    assert metric_eval.COLUMN_DEFINITIONS in user
    for copilot in (metric_eval.copilot_message(task), metric_eval.baseline_message(task)):
        assert task.opening in copilot and metric_eval.COLUMN_DEFINITIONS in copilot
        assert task.answer_key not in copilot and task.example not in copilot
    file_19 = metric_eval.FILE_19.read_text(encoding="utf-8")
    assert file_19 in metric_eval.copilot_message(task)
    assert file_19 not in metric_eval.baseline_message(task)
    assert metric_eval.request_form() in metric_eval.baseline_message(task)


def test_the_definitions_name_only_the_example_databases_columns() -> None:
    assert metric_eval.invented_names(metric_eval.COLUMN_DEFINITIONS) == []


def test_a_held_out_task_grilled_with_file_19_is_kept_by_the_files_version(
        monkeypatch: pytest.MonkeyPatch) -> None:
    def key(task: str, arm: str) -> eval_memo.Key:
        return metric_eval.memo_key(task, "a reply", arm=arm, model="haiku", files="abc")
    assert key("M05", "C").files_version == "abc"
    assert key("M05", "A0").files_version == eval_memo.NO_FILES_VERSION
    assert key("M01", "C").files_version == eval_memo.NO_FILES_VERSION
    assert key("M01", "C").loaded_text_hash != key("M01", "A0").loaded_text_hash
    assert key("M01", "C").task_text_hash != key("M02", "C").task_text_hash
    before = key("M01", "C")
    monkeypatch.setattr(metric_eval, "COLUMN_DEFINITIONS", "ops.jobs\n  job_id - job id\n")
    after = key("M01", "C")
    assert (after.task_text_hash, after.loaded_text_hash) != (
        before.task_text_hash, before.loaded_text_hash)


def test_a_task_folders_turns_give_the_transcript_and_request(tmp_path: Path) -> None:
    folder = tmp_path / "M01"
    metric_eval.write_task_messages(BY_ID["M01"], "C", folder)
    assert (folder / "user.md").read_text(encoding="utf-8") == metric_eval.user_message(
        BY_ID["M01"])
    (folder / "turn-01-copilot.md").write_text("Does a retried run count once or twice?",
                                              encoding="utf-8")
    (folder / "turn-01-user.md").write_text("Once.", encoding="utf-8")
    (folder / "turn-02-copilot.md").write_text("Thanks.\n\n" + REQUEST, encoding="utf-8")
    metric_eval.write_request(folder)
    assert (folder / "request.md").read_text(encoding="utf-8") == REQUEST
    transcript = (folder / "transcript.md").read_text(encoding="utf-8")
    assert transcript.index("Copilot:\n\nDoes a retried") < transcript.index("User:\n\nOnce.")


def test_a_baseline_task_folder_holds_copilots_message_alone(tmp_path: Path) -> None:
    metric_eval.write_task_messages(BY_ID["M02"], "A0", tmp_path / "M02")
    assert sorted(path.name for path in (tmp_path / "M02").iterdir()) == ["copilot.md"]


def test_a_scored_round_is_recorded_and_kept_in_the_memo(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    run = tmp_path / "run"
    for task, request in ((BY_ID["M01"], BY_ID["M01"].example), (BY_ID["M02"], "No request.")):
        (run / task.id).mkdir(parents=True)
        (run / task.id / "request.md").write_text(request, encoding="utf-8")
    answers = tmp_path / "answers.md"
    memo, record = tmp_path / "memo", tmp_path / "results.md"
    record.write_text("# results\n", encoding="utf-8")
    assert metric_eval.main(["answers", str(run), "--arm", "C", "--model", "haiku",
                             "--files", "abc1234", "--memo-files", "-",
                             "--into", str(answers)]) == 0
    assert metric_eval.main(["score", str(answers), "--split", "dev", "--memo", str(memo),
                             "--record", str(record)]) == 0
    row = record.read_text(encoding="utf-8").splitlines()[-1]
    assert row.startswith("| ") and "| abc1234 | haiku | C | dev | 50 | 50 |" in row
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
    asked = [task.id for task in TASKS if task.split == "dev"][2:]
    assert capsys.readouterr().out.strip() == f"Wrote the messages of {', '.join(asked)}."
    assert sorted(path.name for path in (tmp_path / "next").iterdir()) == asked
