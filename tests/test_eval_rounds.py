"""The Copilot and Excel evaluations run by script (evaluation system, ticket 03).

A round is plan, batch, (the session spawns the proxies), collect, score and record, with no
orchestrating agent. Each test gives the tools a temporary local folder with `--local`, so none
writes the repo's `.eval-local/`.
"""

from __future__ import annotations

import json
from pathlib import Path

import copilot_eval
import eval_runs
import excel_eval
import pytest
from copilot_eval_tasks import BY_ID, TASKS
from excel_eval_tasks import BY_ID as EXCEL_BY_ID


def fenced(code: str) -> str:
    return f"Here it is:\n\n```python\n{code}```\n"


def keep(task_id: str, arm: str, reply: str, local: Path, model: str = "haiku") -> None:
    """Keep a reply to a Copilot task, under the key it has now."""
    key = copilot_eval.memo_key(task_id, reply, arm, model)
    eval_runs.write_kept(eval_runs.Kept(key, "2026-11-12", "", reply), local / "memo")


def record_a_proxy(local: Path) -> None:
    """A past row of a proxy of 30,000 tokens in arm C on haiku, to estimate by."""
    run = eval_runs.Run("2026-11-14", "abc", "r0", "copilot", "c03", "C", "haiku", "proxy",
                        "30000", "40", "pass")
    eval_runs.record_run(run, local)


ROUND_OF = ["--split", "dev", "--objective", "03", "--model", "haiku"]


# --- Shared: the folder, the batch and the collect --------------------------------------------


def test_a_batch_writes_each_proxys_message_and_prints_one_line_per_proxy(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    local = ["--local", str(tmp_path)]
    assert copilot_eval.main(["batch", "C", *ROUND_OF, "--round", "r1", *local]) == 0
    lines = capsys.readouterr().out.splitlines()
    [line] = lines
    agent, model, prompt = line.split(" | ")
    assert (agent, model) == ("copilot-proxy", "haiku")
    folder = tmp_path / "copilot" / "runs" / "r1" / "c03"
    assert (folder / "message.md").is_file() and not (folder / "answers.md").exists()
    assert str((folder / "message.md").as_posix()) in prompt.replace("\\", "/") or \
        "c03/message.md" in prompt.replace("\\", "/")
    message = (folder / "message.md").read_text(encoding="utf-8")
    assert "## T07\n" in message and "## T08\n" in message
    saved = json.loads((tmp_path / "copilot" / "runs" / "r1" / "round.json").read_text(
        encoding="utf-8"))
    assert saved["arm"] == "C" and saved["proxies"] == {"c03": ["T07", "T08"]}


def test_a_round_name_is_never_used_twice(tmp_path: Path) -> None:
    args = ["batch", "C", *ROUND_OF, "--round", "r1", "--local", str(tmp_path)]
    assert copilot_eval.main(args) == 0
    with pytest.raises(SystemExit, match="exists"):
        copilot_eval.main(args)


def test_arm_c_gives_each_objective_its_own_proxy_and_the_other_arms_ten_tasks_each(
        ) -> None:
    asked = [task.id for task in TASKS if task.split == "dev"]
    by_objective = copilot_eval.proxy_groups("C", asked)
    assert sorted(by_objective) == [f"c{objective}" for objective in sorted(
        {BY_ID[task].objective for task in asked})]
    assert all(len({BY_ID[task].objective for task in group}) == 1
               for group in by_objective.values())
    routing = copilot_eval.proxy_groups("R", asked)
    assert all(len(group) <= 10 for group in routing.values())
    assert [task for group in routing.values() for task in group] == asked


def test_collect_merges_the_proxies_answers_and_says_what_is_missing(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    local = ["--local", str(tmp_path)]
    assert copilot_eval.main(["batch", "C", "--split", "dev", "--model", "haiku",
                              "--round", "r1", "--objective", "03", *local]) == 0
    folder = tmp_path / "copilot" / "runs" / "r1" / "c03"
    (folder / "answers.md").write_text(
        f"## T07\n\n{fenced('a = 1')}\n## T99\n\nNot one of its tasks.\n", encoding="utf-8")
    capsys.readouterr()
    assert copilot_eval.main(["collect", "r1", *local]) == 1
    said = capsys.readouterr().out
    assert "No reply for T08." in said
    header, replies = eval_runs.read_answers(
        (tmp_path / "copilot" / "runs" / "r1" / "answers.md").read_text(encoding="utf-8"), "T")
    assert (header["arm"], header["model"], header["round_tasks"]) == ("C", "haiku", "T07,T08")
    assert list(replies) == ["T07"]


def test_collect_says_which_proxy_wrote_no_answers_file(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    local = ["--local", str(tmp_path)]
    copilot_eval.main(["batch", "C", *ROUND_OF, "--round", "r1", *local])
    capsys.readouterr()
    assert copilot_eval.main(["collect", "r1", *local]) == 1
    assert "No answers file from c03." in capsys.readouterr().out


def test_a_path_that_leaves_the_local_folder_is_refused(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="outside the local folder"):
        copilot_eval.main(["batch", "C", *ROUND_OF, "--round", "../../../escape",
                           "--local", str(tmp_path)])


# --- Plan: the memo, held out once per loaded text, the estimate ------------------------------


def test_plan_names_only_the_tasks_to_ask_and_batch_writes_only_those(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    keep("T07", "C", fenced(BY_ID["T07"].reference), tmp_path)
    local = ["--local", str(tmp_path)]
    assert copilot_eval.main(["plan", "C", *ROUND_OF, *local]) == 0
    plan = capsys.readouterr().out
    assert "T07: from the memo, T07-C-haiku-" in plan
    assert "T08: ask: no reply kept" in plan and "Spawn 1 proxies." in plan
    assert copilot_eval.main(["batch", "C", *ROUND_OF, "--round", "r1", *local]) == 0
    capsys.readouterr()
    message = (tmp_path / "copilot" / "runs" / "r1" / "c03" / "message.md").read_text(
        encoding="utf-8")
    assert "## T08\n" in message and "## T07\n" not in message
    assert copilot_eval.main(["prompts", "C", *ROUND_OF, *local]) == 0
    prompts = capsys.readouterr().out
    assert "## T08\n" in prompts and "## T07\n" not in prompts
    assert copilot_eval.main(["template", "C", *ROUND_OF, *local]) == 0
    _, replies = eval_runs.read_answers(capsys.readouterr().out, "T")
    assert list(replies) == ["T08"]


def test_a_round_with_every_reply_kept_asks_nothing_and_is_scored_from_the_memo(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    for task_id in ("T07", "T08"):
        keep(task_id, "C", fenced(BY_ID[task_id].reference), tmp_path)
    local = ["--local", str(tmp_path)]
    assert copilot_eval.main(["batch", "C", *ROUND_OF, "--round", "r1", *local]) == 0
    assert capsys.readouterr().out.startswith("Nothing to ask")
    assert copilot_eval.main(["collect", "r1", *local]) == 0
    capsys.readouterr()
    assert copilot_eval.main(["score", "r1", *local]) == 0
    assert "2 of 2 replies from the memo." in capsys.readouterr().out


def test_a_held_out_task_is_asked_once_per_text_it_loads_not_once_per_files_version(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    reply = fenced(BY_ID["T09"].reference)
    keep("T09", "C", reply, tmp_path)
    keep("T07", "C", fenced(BY_ID["T07"].reference), tmp_path)
    held_out = ["--split", "held_out", "--objective", "03", "--model", "haiku",
                "--local", str(tmp_path)]
    assert copilot_eval.main(["plan", "C", *held_out, "--fresh"]) == 0
    assert "T09: from the memo" in capsys.readouterr().out
    # `--fresh` asks a dev task again, not a held-out task already asked on the same text.
    assert copilot_eval.main(["plan", "C", *ROUND_OF, "--fresh",
                              "--local", str(tmp_path)]) == 0
    assert "T07: ask: --fresh" in capsys.readouterr().out
    # The key holds no files version: it changes with the text its task loads, and no other.
    assert copilot_eval.memo_key("T09", reply, "C", "haiku").files_version == "-"


def test_a_plan_estimates_by_proxy_from_the_ledger(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    record_a_proxy(tmp_path)
    assert copilot_eval.main(["plan", "C", *ROUND_OF, "--local", str(tmp_path)]) == 0
    assert "estimated 30000 tokens" in capsys.readouterr().out


def test_a_plan_over_the_budget_is_refused_unless_over_budget_is_given(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    record_a_proxy(tmp_path)
    monkeypatch.setitem(eval_runs.BUDGET, "copilot", 100)
    args = ["batch", "C", *ROUND_OF, "--local", str(tmp_path)]
    with pytest.raises(SystemExit, match="over-budget"):
        copilot_eval.main([*args, "--round", "r1"])
    assert not (tmp_path / "copilot" / "runs" / "r1").exists()
    assert copilot_eval.main([*args, "--round", "r2", "--over-budget"]) == 0


# --- Score: a round, the memo and the results -------------------------------------------------


def test_a_round_runs_plan_batch_collect_score_and_keeps_the_replies_and_the_row(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    keep("T08", "C", fenced(BY_ID["T08"].reference), tmp_path)
    local = ["--local", str(tmp_path)]
    assert copilot_eval.main(["batch", "C", *ROUND_OF, "--round", "r1", *local]) == 0
    (tmp_path / "copilot" / "runs" / "r1" / "c03").joinpath("answers.md").write_text(
        f"## T07\n\n{fenced(BY_ID['T07'].reference)}", encoding="utf-8")
    assert copilot_eval.main(["collect", "r1", *local]) == 0
    capsys.readouterr()
    assert copilot_eval.main(["score", "r1", *local]) == 0
    report = capsys.readouterr().out
    assert "T07  pass" in report and "T08  pass" in report
    assert "1 of 2 replies from the memo." in report
    results = tmp_path / "copilot" / "results.md"
    assert results.read_text(encoding="utf-8").endswith(" | 03:100 | 1 |\n")
    [t07] = eval_runs.read_kept("T07", "C", "haiku", tmp_path / "memo")
    assert t07.score.startswith("T07  pass")
    [t08] = eval_runs.read_kept("T08", "C", "haiku", tmp_path / "memo")
    assert t08.asked == "2026-11-12"


def test_score_takes_an_answers_file_from_a_round_run_by_hand(tmp_path: Path) -> None:
    answers = tmp_path / "answers.md"
    answers.write_text(f"date: 2026-11-14\narm: C\nmodel: copilot-web\nfiles: abc\n\n"
                       f"## T07\n\n{fenced(BY_ID['T07'].reference)}", encoding="utf-8")
    assert copilot_eval.main(["score", str(answers), "--local", str(tmp_path / "local")]) == 0
    assert (tmp_path / "local" / "copilot" / "results.md").is_file()


def test_score_refuses_an_answers_file_whose_header_gives_no_arm_or_model(
        tmp_path: Path) -> None:
    answers = tmp_path / "answers.md"
    answers.write_text(copilot_eval.template([BY_ID["T07"]]), encoding="utf-8")
    with pytest.raises(SystemExit, match="fill both in"):
        copilot_eval.main(["score", str(answers), "--local", str(tmp_path)])


# --- Arm R: routing, scored by its rules and by the Index -------------------------------------


def test_the_index_gives_each_objective_the_files_its_rows_load() -> None:
    text = (copilot_eval.COPILOT / "00_start_here.txt").read_text(encoding="utf-8")
    allowed = copilot_eval.index_loads(text)
    assert allowed["03"] == {"03"} and allowed["17"] == {"17"}
    # A workbook loads 15, 11 and 12, and 20 too where it has a PivotTable (Toolbox 8.9).
    assert allowed["15"] == {"15", "11", "12", "20"}
    # A converted pivot grown loads 21 with 03, 05 and 06, which a task of 05 never needs 21
    # for (Toolbox 8.9).
    assert allowed["21"] == {"21", "03", "05", "06"} and allowed["05"] == {"05"}


def test_arm_c_loads_file_21_with_the_files_it_is_loaded_with() -> None:
    texts = copilot_eval.files_loaded("C", "T50")
    assert list(texts) == ["21", "03", "05", "06"]
    assert copilot_eval.shared_text("C", "21") == "\n\n".join(texts.values())
    message = copilot_eval.proxy_message("C", [BY_ID["T50"]])
    assert "each with its file's number, such as `Used: 21:R3, 05:W2`" in message
    assert list(copilot_eval.files_loaded("C", "T07")) == ["03"]


@pytest.mark.parametrize(("reply", "strict", "index"), [
    ("## T07\n\n03_build_a_statement.txt", True, True),
    ("I would load `03_build_a_statement.txt`.", True, True),
    ("03_build_a_statement.txt, then 04_joins.txt", False, True),
    ("04_joins.txt, then 03_build_a_statement.txt", False, False),
    ("04_joins.txt", False, False),
    ("00_start_here.txt", False, False),
    ("99_made_up_file.txt", False, False),
    ("", False, False),
])
def test_a_routing_reply_is_right_strictly_by_the_rules_and_by_the_index(
        reply: str, strict: bool, index: bool) -> None:
    result = copilot_eval.routing(BY_ID["T07"], reply)
    assert (result.strict, result.index) == (strict, index)


def test_an_arm_r_round_is_scored_as_routing_kept_in_the_memo_and_recorded(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    local = ["--local", str(tmp_path)]
    assert copilot_eval.main(["batch", "R", *ROUND_OF, "--round", "r1", *local]) == 0
    assert "r-1/message.md" in capsys.readouterr().out.replace("\\", "/")
    (tmp_path / "copilot" / "runs" / "r1" / "r-1" / "answers.md").write_text(
        "## T07\n\n03_build_a_statement.txt\n\n## T08\n\n04_joins.txt\n", encoding="utf-8")
    assert copilot_eval.main(["collect", "r1", *local]) == 0
    capsys.readouterr()
    assert copilot_eval.main(["score", "r1", *local]) == 0
    report = capsys.readouterr().out
    assert "T07  route  strict pass  index pass" in report
    assert "T08  route  strict FAIL  index FAIL" in report
    assert "R on haiku: strict 50%, by the Index 50% of 2" in report
    row = (tmp_path / "copilot" / "results.md").read_text(encoding="utf-8")
    assert "| R | dev | 2 | 50 | 50 | 0 |" in row
    [kept] = eval_runs.read_kept("T07", "R", "haiku", tmp_path / "memo")
    assert kept.score.startswith("T07  route") and kept.key.arm == "R"


def test_arm_r_loads_file_00_and_the_file_its_reply_names() -> None:
    task = BY_ID["T07"]
    file_00 = copilot_eval.shared_text("R", None)
    file_03 = copilot_eval.shared_text("C", "03")
    named = copilot_eval.loaded_text("R", task, "## T07\n\n03_build_a_statement.txt\n")
    assert named == f"{file_00}{file_03}"
    assert copilot_eval.loaded_text("R", task, "") == file_00
    assert copilot_eval.loaded_text("C", task, "anything") == file_03


# --- The Excel tasks --------------------------------------------------------------------------


def test_an_excel_round_gives_each_proxy_five_workbooks_at_most(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    local = ["--local", str(tmp_path)]
    ids = ",".join(f"X{n:02d}" for n in range(1, 8))
    assert excel_eval.main(["batch", "C", "--split", "dev", "--tasks", ids, "--model", "haiku",
                            "--round", "x1", *local]) == 0
    lines = capsys.readouterr().out.splitlines()
    assert len(lines) == 2
    assert all(line.startswith("copilot-proxy | haiku | ") for line in lines)
    folder = tmp_path / "excel" / "runs" / "x1"
    first = (folder / "c-1" / "message.md").read_text(encoding="utf-8")
    assert "## X05\n" in first and "## X06\n" not in first
    assert "## X07\n" in (folder / "c-2" / "message.md").read_text(encoding="utf-8")


def test_an_excel_round_is_planned_collected_and_scored_with_the_memo(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    local = ["--local", str(tmp_path)]
    kept = excel_eval.memo_key("X01", "an earlier reply", "C", "haiku")
    eval_runs.write_kept(eval_runs.Kept(kept, "2026-11-12", "", "an earlier reply"),
                         tmp_path / "memo")
    round_of = ["--split", "dev", "--tasks", "X01,X02", "--model", "haiku"]
    assert excel_eval.main(["plan", "C", *round_of, *local]) == 0
    plan = capsys.readouterr().out
    assert "X01: from the memo, X01-C-haiku-" in plan and "X02: ask: no reply kept" in plan
    assert excel_eval.main(["batch", "C", *round_of, "--round", "x1", *local]) == 0
    capsys.readouterr()
    (tmp_path / "excel" / "runs" / "x1" / "c-1" / "answers.md").write_text(
        "## X02\n\nNo SQL.\n", encoding="utf-8")
    assert excel_eval.main(["collect", "x1", *local]) == 0
    capsys.readouterr()
    assert excel_eval.main(["score", "x1", *local]) == 0
    assert "1 of 2 replies from the memo." in capsys.readouterr().out
    assert [one.score[:9] for one in eval_runs.read_kept(
        "X02", "C", "haiku", tmp_path / "memo")] == ["X02  FAIL"]
    assert (tmp_path / "copilot" / "results.md").is_file()


def test_a_held_out_excel_task_is_kept_by_the_text_arm_c_loads_alone() -> None:
    held_out = next(task.id for task in excel_eval.TASKS if task.split == "held_out")
    assert excel_eval.memo_key(held_out, "", "C", "haiku").files_version == "-"
    assert held_out in EXCEL_BY_ID
    first = excel_eval.memo_key(held_out, "", "C", "haiku")
    assert first == excel_eval.memo_key(held_out, "a reply changes no key", "C", "haiku")
    assert first.loaded_text_hash != excel_eval.memo_key(held_out, "", "A0",
                                                         "haiku").loaded_text_hash


def test_the_files_version_is_one_hash_of_every_file_in_a_folder(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("one\r\n", encoding="utf-8", newline="")
    first = eval_runs.files_version(tmp_path)
    (tmp_path / "a.txt").write_text("one\n", encoding="utf-8", newline="")
    assert eval_runs.files_version(tmp_path) == first
    (tmp_path / "b.txt").write_text("two", encoding="utf-8")
    assert eval_runs.files_version(tmp_path) != first
