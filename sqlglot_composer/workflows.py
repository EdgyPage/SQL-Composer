"""The Workflows: each ordered list of steps that takes a Project to one end goal.

A Workflow starts from its start materials, what the user brings, and ends at its end
artifacts. Each step takes what it needs, which earlier steps or the start materials gave, and
makes what it makes. Each is one of four kinds:

- a **file step**, which touches only files, or only prints, never the Warehouse, and can
  be run for the user: a Project action, or show_hive;
- a **permission**, a call to the Warehouse the user makes on purpose, which the user reads as
  "a call to the warehouse";
- a **decision**, which needs the user's judgement, such as a risk the original Hive took;
- **fiddling**, a step the user does by hand though the code already knows the answer: typing a
  name it knows, uncommenting a call, pasting or splitting a file, filling a placeholder.

Toolbox 8.0 removes the fiddling, Workflow by Workflow. Each Workflow's notebook,
admin/workflows/<name>/<name>.ipynb, is written from its list here: a names cell holding its
inputs, the start materials the user fills in once, then a cell for each step, whose call reads
them. Each step can say whether it is done, read from the Project's files and the inputs, and a
file step can run itself: project.check() names each started Workflow's next step, and
project.do_next() runs the file steps up to the first it can't run for the user.
`tools/workflow_graph.py`, on dev, draws the lists and counts each kind of step.
"""

from __future__ import annotations

import ast
import csv
import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from .project_files import table_stem
from .shared import escaped_literal
from .unchecked import SENT
from .upgrades import MARK_LINE, marks_in

if TYPE_CHECKING:  # project.py imports this file, so its name is for the hints alone
    from .project import ProjectReport

FILE_STEP = "file step"
PERMISSION = "permission"
DECISION = "decision"
FIDDLING = "fiddling"
KINDS = (FILE_STEP, PERMISSION, DECISION, FIDDLING)

# Each Workflow's folder in a Project.
WORKFLOWS_FOLDER = Path("admin") / "workflows"
# A placeholder a Template leaves to fill in, such as <PARTITION_COLUMN>.
PLACEHOLDER = re.compile(r"<[A-Z][A-Z_]*>")

@dataclass(frozen=True)
class Input:
    """One start material a Workflow's notebook asks for in its names cell: its variable's
    name, its value until the user fills it in, what to write there, and whether filling it in
    starts the Workflow, as naming the tables does."""

    name: str
    empty: object
    about: str
    starts: bool = False


@dataclass(frozen=True)
class Step:
    """One step of a Workflow: what it is, its kind, what it needs and makes, the call that
    does it, if one does, as its notebook writes it, whether it is done (None when the
    Project's files can't tell), and, for a file step, the function that does it. A done or run
    function is given the Project's folder and the Workflow's inputs, by name, as its
    notebook's names cell holds them."""

    name: str
    kind: str
    needs: tuple[str, ...]
    makes: tuple[str, ...]
    call: str = ""
    done: Callable[[Path, dict[str, object]], bool] | None = None
    run: Callable[[dict[str, object]], ProjectReport] | None = None


@dataclass(frozen=True)
class Workflow:
    """A Workflow: its name, its start materials, its end artifacts, its steps in order, and
    the inputs its notebook's names cell asks for."""

    name: str
    start_materials: tuple[str, ...]
    end_artifacts: tuple[str, ...]
    steps: tuple[Step, ...]
    inputs: tuple[Input, ...] = ()
    about: str = ""


# --- What the Project's files say -------------------------------------------------------------


def names_in(inputs: dict[str, object], name: str) -> list[str]:
    """An input that names tables, as a list: one name as a list of it."""
    given = inputs.get(name)
    if isinstance(given, str):
        return [given]
    if isinstance(given, (list, tuple)):
        return [str(each) for each in given]
    return []


def sent_rows(root: Path) -> list[dict[str, str]]:
    """Each Warehouse send admin/sent.csv records, oldest first; none when there is no file."""
    path = root / SENT
    if not path.is_file():
        return []
    with open(path, encoding="utf-8", newline="") as rows:
        return list(csv.DictReader(rows))


def was_sent(root: Path, kind: str, table: str) -> bool:
    """Whether admin/sent.csv records a send of `kind`, such as "write", for `table`."""
    for row in sent_rows(root):
        if row["kind"] == kind and table in row["tables"].split(";"):
            return True
    return False


def file_text(path: Path) -> str:
    """A file's text, or nothing when it isn't there."""
    if not path.is_file():
        return ""
    return path.read_text(encoding="utf-8")


def every_table_folder_made(root: Path, inputs: dict[str, object]) -> bool:
    """Whether each table TABLES names has its Table folder."""
    tables = names_in(inputs, "TABLES")
    return bool(tables) and all((root / "tables" / table_stem(table)).is_dir()
                                for table in tables)


def every_reference_written(root: Path, inputs: dict[str, object]) -> bool:
    """Whether each table TABLES names has its Table reference."""
    tables = names_in(inputs, "TABLES")
    return bool(tables) and all(reference_path(root, table).is_file() for table in tables)


def reference_path(root: Path, table: str) -> Path:
    """A table's Table reference in a Project."""
    return root / "references" / f"{table_stem(table)}.py"


def every_reference_filled_in(root: Path, inputs: dict[str, object]) -> bool:
    """Whether each table's Table reference holds no TODO line and no placeholder left."""
    for table in names_in(inputs, "TABLES"):
        text = file_text(reference_path(root, table))
        if not text or "TODO" in text or PLACEHOLDER.search(text):
            return False
    return bool(names_in(inputs, "TABLES"))


def every_logic_written(root: Path, inputs: dict[str, object]) -> bool:
    """Whether each table's notebook holds no placeholder left from its Template."""
    for table in names_in(inputs, "TABLES"):
        stem = table_stem(table)
        text = file_text(root / "tables" / stem / f"{stem}.ipynb")
        if not text or PLACEHOLDER.search(text):
            return False
    return bool(names_in(inputs, "TABLES"))


def every_table_written(root: Path, inputs: dict[str, object]) -> bool:
    """Whether admin/sent.csv records a write of each table TABLES names."""
    tables = names_in(inputs, "TABLES")
    return bool(tables) and all(was_sent(root, "write", table) for table in tables)


def reference_sheet_is_fresh(root: Path, inputs: dict[str, object]) -> bool:
    """Whether the Reference sheet was written after each of these tables' Table references."""
    sheet = root / "references" / "reference_sheet.csv"
    if not sheet.is_file():
        return False
    written = sheet.stat().st_mtime
    for table in names_in(inputs, "TABLES"):
        path = reference_path(root, table)
        if not path.is_file() or path.stat().st_mtime > written:
            return False
    return True


def project_is_current(root: Path, inputs: dict[str, object]) -> bool:
    """Whether the Project was last written by the Toolbox copied in."""
    from . import TOOLBOX_VERSION  # the package imports this file

    recorded = file_text(root / "admin" / "project_version.txt").strip()
    return recorded == TOOLBOX_VERSION


def no_upgrade_mark_left(root: Path, inputs: dict[str, object]) -> bool:
    """Whether no # UPGRADE mark is left in the Project's own files."""
    return not marks_in(root, MARK_LINE)


def every_change_sent(root: Path, inputs: dict[str, object]) -> bool:
    """Whether admin/sent.csv records an Admin statement on the Saved table TABLE names."""
    tables = names_in(inputs, "TABLE")
    return bool(tables) and all(was_sent(root, "admin", table) for table in tables)


# --- What a file step runs --------------------------------------------------------------------


def make_table_folders(inputs: dict[str, object]) -> ProjectReport:
    """project.new_table for each table TABLES names."""
    from . import project  # project.py imports this file

    return project.new_table(names_in(inputs, "TABLES"))


def refresh_the_sheet(inputs: dict[str, object]) -> ProjectReport:
    """project.refresh_reference_sheet for each table TABLES names."""
    from . import project  # project.py imports this file

    return project.refresh_reference_sheet(names_in(inputs, "TABLES"))


def upgrade_the_project(inputs: dict[str, object]) -> ProjectReport:
    """project.upgrade()."""
    from . import project  # project.py imports this file

    return project.upgrade()


# --- The Workflows ---------------------------------------------------------------------------

TABLES_INPUT = Input("TABLES", [], 'the tables, by their names in the warehouse, such as '
                     '["mart.daily_job_runs"]', starts=True)

# Convert someone else's Hive, as 7.2 does it: one query at a time, by hand around each call.
# Tickets 13 to 16 rebuild it.
CONVERT = Workflow(
    "convert",
    start_materials=("Hive scripts", "your Dev Database's name", "read access to the sources"),
    end_artifacts=("a dev Table folder per table the scripts create", "each written in dev",
                   "each compared with its original", "each decision made"),
    steps=(
        Step("Split each script into files of one query each", FIDDLING,
             ("Hive scripts",), ("a file per query",)),
        Step("Rewrite each CREATE: a CREATE TABLE ... AS as an INSERT, and drop a CREATE an "
             "INSERT fills, since a CREATE is refused", FIDDLING,
             ("a file per query",), ("queries a Conversion takes",)),
        Step("Paste each query into the notebook's HIVE, or name its file in FILE", FIDDLING,
             ("queries a Conversion takes",), ("the Hive in the notebook",)),
        Step("Set DATABASE, for the tables the Hive names without one", DECISION,
             ("the Hive in the notebook",), ("the Hive with its database",)),
        Step("Convert the query, reading the sources' DESCRIBE", PERMISSION,
             ("the Hive with its database", "read access to the sources"),
             ("a Conversion folder", "Table references for the sources"),
             "project.convert(NAME, HIVE, file=FILE, query=query, database=DATABASE)"),
        Step("Fill in the new Table references' TODO lines", DECISION,
             ("Table references for the sources",), ("filled-in source references",)),
        Step("Point each query that reads an earlier one's table at your copy: no step of the "
             "Toolbox does it", FIDDLING,
             ("a Conversion folder", "your Dev Database's name"),
             ("Conversions that read your tables",)),
        Step("Decide each CONVERSION mark project.convert left", DECISION,
             ("Conversions that read your tables",), ("each decision made",)),
        Step("Fill in the compare cell's partition, and uncomment it", FIDDLING,
             ("each decision made",), ("a compare call to run",)),
        Step("Compare each query with its original, in the Conversion's notebook",
             PERMISSION, ("a compare call to run",), ("each compared with its original",)),
        Step("Finish the Conversion as the Saved table TABLE names", FILE_STEP,
             ("each compared with its original", "your Dev Database's name"),
             ("a dev Table folder per table the scripts create", "its Table reference",
              "leftover compare cells"),
             "project.finish_conversion(NAME, table=TABLE)"),
        Step("Delete the compare cells the Table notebook keeps", FIDDLING,
             ("leftover compare cells",), ("a Table notebook of its own",)),
        Step("Fill in each <COLUMN_TYPE> and the partitions, which the original's DESCRIBE "
             "gives", FIDDLING, ("its Table reference",), ("its columns filled in",)),
        Step("Fill in its <LOCATION>", FIDDLING, ("its columns filled in",),
             ("its place filled in",)),
        Step("Choose its Key, if it has one", DECISION, ("its place filled in",),
             ("a filled-in Table reference",)),
        Step("Send the original's SET lines with session_settings() by hand", FIDDLING,
             ("a Table notebook of its own",), ("the settings sent",)),
        Step("Create and write each table in dev", PERMISSION,
             ("a filled-in Table reference", "filled-in source references",
              "the settings sent"), ("each written in dev",),
             "project.run_tables(tables=[TABLE], execute=execute)"),
    ),
    inputs=(Input("NAME", "", "the Conversion's name, plain lowercase, such as \"weekly\"",
                  starts=True),
            Input("HIVE", None, 'the Hive as text, such as """SELECT ...""", or None '
                  "to read FILE"),
            Input("FILE", None, 'the file of Hive, from this folder, such as "report.hql", '
                  "or None"),
            Input("DATABASE", "default", "the database of a table the Hive names without one"),
            Input("TABLE", "", "the Saved table it becomes, such as \"mart.weekly_report\"")),
    about="Turns one query of Hive someone else wrote into your own code: a Conversion, then "
    "a Saved table of yours.",
)

# Promote dev tables to prod: no Project action does it yet, so it is all by hand. Ticket 17
# builds it.
PROMOTE = Workflow(
    "promote",
    start_materials=("dev Table folders, decided and compared", "your Prod Database's name"),
    end_artifacts=("prod Table folders", "each written in prod"),
    steps=(
        Step("Copy each dev Table folder to a prod one", FIDDLING,
             ("dev Table folders, decided and compared",), ("copied Table folders",)),
        Step("Change each copy's database to prod, and its Table reference's", FIDDLING,
             ("copied Table folders", "your Prod Database's name"), ("prod Table folders",)),
        Step("Change each prod notebook that reads another promoted table", FIDDLING,
             ("prod Table folders",), ("prod notebooks that read prod",)),
        Step("Create and write each table in prod", PERMISSION,
             ("prod notebooks that read prod",), ("each written in prod",),
             "project.run_tables(execute=execute)  # or tables=[...], the promoted ones"),
    ),
    inputs=(TABLES_INPUT,),
    about="Carries Saved tables from your Dev Database to your Prod Database.",
)

# Build new Saved tables from scratch.
NEW_TABLE = Workflow(
    "new_table",
    start_materials=("the tables' names", "what each table should hold"),
    end_artifacts=("a dev Table folder whose logic loads", "written in dev",
                   "its Table reference"),
    steps=(
        Step("Make each Table folder", FILE_STEP, ("the tables' names",),
             ("a Table folder", "its Table reference to fill in"),
             "project.new_table(TABLES)", every_table_folder_made, make_table_folders),
        Step("Fill in each Table reference", DECISION, ("its Table reference to fill in",),
             ("its Table reference",), done=every_reference_filled_in),
        Step("Write each table's logic in its notebook", DECISION,
             ("a Table folder", "what each table should hold"),
             ("a dev Table folder whose logic loads",), done=every_logic_written),
        Step("Create and write each in dev", PERMISSION,
             ("a dev Table folder whose logic loads", "its Table reference"),
             ("written in dev",), "project.run_tables(tables=TABLES, execute=execute)",
             every_table_written),
    ),
    inputs=(TABLES_INPUT,),
    about="Makes a Table folder for each new Saved table, for you to fill in and write. A "
    "Building block, a piece several notebooks share, is made with project.new_block(...).",
)

# Add Table references for tables a Project reads.
REFERENCES = Workflow(
    "references",
    start_materials=("table names your query can DESCRIBE",),
    end_artifacts=("filled-in Table references", "the Reference sheet", "the Database modules"),
    steps=(
        Step("Write the Table references from DESCRIBE", PERMISSION,
             ("table names your query can DESCRIBE",), ("Table references with TODO lines",),
             "project.add_references(TABLES, query=query)", every_reference_written),
        Step("Fill in each TODO line and Alias", DECISION,
             ("Table references with TODO lines",), ("filled-in Table references",),
             done=every_reference_filled_in),
        Step("Refresh the Reference sheet and the Database modules", FILE_STEP,
             ("filled-in Table references",),
             ("the Reference sheet", "the Database modules"),
             "project.refresh_reference_sheet(TABLES)", reference_sheet_is_fresh,
             refresh_the_sheet),
    ),
    inputs=(TABLES_INPUT,),
    about="Writes a Table reference for each table your Project reads, from its DESCRIBE.",
)

# Carry a Project to a new Toolbox version.
UPGRADE = Workflow(
    "upgrade",
    start_materials=("a Project at an older version", "the new Toolbox copied in"),
    end_artifacts=("the Project at the new version", "every # UPGRADE box ticked"),
    steps=(
        Step("Upgrade the Project's files", FILE_STEP,
             ("a Project at an older version", "the new Toolbox copied in"),
             ("the Project at the new version", "# UPGRADE marks"), "project.upgrade()",
             project_is_current, upgrade_the_project),
        Step("Make each change an # UPGRADE mark asks for, and tick its box", DECISION,
             ("# UPGRADE marks",), ("every # UPGRADE box ticked",),
             done=no_upgrade_mark_left),
    ),
    about="Carries the Project's files to the Toolbox you copied in, once you have restarted "
    "the kernel.",
)

# Change a Saved table in the warehouse.
CHANGE_A_SAVED_TABLE = Workflow(
    "change_a_saved_table",
    start_materials=("a Saved table", "the change wanted"),
    end_artifacts=("the change sent", "the change logged", "its check passed"),
    steps=(
        Step("Write the Admin statement for the change", DECISION,
             ("a Saved table", "the change wanted"), ("an Admin statement",),
             "change = admin.drop_partitions(...)  # or another of the admin module's"),
        Step("Print the Hive it sends, which sends nothing", FILE_STEP,
             ("an Admin statement",), ("its Hive, read",), "show_hive(change)"),
        Step("Send it", PERMISSION, ("its Hive, read",),
             ("the change sent", "the change logged"), "run_execute(change, execute)",
             every_change_sent),
        Step("Run the check its report names", PERMISSION, ("the change sent",),
             ("its check passed",)),
    ),
    inputs=(Input("TABLE", "", 'the Saved table to change, such as "mart.daily_job_runs"',
                  starts=True),),
    about="Changes a Saved table in the warehouse with one of the admin module's Admin "
    "statements, each logged in admin/admin_log.md.",
)

WORKFLOWS = (CONVERT, PROMOTE, NEW_TABLE, REFERENCES, UPGRADE, CHANGE_A_SAVED_TABLE)


# --- Each Workflow's notebook -----------------------------------------------------------------


def notebook_path(root: Path, workflow: Workflow) -> Path:
    """A Workflow's notebook in a Project: admin/workflows/<name>/<name>.ipynb."""
    return root / WORKFLOWS_FOLDER / workflow.name / f"{workflow.name}.ipynb"


def inputs_cell(workflow: Workflow) -> str:
    """The first code cell of a Workflow's notebook: each input, empty, with what to write."""
    lines = []
    for each in workflow.inputs:
        lines.append(f"{each.name} = {each.empty!r}  # {each.about}")
    return "\n".join(lines)


# Each kind of step as the user reads it, in a step's cell and in check()'s next step.
KIND_SAID = {FILE_STEP: "changes only files, so project.do_next() runs it for you",
             PERMISSION: "is a call to the warehouse, yours to run",
             DECISION: "is a decision, yours to make",
             FIDDLING: "is done by hand, since no call does it yet"}


def step_cell(number: int, step: Step) -> str:
    """A step's markdown cell in its Workflow's notebook: its number, name and kind."""
    said = KIND_SAID[step.kind]
    return f"## {number}. {step.name}\n\nIt {said}."


def notebook_cells(workflow: Workflow, path_lines: list[str]) -> list[tuple[str, str]]:
    """A Workflow's notebook, as (kind, text) cells: what it is for, the lines that find the
    Project, its inputs, then each step and its call, and the cell that runs what is next."""
    about = f"# {workflow.name}\n\n{workflow.about} Run each step's cell in turn."
    if workflow.inputs:
        about += (" First fill in the names cell below and save the notebook: each call reads "
                  "it, and so do project.check(), which names the next step, and the last "
                  "cell, project.do_next(), which runs each step that changes only files for "
                  "you, up to the first it can't: yours, or one done by hand.")
    cells = [("markdown", about), ("code", "\n".join(path_lines))]
    if workflow.inputs:
        cells.append(("code", inputs_cell(workflow)))
    for number, step in enumerate(workflow.steps, 1):
        cells.append(("markdown", step_cell(number, step)))
        if step.call:
            cells.append(("code", step.call))
    if workflow.inputs:
        cells.append(("code", "project.do_next()"))
    return cells


def given_inputs(root: Path, workflow: Workflow) -> dict[str, object]:
    """A Workflow's inputs, as its notebook's names cell holds them: each name given a
    plain value there. A value that isn't plain Python, or a notebook that isn't there, gives
    none."""
    text = file_text(notebook_path(root, workflow))
    if not text or not workflow.inputs:
        return {}
    names = {each.name for each in workflow.inputs}
    first_line = f"{workflow.inputs[0].name} ="
    for cell in json.loads(text).get("cells", []):
        source = "".join(cell.get("source", []))
        if cell.get("cell_type") == "code" and source.startswith(first_line):
            return _plain_assignments(source, names)
    return {}


def _plain_assignments(source: str, names: set[str]) -> dict[str, object]:
    """Each name in `names` a source assigns a plain value: text, a number, a list of them."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return {}
    found: dict[str, object] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and target.id in names:
            try:
                found[target.id] = ast.literal_eval(node.value)
            except ValueError:
                continue
    return found


def is_started(workflow: Workflow, inputs: dict[str, object]) -> bool:
    """Whether a Workflow is started: an input that starts it, such as TABLES, holds
    something other than its empty value. A Workflow with no such input, such as upgrade, is
    never started: check() and do_next() pass it over."""
    for each in workflow.inputs:
        if each.starts and inputs.get(each.name, each.empty) != each.empty:
            return True
    return False


def started_inputs(root: Path, workflow: Workflow) -> dict[str, object] | None:
    """A Workflow's inputs, once it is started; None until then."""
    inputs = given_inputs(root, workflow)
    if not is_started(workflow, inputs):
        return None
    return inputs


def next_step(root: Path, workflow: Workflow, inputs: dict[str, object]) -> Step | None:
    """The first step not done after the last one the Project's files say is done: a step
    whose done function says no, or that has none. A step whose done function says yes means
    each one before it is done too, though the files can't tell of some."""
    after = 0
    for number, step in enumerate(workflow.steps, 1):
        if step.done is not None and step.done(root, inputs):
            after = number
    for step in workflow.steps[after:]:
        if step.done is None or not step.done(root, inputs):
            return step
    return None


def ready_call(call: str, inputs: dict[str, object]) -> str:
    """A step's call with each input it reads written out as its value, such as
    project.new_table(["mart.daily_job_runs"]), ready to run from any notebook."""
    for name, value in inputs.items():
        # Split on the whole name, kept, so a value's text is never read as a pattern.
        pieces = re.split(rf"\b({name})\b", call)
        call = "".join(escaped_literal(value) if piece == name else piece for piece in pieces)
    return call
