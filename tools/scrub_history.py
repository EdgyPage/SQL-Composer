"""The history scrub (evaluation system, ticket 10): the rules `git filter-repo` rewrites the
history with, and the check of what it wrote.

The user: "add to the tickets a scrubbing of the git history to take out my file paths and other
pii from the git history." Ticket 02 keeps new records and paths out of git; this takes the old
ones out of every commit. The procedure, which the user runs once on the final history, is in
`.scratch/eval-system/issues/10-scrub-history.md`. This file only reads and writes text: git
and `git filter-repo` are run by hand, and their output is piped in.

- `rules` writes what filter-repo is given, under the git-ignored `.eval-local/scrub/`, since it
  names the user: the record paths to remove, the replacements for file text and commit
  messages, and the mailmap for the authors' emails.
- `check` reads `git fast-export --all --show-original-ids` on stdin and reports each local
  path or personal detail in any blob, commit message or name line, by `tools/local_paths.py`'s
  rules.
- `compare` reads a branch's tree before and after (as `git archive` gives them) and names each
  file that isn't the old file scrubbed by the rules.

    git log --all --format=%ae%n%ce | .venv/Scripts/python tools/scrub_history.py rules
    git fast-export --all --show-original-ids | .venv/Scripts/python tools/scrub_history.py \
        check
    .venv/Scripts/python tools/scrub_history.py compare <before folder> <after folder>

The whole procedure, with the tagger's email, filter-repo's command and the checks, is the
ticket's.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path

import eval_runs
import local_paths

# Where the rules go: they name the user, so they stay on this computer.
LOCAL_RULES = eval_runs.LOCAL / "scrub"

# The records ticket 02 untracked, removed from every commit (filter-repo's --invert-paths).
RECORD_PATHS = (
    ".scratch/usability-loop/runs/",
    ".scratch/usability-loop/results.md",
    ".scratch/copilot-eval/runs/",
    ".scratch/copilot-eval/memo/",
    ".scratch/copilot-eval/results.md",
)

# Old files whose past versions hold a path that names no one, which the check leaves, by the
# one kind of finding each holds: the dropped Spark Composer's made-up users (a Windows short
# name, and a test's folder name with symbols in it), and notes that spoke of a work folder
# with no folder above it. The user's folder name and email are still found in them.
HISTORY_LEFT = {
    "spark_composer/engine.py": "user path",
    "tests/spark_edition/test_spark_example_database.py": "user path",
    ".scratch/sql-composer-v2/reports/22-beginner-reader.md": "work folder",
    ".scratch/spark-edition/reports/23-beginner-reader.md": "work folder",
    ".scratch/toolbox-5/orchestration.md": "work folder",
    ".scratch/eval-system/issues/02-records-local-only.md": "work folder",
}

_NOREPLY_DOMAIN = "users.noreply.github.com"
_SEPARATOR = r"[\\/]{1,2}"
_WORD_EDGE = "A-Za-z0-9"
# How much of a file filter-repo reads for a zero byte, which makes the file binary.
_BINARY_PROBE_BYTES = 8192


def personal_emails(emails: Iterable[str]) -> list[str]:
    """Each address in `emails` that is a person's: not at an example domain, nor Claude's,
    nor GitHub's, in order, once each."""
    personal = [email for email in emails if "@" in email
                and email.rsplit("@", 1)[1].lower() not in local_paths.EXAMPLE_DOMAINS
                and email.lower() != local_paths.GITHUB_COMMITTER]
    return list(dict.fromkeys(personal))


def rules_text(names: Sequence[str], emails: Iterable[str]) -> str:
    """The expressions for filter-repo's --replace-text and --replace-message, one per line,
    each a regex applied in turn: each of `emails` becomes `<user email>`; a work folder under
    a user folder of `names` becomes `<scratchpad>`, `<temp>` or `<app data>`; and each of
    `names` left, as a word, becomes `<user folder>`, so `C:\\Users\\<name>\\x` keeps its
    shape. They name the user, so they are kept under `.eval-local/`, never in git."""
    lines = [f"regex:(?i){re.escape(email)}==><user email>" for email in emails]
    for name in names:
        user_folder = (rf"(?:[A-Za-z]:|/[A-Za-z])?{_SEPARATOR}(?:Users|home){_SEPARATOR}"
                       rf"{re.escape(name)}{_SEPARATOR}AppData{_SEPARATOR}")
        lines += [
            rf"regex:(?i){user_folder}Local{_SEPARATOR}Temp{_SEPARATOR}claude"
            rf"(?:{_SEPARATOR}[\w-]+){{0,2}}{_SEPARATOR}scratchpad==><scratchpad>",
            rf"regex:(?i){user_folder}Local{_SEPARATOR}Temp(?![{_WORD_EDGE}])==><temp>",
            rf"regex:(?i){user_folder}(?:LocalLow|Local|Roaming)(?![{_WORD_EDGE}])"
            "==><app data>",
        ]
    lines += [rf"regex:(?i)(?<![{_WORD_EDGE}]){re.escape(name)}(?![{_WORD_EDGE}])"
              "==><user folder>" for name in names]
    return "".join(line + "\n" for line in lines)


def scrubbed(data: bytes, rules: str) -> bytes:
    """A file's `data` as filter-repo's --replace-text leaves it given `rules`, a file of
    `regex:` lines: each line's regex replaced in turn, unless the file is binary (a zero byte
    in its first 8 KiB), which filter-repo leaves as it is."""
    if b"\0" in data[:_BINARY_PROBE_BYTES]:
        return data
    for line in rules.encode("utf-8").splitlines():
        pattern, replacement = line[len(b"regex:"):].rsplit(b"==>", 1)
        data = re.sub(pattern, replacement, data)
    return data


def _files_under(folder: Path) -> dict[str, Path]:
    """Each file under `folder`, by its path relative to it, with forward slashes."""
    return {path.relative_to(folder).as_posix(): path
            for path in folder.rglob("*") if path.is_file()}


def tree_differences(before: Path, after: Path, rules: str) -> list[str]:
    """Each file of the `after` folder that isn't the `before` folder's file scrubbed by
    `rules`, as `path: why`: a file not the scrubbed text, gone, or new. A record path is
    expected to be gone."""
    old, new = _files_under(before), _files_under(after)
    expected = [path for path in old if not path.startswith(RECORD_PATHS)]
    differences = [f"{path}: gone" for path in expected if path not in new]
    differences += [f"{path}: new" for path in new if path not in old]
    differences += [f"{path}: not the scrubbed text" for path in expected if path in new
                    and new[path].read_bytes() != scrubbed(old[path].read_bytes(), rules)]
    return sorted(differences)


def mailmap_text(emails: Iterable[str], noreply: str | None = None) -> str:
    """A mailmap giving each personal address in `emails` the `noreply` address, which is by
    default the one GitHub address of the form `<id>+<login>@users.noreply.github.com` among
    `emails`. Each name stays as it is."""
    emails = list(emails)
    if noreply is None:
        found = list(dict.fromkeys(email for email in emails
                                   if email.lower().endswith("@" + _NOREPLY_DOMAIN)))
        if len(found) != 1:
            raise SystemExit(f"Found {len(found)} GitHub noreply addresses in the history, "
                             "not one: give the one to use with --noreply.")
        noreply = found[0]
    return "".join(f"<{noreply}> <{email}>\n" for email in personal_emails(emails))


# What a backslash and the letter after it stand for in a path git quotes (git's quote.c).
_ESCAPES = {b"a": b"\a", b"b": b"\b", b"f": b"\f", b"n": b"\n", b"r": b"\r", b"t": b"\t",
            b"v": b"\v", b"\\": b"\\", b'"': b'"'}
_ESCAPE = re.compile(rb"\\([0-7]{3}|.)")


def hash_rules(commit_map: str) -> str:
    """Literal rules for filter-repo's --replace-message from its `filter-repo/commit-map`
    (a header, then `old new` a line): each old full hash becomes its new one. The first pass
    rewrites a hash only of a commit it has already written, so main's "Generated from dev
    <hash>" stamps, which name commits on another line of history, need this second pass."""
    pairs = [line.split() for line in commit_map.splitlines()[1:]]
    return "".join(f"{old}==>{new}\n" for old, new in pairs
                   if old != new and new.strip("0"))


def _escaped_byte(match: re.Match[bytes]) -> bytes:
    """The byte one escape in a quoted path stands for: a letter's, or three octal digits'."""
    escape = match.group(1)
    if escape in _ESCAPES:
        return _ESCAPES[escape]
    return bytes([int(escape, 8)])


def unquoted(path: bytes) -> str:
    """A path as fast-export writes it, in double quotes with C escapes when it holds a quote,
    a backslash, a control character or a byte outside ASCII, read back as text."""
    if path.startswith(b'"') and path.endswith(b'"'):
        path = _ESCAPE.sub(_escaped_byte, path[1:-1])
    return path.decode("utf-8", errors="replace")


def stream_findings(stream: bytes, names: Iterable[str] | None = None,
                    keep_emails: bool = False) -> list[str]:
    """Each local path or personal detail in a fast-export `stream`: in a blob, as
    `path:line kind: text` at the first path that holds it; in a file's path itself, as
    `path as a path:1 kind: text`; in a commit's or a tag's message, or its author, committer
    or tagger line, as `commit <id> message:line kind: text`. With `keep_emails` (the user's
    answer (b)), an email in an author, committer or tagger line is not a finding; one in a
    file or a message still is."""
    names = local_paths.own_names() if names is None else tuple(names)
    blob_findings: dict[str, list[str]] = {}
    reported: set[str] = set()
    paths_read: set[str] = set()
    found: list[str] = []
    command = mark = oid = ""
    for word, line, data in stream_lines(stream):
        if word in ("blob", "commit", "tag"):
            command, mark, oid = word, "", ""
        elif word == "mark":
            mark = line[5:].decode("utf-8")
        elif word == "original-oid":
            oid = line[13:].decode("utf-8")
        elif word in ("author", "committer", "tagger"):
            found += identity_findings(line, f"{command} {oid} {word}", names, keep_emails)
        elif word == "data" and command == "blob":
            blob_findings[mark] = local_paths.findings_in(data, "", names)
        elif word == "data":
            found += local_paths.findings_in(data, f"{command} {oid} message", names)
        elif word == "M":
            _, _, data_reference, quoted = line.split(b" ", 3)
            reference, path = data_reference.decode("utf-8"), unquoted(quoted)
            paths_read.add(path)
            at_path = findings_at(path, blob_findings.get(reference, []))
            if at_path and reference not in reported:
                found += at_path
                reported.add(reference)
    return found + path_findings(paths_read, names)


def path_findings(paths: Iterable[str], names: Iterable[str]) -> list[str]:
    """The findings in each of `paths` itself, in order, as `path as a path:1 kind: text`."""
    found: list[str] = []
    for path in sorted(paths):
        found += local_paths.findings_in(path, f"{path} as a path", names)
    return found


def stream_lines(stream: bytes) -> Iterator[tuple[str, bytes, str]]:
    """Each line of a fast-export `stream` as its first word, the line, and, for a `data` line,
    the data after it as text ("" if it isn't UTF-8, or for any other line)."""
    position = 0
    while position < len(stream):
        end = stream.find(b"\n", position)
        if end < 0:
            end = len(stream)
        line = stream[position:end]
        position = end + 1
        word = line.split(b" ", 1)[0].decode("utf-8")
        data = ""
        if word == "data":
            size = int(line[5:])
            data = local_paths.text_of(stream[position:position + size]) or ""
            position += size
        yield word, line, data


def identity_findings(line: bytes, where: str, names: Iterable[str],
                      keep_emails: bool = False) -> list[str]:
    """The findings in an author, committer or tagger `line`'s name and email, none for
    GitHub's own committer address, and none for its email when the emails are kept."""
    identity = line.decode("utf-8").rsplit(">", 1)[0] + ">"
    if identity.lower().endswith(f"<{local_paths.GITHUB_COMMITTER}>"):
        return []
    if keep_emails:
        identity = identity.rsplit("<", 1)[0]
    return local_paths.findings_in(identity, where, names)


_FINDING = re.compile(r"^(?P<where>.*?):\d+ (?P<kind>[^:]+): ")


def summary(found: list[str]) -> str:
    """How many findings of each kind there are in files, in messages and in name lines
    (author, committer, tagger), with no path and no text: what a report may quote."""
    if not found:
        return "No local path or personal detail in any commit.\n"
    counts: dict[tuple[str, str], int] = {}
    files: set[str] = set()
    commits: set[str] = set()
    for finding in found:
        match = _FINDING.match(finding)
        where, kind = match.group("where"), match.group("kind")
        if where.startswith(("commit ", "tag ")):
            commits.add(where.split(" ")[1])
            if where.endswith(" message"):
                part = "messages"
            else:
                part = "name lines"
        else:
            files.add(where)
            part = "files"
        counts[(part, kind)] = counts.get((part, kind), 0) + 1
    lines = [f"  {count} in {part}: {kind}\n" for (part, kind), count in sorted(counts.items())]
    return (f"{len(found)} finding(s) in {len(files)} file(s) and {len(commits)} commit(s) or "
            "tag(s):\n" + "".join(lines))


def write_rules(folder: Path, emails: Iterable[str], names: Sequence[str],
                noreply: str | None = None, keep_emails: bool = False) -> None:
    """Write what filter-repo is given into `folder`: `paths.txt`, the record paths;
    `replacements.txt`, the rules for `names` and the personal addresses among `emails`; and,
    unless the authors keep their emails, `mailmap`."""
    emails = list(emails)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "paths.txt").write_text("".join(path + "\n" for path in RECORD_PATHS),
                                      encoding="utf-8")
    (folder / "replacements.txt").write_text(rules_text(names, personal_emails(emails)),
                                             encoding="utf-8")
    if not keep_emails:
        (folder / "mailmap").write_text(mailmap_text(emails, noreply), encoding="utf-8")


def findings_at(path: str, findings: list[str]) -> list[str]:
    """A blob's `findings` (each `:line kind: text`) where `path` holds it: none in a file that
    names the patterns, and none of the kind `HISTORY_LEFT` leaves in an old file."""
    if path in local_paths.NAMES_THE_PATTERNS:
        return []
    return [path + finding for finding in findings
            if finding.split(" ", 1)[1].split(":", 1)[0] != HISTORY_LEFT.get(path)]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    rules = commands.add_parser("rules", help="write what filter-repo is given, from the "
                                "authors' and committers' emails on stdin, one a line")
    rules.add_argument("--out", type=Path, default=LOCAL_RULES,
                       help="the folder to write into (default .eval-local/scrub/)")
    rules.add_argument("--noreply", help="the address each personal email becomes "
                       "(default: the one GitHub noreply address in the history)")
    rules.add_argument("--keep-emails", action="store_true",
                       help="leave the authors' and committers' emails as they are")
    check = commands.add_parser("check", help="read `git fast-export --all "
                                "--show-original-ids` on stdin and count what it finds")
    check.add_argument("--list", action="store_true", help="print each finding too")
    check.add_argument("--keep-emails", action="store_true",
                       help="an author's, committer's or tagger's email is no finding, as "
                       "`rules --keep-emails` leaves it")
    compare = commands.add_parser("compare", help="say each file of a rewritten tree that "
                                  "isn't the old tree's file scrubbed by the rules")
    compare.add_argument("before", type=Path, help="the old tree, as `git archive` gives it")
    compare.add_argument("after", type=Path, help="the rewritten tree")
    compare.add_argument("--rules", type=Path, default=LOCAL_RULES / "replacements.txt",
                         help="the replacements filter-repo was given")
    commands.add_parser("hashes", help="print the second pass's rules from filter-repo's "
                        "commit-map on stdin")
    given = parser.parse_args(argv)
    if given.command == "hashes":
        print(hash_rules(sys.stdin.read()), end="")
        return 0
    if given.command == "compare":
        differences = tree_differences(given.before, given.after,
                                       given.rules.read_text(encoding="utf-8"))
        print("".join(difference + "\n" for difference in differences)
              + f"{len(differences)} file(s) differ but for the scrubbed text.")
        return 1 if differences else 0
    if given.command == "rules":
        emails = [email.strip("<>") for email in sys.stdin.read().split()]
        write_rules(given.out, emails, local_paths.own_names(),
                    given.noreply, given.keep_emails)
        print(f"Wrote paths.txt, replacements.txt and, unless the emails are kept, mailmap "
              f"into {given.out}.")
        return 0
    found = stream_findings(sys.stdin.buffer.read(), keep_emails=given.keep_emails)
    if given.list:
        print("".join(finding + "\n" for finding in found), end="")
    print(summary(found), end="")
    return 1 if found else 0


if __name__ == "__main__":
    raise SystemExit(main())
