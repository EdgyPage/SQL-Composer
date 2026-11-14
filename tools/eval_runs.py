"""The evaluation system's one module: the local folder, the ledger of every agent run, the memo
of every reply, and the plan of a round with its estimate and its budget (evaluation system,
ticket 01).

Every testing pipeline (the usability loop, the Copilot, Excel and Metric request evaluations)
and the maintainer agents keep their records here, and only their tasks and their scorers stay
in their own tools. Nothing here reaches the network, and nothing here is committed: every file
this module writes is under `.eval-local/`, which git ignores.

    .venv/Scripts/python tools/eval_runs.py record --pipeline copilot --round r1 --task T07 \\
        --arm C --model haiku --role proxy --tokens 41000 --seconds 38 --result pass \\
        --commit <sha>
    .venv/Scripts/python tools/eval_runs.py ledger
    .venv/Scripts/python tools/eval_runs.py carry-over

- **The local folder**, `LOCAL`: `.eval-local/`, made on first use. `make_local_path` is the one
  way to a path in it and refuses a path that would leave it.
- **The ledger**, `.eval-local/ledger.csv`: one row (`Run`) per agent run, written by `record`
  from the usage the agent reported when it finished, and read by `read_ledger`.
- **The memo**, `.eval-local/memo/`: each reply kept in one plain file under a `Key`: its
  task's id and the hash of its text, the arm, the model, and the hash of exactly the text the
  task loads. A reply is asked again only when one of those changes, held-out tasks included.
  (`files_version` in a key is for the pipelines not yet moved onto this module, which key a
  held-out reply by the Copilot files' version too; a key made here leaves it out.)
- **A plan**, `plan_round`: each task of a round, asked and why, or taken from the memo; the
  round's estimated tokens, the mean of the past ledger rows of the same pipeline, arm and
  model for each task asked; and the check against the pipeline's `BUDGET`.
- **Budgets**, `BUDGET`: `{pipeline: math.inf}` until the ledger has the data to set one, so a
  budget is one edit. A round over it is refused unless `--over-budget` is given.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
import re
import shutil
from collections.abc import Callable
from dataclasses import dataclass, fields
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOCAL = ROOT / ".eval-local"
MEMO = LOCAL / "memo"
# The folder the memo was kept in before the evaluation system, which `carry-over` reads.
OLD_MEMO = ROOT / ".scratch" / "copilot-eval" / "memo"
LEDGER_NAME = "ledger.csv"

PIPELINES = ("usability", "copilot", "excel", "metric", "maintainer")
# The agent that ran: a proxy for Copilot's reader, a user of the usability loop or the Metric
# request, Copilot itself, or a maintainer agent (drift reviewer, code reviewer, beginner
# reader).
ROLES = ("proxy", "user", "copilot", "maintainer")
# A maintainer agent's run is a row of pipeline and role "maintainer": its task is one of these
# names, its round the ticket or commit it reviewed, its arm "-", and its result "clean" or
# "opened" with the items or findings it opened ("opened D3 D4", "opened 2 findings").
MAINTAINER_AGENTS = ("drift-reviewer", "code-review-standards", "code-review-spec",
                     "beginner-reader")
# The most tokens a round of each pipeline may be estimated to use, with no limit until the
# ledger has data to set one.
BUDGET: dict[str, float] = dict.fromkeys(PIPELINES, math.inf)

# A key's files version where its task is asked once per text, not once per files version.
NO_FILES_VERSION = "-"
# What parts a kept reply's file from its header.
REPLY_HEADING = "\n\n## Reply\n\n"


# --- The local folder ------------------------------------------------------------------------


def make_local_path(*parts: str, local: Path = LOCAL) -> Path:
    """A path under the local folder, whose parent is made. Refuses a path outside it."""
    path = local.joinpath(*parts)
    if not path.resolve().is_relative_to(local.resolve()):
        raise SystemExit(f"{path} is outside the local folder {local}: every file of the "
                         "evaluation records is kept under it.")
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


# --- The ledger ------------------------------------------------------------------------------


@dataclass
class Run:
    """One agent run: when, on which commit, in which round, and what it cost and found.
    `tokens` is the total the agent reported, or its input tokens where only those are known."""

    date: str
    commit: str
    round: str
    pipeline: str
    task: str
    arm: str
    model: str
    role: str
    tokens: str
    seconds: str
    result: str


LEDGER_FIELDS = [one.name for one in fields(Run)]


def check_run(run: Run) -> None:
    """Refuse a row whose pipeline or role is unknown or whose tokens or seconds aren't a
    number of at least 0."""
    if run.pipeline not in PIPELINES:
        raise SystemExit(f"The pipeline {run.pipeline!r} is not one the ledger knows: "
                         f"{', '.join(PIPELINES)}.")
    if run.role not in ROLES:
        raise SystemExit(f"The role {run.role!r} is not one the ledger knows: "
                         f"{', '.join(ROLES)}.")
    if run.pipeline == "maintainer":
        check_maintainer_run(run)
    for name in ("tokens", "seconds"):
        if not re.fullmatch(r"\d+(\.\d+)?", getattr(run, name)):
            raise SystemExit(f"The ledger's {name} is a number of at least 0, not "
                             f"{getattr(run, name)!r}.")


def check_maintainer_run(run: Run) -> None:
    """Refuse a maintainer row whose role or task isn't one of the agents' or whose result
    doesn't start with "clean" or "opened"."""
    if run.role != "maintainer" or run.task not in MAINTAINER_AGENTS:
        raise SystemExit(f"A maintainer run has the role maintainer and, as its task, one of "
                         f"{', '.join(MAINTAINER_AGENTS)}, not {run.role!r} and {run.task!r}.")
    if not re.match(r"(clean|opened)\b", run.result):
        raise SystemExit(f"A maintainer run's result starts with clean or opened, not "
                         f"{run.result!r}.")


def record_run(run: Run, local: Path = LOCAL) -> Path:
    """Add a run to the ledger, whose header is written with its first row."""
    check_run(run)
    path = make_local_path(LEDGER_NAME, local=local)
    is_new = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as ledger:
        writer = csv.writer(ledger, lineterminator="\n")
        if is_new:
            writer.writerow(LEDGER_FIELDS)
        writer.writerow([getattr(run, name) for name in LEDGER_FIELDS])
    return path


def read_ledger(local: Path = LOCAL) -> list[Run]:
    """Every run in the ledger, in the order recorded; none when there is no ledger yet."""
    path = local / LEDGER_NAME
    if not path.exists():
        return []
    with path.open(encoding="utf-8", newline="") as ledger:
        return [Run(**row) for row in csv.DictReader(ledger)]


# --- The memo --------------------------------------------------------------------------------


def text_hash(text: str) -> str:
    """A text's SHA-256, in hex."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Key:
    """What a reply was asked on: its texts by their hashes."""

    task: str
    task_text_hash: str
    arm: str
    model: str
    loaded_text_hash: str
    files_version: str = NO_FILES_VERSION

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
        fields_of = dict(line.split(": ", 1) for line in head.splitlines())
        key = Key(fields_of["task"], fields_of["task text hash"], fields_of["arm"],
                  fields_of["model"], fields_of["loaded text hash"],
                  fields_of.get("files version", NO_FILES_VERSION))
        if key.model == model:
            found.append(Kept(key, fields_of["asked"], fields_of["score"], reply))
    return found


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


def carry_over(old: Path = OLD_MEMO, new: Path = MEMO) -> int:
    """Copy each reply kept in the old memo's folder into the new one, under the key it holds
    (each file records the hash of the text it loaded), unless the new folder already keeps
    that key. Returns how many were copied."""
    copied = 0
    for path in sorted(old.glob("*.md")):
        target = new / path.name
        if not target.exists():
            new.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            copied += 1
    return copied


# --- A round's plan --------------------------------------------------------------------------


@dataclass
class Planned:
    """What a round's plan says of a task: why it is asked, or the reply kept for it."""

    task: str
    reason: str  # why it is asked, or "" when its kept reply is taken
    kept: Kept | None


def memo_plan(tasks: list[str], key_of: Callable[[str, str], Key], fresh: bool,
              folder: Path = MEMO) -> list[Planned]:
    """Whether a round asks each task, and why, or the reply kept for it: asked when no reply
    is kept under the key it has now, and with `fresh` whatever is kept."""
    plan = []
    for task in tasks:
        kept = kept_reply(task, key_of, folder)
        if kept is None:
            plan.append(Planned(task, _why_asked(task, key_of, folder), None))
        elif fresh:
            plan.append(Planned(task, "--fresh", None))
        else:
            plan.append(Planned(task, "", kept))
    return plan


def _why_asked(task: str, key_of: Callable[[str, str], Key], folder: Path) -> str:
    """Why a task with no reply kept under its key now is asked: what changed since one was
    kept, or that none was."""
    wanted = key_of(task, "")
    earlier = read_kept(task, wanted.arm, wanted.model, folder)
    if not earlier:
        return "no reply kept"
    if all(kept.key.task_text_hash != wanted.task_text_hash for kept in earlier):
        return "its text changed"
    return "the text it loads changed"


def estimated_tokens(rows: list[Run], pipeline: str, arm: str, model: str, asked: int
                     ) -> float | None:
    """The tokens `asked` tasks are estimated to use: the mean tokens of the ledger's rows of
    the pipeline, arm and model, for each. None when the ledger has no such row."""
    past = [float(row.tokens) for row in rows
            if (row.pipeline, row.arm, row.model) == (pipeline, arm, model)]
    if not past:
        return None
    return sum(past) / len(past) * asked


def check_budget(pipeline: str, estimate: float | None, over_budget: bool,
                 budget: dict[str, float] = BUDGET) -> None:
    """Refuse a round whose estimate is over its pipeline's budget, unless `over_budget`.
    A round with no estimate passes: there is nothing to check it by."""
    if estimate is None or over_budget or estimate <= budget[pipeline]:
        return
    raise SystemExit(f"The round is estimated at {estimate:.0f} tokens, over the {pipeline} "
                     f"budget of {budget[pipeline]:.0f}. Ask fewer tasks, or give "
                     "--over-budget to run it anyway.")


@dataclass
class RoundToPlan:
    """A round to plan: its pipeline, arm and model, and each task it covers by id."""

    pipeline: str
    arm: str
    model: str
    tasks: list[str]


@dataclass
class RoundPlan:
    """A planned round: the tasks to ask, the estimate in tokens (None with no past rows), and
    the plan as text."""

    asked: list[str]
    tokens: float | None
    text: str


def plan_round(asking: RoundToPlan, key_of: Callable[[str, str], Key], fresh: bool,
               over_budget: bool, local: Path = LOCAL,
               budget: dict[str, float] = BUDGET) -> RoundPlan:
    """Plan a round: each task asked and why, or taken from the memo, the estimate from the
    ledger, and the budget check, which refuses a round over its pipeline's budget unless
    `over_budget`."""
    planned = memo_plan(asking.tasks, key_of, fresh, local / "memo")
    asked = [one.task for one in planned if one.kept is None]
    tokens = estimated_tokens(read_ledger(local), asking.pipeline, asking.arm, asking.model,
                              len(asked))
    check_budget(asking.pipeline, tokens, over_budget, budget)
    lines = []
    for one in planned:
        if one.kept is None:
            lines.append(f"{one.task}: ask: {one.reason}")
        else:
            lines.append(f"{one.task}: from the memo, {one.kept.key.file_name()}")
    lines.append(f"Ask {len(asked)} of {len(planned)}; {len(planned) - len(asked)} from "
                 "the memo.")
    lines.append(_estimate_line(tokens, budget[asking.pipeline]))
    return RoundPlan(asked, tokens, "\n".join(lines))


def _estimate_line(tokens: float | None, limit: float) -> str:
    """The plan's last line: the estimate and the budget it was checked against."""
    if limit == math.inf:
        budget_text = "budget: no limit"
    elif tokens is not None and tokens > limit:
        budget_text = f"over budget: {limit:.0f} tokens"
    else:
        budget_text = f"budget: {limit:.0f} tokens"
    if tokens is None:
        return f"No estimate: the ledger has no past row of this pipeline, arm and model; "\
               f"{budget_text}."
    return f"Round estimated {tokens:.0f} tokens from past ledger rows ({budget_text})."


# --- The commands ----------------------------------------------------------------------------


def _record(given: argparse.Namespace) -> int:
    """Add the row `record` was given to the ledger."""
    run = Run(date=given.date, commit=given.commit, round=given.round, pipeline=given.pipeline,
              task=given.task, arm=given.arm, model=given.model, role=given.role,
              tokens=given.tokens, seconds=given.seconds, result=given.result)
    path = record_run(run, given.local)
    print(f"Recorded {run.pipeline} {run.task} ({run.tokens} tokens) in {path.name}.")
    return 0


def _print_ledger(given: argparse.Namespace) -> int:
    """Print the ledger's rows and their total tokens."""
    rows = read_ledger(given.local)
    for row in rows:
        print(",".join(getattr(row, name) for name in LEDGER_FIELDS))
    total = sum(float(row.tokens) for row in rows)
    print(f"{len(rows)} runs, {total:.0f} tokens.")
    return 0


def _carry_over(given: argparse.Namespace) -> int:
    """Copy the old memo's replies into the new memo."""
    copied = carry_over(given.old, given.local / "memo")
    print(f"Carried over {copied} replies from {given.old.name}.")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run `record`, `ledger` or `carry-over`; each takes `--local`, the folder it keeps its
    records in, which is `.eval-local/` but for a test's."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    commands = parser.add_subparsers(dest="command", required=True)
    record = commands.add_parser("record", help="add an agent's run to the ledger")
    for name in ("pipeline", "round", "task", "arm", "model", "role", "tokens", "seconds",
                 "result"):
        record.add_argument(f"--{name}", required=True)
    record.add_argument("--commit", default="", help="the commit the run was made on")
    record.add_argument("--date", default=date.today().isoformat())
    ledger = commands.add_parser("ledger", help="print the ledger")
    carry = commands.add_parser("carry-over", help="copy the old memo into the new one")
    carry.add_argument("--old", type=Path, default=OLD_MEMO)
    for command in (record, ledger, carry):
        command.add_argument("--local", type=Path, default=LOCAL)
    given = parser.parse_args(argv)
    run_command = {"record": _record, "ledger": _print_ledger, "carry-over": _carry_over}
    return run_command[given.command](given)


if __name__ == "__main__":
    raise SystemExit(main())
