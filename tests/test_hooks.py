"""The decisions the `dev` hooks make, checked without running Claude Code.

The hooks live in `.claude/hooks/` and import each other by name, so that folder goes on
`sys.path` here the way Claude Code's `python <script>` puts it there.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / ".claude" / "hooks"))

from drift_list import MAKES_A_COMMIT, needs_review, open_items, reviewed_commits  # noqa: E402
from drift_review import review_request  # noqa: E402
from drift_stop import what_blocks  # noqa: E402
from protect_main import refusal  # noqa: E402

DRIFT_TEXT = """\
# Drift

    - [ ] D3 | 1a2b3c4 | glossary | an example line, indented, never counted

## Items

- [x] D1 | aaaaaaa | docstring | closed - closed by bbbbbbb
- [ ] D2 | ccccccc | glossary | `first_look` says "sample"

## Reviewed commits

- aaaaaaa: D1
- ccccccc: D2
- ddddddd: clean
"""


def test_a_commit_command_is_recognised() -> None:
    assert MAKES_A_COMMIT.search('git commit -m "x"')
    assert MAKES_A_COMMIT.search("git -C repo merge dev")
    assert not MAKES_A_COMMIT.search("git status && git log --oneline")


def test_watched_paths_need_a_review_and_tracker_commits_do_not() -> None:
    changed = ["sql_composer/tables.py", ".scratch/drift.md", "CONTEXT.md", "tests/test_x.py"]
    assert needs_review(changed, "feat: x") == ["sql_composer/tables.py", "CONTEXT.md"]
    assert needs_review([".scratch/sql-composer-v2/map.md"], "docs(wayfinder): x") == []


def test_a_no_drift_commit_needs_a_review_even_off_the_watched_paths() -> None:
    assert needs_review(["tests/test_x.py"], "fix: x\n\nNo-drift: D2 - it was fine") == ["No-drift"]


def test_the_drift_list_is_read_without_its_examples() -> None:
    assert open_items(DRIFT_TEXT) == [("D2", "ccccccc")]
    assert reviewed_commits(DRIFT_TEXT) == ["aaaaaaa", "ccccccc", "ddddddd"]


def test_the_review_request_names_the_brief_and_the_commit() -> None:
    request = review_request("ccccccc0123456789", ["CONTEXT.md"])
    assert ".claude/hooks/drift-reviewer.md" in request
    assert "ccccccc" in request and "0123456789" not in request


def test_a_session_with_its_reviews_done_and_items_closed_may_stop() -> None:
    assert what_blocks(["aaaaaaa0000", "ddddddd"], DRIFT_TEXT) is None


def test_an_open_item_from_the_sessions_own_commit_blocks_stopping() -> None:
    why = what_blocks(["ccccccc"], DRIFT_TEXT)
    assert why is not None and "D2" in why


def test_an_unreviewed_commit_blocks_stopping() -> None:
    why = what_blocks(["eeeeeee"], DRIFT_TEXT)
    assert why is not None and "eeeeeee" in why and "D2" not in why


def test_switching_to_main_to_commit_is_refused_but_reading_is_not() -> None:
    assert refusal("Bash", {"command": "git checkout main && git commit -m x"}, str(ROOT))
    assert refusal("Bash", {"command": "git log main"}, str(ROOT)) is None


def test_the_export_script_run_alone_goes_through() -> None:
    for command in (
        "python tools/export_clean.py",
        "python tools\\export_clean.py",
        f'python "{ROOT.as_posix()}/tools/export_clean.py"',
        "python tools/export_clean.py --preview clean",
    ):
        assert refusal("Bash", {"command": command}, str(ROOT)) is None, command


def test_naming_the_export_script_does_not_excuse_a_commit_by_hand() -> None:
    command = "git checkout main && python tools/export_clean.py && git commit -m export"
    assert refusal("Bash", {"command": command}, str(ROOT))


def test_moving_main_by_hand_is_refused() -> None:
    for command in (
        "git update-ref refs/heads/main 1a2b3c4",
        "python tools/export_clean.py; git update-ref refs/heads/main HEAD",
        "git branch -f main dev",
    ):
        assert refusal("Bash", {"command": command}, str(ROOT)), command
    assert refusal("Bash", {"command": "git update-ref refs/heads/dev 1a2b3c4"}, str(ROOT)) is None
