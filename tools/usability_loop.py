"""The usability loop: zero-context agents run a Workflow, or the Excel path, from what main
ships, and each run is scored against its scenario's answer key (Toolbox 8.2, ticket 02; the
map's Notes, "The loop"). `docs/usability-loop.md` says how a round is run.

    python tools/usability_loop.py prepare W1 2026-11-01-W1-1
    python tools/usability_loop.py route 2026-11-01-W1-1 "<the agent's question>"
    python tools/usability_loop.py answer 2026-11-01-W1-1 1 07_convert_hive.txt \
        --attach my_work/book.xlsx
    python tools/usability_loop.py score W1 2026-11-01-W1-1 --record "<a note>"

A scenario is a folder in `tools/usability_scenarios/`: `scenario.json` (its id, split, title,
the Hive its team's warehouse ran already, the files the user is given, any Project they
start from, as `project`, a folder of dev's, or `start_from`, another scenario whose reference
end makes it, and each phase: a role and the job in the user's words) and `key.json`, its
answer key (each table the end goal holds, with its columns and rows, and each file it holds,
from the Project's folder, with any text it must hold), never copied into a run.

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
- `_loop/`, which only the loop reads: the warehouse's file, each phase's message, each
  question, each Copilot message and reply, and each agent's reply.

Scored with `--record`, a run's folder, but for `main/` and any copy of the Toolbox's
folder, is copied into `.scratch/usability-loop/runs/`, and a row added to
`.scratch/usability-loop/results.md`.
"""

from __future__ import annotations

import argparse
import datetime
import json
import math
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
sys.path[:0] = [str(ROOT)]

import export_clean  # noqa: E402
import openpyxl  # noqa: E402
from formula_workbook import row_label  # noqa: E402
from workflow_warehouse import SavedWarehouse  # noqa: E402

from sqlglot_composer import notebooks, workflows  # noqa: E402
from sqlglot_composer.shared import counted, in_words  # noqa: E402

SCENARIOS = TOOLS / "usability_scenarios"
KEPT = ROOT / ".scratch" / "usability-loop"
RESULTS = KEPT / "results.md"
# Where runs are made, and the Python their agents run: outside the repo, so nothing of dev's
# is near them.
OUTSIDE = Path(tempfile.gettempdir()) / "usability-loop"
RUNS = OUTSIDE / "runs"
PYTHON = OUTSIDE / "python" / "Scripts" / "python.exe"
# The questions a run may ask before it counts as stuck.
MOST_QUESTIONS = 5

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


def read_scenario(scenario_id: str, folder: Path = SCENARIOS) -> Scenario:
    """The scenario with this id, read from its folder."""
    held = json.loads((folder / scenario_id / "scenario.json").read_text(encoding="utf-8"))
    phases = tuple(Phase(each["role"], each["job"]) for each in held["phases"])
    for phase in phases:
        if phase.role not in ROLE_TEXT:
            raise ValueError(f"{scenario_id}: a phase's role is {phase.role!r}, not "
                             f"{in_words(list(ROLE_TEXT), last='or')}")
    return Scenario(held["id"], held["split"], held["title"], phases,
                    tuple(held.get("hive_ran", [])), dict(held.get("given", {})), folder,
                    held.get("project", ""), held.get("start_from", ""))


def read_answer_key(chosen: Scenario) -> dict[str, dict]:
    """A scenario's answer key: "tables", by name, each with its "columns" and "rows", and
    "files", each a path from the Project's folder or {"path": ..., "holds": [...]}."""
    return json.loads((chosen.folder / chosen.id / "key.json").read_text(encoding="utf-8"))


# --- Preparing a run ------------------------------------------------------------------------


def build_main(into: Path) -> None:
    """The Clean tree, as main would hold it from dev's last commit, built into `into`."""
    commit = export_clean.git(ROOT, "rev-parse", "HEAD")
    with tempfile.TemporaryDirectory() as temporary:
        committed = export_clean.committed_files(ROOT, commit, Path(temporary) / "dev")
        export_clean.build(committed, into, datetime.datetime.now(), commit)


def prepare(chosen: Scenario, run: Path, *, main: Path | None = None,
            python: Path = PYTHON) -> Path:
    """A run's folder for a scenario, as the user has it before starting: main's tree (built,
    or copied from `main`), the scenario's files, the team's connection to a warehouse that has
    run the scenario's Hive, and the notebook runner; then each phase's message."""
    if run.exists() and any(run.iterdir()):
        raise ValueError(f"{run} isn't empty: prepare each run in a folder of its own")
    if not python.is_file():
        raise FileNotFoundError(f"There is no Python for the agents at {python}: make it as "
                                "docs/usability-loop.md says, then prepare again.")
    (run / "_loop").mkdir(parents=True)
    (run / "my_work").mkdir()
    if main is None:
        build_main(run / "main")
    else:
        shutil.copytree(main, run / "main")
    for given, source in chosen.given.items():
        (run / given).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(chosen.folder / chosen.id / source, run / given)
    set_up_the_warehouse(chosen, run)
    if chosen.project or chosen.start_from:
        bring_in_the_project(chosen, run)
    shutil.copyfile(TOOLS / "notebook_runner.py", run / "run_notebook.py")
    for number, phase in enumerate(chosen.phases, 1):
        (run / "_loop" / f"phase_{number}.md").write_text(
            phase_message(phase, run, python, bool(chosen.given)), encoding="utf-8")
    write_questions(run, [])
    return run


def set_up_the_warehouse(chosen: Scenario, run: Path) -> None:
    """Write the team's connection, and its warehouse, having run the scenario's Hive."""
    loop = run / "_loop"
    shutil.copyfile(TOOLS / "workflow_warehouse.py", loop / "workflow_warehouse.py")
    warehouse = SavedWarehouse(loop / "warehouse.json")
    for hive in chosen.hive_ran:
        warehouse.execute((chosen.folder / chosen.id / hive).read_text(encoding="utf-8"))
    warehouse.save()
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
# The lines the team's connection is given by in each, beside the Project: a connection kept
# in a file outside it, as the notebook's comment says.
TEAMS_CONNECT = ('sys.path.append({run!r})  # the folder team_connection.py is in\n'
                 "from team_connection import conn\nconnect(conn)")


def bring_in_the_project(chosen: Scenario, run: Path) -> None:
    """The Project the scenario's user has already, as my_project/: copied in, or made by the
    reference end of the scenario it starts from, its tables in the run's warehouse; then its
    notebooks reaching the team's connection."""
    root = run / "my_project"
    if chosen.start_from:
        import usability_scenario_files  # it imports this file

        usability_scenario_files.reference_end(chosen.start_from, run)
    else:
        shutil.copytree(ROOT / chosen.project, root)
    if not (root / "sqlglot_composer").is_dir():
        # As a Project the user made holds it: the README has them copy it in. A test's run
        # has no main/, so dev's own copy stands in.
        toolbox = run / "main" / "sqlglot_composer"
        if not toolbox.is_dir():
            toolbox = ROOT / "sqlglot_composer"
        shutil.copytree(toolbox, root / "sqlglot_composer",
                        ignore=shutil.ignore_patterns("__pycache__"))
    connect_the_team(root)


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
    """A cell's or Template's text, each of its lines connect(...) the team's connection."""
    lines = text.split("\n")
    return "\n".join(teams if line in LINES_TO_CONNECT else line for line in lines)


def what_you_have(phase: Phase, run: Path, python: Path, given: bool = True) -> list[str]:
    """The lines of a phase's message saying what the agent has, by its role: `given`, when
    the team gave files, names `from_your_team/`."""
    folders = ["Its `main/` folder is the Toolbox as you downloaded it, with its README "
               "(`main/.github/README.md`) and its guides."]
    if given:
        folders.append("`from_your_team/` holds what your team gave you.")
    if (run / "my_project").is_dir():
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


def phase_message(phase: Phase, run: Path, python: Path, given: bool = True) -> str:
    """What an agent is told for one phase: who it is, its job, and what it has."""
    return "\n".join([
        ROLE_TEXT[phase.role],
        "",
        "Your job, in your own words:",
        "",
        phase.job,
        "",
        "What you have:",
        *what_you_have(phase, run, python, given),
        "",
        "How to work:",
        "1. Find what you need in the files you have, and do what they say, in order.",
        "2. If you are stuck, you may ask Copilot, the help your company gives you: end your "
        "turn with one line `QUESTION: ` and your question, then, for each file you would "
        "attach in the chat, a line `ATTACH: ` and its path. You get Copilot's answer as your "
        f"next message. You may ask at most {counted(MOST_QUESTIONS, 'question')}.",
        "3. Run each command in the foreground and wait for it to finish before you go on.",
        "4. When the job is done, end your turn with one line `DONE: ` and what you did, or, "
        "if you can't finish it, `STUCK: ` and where you stopped.",
    ]) + "\n"


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
    message.write_text(text + f"Write your reply under one heading, `## Q{number}`.\n",
                       encoding="utf-8")
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
        return not any(failures) and self.questions <= MOST_QUESTIONS


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
    return result


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
    edited = "none"
    if result.edited_cells:
        edited = in_words([f"{name} {count}" for name, count in result.edited_cells.items()])
    lines.append(f"  actions: {result.actions}, cells edited ({edited}), "
                 f"{counted(len(result.own_files), 'file')} of its own")
    return "\n".join(lines)


def record(result: RunScore, run: Path, chosen: Scenario, note: str = "") -> str:
    """Keep a scored run: its folder, but for main/ and any copy of the Toolbox's folder,
    copied into `.scratch/usability-loop/runs/`, and a row in
    `.scratch/usability-loop/results.md`."""
    left_out = shutil.ignore_patterns("main", "sqlglot_composer", "__pycache__")
    shutil.copytree(run, KEPT / "runs" / run.name, ignore=left_out)
    actions = f"{result.actions} actions"
    note = f"{note}; {actions}" if note else actions
    row = (f"| {datetime.date.today().isoformat()} | {chosen.id} | {chosen.split} | {run.name} "
           f"| {'pass' if result.passed else 'fail'} | {result.questions} | {note} |")
    if not RESULTS.is_file():
        RESULTS.write_text("# Usability loop results\n\nOne row per scored run "
                           "(`tools/usability_loop.py score <scenario> <run> --record`).\n\n"
                           "| date | scenario | split | run | result | questions | note |\n"
                           "|---|---|---|---|---|---|---|\n", encoding="utf-8")
    with RESULTS.open("a", encoding="utf-8") as results:
        results.write(row + "\n")
    return row


def main(arguments: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    preparing = commands.add_parser("prepare")
    preparing.add_argument("scenario")
    preparing.add_argument("run", help="the run's name, its folder made in " + str(RUNS))
    preparing.add_argument("--main", type=Path, help="a Clean tree built already, to copy")
    routing = commands.add_parser("route")
    routing.add_argument("run")
    routing.add_argument("question")
    answering = commands.add_parser("answer")
    answering.add_argument("run")
    answering.add_argument("number", type=int)
    answering.add_argument("copilot_files", nargs="+", help="each Copilot file loaded, in turn")
    answering.add_argument("--attach", type=Path, action="append",
                           help="a file the user attaches, by its path from the run's folder")
    scoring = commands.add_parser("score")
    scoring.add_argument("scenario")
    scoring.add_argument("run")
    scoring.add_argument("--record", metavar="NOTE", nargs="?", const="")
    given = parser.parse_args(arguments)
    run = RUNS / given.run
    if given.command == "prepare":
        print(prepare(read_scenario(given.scenario), run, main=given.main))
    elif given.command == "route":
        print("\n".join(str(path) for path in route(run, given.question)))
    elif given.command == "answer":
        print("\n".join(str(path) for path in answer(run, given.number, given.copilot_files,
                                                      given.attach)))
    else:
        chosen = read_scenario(given.scenario)
        result = score(chosen, run)
        print(report_text(result, run))
        if given.record is not None:
            print(record(result, run, chosen, given.record))
    return 0


if __name__ == "__main__":
    sys.exit(main())
