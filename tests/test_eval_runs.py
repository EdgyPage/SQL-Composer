"""The evaluation system's one module (evaluation system, ticket 01): the local folder, the
ledger, the memo keyed by the text a task loads, plans and budgets.

Each test gives the module a temporary folder, so none writes the repo's `.eval-local/`.
"""

from __future__ import annotations

import math
from pathlib import Path

import eval_memo
import eval_runs
import pytest


def a_run(**changed: str) -> eval_runs.Run:
    """A ledger row of a haiku proxy's run on a Copilot task, with `changed` fields."""
    fields = {"date": "2026-11-14", "commit": "dd2965b2", "round": "r1", "pipeline": "copilot",
              "task": "T07", "arm": "C", "model": "haiku", "role": "proxy", "tokens": "1000",
              "seconds": "12", "result": "pass"}
    return eval_runs.Run(**{**fields, **changed})


def a_key(task_text: str = "Count the failed runs.", loaded_text: str = "file 03"
          ) -> eval_runs.Key:
    return eval_runs.hashed_key("T07", task_text, "C", "haiku", loaded_text)


def keep(key: eval_runs.Key, folder: Path) -> None:
    eval_runs.write_kept(eval_runs.Kept(key, "2026-11-14", "T07  pass", "a reply"), folder)


# --- The local folder ------------------------------------------------------------------------


def test_the_local_folder_is_the_repos_eval_local_and_is_made_on_first_use(
        tmp_path: Path) -> None:
    assert eval_runs.LOCAL == eval_runs.ROOT / ".eval-local"
    assert eval_runs.MEMO == eval_runs.LOCAL / "memo"
    made = eval_runs.make_local_path("runs", "r1", local=tmp_path / ".eval-local")
    assert made == tmp_path / ".eval-local" / "runs" / "r1" and made.parent.is_dir()


def test_a_path_outside_the_local_folder_is_refused(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="outside"):
        eval_runs.make_local_path("..", "elsewhere", local=tmp_path / ".eval-local")


# --- The ledger ------------------------------------------------------------------------------


def test_a_recorded_run_reads_back_from_the_ledger_csv(tmp_path: Path) -> None:
    assert eval_runs.read_ledger(tmp_path) == []
    eval_runs.record_run(a_run(), tmp_path)
    eval_runs.record_run(a_run(task="T08", result="fail, a comma"), tmp_path)
    rows = eval_runs.read_ledger(tmp_path)
    assert [row.task for row in rows] == ["T07", "T08"]
    assert rows[1].result == "fail, a comma"
    lines = (tmp_path / "ledger.csv").read_text(encoding="utf-8").splitlines()
    assert lines[0] == ("date,commit,round,pipeline,task,arm,model,role,tokens,seconds,result")
    assert len(lines) == 3


def test_the_record_command_writes_a_row_from_an_agents_reported_usage(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    code = eval_runs.main(["record", "--local", str(tmp_path), "--pipeline", "metric",
                           "--round", "r2", "--task", "M01", "--arm", "C", "--model", "haiku",
                           "--role", "user", "--tokens", "84000", "--seconds", "95",
                           "--result", "pass", "--commit", "abc1234", "--date", "2026-11-14"])
    assert code == 0
    (row,) = eval_runs.read_ledger(tmp_path)
    assert (row.pipeline, row.role, row.tokens, row.commit) == ("metric", "user", "84000",
                                                                "abc1234")
    assert "recorded" in capsys.readouterr().out.lower()


@pytest.mark.parametrize(("field", "value"), [("pipeline", "tarot"), ("role", "wizard"),
                                              ("tokens", "many"), ("seconds", "-3")])
def test_a_row_with_an_unknown_pipeline_or_role_or_a_bad_number_is_refused(
        tmp_path: Path, field: str, value: str) -> None:
    with pytest.raises(SystemExit):
        eval_runs.record_run(a_run(**{field: value}), tmp_path)
    assert eval_runs.read_ledger(tmp_path) == []


def a_maintainer_run(**changed: str) -> eval_runs.Run:
    return a_run(**{"pipeline": "maintainer", "role": "maintainer", "task": "drift-reviewer",
                    "round": "eval-system-08", "arm": "-", "model": "opus",
                    "result": "opened D3 D4", **changed})


def test_each_maintainer_agent_records_a_run_with_its_result(tmp_path: Path) -> None:
    for agent in eval_runs.MAINTAINER_AGENTS:
        eval_runs.record_run(a_maintainer_run(task=agent), tmp_path)
    eval_runs.record_run(a_maintainer_run(result="clean"), tmp_path)
    rows = eval_runs.read_ledger(tmp_path)
    assert [row.task for row in rows[:4]] == list(eval_runs.MAINTAINER_AGENTS)
    assert rows[-1].result == "clean"


@pytest.mark.parametrize(("field", "value"), [("task", "T07"), ("role", "proxy"),
                                              ("pipeline", "metric"), ("result", "pass")])
def test_a_maintainer_row_naming_no_agent_or_no_outcome_is_refused(
        tmp_path: Path, field: str, value: str) -> None:
    with pytest.raises(SystemExit, match="maintainer"):
        eval_runs.record_run(a_maintainer_run(**{field: value}), tmp_path)
    assert eval_runs.read_ledger(tmp_path) == []


# --- The memo, keyed by exactly the loaded text ----------------------------------------------


def test_a_kept_reply_reads_back_and_a_key_is_its_task_arm_model_and_texts(
        tmp_path: Path) -> None:
    key = a_key()
    keep(key, tmp_path)
    (kept,) = eval_runs.read_kept("T07", "C", "haiku", tmp_path)
    assert kept.key == key and kept.reply == "a reply"
    assert eval_runs.read_kept("T07", "C", "sonnet", tmp_path) == []
    assert key.loaded_text_hash == eval_runs.text_hash("file 03")


def test_the_memo_is_the_one_eval_memo_reads(tmp_path: Path) -> None:
    keep(a_key(), tmp_path)
    (kept,) = eval_memo.read_kept("T07", "C", "haiku", tmp_path)
    assert kept.key == a_key() and kept.reply == "a reply"


def test_a_reply_is_kept_until_the_text_it_loads_changes(tmp_path: Path) -> None:
    def key_of(task: str, reply: str) -> eval_runs.Key:
        return a_key(loaded_text=loaded[0])
    loaded = ["file 03"]
    first = eval_runs.memo_plan(["T07"], key_of, fresh=False, folder=tmp_path)[0]
    assert (first.reason, first.kept) == ("no reply kept", None)
    keep(a_key(), tmp_path)
    again = eval_runs.memo_plan(["T07"], key_of, fresh=False, folder=tmp_path)[0]
    assert again.reason == "" and again.kept is not None
    loaded[0] = "file 03, edited"
    changed = eval_runs.memo_plan(["T07"], key_of, fresh=False, folder=tmp_path)[0]
    assert (changed.reason, changed.kept) == ("the text it loads changed", None)


def test_a_held_out_reply_is_kept_by_the_same_key_as_a_dev_reply(tmp_path: Path) -> None:
    keep(a_key(), tmp_path)
    found = eval_runs.memo_plan(["T07"], lambda task, reply: a_key(), fresh=False,
                                folder=tmp_path)[0]
    assert found.kept is not None


def test_a_changed_task_text_is_asked_again_and_fresh_asks_every_task(tmp_path: Path) -> None:
    keep(a_key(), tmp_path)
    edited = eval_runs.memo_plan(["T07"], lambda task, reply: a_key("Count by day."),
                                 fresh=False, folder=tmp_path)[0]
    assert edited.reason == "its text changed"
    fresh = eval_runs.memo_plan(["T07"], lambda task, reply: a_key(), fresh=True,
                                folder=tmp_path)[0]
    assert (fresh.reason, fresh.kept) == ("--fresh", None)


# --- Plans and budgets -----------------------------------------------------------------------


def test_the_estimate_is_the_mean_tokens_of_past_rows_of_the_pipeline_arm_and_model() -> None:
    rows = [a_run(tokens="1000"), a_run(tokens="3000"), a_run(arm="R", tokens="9000"),
            a_run(model="sonnet", tokens="9000"), a_run(pipeline="excel", tokens="9000")]
    assert eval_runs.estimated_tokens(rows, "copilot", "C", "haiku", asked=3) == 6000
    assert eval_runs.estimated_tokens(rows, "metric", "C", "haiku", asked=3) is None
    assert eval_runs.estimated_tokens(rows, "copilot", "C", "haiku", asked=0) == 0


def test_every_pipeline_has_a_budget_of_infinity_today() -> None:
    assert set(eval_runs.BUDGET) == set(eval_runs.PIPELINES)
    assert all(limit == math.inf for limit in eval_runs.BUDGET.values())


def test_a_round_over_its_pipelines_budget_is_refused_unless_over_budget_is_given() -> None:
    eval_runs.check_budget("copilot", 5000, over_budget=False)
    eval_runs.check_budget("copilot", None, over_budget=False)
    limits = {**eval_runs.BUDGET, "copilot": 4000}
    with pytest.raises(SystemExit, match="over-budget"):
        eval_runs.check_budget("copilot", 5000, over_budget=False, budget=limits)
    eval_runs.check_budget("copilot", 5000, over_budget=True, budget=limits)


def test_a_plan_lists_each_task_with_why_and_estimates_from_past_rows(tmp_path: Path) -> None:
    eval_runs.record_run(a_run(tokens="2000"), tmp_path)
    eval_runs.record_run(a_run(tokens="4000"), tmp_path)

    def key_of(task: str, reply: str) -> eval_runs.Key:
        return eval_runs.hashed_key(task, "text", "C", "haiku", "file 03")
    keep(eval_runs.hashed_key("T07", "text", "C", "haiku", "file 03"), tmp_path / "memo")
    asking = eval_runs.RoundToPlan("copilot", "C", "haiku", ["T07", "T08", "T09"])
    plan = eval_runs.plan_round(asking, key_of, fresh=False, over_budget=False,
                                local=tmp_path)
    assert "T07: from the memo" in plan.text
    assert "T08: ask: no reply kept" in plan.text and "T09: ask: no reply kept" in plan.text
    assert plan.asked == ["T08", "T09"] and plan.tokens == 6000
    assert "estimated 6000 tokens" in plan.text and "budget: no limit" in plan.text


def test_a_plan_with_no_past_rows_says_there_is_no_estimate(tmp_path: Path) -> None:
    asking = eval_runs.RoundToPlan("copilot", "C", "haiku", ["T07"])
    plan = eval_runs.plan_round(asking, lambda task, reply: a_key(), fresh=False,
                                over_budget=False, local=tmp_path)
    assert plan.tokens is None and "No estimate" in plan.text


def test_a_plan_over_the_budget_refuses(tmp_path: Path) -> None:
    eval_runs.record_run(a_run(tokens="9000"), tmp_path)
    asking = eval_runs.RoundToPlan("copilot", "C", "haiku", ["T07"])
    limits = {**eval_runs.BUDGET, "copilot": 100}
    with pytest.raises(SystemExit, match="over-budget"):
        eval_runs.plan_round(asking, lambda task, reply: a_key(), fresh=False,
                             over_budget=False, local=tmp_path, budget=limits)
    plan = eval_runs.plan_round(asking, lambda task, reply: a_key(), fresh=False,
                                over_budget=True, local=tmp_path, budget=limits)
    assert "over budget" in plan.text


# --- Carrying the old memo over --------------------------------------------------------------


def test_the_old_memo_is_carried_over_under_its_keys_and_not_over_a_newer_reply(
        tmp_path: Path) -> None:
    old, new = tmp_path / "old", tmp_path / "new"
    keep(a_key(), old)
    keep(a_key("another task text"), old)
    assert eval_runs.carry_over(old, new) == 2
    assert len(eval_runs.read_kept("T07", "C", "haiku", new)) == 2
    assert eval_runs.carry_over(old, new) == 0
    assert eval_runs.carry_over(tmp_path / "nothing", new) == 0


def test_the_old_records_are_copied_under_the_local_folder_and_nothing_is_deleted(
        tmp_path: Path) -> None:
    root, local = tmp_path / "repo", tmp_path / "local"
    scratch = root / ".scratch"
    (scratch / "usability-loop" / "runs" / "r1").mkdir(parents=True)
    report = scratch / "usability-loop" / "runs" / "r1" / "report.md"
    report.write_text("u", encoding="utf-8")
    (scratch / "usability-loop" / "results.md").write_text("ur", encoding="utf-8")
    (scratch / "copilot-eval" / "runs" / "a").mkdir(parents=True)
    (scratch / "copilot-eval" / "runs" / "a" / "x.md").write_text("c", encoding="utf-8")
    keep(a_key(), scratch / "copilot-eval" / "memo")
    assert eval_runs.copy_records(root, local) == 4
    assert (local / "usability/runs/r1/report.md").read_text(encoding="utf-8") == "u"
    assert (local / "usability" / "results.md").read_text(encoding="utf-8") == "ur"
    assert (local / "copilot" / "runs" / "a" / "x.md").read_text(encoding="utf-8") == "c"
    assert len(eval_runs.read_kept("T07", "C", "haiku", local / "memo")) == 1
    assert (scratch / "usability-loop" / "results.md").is_file()
    assert eval_runs.copy_records(root, local) == 0
    assert eval_runs.copy_records(tmp_path / "nothing", local) == 0


def test_the_copy_records_command_copies_from_a_root_into_a_local_folder(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    root = tmp_path / "repo"
    (root / ".scratch" / "copilot-eval").mkdir(parents=True)
    (root / ".scratch" / "copilot-eval" / "results.md").write_text("r", encoding="utf-8")
    assert eval_runs.main(["copy-records", "--root", str(root),
                           "--local", str(tmp_path / "local")]) == 0
    assert "Copied 1 files" in capsys.readouterr().out


# --- A held-out task and an agent-counted estimate (evaluation system, ticket 03) -------------


def test_fresh_asks_every_kept_task_again_but_not_a_held_out_one(tmp_path: Path) -> None:
    keep(eval_runs.hashed_key("T07", "text", "C", "haiku", "file 03"), tmp_path)
    keep(eval_runs.hashed_key("T09", "text", "C", "haiku", "file 03"), tmp_path)

    def key_of(task: str, reply: str) -> eval_runs.Key:
        return eval_runs.hashed_key(task, "text", "C", "haiku", "file 03")
    plan = eval_runs.memo_plan(["T07", "T09"], key_of, fresh=True, folder=tmp_path,
                               held_out=frozenset({"T09"}))
    assert [(one.task, one.reason) for one in plan] == [("T07", "--fresh"), ("T09", "")]


def test_a_plans_estimate_is_by_agent_when_a_proxy_takes_several_tasks(tmp_path: Path) -> None:
    eval_runs.record_run(a_run(tokens="2000"), tmp_path)
    asking = eval_runs.RoundToPlan("copilot", "C", "haiku", ["T07", "T08", "T09"],
                                   agents=lambda asked: 1)
    plan = eval_runs.plan_round(asking, lambda task, reply: a_key(), fresh=False,
                                over_budget=False, local=tmp_path)
    assert plan.tokens == 2000 and "Spawn 1 proxies." in plan.text
