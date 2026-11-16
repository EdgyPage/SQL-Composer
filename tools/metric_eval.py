"""Score Copilot file 19, Metric request, offline, by the requirements each request holds
(Toolbox 8.7, tickets 11 and 17; run by script on `tools/eval_runs.py`, evaluation system,
ticket 04).

File 19 takes a user from a vague wish for a new metric to a Metric request: plain text, no SQL
and no worked numbers, that a chatbot knowing the user's databases writes the column from. This
measures it with two agents per task (`tools/metric_eval_tasks.py`), each a small model in a
Claude session (`.claude/agents/metric-proxy.md`):

- the stand-in user, who pasted the column definitions, says the task's vague goal and answers
  from its secret answer key;
- Copilot, loaded with file 19 and given the column definitions, who asks one question at a
  time and writes the request.

A conversation is those two agents, each spawned once with its first message and continued with
SendMessage for the turns after, so each keeps what it has read. The script writes each turn's
message into the task's folder, reads each reply, and ends the conversation when Copilot's turn
holds a request or after Copilot's turns reach the metric cap in `eval_runs.CAPS`. The
request is scored directly, by rules (`score_request`), for direction, not exactness: it
passes when it holds every essential element of its task's requirements key, more of the
helpful elements than not, no invented column name and no worked-out number, and no SQL. The
baseline, arm A0, is the same Copilot given file 19's request form, the definitions and the
vague goal, with no file 19 and no one to ask.

Everything is under `.eval-local/` (git-ignored): a round's folders in `metric/<round>/<task>/`,
the results table in `metric/results.md`, the replies in the memo and each agent's usage in the
ledger.

    .venv/Scripts/python tools/metric_eval.py plan C --split dev --model haiku
    .venv/Scripts/python tools/metric_eval.py start C --round r1 --split dev --model haiku
    .venv/Scripts/python tools/metric_eval.py next <task folder>
    .venv/Scripts/python tools/metric_eval.py usage <task folder> --role copilot --tokens N \\
        --seconds S
    .venv/Scripts/python tools/metric_eval.py score r1 C --split dev --model haiku

`start` writes each asked task's folder (user.md and copilot.md, or in A0 copilot.md alone) and,
for each, what the session spawns first. `next` reads the folder's newest turn and prints the
one thing to do: spawn the user's agent, or send a turn to an agent already spawned, each
naming the agent type, the model and the files to read and write; at the end it writes
transcript.md and request.md. `usage` records one agent's reported usage in the ledger. `score`
scores the round's requests, taking a task with no folder from the memo, and records its row.
"""

from __future__ import annotations

import argparse
import datetime
import functools
import json
import re
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT)]

import eval_runs  # noqa: E402
import eval_sources  # noqa: E402
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
WORKED_NUMBER = re.compile(r"(?<![<>!=])=\s*-?\d[\d.,]*\s*(?:%|percent)?\s*(?:[.;,)]|$)",
                           re.MULTILINE)


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
    missing = []
    for name, body in sections(request):
        missing += [f"{name}: {part}" for part in PARTS if part not in parts_of(body)]
    return missing


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
    return eval_sources.without_source_lines(request).strip() + "\n"


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


def said_before(reply: str) -> str:
    """What Copilot said in a reply before its Metric request: the turns it pushed back or
    asked in, or the whole reply where it holds no request."""
    found = REQUEST_START.search(reply)
    return reply if found is None else reply[:found.start()]


def meets(request: str, required: Required, said: str = "") -> bool:
    """Whether a request holds a requirement: each pattern found in its part, or, where the
    requirement is `absent`, none. A requirement that may be `said` is read in what Copilot
    said before the request too."""
    text = text_of(request, required.part)
    if required.said:
        text += "\n" + said
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
    """Score the Metric request in a reply against its task's requirements key. The reply may
    hold what Copilot said before the request, which a requirement that may be `said` reads."""
    result = Score(task.id)
    request, said = request_in(reply), said_before(reply)
    result.request_missing = not request
    result.sql_in_request = holds_sql(request)
    result.parts_missing = missing_parts(request)
    result.invented = invented_names(request)
    result.worked = worked_numbers(request)
    checks = [(column_count(task), len(sections(request)) == task.columns)]
    checks += [(required, meets(request, required, said)) for required in task.required]
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
    return (_copilot_start(loaded, task) + "\n\nReply as Copilot, following the file. End "
            "each reply with a line `Used: ` and the ids of the file's rules you followed, "
            "such as `Used: A1, D2, Q7`, or `Used: none`; then, after it, your one closing "
            "word.")


def request_form() -> str:
    """File 19's form of a Metric request, its first ```text block."""
    text = FILE_19.read_text(encoding="utf-8")
    found = re.search(r"```text\n(# Metric request:.*?)```", text, re.DOTALL)
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


def memo_key(task_id: str, reply: str, arm: str, model: str) -> eval_runs.Key:
    """The key a task's reply is kept under in the memo (`tools/eval_runs.py`): the task's
    text and the text it loads. In arm C the task's text is the stand-in user's message, which
    holds the column definitions, and the text loaded is file 19 and the definitions; in A0 it
    is the vague goal and the baseline's form with the definitions. `reply` is unused, but the
    memo gives every tool's key function one: the loaded text never depends on it."""
    task = BY_ID[task_id]
    if arm == "C":
        task_text = user_message(task)
        loaded = FILE_19.read_text(encoding="utf-8") + COLUMN_DEFINITIONS
    else:
        task_text, loaded = task.opening, A0_INSTRUCTIONS + request_form() + COLUMN_DEFINITIONS
    return eval_runs.hashed_key(task_id, task_text, arm, model, loaded)


# --- A conversation ------------------------------------------------------------------------

# The agent a conversation spawns, for either part.
AGENT = "metric-proxy"
CONVERSATION = "conversation.json"
# A task's turn file: turn-01-copilot.md, then turn-01-user.md, and so on.
TURN = re.compile(r"^turn-(\d+)-(copilot|user)\.md$")
# Who speaks in a turn, by the turn file's last part, in the transcript's words.
SPEAKERS = {"copilot": "Copilot", "user": "User"}


@dataclass
class Conversation:
    """What a task's folder says of its conversation: the round, the task, the arm and the
    model."""

    round: str
    task: str
    arm: str
    model: str


def task_folder(round_name: str, task: str, local: Path = eval_runs.LOCAL) -> Path:
    """A task's folder in a round, under the local folder; its parent is made."""
    return eval_runs.make_local_path("metric", round_name, task, local=local)


def write_task_folder(task: MetricTask, conversation: Conversation, folder: Path) -> None:
    """Write what a task's agents start from into its folder: copilot.md and, in arm C, the
    stand-in user's user.md, and the conversation's record."""
    folder.mkdir(parents=True, exist_ok=True)
    if conversation.arm == "C":
        caps = "\n\n" + eval_runs.cap_text("metric") + "\n"
        (folder / "user.md").write_text(user_message(task) + caps, encoding="utf-8")
        (folder / "copilot.md").write_text(copilot_message(task) + caps, encoding="utf-8")
    else:
        caps = "\n\n" + eval_runs.reply_cap_text("metric") + "\n"
        (folder / "copilot.md").write_text(baseline_message(task) + caps, encoding="utf-8")
    (folder / CONVERSATION).write_text(json.dumps(vars(conversation)), encoding="utf-8")


def read_conversation(folder: Path) -> Conversation:
    """The conversation a task's folder holds."""
    return Conversation(**json.loads((folder / CONVERSATION).read_text(encoding="utf-8")))


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


def scored_reply(folder: Path) -> str:
    """What a task's round is scored on: every turn Copilot took, its request in the last, or,
    with no turn files, the folder's request.md alone."""
    copilots = [path for speaker, path in _turns(folder) if speaker == "Copilot"]
    if not copilots:
        return (folder / "request.md").read_text(encoding="utf-8")
    return "\n\n".join(path.read_text(encoding="utf-8").strip() for path in copilots) + "\n"


def _shown(path: Path) -> str:
    """A path as the session is told it: from the repo's root where it is under it."""
    return (path.relative_to(ROOT) if path.is_relative_to(ROOT) else path).as_posix()


def ending(folder: Path) -> str | None:
    """Why a task's conversation is over, or None while it goes on: Copilot's newest turn
    holds a request, it is arm A0's one turn, or it is the turn the metric cap in
    `eval_runs.CAPS` names."""
    copilots = [path for speaker, path in _turns(folder) if speaker == "Copilot"]
    if not copilots:
        return None
    count = len(copilots)
    if request_in(copilots[-1].read_text(encoding="utf-8")):
        return f"request in turn {count}"
    if read_conversation(folder).arm == "A0":
        return f"no request in turn {count}"
    if count >= eval_runs.CAPS["metric"].turns:
        return f"turn cap, {count} turns"
    return None


def advance(folder: Path) -> str:
    """The one thing the session does next for a task, in a line: spawn an agent with its
    first message, or send an agent already spawned the other's newest turn. When the
    conversation is over, it writes the transcript and request and says so."""
    conversation = read_conversation(folder)
    task, model, here = conversation.task, conversation.model, _shown(folder)
    done = ending(folder)
    if done is not None:
        write_request(folder)
        return (f"{task}: ended: {done}. Wrote transcript.md and request.md. Record each "
                f"agent's usage with `usage {here} --role <copilot|user>`.")
    turns = _turns(folder)
    if not turns:
        return (f"{task}: spawn {AGENT} model {model}, prompt: Read {here}/copilot.md, then "
                f"write your reply to {here}/turn-01-copilot.md.")
    speaker, newest = turns[-1]
    count = len([one for one, _ in turns if one == speaker])
    if speaker == "Copilot":
        reply = f"{here}/turn-{count:02}-user.md"
        if count == 1:
            return (f"{task}: spawn {AGENT} model {model}, prompt: Read {here}/user.md, then "
                    f"{_shown(newest)}, then write your reply to {reply}.")
        return (f"{task}: SendMessage to the {task} user agent: Read {_shown(newest)}, then "
                f"write your reply to {reply}.")
    return (f"{task}: SendMessage to the {task} Copilot agent: Read {_shown(newest)}, then "
            f"write your reply to {here}/turn-{count + 1:02}-copilot.md.")


# --- The round's plan and its score --------------------------------------------------------


def _round_tasks(split: str, only: list[str] | None = None) -> list[str]:
    """The tasks of a split, or only the ones named, each as its own word or comma-separated."""
    named = []
    for item in only or []:
        named += [task for task in item.split(",") if task]
    return [task.id for task in TASKS
            if split in ("all", task.split) and (not named or task.id in named)]


def _key_of(given: argparse.Namespace) -> functools.partial[eval_runs.Key]:
    """The memo's key function for the round's arm and model."""
    return functools.partial(memo_key, arm=given.arm, model=given.model)


def plan_of(given: argparse.Namespace) -> eval_runs.RoundPlan:
    """The round's plan: which tasks are asked, which come from the memo, and the estimate."""
    tasks = _round_tasks(given.split, given.only)
    def key_for_model(model: str) -> Callable[[str, str], eval_runs.Key]:
        return functools.partial(memo_key, arm=given.arm, model=model)
    asking = eval_runs.RoundToPlan("metric", given.arm, given.model, tasks,
                                   key_for_model=key_for_model)
    return eval_runs.plan_round(asking, _key_of(given), given.fresh, given.over_budget,
                                given.local)


def start_round(given: argparse.Namespace) -> str:
    """Plan a round, write each asked task's folder and say what the session spawns first."""
    eval_runs.check_not_the_ladder(given.model)
    plan = plan_of(given)
    lines = [plan.text]
    for task in plan.asked:
        folder = task_folder(given.round, task, given.local)
        conversation = Conversation(given.round, task, given.arm, given.model)
        write_task_folder(BY_ID[task], conversation, folder)
        lines.append(advance(folder))
    return "\n".join(lines)


RESULTS_HEADING = ("## Metric requests by their requirements, Copilot file 19 "
                   "(`tools/metric_eval.py`)")
RESULTS_TABLE = (
    "\n\n" + RESULTS_HEADING + "\n\n"
    "One row per scored round. Arms: A0 Copilot given the request's form, the column "
    "definitions and the vague goal, no one to ask; C the goal grilled by a proxy loaded with "
    "file 19 and the definitions. \"passed\" holds every essential element, more helpful "
    "elements than not, nothing invented, no number worked out and no SQL; \"essential\" the "
    "share holding every essential element; \"helpful\" the share of helpful elements held; "
    "\"invented\" counts requests with an invented name or a worked number.\n\n"
    "| date | round | model | arm | split | passed | essential | helpful | invented "
    "| with SQL | per task | from memo |\n"
    "|---|---|---|---|---|---|---|---|---|---|---|---|\n")


def _percent(count: int, total: int) -> int:
    """A count as a whole percent of a total."""
    return round(100 * count / total) if total else 0


def results_row(given: argparse.Namespace, results: list[Score], from_memo: int) -> str:
    """A round's row of the results table."""
    total = len(results)
    helpful = _percent(sum(one.helpful_met for one in results),
                       sum(one.helpful_total for one in results))
    invented = sum(bool(one.invented or one.worked) for one in results)
    per_task = " ".join(f"{one.task}:{'pass' if one.passed else 'fail'}" for one in results)
    cells = [datetime.date.today().isoformat(), given.round, given.model, given.arm,
             given.split, str(_percent(sum(one.passed for one in results), total)),
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


def source_row_of(given: argparse.Namespace, task: str, passed: bool, folder: Path
                  ) -> eval_sources.SourceRow:
    """A task's row of sources: what Copilot cited in any of its turns, which its instructions
    ask for at the end of each, against file 19, whose ids it may cite."""
    said = "\n".join(path.read_text(encoding="utf-8") for speaker, path in _turns(folder)
                     if speaker == "Copilot")
    run = eval_sources.RunOf(datetime.date.today().isoformat(), given.round, "metric", task,
                             given.arm, given.model, eval_runs.files_version())
    return eval_sources.source_row(run, passed, said,
                                   {"19": FILE_19.read_text(encoding="utf-8")})


def cap_flags(folder: Path) -> str:
    """What a conversation held past the metric caps, as a flag for its score line: each turn
    file over the reply cap, and Copilot's turns past the turn cap; "" when it held both."""
    caps = eval_runs.CAPS["metric"]
    turns = _turns(folder)
    notes = []
    for _, path in turns:
        length = len(path.read_text(encoding="utf-8").strip())
        if length > caps.reply:
            notes.append(f"{path.name} ({length} characters, cap {caps.reply})")
    copilot_turns = len([one for one, _ in turns if one == "Copilot"])
    if copilot_turns > caps.turns:
        notes.append(f"{copilot_turns} turns of Copilot's, cap {caps.turns}")
    return f"  OVER CAP: {'; '.join(notes)}" if notes else ""


def score_round(given: argparse.Namespace) -> str:
    """Score a round's requests, each task's request.md or, with no folder, the reply kept
    for it in the memo; keep each new request in the memo; record the round's row. Gives the
    report, a line per task."""
    eval_runs.check_not_the_ladder(given.model)
    key_of = _key_of(given)
    lines, results, from_memo, new_sources = [], [], 0, []
    for task in _round_tasks(given.split, given.only):
        folder = task_folder(given.round, task, given.local)
        path = folder / "request.md"
        if path.exists():
            reply = scored_reply(folder)
            result = score_request(BY_ID[task], reply)
            new_sources.append(source_row_of(given, task, result.passed, folder))
            line = score_line(result) + cap_flags(path.parent)
            eval_runs.write_kept(
                eval_runs.Kept(key_of(task, reply), datetime.date.today().isoformat(),
                               line, reply), given.local / "memo")
        else:
            kept = eval_runs.kept_reply(task, key_of, given.local / "memo")
            if kept is None:
                lines.append(f"{task}  no reply")
                continue
            result = score_request(BY_ID[task], kept.reply)
            line = score_line(result)
            from_memo += 1
        results.append(result)
        lines.append(line)
    if new_sources and given.arm == "C":
        eval_sources.keep_sources(new_sources, given.local)
    if results:
        record_row(eval_runs.make_local_path("metric", "results.md", local=given.local),
                   results_row(given, results, from_memo))
        eval_runs.keep_round_result(
            "metric", {"round": given.round, "date": datetime.date.today().isoformat(),
                       "arm": given.arm, "model": given.model},
            [one.passed for one in results], from_memo, given.local)
    lines.append(f"{len(results)} scored, {from_memo} from the memo.")
    return "\n".join(lines)


def record_usage(given: argparse.Namespace) -> str:
    """Record one agent's reported usage for a task's conversation in the ledger."""
    conversation = read_conversation(given.folder)
    run = eval_runs.Run(date=datetime.date.today().isoformat(), commit=given.commit,
                        round=conversation.round, pipeline="metric", task=conversation.task,
                        arm=conversation.arm, model=conversation.model, role=given.role,
                        tokens=given.tokens, seconds=given.seconds,
                        result=ending(given.folder) or "not ended")
    eval_runs.record_run(run, given.local)
    return f"Recorded {run.task} {run.role} ({run.tokens} tokens) in {eval_runs.LEDGER_NAME}."


# --- The commands --------------------------------------------------------------------------


def _parser() -> argparse.ArgumentParser:
    """The commands: plan, start, next, usage and score."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("plan", "start", "score"):
        command = commands.add_parser(name)
        if name == "score":
            command.add_argument("round")
            command.add_argument("--only", nargs="+", metavar="TASK")
        command.add_argument("arm", choices=list(ARMS))
        if name == "start":
            command.add_argument("--round", required=True)
        command.add_argument("--split", choices=["dev", "held_out", "all"], default="dev")
        if name == "plan":
            command.add_argument("--model", default=eval_runs.LADDER_MODEL)
        else:
            command.add_argument("--model", required=True)
        if name != "score":
            command.add_argument("--fresh", action="store_true")
            command.add_argument("--over-budget", action="store_true")
            command.add_argument("--only", nargs="+", metavar="TASK",
                                 help="ask only these tasks of the split")
    commands.add_parser("next").add_argument("folder", type=Path)
    usage = commands.add_parser("usage")
    usage.add_argument("folder", type=Path)
    usage.add_argument("--role", choices=["copilot", "user"], required=True)
    usage.add_argument("--tokens", required=True)
    usage.add_argument("--seconds", required=True)
    usage.add_argument("--commit", default="")
    for command in commands.choices.values():
        command.add_argument("--local", type=Path, default=eval_runs.LOCAL)
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run one command."""
    given = _parser().parse_args(argv)
    if given.command == "plan":
        print(plan_of(given).text)
    elif given.command == "start":
        print(start_round(given))
    elif given.command == "next":
        print(advance(given.folder))
    elif given.command == "usage":
        print(record_usage(given))
    else:
        print(score_round(given))
    return 0


if __name__ == "__main__":
    sys.exit(main())
