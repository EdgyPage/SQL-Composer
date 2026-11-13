"""The memo of the Copilot evaluations: each task's reply and score, kept by what it was asked
on, so a round asks only the tasks whose text changed (Toolbox 8.7, ticket 02).

`tools/copilot_eval.py` and `tools/excel_eval.py` keep their replies here, and so does any
evaluation that asks a model a task in an arm. A reply is kept under a key of:

- the task's id, and the hash of its text, the prompt it is asked;
- the arm;
- the model;
- the hash of the text the arm loads before the prompt, such as the task's objective file in
  arm C;
- for a held-out task in an arm that loads a Copilot file, the Copilot files' version, so a
  held-out task is asked once per files version, and its reply is never scored against
  another.

Each key is one plain file in `.scratch/copilot-eval/memo/`: its key's parts, the date it was
asked, its score line, then the reply as it came, so a round's replies stay readable and can be
scored again. A round's plan names each task to ask and why: no reply kept, its text changed,
the text its arm loads changed, held out and the Copilot files changed, or `--fresh`. The rest
are taken from the memo.

Each tool gives this module its own `memo_key(task_id, reply, arm, model, files)`, which makes
a task's key from its prompt and the text its arm loads (`hashed_key`), and its task filters,
and this module does the rest: the commands `plan`, `prompts`, `template`, `proxy` and
`score` take their arguments here, and a round is planned, and its replies gathered and kept,
here.
"""

from __future__ import annotations

import argparse
import functools
import hashlib
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MEMO = ROOT / ".scratch" / "copilot-eval" / "memo"
COPILOT = ROOT / "copilot"
# A key's files version where its task is asked once per text, not once per files version.
NO_FILES_VERSION = "-"
# What `prompts`, `proxy` and `template` print when the memo keeps every reply of a round.
NOTHING_TO_ASK = ("Nothing to ask: the memo keeps a reply to every task of this round, as "
                  "plan shows. Score the round to score them again.")
# What parts a kept reply's file from its header.
REPLY_HEADING = "\n\n## Reply\n\n"
# The answers file's header line naming the Copilot files' version its replies were asked on.
FILES_HEADER = "memo_files"


def text_hash(text: str) -> str:
    """A text's SHA-256, in hex."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def files_version(folder: Path = COPILOT) -> str:
    """The Copilot files' version: one hash of every file in `folder`, by its path and its
    bytes, each line ending read as \\n, cut to 12 characters."""
    digest = hashlib.sha256()
    for path in sorted(folder.rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(folder).as_posix().encode("utf-8") + b"\0")
            digest.update(path.read_bytes().replace(b"\r\n", b"\n") + b"\0")
    return digest.hexdigest()[:12]


@dataclass(frozen=True)
class Key:
    """What a reply was asked on: its texts by their hashes."""

    task: str
    task_text_hash: str
    arm: str
    model: str
    loaded_text_hash: str
    files_version: str

    def file_name(self) -> str:
        """The name of the memo's file for this key: the task, the arm and the model, readable,
        then a hash of the whole key."""
        whole = "\n".join([self.task, self.task_text_hash, self.arm, self.model,
                           self.loaded_text_hash, self.files_version])
        return f"{_file_name_start(self.task, self.arm, self.model)}{text_hash(whole)[:12]}.md"


def _file_name_start(task: str, arm: str, model: str) -> str:
    """The start of every memo file's name for a task in an arm on a model."""
    return f"{task}-{arm}-{re.sub(r'[^0-9A-Za-z_.]', '_', model)}-"


def hashed_key(task: str, task_text: str, arm: str, model: str, loaded_text: str,
               files: str = NO_FILES_VERSION) -> Key:
    """The key a task's reply is kept under: its texts hashed, `files` as it is given."""
    return Key(task, text_hash(task_text), arm, model, text_hash(loaded_text), files)


@dataclass
class Kept:
    """A reply kept in the memo: its key, the date it was asked, its score line, and the reply
    as it came."""

    key: Key
    asked: str
    score: str
    reply: str


def write_kept(kept: Kept, folder: Path = MEMO) -> Path:
    """Write a kept reply to its key's file in `folder`, in place of one kept before."""
    folder.mkdir(parents=True, exist_ok=True)
    key = kept.key
    score_line = kept.score.replace("\n", " ")
    header = [f"task: {key.task}", f"task text hash: {key.task_text_hash}", f"arm: {key.arm}",
              f"model: {key.model}", f"loaded text hash: {key.loaded_text_hash}",
              f"files version: {key.files_version}", f"asked: {kept.asked}",
              f"score: {score_line}"]
    path = folder / key.file_name()
    path.write_text("\n".join(header) + REPLY_HEADING + kept.reply, encoding="utf-8")
    return path


def read_kept(task: str, arm: str, model: str, folder: Path = MEMO) -> list[Kept]:
    """Each reply kept for a task in an arm on a model, whatever text it was asked on."""
    found = []
    for path in sorted(folder.glob(f"{_file_name_start(task, arm, model)}*.md")):
        head, reply = path.read_text(encoding="utf-8").split(REPLY_HEADING, 1)
        fields = dict(line.split(": ", 1) for line in head.splitlines())
        key = Key(fields["task"], fields["task text hash"], fields["arm"], fields["model"],
                  fields["loaded text hash"], fields["files version"])
        if key.model == model:
            found.append(Kept(key, fields["asked"], fields["score"], reply))
    return found


# --- A round's plan --------------------------------------------------------------------------


def kept_reply(task: str, key_of: Callable[[str, str], Key], folder: Path = MEMO
               ) -> Kept | None:
    """The reply kept for a task under the key it has now, or None. `key_of` gives a task's
    key for a reply: in arm R, the text loaded is file 00 and the file the reply names, and
    every other arm's key leaves the reply out."""
    wanted = key_of(task, "")
    for kept in read_kept(task, wanted.arm, wanted.model, folder):
        if kept.key == key_of(task, kept.reply):
            return kept
    return None


@dataclass
class Planned:
    """What a round's plan says of a task: why it is asked, or the reply kept for it."""

    task: str
    reason: str  # why it is asked, or "" when its kept reply is taken
    kept: Kept | None


def task_plan(task: str, key_of: Callable[[str, str], Key], held_out: bool, fresh: bool,
              folder: Path = MEMO) -> Planned:
    """Whether a round asks a task, and why, or the reply kept for it. `fresh` asks a dev task
    again, but not a held-out task already asked on the same text and files: it is asked once
    per files version."""
    kept = kept_reply(task, key_of, folder)
    if kept is not None and (held_out or not fresh):
        return Planned(task, "", kept)
    if kept is not None:
        return Planned(task, "--fresh", None)
    return Planned(task, _why_asked(task, key_of, folder), None)


def _why_asked(task: str, key_of: Callable[[str, str], Key], folder: Path) -> str:
    """Why a task with no reply kept under its key now is asked: what changed since one was
    kept, or that none was."""
    wanted = key_of(task, "")
    earlier = read_kept(task, wanted.arm, wanted.model, folder)
    if not earlier:
        return "no reply kept"
    if all(kept.key.task_text_hash != wanted.task_text_hash for kept in earlier):
        return "its text changed"
    if all(kept.key.loaded_text_hash != key_of(task, kept.reply).loaded_text_hash
           for kept in earlier):
        return f"the text arm {wanted.arm} loads changed"
    return "held out, and the Copilot files changed since it was asked"


def round_plan(tasks: list[tuple[str, bool]], memo_key: Callable[..., Key],
               given: argparse.Namespace) -> list[Planned]:
    """What the plan says of each task of a round, each given as its id and whether it is
    held out, in the arm, on the model, memo and `--fresh` the command was given. `memo_key`
    is the tool's own: memo_key(task_id, reply, arm=, model=, files=)."""
    key_of = functools.partial(memo_key, arm=given.arm, model=given.model,
                               files=files_version())
    return [task_plan(task, key_of, held_out, given.fresh, given.memo)
            for task, held_out in tasks]


def plan_text(plan: list[Planned], files: str) -> str:
    """A round's plan as text: the files version to write in the answers file's header, a line
    per task, saying why it is asked or which kept reply is taken, then how many of each."""
    lines = [f"The Copilot files' version: {files}. Write it in the answers file's header as "
             f"{FILES_HEADER}: {files}."]
    for one in plan:
        if one.kept is None:
            lines.append(f"{one.task}: ask: {one.reason}")
        else:
            lines.append(f"{one.task}: from the memo, {one.kept.key.file_name()}")
    asked = sum(one.kept is None for one in plan)
    lines.append(f"Ask {asked} of {len(plan)}; {len(plan) - asked} from the memo.")
    return "\n".join(lines)


def print_round(tasks: list[tuple[str, bool]], memo_key: Callable[..., Key],
                given: argparse.Namespace, asked_text: Callable[[list[str]], str]) -> None:
    """Print what a `plan`, `prompts`, `template` or `proxy` command gives for a round: the
    plan, or `asked_text` of the tasks it says to ask, or that there is nothing to ask."""
    plan = round_plan(tasks, memo_key, given)
    if given.command == "plan":
        print(plan_text(plan, files_version()))
        return
    asked = [one.task for one in plan if one.kept is None]
    if asked:
        print(asked_text(asked))
    else:
        print(NOTHING_TO_ASK)


# --- The commands ----------------------------------------------------------------------------


def add_round_commands(commands: argparse._SubParsersAction[argparse.ArgumentParser],
                       arms: list[str],
                       add_task_filters: Callable[..., argparse.ArgumentParser]) -> None:
    """The commands that write only the tasks a round's plan names: `prompts` and `template`,
    which take `--arm`, and `plan` and `proxy`, which take the arm first; and `score`. Each
    takes the tool's task filters."""
    for name in ("prompts", "template"):
        command = add_task_filters(commands.add_parser(name))
        command.add_argument("--arm", choices=arms, required=True)
        _add_plan_arguments(command)
    for name in ("plan", "proxy"):
        command = add_task_filters(commands.add_parser(name))
        command.add_argument("arm", choices=arms)
        _add_plan_arguments(command)
    scoring = add_task_filters(commands.add_parser("score"), split=None)
    scoring.add_argument("answers", type=Path)
    scoring.add_argument("--record", type=Path)
    scoring.add_argument("--memo", type=Path, default=MEMO, help="the memo's folder")


def _add_plan_arguments(parser: argparse.ArgumentParser) -> None:
    """The arguments of a command that writes only the tasks a round's plan names."""
    parser.add_argument("--model", required=True,
                        help="the model asked, such as haiku, or copilot-web in Copilot")
    parser.add_argument("--fresh", action="store_true",
                        help="ask every dev task again, kept or not")
    parser.add_argument("--memo", type=Path, default=MEMO, help="the memo's folder")


# --- Scoring a round -------------------------------------------------------------------------


def read_answers(text: str, letter: str) -> tuple[dict[str, str], dict[str, str]]:
    """An answers file's header, by name, and each reply, by its task's id: a heading such as
    `## T07` for the Copilot tasks, `letter` "T", `## X07` for the Excel tasks and `## M01`
    for the Metric request tasks."""
    parts = re.split(rf"^## ({letter}\d+)\s*$", text, flags=re.MULTILINE)
    header = dict(re.findall(r"^(\w+):[ \t]*(.*?)[ \t]*$", parts[0], re.MULTILINE))
    return header, {parts[i]: parts[i + 1] for i in range(1, len(parts), 2)}


@dataclass
class RoundReplies:
    """The replies a round scores, by task in the round's order, those of them taken from the
    memo, each task of the round, and the key of a task's reply."""

    tasks: list[str]
    replies: dict[str, str]
    taken: dict[str, Kept]
    key_of: Callable[[str, str], Key]
    folder: Path


def round_replies(header: dict[str, str], answered: dict[str, str], tasks: list[str],
                  memo_key: Callable[..., Key], arms: list[str], folder: Path = MEMO
                  ) -> RoundReplies:
    """The replies a round scores: the answers file's, and for each task of the round it
    doesn't answer, the reply kept under the task's key now. The arm and the model are the
    header's, and a held-out reply's files version its `memo_files:`, the version the plan
    named when it was asked."""
    check_answers_header(header, arms)
    asked_on = header.get(FILES_HEADER, "")
    key_of = functools.partial(memo_key, arm=header["arm"], model=header["model"],
                               files=asked_on or files_version())
    versioned = [task for task in tasks if task in answered
                 and key_of(task, answered[task]).files_version != NO_FILES_VERSION]
    if versioned and not asked_on:
        raise SystemExit(f"{', '.join(versioned)} held out, and the memo keeps a held-out "
                         "reply by the Copilot files' version it was asked on. Write that "
                         f"version in the answers file's header as {FILES_HEADER}: <version>, "
                         "as plan printed it, or as template wrote it.")
    found = RoundReplies(tasks, {}, {}, key_of, folder)
    for task in tasks:
        if task in answered:
            found.replies[task] = answered[task]
            continue
        kept = kept_reply(task, key_of, folder)
        if kept is not None:
            found.taken[task] = kept
            found.replies[task] = kept.reply
    return found


def check_answers_header(header: dict[str, str], arms: list[str]) -> None:
    """Refuse an answers file whose header doesn't give its arm and its model, which the memo
    keeps each reply by."""
    arm, model = header.get("arm", ""), header.get("model", "")
    if arm not in arms or not model or model.startswith("<"):
        raise SystemExit(f"The answers file's header gives arm {arm or 'none'} and model "
                         f"{model or 'none'}. The memo keeps each reply by its arm, one of "
                         f"{', '.join(arms)}, and its model, such as haiku: fill both in.")


def keep_round(found: RoundReplies, scores: dict[str, str], asked: str) -> None:
    """Keep each reply a round scored with its new score line: a new reply as asked on
    `asked`, a kept one as it was asked."""
    for task, reply in found.replies.items():
        if task in found.taken:
            asked_on = found.taken[task].asked
        else:
            asked_on = asked
        write_kept(Kept(found.key_of(task, reply), asked_on, scores[task], reply),
                   found.folder)


def memo_line(found: RoundReplies) -> str:
    """How many of a round's replies came from the memo, and each task with no reply."""
    line = f"{len(found.taken)} of {len(found.replies)} replies from the memo"
    missing = [task for task in found.tasks if task not in found.replies]
    if missing:
        line += f"; no reply, in the answers file or the memo, for {', '.join(missing)}"
    return line + "."
