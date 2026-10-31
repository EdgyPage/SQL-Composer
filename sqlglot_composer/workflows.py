"""The Workflows: each ordered list of steps that takes a Project to one end goal.

A Workflow starts from its start materials, what the user brings, and ends at its end
artifacts. Each step takes what it needs, which earlier steps or the start materials gave, and
makes what it makes. Each is one of four kinds:

- a **file step**, which touches only files, or only prints, never the Warehouse, and can
  be run for the user: a Project action, or show_hive;
- a **permission**, a call to the Warehouse the user makes on purpose;
- a **decision**, which needs the user's judgement, such as a risk the original Hive took;
- **fiddling**, a step the user does by hand though the code already knows the answer: typing a
  name it knows, uncommenting a call, pasting or splitting a file, filling a placeholder.

Toolbox 8.0 removes the fiddling, Workflow by Workflow. The lists here are what each Workflow
is today; `tools/workflow_graph.py`, on dev, draws them and counts each kind of step.
"""

from __future__ import annotations

from dataclasses import dataclass

FILE_STEP = "file step"
PERMISSION = "permission"
DECISION = "decision"
FIDDLING = "fiddling"
KINDS = (FILE_STEP, PERMISSION, DECISION, FIDDLING)


@dataclass(frozen=True)
class Step:
    """One step of a Workflow: what it is, its kind, what it needs and makes, and the call
    that does it, if one does."""

    name: str
    kind: str
    needs: tuple[str, ...]
    makes: tuple[str, ...]
    call: str = ""


@dataclass(frozen=True)
class Workflow:
    """A Workflow: its name, its start materials, its end artifacts, and its steps in order."""

    name: str
    start_materials: tuple[str, ...]
    end_artifacts: tuple[str, ...]
    steps: tuple[Step, ...]


# Convert someone else's Hive, as 7.2 does it: one query at a time, by hand around each call.
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
        Step("Paste each query into admin/convert.ipynb", FIDDLING,
             ("queries a Conversion takes",), ("the Hive in the notebook",)),
        Step("Set DATABASE, for the tables the Hive names without one", DECISION,
             ("the Hive in the notebook",), ("the Hive with its database",)),
        Step("Type a Conversion's name into the commented-out convert call, and uncomment it",
             FIDDLING, ("the Hive with its database",), ("a convert call to run",)),
        Step("Convert the query, reading the sources' DESCRIBE", PERMISSION,
             ("a convert call to run", "read access to the sources"),
             ("a Conversion folder", "Table references for the sources"),
             "project.convert(name, hive, query=query)"),
        Step("Fill in the new Table references' TODO lines", DECISION,
             ("Table references for the sources",), ("filled-in source references",)),
        Step("Point each query that reads an earlier one's table at your copy: no step of the "
             "Toolbox does it", FIDDLING,
             ("a Conversion folder", "your Dev Database's name"),
             ("Conversions that read your tables",)),
        Step("Decide each # CONVERSION: mark", DECISION,
             ("Conversions that read your tables",), ("each decision made",)),
        Step("Fill in the compare cell's partition, and uncomment it", FIDDLING,
             ("each decision made",), ("a compare call to run",)),
        Step("Compare each query with its original", PERMISSION, ("a compare call to run",),
             ("each compared with its original",), "compare_with_original(...)"),
        Step("Type the Saved table's name into finish_conversion, and uncomment it", FIDDLING,
             ("each compared with its original", "your Dev Database's name"),
             ("a finish call to run",)),
        Step("Finish the Conversion", FILE_STEP, ("a finish call to run",),
             ("a dev Table folder per table the scripts create", "its Table reference",
              "leftover compare cells"),
             "project.finish_conversion(name, table)"),
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
             "run_tables(execute=execute)"),
    ),
)

# Promote dev tables to prod: no Project action does it yet, so it is all by hand.
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
             "run_tables(execute=execute)"),
    ),
)

# Build a new Saved table from scratch, from admin/new_table.ipynb.
NEW_TABLE = Workflow(
    "new_table",
    start_materials=("a table name", "what the table should hold"),
    end_artifacts=("a dev Table folder whose logic loads", "written in dev",
                   "its Table reference"),
    steps=(
        Step("Type the table's name over \"mart.your_table\" in the notebook", FIDDLING,
             ("a table name",), ("a new_table call to run",)),
        Step("Make the Table folder", FILE_STEP, ("a new_table call to run",),
             ("a Table folder", "its Table reference to fill in"),
             'project.new_table(name)'),
        Step("Fill in its Table reference", DECISION, ("its Table reference to fill in",),
             ("its Table reference",)),
        Step("Write its logic", DECISION, ("a Table folder", "what the table should hold"),
             ("a dev Table folder whose logic loads",)),
        Step("Create and write it in dev", PERMISSION,
             ("a dev Table folder whose logic loads", "its Table reference"),
             ("written in dev",), "run_tables(execute=execute)"),
    ),
)

# Add Table references for tables a Project reads, from admin/add_references.ipynb.
REFERENCES = Workflow(
    "references",
    start_materials=("table names your query can DESCRIBE",),
    end_artifacts=("filled-in Table references", "the Reference sheet", "the Database modules"),
    steps=(
        Step("Type the table names over the notebook's \"ops.your_table\" placeholders",
             FIDDLING, ("table names your query can DESCRIBE",),
             ("an add_references call to run",)),
        Step("Write the Table references from DESCRIBE", PERMISSION,
             ("an add_references call to run",), ("Table references with TODO lines",),
             "project.add_references(names, query=query)"),
        Step("Fill in each TODO line and Alias", DECISION,
             ("Table references with TODO lines",), ("filled-in Table references",)),
        Step("Refresh the Reference sheet and the Database modules", FILE_STEP,
             ("filled-in Table references",),
             ("the Reference sheet", "the Database modules"),
             "project.refresh_reference_sheet()"),
    ),
)

# Carry a Project to a new Toolbox version, from admin/upgrade.ipynb.
UPGRADE = Workflow(
    "upgrade",
    start_materials=("a Project at an older version", "the new Toolbox copied in"),
    end_artifacts=("the Project at the new version", "every # UPGRADE box ticked"),
    steps=(
        Step("Upgrade the Project's files", FILE_STEP,
             ("a Project at an older version", "the new Toolbox copied in"),
             ("the Project at the new version", "# UPGRADE marks"), "project.upgrade()"),
        Step("Make each change an # UPGRADE mark asks for, and tick its box", DECISION,
             ("# UPGRADE marks",), ("every # UPGRADE box ticked",)),
    ),
)

# Change a Saved table in the warehouse, from admin/change_a_saved_table.ipynb.
CHANGE_A_SAVED_TABLE = Workflow(
    "change_a_saved_table",
    start_materials=("a Saved table", "the change wanted"),
    end_artifacts=("the change sent", "the change logged", "its check passed"),
    steps=(
        Step("Pick the notebook's example for the change, uncomment it and fill it in",
             FIDDLING, ("a Saved table", "the change wanted"), ("an Admin statement",)),
        Step("Print the Hive it sends, which sends nothing", FILE_STEP,
             ("an Admin statement",), ("its Hive, read",), "show_hive(statement)"),
        Step("Send it", PERMISSION, ("its Hive, read",),
             ("the change sent", "the change logged"), "run_execute(statement, execute)"),
        Step("Run the check its report names", PERMISSION, ("the change sent",),
             ("its check passed",)),
    ),
)

WORKFLOWS = (CONVERT, PROMOTE, NEW_TABLE, REFERENCES, UPGRADE, CHANGE_A_SAVED_TABLE)
