"""Score Copilot file 19, Metric request, offline, on the Example database (Toolbox 8.7,
ticket 11).

File 19 takes a user from a vague wish for a new metric to a Metric request: plain text, no
SQL, that a chatbot knowing the user's databases writes the column from. This measures it with
three proxies per task (`tools/metric_eval_tasks.py`), each a small model in a Claude session
(`.claude/agents/metric-proxy.md`):

- the stand-in user, who says the task's vague goal and answers from its secret answer key;
- Copilot, loaded with file 19, who asks one question at a time and writes the request;
- the stand-in chatbot, given only the Example database's column descriptions and the request,
  who writes the column's Hive.

The column passes when its Hive gives the key's numbers on the Example database, whatever its
columns are called; in arm C the request must also be there and hold no SQL. The baseline, arm
A0, is the same chatbot given only the vague goal.

    python tools/metric_eval.py plan C --split dev --model haiku
    python tools/metric_eval.py messages C --split dev --model haiku --into <run>
    python tools/metric_eval.py chatbot <run>/M01
    python tools/metric_eval.py answers <run> --arm C --model haiku --files <hash> \\
        --memo-files <version> --into <run>/answers.md
    python tools/metric_eval.py score <run>/answers.md --split dev \\
        --record .scratch/copilot-eval/results.md

`messages` writes, for each task the round's plan names, a folder holding the messages the
proxies start from: in arm C user.md and copilot.md, in A0 chatbot-message.md. In arm C the
two talk turn by turn, Copilot writing turn-01-copilot.md, the user turn-01-user.md, and so on,
until Copilot's turn holds the Metric request; `chatbot` then writes the folder's transcript.md,
request.md and chatbot-message.md. The chatbot writes chatbot.md. `answers` gathers a round's
folders into one answers file, and `score` scores it, keeping each answer in the memo
(`tools/eval_memo.py`) as the Copilot evaluation does: a held-out task in arm C once per
version of the Copilot files.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime
import functools
import io
import itertools
import math
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT)]

import eval_memo  # noqa: E402
from copilot_eval import EXAMPLE_TABLES  # noqa: E402
from metric_eval_tasks import BY_ID, TASKS, USER_RULES, MetricTask  # noqa: E402

from sqlglot_composer import example_database  # noqa: E402

FILE_19 = ROOT / "copilot" / "19_metric_request.txt"

# A block of Hive in a reply: the chatbot's answer is the last.
SQL_BLOCK = re.compile(r"```(?:sql|hive|hql)[ \t]*\n(.*?)```", re.DOTALL | re.IGNORECASE)


# SQL in a Metric request: a code block of it, or the words only SQL writes, in capitals.
SQL_IN_TEXT = re.compile(r"```(?:sql|hive|hql)\b|\bSELECT\b[^\n]*\bFROM\b|\bCASE\s+WHEN\b"
                         r"|\bGROUP\s+BY\b|\bJOIN\b[^\n]*\bON\b")
# Where a Metric request starts, and each column's section.
REQUEST_START = re.compile(r"^# Metric request\b", re.MULTILINE)
COLUMN = re.compile(r"^## Column: *(.+?) *$", re.MULTILINE)
# The nine parts of a column's section, as file 19's Output writes them.
PARTS = ("What it is", "Formula", "Quantities", "One row per", "Days counted", "Left out",
         "Edge cases", "Worked example", "Open questions")


def holds_sql(request: str) -> bool:
    """Whether a Metric request holds SQL, which it never should: it is plain words and
    maths, for the chatbot to write the column from."""
    return SQL_IN_TEXT.search(request) is not None


def missing_parts(request: str) -> list[str]:
    """Each part a Metric request's column sections lack, as `<column>: <part>`, or that it
    has no column section at all."""
    sections = COLUMN.split(request)[1:]
    if not sections:
        return ["a column section"]
    missing = []
    for name, body in zip(sections[::2], sections[1::2]):
        missing += [f"{name}: {part}" for part in PARTS
                    if not re.search(rf"^\s*\d+\.\s*{part}\b[^:\n]*:", body, re.MULTILINE)]
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
    return request.strip() + "\n"


# --- The messages each proxy is given ----------------------------------------------------


def column_descriptions() -> str:
    """What the stand-in chatbot knows of the Example database, as a chatbot at work knows
    the indexed databases: each table's Table reference, its columns, their types and their
    descriptions, its partitions and its Key. No rows."""
    lines = []
    for name in EXAMPLE_TABLES:
        table = getattr(example_database, name)
        about = []
        if table._partitioned_by:
            about.append(f"partitioned by {', '.join(table._partitioned_by)}")
        about.append(f"Key {', '.join(table._key)}" if table._key else "no Key")
        lines.append(f"- `{table._name}` ({'; '.join(about)}):")
        for column, kind in table._columns.items():
            description = table._descriptions.get(column)
            described = f": {description}" if description else ""
            lines.append(f"  - {column} {kind}{described}")
    return "\n".join(lines)


def _quoted(text: str) -> str:
    """Text a message quotes, between <<< and >>>."""
    return f"<<<\n{text.rstrip()}\n>>>"


def user_message(task: MetricTask) -> str:
    """The stand-in user's message: the vague goal they said first, the answer key they keep
    from Copilot, and how they answer."""
    return (
        "You are standing in for a person at work, in a measurement of a Copilot file. You "
        "want a new metric, and you are asking Microsoft Copilot to help you say exactly what "
        "it is. You know your business, not the database. Use no tools but the ones your "
        "prompt names.\n\nYou said this to Copilot first:\n\n" + _quoted(task.opening)
        + "\n\nYour answer key, which Copilot can't see. Answer its questions from it:\n\n"
        + _quoted(task.answer_key) + "\n\nHow you answer:\n\n" + USER_RULES)


def copilot_message(task: MetricTask) -> str:
    """The grilling proxy's first message: file 19, pasted first, then the user's vague
    goal."""
    return (
        "You are standing in for Microsoft Copilot in a web chat. Use no tools but the ones "
        "your prompt names: answer from what is written here and what you already know.\n\n"
        "The user pasted this as their first message:\n\n"
        + _quoted(FILE_19.read_text(encoding="utf-8"))
        + "\n\nThen they sent:\n\n" + _quoted(task.opening)
        + "\n\nReply as Copilot, following the file.")


CHATBOT_INSTRUCTIONS = (
    "You are standing in for a company's chatbot, which knows the company's databases from "
    "their tables' column descriptions, below; it never sees their rows. A user asks it for a "
    "new column. Write one Hive SELECT that gives it: one row per what the user asks, with the "
    "columns that name each row, such as job_id, then the new column or columns. It runs on "
    "a small Hive engine with no CAST: write 1.0 * x for a decimal. Use no tools but the ones "
    "your prompt names. Reply with the SELECT in one ```sql block, and nothing else.\n\n"
    "The tables:\n\n")


def chatbot_message(task: MetricTask, request: str | None = None) -> str:
    """The stand-in chatbot's message: the column descriptions, then the Metric request, or
    in the baseline, with no request, the user's vague goal."""
    user_text = task.opening if request is None else request
    return (CHATBOT_INSTRUCTIONS + column_descriptions() + "\n\nThe user's message:\n\n"
            + _quoted(user_text))


# --- The memo ------------------------------------------------------------------------------

# The arms: the chatbot given the vague goal alone, or the Metric request file 19 wrote.
ARMS = {"A0": "the chatbot given the vague goal alone",
        "C": "the goal grilled with Copilot file 19, the chatbot given the Metric request"}


def memo_key(task_id: str, reply: str, arm: str, model: str, files: str) -> eval_memo.Key:
    """The key a task's reply is kept under in the memo (`tools/eval_memo.py`): in arm C the
    stand-in user's message, file 19 and the chatbot's, and a held-out task's Copilot files
    version `files`; in A0 the vague goal and the chatbot's message. `reply` is unused: the
    loaded text never depends on it."""
    task = BY_ID[task_id]
    chatbot = CHATBOT_INSTRUCTIONS + column_descriptions()
    if arm == "C":
        task_text, loaded = user_message(task), FILE_19.read_text(encoding="utf-8") + chatbot
    else:
        task_text, loaded = task.opening, chatbot
    if task.split != "held_out" or arm != "C":
        files = eval_memo.NO_FILES_VERSION
    return eval_memo.hashed_key(task_id, task_text, arm, model, loaded, files)


# --- Scoring -------------------------------------------------------------------------------


def compared(value: object) -> object:
    """A value as the scorer compares it: a number rounded to two places, NULL as None, and
    any other value as text."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if isinstance(value, bool):
        return str(value)
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return str(value)


@dataclass
class Score:
    """How a task's answer did: the chatbot's Hive found, run on the Example database, and
    giving the key's numbers; and whether the Metric request it was given held SQL."""

    task: str
    found: bool = False
    runs: bool = False
    correct: bool = False
    sql_in_request: bool = False
    request_missing: bool = False
    parts_missing: list[str] = field(default_factory=list)
    note: str = ""

    @property
    def passed(self) -> bool:
        """Whether the answer passes: the key's numbers, and in arm C from a Metric request
        that holds no SQL."""
        return self.correct and not self.sql_in_request and not self.request_missing


def compared_row(row: tuple[object, ...]) -> tuple[object, ...]:
    """A row as the scorer compares it, each value by `compared`."""
    return tuple(map(compared, row))


def _picked(row: tuple[object, ...], positions: tuple[int, ...]) -> tuple[object, ...]:
    """The values at some positions of a row, in that order."""
    return tuple(row[position] for position in positions)


def _sorted_column(rows: list[tuple[object, ...]], position: int) -> list[object]:
    """One column's values, in one order whatever their types."""
    return sorted([row[position] for row in rows], key=repr)


def gives_the_keys_numbers(columns: list[str], rows: list[tuple[object, ...]],
                           task: MetricTask) -> bool:
    """Whether rows hold the key's: the same number of rows, and for each of the key's columns
    one of theirs with the same values on the same rows, whatever it is called or where it is.
    Extra columns are fine."""
    answer_rows = [compared_row(row) for row in rows]
    key = sorted([compared_row(row) for row in task.key_rows], key=repr)
    if len(answer_rows) != len(key):
        return False
    candidates = []
    for wanted in range(len(task.key_columns)):
        values = _sorted_column(key, wanted)
        candidates.append([position for position in range(len(columns))
                           if _sorted_column(answer_rows, position) == values])
    for choice in itertools.product(*candidates):
        if len(set(choice)) < len(choice):
            continue
        if sorted([_picked(row, choice) for row in answer_rows], key=repr) == key:
            return True
    return False


def score(task: MetricTask, reply: str) -> Score:
    """Score a chatbot's reply to a task: its last block of Hive, run on the Example database,
    must give the key's numbers."""
    result = Score(task.id)
    blocks = SQL_BLOCK.findall(reply)
    if not blocks:
        result.note = "no ```sql block"
        return result
    result.found = True
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            given_back = example_database.query(blocks[-1].strip().rstrip(";"))
    except Exception as error:  # the chatbot's Hive: any refusal or error is a miss
        result.note = " ".join(str(error).split())[:300]
        return result
    result.runs = True
    rows = list(given_back.itertuples(index=False, name=None))
    columns = [str(column) for column in given_back.columns]
    result.correct = gives_the_keys_numbers(columns, rows, task)
    if not result.correct:
        result.note = f"gives {len(rows)} rows of {', '.join(columns)}"
    return result


# An arm C answer's two parts, under these headings: the Metric request, then the chatbot's
# reply to it.
REQUEST_HEADING = "### Metric request"
CHATBOT_HEADING = "### Chatbot"


def score_reply(task: MetricTask, reply: str, arm: str) -> Score:
    """Score an answer: in A0 the chatbot's reply; in C the Metric request, which must be
    there and hold no SQL, then the chatbot's reply to it, under their headings."""
    if arm != "C":
        return score(task, reply)
    request, _, chatbot = reply.partition(CHATBOT_HEADING)
    request = request.replace(REQUEST_HEADING, "", 1)
    result = score(task, chatbot)
    result.request_missing = request_in(request) == ""
    result.sql_in_request = holds_sql(request)
    result.parts_missing = missing_parts(request)
    if result.request_missing:
        result.note = f"no Metric request; {result.note}"
    return result


def score_line(result: Score) -> str:
    """A scored answer in one line: pass or fail, the checks it got to, and why it failed."""
    checks = [name for name in ("found", "runs", "correct") if getattr(result, name)]
    if result.sql_in_request:
        checks.append("SQL in the request")
    if result.parts_missing:
        checks.append(f"request lacks {', '.join(result.parts_missing)}")
    verdict = "pass" if result.passed else "fail"
    return f"{result.task}  {verdict}  {' '.join(checks)}  {result.note}".rstrip()


# --- A round's folders ---------------------------------------------------------------------


def write_task_messages(task: MetricTask, arm: str, folder: Path) -> None:
    """Write the messages a task's proxies start from into its folder: in arm C the stand-in
    user's, user.md, and the grilling proxy's, copilot.md; in A0 the chatbot's alone,
    chatbot-message.md."""
    folder.mkdir(parents=True, exist_ok=True)
    if arm == "C":
        (folder / "user.md").write_text(user_message(task), encoding="utf-8")
        (folder / "copilot.md").write_text(copilot_message(task), encoding="utf-8")
    else:
        (folder / "chatbot-message.md").write_text(chatbot_message(task), encoding="utf-8")


# A grilled task's turn file: turn-01-copilot.md, then turn-01-user.md, and so on.
TURN = re.compile(r"^turn-(\d+)-(copilot|user)\.md$")
# Who speaks in a turn, by the turn file's last part, in the transcript's words.
SPEAKERS = {"copilot": "Copilot", "user": "User"}


def _turns(folder: Path) -> list[tuple[str, Path]]:
    """A grilled task's turns, in order, each its speaker and its file: Copilot's turn 1,
    the user's turn 1, Copilot's turn 2, and so on."""
    turns = []
    for path in folder.iterdir():
        named = TURN.match(path.name)
        if named is not None:
            turns.append((int(named.group(1)), named.group(2) == "user",
                          SPEAKERS[named.group(2)], path))
    return [(speaker, path) for _, _, speaker, path in sorted(turns)]


def write_chatbot_message(folder: Path) -> None:
    """From a grilled task's turns, write its transcript.md, the Metric request in Copilot's
    last turn as request.md, and the chatbot's message given it, chatbot-message.md."""
    turns = _turns(folder)
    transcript = [f"{speaker}:\n\n{path.read_text(encoding='utf-8').strip()}\n"
                  for speaker, path in turns]
    (folder / "transcript.md").write_text("\n".join(transcript), encoding="utf-8")
    copilots = [path for speaker, path in turns if speaker == "Copilot"]
    request = request_in(copilots[-1].read_text(encoding="utf-8")) if copilots else ""
    (folder / "request.md").write_text(request, encoding="utf-8")
    message = chatbot_message(BY_ID[folder.name], request)
    (folder / "chatbot-message.md").write_text(message, encoding="utf-8")


def answers_text(run: Path, header: dict[str, str]) -> str:
    """A round's answers file, from its task folders: the header, then each task's answer, in
    arm C its request.md and chatbot.md under their headings, in A0 its chatbot.md."""
    parts = ["\n".join(f"{name}: {value}" for name, value in header.items()) + "\n"]
    for folder in sorted(path for path in run.iterdir() if path.name in BY_ID):
        chatbot = (folder / "chatbot.md").read_text(encoding="utf-8").strip()
        if header["arm"] == "C":
            request = (folder / "request.md").read_text(encoding="utf-8").strip()
            chatbot = f"{REQUEST_HEADING}\n\n{request}\n\n{CHATBOT_HEADING}\n\n{chatbot}"
        parts.append(f"## {folder.name}\n\n{chatbot}\n")
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


RESULTS_HEADING = "## Metric requests, Copilot file 19 (`tools/metric_eval.py`)"
RESULTS_TABLE = (
    "\n\n" + RESULTS_HEADING + "\n\n"
    "One row per scored answers file. Arms: A0 the chatbot given the vague goal alone; C the "
    "goal grilled by a proxy loaded with file 19, the chatbot given the Metric request. "
    "\"passed\" gives the key's numbers on the Example database, and in C from a request with "
    "no SQL; \"with SQL\" counts requests holding SQL, \"whole\" the share with the nine parts "
    "in every column.\n\n"
    "| date | files | model | arm | split | passed | found | runs | correct | with SQL | whole "
    "| per task | from memo |\n"
    "|---|---|---|---|---|---|---|---|---|---|---|---|---|\n")


def _percent(count: int, total: int) -> int:
    """A count as a whole percent of a total."""
    return round(100 * count / total) if total else 0


def results_row(header: dict[str, str], split: str, results: list[Score],
                from_memo: int) -> str:
    """A round's row of the results table."""
    total = len(results)
    rates = []
    for name in ("passed", "found", "runs", "correct"):
        rates.append(_percent(sum(getattr(one, name) for one in results), total))
    with_sql = str(sum(one.sql_in_request for one in results))
    whole = str(_percent(sum(not one.parts_missing for one in results), total))
    if header["arm"] != "C":
        with_sql = whole = "-"
    per_task = " ".join(f"{one.task}:{'pass' if one.passed else 'fail'}" for one in results)
    cells = [header.get("date", ""), header.get("files", ""), header["model"], header["arm"],
             split, *map(str, rates), with_sql, whole, per_task, str(from_memo)]
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
    results = [score_reply(BY_ID[task], reply, header["arm"])
               for task, reply in replies.replies.items()]
    lines = [score_line(one) for one in results]
    eval_memo.keep_round(replies, {one.task: line for one, line in zip(results, lines)},
                         header.get("date", ""))
    if record is not None:
        record_row(record, results_row(header, split, results, len(replies.taken)))
    return "\n".join([*lines, eval_memo.memo_line(replies)])


# --- The commands --------------------------------------------------------------------------


def _parser() -> argparse.ArgumentParser:
    """The commands: plan, messages, chatbot, answers and score."""
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
    commands.add_parser("chatbot").add_argument("folder", type=Path)
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
    elif given.command == "chatbot":
        write_chatbot_message(given.folder)
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
