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
project.do_next() runs the file steps up to the first it can't run for the user. A step that
calls the Warehouse can send itself too, through the user's query and execute:
project.run_workflow(...) runs every step left, up to the first that needs the user.
`tools/workflow_graph.py`, on dev, draws the lists and counts each kind of step.
"""

from __future__ import annotations

import ast
import contextlib
import csv
import io
import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from . import decisions
from .project_files import table_stem
from .shared import escaped_literal, in_words, split_table_name
from .unchecked import SENT, hive_settings
from .upgrades import MARK_LINE, marks_in, project_version

if TYPE_CHECKING:  # project.py imports this file, so its name is for the hints alone
    import pandas as pd

    from .clauses import Statement
    from .project import ProjectReport
    from .unchecked import SessionSettings

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
FAILED = "Failed: "
COMPARED_AT = "Compared at "
# Each result compare.md keeps, one for each Partition compared, starts on a line of its own:
# "## dt = '2026-09-24'", or "## Every row" for a table compared whole.
RESULT_HEADING = "## "
# A converted table's own folder, in its Table folder, and its checklist there, a view of its
# open Decisions.
CONVERSION = "conversion"
CHECKLIST = "checklist.md"
# A placeholder a Template leaves to fill in, such as <PARTITION_COLUMN>.
PLACEHOLDER = decisions.PLACEHOLDER_WORD

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
    # A decision step's kinds of Decision, which you answer in the decisions cell.
    decides: tuple[str, ...] = ()
    # A step that only reads, such as a preview: it waits on nothing, and check() names it
    # beside the step after it.
    reads_only: bool = False
    # A step project.run_workflow runs that calls the warehouse, or only prints: what it did,
    # or, in a dry run, the Hive it would send.
    send: Callable[[dict[str, object], Calls], list[str]] | None = None
    # Its cell's text, for the person who runs it: what it is for, what to do, and what says
    # it is done, which step_cell writes as its Goal, Action and Done when.
    goal: str = ""
    action: str = ""
    done_when: str = ""


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
    # What its notebook's last cell gives project.run_workflow, by name.
    run_with: tuple[str, ...] = ("query", "execute")
    # Its notebook's Self-check: what holds once its last step is done, each a line.
    checks: tuple[str, ...] = ()


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


# The decisions cell's name, the code cell beside the names cell of a Workflow whose step
# waits on Decisions.
DECISIONS = "DECISIONS"
# The kinds of Decision each Workflow's decision step waits on.
DEV_DECISIONS = decisions.ANSWERED_KINDS
PROD_DECISIONS = (decisions.LOCATION,)
SOURCE_DECISIONS = (decisions.KEY,)


def open_decisions_of(root: Path, tables: list[str],
                      kinds: tuple[str, ...]) -> list[decisions.Decision]:
    """Each Decision of `kinds` the Table references of `tables` leave open, table by table."""
    found = []
    for table in tables:
        found += decisions.open_decisions(file_text(reference_path(root, table)), table,
                                          kinds)
    return found


def _every_decision_answered(root: Path, tables: list[str], kinds: tuple[str, ...],
                             inputs: dict[str, object]) -> bool:
    """Whether the decisions cell answers each Decision of `kinds` the tables leave open,
    each table's Table reference written: none answers a Decision not yet asked."""
    if not tables or not all(reference_path(root, table).is_file() for table in tables):
        return False
    answers = inputs.get(DECISIONS)
    if not isinstance(answers, dict):
        answers = {}
    for decision in open_decisions_of(root, tables, kinds):
        answer = answers.get(decision.table)
        if not isinstance(answer, dict) or not decisions.is_answered(decision, answer):
            return False
    return True


def _every_decision_made(root: Path, tables: list[str], kinds: tuple[str, ...]) -> bool:
    """Whether the tables' Table references leave no Decision of `kinds` open."""
    if not tables or not all(reference_path(root, table).is_file() for table in tables):
        return False
    return not open_decisions_of(root, tables, kinds)


def every_dev_decision_answered(root: Path, inputs: dict[str, object]) -> bool:
    """Whether the decisions cell answers each Decision the batch's tables leave open."""
    return every_batch_converted(root, inputs) and _every_decision_answered(
        root, names_in(inputs, "TABLES"), DEV_DECISIONS, inputs)


def every_dev_decision_made(root: Path, inputs: dict[str, object]) -> bool:
    """Whether the batch's tables' Table references leave no Decision open."""
    return every_batch_converted(root, inputs) and _every_decision_made(
        root, names_in(inputs, "TABLES"), DEV_DECISIONS)


def every_prod_decision_answered(root: Path, inputs: dict[str, object]) -> bool:
    """Whether the decisions cell answers each Decision the prod copies leave open."""
    return _every_decision_answered(root, names_in(prod_inputs(root, inputs), "TABLES"),
                                    PROD_DECISIONS, inputs)


def every_prod_decision_made(root: Path, inputs: dict[str, object]) -> bool:
    """Whether the prod copies' Table references leave no Decision open."""
    return _every_decision_made(root, names_in(prod_inputs(root, inputs), "TABLES"),
                                PROD_DECISIONS)


def every_source_decision_answered(root: Path, inputs: dict[str, object]) -> bool:
    """Whether the decisions cell answers each Key the tables' Table references leave open."""
    return _every_decision_answered(root, names_in(inputs, "TABLES"), SOURCE_DECISIONS,
                                    inputs)


def every_source_decision_made(root: Path, inputs: dict[str, object]) -> bool:
    """Whether the tables' Table references leave no Key open."""
    return _every_decision_made(root, names_in(inputs, "TABLES"), SOURCE_DECISIONS)


def decisions_waited_on(root: Path, workflow: Workflow, inputs: dict[str, object],
                        step: Step) -> list[decisions.Decision]:
    """Each Decision a decision step waits on, for the tables of its Workflow's instance: the
    prod copies' for promote."""
    if not step.decides:
        return []
    if workflow.name == "promote":
        inputs = prod_inputs(root, inputs)
    return open_decisions_of(root, names_in(inputs, "TABLES"), step.decides)


def write_the_decisions(inputs: dict[str, object]) -> ProjectReport:
    """The step that writes each answer of the decisions cell into its table's Table
    reference."""
    from . import project  # project.py imports this file

    answers = inputs.get(DECISIONS)
    return project.write_decisions(answers if isinstance(answers, dict) else {})


def every_preview_builds(root: Path, inputs: dict[str, object]) -> bool:
    """Whether each table's notebook's logic runs and its preview() builds its Statement."""
    from . import project  # project.py imports this file

    tables = names_in(inputs, "TABLES")
    return bool(tables) and all(project.preview_builds(root, table) for table in tables)


def every_reference_from_logic(root: Path, inputs: dict[str, object]) -> bool:
    """Whether each table's Table reference is written, its columns no longer new_table's
    <COLUMNS>."""
    paths = [reference_path(root, table) for table in names_in(inputs, "TABLES")]
    return bool(paths) and all(path.is_file() and decisions.has_columns_written(file_text(path))
                               for path in paths)


def every_new_table_decision_answered(root: Path, inputs: dict[str, object]) -> bool:
    """Whether the decisions cell answers each Decision the new tables' Table references,
    written from their logic, leave open."""
    return every_reference_from_logic(root, inputs) and _every_decision_answered(
        root, names_in(inputs, "TABLES"), DEV_DECISIONS, inputs)


def every_new_table_decision_made(root: Path, inputs: dict[str, object]) -> bool:
    """Whether the new tables' Table references, written from their logic, leave no Decision
    open."""
    return every_reference_from_logic(root, inputs) and _every_decision_made(
        root, names_in(inputs, "TABLES"), DEV_DECISIONS)


def every_batch_converted(root: Path, inputs: dict[str, object]) -> bool:
    """Whether the batch NAME names has its batch.md, which convert writes last."""
    name = inputs.get("NAME")
    if not isinstance(name, str) or not name:
        return False
    return (root / BATCHES / name / BATCH_LIST).is_file()


def batch_instances(root: Path) -> list[dict[str, object]]:
    """Each batch convert made, as the convert Workflow's inputs: its name, and the tables
    its record lists."""
    found: list[dict[str, object]] = []
    folder = root / BATCHES
    if not folder.is_dir():
        return found
    for record in sorted(folder.glob(f"*/{BATCH_RECORD}")):
        kept = json.loads(record.read_text(encoding="utf-8"))
        # A table new_table made from its query: its own Workflow takes it on.
        if kept.get("made_for"):
            continue
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
    """Whether each result a converted table's conversion/compare.md keeps says it passed,
    and admin/sent.csv records no write of it since."""
    path = root / "tables" / table_stem(table) / CONVERSION / COMPARED
    text = file_text(path)
    said = [line for line in text.split("\n") if line.startswith((PASSED, FAILED))]
    times = compared_times(text)
    if not said or len(said) != len(times) or not all(line.startswith(PASSED) for line in said):
        return False
    return all(written <= min(times) for written in write_times(root, table))


def compared_times(text: str) -> list[str]:
    """When each result of a compare.md's text was compared, as its Compared at line says,
    such as 2026-10-31 09:30:00."""
    return [line.removeprefix(COMPARED_AT).rstrip(".") for line in text.split("\n")
            if line.startswith(COMPARED_AT)]


def write_times(root: Path, table: str) -> list[str]:
    """When admin/sent.csv records each write of `table`, as its time column holds it."""
    return [row["time"] for row in sent_rows(root)
            if row["kind"] in ("write", "unchecked") and table in row["tables"].split(";")]


def compare_results(text: str) -> dict[str, str]:
    """Each result a conversion/compare.md's text keeps, by the Partition it was compared on,
    as its RESULT_HEADING line names it. A compare.md from before 8.2 holds one result and no
    such line: it is kept under ""."""
    _, _, rest = text.partition(f"\n{RESULT_HEADING}")
    if rest:
        results = {}
        for block in rest.split(f"\n{RESULT_HEADING}"):
            compared_on, _, said = block.partition("\n")
            results[compared_on] = said.strip("\n")
        return results
    for status in (PASSED, FAILED):
        _, _, rest = text.partition(f"\n{status}")
        if rest:
            return {"": f"{status}{rest}".rstrip("\n")}
    return {}


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
    """Whether the Reference sheet was written after each of these tables' Table references:
    no when it names none, as promote's before any prod copy is made."""
    sheet = root / "references" / "reference_sheet.csv"
    if not names_in(inputs, "TABLES") or not sheet.is_file():
        return False
    written = sheet.stat().st_mtime
    for table in names_in(inputs, "TABLES"):
        path = reference_path(root, table)
        if not path.is_file() or path.stat().st_mtime > written:
            return False
    return True


def prod_sheet_is_fresh(root: Path, inputs: dict[str, object]) -> bool:
    """Whether the Reference sheet was written after each prod copy's Table reference."""
    return reference_sheet_is_fresh(root, prod_inputs(root, inputs))


def project_is_current(root: Path, inputs: dict[str, object]) -> bool:
    """Whether the Project was last written by the Toolbox copied in."""
    from . import TOOLBOX_VERSION  # the package imports this file

    return project_version(root) == TOOLBOX_VERSION


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


# --- What project.run_workflow sends --------------------------------------------------------

@dataclass(frozen=True)
class Calls:
    """What project.run_workflow gives a step that calls the warehouse: your query and
    execute, whether it is a dry run, which sends nothing through your execute and says the
    Hive each call would send, and, for change_a_saved_table, the change."""

    query: Callable[[str], pd.DataFrame] | None
    execute: Callable[[str], None] | None
    dry_run: bool = False
    # change_a_saved_table's Admin statement, which its notebook's first step writes.
    change: Statement | None = None
    # In a dry run, each line of Hive it said it would send, so far.
    hive_lines_said: list[str] = field(default_factory=list)

    def send(self, statement: Statement | SessionSettings) -> list[str]:
        """Send a Statement through your execute, as run_execute does; in a dry run, the Hive
        it would send, a line each."""
        from .running import run_execute  # running imports what imports this

        if self.dry_run:
            return self.say_would_send(hive_lines(statement, "would send"))
        run_execute(statement, self.execute)
        return []

    def say_would_send(self, lines: list[str]) -> list[str]:
        """Keep a dry run's lines of Hive it would send, and give them back to report."""
        self.hive_lines_said.extend(lines)
        return lines

    @property
    def would_have_sent(self) -> bool:
        """Whether a dry run has said it would send something."""
        return bool(self.hive_lines_said)


def hive_lines(statement: Statement | SessionSettings, said: str) -> list[str]:
    """A Statement's Hive, a line each, each after `said`, such as "would send: ..."."""
    from .running import to_hive  # running imports what imports this

    return [f"{said}: {line}" for line in to_hive(statement).split("\n")]


def batch_tables_of(inputs: dict[str, object], seeded: bool = False) -> list[str]:
    """The dev tables of the batch NAME names, or those that read themselves."""
    from . import project  # project.py imports this file

    return project.batch_tables(str(inputs.get("NAME")), seeded=seeded)


def prod_tables_of(inputs: dict[str, object], seeded: bool = False) -> list[str]:
    """The prod copies of the dev tables TABLES names, or those that read themselves."""
    from . import project  # project.py imports this file

    return project.promoted_tables(names_in(inputs, "TABLES"), seeded=seeded)


def convert_the_batch(inputs: dict[str, object], calls: Calls) -> list[str]:
    """project.convert for the batch NAME names, from FILES or HIVE, each copy RENAME names
    named so. It reads only, DESCRIBE
    through your query, and writes files, so a dry run runs it too."""
    from . import project  # project.py imports this file

    files = inputs.get("FILES") or None
    hive = inputs.get("HIVE")
    # STAGING goes as given, so convert refuses one that isn't a dict, as its cell does.
    report = project.convert(str(inputs.get("NAME")), hive if isinstance(hive, str) else None,
                             files=files, query=calls.query,
                             database=str(inputs.get("DATABASE", "default")),
                             rename=inputs.get("RENAME") or None,
                             staging=inputs.get("STAGING"))
    return report.lines


def add_the_references(inputs: dict[str, object], calls: Calls) -> list[str]:
    """project.add_references for the tables TABLES names: it reads DESCRIBE through your
    query and writes files, so a dry run runs it too."""
    from . import project  # project.py imports this file

    return project.add_references(names_in(inputs, "TABLES"), query=calls.query).lines


def _send_creates(tables: list[str], calls: Calls) -> list[str]:
    """Send each table's create()."""
    from . import project  # project.py imports this file

    lines = []
    for table in tables:
        lines += calls.send(project.load(table).create())
    return lines


def _send_seeds(seeded: list[str], calls: Calls) -> list[str]:
    """Send each seed() of the tables that read themselves, after the Session setting their
    Partitions need; nothing when none does."""
    from . import project  # project.py imports this file

    if not seeded:
        return []
    lines = calls.send(hive_settings("dynamic_partitions"))
    for table in seeded:
        lines += calls.send(project.load(table).seed())
    return lines


def _send_writes(tables: list[str], calls: Calls) -> list[str]:
    """Write each table with project.run_tables; in a dry run, the Hive run_tables' own dry run
    prints, in its order, its SET lines with it, each line it would send marked so."""
    from . import project  # project.py imports this file

    if not calls.dry_run:
        return project.run_tables(tables=tables, execute=calls.execute).lines
    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):
        project.run_tables(tables=tables)
    # Its heading lines start "--", as "-- 1 of 2: mart.daily_job_runs": the rest is Hive.
    return calls.say_would_send([line if line.startswith("--") else f"would send: {line}"
                             for line in printed.getvalue().rstrip("\n").split("\n")])


def create_the_batch(inputs: dict[str, object], calls: Calls) -> list[str]:
    """convert's create step: each table of the batch created in dev."""
    return _send_creates(batch_tables_of(inputs), calls)


def seed_the_batch(inputs: dict[str, object], calls: Calls) -> list[str]:
    """convert's seed step: each table of the batch that reads itself seeded."""
    return _send_seeds(batch_tables_of(inputs, seeded=True), calls)


def write_the_batch(inputs: dict[str, object], calls: Calls) -> list[str]:
    """convert's write step: each table of the batch written in dev."""
    return _send_writes(batch_tables_of(inputs), calls)


def create_the_prod_copies(inputs: dict[str, object], calls: Calls) -> list[str]:
    """promote's create step: each prod copy created."""
    return _send_creates(prod_tables_of(inputs), calls)


def seed_the_prod_copies(inputs: dict[str, object], calls: Calls) -> list[str]:
    """promote's seed step: each prod copy that reads itself seeded."""
    return _send_seeds(prod_tables_of(inputs, seeded=True), calls)


def write_the_prod_copies(inputs: dict[str, object], calls: Calls) -> list[str]:
    """promote's write step: each prod copy written."""
    return _send_writes(prod_tables_of(inputs), calls)


def create_and_write_the_tables(inputs: dict[str, object], calls: Calls) -> list[str]:
    """new_table's last step: each table TABLES names created, then written."""
    tables = names_in(inputs, "TABLES")
    return _send_creates(tables, calls) + _send_writes(tables, calls)


def compare_the_batch(inputs: dict[str, object], calls: Calls) -> list[str]:
    """project.compare_batch for the batch NAME names; a dry run names what it would read."""
    from . import project  # project.py imports this file

    if calls.dry_run:
        return ["would compare each with its original, through your query: "
                f"{in_words(batch_tables_of(inputs))}"]
    return project.compare_batch(str(inputs.get("NAME")), query=calls.query).lines


def preview_each(inputs: dict[str, object], calls: Calls) -> list[str]:
    """Each table's preview(), its rows read through your query; a dry run says its Hive."""
    from . import project  # project.py imports this file
    from .running import run_query  # running imports what imports this

    lines = []
    for table in names_in(inputs, "TABLES"):
        preview = project.load(table).preview()
        if calls.dry_run:
            lines += hive_lines(preview, "would read")
        else:
            lines += [f"{table}:", *str(run_query(preview, calls.query)).split("\n")]
    return lines


def the_change(calls: Calls) -> Statement:
    """The Admin statement change_a_saved_table sends, as project.run_workflow was given it."""
    from .refusals import refuse  # it imports what imports this

    if calls.change is None:
        refuse(what='project.run_workflow("change_a_saved_table", ...) was given no '
               "change=.",
               why="The change is the Admin statement your notebook's step 1 writes, which "
               "only your notebook holds.",
               fix="Run step 1's cell, then the last cell, which passes it: change=change.",
               error=ValueError)
    return calls.change


def show_the_change(inputs: dict[str, object], calls: Calls) -> list[str]:
    """change_a_saved_table's second step: the change's Hive as show_hive prints it, its
    Check first line with it, then what the check that line names reads through your query,
    as the step's cell reads it, to read before you send it; a dry run says the check's
    Hive."""
    from .running import show_hive  # running imports what imports this

    change = the_change(calls)
    printed = io.StringIO()
    with contextlib.redirect_stdout(printed):
        show_hive(change)
    lines = printed.getvalue().rstrip("\n").split("\n")
    check = check_first_hive(change)
    if check is None:
        return lines
    if calls.dry_run:
        return [*lines, f"would read: {check}"]
    return [*lines, f"{check}:", *str(calls.query(check)).split("\n")]


# The check an Admin statement's Check first line names, such as
# "Check first: SHOW PARTITIONS mart.daily_runs lists its Partitions: ...".
CHECK_FIRST = re.compile(
    r"^Check first: (?P<check>(SHOW PARTITIONS|DESCRIBE FORMATTED|DESCRIBE) \S+) ")


def check_first_hive(change: Statement) -> str | None:
    """The Hive of the check an Admin statement's Check first line names, such as
    SHOW PARTITIONS mart.daily_runs; None for one with no such line."""
    for said in change._admin_about:
        found = CHECK_FIRST.match(said)
        if found:
            return found["check"]
    return None


# --- What a file step runs --------------------------------------------------------------------


def make_table_folders(inputs: dict[str, object]) -> ProjectReport:
    """project.new_table for each table TABLES names, from its query where QUERIES gives one."""
    from . import project  # project.py imports this file

    return project.new_table(names_in(inputs, "TABLES"), queries=queries_given(inputs))


def queries_given(inputs: dict[str, object]) -> dict[str, str]:
    """The queries QUERIES gives, by each table's name without its database; none when it
    holds no dict."""
    queries = inputs.get("QUERIES")
    if not isinstance(queries, dict):
        return {}
    return {str(name): str(query) for name, query in queries.items()}


def queries_of(inputs: dict[str, object]) -> list[str]:
    """The names QUERIES gives a query for that TABLES names too, each a batch of one
    new_table made: a name TABLES no longer holds is passed over."""
    named = {split_table_name(table)[1] for table in names_in(inputs, "TABLES")}
    return [name for name in queries_given(inputs) if name in named]


def every_query_table_compared(root: Path, inputs: dict[str, object]) -> bool:
    """Whether each table is written, and each made from a query has passed its compare with
    it, or finished."""
    dev = databases(root).get("DEV", "")
    return every_table_written(root, inputs) and all(
        (root / BATCHES / FINISHED / name).is_dir() or compare_passed(root, f"{dev}.{name}")
        for name in queries_of(inputs))


def compare_the_queries(inputs: dict[str, object], calls: Calls) -> list[str]:
    """project.compare_batch for each table made from a query; a dry run names them."""
    from . import project  # project.py imports this file

    names = queries_of(inputs)
    if calls.dry_run:
        return [f"would compare each with its query, through your query: {in_words(names)}"]
    lines = []
    for name in names:
        lines += project.compare_batch(name, query=calls.query).lines
    return lines


def write_references_from_logic(inputs: dict[str, object]) -> ProjectReport:
    """project.reference_from_logic for each table TABLES names."""
    from . import project  # project.py imports this file

    return project.reference_from_logic(names_in(inputs, "TABLES"))


def refresh_the_sheet(inputs: dict[str, object]) -> ProjectReport:
    """project.refresh_reference_sheet for each table TABLES names."""
    from . import project  # project.py imports this file

    return project.refresh_reference_sheet(names_in(inputs, "TABLES"))


def refresh_the_prod_sheet(inputs: dict[str, object]) -> ProjectReport:
    """project.refresh_reference_sheet for the prod copy of each table TABLES names."""
    from . import project  # project.py imports this file

    return project.refresh_reference_sheet(project.promoted_tables(names_in(inputs, "TABLES")))


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
                   "each compared with its original", "each answer written in"),
    steps=(
        Step("Convert the scripts: each table they write a Saved table in dev", PERMISSION,
             ("Hive scripts", "your Dev Database's name", "read access to the sources"),
             ("a dev Table folder per table the scripts write", "a Table reference per table"),
             "project.convert(NAME, HIVE, files=FILES, query=query, database=DATABASE,\n"
             "                rename=RENAME, staging=STAGING)",
             every_batch_converted, send=convert_the_batch,
             goal="a Table folder and a Table reference for each table the scripts write, each "
             "a Saved table in your Dev Database",
             action="run the cell below. It reads DESCRIBE through your query, and writes only "
             "files.",
             done_when="admin/workflows/convert/ holds the batch's folder, under its name, "
             "with its batch.md, which convert writes last"),
        Step("Answer each table's open Decisions in the decisions cell", DECISION,
             ("a Table reference per table",), ("each answer in the decisions cell",),
             done=every_dev_decision_answered, decides=DEV_DECISIONS,
             goal="an answer to each open Decision of the batch's tables",
             action="write each answer in the decisions cell, `DECISIONS`, by the table's name "
             "as `project.check()` writes it, then save the notebook. Each table's "
             "`conversion/checklist.md`, in its Table folder, lists its open Decisions.",
             done_when="the decisions cell answers each Decision `project.check()` names for "
             "this batch"),
        Step("Write each answer into its table's Table reference", FILE_STEP,
             ("each answer in the decisions cell",), ("each answer written in",),
             "project.write_decisions(DECISIONS)", every_dev_decision_made,
             write_the_decisions,
             goal="each answer written into its table's Table reference",
             action="run the cell below.",
             done_when="each table's `conversion/checklist.md` says None under Open Decisions"),
        Step("Create each table in dev", PERMISSION, ("each answer written in",),
             ("each made in dev",),
             "for table in project.batch_tables(NAME):\n"
             "    run_execute(project.load(table).create(), execute)", every_table_created,
             send=create_the_batch,
             goal="each table of the batch made in your Dev Database",
             action="run the cell below. It sends each table's `create()` through your "
             "execute.",
             done_when="admin/sent.csv records a create of each table"),
        Step("Seed each table that reads itself, once, from its original", PERMISSION,
             ("each made in dev",), ("each seeded",),
             'run_execute(hive_settings("dynamic_partitions"), execute)\n'
             "for table in project.batch_tables(NAME, seeded=True):\n"
             "    run_execute(project.load(table).seed(), execute)", every_table_seeded,
             send=seed_the_batch,
             goal="each table that reads itself holding its original's rows, once",
             action="run the cell below. It sends the Session setting their Partitions need, "
             "then each such table's `seed()`, through your execute. If no table of the batch "
             "reads itself, this step is done once step 4 is.",
             done_when="admin/sent.csv records the seed of each table that reads itself"),
        Step("Write each table in dev", PERMISSION, ("each seeded",), ("each written in dev",),
             "project.run_tables(tables=project.batch_tables(NAME), execute=execute)",
             every_table_written, send=write_the_batch,
             goal="each table's rows written in your Dev Database",
             action="run the cell below. `project.run_tables` sends each table's `write()` "
             "through your execute.",
             done_when="admin/sent.csv records each table written"),
        Step("Compare each table with its original",
             PERMISSION, ("each written in dev",), ("each compared with its original",),
             "project.compare_batch(NAME, query=query)", every_table_compared,
             send=compare_the_batch,
             goal="each table's rows checked against its original's",
             action="run the cell below. `project.compare_batch` reads both through your query "
             "and writes each table's result in its `conversion/compare.md`. A partitioned "
             "table is compared on the latest Partition both tables hold. If you want another "
             "Partition compared too, then run `print(project.compare_batch(NAME, "
             "query=query, partition={\"dt\": \"2026-09-23\"}))` in a new cell, NAME being "
             "the names cell's: its result is kept beside the first.",
             done_when="every result in each table's `conversion/compare.md` says Passed, "
             "and the batch's folder has moved to admin/workflows/convert/finished/; a table "
             "with a result that failed is one promote refuses"),
    ),
    inputs=(Input("NAME", "", "the batch's name, plain lowercase, such as \"weekly\" (or, "
                  "for the last cell alone, a list of batches converted already)", starts=True),
            Input("FILES", [], 'the scripts\' files, from this folder, such as ["daily.hql"], '
                  "or [] to read HIVE"),
            Input("HIVE", None, 'the Hive as text, such as """SELECT ...""", or None '
                  "to read FILES"),
            Input("DATABASE", "default", "the database of a table the Hive names without one"),
            Input("RENAME", {}, "a name of your own for a table's copy in dev, by the table's "
                  'full name, such as {"mart.team_fails": "team_fails"} for '
                  "mart_dev.team_fails: left out, a copy is <table>_<its database>, such as "
                  "mart_dev.team_fails_mart"),
            Input("STAGING", {}, 'each staging table convert names, kept or folded, such as '
                  '{"ops_reports.failed": "keep"}: left out, a temporary or DROPped one is '
                  "folded, any other kept")),
    about="Turns Hive someone else wrote, one query or a batch of scripts, into your own code: "
    "each table the scripts write becomes a Saved table in your Dev Database, with its Table "
    "folder, and what only you can decide of it, a Decision, answered in the decisions cell.",
    databases=("DEV",),
    instances=batch_instances,
    checks=("Each table the scripts write has its Table folder in tables/ and its Table "
            "reference in references/.",
            "Each table's `conversion/checklist.md` says None under Open Decisions.",
            "admin/sent.csv records each table created and written, and each that reads itself "
            "seeded.",
            "Each table's `conversion/compare.md` says it passed, and the batch's folder is in "
            "admin/workflows/convert/finished/.",
            "`project.check()` names no next step of this batch."),
)

# Promote dev tables to prod, project.promote's copies reading each other's.
PROMOTE = Workflow(
    "promote",
    start_materials=("dev Table folders, each Decision made and compared",
                     "your Prod Database's name"),
    end_artifacts=("prod Table folders", "each written in prod",
                   "each in the Reference sheet"),
    steps=(
        Step("Promote each table: a prod copy of its folder and Table reference",
             FILE_STEP,
             ("dev Table folders, each Decision made and compared",
              "your Prod Database's name"),
             ("prod Table folders", "prod Table references"), "project.promote(TABLES)",
             every_table_promoted,
             promote_tables,
             goal="a prod copy of each dev table in `TABLES`, its own Table folder and Table "
             "reference, each reading the prod copies of the others promoted with it",
             action="run the cell below.",
             done_when="each dev table in `TABLES` has its prod copy's Table folder in "
             "tables/"),
        Step("Answer each prod table's open Decisions in the decisions cell", DECISION,
             ("prod Table references",), ("each answer in the decisions cell",),
             done=every_prod_decision_answered, decides=PROD_DECISIONS,
             goal="an answer to each prod copy's open Decision: its location, the folder its "
             "files go in",
             action="read what step 1 printed, or run `project.check()`. If neither names an "
             "open Decision of a prod copy, there is nothing to answer: step 1 filled in each "
             "prod copy's `location=` from its dev one, its folder named for your Prod "
             "Database, or from the one it had when promoted before. Leave the decisions cell "
             "as it is, and go on. Else write each answer in the decisions cell, `DECISIONS`, "
             "by the prod table's name as `project.check()` writes it, then save the notebook.",
             done_when="the decisions cell answers each Decision `project.check()` names for "
             "the prod copies, or it names none"),
        Step("Write each answer into its prod table's Table reference", FILE_STEP,
             ("each answer in the decisions cell",), ("each with its location=",),
             "project.write_decisions(DECISIONS)", every_prod_decision_made,
             write_the_decisions,
             goal="each answer written into its prod copy's Table reference, which then has "
             "its `location=`",
             action="run the cell below.",
             done_when="each prod copy's Table reference leaves no Decision open"),
        Step("Create each table in prod", PERMISSION, ("each with its location=",),
             ("each made in prod",),
             "for table in project.promoted_tables(TABLES):\n"
             "    run_execute(project.load(table).create(), execute)",
             every_prod_table_created, send=create_the_prod_copies,
             goal="each prod copy made in your Prod Database",
             action="run the cell below. It sends each prod copy's `create()` through your "
             "execute.",
             done_when="admin/sent.csv records a create of each prod copy"),
        Step("Seed each prod table that reads itself, once, from its original", PERMISSION,
             ("each made in prod",), ("each seeded in prod",),
             'run_execute(hive_settings("dynamic_partitions"), execute)\n'
             "for table in project.promoted_tables(TABLES, seeded=True):\n"
             "    run_execute(project.load(table).seed(), execute)", every_prod_table_seeded,
             send=seed_the_prod_copies,
             goal="each prod copy that reads itself holding its original's rows, once: a prod "
             "copy's original is its dev copy's original",
             action="run the cell below. It sends the Session setting their Partitions need, "
             "then each such prod copy's `seed()`, through your execute. If no prod copy reads "
             "itself, this step is done once step 4 is.",
             done_when="admin/sent.csv records the seed of each prod copy that reads itself"),
        Step("Write each table in prod", PERMISSION, ("each seeded in prod",),
             ("each written in prod",),
             "project.run_tables(tables=project.promoted_tables(TABLES), execute=execute)",
             every_prod_table_written, send=write_the_prod_copies,
             goal="each prod copy's rows written in your Prod Database",
             action="run the cell below. `project.run_tables` sends each prod copy's `write()` "
             "through your execute.",
             done_when="admin/sent.csv records each prod copy written"),
        Step("Refresh the Reference sheet and the Database modules", FILE_STEP,
             ("each written in prod",), ("each in the Reference sheet",),
             "project.refresh_reference_sheet(project.promoted_tables(TABLES))",
             prod_sheet_is_fresh, refresh_the_prod_sheet,
             goal="each prod copy in the Reference sheet and in its Database module",
             action="run the cell below.",
             done_when="references/reference_sheet.csv is written again after each prod copy's "
             "Table reference last changed"),
    ),
    inputs=(Input("TABLES", [], 'the dev tables, by their names in your Dev Database, such '
                  'as ["mart_dev.daily_job_runs"]', starts=True),),
    databases=("DEV", "PROD"),
    about="Carries Saved tables from your Dev Database to your Prod Database.",
    checks=("Each dev table in `TABLES` has a prod copy: its Table folder in tables/ and its "
            "Table reference in references/.",
            "Each prod copy's Table reference has its `location=` and leaves no Decision open.",
            "admin/sent.csv records each prod copy created and written, and each that reads "
            "itself seeded.",
            "references/reference_sheet.csv lists each prod copy's columns.",
            "`project.check()` names no next step of this Workflow."),
)

# Build new Saved tables from scratch.
NEW_TABLE = Workflow(
    "new_table",
    start_materials=("the tables' names", "what each table should hold"),
    end_artifacts=("a dev Table folder whose logic loads", "written in dev",
                   "its Table reference", "each from a query compared with it"),
    steps=(
        Step("Make each Table folder, converting each table's query QUERIES gives",
             FILE_STEP, ("the tables' names",), ("a Table folder",),
             "project.new_table(TABLES, queries=QUERIES)", every_table_folder_made,
             make_table_folders,
             goal="a Table folder for each table in `TABLES`: from its query, when `QUERIES` "
             "gives one, its logic written for you; else from a Template, its logic for you to "
             "write",
             action="if `QUERIES` gives a query, first give each table it reads a Table "
             "reference, with the references Workflow. Then run the cell below. Each query is "
             "converted as the convert Workflow converts one: in a batch of its own, named for "
             "its table, in `admin/workflows/convert/`; the batch moves to `finished/` once "
             "compared.",
             done_when="each table in `TABLES` has its Table folder in tables/"),
        Step("Write each table's logic in its Table notebook, and save it", DECISION,
             ("a Table folder", "what each table should hold"), ("its logic",),
             "for table in TABLES:\n"
             "    project.load(table).preview()  # says what stops it, if anything does",
             every_preview_builds,
             goal="logic in each Table notebook that loads, so its `preview()` builds",
             action="for each table in `TABLES`, open its Table notebook, in its Table "
             "folder, and do as the rules below say. If `QUERIES` gives the table's query, "
             "its logic is written already, from that query: read its logic cell, the one "
             "whose first line is `# logic`, and each `# CONVERSION:` line in it, which "
             "`project.check()` lists too, and change nothing unless you want to, since step 8 "
             "compares its rows with the query's. If `QUERIES` gives it no query, fill in each "
             "`<...>` in its code cells as its text cell says, and save it. Then run the cell "
             "below: it says what stops each table's logic, if anything does.",
             done_when="the cell below runs with no error"),
        Step("Write each Table reference from its logic", FILE_STEP, ("its logic",),
             ("its Table reference",), "project.reference_from_logic(TABLES)",
             every_reference_from_logic, write_references_from_logic,
             goal="each table's Table reference written from its logic: its columns and types "
             "from `preview()`, its partition columns from `PARTITIONED_BY`, and the Key its "
             "logic makes",
             action="run the cell below. It names each TODO line each Table reference leaves, "
             "such as its docstring's first line, which waits on nothing. If it says it kept a "
             "Table reference, as it does for a table made from its query, that file is yours "
             "already, its columns written. Either way, open each Table reference it names, "
             "fill in each TODO line it names by hand, such as one line saying what one row "
             "is, and save the file, now or when you like: no step waits on them.",
             done_when="each table's Table reference in references/ lists its columns, no "
             "longer the stand-in new_table wrote"),
        Step("Answer each table's open Decisions in the decisions cell", DECISION,
             ("its Table reference",), ("each answer in the decisions cell",),
             done=every_new_table_decision_answered, decides=DEV_DECISIONS,
             goal="an answer to each open Decision of the new tables",
             action="write each answer in the decisions cell, `DECISIONS`, by the table's name "
             "as `project.check()` writes it, then save the notebook.",
             done_when="the decisions cell answers each Decision `project.check()` names for "
             "these tables"),
        Step("Write each answer into its table's Table reference", FILE_STEP,
             ("each answer in the decisions cell",), ("a dev Table folder whose logic loads",),
             "project.write_decisions(DECISIONS)", every_new_table_decision_made,
             write_the_decisions,
             goal="each answer written into its table's Table reference",
             action="run the cell below.",
             done_when="each table's Table reference leaves no Decision open"),
        Step("Check each table's rows with preview(), which writes nothing", PERMISSION,
             ("a dev Table folder whose logic loads",), ("its rows, checked",),
             "for table in TABLES:\n"
             "    print(run_query(project.load(table).preview(), query))", reads_only=True,
             send=preview_each,
             goal="each table's rows read and checked before anything is written",
             action="run the cell below. It prints the rows each table's `preview()` gives, "
             "read through your query. `project.check()` names this step beside step 7.",
             done_when="you have read each table's rows, and they are the rows it should "
             "hold"),
        Step("Create and write each in dev", PERMISSION,
             ("its rows, checked", "its Table reference"),
             ("written in dev",),
             "for table in TABLES:\n"
             "    run_execute(project.load(table).create(), execute)\n"
             "project.run_tables(tables=TABLES, execute=execute)", every_table_written,
             send=create_and_write_the_tables,
             goal="each table made and written in your Dev Database",
             action="run the cell below. It sends each table's `create()`, then "
             "`project.run_tables` sends each table's `write()`, through your execute.",
             done_when="admin/sent.csv records each table written"),
        Step("Compare each table made from a query with its query", PERMISSION,
             ("written in dev",), ("each from a query compared with it",),
             "for name in QUERIES:\n"
             "    print(project.compare_batch(name, query=query))",
             every_query_table_compared, send=compare_the_queries,
             goal="each table made from a query checked against its query",
             action="run the cell below. `project.compare_batch` compares each with its query, "
             "through your query, and writes the result in its `conversion/compare.md`. If "
             "`QUERIES` gives no query, this step is done once step 7 is.",
             done_when="each table made from a query has a `conversion/compare.md` that says "
             "it passed"),
    ),
    inputs=(Input("TABLES", [], 'the new tables, by their names in the warehouse, such as '
                  '["mart_dev.daily_job_runs"]', starts=True),
            Input("QUERIES", {}, "each table's query, by its name without its database, as "
                  "Hive text or a .hql file in admin/workflows/new_table/, such as "
                  '{"daily_job_runs": "daily_job_runs.hql"} for mart_dev.daily_job_runs: it is '
                  "made in your Dev Database, its logic written from its query")),
    about="Makes a Table folder for each new Saved table: from its query, when QUERIES gives "
    "one, its logic written for you; else from a Template, its logic for you to write. A "
    "Building block, a piece several notebooks share, is made with project.new_block(...).",
    checks=("Each table in `TABLES` has its Table folder in tables/, and its step 2 cell runs "
            "with no error.",
            "Each table's Table reference lists its columns and leaves no Decision open.",
            "admin/sent.csv records each table created and written.",
            "Each table made from a query has a `conversion/compare.md` that says it passed.",
            "`project.check()` names no next step of this Workflow."),
)

# Add Table references for tables a Project reads.
REFERENCES = Workflow(
    "references",
    start_materials=("table names your query can DESCRIBE",),
    end_artifacts=("filled-in Table references", "the Reference sheet", "the Database modules"),
    steps=(
        Step("Write the Table references from DESCRIBE", PERMISSION,
             ("table names your query can DESCRIBE",), ("Table references with TODO lines",),
             "project.add_references(TABLES, query=query)", every_reference_written,
             send=add_the_references,
             goal="a Table reference for each table in `TABLES`, its columns and their types "
             "read from its DESCRIBE",
             action="run the cell below. It reads each table's DESCRIBE through your query, "
             "and writes only files.",
             done_when="each table in `TABLES` has its Table reference in references/"),
        Step("Answer each table's open Decisions in the decisions cell", DECISION,
             ("Table references with TODO lines",), ("each answer in the decisions cell",),
             done=every_source_decision_answered, decides=SOURCE_DECISIONS,
             goal="an answer to each table's open Key: the columns whose values name exactly "
             "one row, or None when no columns do",
             action="write each answer in the decisions cell, `DECISIONS`, by the table's name "
             "as `project.check()` writes it, then save the notebook.",
             done_when="the decisions cell answers each Key `project.check()` names for these "
             "tables"),
        Step("Write each answer into its table's Table reference", FILE_STEP,
             ("each answer in the decisions cell",), ("filled-in Table references",),
             "project.write_decisions(DECISIONS)", every_source_decision_made,
             write_the_decisions,
             goal="each answer written into its table's Table reference",
             action="run the cell below.",
             done_when="each table's Table reference leaves no Key open"),
        Step("Refresh the Reference sheet and the Database modules", FILE_STEP,
             ("filled-in Table references",),
             ("the Reference sheet", "the Database modules"),
             "project.refresh_reference_sheet(TABLES)", reference_sheet_is_fresh,
             refresh_the_sheet,
             goal="each table in the Reference sheet and in its Database module",
             action="run the cell below.",
             done_when="references/reference_sheet.csv is written again after each table's "
             "Table reference last changed"),
    ),
    inputs=(TABLES_INPUT,),
    about="Writes a Table reference for each table your Project reads, from its DESCRIBE.",
    checks=("Each table in `TABLES` has its Table reference in references/, and leaves no Key "
            "open.",
            "references/reference_sheet.csv lists each table's columns.",
            "`project.check()` names no next step of this Workflow."),
)

# Carry a Project to a new Toolbox version.
UPGRADE = Workflow(
    "upgrade",
    start_materials=("a Project at an older version", "the new Toolbox copied in"),
    end_artifacts=("the Project at the new version", "every UPGRADE mark dealt with"),
    steps=(
        Step("Upgrade the Project's files", FILE_STEP,
             ("a Project at an older version", "the new Toolbox copied in"),
             ("the Project at the new version", "UPGRADE marks"), "project.upgrade()",
             project_is_current, upgrade_the_project,
             goal="the Project's files carried to the Toolbox version you copied in, each file "
             "it changes archived first",
             action="restart the kernel, then run the cell below.",
             done_when="admin/project_version.txt names the Toolbox version you copied in"),
        Step("Make each change an UPGRADE mark asks for, and delete the mark", DECISION,
             ("UPGRADE marks",), ("every UPGRADE mark dealt with",),
             done=no_upgrade_mark_left,
             goal="each change the Upgrade left for you made",
             action="go to each `# UPGRADE` mark, which the Upgrade's report names, "
             "`admin/upgrade_<version>.md` lists and `project.check()` lists, make the change "
             "it asks for, then delete the mark. If a mark in `admin/databases.py` asks for "
             "your Dev and Prod Databases' names, naming them renames nothing: each Saved "
             "table made before keeps its name and its folder.",
             done_when="no `# UPGRADE` mark is left in the Project's own files"),
    ),
    about="Carries the Project's files to the Toolbox you copied in, once you have restarted "
    "the kernel.",
    run_with=(),
    checks=("admin/project_version.txt names the Toolbox version you copied in.",
            "No `# UPGRADE` mark is left in the Project's own files.",
            "`project.check()` lists no UPGRADE mark and no upgrade to make."),
)

# Change a Saved table in the warehouse.
CHANGE_A_SAVED_TABLE = Workflow(
    "change_a_saved_table",
    start_materials=("a Saved table", "the change wanted"),
    end_artifacts=("the change sent", "the change logged"),
    steps=(
        Step("Write the Admin statement for the change", DECISION,
             ("a Saved table", "the change wanted"), ("an Admin statement",),
             "from sqlglot_composer import between, equals  # where= takes a Condition\n"
             "table = project.table_reference(TABLE)\n"
             '# such as where=equals(table.dt, "2026-09-24"), or a range of days,\n'
             '# where=between(table.dt, "2026-09-01", "2026-09-30"), dt its partition column\n'
             "change = admin.drop_partitions(table, where=...)  # or another: help(admin)",
             change_written,
             goal="`change`, the Admin statement that makes the change you want to `TABLE`",
             action="in the cell below, write the Partitions to change in place of the `...` "
             "in `where=...`, or call another Admin statement in place of "
             "`admin.drop_partitions` (`help(admin)` lists them), then run the cell.",
             done_when="the cell sets `change` with its arguments, no `...` left, and runs "
             "with no error"),
        Step("Print its Hive, and run the check its Check first line names", PERMISSION,
             ("an Admin statement",), ("its Hive, read and checked",),
             "show_hive(change)\n"
             'print(query("SHOW PARTITIONS " + TABLE))',
             send=show_the_change,
             goal="the change's Hive read and checked before you send it",
             action="run the cell below. It prints the change's Hive, with what it changes and "
             "its `Check first` line, then sends the check that line names through your "
             "query, a `SHOW PARTITIONS` for `admin.drop_partitions`, and prints what it "
             "reads. If you wrote another Admin statement in step 1, first write the check its "
             '`Check first` line names in place of `"SHOW PARTITIONS "`, such as '
             '`"DESCRIBE FORMATTED "` for `admin.drop_table` or `"DESCRIBE "` for '
             "`admin.add_columns`. Read the Hive and the rows the check prints.",
             done_when="that check shows the change reaches only what you mean it to"),
        Step("Send it, then any check after it, such as admin.check_the_copy", PERMISSION,
             ("its Hive, read and checked",),
             ("the change sent", "the change logged"), "run_execute(change, execute)",
             every_change_sent,
             goal="the change made in the warehouse, and logged",
             action="run the cell below. It sends `change` through your execute. Then run any "
             "check after it, such as `admin.check_the_copy`.",
             done_when="admin/sent.csv records the Admin statement on `TABLE`, and "
             "admin/admin_log.md logs it"),
    ),
    inputs=(Input("TABLE", "", 'the Saved table to change, such as "mart.daily_job_runs"',
                  starts=True),),
    about="Changes a Saved table in the warehouse with one of the admin module's Admin "
    "statements, each logged in admin/admin_log.md.",
    run_with=("query", "execute", "change"),
    checks=("Step 1's cell sets `change` with its arguments, no `...` left.",
            "admin/sent.csv records the Admin statement on `TABLE`, and admin/admin_log.md "
            "logs it.",
            "You ran the check its `Check first` line names, and any check after it.",
            "`project.check()` names no next step of this Workflow."),
)

WORKFLOWS = (CONVERT, PROMOTE, NEW_TABLE, REFERENCES, UPGRADE, CHANGE_A_SAVED_TABLE)


# --- Each Workflow's notebook -----------------------------------------------------------------


def notebook_path(root: Path, workflow: Workflow) -> Path:
    """A Workflow's notebook in a Project: admin/workflows/<name>/<name>.ipynb."""
    return root / WORKFLOWS_FOLDER / workflow.name / f"{workflow.name}.ipynb"


def inputs_cell(workflow: Workflow) -> str:
    """The first code cell of a Workflow's notebook: each input, empty, with what to write."""
    return "\n".join(input_line(each, each.empty) for each in workflow.inputs)


def input_line(given: Input, value: object) -> str:
    """One input's line of a Workflow notebook's names cell, holding `value`."""
    return f"{given.name} = {value!r}  # {given.about}"


# The decisions cell of a Workflow whose step waits on Decisions.
DECISIONS_CELL = (
    f"{DECISIONS} = {{}}  # your answer to each open Decision, by the table's name as\n"
    "# project.check() writes it, such as\n"
    '# {"mart_dev.weekly_ops": {"location": "/data/team/mart_dev.db/weekly",\n'
    '#                          "key": ["job_id"], "types": {"fails": "bigint"}}}\n'
    '# "key": None says no columns name one row. project.check() names each one open;\n'
    "# a Key marked # proposed is made, but an answer here changes it")

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
    """A step's markdown cell in its Workflow's notebook: its number, name and kind, then its
    Goal, Action and Done when, which names the step after it."""
    then = f"then step {number + 1}"
    if number == len(workflow.steps):
        then = "the Workflow is done: go through the Self-check at the top"
    return (f"## {number}. {step.name}\n\nIt {step_said(workflow, step)}.\n\n"
            f"- **Goal:** {step.goal}.\n- **Action:** {step.action[0].upper()}"
            f"{step.action[1:]}\n- **Done when** {step.done_when}; {then}.")


# The words of this repo a Workflow notebook's text uses, each defined in its Terms the first
# time its text uses it, in the order the text first does.
NOTEBOOK_TERMS = {
    "Hive": "the SQL your warehouse runs.",
    "Saved table": "a table in the warehouse that only your own code writes, its files in a "
                   "folder of its own.",
    "Dev Database": "the database where you create and write tables of your own, each built, "
                    "written and compared there first: `DEV` in admin/databases.py.",
    "Prod Database": "the database others read your finished Saved tables from, which a table "
                     "reaches only once promoted from the Dev Database: `PROD` in "
                     "admin/databases.py.",
    "Table folder": "the folder in tables/ that holds everything about one Saved table: its "
                    "Table notebook, its past lineage, and its Hive.",
    "Table notebook": "the notebook in a Table folder whose cells create, preview and write "
                      "its Saved table; its logic cell is the one whose first line is "
                      "`# logic`.",
    "Table reference": "a script in references/ describing one table: its columns and their "
                       "types, its Partitions and its Key.",
    "Decision": "one thing about one table that only you decide, such as its location or its "
                "Key; the table's files say whether it is answered yet.",
    "Key": "the columns whose values name exactly one row of a table.",
    "Partition": "the rows of a table that share one value of each column it is partitioned "
                 "by.",
    "Session setting": "a `SET` line sent before a Statement, which it needs to run.",
    "original": "the table a converted script writes, in the warehouse already, which its "
                "Saved table copies; for a query alone, such as one Copilot wrote from a "
                "workbook, the rows the query gives.",
    "reads itself": "a table whose own script reads it, such as a running total, seeded once "
                    "from its original before its first write.",
    "staging table": "a table one script makes and a later one reads, folded into the table "
                     "that reads it or kept as a Saved table of its own.",
    "batch": "the scripts converted together, under one name.",
    "Template": "the empty shape of a Table notebook, in admin/templates/, each specific left "
                "as a `<...>` to fill in.",
    "Building block": "a piece of your own code several notebooks share, a file of its own in "
                      "building_blocks/.",
    "Reference sheet": "references/reference_sheet.csv, one table listing every column of "
                       "every table the Project has a Table reference for.",
    "Database module": "a file such as references/ops.py, which gives each table of one "
                       "database by name, such as ops.jobs.",
    "Admin statement": "a Statement from the Toolbox's admin module that changes a Saved "
                       "table's definition or deletes its data, such as dropping some of its "
                       "Partitions; it shows what it will change before its Hive.",
    "Statement": "a query your code builds, which becomes one Hive string.",
    "Project action": "a one-time change to a Project's files, run from the admin folder or a "
                      "Workflow's notebook, and recorded in admin/admin_log.md.",
    "Upgrade": "the Project action that carries a Project's files from the Toolbox version "
               "that last wrote them to the one copied in, one version at a time.",
    "UPGRADE mark": "a `# UPGRADE` comment the Upgrade puts at a line it leaves for you to "
                    "change.",
}


def terms_cell_lines(workflow: Workflow, text: str) -> list[str]:
    """The Terms of a Workflow's notebook: its step, names cell and decisions cell, then each
    word of NOTEBOOK_TERMS its text, or a Term before, uses, in the order the text first
    does."""
    lines = ["- **Step**: each numbered heading below, with the code cell under it. Its first "
             "line says its kind: it changes only files, or only prints; it is a call to the "
             "warehouse, yours to run; or it is a decision, yours to make."]
    if workflow.inputs:
        lines.append("- **Names cell**: the code cell after the one that finds the Project. It "
                     "holds this Workflow's inputs, the start materials you fill in once, each "
                     "with what to write in its comment; each step's call reads them.")
    if any(step.decides for step in workflow.steps):
        lines.append(f"- **Decisions cell**: `{DECISIONS}`, the code cell after the names "
                     "cell, where you answer each open Decision a step waits on, by the "
                     "table's name.")
    used: list[str] = []
    # The cell's text, then each definition added, as each can use a term of its own.
    scanned_text = text
    while True:
        found = []
        for word in NOTEBOOK_TERMS:
            # A whole word, or its plural: batch, not compare_batch.
            first = re.search(rf"\b{re.escape(word)}s?\b", scanned_text)
            if first is not None and word not in used:
                found.append((first.start(), word))
        if not found:
            break
        word = min(found)[1]
        used.append(word)
        scanned_text += NOTEBOOK_TERMS[word]
    for word in used:
        lines.append(f"- **{word[0].upper()}{word[1:]}**: {NOTEBOOK_TERMS[word]}")
    return lines


def about_cell(workflow: Workflow) -> str:
    """A Workflow notebook's first cell: what it is for, its Terms, what to do before step 1,
    which cells to run, and its Self-check."""
    rules = ["- If you run the steps yourself, run each step's cell in turn, in order.",
             "- If you want them run for you, run the last cell, `project.run_workflow(...)`, "
             "in place of their cells. It runs every step left in turn, up to the first only "
             "you can do, and says where it stopped: go on from that step."]
    before: list[str] = []
    if workflow.inputs:
        rules.append("- If you want only the steps that change files run for you, run "
                     "`project.do_next()`, the cell before the last. It runs them up to the "
                     "first it can't.")
        before = ["## Before step 1", "",
                  "Fill in the names cell below and save the notebook: each call reads it, and "
                  "so do `project.check()`, which names the next step, and "
                  "`project.do_next()`, the cell before the last.", ""]
    steps = "\n".join(step_cell(number, workflow, step)
                      for number, step in enumerate(workflow.steps, 1))
    head = [f"# {workflow.name}", "", workflow.about, ""]
    return "\n".join([
        *head, "## Terms", "", *terms_cell_lines(workflow, "\n".join([*head, *rules, steps])),
        "", *before, "## Decision rules", "", *rules, "", "## Self-check", "",
        "Once the last step is done, each of these holds:", "",
        *[f"- {check}" for check in workflow.checks]])


def step_name_of(cell: str) -> str | None:
    """The step's name a step's markdown cell, as step_cell writes it, heads; None for any
    other cell."""
    if not cell.startswith("## "):
        return None
    return cell.split("\n")[0].split(". ", 1)[-1]


def notebook_cells(workflow: Workflow, path_lines: list[str]) -> list[tuple[str, str]]:
    """A Workflow's notebook, as (kind, text) cells: what it is for, the lines that find the
    Project, its inputs, then each step and its call, and the cell that runs what is next."""
    cells = [("markdown", about_cell(workflow)), ("code", "\n".join(path_lines))]
    if workflow.inputs:
        cells.append(("code", inputs_cell(workflow)))
    if any(step.decides for step in workflow.steps):
        cells.append(("code", DECISIONS_CELL))
    for number, step in enumerate(workflow.steps, 1):
        cells.append(("markdown", step_cell(number, workflow, step)))
        if step.call:
            cells.append(("code", step.call))
    if workflow.inputs:
        cells.append(("code", "project.do_next()"))
    cells.append(("code", run_cell_text(workflow)))
    return cells


def run_cell_text(workflow: Workflow) -> str:
    """A Workflow notebook's last cell: project.run_workflow, which runs every step left."""
    given = "".join(f", {name}={name}" for name in workflow.run_with)
    return ("# Every step left, in place of their cells, up to the first only you can do.\n"
            "# Add dry_run=True to see the Hive it would send, sending nothing through your\n"
            "# execute: help(project.run_workflow) says the steps it still runs:\n"
            f'project.run_workflow("{workflow.name}"{given})')


def given_inputs(root: Path, workflow: Workflow) -> dict[str, object]:
    """A Workflow's inputs, as its notebook's names cell holds them: each name given a
    plain value there, and its decisions cell's DECISIONS, when it has one. A value that isn't
    plain Python, or a notebook that isn't there, gives none."""
    text = file_text(notebook_path(root, workflow))
    if not text or not workflow.inputs:
        return {}
    names = {each.name for each in workflow.inputs}
    first_line = f"{workflow.inputs[0].name} ="
    given: dict[str, object] = {}
    for cell in json.loads(text).get("cells", []):
        source = "".join(cell.get("source", []))
        if cell.get("cell_type") != "code":
            continue
        # A names cell may start with an UPGRADE mark an Upgrade put above its first line.
        if any(line.startswith(first_line) for line in source.split("\n")):
            given.update(_plain_assignments(source, names))
        elif source.startswith(f"{DECISIONS} ="):
            given.update(_plain_assignments(source, {DECISIONS}))
    return given


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
    named = {each.get("NAME") for each in found}
    started = started_inputs(root, workflow)
    if started is not None:
        found = [*[each for each in one_per_name(started) if each.get("NAME") not in named],
                 *found]
    # Each instance reads the one decisions cell, which answers by table.
    answers = given_inputs(root, workflow).get(DECISIONS, {})
    return [{**each, DECISIONS: answers} for each in found if not is_finished(root, each)]


def is_finished(root: Path, inputs: dict[str, object]) -> bool:
    """Whether the batch NAME names is finished: each table compared and passed, its folder
    moved to finished/, so no step of it is left."""
    name = inputs.get("NAME")
    return isinstance(name, str) and bool(name) and (root / BATCHES / FINISHED / name).is_dir()


def one_per_name(inputs: dict[str, object]) -> list[dict[str, object]]:
    """A names cell's inputs, one instance per batch when NAME is a list of them. Each is one
    convert made already: FILES and HIVE convert the batch NAME names alone."""
    names = inputs.get("NAME")
    if not isinstance(names, list):
        return [inputs]
    return [{**inputs, "NAME": name, "FILES": [], "HIVE": None} for name in names]


def read_again(root: Path, workflow: Workflow, inputs: dict[str, object]) -> dict[str, object]:
    """An instance's inputs read again once a step has run, which may have made more of them:
    the tables of the batch convert has just recorded, beside the names cell's inputs."""
    if workflow.instances is None:
        return inputs
    for each in workflow.instances(root):
        if each.get("NAME") == inputs.get("NAME"):
            return {**inputs, **each}
    return inputs


def started_inputs(root: Path, workflow: Workflow) -> dict[str, object] | None:
    """A Workflow's inputs, once it is started; None until then."""
    inputs = given_inputs(root, workflow)
    if not is_started(workflow, inputs):
        return None
    return inputs


def next_step(root: Path, workflow: Workflow, inputs: dict[str, object]) -> Step | None:
    """The first step not done after the last one the Project's files say is done: a step
    whose done function says no, or that has none, but one that only reads, which waits on
    nothing. A step whose done function says yes means each one before it is done too,
    though the files can't tell of some, but for a step of Decisions still open, which the
    Table references tell exactly: it is named whatever ran after it."""
    for step in steps_left(root, workflow, inputs):
        if step.reads_only:
            continue
        if step.done is None or not step.done(root, inputs):
            return step
    return None


def steps_left(root: Path, workflow: Workflow, inputs: dict[str, object]) -> tuple[Step, ...]:
    """The steps after the last one the Project's files say is done, or from the first step
    of Decisions still open before it: its Table references say so exactly, whatever ran
    after it."""
    after = 0
    for number, step in enumerate(workflow.steps, 1):
        if step.done is not None and step.done(root, inputs):
            after = number
    for index, step in enumerate(workflow.steps[:after]):
        if step.decides and step.done is not None and not step.done(root, inputs):
            return workflow.steps[index:]
    return workflow.steps[after:]


def read_before(workflow: Workflow, step: Step) -> Step | None:
    """The step just before `step` when it only reads, which check() names beside it."""
    number = workflow.steps.index(step)
    if number and workflow.steps[number - 1].reads_only:
        return workflow.steps[number - 1]
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
