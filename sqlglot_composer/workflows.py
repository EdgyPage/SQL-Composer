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

# Each Workflow's folder in a Project, and the file naming the user's two Databases.
WORKFLOWS_FOLDER = Path("admin") / "workflows"
DATABASES = Path("admin") / "databases.py"
# A batch's index, in the convert Workflow's folder: what each statement became, and its
# record, written.json, of the tables it made and each file it wrote, with its hash.
BATCHES = WORKFLOWS_FOLDER / "convert"
BATCH_LIST = "batch.md"
BATCH_RECORD = "written.json"
# A batch's folder once every table it made has passed the compare step, which check no
# longer lists; and each table's result, in its conversion/ folder, its third line saying
# whether it passed.
FINISHED = "finished"
# Each table promote made in prod: its dev table, whether it reads itself, and each file of its
# prod Table folder, with its hash, to tell one edited by hand.
PROMOTED = WORKFLOWS_FOLDER / "promote" / "promoted.json"
COMPARED = "compare.md"
PASSED = "Passed: "
COMPARED_AT = "Compared at "
# A converted table's own folder, in its Table folder, its checklist there, and a box on it
# not yet ticked.
CONVERSION = "conversion"
CHECKLIST = "checklist.md"
OPEN_BOX = "- [ ] "
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
    # The names in admin/databases.py it reads, which check() asks for once it is started.
    databases: tuple[str, ...] = ()
    # Its instances in a Project, each its inputs, when it has more than its notebook's
    # names cell: each batch the convert Workflow made, from its record.
    instances: Callable[[Path], list[dict[str, object]]] | None = None


# --- What the Project's files say -------------------------------------------------------------


def names_in(inputs: dict[str, object], name: str) -> list[str]:
    """An input that names tables, as a list: one name as a list of it."""
    given = inputs.get(name)
    if isinstance(given, str):
        return [given]
    if isinstance(given, (list, tuple)):
        return [str(each) for each in given]
    return []


def databases(root: Path) -> dict[str, str]:
    """The names admin/databases.py gives DEV and PROD, as written: <DEV_DATABASE> until the
    user fills one in. None for a name it doesn't give as text."""
    text = file_text(root / DATABASES)
    found = {}
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return found
    for node in tree.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)):
            found[node.targets[0].id] = node.value.value
    return found


def databases_to_fill(root: Path, names: tuple[str, ...]) -> list[str]:
    """Each of `names`, such as DEV, that admin/databases.py doesn't fill in yet."""
    given = databases(root)
    return [name for name in names if PLACEHOLDER.fullmatch(given.get(name, "<>")) or
            not given.get(name)]


def sent_rows(root: Path) -> list[dict[str, str]]:
    """Each Warehouse send admin/sent.csv records, oldest first; none when there is no file."""
    path = root / SENT
    if not path.is_file():
        return []
    with open(path, encoding="utf-8", newline="") as rows:
        return list(csv.DictReader(rows))


def was_sent(root: Path, kind: str, table: str) -> bool:
    """Whether admin/sent.csv records a send of `kind`, such as "write", for `table`."""
    return times_sent(root, kind, table) > 0


def times_sent(root: Path, kind: str, table: str) -> int:
    """How many sends of `kind`, such as "write", admin/sent.csv records for `table`."""
    return len([row for row in sent_rows(root)
                if row["kind"] == kind and table in row["tables"].split(";")])


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
    """Whether each table's Table reference holds no TODO: line and no placeholder left in its
    code; its docstring may still name the placeholders, as a Template's says what each was."""
    for table in names_in(inputs, "TABLES"):
        text = file_text(reference_path(root, table))
        if not text or "TODO:" in text or PLACEHOLDER.search(code_of(text)):
            return False
    return bool(names_in(inputs, "TABLES"))


def code_of(text: str) -> str:
    """A Python file's text but its module docstring; all of it when it doesn't parse yet, as
    a placeholder left in its code stops Python."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return text
    docstring = ast.get_docstring(tree, clean=False)
    if docstring is None:
        return text
    return "\n".join(text.split("\n")[tree.body[0].end_lineno:])


def every_logic_loads(root: Path, inputs: dict[str, object]) -> bool:
    """Whether each table's notebook's logic runs and its write() builds its Statement, as
    project.load(table).write() does. Its text cells may still name a Template's
    placeholders, as they say what each was."""
    from . import project  # project.py imports this file

    tables = names_in(inputs, "TABLES")
    return bool(tables) and all(project.logic_loads(root, table) for table in tables)


def every_batch_converted(root: Path, inputs: dict[str, object]) -> bool:
    """Whether the batch NAME names has its batch.md, which convert writes last."""
    name = inputs.get("NAME")
    if not isinstance(name, str) or not name:
        return False
    return (root / BATCHES / name / BATCH_LIST).is_file()


def every_box_ticked(root: Path, inputs: dict[str, object]) -> bool:
    """Whether every box is ticked of the checklist of each table TABLES names that has a
    Table folder; a checklist missing from one is not, nor are those of a batch not yet
    converted."""
    if not every_batch_converted(root, inputs):
        return False
    for table in names_in(inputs, "TABLES"):
        folder = root / "tables" / table_stem(table)
        checklist = folder / CONVERSION / CHECKLIST
        if folder.is_dir() and (not checklist.is_file() or OPEN_BOX in file_text(checklist)):
            return False
    return True


def batch_instances(root: Path) -> list[dict[str, object]]:
    """Each batch convert made, as the convert Workflow's inputs: its name, and the tables
    its record lists."""
    found: list[dict[str, object]] = []
    folder = root / BATCHES
    if not folder.is_dir():
        return found
    for record in sorted(folder.glob(f"*/{BATCH_RECORD}")):
        kept = json.loads(record.read_text(encoding="utf-8"))
        found.append({"NAME": record.parent.name, "TABLES": kept.get("tables", []),
                      "SEEDED": kept.get("seeded", []),
                      "MADE": list(kept.get("originals", {}))})
    return found


def every_table_created(root: Path, inputs: dict[str, object]) -> bool:
    """Whether admin/sent.csv records a create of each table TABLES names."""
    tables = names_in(inputs, "TABLES")
    return bool(tables) and all(was_sent(root, "create", table) for table in tables)


def every_table_seeded(root: Path, inputs: dict[str, object]) -> bool:
    """Whether admin/sent.csv records the seed, an Unchecked statement, of each table
    SEEDED names, once each table is created; true then when none reads itself."""
    if not every_table_created(root, inputs):
        return False
    return all(was_sent(root, "unchecked", table) for table in names_in(inputs, "SEEDED"))


def every_table_written(root: Path, inputs: dict[str, object]) -> bool:
    """Whether admin/sent.csv records a write of each table TABLES names: a write, or an
    Unchecked statement, its write kept as Hive, besides the seed of one SEEDED names."""
    tables = names_in(inputs, "TABLES")
    seeded = names_in(inputs, "SEEDED")
    return bool(tables) and all(was_written(root, table, table in seeded) for table in tables)


def was_written(root: Path, table: str, seeded: bool) -> bool:
    """Whether admin/sent.csv records a write of `table`: a write, or an Unchecked statement
    besides its seed when it was `seeded`."""
    if was_sent(root, "write", table):
        return True
    seeds = 0
    if seeded:
        seeds = 1
    return times_sent(root, "unchecked", table) > seeds


def every_table_compared(root: Path, inputs: dict[str, object]) -> bool:
    """Whether each table MADE names, each a batch wrote, passed its compare."""
    made = names_in(inputs, "MADE")
    return bool(made) and all(compare_passed(root, table) for table in made)


def compare_passed(root: Path, table: str) -> bool:
    """Whether a converted table's conversion/compare.md says it passed, and admin/sent.csv
    records no write of it since."""
    path = root / "tables" / table_stem(table) / CONVERSION / COMPARED
    said = [line for line in file_text(path).split("\n")
            if line.startswith((PASSED, COMPARED_AT))]
    if len(said) != 2 or not said[0].startswith(PASSED):
        return False
    compared_at = said[1].removeprefix(COMPARED_AT).rstrip(".")
    return all(row["time"] <= compared_at for row in sent_rows(root)
               if row["kind"] in ("write", "unchecked") and table in row["tables"].split(";"))


def promoted_record(root: Path) -> dict[str, dict[str, object]]:
    """admin/workflows/promote/promoted.json: each prod table promote made, by its name; none
    before the first promote."""
    path = root / PROMOTED
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_promoted_record(root: Path, record: dict[str, dict[str, object]]) -> None:
    """Write admin/workflows/promote/promoted.json, as promoted_record reads it."""
    (root / PROMOTED).parent.mkdir(parents=True, exist_ok=True)
    (root / PROMOTED).write_text(json.dumps(record, indent=1, sort_keys=True), encoding="utf-8")


def prod_inputs(root: Path, inputs: dict[str, object]) -> dict[str, object]:
    """The promote Workflow's inputs as its prod steps read them: TABLES, the prod copy of each
    dev table TABLES names, and SEEDED, those that read themselves; no TABLES when one isn't
    promoted yet."""
    record = promoted_record(root)
    prod_of = {entry["dev"]: prod for prod, entry in record.items()}
    devs = names_in(inputs, "TABLES")
    if not devs or any(dev not in prod_of for dev in devs):
        return {"TABLES": [], "SEEDED": []}
    prods = [prod_of[dev] for dev in devs]
    return {"TABLES": prods, "SEEDED": [prod for prod in prods if record[prod]["seeded"]]}


def every_table_promoted(root: Path, inputs: dict[str, object]) -> bool:
    """Whether each dev table TABLES names has its prod copy's Table folder."""
    prods = names_in(prod_inputs(root, inputs), "TABLES")
    return bool(prods) and all((root / "tables" / table_stem(prod)).is_dir() for prod in prods)


def every_prod_location_filled(root: Path, inputs: dict[str, object]) -> bool:
    """Whether each prod copy's Table reference names its folder, location=."""
    prods = names_in(prod_inputs(root, inputs), "TABLES")
    return bool(prods) and all("location=None" not in file_text(reference_path(root, prod))
                               for prod in prods)


def every_prod_table_created(root: Path, inputs: dict[str, object]) -> bool:
    """Whether admin/sent.csv records a create of each prod copy."""
    return every_table_created(root, prod_inputs(root, inputs))


def every_prod_table_seeded(root: Path, inputs: dict[str, object]) -> bool:
    """Whether admin/sent.csv records the seed of each prod copy that reads itself."""
    return every_table_seeded(root, prod_inputs(root, inputs))


def every_prod_table_written(root: Path, inputs: dict[str, object]) -> bool:
    """Whether admin/sent.csv records a write of each prod copy."""
    return every_table_written(root, prod_inputs(root, inputs))


def promote_tables(inputs: dict[str, object]) -> ProjectReport:
    """project.promote for the tables TABLES names."""
    from . import project  # project.py imports this file

    return project.promote(names_in(inputs, "TABLES"))


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


def change_written(root: Path, inputs: dict[str, object]) -> bool:
    """Whether the change_a_saved_table notebook's code sets change to an Admin statement with
    its arguments, on one line or several, not the (...) it starts with."""
    path = root / WORKFLOWS_FOLDER / "change_a_saved_table" / "change_a_saved_table.ipynb"
    found = re.search(r"^change = admin\.\w+\(\s*(.*?)\s*\)", notebook_code(path),
                      re.MULTILINE | re.DOTALL)
    return (bool(names_in(inputs, "TABLE")) and found is not None
            and found.group(1) != "" and "..." not in found.group(1))


def notebook_code(path: Path) -> str:
    """A notebook's code cells, each as its lines, joined; nothing when there is none."""
    text = file_text(path)
    if not text:
        return ""
    cells = json.loads(text).get("cells", [])
    return "\n".join("".join(cell.get("source", [])) for cell in cells
                     if cell.get("cell_type") == "code")


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

# Convert someone else's Hive: one query or a batch of scripts, each table they write a
# Saved table in dev.
CONVERT = Workflow(
    "convert",
    start_materials=("Hive scripts", "your Dev Database's name", "read access to the sources"),
    end_artifacts=("a dev Table folder per table the scripts write", "each written in dev",
                   "each compared with its original", "each decision made"),
    steps=(
        Step("Convert the scripts: each table they write a Saved table in dev", PERMISSION,
             ("Hive scripts", "your Dev Database's name", "read access to the sources"),
             ("a dev Table folder per table the scripts write", "a checklist per table"),
             "project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE)",
             every_batch_converted),
        Step("Tick each box of each table's checklist", DECISION,
             ("a checklist per table",), ("each decision made",), done=every_box_ticked),
        Step("Create each table in dev", PERMISSION, ("each decision made",),
             ("each made in dev",),
             "for table in project.batch_tables(NAME):\n"
             "    run_execute(project.load(table).create(), execute)", every_table_created),
        Step("Seed each table that reads itself, once, from its original", PERMISSION,
             ("each made in dev",), ("each seeded",),
             'run_execute(hive_settings("dynamic_partitions"), execute)\n'
             "for table in project.batch_tables(NAME, seeded=True):\n"
             "    run_execute(project.load(table).seed(), execute)", every_table_seeded),
        Step("Write each table in dev", PERMISSION, ("each seeded",), ("each written in dev",),
             "project.run_tables(tables=project.batch_tables(NAME), execute=execute)",
             every_table_written),
        Step("Compare each table with its original",
             PERMISSION, ("each written in dev",), ("each compared with its original",),
             "project.compare_batch(NAME, query=query)", every_table_compared),
    ),
    inputs=(Input("NAME", "", "the batch's name, plain lowercase, such as \"weekly\"",
                  starts=True),
            Input("FILES", [], 'the scripts\' files, from this folder, such as ["daily.hql"], '
                  "or [] to read HIVE"),
            Input("HIVE", None, 'the Hive as text, such as """SELECT ...""", or None '
                  "to read FILES"),
            Input("DATABASE", "default", "the database of a table the Hive names without one")),
    about="Turns Hive someone else wrote, one query or a batch of scripts, into your own code: "
    "each table the scripts write becomes a Saved table in your Dev Database, with its Table "
    "folder and a checklist.",
    databases=("DEV",),
    instances=batch_instances,
)

# Promote dev tables to prod, project.promote's copies reading each other's.
PROMOTE = Workflow(
    "promote",
    start_materials=("dev Table folders, each box ticked and compared",
                     "your Prod Database's name"),
    end_artifacts=("prod Table folders", "each written in prod"),
    steps=(
        Step("Promote each table: a prod copy of its Table folder and Table reference",
             FILE_STEP,
             ("dev Table folders, each box ticked and compared",
              "your Prod Database's name"),
             ("prod Table folders", "prod Table references"), "project.promote(TABLES)",
             every_table_promoted,
             promote_tables),
        Step("Fill in each prod Table reference's location=", DECISION,
             ("prod Table references",), ("each with its location=",),
             done=every_prod_location_filled),
        Step("Create each table in prod", PERMISSION, ("each with its location=",),
             ("each made in prod",),
             "for table in project.promoted_tables(TABLES):\n"
             "    run_execute(project.load(table).create(), execute)",
             every_prod_table_created),
        Step("Seed each prod table that reads itself, once, from its original", PERMISSION,
             ("each made in prod",), ("each seeded in prod",),
             'run_execute(hive_settings("dynamic_partitions"), execute)\n'
             "for table in project.promoted_tables(TABLES, seeded=True):\n"
             "    run_execute(project.load(table).seed(), execute)", every_prod_table_seeded),
        Step("Write each table in prod", PERMISSION, ("each seeded in prod",),
             ("each written in prod",),
             "project.run_tables(tables=project.promoted_tables(TABLES), execute=execute)",
             every_prod_table_written),
    ),
    inputs=(Input("TABLES", [], 'the dev tables, by their names in your Dev Database, such '
                  'as ["mart_dev.daily_job_runs"]', starts=True),),
    databases=("DEV", "PROD"),
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
        Step("Fill in each Table reference, in references/, and save it", DECISION,
             ("its Table reference to fill in",), ("its Table reference",),
             done=every_reference_filled_in),
        Step("Write each table's logic in its Table notebook, and save it", DECISION,
             ("a Table folder", "what each table should hold"),
             ("a dev Table folder whose logic loads",),
             "for table in TABLES:\n"
             "    project.load(table).write()  # says what stops it, if anything does",
             every_logic_loads),
        Step("Check each table's rows with preview(), which writes nothing", PERMISSION,
             ("a dev Table folder whose logic loads",), ("its rows, checked",),
             "for table in TABLES:\n"
             "    print(run_query(project.load(table).preview(), query))"),
        Step("Create and write each in dev", PERMISSION,
             ("its rows, checked", "its Table reference"),
             ("written in dev",),
             "for table in TABLES:\n"
             "    run_execute(project.load(table).create(), execute)\n"
             "project.run_tables(tables=TABLES, execute=execute)", every_table_written),
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
    end_artifacts=("the change sent", "the change logged"),
    steps=(
        Step("Write the Admin statement for the change", DECISION,
             ("a Saved table", "the change wanted"), ("an Admin statement",),
             "table = project.table_reference(TABLE)\n"
             "change = admin.drop_partitions(table, where=...)  # or another: help(admin)",
             change_written),
        Step("Print its Hive, and run the check its Check first line names", FILE_STEP,
             ("an Admin statement",), ("its Hive, read and checked",), "show_hive(change)"),
        Step("Send it, then any check after it, such as admin.check_the_copy", PERMISSION,
             ("its Hive, read and checked",),
             ("the change sent", "the change logged"), "run_execute(change, execute)",
             every_change_sent),
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
KIND_SAID = {FILE_STEP: "changes only files, or only prints: run its cell",
             PERMISSION: "is a call to the warehouse, yours to run",
             DECISION: "is a decision, yours to make",
             FIDDLING: "is done by hand, since no call does it yet"}


def step_said(workflow: Workflow, step: Step) -> str:
    """What a step is, as its cell and check() say it: its kind in words, and, for a file step
    project.do_next() runs, that it does."""
    if step.kind == FILE_STEP and step.run is not None and is_startable(workflow):
        return "changes only files, so project.do_next() runs it for you"
    return KIND_SAID[step.kind]


def step_cell(number: int, workflow: Workflow, step: Step) -> str:
    """A step's markdown cell in its Workflow's notebook: its number, name and kind."""
    return f"## {number}. {step.name}\n\nIt {step_said(workflow, step)}."


def notebook_cells(workflow: Workflow, path_lines: list[str]) -> list[tuple[str, str]]:
    """A Workflow's notebook, as (kind, text) cells: what it is for, the lines that find the
    Project, its inputs, then each step and its call, and the cell that runs what is next."""
    about = f"# {workflow.name}\n\n{workflow.about} Run each step's cell in turn."
    if workflow.inputs:
        about += (" First fill in the names cell below and save the notebook: each call reads "
                  "it, and so do project.check(), which names the next step, and the last "
                  "cell, project.do_next(), which runs the steps it can for you, up to the "
                  "first it can't: yours, one done by hand, or one only its cell runs.")
    cells = [("markdown", about), ("code", "\n".join(path_lines))]
    if workflow.inputs:
        cells.append(("code", inputs_cell(workflow)))
    for number, step in enumerate(workflow.steps, 1):
        cells.append(("markdown", step_cell(number, workflow, step)))
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


def is_startable(workflow: Workflow) -> bool:
    """Whether a Workflow has an input that starts it, so check() and do_next() read it."""
    return any(each.starts for each in workflow.inputs)


def instances_of(root: Path, workflow: Workflow) -> list[dict[str, object]]:
    """Each instance of a Workflow in a Project, as its inputs: its notebook's names cell,
    once started, and, for one that keeps instances, each it made, but the one the names cell
    names already."""
    found = []
    if workflow.instances is not None:
        found = workflow.instances(root)
    started = started_inputs(root, workflow)
    named = {each.get("NAME") for each in found}
    if started is not None and started.get("NAME") not in named:
        found.insert(0, started)
    return found


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
    if not inputs:
        return call
    # Split on every name at once, each kept, so a value's text is never read as a pattern,
    # nor a name inside one value, such as TABLE in Hive, taken for another input.
    names = "|".join(re.escape(name) for name in inputs)
    pieces = re.split(rf"\b({names})\b", call)
    return "".join(escaped_literal(inputs[piece]) if piece in inputs else piece
                   for piece in pieces)
