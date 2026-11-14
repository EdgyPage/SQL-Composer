"""The history scrub's two jobs (evaluation system, ticket 10): the rules `git filter-repo` is
given, and the check of a rewritten history, read from `git fast-export`'s stream.

Both are tested on made-up text: a made-up user, a made-up email and a made-up stream, since
the suite runs no git of its own here.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))

import local_paths  # noqa: E402
import scrub_history  # noqa: E402

NAMES = ("zorbax",)


def a_stream(*parts: bytes) -> bytes:
    """A fast-export stream of `parts`, each a command whose data is written with its size."""
    return b"".join(parts)


def blob(mark: int, text: str) -> bytes:
    data = text.encode("utf-8")
    return b"blob\nmark :%d\ndata %d\n%s\n" % (mark, len(data), data)


def commit(mark: int, message: str, changes: str,
           author: str = "Jo <jo@example.com>") -> bytes:
    data = message.encode("utf-8")
    return (b"commit refs/heads/dev\nmark :%d\noriginal-oid %s\nauthor %s 1 +0000\n"
            b"committer %s 1 +0000\ndata %d\n%s\n%s\n"
            % (mark, b"%040d" % mark, author.encode(), author.encode(), len(data), data,
               changes.encode("utf-8")))


EMAILS = ("jo.zorb@mail.test",)


def scrubbed(text: str) -> str:
    """`text` as filter-repo's --replace-text would leave it, with the rules for NAMES and
    EMAILS."""
    rules = scrub_history.rules_text(NAMES, EMAILS)
    return scrub_history.scrubbed(text.encode("utf-8"), rules).decode("utf-8")


@pytest.mark.parametrize("text", [
    "C:\\Users\\zorbax\\Code\\repo\\tools\\x.py", "C:\\\\Users\\\\zorbax\\\\Code\\\\x.py",
    "C:/Users/zorbax/Code/x.py", "/c/Users/zorbax/Code/x.py", "c:\\users\\ZORBAX\\x",
    "/home/zorbax/x", "/Users/zorbax/x",
])
def test_a_user_path_keeps_its_shape_with_the_name_replaced(text: str) -> None:
    assert "<user folder>" in scrubbed(text)
    assert local_paths.findings_in(scrubbed(text), "x.md", NAMES) == []


@pytest.mark.parametrize(("text", "expected"), [
    ("C:\\Users\\zorbax\\AppData\\Local\\Temp\\claude\\ab12\\cd-34\\scratchpad\\t1\\x.py",
     "<scratchpad>\\t1\\x.py"),
    ("C:/Users/zorbax/AppData/Local/Temp/claude/ab12/cd-34/scratchpad/x.py",
     "<scratchpad>/x.py"),
    ("C:\\\\Users\\\\zorbax\\\\AppData\\\\Local\\\\Temp\\\\pytest-of-zorbax\\\\p0",
     "<temp>\\\\pytest-of-<user folder>\\\\p0"),
    ("C:\\Users\\zorbax\\AppData\\Roaming\\Code\\x", "<app data>\\Code\\x"),
])
def test_a_work_folder_of_the_user_is_one_placeholder(text: str, expected: str) -> None:
    assert scrubbed(text) == expected
    assert local_paths.findings_in(scrubbed(text), "x.md", NAMES) == []


def test_the_email_and_the_name_in_prose_are_replaced() -> None:
    assert scrubbed("Mail jo.zorb@mail.test, or ask zorbax.") == (
        "Mail <user email>, or ask <user folder>.")


@pytest.mark.parametrize("text", [
    "C:\\Users\\someone\\AppData\\Local\\Temp\\x", "/home/<user folder>/x", "AppData\\Local\\x",
    "zorbaxes and azorbax", "jo@example.com",
])
def test_text_not_naming_this_user_is_left_as_it_is(text: str) -> None:
    assert scrubbed(text) == text


def test_a_binary_file_is_left_as_filter_repo_leaves_it() -> None:
    rules = scrub_history.rules_text(NAMES, EMAILS)
    assert scrub_history.scrubbed(b"PK\0\0zorbax", rules) == b"PK\0\0zorbax"


def test_the_mailmap_gives_each_personal_email_the_noreply_address() -> None:
    emails = ["jo.zorb@mail.test", "1+Jo@users.noreply.github.com", "noreply@anthropic.com",
              "noreply@github.com", "jo.zorb@mail.test"]
    assert scrub_history.mailmap_text(emails) == (
        "<1+Jo@users.noreply.github.com> <jo.zorb@mail.test>\n")


def test_the_mailmap_takes_the_noreply_address_given() -> None:
    noreply = "2+Jo@users.noreply.github.com"
    assert scrub_history.mailmap_text(["jo.zorb@mail.test"], noreply) == (
        "<2+Jo@users.noreply.github.com> <jo.zorb@mail.test>\n")


def test_the_rules_are_written_under_the_folder_given(tmp_path: Path) -> None:
    emails = ["jo.zorb@mail.test", "1+Jo@users.noreply.github.com"]
    scrub_history.write_rules(tmp_path, emails, NAMES)
    assert (tmp_path / "paths.txt").read_text(encoding="utf-8").splitlines() == [
        ".scratch/usability-loop/runs/", ".scratch/usability-loop/results.md",
        ".scratch/copilot-eval/runs/", ".scratch/copilot-eval/memo/",
        ".scratch/copilot-eval/results.md",
    ]
    rules = (tmp_path / "replacements.txt").read_text(encoding="utf-8")
    assert scrub_history.scrubbed(b"zorbax, jo.zorb@mail.test", rules) == (
        b"<user folder>, <user email>")
    assert (tmp_path / "mailmap").read_text(encoding="utf-8") == (
        "<1+Jo@users.noreply.github.com> <jo.zorb@mail.test>\n")


def test_keeping_the_emails_writes_no_mailmap(tmp_path: Path) -> None:
    scrub_history.write_rules(tmp_path, ["jo.zorb@mail.test"], NAMES, keep_emails=True)
    assert sorted(path.name for path in tmp_path.iterdir()) == ["paths.txt", "replacements.txt"]


def test_the_summary_counts_each_kind_where_it_was_found() -> None:
    found = ["a.md:1 user path: C:/Users/zorbax", "a.md:1 user's folder name: zorbax",
             "b.md:4 user's folder name: zorbax", f"commit {'1' * 40} author:1 email: j@x.test",
             f"commit {'2' * 40} committer:1 email: j@x.test",
             f"tag {'3' * 40} message:2 email: j@x.test"]
    assert scrub_history.summary(found) == (
        "6 finding(s) in 2 file(s) and 3 commit(s) or tag(s):\n"
        "  1 in files: user path\n"
        "  2 in files: user's folder name\n"
        "  1 in messages: email\n"
        "  2 in name lines: email\n")


def test_the_summary_of_no_finding_says_so() -> None:
    assert scrub_history.summary([]) == "No local path or personal detail in any commit.\n"


def a_tree(folder: Path, files: dict[str, bytes]) -> Path:
    for name, data in files.items():
        (folder / name).parent.mkdir(parents=True, exist_ok=True)
        (folder / name).write_bytes(data)
    return folder


def test_a_tree_changed_only_by_the_rules_compares_clean(tmp_path: Path) -> None:
    rules = scrub_history.rules_text(NAMES, EMAILS)
    before = a_tree(tmp_path / "before", {
        "a.md": b"C:/Users/zorbax/x\n", "b.bin": b"\0zorbax", "c.md": b"plain\n",
        ".scratch/copilot-eval/memo/r.md": b"zorbax\n"})
    after = a_tree(tmp_path / "after", {
        "a.md": b"C:/Users/<user folder>/x\n", "b.bin": b"\0zorbax", "c.md": b"plain\n"})
    assert scrub_history.tree_differences(before, after, rules) == []


def test_a_tree_changed_otherwise_says_where(tmp_path: Path) -> None:
    rules = scrub_history.rules_text(NAMES, EMAILS)
    before = a_tree(tmp_path / "before", {"a.md": b"zorbax\n", "b.md": b"x\n", "c.md": b"c\n"})
    after = a_tree(tmp_path / "after", {"a.md": b"<user folder>\n", "b.md": b"y\n",
                                        "d.md": b"d\n"})
    assert scrub_history.tree_differences(before, after, rules) == [
        "b.md: not the scrubbed text", "c.md: gone", "d.md: new"]


def test_the_check_reads_the_stream_on_stdin_and_fails_on_a_finding(
        monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    stream = a_stream(blob(1, "see C:/Users/jo/x\n"), commit(2, "Add", "M 100644 :1 a.md"))
    monkeypatch.setattr(sys, "stdin", io.TextIOWrapper(io.BytesIO(stream)))
    assert scrub_history.main(["check"]) == 1
    assert capsys.readouterr().out == (
        "1 finding(s) in 1 file(s) and 0 commit(s) or tag(s):\n  1 in files: user path\n")


def test_the_hash_rules_give_each_rewritten_commit_its_new_hash() -> None:
    commit_map = ("old                                      new\n"
                  f"{'a' * 40} {'b' * 40}\n{'c' * 40} {'c' * 40}\n{'d' * 40} {'0' * 40}\n")
    assert scrub_history.hash_rules(commit_map) == f"{'a' * 40}==>{'b' * 40}\n"


def test_a_clean_stream_has_no_finding() -> None:
    stream = a_stream(blob(1, "plain text\n"), commit(2, "Add notes", "M 100644 :1 notes.md"))
    assert scrub_history.stream_findings(stream, NAMES) == []


def test_a_blob_holding_a_user_path_is_found_at_its_path() -> None:
    stream = a_stream(blob(1, "line one\nsee C:\\Users\\zorbax\\x.py\n"),
                      commit(2, "Add notes", "M 100644 :1 docs/notes.md"))
    assert scrub_history.stream_findings(stream, NAMES) == [
        "docs/notes.md:2 user path: C:\\Users\\zorbax",
        "docs/notes.md:2 user's folder name: zorbax",
    ]


def test_a_file_that_names_the_patterns_is_left_but_its_copy_elsewhere_is_not() -> None:
    stream = a_stream(blob(1, "C:/Users/zorbax/x\n"),
                      commit(2, "Add", "M 100644 :1 tools/local_paths.py"),
                      commit(3, "Copy", "M 100644 :1 notes/copy.py"))
    assert scrub_history.stream_findings(stream, NAMES) == [
        "notes/copy.py:1 user path: C:/Users/zorbax",
        "notes/copy.py:1 user's folder name: zorbax",
    ]


def test_an_old_file_that_names_no_one_is_left_for_its_kind_only() -> None:
    stream = a_stream(blob(1, "C:\\\\Users\\\\JOHNSM~1\\\\x\nzorbax\n"),
                      commit(2, "Add", "M 100644 :1 spark_composer/engine.py"))
    assert scrub_history.stream_findings(stream, NAMES) == [
        "spark_composer/engine.py:2 user's folder name: zorbax",
    ]


def test_githubs_own_committer_address_is_no_ones() -> None:
    stream = a_stream(blob(1, "plain\n"),
                      commit(2, "Merge", "M 100644 :1 a.md",
                             author="GitHub <noreply@github.com>"))
    assert scrub_history.stream_findings(stream, NAMES) == []


def test_a_path_holding_the_name_is_found_once() -> None:
    stream = a_stream(blob(1, "plain\n"),
                      commit(2, "Add", "M 100644 :1 notes/zorbax/a.md"),
                      commit(3, "Again", "M 100644 :1 notes/zorbax/a.md"))
    assert scrub_history.stream_findings(stream, NAMES) == [
        "notes/zorbax/a.md as a path:1 user's folder name: zorbax",
    ]


def test_a_quoted_path_is_read_unquoted() -> None:
    stream = a_stream(blob(1, "zorbax\n"),
                      commit(2, "Add", 'M 100644 :1 "docs/caf\\303\\251 \\"x\\".md"'))
    assert scrub_history.stream_findings(stream, NAMES) == [
        'docs/caf\u00e9 "x".md:1 user\'s folder name: zorbax',
    ]


def test_a_commit_message_and_its_author_and_committer_are_read() -> None:
    stream = a_stream(blob(1, "plain\n"),
                      commit(2, "Fix\n\nRan in /home/zorbax/repo", "M 100644 :1 a.md",
                             author="Jo <jo@mail.test>"))
    oid = "0" * 39 + "2"
    assert scrub_history.stream_findings(stream, NAMES) == [
        f"commit {oid} author:1 email: jo@mail.test",
        f"commit {oid} committer:1 email: jo@mail.test",
        f"commit {oid} message:3 user path: /home/zorbax",
        f"commit {oid} message:3 user's folder name: zorbax",
    ]


def test_a_tag_message_and_its_tagger_are_read() -> None:
    message = b"The last one, from jo@mail.test"
    stream = a_stream(blob(1, "plain\n"), commit(2, "Add", "M 100644 :1 a.md"),
                      b"tag last\nfrom :2\noriginal-oid %s\ntagger Jo <jo@mail.test> 1 +0000\n"
                      b"data %d\n%s\n" % (b"9" * 40, len(message), message))
    assert scrub_history.stream_findings(stream, NAMES) == [
        f"tag {'9' * 40} tagger:1 email: jo@mail.test",
        f"tag {'9' * 40} message:1 email: jo@mail.test",
    ]
