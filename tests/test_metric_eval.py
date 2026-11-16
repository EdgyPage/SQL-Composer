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

import eval_runs
import metric_eval
import pytest
from metric_eval_tasks import BY_ID, TASKS, MetricTask, Required, request


def test_there_are_twenty_eight_tasks_fifteen_dev_and_thirteen_held_out() -> None:
    assert [task.id for task in TASKS] == [f"M{number:02}" for number in range(1, 29)]
    assert sorted(task.split for task in TASKS) == ["dev"] * 15 + ["held_out"] * 13


def test_the_six_newest_held_out_tasks_vary_and_two_ask_for_missing_data() -> None:
    newest = [BY_ID[f"M{number}"] for number in range(18, 24)]
    assert {task.split for task in newest} == {"held_out"}
    assert len([task for task in newest if task.missing]) >= 2
    assert any(task.muddled for task in newest) and any(task.sample_rows for task in newest)


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


REFUTED = "the refuting evidence named"

# A request for each premise task built on what the user said, with no word of what refutes it.
TRUSTING = {
    "M24": request("job failure rate", ("failure_rate_pct", (
        "the share of a job's finished runs that failed, as a percent.",
        "failure_rate_pct = 100 x failed runs / finished runs",
        "failed runs: rows of ops.job_runs whose status is FAILED or NULL, a NULL being a run "
        "that crashed; finished runs: rows whose status is SUCCESS, FAILED or NULL.",
        "job (job_id) with at least one finished run.",
        "every day ops.job_runs holds, as one total.",
        "TEST runs.",
        "a job whose runs are all TEST has no row.",
        "a run with status NULL counts as failed.",
        "none. Not rounded.",
    ))),
    "M25": request("jobs per owner", ("owned_jobs", (
        "how many jobs an owner looks after.",
        "owned_jobs = count of the owner's rows in ops.job_owners",
        "owner and job_id of ops.job_owners, a row per job.",
        "owner (ops.job_owners.owner) who owns at least one job.",
        "every day ops.job_owners holds.",
        "rows whose owner is NULL (nobody).",
        "a job counts once for its owner.",
        "an owner of two jobs shows two.",
        "none.",
    ))),
    "M26": request("runs per job", ("run_count", (
        "how many runs a job has had.",
        "run_count = count of the job's rows in ops.job_events",
        "runs: rows of ops.job_events, a row per run.",
        "job (job_id) with at least one run.",
        "every day ops.job_events holds, as one total.",
        "TEST runs.",
        "a job with no rows has no row.",
        "a job with three rows shows three.",
        "none.",
    ))),
    "M27": request("cost per job location", ("location_cost_cents", (
        "the billed cost of the jobs at each job location, in cents.",
        "location_cost_cents = sum of cost_cents matched to the location on region",
        "cost_cents of ops.region_costs, matched to ops.jobs on region, every region added "
        "up.",
        "location (ops.jobs.region) with at least one billed cost.",
        "every day ops.region_costs holds.",
        "costs whose cost_cents is NULL, not billed yet.",
        "a job billed in its region adds its cost to the location; job_id is not needed.",
        "job 1, at LON, takes the LON costs.",
        "none.",
    ))),
}


@pytest.mark.parametrize("task_id", sorted(TRUSTING))
def test_a_request_built_on_the_users_false_premise_fails(task_id: str) -> None:
    result = metric_eval.score_request(BY_ID[task_id], TRUSTING[task_id])
    assert REFUTED in result.essential_unmet and not result.passed
    assert any(unmet.startswith("the wrong reading kept out of")
               for unmet in result.essential_unmet)


# What refutes each premise, said in other plain words a request might use. M27's last two are
# from the baseline's own requests (ticket 12): arm A0's and arm C's held-out replies.
PARAPHRASED = {
    "M24": ("a NULL status means the run has no status yet",
            "a run that hasn't finished is left out"),
    "M25": ("the table keeps a history of owners by date",
            "ops.job_owners holds one row per job for each day"),
    "M26": ("ops.job_events has several rows for each run: a start, a finish, a retry",
            "it holds a row per event, not a row per run"),
    "M27": ("the two tables use different codes for a region",
            "the region codes disagree",
            "the definitions do not say whether eu and us name the same places as LON and NYC"),
}


@pytest.mark.parametrize(("task_id", "words"),
                         [(task, words) for task, all_words in PARAPHRASED.items()
                          for words in all_words])
def test_the_refuting_evidence_reads_in_other_plain_words(task_id: str, words: str) -> None:
    evidence = next(one for one in BY_ID[task_id].required if one.what == REFUTED)
    assert metric_eval.meets(words, evidence)


@pytest.mark.parametrize(("task_id", "rejected"), [
    ("M24", ("whose status is SUCCESS or FAILED.",
             "whose status is SUCCESS or FAILED; a NULL is never a crash.")),
    ("M26", ("a row per run, whose status is not TEST.",
             "a row per run, whose status is not TEST, not from ops.job_events, which has a "
             "row per event.")),
    ("M27", ("matched to its job by job_id,",
             "matched to its job by job_id, not on the region,")),
])
def test_a_request_may_name_the_reading_it_rejects(task_id: str,
                                                   rejected: tuple[str, str]) -> None:
    task = BY_ID[task_id]
    result = metric_eval.score_request(task, task.example.replace(*rejected))
    assert result.passed, metric_eval.score_line(result)


@pytest.mark.parametrize(("task_id", "trusted"), [
    ("M24", ("rows of ops.job_runs whose status is FAILED;",
             "rows of ops.job_runs whose status is FAILED or status NULL;")),
    ("M26", ("runs: rows of ops.job_runs, a row per run,",
             "runs: the number of rows in ops.job_events for the job,")),
    ("M27", ("matched to its job by job_id,", "matched by region to the job,")),
])
def test_the_wrong_reading_in_other_words_is_still_caught(task_id: str,
                                                          trusted: tuple[str, str]) -> None:
    task = BY_ID[task_id]
    result = metric_eval.score_request(task, task.example.replace(*trusted))
    assert any(unmet.startswith("the wrong reading kept out of")
               for unmet in result.essential_unmet), metric_eval.score_line(result)


def _quiet(task_id: str) -> str:
    """A premise task's example request with its part 9 saying nothing of the premise."""
    return re.sub(r"9\. Open questions:[^\n]*", "9. Open questions: none.",
                  BY_ID[task_id].example)


# What Copilot says to the user in a turn before its request, pushing back on the premise.
PUSHBACK = {
    "M26": "ops.job_events has several rows per run, by its event_type (start, finish, retry, "
           "fail); ops.job_runs has one row per run. Count from ops.job_runs?",
    "M28": "Your column definitions call ops.region_costs.dt a load date, which may not be the "
           "day the job ran. Which is it?",
}


@pytest.mark.parametrize("task_id", sorted(PUSHBACK))
def test_pushing_back_in_the_conversation_names_what_refutes_the_premise(task_id: str) -> None:
    task, quiet = BY_ID[task_id], _quiet(task_id)
    assert not metric_eval.score_request(task, quiet).passed
    reply = PUSHBACK[task_id] + "\n\nCopilot:\n\n" + quiet
    result = metric_eval.score_request(task, reply)
    assert result.passed, metric_eval.score_line(result)


def test_pushing_back_and_then_building_on_the_premise_still_fails() -> None:
    reply = ("Your column definitions say status is NULL while a run is still running.\n\n"
             + TRUSTING["M24"])
    result = metric_eval.score_request(BY_ID["M24"], reply)
    assert REFUTED not in result.essential_unmet and not result.passed


def test_a_round_is_scored_on_all_copilot_said_with_the_request_last(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _run(["start", "C", "--round", "r1", "--split", "dev", "--model", "haiku", "--only",
          "M26"], tmp_path, capsys)
    folder = _folder(tmp_path, "r1", "M26")
    _write(folder, "turn-01-copilot.md", PUSHBACK["M26"])
    _write(folder, "turn-01-user.md", "Yes, count from ops.job_runs.")
    _write(folder, "turn-02-copilot.md", "Here it is.\n\n" + _quiet("M26"))
    _run(["next", str(folder)], tmp_path, capsys)
    out = _run(["score", "r1", "C", "--split", "dev", "--model", "haiku", "--only", "M26"],
               tmp_path, capsys)
    assert "M26  pass" in out


def test_m28_keeps_the_users_reading_and_records_the_conflict_with_the_definitions() -> None:
    task = BY_ID["M28"]
    unrecorded = re.sub(r"9\. Open questions:[^\n]*", "9. Open questions: none.", task.example)
    unmet = metric_eval.score_request(task, unrecorded).essential_unmet
    assert "the conflict recorded" in unmet
    overruled = task.example.replace(
        "its dt taken as the day the job ran, as you said",
        "its dt a load date, matched to the run on the day before it")
    result = metric_eval.score_request(task, overruled)
    assert "the user's reading kept" in result.essential_unmet and not result.passed


def test_five_tasks_state_a_premise_their_definitions_or_rows_refute() -> None:
    premised = [task for task in TASKS if task.premise]
    assert [task.id for task in premised] == ["M24", "M25", "M26", "M27", "M28"]
    assert [task.split for task in premised] == ["dev"] * 3 + ["held_out"] * 2
    assert BY_ID["M27"].sample_rows


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


def test_a_replys_key_is_the_text_its_task_loads_whatever_the_files_version(
        monkeypatch: pytest.MonkeyPatch) -> None:
    def key(task: str, arm: str) -> eval_runs.Key:
        return metric_eval.memo_key(task, "a reply", arm=arm, model="haiku")
    assert key("M05", "C").files_version == eval_runs.NO_FILES_VERSION
    assert key("M01", "C").loaded_text_hash != key("M01", "A0").loaded_text_hash
    assert key("M01", "C").task_text_hash != key("M02", "C").task_text_hash
    before = key("M01", "C")
    monkeypatch.setattr(metric_eval, "COLUMN_DEFINITIONS", "ops.jobs\n  job_id - job id\n")
    after = key("M01", "C")
    assert (after.task_text_hash, after.loaded_text_hash) != (
        before.task_text_hash, before.loaded_text_hash)


def _run(argv: list[str], local: Path, capsys: pytest.CaptureFixture[str]) -> str:
    """Run a command with the test's local folder, and give what it printed."""
    capsys.readouterr()
    assert metric_eval.main([*argv, "--local", str(local)]) == 0
    return capsys.readouterr().out


def _folder(local: Path, round_name: str, task: str) -> Path:
    return local / "metric" / round_name / task


def _write(folder: Path, name: str, text: str) -> None:
    (folder / name).write_text(text, encoding="utf-8")


def test_start_plans_the_round_and_names_what_the_session_spawns(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = _run(["start", "C", "--round", "r1", "--split", "dev", "--model", "haiku"],
               tmp_path, capsys)
    dev = [task.id for task in TASKS if task.split == "dev"]
    folder = _folder(tmp_path, "r1", "M01")
    assert sorted(path.name for path in folder.iterdir()) == [
        "conversation.json", "copilot.md", "user.md"]
    assert (folder / "user.md").read_text(encoding="utf-8") == (
        metric_eval.user_message(BY_ID["M01"]) + "\n\n" + eval_runs.cap_text("metric") + "\n")
    assert f"Ask {len(dev)} of {len(dev)}" in out
    spawn = [line for line in out.splitlines() if line.startswith("M01: spawn")]
    assert len(spawn) == 1
    assert "metric-proxy" in spawn[0] and "haiku" in spawn[0]
    assert "copilot.md" in spawn[0] and "turn-01-copilot.md" in spawn[0]


def test_a_conversation_goes_one_agent_per_role_until_a_request(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _run(["start", "C", "--round", "r1", "--split", "dev", "--model", "haiku"], tmp_path,
         capsys)
    folder = _folder(tmp_path, "r1", "M01")
    again = _run(["next", str(folder)], tmp_path, capsys)
    assert "spawn metric-proxy" in again and "turn-01-copilot.md" in again
    _write(folder, "turn-01-copilot.md", "Does a retried run count once or twice?")
    out = _run(["next", str(folder)], tmp_path, capsys)
    assert "spawn metric-proxy" in out and "user.md" in out
    assert "turn-01-copilot.md" in out and "turn-01-user.md" in out
    _write(folder, "turn-01-user.md", "Once.")
    out = _run(["next", str(folder)], tmp_path, capsys)
    assert "SendMessage" in out and "spawn" not in out
    assert "turn-01-user.md" in out and "turn-02-copilot.md" in out
    _write(folder, "turn-02-copilot.md", "Thanks.\n\n" + REQUEST)
    out = _run(["next", str(folder)], tmp_path, capsys)
    assert "ended: request in turn 2" in out and "usage" in out
    assert (folder / "request.md").read_text(encoding="utf-8") == REQUEST
    assert (folder / "transcript.md").exists()
    assert _run(["next", str(folder)], tmp_path, capsys).startswith("M01: ended")


def test_a_conversation_ends_at_the_turn_cap(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _run(["start", "C", "--round", "r1", "--split", "dev", "--model", "haiku"], tmp_path,
         capsys)
    folder = _folder(tmp_path, "r1", "M01")
    cap = eval_runs.CAPS["metric"].turns
    for turn in range(1, cap):
        _write(folder, f"turn-{turn:02}-copilot.md", "Another question?")
        _write(folder, f"turn-{turn:02}-user.md", "An answer.")
    _write(folder, f"turn-{cap:02}-copilot.md", "One more question?")
    out = _run(["next", str(folder)], tmp_path, capsys)
    assert f"ended: turn cap, {cap} turns" in out
    assert (folder / "request.md").read_text(encoding="utf-8") == ""


def test_the_baseline_has_one_agent_and_ends_after_its_first_turn(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _run(["start", "A0", "--round", "b1", "--split", "dev", "--model", "haiku"], tmp_path,
         capsys)
    folder = _folder(tmp_path, "b1", "M02")
    _write(folder, "turn-01-copilot.md", "Here it is.\n\n" + BY_ID["M02"].example)
    assert "ended: request in turn 1" in _run(["next", str(folder)], tmp_path, capsys)


def test_each_agents_usage_is_recorded_once_per_conversation(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _run(["start", "C", "--round", "r1", "--split", "dev", "--model", "haiku"], tmp_path,
         capsys)
    folder = _folder(tmp_path, "r1", "M01")
    _write(folder, "turn-01-copilot.md", REQUEST)
    _run(["next", str(folder)], tmp_path, capsys)
    _run(["usage", str(folder), "--role", "copilot", "--tokens", "30000", "--seconds", "40",
          "--commit", "abc1234"], tmp_path, capsys)
    _run(["usage", str(folder), "--role", "user", "--tokens", "20000", "--seconds", "30"],
         tmp_path, capsys)
    rows = eval_runs.read_ledger(tmp_path)
    assert [(row.pipeline, row.round, row.task, row.arm, row.model, row.role, row.tokens)
            for row in rows] == [
        ("metric", "r1", "M01", "C", "haiku", "copilot", "30000"),
        ("metric", "r1", "M01", "C", "haiku", "user", "20000")]
    assert rows[0].result == "request in turn 1" and rows[0].commit == "abc1234"


def test_a_scored_round_is_recorded_and_kept_in_the_memo(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _run(["start", "C", "--round", "r1", "--split", "dev", "--model", "haiku"], tmp_path,
         capsys)
    for task, written in (("M01", BY_ID["M01"].example), ("M02", "No request.")):
        _write(_folder(tmp_path, "r1", task), "request.md", written)
    out = _run(["score", "r1", "C", "--split", "dev", "--model", "haiku"], tmp_path, capsys)
    assert "M01  pass" in out and "M02  fail" in out and "M03  no reply" in out
    row = (tmp_path / "metric" / "results.md").read_text(encoding="utf-8").splitlines()[-1]
    assert row.startswith("| ") and "| haiku | C | dev | 50 | 50 |" in row
    assert "M01:pass M02:fail" in row
    assert sorted(path.name[:12] for path in (tmp_path / "memo").iterdir()) == [
        "M01-C-haiku-", "M02-C-haiku-"]
    plan = _run(["plan", "C", "--split", "dev", "--model", "haiku"], tmp_path, capsys)
    assert "M01: from the memo" in plan and "M03: ask: no reply kept" in plan
    later = _run(["score", "r2", "C", "--split", "dev", "--model", "haiku"], tmp_path, capsys)
    assert "M01  pass" in later and "2 from the memo" in later


def test_a_round_name_outside_the_local_folder_is_refused(tmp_path: Path) -> None:
    with pytest.raises(SystemExit):
        metric_eval.main(["start", "C", "--round", "../../out", "--split", "dev",
                          "--model", "haiku", "--local", str(tmp_path)])


def test_only_the_tasks_named_are_asked(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    out = _run(["start", "C", "--round", "r1", "--split", "dev", "--model", "haiku",
                "--only", "M01"], tmp_path, capsys)
    assert "Ask 1 of 1" in out
    assert sorted(path.name for path in (tmp_path / "metric" / "r1").iterdir()) == ["M01"]


# --- The caps and the ladder (evaluation system, ticket 07) -----------------------------------


def test_the_turn_cap_is_the_metric_caps_in_the_one_table() -> None:
    assert not hasattr(metric_eval, "TURN_CAP")
    assert eval_runs.CAPS["metric"].turns == 12


def test_start_writes_the_caps_into_each_agents_first_message_and_not_into_the_key(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _run(["start", "C", "--round", "r1", "--split", "dev", "--model", "haiku",
          "--only", "M01"], tmp_path, capsys)
    folder = _folder(tmp_path, "r1", "M01")
    for name in ("copilot.md", "user.md"):
        assert eval_runs.cap_text("metric") in (folder / name).read_text(encoding="utf-8")
    assert eval_runs.cap_text("metric") not in metric_eval.user_message(BY_ID["M01"])


def test_a_turn_longer_than_the_reply_cap_or_a_turn_past_the_turn_cap_is_flagged_in_the_score(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    _run(["start", "C", "--round", "r1", "--split", "dev", "--model", "haiku",
          "--only", "M01"], tmp_path, capsys)
    folder = _folder(tmp_path, "r1", "M01")
    caps = eval_runs.CAPS["metric"]
    for turn in range(1, caps.turns + 2):
        _write(folder, f"turn-{turn:02}-copilot.md", "A question?")
        _write(folder, f"turn-{turn:02}-user.md", "x" * (caps.reply + 1) if turn == 1 else "ok")
    _write(folder, "request.md", REQUEST)
    out = _run(["score", "r1", "C", "--split", "dev", "--model", "haiku", "--only", "M01"],
               tmp_path, capsys)
    assert "OVER CAP" in out and "turn-01-user.md" in out
    assert f"{caps.turns + 1} turns of Copilot's, cap {caps.turns}" in out


def test_the_metric_plan_asks_no_task_whose_key_is_unchanged_and_proposes_a_rung_otherwise(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    key = metric_eval.memo_key("M01", REQUEST, arm="C", model="haiku")
    eval_runs.write_kept(eval_runs.Kept(key, "2026-11-14", "M01  pass", REQUEST),
                         tmp_path / "memo")
    out = _run(["plan", "C", "--split", "dev", "--only", "M01", "M02"], tmp_path, capsys)
    assert "M01: from the memo" in out and "(haiku passed), not asked again" in out
    assert "M02: ask on haiku: no reply kept" in out and "Rung haiku: M02" in out
    out = _run(["plan", "C", "--split", "dev", "--only", "M01", "--model", "haiku"], tmp_path,
               capsys)
    assert "M01: from the memo" in out and "Ask 0 of 1" in out
    with pytest.raises(SystemExit, match="each rung"):
        metric_eval.main(["start", "C", "--round", "r9", "--split", "dev", "--model",
                          "ladder", "--local", str(tmp_path)])
