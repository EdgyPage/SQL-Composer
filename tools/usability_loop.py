"""The usability loop: zero-context agents run a Workflow, or the Excel path, from what main
ships, and each run is scored against its scenario's answer key (Toolbox 8.2, ticket 02; the
map's Notes, "The loop"). `docs/usability-loop.md` says how a round is run.

    python tools/usability_loop.py plan W1 W8
    python tools/usability_loop.py prepare W1 2026-11-01-W1-1
    python tools/usability_loop.py route 2026-11-01-W1-1 "<the agent's question>"
    python tools/usability_loop.py answer 2026-11-01-W1-1 1 07_convert_hive.txt \
        --attach my_work/book.xlsx
    python tools/usability_loop.py score W1 2026-11-01-W1-1 --record "<a note>"
    python tools/usability_loop.py usage 2026-11-01-W1-1 phase-1 --tokens 51000 --seconds 90 \
        --result done
    python tools/usability_loop.py migrate

The loop is a script over `tools/eval_runs.py` (evaluation system, ticket 05): `prepare` prints
one line for each phase's agent to spawn, and `route` and `answer` one for each Copilot proxy,
each `<agent type> | <model> | <prompt>`; the session spawns them, and `usage` records each
agent's reported tokens and seconds in the ledger. Every record is kept under `.eval-local/`,
which is not committed: the memo, the ledger, each scored run (`usability/runs/`, its phase
replies and its questions the transcript) and `usability/results.md`.

A scenario is a folder in `tools/usability_scenarios/`: `scenario.json` (its id, split, title,
the Hive its team's warehouse ran already, the files the user is given, any Project they
start from, as `project`, a folder of dev's, or `start_from`, another scenario whose reference
end makes it, and each phase: a role and the job in the user's words) and `key.json`, its
answer key (each table the end goal holds, with its columns and rows, and each file it holds,
from the Project's folder, with any text it must hold), never copied into a run; and
`reads.json`, what its path reads of main.

A run's folder is made outside the repo, in the computer's temporary folder, so an agent finds
nothing of dev's around it; its agents run Python from a virtual environment outside the repo
too (the doc says how to make it). It holds what the user has:

- `main/`, the Clean tree, built from dev's last commit by the export's own builder: what a
  user downloads;
- `from_your_team/`, the scenario's files, such as a script or a workbook;
- `my_work/`, empty, where the agents keep what they make;
- `my_project/`, when the scenario starts from a Project: its folder, each notebook's
  `connect(...)` line given the team's connection (its warehouse.py's `conn`, in a Project
  from before 8.6);
- `team_connection.py`, their team's connection, `conn`, to a warehouse that keeps each table
  between processes (`tools/workflow_warehouse.py`'s SavedWarehouse), holding the Example
  database's tables and what the scenario's Hive wrote;
- `run_notebook.py`, which runs a notebook's cells as Jupyter's Run All does
  (`tools/notebook_runner.py`);
- `_loop/`, which only the loop reads: the warehouse's file and its code, with dev's Example
  database (`example_database/`), which main doesn't ship, each phase's message, each
  question, each Copilot message and reply, each agent's reply, and `inputs.json`, what the
  run was given.

Scored with `--record`, a run's folder, but for `main/` and any copy of the Toolbox's
folder, is copied into `.eval-local/usability/runs/`, a row added to
`.eval-local/usability/results.md`, naming its inputs, and the run kept in the memo.

The inputs, recorded and memoized (Toolbox 8.6, ticket 11). `inputs.json` holds the
scenario, dev's commit, and a hash of each thing an agent is given, each file's export stamp
left out: main by part (Toolbox 8.7, ticket 01), the Toolbox folder whole, the README by `##`
section, each how-to and each Copilot file, and each other file of main the phases name; what
the scenario's path reads of main, its `reads.json`: README sections, how-tos and Copilot
files; the Project brought in, file by file, but for its copy of the Toolbox; the team's
warehouse as set up; the scenario's own files, its key among them; each phase's message, with
the run's folder and the agents' Python left out; and the files the loop puts beside them. Its
`inputs_hash` is made from those but for the parts of main the scenario doesn't list, the
commit left out, so a commit that changes none of what it reads keeps it; `plan` names each
input that changed since the scenario's last recorded run. Main's tree is built once
per commit into `<temp>/usability-loop/cache/main/<commit>/`, and each scenario's warehouse
and Project once per commit into `cache/scenarios/<commit>/<scenario>-<hash>/`, the hash that
of the scenario's files, any folder of dev's its Project is copied from and the files of any
scenario it starts from, then copied into each run; building a new commit's tree drops the
other commits' caches. Each is built into a folder of its own and renamed into place, and a
prepare holds the cache's lock, `cache/prepare.lock`, while it builds, drops or copies, so
prepares may run at once: one waits for another's lock, then refuses, naming it.

The memo is `eval_runs`' (`.eval-local/memo/`). A run is kept under the key of its slot, the
run's number in its round: the scenario and the number, `W1-2`; the arm `run`; the model
`haiku`; the hash of the scenario's text; and, as the text it loads, its `inputs_hash`, or
for a held-out scenario the Toolbox version, so it runs once a version. `plan` says of each
scenario whether it is memoized: as many slots as a round gives it (one, `ROUND_RUNS`) hold a
run that passed with its inputs, and none holds one that failed. It estimates the round's
tokens from the ledger's past phase agents, and refuses a round over the usability budget
unless given `--over-budget`. `prepare` refuses a memoized
scenario, or a slot holding a run that passed, naming its runs, unless given `--fresh`.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime
import functools
import hashlib
import json
import math
import re
import shutil
import sys
import tempfile
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
# Dev's Example database, which the run's warehouse imports beside it.
EXAMPLE_DATABASE = ROOT / "example_database"
sys.path[:0] = [str(ROOT)]

import eval_runs  # noqa: E402
import eval_sources  # noqa: E402
import export_clean  # noqa: E402
import openpyxl  # noqa: E402
from formula_workbook import row_label  # noqa: E402
from workflow_warehouse import SavedWarehouse  # noqa: E402

from sqlglot_composer import notebooks, workflows  # noqa: E402
from sqlglot_composer.shared import counted, in_words  # noqa: E402

SCENARIOS = TOOLS / "usability_scenarios"
# Where the records are kept: the evaluation system's local folder. A test gives another.
LOCAL = eval_runs.LOCAL
# The agents the loop has the session spawn, and the model each runs on.
USER_AGENT = "zero-context-user"
PROXY_AGENT = "copilot-proxy"
MODEL = "haiku"
# The arm a kept run has in the memo, and the arms of a phase agent's and of a routed
# question's ledger rows.
MEMO_ARM = "run"
PHASE_ARM = "phase"
QUESTION_ARM = "question"
# Where runs are made, and the Python their agents run: outside the repo, so nothing of dev's
# is near them.
OUTSIDE = Path(tempfile.gettempdir()) / "usability-loop"
RUNS = OUTSIDE / "runs"
PYTHON = OUTSIDE / "python" / "Scripts" / "python.exe"
# Main's tree, built once per commit, and each scenario's warehouse and Project, set up once
# per commit (Toolbox 8.6, ticket 11).
CACHE = OUTSIDE / "cache"
# The cache's lock, a folder in it held while a prepare builds, drops or copies from it, so
# prepares may run at once; how long a prepare waits for another to let it go, in seconds,
# and how often it looks.
LOCK = "prepare.lock"
LOCK_WAIT = 300.0
LOCK_POLL = 0.5
# The runs a round gives a scenario, by its split: memoized once that many passed with its
# inputs and none failed. One a dev scenario, not three: of 264 runs to 2026-11-14, 260 passed,
# so a second and third run seldom showed anything (the user, 2026-11-14).
ROUND_RUNS = {"dev": 1, "held_out": 1}
# The Toolbox version, which keys a held-out scenario's runs in place of its inputs: a held-out
# scenario runs once a version, at its raise, not each time an input changes (the user,
# 2026-11-14).
VERSION_FILE = ROOT / "sqlglot_composer" / "version.txt"
# The export's stamp in main's version.txt and README, when it ran and from which commit: left
# out of a file's hash, as it changes with every build.
EXPORT_STAMP = re.compile(rb"exported \d{4}-\d\d-\d\d \d\d:\d\d(?: from dev commit [0-9a-f]+)?")
# A file of main a phase's message names, such as main/.github/README.md.
NAMED_IN_MAIN = re.compile(r"\bmain/([\w./-]*\w)")
# How much of an inputs hash a row of results.md names.
SHORT_HASH = 16
# Main, hashed by part (Toolbox 8.7, ticket 01): its README, by `##` section; its how-to page,
# by how-to, each an entry of the page; the Toolbox folder and the other pages of main's docs/
# (ticket 13), whole, but for the how-tos; and each Copilot file.
README = ".github/README.md"
TOOLBOX = "sqlglot_composer"
DOCS = export_clean.DOCS
HOW_TO_PAGE = f"{DOCS}/how_to.html"
COPILOT = "copilot"
HOW_TO_ENTRY = re.compile(r'<section class="entry" id="([^"]+)">.*?</section>', re.DOTALL)
# What a scenario's path reads of main, in the file beside its answer key: each kind, and how a
# name of that kind is said.
READS_FILE = "reads.json"
READ_KINDS = {"readme": "README section", "how_tos": "how-to", "copilot": "Copilot file"}

ROLE_TEXT = {
    "technical": "You are a data analyst who writes some Python and some SQL. You have never "
                 "used sqlglot Composer, and nobody has told you anything about it.",
    "non_technical": "You use Excel every day, but you don't write code or SQL, and you have "
                     "never heard of sqlglot Composer. You work through files as a person "
                     "would, one step at a time, as the instructions you find say.",
    "converter": "You are a data analyst who writes some Python and some SQL. You have never "
                 "used sqlglot Composer. A colleague left you their work in `my_work/`; nobody "
                 "has told you anything else.",
}

TEAM_CONNECTION = '''"""team_connection - your team's connection to its warehouse.

conn.query(sql) runs Hive that gives back rows, and gives them back as a pandas DataFrame;
conn.execute(sql) runs Hive that changes something.
"""

import sys

# After your own folders: a Project's own copy of the Toolbox is the one it imports.
sys.path += [{main!r}, {loop!r}]

from workflow_warehouse import SavedWarehouse  # noqa: E402

conn = SavedWarehouse({warehouse!r})
'''


@dataclass(frozen=True)
class Phase:
    """One agent's part of a run: its role, and its job in the user's words."""

    role: str
    job: str


@dataclass(frozen=True)
class Scenario:
    """A job a zero-context user is given, and the end its answer key holds."""

    id: str
    split: str  # "dev" or "held_out"
    title: str
    phases: tuple[Phase, ...]
    hive_ran: tuple[str, ...] = ()  # files of Hive the team's warehouse ran already
    given: dict[str, str] = field(default_factory=dict)  # file given, by its path from the run
    folder: Path = SCENARIOS
    # A Project the user has already, as my_project/: copied in, by its path from the repo's
    # top, or made by the reference end of the scenario it starts from, by that one's id.
    project: str = ""
    start_from: str = ""
    # What its path reads of main, by kind, as READ_KINDS names them (Toolbox 8.7, ticket 01).
    reads: dict[str, tuple[str, ...]] = field(default_factory=dict)


def read_scenario(scenario_id: str, folder: Path = SCENARIOS) -> Scenario:
    """The scenario with this id, read from its folder: scenario.json, and reads.json, what its
    path reads of main, each kind of READ_KINDS a list of names, and no other kind."""
    held = json.loads((folder / scenario_id / "scenario.json").read_text(encoding="utf-8"))
    phases = tuple(Phase(each["role"], each["job"]) for each in held["phases"])
    for phase in phases:
        if phase.role not in ROLE_TEXT:
            raise ValueError(f"{scenario_id}: a phase's role is {phase.role!r}, not "
                             f"{in_words(list(ROLE_TEXT), last='or')}")
    listed_reads = json.loads((folder / scenario_id / READS_FILE).read_text(encoding="utf-8"))
    unknown_kinds = sorted(set(listed_reads) - set(READ_KINDS))
    if unknown_kinds:
        raise ValueError(f"{scenario_id}: {READS_FILE} lists {in_words(unknown_kinds)}, but it "
                         f"lists only {in_words(list(READ_KINDS))}")
    reads = {kind: tuple(listed_reads.get(kind, [])) for kind in READ_KINDS}
    return Scenario(held["id"], held["split"], held["title"], phases,
                    tuple(held.get("hive_ran", [])), dict(held.get("given", {})), folder,
                    held.get("project", ""), held.get("start_from", ""), reads)


def read_answer_key(chosen: Scenario) -> dict[str, dict]:
    """A scenario's answer key: "tables", by name, each with its "columns" and "rows", and
    "files", each a path from the Project's folder or {"path": ..., "holds": [...]}."""
    return json.loads((chosen.folder / chosen.id / "key.json").read_text(encoding="utf-8"))


# --- Preparing a run ------------------------------------------------------------------------


def dev_commit() -> str:
    """Dev's last commit, the one main's tree is built from."""
    return export_clean.git(ROOT, "rev-parse", "HEAD")


def build_main(into: Path, commit: str) -> None:
    """The Clean tree, as main would hold it from dev's commit `commit`, built into `into`."""
    with tempfile.TemporaryDirectory() as temporary:
        committed = export_clean.committed_files(ROOT, commit, Path(temporary) / "dev")
        export_clean.build(committed, into, datetime.datetime.now(), commit)


def has_a_project(chosen: Scenario) -> bool:
    """Whether the scenario's user starts from a Project of theirs, as my_project/."""
    return bool(chosen.project or chosen.start_from)


def prepare(chosen: Scenario, run: Path, *, main: Path | None = None,
            python: Path = PYTHON, cache: Path | None = None, fresh: bool = False) -> Path:
    """A run's folder for a scenario, as the user has it before starting: main's tree (from
    `cache`, built into it once per commit, or copied from `main`), the scenario's files, the
    team's connection to a warehouse that has run the scenario's Hive, any Project the user
    starts from, and the notebook runner; then each phase's message, and what the run was
    given, `_loop/inputs.json`. A memoized scenario, or a run whose slot passed, is refused
    unless `fresh`. With no `cache`, each is made afresh, in a temporary folder."""
    if run.exists() and any(run.iterdir()):
        raise ValueError(f"{run} isn't empty: prepare each run in a folder of its own")
    if not python.is_file():
        raise FileNotFoundError(f"There is no Python for the agents at {python}: make it as "
                                "docs/usability-loop.md says, then prepare again.")
    with tempfile.TemporaryDirectory() as temporary:
        cache_folder = cache or Path(temporary)
        with hold_the_cache(cache_folder):
            given = the_inputs(chosen, cache_folder, main)
            inputs_hash = given.inputs["inputs_hash"]
            if not fresh:
                refuse_a_kept_run(chosen, run.name, inputs_hash)
            make_the_run(chosen, run, given.main_tree, given.set_up, python)
    (run / "_loop" / "inputs.json").write_text(json.dumps(given.inputs, indent=1) + "\n",
                                               encoding="utf-8")
    return run


def make_the_run(chosen: Scenario, run: Path, main_tree: Path, set_up: Path,
                 python: Path) -> None:
    """The run's folder: main's tree and the scenario's set-up copied in, the team's connection
    written and given to any Project, the notebook runner, and each phase's message."""
    (run / "_loop").mkdir(parents=True)
    (run / "my_work").mkdir()
    shutil.copytree(main_tree, run / "main")
    shutil.copytree(set_up, run, dirs_exist_ok=True)
    write_the_team_connection(run)
    if has_a_project(chosen):
        connect_the_team(run / "my_project")
    shutil.copyfile(TOOLS / "notebook_runner.py", run / "run_notebook.py")
    for number, phase in enumerate(chosen.phases, 1):
        message = phase_message(phase, run, python, bool(chosen.given), has_a_project(chosen))
        (run / "_loop" / f"phase_{number}.md").write_text(message, encoding="utf-8")
    write_questions(run, [])


class RunInputs(NamedTuple):
    """What a run of a scenario is given: its inputs, as inputs.json holds them, and the two
    folders a run is copied from, main's tree and the scenario's set-up."""

    inputs: dict[str, object]
    main_tree: Path
    set_up: Path


def the_inputs(chosen: Scenario, cache: Path, main: Path | None) -> RunInputs:
    """What a run of the scenario is given now, with main's tree (`main`, or the cache's for
    dev's commit) and the scenario's set-up in `cache`. Called while the cache is held."""
    commit = dev_commit()
    main_tree = main or cached_main(cache, commit)
    set_up = cached_scenario(chosen, cache, commit, main_tree)
    return RunInputs(inputs_of(chosen, main_tree, set_up, commit), main_tree, set_up)


@contextlib.contextmanager
def hold_the_cache(cache: Path) -> Iterator[None]:
    """Hold the cache's lock, the folder `cache/prepare.lock`, made with mkdir, which only one
    process can make, while a prepare builds, drops or copies from the cache; removed when it
    is done, however it ends. Another prepare holding it is waited for, up to LOCK_WAIT
    seconds, then refused, naming the lock."""
    cache.mkdir(parents=True, exist_ok=True)
    lock = cache / LOCK
    give_up_at = time.monotonic() + LOCK_WAIT
    while True:
        try:
            lock.mkdir()
            break
        except FileExistsError:
            if time.monotonic() >= give_up_at:
                raise TimeoutError(
                    f"Another prepare has held the usability loop's cache for {LOCK_WAIT:g} "
                    f"seconds: its lock is {lock}. Wait for that prepare to finish, then "
                    "prepare again. If no prepare is running, one was stopped while it held "
                    "the cache: delete that folder, then prepare again.") from None
            time.sleep(LOCK_POLL)
    try:
        yield
    finally:
        lock.rmdir()


def build_in_place(place: Path, build: Callable[[Path], None]) -> Path:
    """`place`, built by `build` into a folder of this call's own beside it and then renamed
    into place, so a build cut short, or one still going, is never taken for a whole one.
    When `place` is there already, nothing is built; when another build reaches it first,
    this one is discarded."""
    if place.is_dir():
        return place
    place.parent.mkdir(parents=True, exist_ok=True)
    own = Path(tempfile.mkdtemp(prefix=f"{place.name}.building-", dir=place.parent))
    try:
        build(own / place.name)
        try:
            (own / place.name).rename(place)
        except OSError:
            if not place.is_dir():
                raise
    finally:
        shutil.rmtree(own, ignore_errors=True)
    return place


def cached_main(cache: Path, commit: str) -> Path:
    """Main's tree for `commit`, from the cache, built into it the first time; building it
    drops every other commit's cache."""
    main_tree = cache / "main" / commit
    if not main_tree.is_dir():
        drop_other_commits(cache, commit)
    return build_in_place(main_tree, functools.partial(build_main, commit=commit))


def drop_other_commits(cache: Path, commit: str) -> None:
    """Remove each cached main tree and scenario set-up of a commit other than `commit`.
    Called while the cache is held, so no other prepare is copying from one."""
    for kind in ("main", "scenarios"):
        if not (cache / kind).is_dir():
            continue
        for folder in (cache / kind).iterdir():
            if folder.name != commit:
                shutil.rmtree(folder)


def cached_scenario(chosen: Scenario, cache: Path, commit: str, main_tree: Path) -> Path:
    """The scenario's set-up for `commit`, from the cache, set up into it the first time: a
    folder laid out as a run is, holding the files the scenario gives, its team's warehouse
    and any Project its user starts from, the Project's connection not yet given."""
    set_up = cache / "scenarios" / commit / f"{chosen.id}-{scenario_hash(chosen)[:12]}"
    return build_in_place(set_up, functools.partial(set_up_the_scenario, chosen,
                                                    main_tree=main_tree))


def scenario_hash(chosen: Scenario) -> str:
    """A hash of what a scenario's set-up is made from, but dev's commit: its own files, any
    folder of dev's its Project is copied from, and the files of any scenario it starts from."""
    hashed = {"scenario": tree_hashes(chosen.folder / chosen.id)}
    if chosen.project:
        hashed["project"] = tree_hashes(ROOT / chosen.project)
    if chosen.start_from:
        hashed["start_from"] = tree_hashes(chosen.folder / chosen.start_from)
    return text_hash(json.dumps(hashed, sort_keys=True))


def set_up_the_scenario(chosen: Scenario, set_up: Path, main_tree: Path) -> None:
    """Into `set_up`: the files the scenario gives, its team's warehouse, having run its Hive,
    and any Project its user starts from."""
    (set_up / "_loop").mkdir(parents=True)
    for given, source in chosen.given.items():
        (set_up / given).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(chosen.folder / chosen.id / source, set_up / given)
    warehouse = SavedWarehouse(set_up / "_loop" / "warehouse.json")
    for hive in chosen.hive_ran:
        warehouse.execute((chosen.folder / chosen.id / hive).read_text(encoding="utf-8"))
    warehouse.save()
    if has_a_project(chosen):
        bring_in_the_project(chosen, set_up, main_tree)


def write_the_team_connection(run: Path) -> None:
    """Write the team's connection to the run's warehouse, and the warehouse's code beside
    it."""
    loop = run / "_loop"
    shutil.copyfile(TOOLS / "workflow_warehouse.py", loop / "workflow_warehouse.py")
    # The warehouse holds the Example database's tables, which are dev's alone (Toolbox 8.7).
    shutil.copytree(EXAMPLE_DATABASE, loop / EXAMPLE_DATABASE.name,
                    ignore=shutil.ignore_patterns("__pycache__"))
    (run / "team_connection.py").write_text(TEAM_CONNECTION.format(
        main=str(run / "main"), loop=str(loop), warehouse=str(loop / "warehouse.json")),
        encoding="utf-8")


# What a Project's warehouse.py from before 8.6 says, before its user sets conn, and the lines
# the team's connection is given by in a Project the user has already.
EXAMPLE_CONN = "conn = example_database"
TEAMS_CONN = ("import sys  # noqa: E402\nfrom pathlib import Path  # noqa: E402\n\n"
              "sys.path.insert(0, str(Path(__file__).resolve().parent.parent))\n"
              "from team_connection import conn  # noqa: E402")
# Since 8.6, each notebook connects at its top: the lines connect(...) a notebook or Template
# holds before its user fills it in, as start() writes it or as an Example project fills it.
LINES_TO_CONNECT = ("# connect(your_connection)", "connect(example_database)")
# The lines that import the Example database, which main doesn't ship: before 8.7 from the
# Toolbox, and on dev from beside it (Toolbox 8.7, ticket 12). The team's connection takes the
# place of what they import, so they go.
EXAMPLE_IMPORTS = ("from sqlglot_composer import example_database", "import example_database")
# The lines the team's connection is given by in each, beside the Project: a connection kept
# in a file outside it, as the notebook's comment says.
TEAMS_CONNECT = ('sys.path.append({run!r})  # the folder team_connection.py is in\n'
                 "from team_connection import conn\nconnect(conn)")


def bring_in_the_project(chosen: Scenario, set_up: Path, main_tree: Path) -> None:
    """The Project the scenario's user has already, as my_project/ in the set-up `set_up`:
    copied in, or made by the reference end of the scenario it starts from, its tables in the
    set-up's warehouse, with `main_tree`'s copy of the Toolbox; its notebooks' connection is
    given in each run, by connect_the_team."""
    root = set_up / "my_project"
    if chosen.start_from:
        import usability_scenario_files  # it imports this file
        from how_to_page import times_pinned

        # Each Project action's time pinned, as the scenarios' build pins it, so the Project
        # made is the same each time, and so is its hash in the inputs.
        with times_pinned():
            usability_scenario_files.reference_end(chosen.start_from, set_up)
    else:
        shutil.copytree(ROOT / chosen.project, root)
    if not (root / "sqlglot_composer").is_dir():
        # As a Project the user made holds it: the README has them copy it in. A test's main
        # tree has no Toolbox, so dev's own copy stands in.
        toolbox = main_tree / "sqlglot_composer"
        if not toolbox.is_dir():
            toolbox = ROOT / "sqlglot_composer"
        shutil.copytree(toolbox, root / "sqlglot_composer",
                        ignore=shutil.ignore_patterns("__pycache__"))


def connect_the_team(root: Path) -> None:
    """Give the Project at `root` the team's connection, as its user would: each notebook's and
    Template's line connect(...) filled in with it, from team_connection.py beside the
    Project; and, in a Project from before 8.6, its warehouse.py's line conn =
    example_database alone, not a comment that names that line, as 8.2's does. A Project with
    neither is refused."""
    connected = False
    warehouse_py = root / "warehouse.py"
    lines = warehouse_py.read_text(encoding="utf-8").split("\n")
    if EXAMPLE_CONN in lines:
        lines[lines.index(EXAMPLE_CONN)] = TEAMS_CONN
        lines = [line for line in lines if line not in EXAMPLE_IMPORTS]
        warehouse_py.write_text("\n".join(lines), encoding="utf-8")
        connected = True
    teams = TEAMS_CONNECT.format(run=str(root.parent))
    for notebook in sorted(root.rglob("*.ipynb")):
        cells = notebooks.read_cells(notebook)
        filled = [(kind, _with_the_teams_connection(text, teams)) for kind, text in cells]
        if filled != cells:
            notebooks.write_notebook(notebook, filled)
            connected = True
    for template in sorted((root / "admin" / "templates").glob("*.py")):
        text = template.read_text(encoding="utf-8")
        template.write_text(_with_the_teams_connection(text, teams), encoding="utf-8")
    if not connected:
        raise ValueError(f"{root} has no line {EXAMPLE_CONN!r} or connect(...) to set")


def _with_the_teams_connection(text: str, teams: str) -> str:
    """A cell's or Template's text, each of its lines connect(...) the team's connection, and
    each line importing the Example database gone."""
    lines = [line for line in text.split("\n") if line not in EXAMPLE_IMPORTS]
    return "\n".join(teams if line in LINES_TO_CONNECT else line for line in lines)


def what_you_have(phase: Phase, run: Path, python: Path, given: bool = True,
                  project_given: bool = False) -> list[str]:
    """The lines of a phase's message saying what the agent has, by its role: `given`, when
    the team gave files, names `from_your_team/`, and `project_given`, when the user has a
    Project already, `my_project/`."""
    folders = ["Its `main/` folder is the Toolbox as you downloaded it, with its README "
               "(`main/.github/README.md`) and its guides, the pages in `main/docs/`."]
    if given:
        folders.append("`from_your_team/` holds what your team gave you.")
    if project_given:
        folders.append("`my_project/` is the Project you have already.")
    lines = [
        f"- Your work folder, {run}. Work only inside it. " + " ".join(folders) + " Keep what "
        "you make in `my_work/`. Leave `_loop/` alone: it isn't yours.",
    ]
    if phase.role == "non_technical":
        lines.append(f"- Excel can't open here, so open, change and save a workbook with "
                     f"Python's openpyxl, run as `{python} your_script.py`: use it only to do "
                     "what you would do by hand in Excel, typing what the instructions say.")
        return lines
    lines += [
        f"- Python: {python}. Run scripts with it.",
        "- `team_connection.py`, in your work folder: your team's warehouse connection, "
        "`conn`. Import it as `from team_connection import conn`; from a folder below your "
        f"work folder, first put the work folder on the path: `import sys; "
        f"sys.path.append(r\"{run}\")`.",
        "- Jupyter can't open here, so to run a notebook's cells top to bottom, run "
        f"`{python} {run / 'run_notebook.py'} path/to/notebook.ipynb`; to run only some of "
        "its code cells, in order, add `--cells 1-3,5` (code cells counted from 1, text cells "
        "not counted). Each run starts with nothing defined, as a kernel just restarted does, "
        "so name with each step the cells it needs: the imports cell and the names cell, and "
        "from the decisions on the decisions cell too, such as `--cells 1-3,6`. `--list` "
        "prints each code cell's number and first line: those are the numbers `--cells` "
        "takes, and a step's own number may differ. To fill in a cell without Jupyter, change "
        "its lines in the notebook's file, which is JSON: each code cell's lines are its "
        "\"source\" list, each line a JSON string with its quotes escaped, such as "
        "`\"DECISIONS = {\\\"mart_dev.t\\\": {\\\"location\\\": \\\"/data/t\\\"}}\\n\"`.",
    ]
    return lines


def phase_message(phase: Phase, run: Path, python: Path, given: bool = True,
                  project_given: bool = False) -> str:
    """What an agent is told for one phase: who it is, its job, and what it has."""
    return "\n".join([
        ROLE_TEXT[phase.role],
        "",
        "Your job, in your own words:",
        "",
        phase.job,
        "",
        "What you have:",
        *what_you_have(phase, run, python, given, project_given),
        "",
        "How to work:",
        "1. Find what you need in the files you have, and do what they say, in order.",
        "2. If you are stuck, you may ask Copilot, the help your company gives you: end your "
        "turn with one line `QUESTION: ` and your question, then, for each file you would "
        "attach in the chat, a line `ATTACH: ` and its path. You get Copilot's answer as your "
        "next message. You may ask at most "
        f"{counted(eval_runs.CAPS['usability'].turns, 'question')}.",
        "3. Run each command in the foreground and wait for it to finish before you go on.",
        "4. When the job is done, end your turn with one line `DONE: ` and what you did, or, "
        "if you can't finish it, `STUCK: ` and where you stopped.",
    ]) + "\n"


# --- Inputs, recorded and memoized (Toolbox 8.6, ticket 11) ----------------------------------


def file_hash(path: Path) -> str:
    """A file's SHA-256, in hex."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main_file_hash(path: Path) -> str:
    """A file of main's tree's SHA-256, in hex, the export's stamp left out."""
    return hashlib.sha256(EXPORT_STAMP.sub(b"exported", path.read_bytes())).hexdigest()


def text_hash(text: str) -> str:
    """Some text's SHA-256, in hex."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def tree_hashes(folder: Path, hash_of: Callable[[Path], str] = file_hash,
                leave_out: tuple[str, ...] = ("__pycache__",)) -> dict[str, str]:
    """Each file of `folder`, by its path from it, and its hash; each file in a folder named
    in `leave_out` left out."""
    hashes = {}
    for path in sorted(folder.rglob("*")):
        relative = path.relative_to(folder)
        if path.is_file() and not set(relative.parts) & set(leave_out):
            hashes[relative.as_posix()] = hash_of(path)
    return hashes


def main_text(path: Path) -> str:
    """A text file of main's tree, the export's stamp left out."""
    return EXPORT_STAMP.sub(b"exported", path.read_bytes()).decode("utf-8")


def readme_sections(text: str) -> dict[str, str]:
    """A README's text, by section: each `##` heading's, from it to the next, by the heading,
    and the part above the first by the README's `#` title, or "the top" when it has none. A
    line in a ``` block starts none."""
    sections: dict[str, list[str]] = {"": []}
    heading, in_code = "", False
    for line in text.splitlines(keepends=True):
        if line.startswith("```"):
            in_code = not in_code
        elif not in_code and line.startswith("## "):
            heading = line[3:].strip()
        sections.setdefault(heading, []).append(line)
    top = "".join(sections.pop(""))
    titles = [line[2:].strip() for line in top.splitlines() if line.startswith("# ")]
    title = titles[0] if titles else "the top"
    return {title: top, **{name: "".join(lines) for name, lines in sections.items()}}


def main_parts(main: Path) -> dict[str, str | dict[str, str]]:
    """Main's tree, hashed by part, the export's stamp left out of each: `toolbox`, one hash
    of the Toolbox folder and the pages in docs/, the how-to page's how-tos left out;
    `readme`, each `##` section of the README; `how_tos`, each how-to of the how-to page, by
    its link; and `copilot`, each Copilot file, by its path from copilot/. A part main hasn't
    is empty."""
    toolbox = tree_hashes(main / TOOLBOX, main_file_hash) if (main / TOOLBOX).is_dir() else {}
    if (main / DOCS).is_dir():
        toolbox.update({f"{DOCS}/{path}": hashed for path, hashed in
                        tree_hashes(main / DOCS, main_file_hash).items()})
    how_tos = {}
    if (main / HOW_TO_PAGE).is_file():
        page = main_text(main / HOW_TO_PAGE)
        how_tos = {found[1]: text_hash(found[0]) for found in HOW_TO_ENTRY.finditer(page)}
        toolbox[HOW_TO_PAGE] = text_hash(HOW_TO_ENTRY.sub("", page))
    readme = {}
    if (main / README).is_file():
        readme = {heading: text_hash(text)
                  for heading, text in readme_sections(main_text(main / README)).items()}
    copilot = {}
    if (main / COPILOT).is_dir():
        copilot = tree_hashes(main / COPILOT, main_file_hash)
    return {"toolbox": text_hash(json.dumps(toolbox, sort_keys=True)), "readme": readme,
            "how_tos": how_tos, "copilot": copilot}


def missing_reads(chosen: Scenario, parts: dict[str, str | dict[str, str]]) -> list[str]:
    """Each name the scenario's list of what it reads holds that main's `parts` haven't, as it
    is said, such as `README section "Update"`."""
    missing = []
    for kind in READ_KINDS:
        missing += [part_in_words(kind, name) for name in chosen.reads.get(kind, ())
                    if name not in parts[kind]]
    return missing


def part_in_words(kind: str, name: str) -> str:
    """A name of what a scenario reads, as it is said, by its kind."""
    return f'{READ_KINDS[kind]} "{name}"' if kind == "readme" else f"{READ_KINDS[kind]} {name}"


def named_main_files(messages: list[str], main_tree: Path) -> dict[str, str]:
    """Each file of main's tree the phases' messages name, such as main/copilot/
    formula_workbook.xlsx, by its path from main's tree, and its hash, the export's stamp left
    out, in order of path; but for the README, which every message names and which is hashed
    section by section."""
    named = {}
    for message in messages:
        for path in NAMED_IN_MAIN.findall(message):
            if path != README and (main_tree / path).is_file():
                named[path] = main_file_hash(main_tree / path)
    return dict(sorted(named.items()))


def inputs_of(chosen: Scenario, main_tree: Path, set_up: Path,
              commit: str) -> dict[str, object]:
    """What a run of the scenario is given, as its inputs.json holds it: main by part and
    each file of it the phases name, what the scenario's path reads of main, and each other
    thing hashed; and `inputs_hash`, a hash of only what the run's agents read, as
    inputs_hashed_by_part picks it, which leaves out dev's commit, so a commit that changes
    none of it keeps it.
    Each phase's message is hashed as written for no run in particular, so every run's is the
    same. A scenario listing a name main hasn't is refused."""
    parts = main_parts(main_tree)
    missing = missing_reads(chosen, parts)
    if missing:
        raise ValueError(f"{chosen.id}'s {READS_FILE} lists {in_words(missing)}, which main "
                         "hasn't: name each by what main calls it now, then prepare again")
    messages = [phase_message(phase, Path("<run>"), Path("<python>"), bool(chosen.given),
                              has_a_project(chosen)) for phase in chosen.phases]
    project = {}
    if has_a_project(chosen):
        # Its copy of the Toolbox is main's, which main's Toolbox folder hashes already.
        project = tree_hashes(set_up / "my_project",
                              leave_out=("__pycache__", "sqlglot_composer"))
    inputs = {
        "scenario": chosen.id, "commit": commit,
        "main": {**parts, "named": named_main_files(messages, main_tree)},
        "reads": {kind: list(chosen.reads.get(kind, ())) for kind in READ_KINDS},
        "project": project,
        "warehouse": file_hash(set_up / "_loop" / "warehouse.json"),
        "scenario_files": tree_hashes(chosen.folder / chosen.id),
        "phases": [text_hash(message) for message in messages],
        "loop_files": {
            "run_notebook.py": file_hash(TOOLS / "notebook_runner.py"),
            "workflow_warehouse.py": file_hash(TOOLS / "workflow_warehouse.py"),
            "example_database": text_hash(json.dumps(tree_hashes(EXAMPLE_DATABASE),
                                                     sort_keys=True)),
            "team_connection.py": text_hash(TEAM_CONNECTION),
            # The lines that give a Project brought in the team's connection.
            "warehouse.py's conn line": text_hash(TEAMS_CONN),
            "each notebook's connect lines": text_hash(TEAMS_CONNECT)},
    }
    hashed_by_part = inputs_hashed_by_part(inputs)
    return {**inputs, "inputs_hash": text_hash(json.dumps(hashed_by_part, sort_keys=True))}


def inputs_hashed_by_part(inputs: dict[str, object]) -> dict[str, str]:
    """What a run's inputs hash is made from, each part by what it is, as plan names one that
    changed, and its hash: the Toolbox folder; what the scenario's path reads of main, each
    README section, how-to and Copilot file it lists; each file of main the phases name; each
    file of the Project brought in; the team's warehouse; each file of the scenario; each
    phase's message; each file the loop puts in; and the scenario's list of what it reads."""
    main, reads = inputs["main"], inputs["reads"]
    parts = {"the Toolbox folder": main["toolbox"]}
    for kind in READ_KINDS:
        parts |= {part_in_words(kind, name): main[kind][name] for name in reads[kind]}
    parts |= {f"main/{path}": hashed for path, hashed in main["named"].items()}
    parts |= {f"my_project/{path}": hashed for path, hashed in inputs["project"].items()}
    parts["the team's warehouse"] = inputs["warehouse"]
    parts |= {f"the scenario's {path}": hashed
              for path, hashed in inputs["scenario_files"].items()}
    parts |= {f"phase {number}'s message": hashed
              for number, hashed in enumerate(inputs["phases"], 1)}
    parts |= {f"the loop's {name}": hashed for name, hashed in inputs["loop_files"].items()}
    parts["the scenario's list of what it reads"] = text_hash(json.dumps(reads, sort_keys=True))
    return parts


@dataclass(frozen=True)
class RecordedRun:
    """A row of results.md: its run, its scenario, whether it passed, and the start of the
    inputs hash it names, or "" in a row from before 8.6, which names none."""

    run: str
    scenario: str
    passed: bool
    inputs: str


# The inputs a row of results.md names, in its note.
ROW_INPUTS = re.compile(rf"\binputs ([0-9a-f]{{{SHORT_HASH}}})\b")


def results_file() -> Path:
    """The results.md that holds a row for each scored run."""
    return LOCAL / "usability" / "results.md"


def kept_runs_folder() -> Path:
    """The folder each scored run is kept in, by its name."""
    return LOCAL / "usability" / "runs"


def memo_folder() -> Path:
    """The eval_runs memo's folder, where each run is kept under the key of its slot."""
    return LOCAL / "memo"


def read_recorded_runs(results: Path) -> list[RecordedRun]:
    """Each run results.md records, in its order; none when there is no results.md."""
    if not results.is_file():
        return []
    recorded = []
    for line in results.read_text(encoding="utf-8").splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if not line.startswith("| ") or len(cells) < 7 or cells[4] not in ("pass", "fail"):
            continue
        found = ROW_INPUTS.search("|".join(cells[6:]))
        recorded.append(RecordedRun(cells[3], cells[1], cells[4] == "pass",
                                    found[1] if found else ""))
    return recorded


# --- The memo, through eval_runs --------------------------------------------------------------


def slots_of(chosen: Scenario) -> list[str]:
    """The slots a round gives a scenario, one per run: the scenario and a number, W1-2."""
    return [f"{chosen.id}-{number}" for number in range(1, ROUND_RUNS[chosen.split] + 1)]


def slot_of(chosen: Scenario, run_name: str) -> str | None:
    """The slot a run fills, by the number its name ends in, such as 2026-11-01-W1-2 for W1-2;
    None for a name that ends in none."""
    found = re.fullmatch(rf"(?:.*-)?{re.escape(chosen.id)}-(\d+)", run_name)
    return f"{chosen.id}-{found[1]}" if found else None


def require_slot(chosen: Scenario, run_name: str) -> str:
    """The slot a run fills, as `slot_of` says it; a name that ends in none is refused."""
    slot = slot_of(chosen, run_name)
    if slot is None:
        raise ValueError(f"The run {run_name!r} doesn't end in {chosen.id}- and its number, "
                         f"such as 2026-11-01-{chosen.id}-1: name each run so, so it fills a "
                         "slot of its round.")
    return slot


def task_text(chosen: Scenario) -> str:
    """What a scenario's runs are asked: its id, split and title, and each phase's job."""
    return "\n".join([chosen.id, chosen.split, chosen.title,
                      *(f"{phase.role}: {phase.job}" for phase in chosen.phases)])


def toolbox_version() -> str:
    """The Toolbox version dev is at, as its one file says."""
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def loaded_text(chosen: Scenario, inputs_hash: str) -> str:
    """What a scenario's slot is keyed on as the text it loads: a dev scenario's inputs, and a
    held-out scenario's Toolbox version, so it runs again only at the next raise."""
    return inputs_hash if chosen.split == "dev" else f"Toolbox {toolbox_version()}"


def key_of_slot(chosen: Scenario, inputs_hash: str) -> Callable[[str, str], eval_runs.Key]:
    """The memo key of a slot of the scenario given the inputs `inputs_hash`: for a dev
    scenario what its agents read is the text it loads; a held-out one is keyed by the Toolbox
    version (`loaded_text`)."""
    def key_of(slot: str, reply: str) -> eval_runs.Key:
        return eval_runs.hashed_key(slot, task_text(chosen), MEMO_ARM, MODEL,
                                    loaded_text(chosen, inputs_hash))
    return key_of


def keep_run(chosen: Scenario, inputs_hash: str, run_name: str, passed: bool,
             report: str) -> Path:
    """Keep a scored run in the memo, under the key of its slot and its inputs, in place of
    the run kept there before: its score is `pass` or `fail`, its reply the run's name, then
    `report`."""
    key = key_of_slot(chosen, inputs_hash)(require_slot(chosen, run_name), "")
    kept = eval_runs.Kept(key, datetime.date.today().isoformat(), "pass" if passed else "fail",
                          f"run: {run_name}\n{report}")
    return eval_runs.write_kept(kept, memo_folder())


def kept_run_name(kept: eval_runs.Kept) -> str:
    """The name of the run a kept reply is."""
    return kept.reply.splitlines()[0].removeprefix("run: ")


@dataclass
class SlotPlan:
    """What a round does with one slot of a scenario: whether it asks it, and why, or the run
    kept in it. A kept run that failed is asked again."""

    slot: str
    asked: bool
    why: str
    kept: eval_runs.Kept | None


def slot_plan(chosen: Scenario, inputs_hash: str, fresh: bool = False) -> list[SlotPlan]:
    """Each slot of the scenario's round: asked when no run is kept in it with these inputs,
    when the one kept failed, or with `fresh`; else its kept run, which passed."""
    plans = []
    for one in eval_runs.memo_plan(slots_of(chosen), key_of_slot(chosen, inputs_hash), fresh,
                                   memo_folder()):
        if one.kept is not None and one.kept.score != "pass":
            plans.append(SlotPlan(one.task, True,
                                  f"{kept_run_name(one.kept)} failed with these inputs",
                                  one.kept))
        else:
            plans.append(SlotPlan(one.task, one.kept is None, one.reason, one.kept))
    return plans


def is_memoized(chosen: Scenario, inputs_hash: str) -> bool:
    """Whether as many runs as a round gives the scenario passed with these inputs, and none
    failed: so running it again would show nothing new."""
    return not any(one.asked for one in slot_plan(chosen, inputs_hash))


def plan_text(chosen: Scenario, inputs_hash: str, fresh: bool = False) -> str:
    """One line saying whether the scenario is memoized, or why to run it, naming the runs
    kept with these inputs."""
    short = inputs_hash[:SHORT_HASH]
    if fresh:
        return f"{chosen.id}: run it: --fresh asks every run again, inputs {short}"
    plans = slot_plan(chosen, inputs_hash)
    kept = [one.kept for one in plans if one.kept is not None]
    passed = [kept_run_name(each) for each in kept if each.score == "pass"]
    failed = [kept_run_name(each) for each in kept if each.score != "pass"]
    if failed:
        return f"{chosen.id}: run it: {in_words(failed)} failed with these inputs, {short}"
    if not passed:
        return f"{chosen.id}: run it: no run recorded with these inputs, {short}"
    runs = f"with these inputs, {short}: {in_words(passed)}"
    if is_memoized(chosen, inputs_hash):
        return f"{chosen.id}: memoized: {counted(len(passed), 'run')} passed {runs}"
    return (f"{chosen.id}: run it: {len(passed)} of {counted(len(plans), 'run')} passed "
            f"{runs}")


def refuse_a_kept_run(chosen: Scenario, run_name: str, inputs_hash: str) -> None:
    """Refuse a scenario that is memoized, or a run whose slot holds a run that passed with
    these inputs, naming the runs: they show the docs were enough."""
    if is_memoized(chosen, inputs_hash):
        raise ValueError(f"{plan_text(chosen, inputs_hash)}. They show the docs were enough: "
                         "prepare it with --fresh to run it again.")
    slot = slot_of(chosen, run_name)
    for one in slot_plan(chosen, inputs_hash):
        if one.slot == slot and one.kept is not None and not one.asked:
            raise ValueError(f"{slot} passed with these inputs, {inputs_hash[:SHORT_HASH]}, "
                             f"in {kept_run_name(one.kept)}: it shows the docs were enough: "
                             "prepare it with --fresh to run it again.")


@dataclass
class ScenarioPlan:
    """A scenario's line of the plan, and its slots."""

    text: str
    slots: list[SlotPlan]


def plan_scenario(chosen: Scenario, cache: Path | None = None, main: Path | None = None,
                  fresh: bool = False) -> ScenarioPlan:
    """Whether the scenario is memoized, as `plan_text` says it, its inputs worked out as
    `prepare` works them out, with main's tree and its set-up from `cache`; and, when no run
    was recorded with them, what changed since its last run, as `changes_text` says it."""
    with tempfile.TemporaryDirectory() as temporary:
        cache_folder = cache or Path(temporary)
        with hold_the_cache(cache_folder):
            inputs = the_inputs(chosen, cache_folder, main).inputs
    inputs_hash = str(inputs["inputs_hash"])
    plan_line = plan_text(chosen, inputs_hash, fresh)
    held = slot_plan(chosen, inputs_hash)
    slots = slot_plan(chosen, inputs_hash, fresh=True) if fresh else held
    if any(one.kept is not None for one in held):
        return ScenarioPlan(plan_line, slots)
    return ScenarioPlan(plan_line + changes_text(chosen, inputs), slots)


def plan(chosen: Scenario, cache: Path | None = None, main: Path | None = None) -> str:
    """The scenario's line of the plan, as `plan_scenario` makes it."""
    return plan_scenario(chosen, cache, main).text


def estimate_line(slots: list[list[SlotPlan]], scenarios: list[Scenario],
                  over_budget: bool, budget: dict[str, float] = eval_runs.BUDGET) -> str:
    """The round's last line: the tokens its phase agents are estimated to use, the mean of the
    ledger's past phase agents for each (routed questions are extra), and the usability
    budget; refused when over it unless `over_budget`."""
    agents = 0
    for each, chosen in zip(slots, scenarios):
        agents += sum(one.asked for one in each) * len(chosen.phases)
    tokens = eval_runs.estimated_tokens(eval_runs.read_ledger(LOCAL), "usability", PHASE_ARM,
                                        MODEL, agents)
    eval_runs.check_budget("usability", tokens, over_budget, budget)
    limit = budget["usability"]
    if limit == math.inf:
        budget_text = "budget: no limit"
    elif tokens is not None and tokens > limit:
        budget_text = f"over budget: {limit:.0f} tokens"
    else:
        budget_text = f"budget: {limit:.0f} tokens"
    if tokens is None:
        return (f"No estimate for {counted(agents, 'phase agent')}: the ledger has no past "
                f"usability phase agent; {budget_text}.")
    return (f"Round estimated {tokens:.0f} tokens for {counted(agents, 'phase agent')} from "
            f"past ledger rows, routed questions extra ({budget_text}).")


def changes_text(chosen: Scenario, inputs: dict[str, object]) -> str:
    """What changed in the scenario's inputs since its last recorded run, from the inputs.json
    kept with it, such as `; changed since its last run, W1-3: the Toolbox folder`; or "" when
    none of its runs is kept with its inputs."""
    for each in reversed(read_recorded_runs(results_file())):
        kept_inputs = kept_runs_folder() / each.run / "_loop" / "inputs.json"
        if each.scenario != chosen.id or not kept_inputs.is_file():
            continue
        inputs_then = json.loads(kept_inputs.read_text(encoding="utf-8"))
        if "toolbox" not in inputs_then["main"]:
            return (f"; its last run, {each.run}, was recorded with main's whole tree as one "
                    "input")
        parts_then = inputs_hashed_by_part(inputs_then)
        parts_now = inputs_hashed_by_part(inputs)
        changed = [part for part, hashed in parts_now.items() if parts_then.get(part) != hashed]
        changed += [f"{part}, no longer there" for part in parts_then if part not in parts_now]
        return f"; changed since its last run, {each.run}: {in_words(changed)}"
    return ""


def migrate_results() -> int:
    """Keep in the memo each run `results.md` records, from the inputs hash in the inputs.json
    kept with it, so a scenario scored before the memo isn't run again. A run whose folder or
    scenario is gone, or whose name ends in no number, is passed over. Returns how many runs
    were kept."""
    runs_kept = 0
    for each in read_recorded_runs(results_file()):
        inputs = kept_runs_folder() / each.run / "_loop" / "inputs.json"
        if not inputs.is_file() or not (SCENARIOS / each.scenario).is_dir():
            continue
        chosen = read_scenario(each.scenario, SCENARIOS)
        if slot_of(chosen, each.run) is None:
            continue
        inputs_hash = json.loads(inputs.read_text(encoding="utf-8"))["inputs_hash"]
        keep_run(chosen, inputs_hash, each.run, each.passed, "from results.md")
        runs_kept += 1
    return runs_kept


# --- The agents to spawn, and their usage in the ledger ---------------------------------------


def spawn_line(agent: str, model: str, prompt: str) -> str:
    """One agent for the session to spawn, as one line: its type, its model and its prompt."""
    return f"{agent} | {model} | {prompt}"


# What each phase's prompt adds, outside the message the inputs hash is made from, so that
# asking for the sources changes no scenario's memo (evaluation system, ticket 06).
READ_LINE_ASK = ("End your last turn with a line `Read: ` and each file and section you "
                 "read, as `<file> <section>`, separated by commas, such as `Read: "
                 ".github/README.md Update, copilot/13_workflows.txt Steps`.")


def phase_spawn_lines(chosen: Scenario, run: Path) -> list[str]:
    """The agent of each phase of a run, in order: each starts fresh, after the one before it
    is done."""
    return [spawn_line(USER_AGENT, MODEL,
                       f"Read {run / '_loop' / f'phase_{number}.md'} and follow it. "
                       + READ_LINE_ASK)
            for number in range(1, len(chosen.phases) + 1)]


def proxy_spawn_line(message: Path, reply: Path) -> str:
    """The Copilot proxy to spawn for a message, and the file it answers in."""
    return spawn_line(PROXY_AGENT, MODEL,
                      f"Message file: {message} Answers file: {reply} No header lines.")


# What an agent's usage is recorded for: a phase's agent, or the proxy of a question's route or
# answer, by its number.
RUN_NAME = re.compile(r"(.+)-[1-9]\d*")
USAGE_OF = re.compile(r"(phase|route|answer)-([1-9]\d*)")


def record_usage(run_name: str, what: str, *, tokens: str, seconds: str, result: str,
                 round_id: str, commit: str, final: str | None = None) -> Path:
    """Add an agent's reported usage to the ledger: `what` is `phase-<n>`, `route-<n>` or
    `answer-<n>`, the agent of that phase or the proxy of that question's route or answer. A
    phase's `final` message is kept in the run's `_loop/`, for its `Read:` line."""
    found = USAGE_OF.fullmatch(what)
    if found is None:
        raise SystemExit(f"{what!r} isn't an agent of the loop: say phase-1 for a phase's "
                         "agent, or route-1 or answer-1 for a question's proxy.")
    is_phase = found[1] == "phase"
    if final is not None and is_phase:
        (RUNS / run_name / "_loop" / f"final-{found[2]}.txt").write_text(final,
                                                                        encoding="utf-8")
    run = eval_runs.Run(date=datetime.date.today().isoformat(), commit=commit, round=round_id,
                        pipeline="usability", task=f"{run_name}/{what}",
                        arm=PHASE_ARM if is_phase else QUESTION_ARM, model=MODEL,
                        role="user" if is_phase else "proxy", tokens=tokens, seconds=seconds,
                        result=result)
    return eval_runs.record_run(run, LOCAL)


# --- Questions to Copilot -------------------------------------------------------------------

COPILOT_HEAD = ("You are standing in for Microsoft Copilot in a web chat. Use no tools: answer "
                "from what is written here and what you already know.\n\n")


def read_questions(run: Path) -> list[str]:
    """The questions a run's agents have asked, in order."""
    return json.loads((run / "_loop" / "questions.json").read_text(encoding="utf-8"))


def write_questions(run: Path, questions: list[str]) -> None:
    """Keep a run's questions."""
    (run / "_loop" / "questions.json").write_text(json.dumps(questions, indent=1),
                                                  encoding="utf-8")


def chat_so_far(run: Path, question: str) -> str:
    """A chat's start, as a user starts one: the Copilot files' start file pasted, then the
    question."""
    start = (run / "main" / "copilot" / "00_start_here.txt").read_text(encoding="utf-8")
    return (COPILOT_HEAD + "The user pasted this as their first message:\n\n<<<\n" + start
            + "\n>>>\n\nThen asked:\n\n" + question + "\n\n")


def write_copilot_message(run: Path, number: int, name: str, text: str) -> tuple[Path, Path]:
    """Keep a Copilot message for a question; its path, and the path its reply goes to."""
    message = run / "_loop" / f"question_{number}_{name}.md"
    message.write_text(text + f"Write your reply under one heading, `## Q{number}`. "
                       + eval_runs.reply_cap_text("usability") + "\n", encoding="utf-8")
    return message, run / "_loop" / f"question_{number}_{name}_reply.md"


def route(run: Path, question: str) -> tuple[Path, Path]:
    """Start a chat for a question: file 00 pasted, the question, and Copilot asked which file
    to load next. The message's path, and its reply's."""
    questions = [*read_questions(run), question]
    write_questions(run, questions)
    asked = ("Reply with the Copilot file the user should load next, such as "
             "07_convert_hive.txt, with any file file 00 says goes with it, and nothing "
             "else.\n")
    return write_copilot_message(run, len(questions), "route",
                                 chat_so_far(run, question) + asked)


def workbook_text(path: Path) -> str:
    """A saved workbook as Copilot reads an attached one: each sheet's Excel Tables, row by row,
    formulas as typed, its other cells, and its defined names."""
    workbook = openpyxl.load_workbook(path)
    lines = []
    for sheet in workbook.worksheets:
        lines.append(f'Sheet "{sheet.title}"')
        in_a_table: set[str] = set()
        for table in sheet.tables.values():
            lines.append(f'  Excel Table "{table.displayName}", {table.ref}')
            rows = sheet[table.ref]
            for number, row in enumerate(rows, 1):
                in_a_table |= {cell.coordinate for cell in row}
                shown = " | ".join(str(cell.value) for cell in row)
                lines.append(f"    {row_label(table, number, len(rows))}: {shown}")
        for row in sheet.iter_rows():
            for cell in row:
                if cell.coordinate not in in_a_table and cell.value is not None:
                    lines.append(f"  {cell.coordinate}: {cell.value}")
    for name, defined in workbook.defined_names.items():
        lines.append(f"Defined name {name}: {defined.attr_text}")
    return "\n".join(lines) + "\n"


def attached_text(path: Path) -> str:
    """A file the user attaches to a chat, as Copilot reads it."""
    shown = workbook_text(path) if path.suffix == ".xlsx" else path.read_text(encoding="utf-8")
    return f"The user attached {path.name}:\n\n<<<\n{shown}>>>\n\n"


def answer(run: Path, number: int, copilot_files: list[str],
           attached: list[Path] | None = None) -> tuple[Path, Path]:
    """Go on with question `number`'s chat: each Copilot file the user loads pasted, in turn,
    as the Steps sheet's step 12 loads several, and what the user attaches, then Copilot asked
    to answer. The message's path, and its reply's."""
    question = read_questions(run)[number - 1]
    names = [Path(each).name for each in copilot_files]
    text = chat_so_far(run, question) + f"You replied: load {in_words(names)}.\n\n"
    for name in names:
        shared = (run / "main" / "copilot" / name).read_text(encoding="utf-8")
        text += f"The user pasted {name}:\n\n<<<\n{shared}\n>>>\n\n"
    for path in attached or []:
        text += attached_text(run / path)
    text += ("Answer the user's question as you would in that chat, with any code in a "
             "```python block and any SQL in a ```sql block.\n")
    return write_copilot_message(run, number, "answer", text)


# --- Scoring a run --------------------------------------------------------------------------


@dataclass
class RunScore:
    """How a run's end compares with its scenario's answer key, and each Workflow notebook it
    added code cells to, which fails it too: on the intended path no step asks for a cell."""

    scenario: str
    missing_tables: list[str] = field(default_factory=list)
    other_columns: list[str] = field(default_factory=list)
    other_rows: list[str] = field(default_factory=list)
    missing_files: list[str] = field(default_factory=list)
    # Each Workflow notebook the run added code cells to, and how many (Toolbox 8.4, ticket
    # 14): on the intended path a user makes no cell of their own.
    added_cells: list[str] = field(default_factory=list)
    # The run's actions (Toolbox 8.5, ticket 12), which fail nothing: each Workflow notebook's
    # code cells edited from as the Toolbox writes them, by the Workflow, and each file the run
    # wrote of its own, outside its Project or a script saved into it.
    edited_cells: dict[str, int] = field(default_factory=dict)
    own_files: list[str] = field(default_factory=list)
    questions: int = 0
    # The Copilot proxy's reply files over the usability reply cap, which fail nothing.
    long_replies: list[str] = field(default_factory=list)
    project: Path | None = None

    @property
    def actions(self) -> int:
        """How many actions the run took that the Toolbox could count: cells edited and files
        of its own."""
        return sum(self.edited_cells.values()) + len(self.own_files)

    @property
    def passed(self) -> bool:
        failures = [self.missing_tables, self.other_columns, self.other_rows,
                    self.missing_files, self.added_cells]
        return not any(failures) and self.questions <= eval_runs.CAPS["usability"].turns


def compared_value(value: object) -> tuple[str, object]:
    """A value as rows are compared, with its kind: a number by value, rounded; a missing
    value, NULL or NaN, as None; True or False; text as itself."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return ("null", None)
    if isinstance(value, bool):
        return ("bool", value)
    if isinstance(value, (int, float)):
        return ("number", round(float(value), 6))
    return ("text", str(value))


def compared_rows(columns: list[str], rows: list[list[object]],
                  wanted: list[str]) -> list[tuple[tuple[str, object], ...]]:
    """A table's rows, each its values for the `wanted` columns in that order, compared, in a
    fixed order."""
    lowered = [column.lower() for column in columns]
    picked = []
    for row in rows:
        values = []
        for column in wanted:
            values.append(compared_value(row[lowered.index(column.lower())]))
        picked.append(tuple(values))
    return sorted(picked, key=repr)


def find_the_project(run: Path) -> Path | None:
    """The Project the agents made in a run's folder: the folder holding admin/registry.csv,
    outside main/ and _loop/."""
    for registry in sorted(run.rglob("admin/registry.csv")):
        if registry.relative_to(run).parts[0] not in ("main", "_loop"):
            return registry.parent.parent
    return None


def check_tables(result: RunScore, key: dict[str, dict], run: Path) -> None:
    """Note on `result` each table the key holds that the run's warehouse hasn't, or holds
    with other columns or other rows."""
    held = json.loads((run / "_loop" / "warehouse.json").read_text(encoding="utf-8"))
    for name, wanted in key.get("tables", {}).items():
        if name not in held:
            result.missing_tables.append(name)
            continue
        columns = list(held[name]["columns"])
        if sorted(column.lower() for column in columns) != sorted(
                column.lower() for column in wanted["columns"]):
            result.other_columns.append(name)
            continue
        found = compared_rows(columns, held[name]["rows"], wanted["columns"])
        if found != compared_rows(wanted["columns"], wanted["rows"], wanted["columns"]):
            result.other_rows.append(name)


def check_files(result: RunScore, key: dict[str, dict]) -> None:
    """Note on `result` each file the key holds that the Project hasn't, or hasn't with the
    text the key says it holds."""
    for wanted in key.get("files", []):
        path = wanted if isinstance(wanted, str) else wanted["path"]
        holds = [] if isinstance(wanted, str) else wanted.get("holds", [])
        if result.project is None or not (result.project / path).is_file():
            result.missing_files.append(path)
            continue
        text = (result.project / path).read_text(encoding="utf-8")
        if not all(each in text for each in holds):
            result.missing_files.append(f"{path} (without {in_words(holds)})")


def score(chosen: Scenario, run: Path) -> RunScore:
    """A run's end against its scenario's answer key: each table the key holds, in the run's
    warehouse with its columns and rows, and each file it holds, in the Project's folder; and
    each Workflow notebook of the Project the run added code cells to."""
    key = read_answer_key(chosen)
    result = RunScore(chosen.id, questions=len(read_questions(run)),
                      project=find_the_project(run))
    check_tables(result, key, run)
    check_files(result, key)
    check_cells(result)
    count_actions(result, run)
    result.long_replies = long_question_replies(run)
    return result


def long_question_replies(run: Path) -> list[str]:
    """The names of a run's Copilot proxy replies longer than the usability reply cap."""
    cap = eval_runs.CAPS["usability"].reply
    return [path.name for path in sorted((run / "_loop").glob("question_*_reply.md"))
            if len(path.read_text(encoding="utf-8").strip()) > cap]


def count_actions(result: RunScore, run: Path) -> None:
    """Note on `result` each Workflow notebook's code cells the run edited from as the Toolbox
    writes them, and each file it wrote of its own: one in its folder outside the Project,
    main/ and _loop/, such as a script of its own, and each .hql in the Project's
    admin/workflows/, a script saved for a Workflow to read."""
    if result.project is None:
        return
    for workflow in workflows.WORKFLOWS:
        path = workflows.notebook_path(result.project, workflow)
        if not path.is_file():
            continue
        shipped = {text for kind, text in workflows.notebook_cells(workflow, ["paths"])
                   if kind == "code"}
        cells = [text for kind, text in notebooks.read_cells(path) if kind == "code"]
        # The first cell finds the Project, written for its folder: never the user's.
        edited = len([text for text in cells[1:] if text not in shipped])
        if edited:
            result.edited_cells[workflow.name] = edited
    project = result.project.relative_to(run)
    for path in sorted(run.rglob("*")):
        relative = path.relative_to(run)
        if not path.is_file() or relative.parts[0] in ("main", "_loop", "__pycache__"):
            continue
        if not relative.is_relative_to(project) or (
                path.suffix == ".hql"
                and path.relative_to(result.project).parts[:2] == ("admin", "workflows")):
            result.own_files.append(relative.as_posix())


def check_cells(result: RunScore) -> None:
    """Note on `result` each Workflow notebook of the run's Project holding more code cells
    than the Toolbox writes in it: cells the run made of its own."""
    if result.project is None:
        return
    for workflow in workflows.WORKFLOWS:
        path = workflows.notebook_path(result.project, workflow)
        if not path.is_file():
            continue
        shipped = workflows.notebook_cells(workflow, ["paths"])
        added = (len([kind for kind, _ in notebooks.read_cells(path) if kind == "code"])
                 - len([kind for kind, _ in shipped if kind == "code"]))
        if added > 0:
            result.added_cells.append(f"{workflow.name} ({added})")


def report_text(result: RunScore, run: Path) -> str:
    """A run's score as a line or two of text."""
    verdict = "pass" if result.passed else "FAIL"
    project = "no Project found"
    if result.project is not None:
        project = f"its Project at {result.project.relative_to(run).as_posix()}"
    lines = [f"{result.scenario}: {verdict}, {counted(result.questions, 'question')}, "
             f"{project}"]
    for label, names in (("missing tables", result.missing_tables),
                         ("other columns in", result.other_columns),
                         ("other rows in", result.other_rows),
                         ("missing files", result.missing_files),
                         ("cells added to", result.added_cells)):
        if names:
            lines.append(f"  {label}: {in_words(names)}")
    if result.long_replies:
        lines.append(f"  replies over the reply cap of {eval_runs.CAPS['usability'].reply} "
                     f"characters: {in_words(result.long_replies)}")
    edited = "none"
    if result.edited_cells:
        edited = in_words([f"{name} {count}" for name, count in result.edited_cells.items()])
    lines.append(f"  actions: {result.actions}, cells edited ({edited}), "
                 f"{counted(len(result.own_files), 'file')} of its own")
    return "\n".join(lines)


def keep_run_sources(result: RunScore, run: Path) -> None:
    """Keep the run's result with the files and sections its agents said they read: each phase's
    final message, kept by `usage --final`, ends with a `Read:` line; none is no source."""
    inputs = run / "_loop" / "inputs.json"
    inputs_hash = "-"
    if inputs.is_file():
        inputs_hash = json.loads(inputs.read_text(encoding="utf-8"))["inputs_hash"]
    said = "\n".join(path.read_text(encoding="utf-8")
                     for path in sorted((run / "_loop").glob("final-*.txt")))
    named = RUN_NAME.fullmatch(run.name)
    round_id = named[1] if named else run.name
    row = eval_sources.read_row(
        eval_sources.RunOf(datetime.date.today().isoformat(), round_id, "usability", run.name,
                           MEMO_ARM, MODEL, inputs_hash[:SHORT_HASH]),
        result.passed, said, inputs_hash)
    eval_sources.keep_sources([row], LOCAL)


def record(result: RunScore, run: Path, chosen: Scenario, note: str = "") -> str:
    """Keep a scored run, all under the local folder: its folder, but for main/ and any copy of
    the Toolbox's folder, in `usability/runs/`, a row in `usability/results.md` naming its
    actions and, from its inputs.json, the start of its inputs hash, and the run in the memo,
    under the key of its slot, which `plan` and `prepare` read. A run whose name ends in no
    slot is refused, before anything is kept."""
    inputs = run / "_loop" / "inputs.json"
    if inputs.is_file():
        require_slot(chosen, run.name)
    left_out = shutil.ignore_patterns("main", "sqlglot_composer", "__pycache__")
    kept = eval_runs.make_local_path("usability", "runs", run.name, local=LOCAL)
    shutil.copytree(run, kept, ignore=left_out, dirs_exist_ok=True)
    actions = f"{result.actions} actions"
    note = f"{note}; {actions}" if note else actions
    if inputs.is_file():
        inputs_hash = json.loads(inputs.read_text(encoding="utf-8"))["inputs_hash"]
        note += f"; inputs {inputs_hash[:SHORT_HASH]}"
        keep_run(chosen, inputs_hash, run.name, result.passed, report_text(result, run))
    row = (f"| {datetime.date.today().isoformat()} | {chosen.id} | {chosen.split} | {run.name} "
           f"| {'pass' if result.passed else 'fail'} | {result.questions} | {note} |")
    keep_run_sources(result, run)
    named = RUN_NAME.fullmatch(run.name)
    eval_runs.record_round(eval_runs.RoundResult(
        date=datetime.date.today().isoformat(), round=named[1] if named else run.name,
        pipeline="usability", part=run.name, arm=MEMO_ARM, model=MODEL,
        passed=str(int(result.passed)), scored="1", from_memo="0"), LOCAL)
    results_path = eval_runs.make_local_path("usability", "results.md", local=LOCAL)
    if not results_path.is_file():
        results_path.write_text(
            "# Usability loop results\n\nOne row per scored run "
            "(`tools/usability_loop.py score <scenario> <run> --record`).\n\n"
            "| date | scenario | split | run | result | questions | note |\n"
            "|---|---|---|---|---|---|---|\n", encoding="utf-8")
    with results_path.open("a", encoding="utf-8") as results:
        results.write(row + "\n")
    return row


def _plan(given: argparse.Namespace) -> int:
    """Print each scenario's line of the plan, then the round's estimate."""
    chosen = [read_scenario(scenario_id) for scenario_id in given.scenarios]
    planned = [plan_scenario(each, CACHE, fresh=given.fresh) for each in chosen]
    for each in planned:
        print(each.text)
    print(estimate_line([each.slots for each in planned], chosen, given.over_budget))
    return 0


def _prepare(given: argparse.Namespace) -> int:
    """Make a run's folder, then print it and the agent of each phase to spawn."""
    chosen = read_scenario(given.scenario)
    run = prepare(chosen, RUNS / given.run, cache=CACHE, fresh=given.fresh)
    print(f"Run folder: {run}")
    print("\n".join(phase_spawn_lines(chosen, run)))
    return 0


def _usage(given: argparse.Namespace) -> int:
    """Add an agent's reported usage to the ledger."""
    commit = given.commit or dev_commit()
    named = RUN_NAME.fullmatch(given.run)
    round_id = given.round or (named[1] if named else given.run)
    path = record_usage(given.run, given.what, tokens=given.tokens, seconds=given.seconds,
                        result=given.result, round_id=round_id, commit=commit,
                        final=given.final)
    print(f"Recorded {given.run}/{given.what} in {path.name}.")
    return 0


def _route(given: argparse.Namespace) -> int:
    """Start a question's chat and print the proxy to spawn."""
    print(proxy_spawn_line(*route(RUNS / given.run, given.question)))
    return 0


def _answer(given: argparse.Namespace) -> int:
    """Go on with a question's chat and print the proxy to spawn."""
    asked = answer(RUNS / given.run, given.number, given.copilot_files, given.attach)
    print(proxy_spawn_line(*asked))
    return 0


def _score(given: argparse.Namespace) -> int:
    """Score a run, and keep it when asked to."""
    run = RUNS / given.run
    chosen = read_scenario(given.scenario)
    result = score(chosen, run)
    print(report_text(result, run))
    if given.record is not None:
        print(record(result, run, chosen, given.record))
    return 0


def _migrate(given: argparse.Namespace) -> int:
    """Keep each run results.md records in the memo."""
    print(f"Kept {counted(migrate_results(), 'run')} from results.md in the memo.")
    return 0


def _round_parsers(commands: argparse._SubParsersAction) -> None:
    """The commands that plan a round and make and spawn a run."""
    planning = commands.add_parser("plan", help="say which scenarios are memoized, and the "
                                   "round's estimated tokens")
    planning.add_argument("scenarios", nargs="+")
    planning.add_argument("--fresh", action="store_true",
                          help="plan every run again, though it passed")
    planning.add_argument("--over-budget", action="store_true",
                          help="plan a round that is over the usability budget")
    preparing = commands.add_parser("prepare", help="make a run's folder; print the agent of "
                                    "each phase to spawn")
    preparing.add_argument("scenario")
    preparing.add_argument("run", help="the run's name, its folder made in " + str(RUNS))
    preparing.add_argument("--fresh", action="store_true",
                           help="prepare it though it is memoized, to run it again")
    routing = commands.add_parser("route", help="start a question's chat; print the proxy to "
                                  "spawn")
    routing.add_argument("run")
    routing.add_argument("question")
    answering = commands.add_parser("answer", help="go on with a question's chat; print the "
                                    "proxy to spawn")
    answering.add_argument("run")
    answering.add_argument("number", type=int)
    answering.add_argument("copilot_files", nargs="+", help="each Copilot file loaded, in turn")
    answering.add_argument("--attach", type=Path, action="append",
                           help="a file the user attaches, by its path from the run's folder")


def _record_parsers(commands: argparse._SubParsersAction) -> None:
    """The commands that score a run, keep what it cost and bring in older results."""
    scoring = commands.add_parser("score", help="score a run against its answer key")
    scoring.add_argument("scenario")
    scoring.add_argument("run")
    scoring.add_argument("--record", metavar="NOTE", nargs="?", const="")
    usage = commands.add_parser("usage", help="add an agent's reported usage to the ledger")
    usage.add_argument("run")
    usage.add_argument("what", help="phase-<n>, or route-<n> or answer-<n> for a question's "
                       "proxy")
    for name in ("tokens", "seconds", "result"):
        usage.add_argument(f"--{name}", required=True)
    usage.add_argument("--round", help="the round's id (default: the run's name without its "
                       "slot, as its results and sources name the round)")
    usage.add_argument("--commit", default="", help="default: dev's last commit")
    usage.add_argument("--final", help="a phase agent's last message, whose `Read:` line "
                       "says what it read")
    commands.add_parser("migrate", help="keep each run results.md records in the memo")


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    _round_parsers(commands)
    _record_parsers(commands)
    given = parser.parse_args(arguments)
    run_command = {"plan": _plan, "prepare": _prepare, "route": _route, "answer": _answer,
                   "score": _score, "usage": _usage, "migrate": _migrate}
    return run_command[given.command](given)


if __name__ == "__main__":
    sys.exit(main())
