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
    .venv/Scripts/python tools/eval_runs.py copy-records

- **The local folder**, `LOCAL`: `.eval-local/`, made on first use. `make_local_path` is the one
  way to a path in it and refuses a path that would leave it.
- **The ledger**, `.eval-local/ledger.csv`: one row (`Run`) per agent run, written by `record`
  from the usage the agent reported when it finished, and read by `read_ledger`.
- **The memo**, `.eval-local/memo/`: each reply kept in one plain file under a `Key`: its
  task's id and the hash of its text, the arm, the model, and the hash of exactly the text the
  task loads. A reply is asked again only when one of those changes, held-out tasks included.
  (`files_version` in a key is read from replies kept before every pipeline moved onto this
  module, which keyed a held-out reply by the Copilot files' version too; a key made now
  leaves it out.)
- **A plan**, `plan_round`: each task of a round, asked and why, or taken from the memo; the
  round's estimated tokens, the mean of the past ledger rows of the same pipeline, arm and
  model for each task asked; and the check against the pipeline's `BUDGET`.
- **A round by script**, for the pipelines of proxies (the Copilot and Excel evaluations):
  `Pipeline` and `add_round_commands` give each tool its `plan`, `prompts`, `template`,
  `batch`, `collect` and `score`. `batch` writes a round's folder under
  `.eval-local/<pipeline>/runs/<round>/`, a message file per proxy, and prints one line per
  proxy, `copilot-proxy | <model> | <prompt>`; `collect` merges the proxies' answers files.
- **Budgets**, `BUDGET`: `{pipeline: math.inf}` until the ledger has the data to set one, so a
  budget is one edit. A round over it is refused unless `--over-budget` is given.
"""

from __future__ import annotations

import argparse
import csv
import functools
import hashlib
import json
import math
import re
import shutil
from collections.abc import Callable
from dataclasses import asdict, dataclass, fields
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
    if "maintainer" in (run.pipeline, run.role):
        check_maintainer_run(run)
    for name in ("tokens", "seconds"):
        if not re.fullmatch(r"\d+(\.\d+)?", getattr(run, name)):
            raise SystemExit(f"The ledger's {name} is a number of at least 0, not "
                             f"{getattr(run, name)!r}.")


def check_maintainer_run(run: Run) -> None:
    """Refuse a maintainer row whose role or task isn't one of the agents' or whose result
    doesn't start with "clean" or "opened"."""
    if (run.pipeline != "maintainer" or run.role != "maintainer"
            or run.task not in MAINTAINER_AGENTS):
        raise SystemExit(f"A maintainer run has the pipeline and role maintainer and, as its "
                         f"task, one of {', '.join(MAINTAINER_AGENTS)}, not "
                         f"{run.pipeline!r}, {run.role!r} and {run.task!r}.")
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


# Where the records were kept in `.scratch/` while git held them, and where each goes under the
# local folder (ticket 02). The memo's replies go through `carry_over`.
OLD_RECORDS = {
    ".scratch/usability-loop/runs": "usability/runs",
    ".scratch/usability-loop/results.md": "usability/results.md",
    ".scratch/copilot-eval/runs": "copilot/runs",
    ".scratch/copilot-eval/results.md": "copilot/results.md",
}


def copy_records(root: Path = ROOT, local: Path = LOCAL) -> int:
    """Copy each old record under `root`'s `.scratch/` (see `OLD_RECORDS`), and the old memo's
    replies, into `local`, skipping a file already there. Nothing is deleted. Returns how many
    files were copied."""
    copied = 0
    for old, new in OLD_RECORDS.items():
        source = root / old
        if source.is_file():
            pairs = [(source, local / new)]
        else:
            pairs = [(path, local / new / path.relative_to(source))
                     for path in sorted(source.rglob("*")) if path.is_file()]
        for path, target in pairs:
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, target)
                copied += 1
    return copied + carry_over(root / ".scratch" / "copilot-eval" / "memo", local / "memo")


# --- A round's plan --------------------------------------------------------------------------


@dataclass
class Planned:
    """What a round's plan says of a task: why it is asked, or the reply kept for it."""

    task: str
    reason: str  # why it is asked, or "" when its kept reply is taken
    kept: Kept | None


def memo_plan(tasks: list[str], key_of: Callable[[str, str], Key], fresh: bool,
              folder: Path = MEMO, held_out: frozenset[str] = frozenset()) -> list[Planned]:
    """Whether a round asks each task, and why, or the reply kept for it: asked when no reply
    is kept under the key it has now, and with `fresh` whatever is kept but a held-out task's,
    which is asked once per version of the text it loads, however often a round is fresh."""
    plan = []
    for task in tasks:
        kept = kept_reply(task, key_of, folder)
        if kept is None:
            plan.append(Planned(task, _why_asked(task, key_of, folder), None))
        elif fresh and task not in held_out:
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
    """A round to plan: its pipeline, arm and model, and each task it covers by id. `held_out`
    names the tasks `--fresh` doesn't ask again. `agents` says how many agents (proxies) the
    tasks asked take, where a proxy takes several; the estimate is by agent, as the ledger has
    a row per agent. By default each task is an agent."""

    pipeline: str
    arm: str
    model: str
    tasks: list[str]
    held_out: frozenset[str] = frozenset()
    agents: Callable[[list[str]], int] | None = None


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
    planned = memo_plan(asking.tasks, key_of, fresh, local / "memo", asking.held_out)
    asked = [one.task for one in planned if one.kept is None]
    agents = len(asked) if asking.agents is None else asking.agents(asked)
    tokens = estimated_tokens(read_ledger(local), asking.pipeline, asking.arm, asking.model,
                              agents)
    check_budget(asking.pipeline, tokens, over_budget, budget)
    lines = []
    for one in planned:
        if one.kept is None:
            lines.append(f"{one.task}: ask: {one.reason}")
        else:
            lines.append(f"{one.task}: from the memo, {one.kept.key.file_name()}")
    lines.append(f"Ask {len(asked)} of {len(planned)}; {len(planned) - len(asked)} from "
                 "the memo.")
    if asking.agents is not None:
        lines.append(f"Spawn {agents} proxies.")
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


# --- A round by script -----------------------------------------------------------------------
#
# A round of a proxy pipeline (the Copilot and Excel evaluations) is: `plan`, which tasks to
# ask; `batch`, which writes each proxy's message file and prints one line per proxy to spawn;
# the session spawns them; `collect`, which merges their answers files into the round's;
# `score`, which scores and keeps them; and `record` per proxy from its reported usage. Each
# round is a folder, `<local>/<pipeline>/runs/<round>/`, with a folder per proxy.

ROUND_FILE = "round.json"
MESSAGE_FILE = "message.md"
ANSWERS_FILE = "answers.md"
# The agent type a proxy is spawned as.
PROXY_AGENT = "copilot-proxy"
# The results file both the Copilot and the Excel evaluations add a row to, under the local
# folder.
RESULTS = ("copilot", "results.md")


def files_version(folder: Path = ROOT / "copilot") -> str:
    """The Copilot files' version: one hash of every file in `folder`, by its path and its
    bytes, each line ending read as \\n, cut to 12 characters."""
    digest = hashlib.sha256()
    for path in sorted(folder.rglob("*")):
        if path.is_file():
            digest.update(path.relative_to(folder).as_posix().encode("utf-8") + b"\0")
            digest.update(path.read_bytes().replace(b"\r\n", b"\n") + b"\0")
    return digest.hexdigest()[:12]


@dataclass
class Batch:
    """A round of proxies: its pipeline, name, arm and model, the date, every task it covers
    (those asked and those taken from the memo), and each proxy's tasks by the proxy's name."""

    pipeline: str
    name: str
    arm: str
    model: str
    date: str
    tasks: list[str]
    proxies: dict[str, list[str]]


def path_for_proxy(path: Path) -> str:
    """A path as the proxy is told it: from the repo's root where it lies under it."""
    resolved = path.resolve()
    if resolved.is_relative_to(ROOT):
        return resolved.relative_to(ROOT).as_posix()
    return str(resolved)


def write_batch(batch: Batch, messages: dict[str, str], local: Path = LOCAL) -> list[str]:
    """Write a round's folder: its `round.json` and each proxy's message file. Returns one line
    per proxy, giving the agent type, the model and the one-line prompt to spawn it with.
    Refuses a round name already used, so a round's answers are never mixed with another's."""
    round_file = make_local_path(batch.pipeline, "runs", batch.name, ROUND_FILE, local=local)
    if round_file.exists():
        raise SystemExit(f"The round {batch.name!r} exists: name a new one, or `collect` "
                         "and `score` it.")
    round_file.write_text(json.dumps(asdict(batch), indent=1), encoding="utf-8")
    lines = []
    for proxy in batch.proxies:
        message = make_local_path(batch.pipeline, "runs", batch.name, proxy, MESSAGE_FILE,
                                  local=local)
        message.write_text(messages[proxy], encoding="utf-8")
        answers = message.with_name(ANSWERS_FILE)
        lines.append(f"{PROXY_AGENT} | {batch.model} | Read {path_for_proxy(message)} and "
                     f"write your reply to {path_for_proxy(answers)}, as told.")
    return lines


def read_batch(pipeline: str, name: str, local: Path = LOCAL) -> Batch:
    """A round written by `write_batch`."""
    path = local / pipeline / "runs" / name / ROUND_FILE
    if not path.is_file():
        raise SystemExit(f"There is no round {name!r}: `batch` writes it.")
    return Batch(**json.loads(path.read_text(encoding="utf-8")))


def read_answers(text: str, letter: str) -> tuple[dict[str, str], dict[str, str]]:
    """An answers file's header, by name, and each reply, by its task's id: a heading such as
    `## T07` for the Copilot tasks, `letter` "T", and `## X07` for the Excel tasks."""
    parts = re.split(rf"^## ({letter}\d+)\s*$", text, flags=re.MULTILINE)
    header = dict(re.findall(r"^(\w+):[ \t]*(.*?)[ \t]*$", parts[0], re.MULTILINE))
    return header, {parts[i]: parts[i + 1] for i in range(1, len(parts), 2)}


@dataclass
class Collected:
    """What `collect` found: the answers file it wrote, the proxies with no answers file, and
    the tasks no proxy's file answers."""

    path: Path
    no_file: list[str]
    no_reply: list[str]


def collect_batch(pipeline: str, name: str, letter: str, local: Path = LOCAL,
                  files: str | None = None) -> Collected:
    """Merge each proxy's answers file of a round into the round's `answers.md`, under a
    header that gives its date, arm, model, the Copilot files' version and every task of the
    round. A proxy's reply is taken only for a task it was given."""
    batch = read_batch(pipeline, name, local)
    folder = local / pipeline / "runs" / name
    if files is None:
        files = files_version()
    header = [f"date: {batch.date}", f"arm: {batch.arm}", f"model: {batch.model}",
              f"files: {files}", f"round: {batch.name}",
              f"round_tasks: {','.join(batch.tasks)}"]
    body, no_file, no_reply = [], [], []
    for proxy, tasks in batch.proxies.items():
        path = folder / proxy / ANSWERS_FILE
        if not path.is_file():
            no_file.append(proxy)
            no_reply += tasks
            continue
        _, replies = read_answers(path.read_text(encoding="utf-8"), letter)
        for task in tasks:
            if task in replies:
                body.append(f"\n## {task}\n{replies[task].rstrip()}\n")
            else:
                no_reply.append(task)
    answers = make_local_path(pipeline, "runs", name, ANSWERS_FILE, local=local)
    answers.write_text("\n".join(header) + "\n" + "".join(body), encoding="utf-8")
    return Collected(answers, no_file, no_reply)


def chunks(items: list[str], size: int) -> list[list[str]]:
    """`items` in order, in lists of at most `size`."""
    return [items[start:start + size] for start in range(0, len(items), size)]


# --- Scoring a round -------------------------------------------------------------------------


@dataclass
class RoundReplies:
    """The replies a round scores, by task in the round's order, those of them taken from the
    memo, each task of the round, and the key of a task's reply."""

    tasks: list[str]
    replies: dict[str, str]
    taken: dict[str, Kept]
    key_of: Callable[[str, str], Key]
    folder: Path


def check_answers_header(header: dict[str, str], arms: list[str]) -> None:
    """Refuse an answers file whose header doesn't give its arm and its model, which the memo
    keeps each reply by."""
    arm, model = header.get("arm", ""), header.get("model", "")
    if arm not in arms or not model or model.startswith("<"):
        raise SystemExit(f"The answers file's header gives arm {arm or 'none'} and model "
                         f"{model or 'none'}. The memo keeps each reply by its arm, one of "
                         f"{', '.join(arms)}, and its model, such as haiku: fill both in.")


def round_replies(header: dict[str, str], answered: dict[str, str], tasks: list[str],
                  memo_key: Callable[..., Key], arms: list[str], folder: Path = MEMO
                  ) -> RoundReplies:
    """The replies a round scores: the answers file's, and for each task of the round it
    doesn't answer, the reply kept under the task's key now. The arm and the model are the
    header's. `memo_key(task, reply, arm=, model=)` is the pipeline's own."""
    check_answers_header(header, arms)
    key_of = functools.partial(memo_key, arm=header["arm"], model=header["model"])
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


def keep_round(found: RoundReplies, scores: dict[str, str], asked: str) -> None:
    """Keep each reply a round scored with its new score line: a new reply as asked on
    `asked`, a kept one as it was asked."""
    for task, reply in found.replies.items():
        asked_on = found.taken[task].asked if task in found.taken else asked
        write_kept(Kept(found.key_of(task, reply), asked_on, scores[task], reply), found.folder)


def memo_line(found: RoundReplies) -> str:
    """How many of a round's replies came from the memo, and each task with no reply."""
    line = f"{len(found.taken)} of {len(found.replies)} replies from the memo"
    missing = [task for task in found.tasks if task not in found.replies]
    if missing:
        line += f"; no reply, in the answers file or the memo, for {', '.join(missing)}"
    return line + "."


# --- A proxy pipeline's round commands -------------------------------------------------------


@dataclass
class Pipeline:
    """What a proxy pipeline (the Copilot or the Excel evaluation) gives the round commands:
    its name, the letter of its task ids, its arms, its tasks and how a round chooses them, how
    a task's reply is keyed, how the tasks asked are cut among proxies, and the texts it writes.
    `chosen(given)` is the tasks `--split` and the tool's own filter name; `filtered(given)`
    says whether the command gave a filter at all."""

    name: str
    letter: str
    arms: list[str]
    all_tasks: list[str]
    held_out: Callable[[str], bool]
    chosen: Callable[[argparse.Namespace], list[str]]
    filtered: Callable[[argparse.Namespace], bool]
    add_filters: Callable[[argparse.ArgumentParser, str | None], argparse.ArgumentParser]
    memo_key: Callable[..., Key]
    proxy_groups: Callable[[str, list[str]], dict[str, list[str]]]
    proxy_message: Callable[[str, list[str]], str]
    prompts: Callable[[list[str]], str]
    template: Callable[[list[str]], str]


def add_round_commands(commands: argparse._SubParsersAction[argparse.ArgumentParser],
                       pipe: Pipeline) -> None:
    """A proxy pipeline's commands: `plan`, `prompts`, `template` and `batch`, each of an arm
    and a round's tasks; `collect` of a round; and `score` of a round or an answers file."""
    for name in ("plan", "prompts", "template", "batch"):
        command = pipe.add_filters(commands.add_parser(name), "dev")
        command.add_argument("arm", choices=pipe.arms)
        command.add_argument("--model", required=True,
                             help="the model asked, such as haiku, or copilot-web by hand")
        command.add_argument("--fresh", action="store_true",
                             help="ask every dev task again, kept or not")
        command.add_argument("--over-budget", action="store_true",
                             help="run a round estimated over its pipeline's budget")
        if name == "batch":
            command.add_argument("--round", required=True, help="the new round's name")
    collect = commands.add_parser("collect")
    collect.add_argument("round")
    scoring = pipe.add_filters(commands.add_parser("score"), None)
    scoring.add_argument("target", help="a round's name, or an answers file")
    scoring.add_argument("--record", type=Path,
                         help="the results file, `<local>/copilot/results.md` by default")
    for command in commands.choices.values():
        command.add_argument("--local", type=Path, default=LOCAL, help=argparse.SUPPRESS)


def plan_for(pipe: Pipeline, given: argparse.Namespace) -> RoundPlan:
    """The plan of the round a `plan`, `prompts`, `template` or `batch` command names."""
    tasks = pipe.chosen(given)

    def proxies_for(asked: list[str]) -> int:
        return len(pipe.proxy_groups(given.arm, asked))
    asking = RoundToPlan(pipe.name, given.arm, given.model, tasks,
                         frozenset(task for task in tasks if pipe.held_out(task)),
                         agents=proxies_for)
    key_of = functools.partial(pipe.memo_key, arm=given.arm, model=given.model)
    return plan_round(asking, key_of, given.fresh, given.over_budget, given.local)


# What `prompts`, `template` and `batch` say when the memo keeps every reply of a round.
NOTHING_TO_ASK = ("Nothing to ask: the memo keeps a reply to every task of this round, as "
                  "plan shows. Score the round to score them again.")


def run_round_command(pipe: Pipeline, given: argparse.Namespace) -> int:
    """Run `plan`, `prompts`, `template`, `batch` or `collect`, and return the exit code."""
    if given.command == "collect":
        return _collect(pipe, given)
    plan = plan_for(pipe, given)
    if given.command == "plan":
        print(plan.text)
    elif not plan.asked and given.command != "batch":
        print(NOTHING_TO_ASK)
    elif given.command == "prompts":
        print(pipe.prompts(plan.asked))
    elif given.command == "template":
        print(pipe.template(plan.asked))
    else:
        _batch(pipe, given, plan)
    return 0


def _batch(pipe: Pipeline, given: argparse.Namespace, plan: RoundPlan) -> None:
    """Write the round's folder and print one line per proxy to spawn; a round that asks
    nothing says so and has no proxy, and is scored from the memo."""
    groups = pipe.proxy_groups(given.arm, plan.asked) if plan.asked else {}
    messages = {proxy: pipe.proxy_message(given.arm, tasks) for proxy, tasks in groups.items()}
    batch = Batch(pipe.name, given.round, given.arm, given.model, date.today().isoformat(),
                  pipe.chosen(given), groups)
    lines = write_batch(batch, messages, given.local)
    print("\n".join(lines) if lines else NOTHING_TO_ASK)


def _collect(pipe: Pipeline, given: argparse.Namespace) -> int:
    """Merge a round's answers files; say what is missing, and exit 1 if any is."""
    found = collect_batch(pipe.name, given.round, pipe.letter, given.local)
    print(f"Wrote {found.path.name} of round {given.round}.")
    if found.no_file:
        print(f"No answers file from {', '.join(found.no_file)}.")
    if found.no_reply:
        print(f"No reply for {', '.join(found.no_reply)}.")
    return 1 if found.no_reply else 0


def answers_to_score(pipe: Pipeline, given: argparse.Namespace
                     ) -> tuple[dict[str, str], dict[str, str], list[str]]:
    """What `score` reads: the answers file's header and replies, and the tasks of the round it
    scores. `target` is a round's name or an answers file. The round's tasks are the filters'
    where given, else the round's own (its header's `round_tasks`), else those answered."""
    in_round = given.local / pipe.name / "runs" / given.target / ANSWERS_FILE
    path = in_round if in_round.is_file() else Path(given.target)
    header, answered = read_answers(path.read_text(encoding="utf-8"), pipe.letter)
    if pipe.filtered(given):
        tasks = pipe.chosen(given)
    elif header.get("round_tasks"):
        tasks = header["round_tasks"].split(",")
    else:
        tasks = [task for task in pipe.all_tasks if task in answered]
    return header, answered, tasks


def results_path(given: argparse.Namespace) -> Path:
    """Where `score` adds its row: `--record`, or the Copilot results in the local folder."""
    if given.record:
        return given.record
    return make_local_path(*RESULTS, local=given.local)


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


def _copy_records(given: argparse.Namespace) -> int:
    """Copy the records git no longer holds from `.scratch/` into the local folder."""
    copied = copy_records(given.root, given.local)
    print(f"Copied {copied} files into {given.local.name}/.")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Run `record`, `ledger`, `carry-over` or `copy-records`; each takes `--local`, the folder
    it keeps its records in, which is `.eval-local/` but for a test's."""
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
    copy = commands.add_parser("copy-records", help="copy the old records of .scratch/ into "
                               "the local folder; run it before merging the commit that "
                               "untracks them, which deletes them from a checkout")
    copy.add_argument("--root", type=Path, default=ROOT)
    for command in (record, ledger, carry, copy):
        command.add_argument("--local", type=Path, default=LOCAL)
    given = parser.parse_args(argv)
    run_command = {"record": _record, "ledger": _print_ledger, "carry-over": _carry_over,
                   "copy-records": _copy_records}
    return run_command[given.command](given)


if __name__ == "__main__":
    raise SystemExit(main())
