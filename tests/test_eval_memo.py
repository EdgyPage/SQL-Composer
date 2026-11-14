"""The memo by files version, which the Metric request evaluation still keeps (Toolbox 8.7,
ticket 02; evaluation system, ticket 03).

The Copilot and Excel evaluations moved onto `tools/eval_runs.py`, which keys a reply by the
hash of the text its task loads alone (`tests/test_eval_rounds.py`); `tools/eval_memo.py`'s
held-out-by-files-version planning stays until ticket 04 moves the Metric request evaluation,
and these tests hold it until then.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import eval_memo
import pytest


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
