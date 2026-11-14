"""Score Copilot file 19, Metric request, offline, by the requirements each request holds
(Toolbox 8.7, tickets 11 and 17).

File 19 takes a user from a vague wish for a new metric to a Metric request: plain text, no SQL
and no worked numbers, that a chatbot knowing the user's databases writes the column from. This
measures it with two proxies per task (`tools/metric_eval_tasks.py`), each a small model in a
Claude session (`.claude/agents/metric-proxy.md`):

- the stand-in user, who pasted the column definitions, says the task's vague goal and answers
  from its secret answer key;
- Copilot, loaded with file 19 and given the column definitions, who asks one question at a
  time and writes the request.

The request is scored directly, by rules (`score_request`), for direction, not exactness: it
passes when it holds every essential element of its task's requirements key (the source
columns or the named gap, the grain and its conditions, anything the task marks), more of the
helpful elements than not, no invented column name and no worked-out number, and no SQL. The
baseline, arm A0, is the same Copilot given file 19's request form, the definitions and the
vague goal, with no file 19 and no one to ask.

    python tools/metric_eval.py plan C --split dev --model haiku
    python tools/metric_eval.py messages C --split dev --model haiku --into <run>
    python tools/metric_eval.py request <run>/M01
    python tools/metric_eval.py answers <run> --arm C --model haiku --files <hash> \\
        --memo-files <version> --into <run>/answers.md
    python tools/metric_eval.py score <run>/answers.md --split dev \\
        --record .scratch/copilot-eval/results.md

`messages` writes, for each task the round's plan names, a folder holding the messages the
proxies start from: in arm C user.md and copilot.md, in A0 copilot.md alone. In arm C the two
talk turn by turn, Copilot writing turn-01-copilot.md, the user turn-01-user.md, and so on,
until Copilot's turn holds the Metric request; in A0 Copilot writes turn-01-copilot.md alone.
`request` then writes the folder's transcript.md and request.md. `answers` gathers a round's
requests into one answers file, and `score` scores it, keeping each answer in the memo
(`tools/eval_memo.py`) as the Copilot evaluation does: a held-out task in arm C once per
version of the Copilot files.
"""

from __future__ import annotations

import argparse
import datetime
import functools
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT)]

import eval_memo  # noqa: E402
from copilot_eval import EXAMPLE_TABLES  # noqa: E402
from metric_eval_tasks import (  # noqa: E402
    BY_ID,
    COLUMN_DEFINITIONS,
    PARTS,
    TASKS,
    USER_RULES,
    MetricTask,
    Required,
)

import example_database  # noqa: E402
from sqlglot_composer.shared import counted  # noqa: E402

FILE_19 = ROOT / "copilot" / "19_metric_request.txt"

# SQL in a Metric request: a code block of it, or the words only SQL writes, in capitals.
SQL_IN_TEXT = re.compile(r"```(?:sql|hive|hql)\b|\bSELECT\b[^\n]*\bFROM\b|\bCASE\s+WHEN\b"
                         r"|\bGROUP\s+BY\b|\bJOIN\b[^\n]*\bON\b")
# Where a Metric request starts, and each column's section.
REQUEST_START = re.compile(r"^# Metric request\b", re.MULTILINE)
COLUMN = re.compile(r"^## Column: *(.+?) *$", re.MULTILINE)
# A part's first line: its number, its label, perhaps a note, then a colon.
PART_LINE = re.compile(rf"^\s*\d+\.\s*({'|'.join(PARTS)})\b[^:\n]*:", re.MULTILINE)
# A name as a column or table is written: words joined by underscores, perhaps after "ops.".
SNAKE_NAME = re.compile(r"\b(?:ops\.)?[a-z][a-z0-9]*(?:_[a-z0-9]+)+\b")
# A Fix, which may name a column to add, to the end of its line.
FIX_TEXT = re.compile(r"\bFix:[^\n]*", re.IGNORECASE)
# A worked-out number: "=" and a number alone, such as "100 x 1 / 2 = 50".
WORKED_NUMBER = re.compile(r"(?<![<>!=])=\s*-?\d[\d.,]*\s*(?:%|percent)?\s*(?:[.;,)]|$)", re.MULTILINE)


def holds_sql(request: str) -> bool:
    """Whether a Metric request holds SQL, which it never should: it is plain words and
    maths, for the chatbot to write the column from."""
    return SQL_IN_TEXT.search(request) is not None


def sections(request: str) -> list[tuple[str, str]]:
    """A Metric request's column sections, each its column's name and its body."""
    split = COLUMN.split(request)[1:]
    return list(zip(split[::2], split[1::2]))


def parts_of(body: str) -> dict[str, str]:
    """A column section's parts, by their labels, each its text to the next part."""
    found = list(PART_LINE.finditer(body))
    ends = [match.start() for match in found[1:]] + [len(body)]
    return {match.group(1): body[match.end():end] for match, end in zip(found, ends)}


def missing_parts(request: str) -> list[str]:
    """Each part a Metric request's column sections lack, as `<column>: <part>`, or that it
    has no column section at all."""
    if not sections(request):
        return ["a column section"]
    return [f"{name}: {part}" for name, body in sections(request)
            for part in PARTS if part not in parts_of(body)]


def request_in(message: str) -> str:
    """The Metric request in Copilot's message, from its heading on, or "" where it has
    none. A request inside a code block, as file 19's Output shows it, ends at the block's
    end."""
    found = REQUEST_START.search(message)
    if found is None:
        return ""
    request = message[found.start():]
    if message[:found.start()].rstrip().endswith("```text"):
        request = request.split("```", 1)[0]
    return request.strip() + "\n"


# --- What a request holds ------------------------------------------------------------------


@functools.cache
def example_names() -> frozenset[str]:
    """Every name of the Example database's tables and columns, `ops.job_runs` and
    `job_runs` both: the names the column definitions give."""
    names = set()
    for name in EXAMPLE_TABLES:
        table = getattr(example_database, name)
        names |= {table._name, table._name.split(".")[-1], *table._columns}
    return frozenset(names)


def invented_names(request: str) -> list[str]:
    """Each column or table name in a request that the definitions don't give and no column
    section names, outside a Fix, which may name a column to add."""
    named = {name.strip("` ") for name, _ in sections(request)}
    return sorted({name for name in SNAKE_NAME.findall(FIX_TEXT.sub("", request))
                   if name not in example_names() and name not in named})


def worked_numbers(request: str) -> list[str]:
    """Each number a request works out, such as "= 50": Copilot does no maths."""
    return [match.group(0).strip() for match in WORKED_NUMBER.finditer(request)]


def text_of(request: str, part: str) -> str:
    """The text a requirement reads: one part of every column section, or, for "", the
    whole request."""
    if not part:
        return request
    return "\n".join(parts_of(body).get(part, "") for _, body in sections(request))


def meets(request: str, required: Required) -> bool:
    """Whether a request holds a requirement: each pattern found in its part, or, where the
    requirement is `absent`, none."""
    text = text_of(request, required.part)
    found = [re.search(pattern, text, re.IGNORECASE) is not None
             for pattern in required.patterns]
    return not any(found) if required.absent else all(found)


def column_count(task: MetricTask) -> Required:
    """The requirement that a request has the task's number of column sections: essential
    where the user muddled their columns, helpful otherwise."""
    return Required(counted(task.columns, "column section"), "", (),
                    essential=bool(task.muddled))


@dataclass
class Score:
    """How a task's Metric request did, by its requirements key."""

    task: str
    request_missing: bool = False
    sql_in_request: bool = False
    parts_missing: list[str] = field(default_factory=list)
    essential_unmet: list[str] = field(default_factory=list)
    helpful_unmet: list[str] = field(default_factory=list)
    helpful_total: int = 0
    invented: list[str] = field(default_factory=list)
    worked: list[str] = field(default_factory=list)

    @property
    def helpful_met(self) -> int:
        """How many helpful elements the request holds."""
        return self.helpful_total - len(self.helpful_unmet)

    @property
    def holds_essential(self) -> bool:
        """Whether the request holds every essential element."""
        return not self.request_missing and not self.essential_unmet

    @property
    def passed(self) -> bool:
        """Whether the request heads the right way: every essential element, more helpful
        elements met than not, nothing invented, no number worked out, no SQL."""
        return (self.holds_essential and not self.sql_in_request and not self.invented
                and not self.worked and 2 * self.helpful_met > self.helpful_total)


def score_request(task: MetricTask, reply: str) -> Score:
    """Score the Metric request in a reply against its task's requirements key."""
    result = Score(task.id)
    request = request_in(reply)
    result.request_missing = not request
    result.sql_in_request = holds_sql(request)
    result.parts_missing = missing_parts(request)
    result.invented = invented_names(request)
    result.worked = worked_numbers(request)
    checks = [(column_count(task), len(sections(request)) == task.columns)]
    checks += [(required, meets(request, required)) for required in task.required]
    result.helpful_total = sum(not required.essential for required, _ in checks)
    for required, met in checks:
        if request and met:
            continue
        unmet = result.essential_unmet if required.essential else result.helpful_unmet
        unmet.append(required.what)
    return result


def score_line(result: Score) -> str:
    """A scored request in one line: pass or fail, its elements, and what it lacks."""
    notes = [f"helpful {result.helpful_met}/{result.helpful_total}"]
    if result.request_missing:
        notes.append("no Metric request")
    if result.essential_unmet:
        notes.append(f"lacks essential: {'; '.join(result.essential_unmet)}")
    if result.helpful_unmet and not result.request_missing:
        notes.append(f"lacks helpful: {'; '.join(result.helpful_unmet)}")
    if result.invented:
        notes.append(f"invents {', '.join(result.invented)}")
    if result.worked:
        notes.append(f"works out {', '.join(result.worked)}")
    if result.sql_in_request:
        notes.append("SQL in the request")
    if result.parts_missing and not result.request_missing:
        notes.append(f"parts missing: {', '.join(result.parts_missing)}")
    verdict = "pass" if result.passed else "fail"
    return f"{result.task}  {verdict}  {'  '.join(notes)}"


# --- The messages each proxy is given ----------------------------------------------------


def _quoted(text: str) -> str:
    """Text a message quotes, between <<< and >>>."""
    return f"<<<\n{text.rstrip()}\n>>>"


def user_message(task: MetricTask) -> str:
    """The stand-in user's message: the vague goal they said first, the column definitions
    they pasted, the answer key they keep from Copilot, and how they answer."""
    return (
        "You are standing in for a person at work, in a measurement of a Copilot file. You "
        "want a new metric, and you are asking Microsoft Copilot to help you say exactly what "
        "it is. You know your business; you know your tables only as their column "
        "definitions, which you pasted. Use no tools but the ones your prompt names.\n\n"
        "You pasted these column definitions:\n\n" + _quoted(COLUMN_DEFINITIONS)
        + "\n\nThen you said this to Copilot:\n\n" + _quoted(task.opening)
        + "\n\nYour answer key, which Copilot can't see. Answer its questions from it:\n\n"
        + _quoted(task.answer_key) + "\n\nHow you answer:\n\n" + USER_RULES)


def _copilot_start(loaded: str, task: MetricTask) -> str:
    """What Copilot is given first: a file or a form, then the definitions and the goal."""
    return (
        "You are standing in for Microsoft Copilot in a web chat. Use no tools but the ones "
        "your prompt names: answer from what is written here and what you already know.\n\n"
        + loaded + "The user pasted their column definitions:\n\n"
        + _quoted(COLUMN_DEFINITIONS) + "\n\nThen they sent:\n\n" + _quoted(task.opening))


def copilot_message(task: MetricTask) -> str:
    """The grilling proxy's first message: file 19, pasted first, then the column
    definitions and the user's vague goal."""
    loaded = ("The user pasted this as their first message:\n\n"
              + _quoted(FILE_19.read_text(encoding="utf-8")) + "\n\n")
    return _copilot_start(loaded, task) + "\n\nReply as Copilot, following the file."


def request_form() -> str:
    """File 19's form of a Metric request, its first ```text block."""
    found = re.search(r"```text\n(# Metric request:.*?)```", FILE_19.read_text(encoding="utf-8"),
                      re.DOTALL)
    return found.group(1) if found else ""


A0_INSTRUCTIONS = ("The user wants a Metric request: plain text, no SQL, that their chatbot, "
                   "which knows their databases, writes the new column from. Its form:\n\n")


def baseline_message(task: MetricTask) -> str:
    """The baseline's message: the request's form, the definitions and the vague goal, and no
    one to ask."""
    loaded = A0_INSTRUCTIONS + _quoted(request_form()) + "\n\n"
    return (_copilot_start(loaded, task) + "\n\nReply as Copilot with the Metric request, in "
            "its form, now: the user can't answer questions.")


# --- The memo ------------------------------------------------------------------------------

# The arms: Copilot given the request's form alone, or file 19 and the user to ask.
ARMS = {"A0": "the request's form, the definitions and the vague goal, no one to ask",
        "C": "the goal grilled with Copilot file 19 and the definitions"}


def memo_key(task_id: str, reply: str, arm: str, model: str, files: str) -> eval_memo.Key:
    """The key a task's reply is kept under in the memo (`tools/eval_memo.py`): in arm C the
    stand-in user's message, which holds the column definitions, with file 19 and the
    definitions, and a held-out task's Copilot files version `files`; in A0 the vague goal,
    with the baseline's form and the definitions. `reply` is unused, but `eval_memo` gives every
    tool's key function one: the loaded text never depends on it."""
    task = BY_ID[task_id]
    if arm == "C":
        task_text = user_message(task)
        loaded = FILE_19.read_text(encoding="utf-8") + COLUMN_DEFINITIONS
    else:
        task_text, loaded = task.opening, A0_INSTRUCTIONS + request_form() + COLUMN_DEFINITIONS
    if task.split != "held_out" or arm != "C":
        files = eval_memo.NO_FILES_VERSION
    return eval_memo.hashed_key(task_id, task_text, arm, model, loaded, files)


# --- A round's folders ---------------------------------------------------------------------


def write_task_messages(task: MetricTask, arm: str, folder: Path) -> None:
    """Write the messages a task's proxies start from into its folder: copilot.md, and in arm
    C the stand-in user's, user.md."""
    folder.mkdir(parents=True, exist_ok=True)
    if arm == "C":
        (folder / "user.md").write_text(user_message(task), encoding="utf-8")
        (folder / "copilot.md").write_text(copilot_message(task), encoding="utf-8")
    else:
        (folder / "copilot.md").write_text(baseline_message(task), encoding="utf-8")


# A task's turn file: turn-01-copilot.md, then turn-01-user.md, and so on.
TURN = re.compile(r"^turn-(\d+)-(copilot|user)\.md$")
# Who speaks in a turn, by the turn file's last part, in the transcript's words.
SPEAKERS = {"copilot": "Copilot", "user": "User"}


def _turns(folder: Path) -> list[tuple[str, Path]]:
    """A task's turns, in order, each its speaker and its file: Copilot's turn 1, the user's
    turn 1, Copilot's turn 2, and so on."""
    turns = []
    for path in folder.iterdir():
        named = TURN.match(path.name)
        if named is not None:
            turns.append((int(named.group(1)), named.group(2) == "user",
                          SPEAKERS[named.group(2)], path))
    return [(speaker, path) for _, _, speaker, path in sorted(turns)]


def write_request(folder: Path) -> None:
    """From a task's turns, write its transcript.md and the Metric request in Copilot's last
    turn as request.md."""
    turns = _turns(folder)
    transcript = [f"{speaker}:\n\n{path.read_text(encoding='utf-8').strip()}\n"
                  for speaker, path in turns]
    (folder / "transcript.md").write_text("\n".join(transcript), encoding="utf-8")
    copilots = [path for speaker, path in turns if speaker == "Copilot"]
    request = request_in(copilots[-1].read_text(encoding="utf-8")) if copilots else ""
    (folder / "request.md").write_text(request, encoding="utf-8")


def answers_text(run: Path, header: dict[str, str]) -> str:
    """A round's answers file, from its task folders: the header, then each task's
    request.md."""
    parts = ["\n".join(f"{name}: {value}" for name, value in header.items()) + "\n"]
    for folder in sorted(path for path in run.iterdir() if path.name in BY_ID):
        request = (folder / "request.md").read_text(encoding="utf-8").strip()
        parts.append(f"## {folder.name}\n\n{request}\n")
    return "\n".join(parts)


# --- The round's plan and its score --------------------------------------------------------


def _round_tasks(split: str) -> list[tuple[str, bool]]:
    """The tasks of a split, each with whether it is held out."""
    return [(task.id, task.split == "held_out") for task in TASKS
            if split in ("all", task.split)]


def write_round_messages(given: argparse.Namespace, asked: list[str]) -> str:
    """Write the messages of each task a round's plan says to ask into its folder in
    `--into`, and say which were written."""
    for task in asked:
        write_task_messages(BY_ID[task], given.arm, given.into / task)
    return f"Wrote the messages of {', '.join(asked)}."


RESULTS_HEADING = ("## Metric requests by their requirements, Copilot file 19 "
                   "(`tools/metric_eval.py`, ticket 17)")
RESULTS_TABLE = (
    "\n\n" + RESULTS_HEADING + "\n\n"
    "One row per scored answers file. Arms: A0 Copilot given the request's form, the column "
    "definitions and the vague goal, no one to ask; C the goal grilled by a proxy loaded with "
    "file 19 and the definitions. \"passed\" holds every essential element, more helpful "
    "elements than not, nothing invented, no number worked out and no SQL; \"essential\" the "
    "share holding every essential element; \"helpful\" the share of helpful elements held; "
    "\"invented\" counts requests with an invented name or a worked number.\n\n"
    "| date | files | model | arm | split | passed | essential | helpful | invented | with SQL "
    "| per task | from memo |\n"
    "|---|---|---|---|---|---|---|---|---|---|---|---|\n")


def _percent(count: int, total: int) -> int:
    """A count as a whole percent of a total."""
    return round(100 * count / total) if total else 0


def results_row(header: dict[str, str], split: str, results: list[Score],
                from_memo: int) -> str:
    """A round's row of the results table."""
    total = len(results)
    helpful = _percent(sum(one.helpful_met for one in results),
                       sum(one.helpful_total for one in results))
    invented = sum(bool(one.invented or one.worked) for one in results)
    per_task = " ".join(f"{one.task}:{'pass' if one.passed else 'fail'}" for one in results)
    cells = [header.get("date", ""), header.get("files", ""), header["model"], header["arm"],
             split, str(_percent(sum(one.passed for one in results), total)),
             str(_percent(sum(one.holds_essential for one in results), total)), str(helpful),
             str(invented), str(sum(one.sql_in_request for one in results)), per_task,
             str(from_memo)]
    return "| " + " | ".join(cells) + " |"


def record_row(record: Path, row: str) -> None:
    """Add a row to the results file's Metric request table, starting the table if it has
    none."""
    text = record.read_text(encoding="utf-8") if record.exists() else ""
    if RESULTS_HEADING not in text:
        text = text.rstrip("\n") + RESULTS_TABLE
    record.write_text(text.rstrip("\n") + "\n" + row + "\n", encoding="utf-8")


def score_answers(answers: Path, split: str, memo: Path, record: Path | None) -> str:
    """Score an answers file's round, with its tasks' kept replies, keep each in the memo, and
    record its row: the report, a line per task."""
    header, answered = eval_memo.read_answers(answers.read_text(encoding="utf-8"), "M")
    tasks = [task for task, _ in _round_tasks(split)]
    replies = eval_memo.round_replies(header, answered, tasks, memo_key, list(ARMS), memo)
    results = [score_request(BY_ID[task], reply) for task, reply in replies.replies.items()]
    lines = [score_line(one) for one in results]
    eval_memo.keep_round(replies, {one.task: line for one, line in zip(results, lines)},
                         header.get("date", ""))
    if record is not None:
        record_row(record, results_row(header, split, results, len(replies.taken)))
    return "\n".join([*lines, eval_memo.memo_line(replies)])


# --- The commands --------------------------------------------------------------------------


def _parser() -> argparse.ArgumentParser:
    """The commands: plan, messages, request, answers and score."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "messages"):
        command = commands.add_parser(name)
        command.add_argument("arm", choices=list(ARMS))
        command.add_argument("--split", choices=["dev", "held_out", "all"], default="dev")
        command.add_argument("--model", required=True)
        command.add_argument("--fresh", action="store_true")
        command.add_argument("--memo", type=Path, default=eval_memo.MEMO)
        if name == "messages":
            command.add_argument("--into", type=Path, required=True)
    commands.add_parser("request").add_argument("folder", type=Path)
    answers = commands.add_parser("answers")
    answers.add_argument("run", type=Path)
    answers.add_argument("--arm", choices=list(ARMS), required=True)
    answers.add_argument("--model", required=True)
    answers.add_argument("--files", required=True, help="git rev-parse --short HEAD:copilot")
    answers.add_argument("--memo-files", default="", help="the files version plan printed")
    answers.add_argument("--into", type=Path, required=True)
    scoring = commands.add_parser("score")
    scoring.add_argument("answers", type=Path)
    scoring.add_argument("--split", choices=["dev", "held_out", "all"], required=True)
    scoring.add_argument("--memo", type=Path, default=eval_memo.MEMO)
    scoring.add_argument("--record", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run one command."""
    given = _parser().parse_args(argv)
    if given.command in ("plan", "messages"):
        eval_memo.print_round(_round_tasks(given.split), memo_key, given,
                              functools.partial(write_round_messages, given))
    elif given.command == "request":
        write_request(given.folder)
    elif given.command == "answers":
        header = {"date": datetime.date.today().isoformat(), "arm": given.arm,
                  "model": given.model, "files": given.files}
        if given.memo_files:
            header[eval_memo.FILES_HEADER] = given.memo_files
        given.into.write_text(answers_text(given.run, header), encoding="utf-8")
    else:
        print(score_answers(given.answers, given.split, given.memo, given.record))
    return 0


if __name__ == "__main__":
    sys.exit(main())
