"""The model ladder, the caps, and a plan that never asks a task again on an unchanged key
(evaluation system, ticket 07).

A task is asked of the cheapest model that has not failed it; each pipeline has a cap on a
proxy's reply and on a conversation's turns, in one table, `eval_runs.CAPS`, which its batch
writes into each message and its scorer holds. Each test gives the tools a temporary local
folder with `--local`.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import copilot_eval
import eval_runs
import excel_eval
import pytest
from copilot_eval_tasks import BY_ID
from excel_eval_tasks import BY_ID as EXCEL_BY_ID


def keep(task: str, model: str, score: str, folder: Path, arm: str = "C") -> None:
    """Keep a reply to a Copilot task on a model under the key it has now, with a score."""
    reply = "```python\nx = 1\n```\n"
    key = copilot_eval.memo_key(task, reply, arm, model)
    eval_runs.write_kept(eval_runs.Kept(key, "2026-11-14", score, reply), folder / "memo")


def key_for_model(model: str) -> Callable[[str, str], eval_runs.Key]:
    def key_of(task: str, reply: str) -> eval_runs.Key:
        return copilot_eval.memo_key(task, reply, "C", model)
    return key_of


def step(task: str, local: Path, fresh: bool = False, held_out: bool = False,
         pipeline: str = "copilot") -> eval_runs.Step:
    return eval_runs.ladder_step(task, pipeline, key_for_model, fresh, held_out,
                                 local / "memo")


# --- The ladder -------------------------------------------------------------------------------


def test_the_ladder_runs_haiku_sonnet_opus_and_a_pass_is_read_from_a_score_line() -> None:
    assert eval_runs.LADDER == ("haiku", "sonnet", "opus")
    for passing in ("pass", "T07  pass  found parses", "T07  route  strict pass  index FAIL"):
        assert eval_runs.score_passed(passing)
    for failing in ("", "fail", "T07  FAIL  found", "T07  route  strict FAIL  index pass"):
        assert not eval_runs.score_passed(failing)


def test_a_task_with_no_reply_kept_is_asked_of_the_cheapest_rung(tmp_path: Path) -> None:
    found = step("T07", tmp_path)
    assert (found.model, found.kept, found.reason) == ("haiku", None, "no reply kept")


def test_a_task_the_rung_below_failed_climbs_one_rung_and_says_so(tmp_path: Path) -> None:
    keep("T07", "haiku", "T07  FAIL  found", tmp_path)
    found = step("T07", tmp_path)
    assert (found.model, found.kept, found.reason) == ("sonnet", None, "haiku failed it")
    keep("T07", "sonnet", "T07  FAIL  found", tmp_path)
    assert step("T07", tmp_path).model == "opus"
    assert step("T07", tmp_path).reason == "sonnet failed it"


def test_the_cheapest_rung_that_passed_gives_its_reply_and_is_not_asked_again(
        tmp_path: Path) -> None:
    keep("T07", "haiku", "T07  FAIL  found", tmp_path)
    keep("T07", "sonnet", "T07  pass  found", tmp_path)
    keep("T07", "opus", "T07  pass  found", tmp_path)
    found = step("T07", tmp_path)
    assert found.model == "sonnet" and found.kept is not None and found.reason == ""


def test_a_task_every_rung_failed_is_not_asked_again(tmp_path: Path) -> None:
    for model in eval_runs.LADDER:
        keep("T07", model, "T07  FAIL  found", tmp_path)
    found = step("T07", tmp_path)
    assert found.model == "opus" and found.kept is not None


def test_fresh_asks_a_dev_task_on_the_cheapest_rung_but_not_a_held_out_one_kept(
        tmp_path: Path) -> None:
    keep("T07", "sonnet", "T07  pass  found", tmp_path)
    keep("T07", "haiku", "T07  FAIL  found", tmp_path)
    assert step("T07", tmp_path, fresh=True) == eval_runs.Step("T07", "haiku", None, "--fresh")
    assert step("T07", tmp_path, fresh=True, held_out=True).kept is not None


def test_the_usability_loop_has_one_rung_as_a_larger_model_passing_shows_nothing(
        tmp_path: Path) -> None:
    assert eval_runs.rungs_of("usability") == ("haiku",)
    keep("T07", "haiku", "T07  FAIL  found", tmp_path)
    found = step("T07", tmp_path, pipeline="usability")
    assert found.model == "haiku" and found.kept is not None


def test_the_cheapest_model_that_passed_a_task_is_read_from_the_memo_on_any_text(
        tmp_path: Path) -> None:
    assert eval_runs.cheapest_passed("T07", "C", tmp_path / "memo") is None
    keep("T07", "opus", "T07  pass  found", tmp_path)
    keep("T07", "haiku", "T07  FAIL  found", tmp_path)
    assert eval_runs.cheapest_passed("T07", "C", tmp_path / "memo") == "opus"
    keep("T07", "sonnet", "T07  pass  found", tmp_path)
    assert eval_runs.cheapest_passed("T07", "C", tmp_path / "memo") == "sonnet"


# --- A plan on the ladder ---------------------------------------------------------------------

ON_THE_LADDER = ["--split", "dev", "--objective", "03"]


def test_plan_on_the_ladder_proposes_a_model_per_task_and_each_rungs_tasks(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    keep("T07", "haiku", "T07  pass  found", tmp_path)
    keep("T08", "haiku", "T08  FAIL  found", tmp_path)
    local = ["--local", str(tmp_path)]
    assert copilot_eval.main(["plan", "C", *ON_THE_LADDER, *local]) == 0
    plan = capsys.readouterr().out
    assert "T07: from the memo" in plan and "(haiku passed), not asked again" in plan
    assert "T08: ask on sonnet: haiku failed it" in plan
    assert "Rung sonnet: T08" in plan and "Rung haiku" not in plan
    assert "--model <rung> --only <its tasks>" in plan


def test_a_ladder_plan_names_the_cheapest_model_that_passed_on_older_text(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    older = copilot_eval.memo_key("T07", "", "C", "sonnet")
    older = eval_runs.Key(older.task, "changed", older.arm, older.model, older.loaded_text_hash)
    eval_runs.write_kept(eval_runs.Kept(older, "2026-11-01", "T07  pass  found", "x"),
                         tmp_path / "memo")
    assert copilot_eval.main(["plan", "C", *ON_THE_LADDER, "--local", str(tmp_path)]) == 0
    assert "T07: ask on haiku: no reply kept (it passed before on sonnet)" in (
        capsys.readouterr().out)


def test_a_model_given_overrides_the_ladder_for_every_task(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    keep("T07", "haiku", "T07  pass  found", tmp_path)
    assert copilot_eval.main(["plan", "C", *ON_THE_LADDER, "--model", "sonnet",
                              "--local", str(tmp_path)]) == 0
    plan = capsys.readouterr().out
    assert "T07: ask: no reply kept" in plan and "Rung" not in plan


def test_a_round_that_batches_on_the_ladder_is_told_to_batch_each_rung(
        tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="each rung"):
        copilot_eval.main(["batch", "C", *ON_THE_LADDER, "--model", "ladder",
                           "--round", "r1", "--local", str(tmp_path)])
    assert not (tmp_path / "copilot" / "runs" / "r1").exists()


def test_only_cuts_a_round_to_the_tasks_a_rung_names(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    local = ["--local", str(tmp_path)]
    assert copilot_eval.main(["batch", "C", *ON_THE_LADDER, "--model", "sonnet", "--only",
                              "T08", "--round", "r1", *local]) == 0
    capsys.readouterr()
    message = (tmp_path / "copilot" / "runs" / "r1" / "c03" / "message.md").read_text(
        encoding="utf-8")
    assert "## T08\n" in message and "## T07\n" not in message


def test_a_ladder_plan_sums_each_rungs_estimate_and_checks_the_budget(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
        capsys: pytest.CaptureFixture[str]) -> None:
    keep("T07", "haiku", "T07  FAIL  found", tmp_path)
    for model, tokens in (("haiku", "1000"), ("sonnet", "5000")):
        eval_runs.record_run(eval_runs.Run("2026-11-14", "abc", "r0", "copilot", "c03", "C",
                                           model, "proxy", tokens, "40", "pass"), tmp_path)
    local = ["--local", str(tmp_path)]
    assert copilot_eval.main(["plan", "C", *ON_THE_LADDER, *local]) == 0
    assert "estimated 6000 tokens" in capsys.readouterr().out  # one proxy a rung
    monkeypatch.setitem(eval_runs.BUDGET, "copilot", 100)
    with pytest.raises(SystemExit, match="over-budget"):
        copilot_eval.main(["plan", "C", *ON_THE_LADDER, *local])


# --- The caps ---------------------------------------------------------------------------------


def test_every_testing_pipeline_has_its_caps_in_the_one_table() -> None:
    assert set(eval_runs.CAPS) == {"usability", "copilot", "excel", "metric"}
    for caps in eval_runs.CAPS.values():
        assert caps.reply > 0 and caps.turns >= 1
    assert eval_runs.CAPS["metric"].turns == 12 and eval_runs.CAPS["usability"].turns == 5


def test_a_reply_over_the_cap_is_flagged_and_its_score_is_unchanged() -> None:
    cap = eval_runs.CAPS["copilot"].reply
    over = eval_runs.replies_over_cap("copilot", {"T07": "x" * (cap + 1), "T08": "x" * cap})
    assert over == {"T07": cap + 1}
    lines = eval_runs.flag_over_cap("copilot", {"T07": "T07  pass", "T08": "T08  pass"}, over)
    assert lines["T07"] == f"T07  pass  OVER CAP: {cap + 1} characters, cap {cap}"
    assert lines["T08"] == "T08  pass"
    assert eval_runs.score_passed(lines["T07"])
    assert f"T07 ({cap + 1})" in eval_runs.cap_summary("copilot", over)
    assert eval_runs.cap_summary("copilot", {}) == ""


def test_the_caps_are_written_into_the_message_and_the_text_names_them() -> None:
    assert "6000 characters" in eval_runs.cap_text("copilot")
    assert "turns" not in eval_runs.cap_text("copilot")
    assert "12 turns" in eval_runs.cap_text("metric")
    assert eval_runs.cap_text("copilot") in copilot_eval.proxy_message(
        "C", [BY_ID["T07"], BY_ID["T08"]])
    assert eval_runs.cap_text("excel") in excel_eval.proxy_message("C", [next(
        iter(EXCEL_BY_ID.values()))])


def test_a_scored_reply_over_the_cap_is_flagged_in_the_report_and_kept_with_the_flag(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    local = ["--local", str(tmp_path)]
    assert copilot_eval.main(["batch", "C", *ON_THE_LADDER, "--model", "haiku", "--only",
                              "T07", "--round", "r1", *local]) == 0
    long = "```python\nx = 1\n```\n" + "# padding\n" * 700
    (tmp_path / "copilot" / "runs" / "r1" / "c03" / "answers.md").write_text(
        f"## T07\n\n{long}", encoding="utf-8")
    assert copilot_eval.main(["collect", "r1", *local]) == 0
    capsys.readouterr()
    assert copilot_eval.main(["score", "r1", *local]) == 0
    assert "1 replies over the copilot reply cap of 6000 characters: T07" in (
        capsys.readouterr().out)
    [kept] = eval_runs.read_kept("T07", "C", "haiku", tmp_path / "memo")
    assert "OVER CAP" in kept.score


# --- A plan never asks a task again on an unchanged key ---------------------------------------


def test_the_copilot_plan_asks_no_task_whose_key_is_unchanged_and_says_so_per_task(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    keep("T07", "haiku", "T07  pass  found", tmp_path)
    keep("T08", "haiku", "T08  FAIL  found", tmp_path)  # a failure isn't asked again either
    args = ["plan", "C", "--split", "dev", "--objective", "03", "--model", "haiku",
            "--local", str(tmp_path)]
    assert copilot_eval.main(args) == 0
    plan = capsys.readouterr().out
    assert "T07: from the memo" in plan and "T08: from the memo" in plan
    assert "Ask 0 of 2; 2 from the memo." in plan


def test_the_excel_plan_asks_no_task_whose_key_is_unchanged_and_says_so_per_task(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    task = next(iter(EXCEL_BY_ID))
    reply = "```sql\nSELECT 1\n```\n"
    key = excel_eval.memo_key(task, reply, "C", "haiku")
    eval_runs.write_kept(eval_runs.Kept(key, "2026-11-14", f"{task}  pass", reply),
                         tmp_path / "memo")
    assert excel_eval.main(["plan", "C", "--tasks", task, "--model", "haiku",
                            "--local", str(tmp_path)]) == 0
    assert f"{task}: from the memo" in capsys.readouterr().out


def test_a_change_to_the_text_a_task_loads_asks_it_again_on_the_ladder(
        tmp_path: Path, capsys: pytest.CaptureFixture[str],
        monkeypatch: pytest.MonkeyPatch) -> None:
    keep("T07", "haiku", "T07  pass  found", tmp_path)
    monkeypatch.setattr(copilot_eval, "loaded_text", lambda arm, task, reply: "new file")
    assert copilot_eval.main(["plan", "C", *ON_THE_LADDER, "--local", str(tmp_path)]) == 0
    assert "T07: ask on haiku: the text it loads changed" in capsys.readouterr().out
