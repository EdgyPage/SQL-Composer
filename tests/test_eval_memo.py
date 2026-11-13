"""The memo of the Copilot and Excel evaluations (Toolbox 8.7, ticket 02).

Each task's reply and score is kept in `.scratch/copilot-eval/memo/`, one plain file per key:
the task's id and text, the arm, the model, the hash of the text the arm loads, and, for a
held-out task in an arm that loads a Copilot file, the Copilot files' version. `plan` names the
tasks a round asks and why; `prompts`, `proxy` and `template` write only those; `score` scores
the kept replies with the new ones and says how many came from the memo.
"""

from __future__ import annotations

import functools
from collections.abc import Callable
from pathlib import Path

import copilot_eval
import eval_memo
import excel_eval
import pytest
from copilot_eval_tasks import BY_ID


def fenced(code: str) -> str:
    return f"Here it is:\n\n```python\n{code}```\n"


def a_key(task_text: str = "Count the failed runs.", loaded_text: str = "file 03",
          files: str = eval_memo.NO_FILES_VERSION) -> eval_memo.Key:
    return eval_memo.hashed_key("T07", task_text, "C", "haiku", loaded_text, files)


def key_of(task_text: str = "Count the failed runs.", loaded_text: str = "file 03",
           files: str = eval_memo.NO_FILES_VERSION) -> Callable[[str, str], eval_memo.Key]:
    """A tool's key for a task and its reply, its texts given."""
    def key(task_id: str, reply: str) -> eval_memo.Key:
        return eval_memo.hashed_key(task_id, task_text, "C", "haiku", loaded_text, files)
    return key


def test_a_kept_reply_reads_back_from_one_plain_file_per_key(tmp_path: Path) -> None:
    kept = eval_memo.Kept(a_key(), asked="2026-11-13", score="T07  pass  found",
                          reply="Here it is:\n\n```python\ns = 1\n```\n")
    path = eval_memo.write_kept(kept, tmp_path)
    assert path.parent == tmp_path and path.name.startswith("T07-C-haiku-")
    text = path.read_text(encoding="utf-8")
    assert "arm: C\n" in text and "score: T07  pass  found\n" in text
    assert text.endswith("```python\ns = 1\n```\n")
    assert eval_memo.read_kept("T07", "C", "haiku", tmp_path) == [kept]
    assert eval_memo.read_kept("T07", "C", "sonnet", tmp_path) == []


def keep(key: eval_memo.Key, folder: Path) -> None:
    eval_memo.write_kept(eval_memo.Kept(key, "2026-11-12", "T07  pass", "a reply"), folder)


def test_a_task_is_asked_until_a_reply_is_kept_then_taken_from_the_memo(tmp_path: Path) -> None:
    first = eval_memo.task_plan("T07", key_of(), held_out=False, fresh=False, folder=tmp_path)
    assert (first.reason, first.kept) == ("no reply kept", None)
    keep(a_key(), tmp_path)
    then = eval_memo.task_plan("T07", key_of(), held_out=False, fresh=False, folder=tmp_path)
    assert then.reason == "" and then.kept is not None and then.kept.reply == "a reply"


@pytest.mark.parametrize(("changed", "reason"), [
    ({"task_text": "Count the failed runs, by day."}, "its text changed"),
    ({"loaded_text": "file 03, changed"}, "the text arm C loads changed"),
    ({"files": "bbb"}, "held out, and the Copilot files changed since it was asked"),
])
def test_a_task_is_asked_again_when_what_it_was_asked_on_changed(
        tmp_path: Path, changed: dict[str, str], reason: str) -> None:
    keep(a_key(files="aaa"), tmp_path)
    now = {"task_text": "Count the failed runs.", "loaded_text": "file 03", "files": "aaa"}
    plan = eval_memo.task_plan("T07", key_of(**{**now, **changed}), held_out=True, fresh=False,
                             folder=tmp_path)
    assert (plan.reason, plan.kept) == (reason, None)


def test_fresh_asks_a_dev_task_again_but_not_a_held_out_task_on_the_same_files(
        tmp_path: Path) -> None:
    keep(a_key(), tmp_path)
    dev = eval_memo.task_plan("T07", key_of(), held_out=False, fresh=True, folder=tmp_path)
    held_out = eval_memo.task_plan("T07", key_of(), held_out=True, fresh=True, folder=tmp_path)
    assert (dev.reason, dev.kept) == ("--fresh", None)
    assert held_out.reason == "" and held_out.kept is not None


# --- The Copilot evaluation ------------------------------------------------------------------


def keep_copilot(task_id: str, arm: str, reply: str, folder: Path) -> None:
    """Keep a reply to a Copilot task on haiku, under the key it has now."""
    key = copilot_eval.memo_key(task_id, reply, arm, "haiku", eval_memo.files_version())
    eval_memo.write_kept(eval_memo.Kept(key, "2026-11-12", "", reply), folder)


def test_plan_and_proxy_name_only_the_copilot_tasks_to_ask(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    keep_copilot("T07", "C", fenced(BY_ID["T07"].reference), tmp_path)
    memo = ["--model", "haiku", "--memo", str(tmp_path)]
    round_of = ["--split", "dev", "--objective", "03"]
    assert copilot_eval.main(["plan", "C", *round_of, *memo]) == 0
    plan = capsys.readouterr().out
    assert "T07: from the memo, T07-C-haiku-" in plan
    assert "T08: ask: no reply kept" in plan
    assert copilot_eval.main(["proxy", "C", *round_of, *memo]) == 0
    message = capsys.readouterr().out
    assert "## T08\n" in message and "## T07\n" not in message
    assert copilot_eval.main(["prompts", "--arm", "C", *round_of, *memo]) == 0
    prompts = capsys.readouterr().out
    assert "## T08\n" in prompts and "## T07\n" not in prompts
    assert copilot_eval.main(["template", "--arm", "C", *round_of, *memo]) == 0
    _, replies = eval_memo.read_answers(capsys.readouterr().out, "T")
    assert list(replies) == ["T08"]


def test_a_round_with_every_reply_kept_asks_nothing(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    for task_id in ("T07", "T08"):
        keep_copilot(task_id, "C", fenced(BY_ID[task_id].reference), tmp_path)
    assert copilot_eval.main(["proxy", "C", "--split", "dev", "--objective", "03",
                              "--model", "haiku", "--memo", str(tmp_path)]) == 0
    assert capsys.readouterr().out.startswith("Nothing to ask")


ANSWERS_HEAD = "date: 2026-11-13\narm: C\nmodel: haiku\nfiles: abc1234\n"


def test_score_scores_the_kept_replies_with_the_new_ones_and_keeps_both(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    memo, results = tmp_path / "memo", tmp_path / "results.md"
    keep_copilot("T08", "C", fenced(BY_ID["T08"].reference), memo)
    answers = tmp_path / "answers.md"
    answers.write_text(f"{ANSWERS_HEAD}\n## T07\n\n{fenced(BY_ID['T07'].reference)}",
                       encoding="utf-8")
    assert copilot_eval.main(["score", str(answers), "--split", "dev", "--objective", "03",
                              "--memo", str(memo), "--record", str(results)]) == 0
    report = capsys.readouterr().out
    assert "T07  pass" in report and "T08  pass" in report
    assert "1 of 2 replies from the memo." in report
    assert results.read_text(encoding="utf-8").endswith(" | 03:100 | 1 |\n")
    [t07] = eval_memo.read_kept("T07", "C", "haiku", memo)
    assert t07.asked == "2026-11-13" and t07.score.startswith("T07  pass")
    [t08] = eval_memo.read_kept("T08", "C", "haiku", memo)
    assert t08.asked == "2026-11-12" and t08.score.startswith("T08  pass")


def test_score_refuses_an_answers_file_whose_header_gives_no_arm_or_model(
        tmp_path: Path) -> None:
    answers = tmp_path / "answers.md"
    answers.write_text(copilot_eval.template([BY_ID["T07"]]), encoding="utf-8")
    with pytest.raises(SystemExit, match="fill both in"):
        copilot_eval.main(["score", str(answers), "--memo", str(tmp_path)])


def test_a_held_out_reply_is_never_scored_against_files_it_wasnt_asked_on(
        tmp_path: Path) -> None:
    reply = fenced(BY_ID["T09"].reference)
    asked_on = copilot_eval.memo_key("T09", reply, "C", "haiku", files="aaa")
    eval_memo.write_kept(eval_memo.Kept(asked_on, "2026-11-12", "", reply), tmp_path)
    header = {"arm": "C", "model": "haiku", "memo_files": "bbb"}
    arms = sorted(copilot_eval.ARMS)
    other = eval_memo.round_replies(header, {}, ["T09"], copilot_eval.memo_key, arms, tmp_path)
    assert (other.replies, other.taken) == ({}, {})
    key_of = functools.partial(copilot_eval.memo_key, arm="C", model="haiku", files="bbb")
    plan = eval_memo.task_plan("T09", key_of, held_out=True, fresh=False, folder=tmp_path)
    assert plan.reason == "held out, and the Copilot files changed since it was asked"
    header["memo_files"] = "aaa"
    same = eval_memo.round_replies(header, {}, ["T09"], copilot_eval.memo_key, arms, tmp_path)
    assert list(same.taken) == ["T09"]
    dev = copilot_eval.memo_key("T07", "", "C", "haiku", files="aaa")
    baseline = copilot_eval.memo_key("T09", "", "A1", "haiku", files="aaa")
    assert asked_on.files_version == "aaa"
    assert dev.files_version == baseline.files_version == eval_memo.NO_FILES_VERSION


def test_a_new_held_out_reply_is_kept_by_the_files_version_its_header_names(
        tmp_path: Path) -> None:
    answers = tmp_path / "answers.md"
    reply = f"\n## T09\n\n{fenced(BY_ID['T09'].reference)}"
    answers.write_text(ANSWERS_HEAD + reply, encoding="utf-8")
    with pytest.raises(SystemExit, match="memo_files: <version>"):
        copilot_eval.main(["score", str(answers), "--memo", str(tmp_path)])
    answers.write_text(f"{ANSWERS_HEAD}memo_files: aaa\n{reply}", encoding="utf-8")
    assert copilot_eval.main(["score", str(answers), "--memo", str(tmp_path)]) == 0
    [kept] = eval_memo.read_kept("T09", "C", "haiku", tmp_path)
    assert kept.key.files_version == "aaa" and kept.score.startswith("T09  pass")


def test_a_template_names_the_files_version_its_replies_are_asked_on(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert copilot_eval.main(["template", "--arm", "C", "--split", "held_out", "--objective",
                              "03", "--model", "haiku", "--memo", str(tmp_path)]) == 0
    header, replies = eval_memo.read_answers(capsys.readouterr().out, "T")
    assert header["memo_files"] == eval_memo.files_version()
    assert list(replies) == ["T09"]


def test_arm_r_loads_file_00_and_the_file_its_reply_names() -> None:
    task = BY_ID["T07"]
    file_00 = copilot_eval.shared_text("R", None)
    file_03 = copilot_eval.shared_text("C", "03")
    named = copilot_eval.loaded_text("R", task, "## T07\n\n03_build_a_statement.txt\n")
    assert named == f"{file_00}{file_03}"
    assert copilot_eval.loaded_text("R", task, "") == file_00
    assert copilot_eval.loaded_text("C", task, "anything") == file_03


# --- The Excel tasks -------------------------------------------------------------------------


def test_the_excel_tasks_keep_their_replies_in_the_same_memo(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    files = eval_memo.files_version()
    kept = excel_eval.memo_key("X01", "an earlier reply", "C", "haiku", files)
    eval_memo.write_kept(eval_memo.Kept(kept, "2026-11-12", "", "an earlier reply"), tmp_path)
    memo = ["--model", "haiku", "--memo", str(tmp_path)]
    assert excel_eval.main(["plan", "C", "--split", "dev", "--tasks", "X01,X02", *memo]) == 0
    plan = capsys.readouterr().out
    assert "X01: from the memo, X01-C-haiku-" in plan and "X02: ask: no reply kept" in plan
    assert excel_eval.main(["proxy", "C", "--split", "dev", "--tasks", "X01,X02", *memo]) == 0
    message = capsys.readouterr().out
    assert "## X02\n" in message and "## X01\n" not in message
    answers = tmp_path / "answers.md"
    answers.write_text(f"{ANSWERS_HEAD}\n## X02\n\nNo SQL.\n", encoding="utf-8")
    assert excel_eval.main(["score", str(answers), "--split", "dev", "--tasks", "X01,X02",
                            "--memo", str(tmp_path)]) == 0
    assert "1 of 2 replies from the memo." in capsys.readouterr().out
    assert [one.score[:9] for one in eval_memo.read_kept("X02", "C", "haiku", tmp_path)] == [
        "X02  FAIL"]


def test_a_held_out_excel_task_in_arm_c_is_kept_by_the_files_version() -> None:
    held_out = next(task.id for task in excel_eval.TASKS if task.split == "held_out")
    assert excel_eval.memo_key(held_out, "", "C", "haiku", "aaa").files_version == "aaa"
    assert excel_eval.memo_key(held_out, "", "A0", "haiku", "aaa").files_version == "-"
    assert excel_eval.memo_key("X01", "", "C", "haiku", "aaa").files_version == "-"
