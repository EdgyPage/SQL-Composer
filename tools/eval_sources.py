"""Sources: the ids a reply cites, tied to its result (evaluation system, ticket 06).

Each proxy ends a reply with `Used: <ids>`, the patterns, rules and worked patterns of the
Copilot file it followed (`P3, R7, W1`; `11:F4` when it was given more than one file, so the
id's file is clear). A zero-context user ends its last message with `Read: <file> <section>,
...`. The scorers read those lines, and this module keeps each new reply's result with what it
cited in `.eval-local/sources.csv`, which git ignores. A reply with no such line is "no source",
which is a gap in the instructions to a proxy and never a failure of the reply.

    .venv/Scripts/python tools/eval_sources.py summary [--round NAME] [--pipeline NAME]

The summary ranks each cited id by how often failing replies cite it against passing replies,
lists the failing replies that cited nothing (a pattern the file lacks, or a Used line left
off), and flags each cited id the loaded file doesn't define.

An id is defined by a line of its file: a Patterns table row (`| P3 | ...`), a bullet (`- **R7**
...` or `- A1. ...`) or a worked pattern's heading (`### W1: ...`).
"""

from __future__ import annotations

import argparse
import csv
import re
from collections.abc import Callable
from dataclasses import dataclass, fields
from pathlib import Path

import eval_runs

SOURCES_NAME = "sources.csv"

# An id as a Copilot file writes it: one or two capitals and a number.
ID = re.compile(r"\b[A-Z]{1,2}\d+\b")
DEFINITIONS = (
    re.compile(r"^\| ([A-Z]{1,2}\d+) \|", re.MULTILINE),
    re.compile(r"^- \*\*([A-Z]{1,2}\d+)\*\*", re.MULTILINE),
    re.compile(r"^- ([A-Z]{1,2}\d+)[.:\s]", re.MULTILINE),
    re.compile(r"^### ([A-Z]{1,2}\d+)\b", re.MULTILINE),
)
# One of the lines a reply ends with: its label, then the rest of the line.
USED_LINE = re.compile(r"^[*_> \t]*Used[*_]*:[*_ \t]*(.*?)[ \t]*$",
                       re.MULTILINE | re.IGNORECASE)
READ_LINE = re.compile(r"^[*_> \t]*Read[*_]*:[*_ \t]*(.*?)[ \t]*$",
                       re.MULTILINE | re.IGNORECASE)
CITED = re.compile(r"(?:\b\d{2}:)?\b[A-Za-z]{1,2}\d+\b")

AMBIGUOUS = "*"
SEPARATOR = ";"
STATUSES = ("cited", "none", "no source")


def defined_ids(text: str) -> set[str]:
    """Each id a Copilot file defines, by its line's form."""
    found: set[str] = set()
    for pattern in DEFINITIONS:
        found.update(pattern.findall(text))
    return found


def used_ids(reply: str) -> list[str] | None:
    """The ids a reply's `Used:` lines name, each once, in order and upper-case, `11:F4` kept
    with its file; [] where the line says none; None where the reply has no such line."""
    lines = USED_LINE.findall(reply)
    if not lines:
        return None
    tokens = CITED.findall("\n".join(lines))
    return list(dict.fromkeys(token.upper() for token in tokens))


def read_items(reply: str) -> list[str] | None:
    """The `<file> <section>` items of a reply's `Read:` lines, each once, in order; None where
    the reply has no such line."""
    lines = READ_LINE.findall(reply)
    if not lines:
        return None
    items = [item.strip() for item in ",".join(lines).split(",")]
    return list(dict.fromkeys(item for item in items if item and item.lower() != "none"))


def without_source_lines(text: str) -> str:
    """The text with its `Used:` lines taken out, so a request or an answer is scored as it
    was without them."""
    return USED_LINE.sub("", text).rstrip() + ("\n" if text.endswith("\n") else "")


def resolve(tokens: list[str], loaded: dict[str, str]) -> tuple[list[str], list[str]]:
    """What a reply cited, by the files it was given (`loaded`, each file's number and text):
    the ids those files define, each as `<file>:<id>` (`*:<id>` where two files define it and
    the reply didn't say which), then the cited ids no loaded file defines, as cited."""
    defined = {number: defined_ids(text) for number, text in loaded.items()}
    cited, unknown = [], []
    for token in (one.upper() for one in tokens):
        number, _, one = token.rpartition(":")
        homes = [number] if number else [name for name, ids in defined.items() if one in ids]
        if number and one not in defined.get(number, set()):
            homes = []
        if not homes:
            unknown.append(token)
        else:
            cited.append(f"{homes[0] if len(homes) == 1 else AMBIGUOUS}:{one}")
    return list(dict.fromkeys(cited)), unknown


# --- The kept rows ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RunOf:
    """What a round's task was asked on, apart from its reply: when, in which round, which
    pipeline, task, arm and model, and the version of the files the round was given (`files`,
    the Copilot files' hash, or the inputs hash of a usability run)."""

    date: str
    round: str
    pipeline: str
    task: str
    arm: str
    model: str
    files: str


@dataclass(frozen=True)
class SourceRow:
    """One task's result with what its reply cited. `loaded` is the start of the hash of the
    text the task loaded; `status` is cited, none (a line saying none) or no source (no line);
    `cited` and `unknown` hold ids, or a usability run's `<file> <section>` items, apart by
    `;`."""

    date: str
    round: str
    pipeline: str
    task: str
    arm: str
    model: str
    result: str
    files: str
    loaded: str
    status: str
    cited: str
    unknown: str


SOURCE_FIELDS = [one.name for one in fields(SourceRow)]
HASH_START = 12


def _row(run: SourceRow | RunOf, passed: bool, loaded: str, status: str,
         cited: list[str], unknown: list[str]) -> SourceRow:
    return SourceRow(run.date, run.round, run.pipeline, run.task, run.arm, run.model,
                     "pass" if passed else "fail", run.files, loaded[:HASH_START], status,
                     SEPARATOR.join(cited), SEPARATOR.join(unknown))


def source_row(run: RunOf, passed: bool, reply: str, loaded: dict[str, str]) -> SourceRow:
    """A task's row, from its reply's `Used:` lines and the files the task was given."""
    loaded_hash = eval_runs.text_hash("".join(loaded.values()))
    tokens = used_ids(reply)
    if tokens is None:
        return _row(run, passed, loaded_hash, "no source", [], [])
    cited, unknown = resolve(tokens, loaded)
    return _row(run, passed, loaded_hash, "cited" if tokens else "none", cited, unknown)


def read_row(run: RunOf, passed: bool, reply: str, loaded: str) -> SourceRow:
    """A usability run's row, from its `Read:` lines; `loaded` is its inputs hash."""
    items = read_items(reply)
    if items is None:
        return _row(run, passed, loaded, "no source", [], [])
    return _row(run, passed, loaded, "cited" if items else "none", items, [])


def read_sources(local: Path = eval_runs.LOCAL) -> list[SourceRow]:
    """Every row kept, in the order kept; none where there is no file yet."""
    path = local / SOURCES_NAME
    if not path.is_file():
        return []
    with path.open(encoding="utf-8", newline="") as kept:
        return [SourceRow(**row) for row in csv.DictReader(kept)]


def keep_sources(rows: list[SourceRow], local: Path = eval_runs.LOCAL) -> Path:
    """Keep rows, each in place of the row kept before for the same task of the same round of
    the same pipeline."""
    path = eval_runs.make_local_path(SOURCES_NAME, local=local)
    replaced = {(one.pipeline, one.round, one.task) for one in rows}
    kept = [one for one in read_sources(local)
            if (one.pipeline, one.round, one.task) not in replaced]
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file, lineterminator="\n")
        writer.writerow(SOURCE_FIELDS)
        for one in [*kept, *rows]:
            writer.writerow([getattr(one, name) for name in SOURCE_FIELDS])
    return path


def keep_round(pipeline: str, header: dict[str, str], found: eval_runs.RoundReplies,
               passed: dict[str, bool], loaded_of: Callable[[str, str], dict[str, str]],
               local: Path) -> None:
    """Keep the sources of each reply a round asked anew, not one taken from the memo, which an
    earlier round kept. `passed` is each task's result and `loaded_of(arm, task)` the files its
    arm loaded, none for an arm that loads no Copilot file, which has no ids to cite."""
    arm = header["arm"]
    rows = []
    for task, reply in found.replies.items():
        loaded = loaded_of(arm, task)
        if task in found.taken or not loaded:
            continue
        run = RunOf(header.get("date", "?"), header.get("round", "-"), pipeline, task, arm,
                    header["model"], header.get("files", "?"))
        rows.append(source_row(run, passed[task], reply, loaded))
    if rows:
        keep_sources(rows, local)


# --- The attribution -------------------------------------------------------------------------


@dataclass
class Cited:
    """An id, and how many failing and how many passing replies cited it, of those that gave a
    source."""

    id: str
    failing: int
    passing: int
    failing_rate: int
    passing_rate: int


@dataclass
class Attribution:
    """A round's sources: the ids ranked, the replies behind them (those that gave a source),
    the failures that cited nothing, the replies with no source by result, and each cited id no
    loaded file defines."""

    ranked: list[Cited]
    failing_replies: int
    passing_replies: int
    uncited_failures: list[SourceRow]
    no_source: dict[str, int]
    unknown: list[tuple[str, str]]


def _percent(count: int, total: int) -> int:
    return round(100 * count / total) if total else 0


def attribute(rows: list[SourceRow]) -> Attribution:
    """Rank the ids of `rows` by the share of failing replies that cite them minus the share
    of passing replies that do, then by failing citations: the ids to look at first come first.
    A share is of the replies that gave a source line, which leaves out a reply with none."""
    sourced = [one for one in rows if one.status != "no source"]
    failing = [one for one in sourced if one.result == "fail"]
    passing = [one for one in sourced if one.result == "pass"]
    counts: dict[str, list[int]] = {}
    for one in sourced:
        for cited in (one.cited.split(SEPARATOR) if one.cited else []):
            counts.setdefault(cited, [0, 0])[0 if one.result == "fail" else 1] += 1
    ranked = [Cited(name, fail, ok, _percent(fail, len(failing)), _percent(ok, len(passing)))
              for name, (fail, ok) in counts.items()]
    ranked.sort(key=lambda one: (one.passing_rate - one.failing_rate, -one.failing, one.id))
    no_source = {"fail": 0, "pass": 0}
    unknown = []
    for one in rows:
        if one.status == "no source":
            no_source[one.result] += 1
        if one.unknown:
            unknown += [(one.task, flagged) for flagged in one.unknown.split(SEPARATOR)]
    uncited = [one for one in rows if one.result == "fail" and one.status != "cited"]
    return Attribution(ranked, len(failing), len(passing), uncited, no_source, unknown)


def summary_text(rows: list[SourceRow], round_name: str | None = None,
                 pipeline: str | None = None) -> str:
    """The attribution of a round's rows, or of every round's, as text for the report."""
    rows = [one for one in rows if round_name in (None, one.round)
            and pipeline in (None, one.pipeline)]
    scope = " ".join(part for part in (pipeline, round_name and f"round {round_name}") if part)
    if not rows:
        return f"No sources recorded{' for ' + scope if scope else ''}."
    found = attribute(rows)
    versions = sorted({one.loaded for one in rows})
    lines = [f"Sources{' of ' + scope if scope else ''}: {len(rows)} replies, "
             f"{found.failing_replies} failing and {found.passing_replies} passing gave a "
             f"source; loaded text {', '.join(versions)}.",
             "", "Ids ranked, failing replies citing them against passing replies:"]
    for one in found.ranked:
        lines.append(f"  {one.id}  {one.failing} failing ({one.failing_rate}%)  "
                     f"{one.passing} passing ({one.passing_rate}%)")
    if not found.ranked:
        lines.append("  none cited")
    lines += ["", f"Failures that cited nothing: {len(found.uncited_failures)}"]
    lines += [f"  {one.pipeline} {one.round} {one.task} ({one.status})"
              for one in found.uncited_failures]
    lines.append(f"Replies with no source line: {found.no_source['fail']} failing, "
                 f"{found.no_source['pass']} passing.")
    if found.unknown:
        lines += ["", "Cited, not defined by the file the task loaded:"]
        lines += [f"  {task}: {name}" for task, name in found.unknown]
    return "\n".join(lines)


# --- The command -----------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """Run `summary`, which prints the attribution of the kept rows."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    summary = commands.add_parser("summary", help="rank the cited ids by failing replies")
    summary.add_argument("--round", dest="round_name")
    summary.add_argument("--pipeline", choices=eval_runs.PIPELINES)
    summary.add_argument("--local", type=Path, default=eval_runs.LOCAL)
    given = parser.parse_args(argv)
    print(summary_text(read_sources(given.local), given.round_name, given.pipeline))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
