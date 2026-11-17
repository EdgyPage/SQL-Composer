"""Effective logic: what each column of a Project really holds, traced through every Saved
table it reads, down to the tables the Project doesn't write (Toolbox 8.8, ticket 01).

project_logic(root) works out every column the Lineage state records: each Saved table's
write() columns, each Scheduled run's SELECTs and each Table reference's columns for a table
the Project doesn't write. Each column's own logic is the Hive the Toolbox writes for it, with
each Derived table's column it reads written out in its place and each table's column by the
table's name, never its alias; a Run value as its function and what it was given, never the
value it gives; and a Hivevar as its name, so a build on a new day is no change (ADR 0015). The
rows that count for it, each condition that decides its rows, are read as Lineage's report
reads them. Nothing here reaches the warehouse: each Run value is given a stand-in, never
called.
"""

from __future__ import annotations

import ast
import contextlib
import hashlib
import inspect
import re
from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from pathlib import Path

from . import kinds
from .clauses import Statement
from .lineage import (ConditionLogic, build_graph, deciding_boxes, tables_read,
                      tables_written)
from .notebooks import LOGIC, first_line, read_cells
from .project import one_line_message, reference_columns
from .project_files import SCHEDULED_RUN as RUN_FOLDER
from .project_files import (TABLE_FOLDER, Registry, table_notebook, table_references,
                            table_stem)
from .project_lineage import built_run_of, project_tables
from .python_steps import PythonStep, step_columns_read, step_place
from .run_values import stand_ins
from .scheduled_runs import BuiltRun
from .script_tags import SCRIPT_TAG
from .tables import Table, is_unchecked
from .trees import Node
from .unchecked import UncheckedStatement
from .writing import hive_text

# What a recorded column is a column of: a Saved table's write(), a Scheduled run's Statement,
# or a Table reference's table the Project doesn't write, where every chain ends.
SAVED_TABLE = "saved_table"
SCHEDULED_RUN = "scheduled_run"
REFERENCE = "reference"

# The call each table and run is built for, as a refusal while building names it.
_CALL = "project.record_lineage_state()"
# A column's own logic that is a column copied, as ops.jobs.team, written without brackets.
_COPIED = re.compile(r"[\w.`]+")
# The folder of a Project's Building blocks, as their modules are named from.
BLOCKS = "building_blocks"
# How a column read names every column of a table, for an Unchecked statement's text, which
# names tables, never their columns.
WHOLE_TABLE = "*"


def column_key(name: str) -> tuple[str, str]:
    """A column's (table, column), from its name as `reads` writes it, <db>.<table>.<column>,
    or <run>.<result>.<column> for a Scheduled run's Statement."""
    table, column = name.rsplit(".", 1)
    return table, column


def each_column(reads: Iterable[str], keys: Iterable[tuple[str, str]]) -> list[str]:
    """`reads`, each a column's name, with each whole-table read, <db>.<table>.*, which an
    Unchecked step's text makes, given as every column of that table `keys` hold, in order."""
    known = sorted(set(keys))
    each = []
    for read in reads:
        table, column = column_key(read)
        if column != WHOLE_TABLE:
            each.append(read)
            continue
        each += [f"{table}.{name}" for of, name in known if of == table]
    return each


@dataclass(frozen=True)
class ColumnLogic:
    """One recorded column: its own logic, what it reads and its two fingerprints.

    `table` is `<db>.<table>`, or `<run>.<result>` for a Scheduled run's Statement. `reads`
    names each column it reads as `<db>.<table>.<column>`. `own_hash` fingerprints its own
    logic and its rows that count; `effective_hash` fingerprints its own hash and the
    effective hash of every column it reads, so a change anywhere upstream changes it alone.
    An opaque column, one an Unchecked statement or Python step writes, has the whole step as
    its own logic, its text or its function's source, one fingerprint for every column the
    step writes; a column that reads an Unchecked derived table holds its text, and is opaque
    too.

    A read of `<db>.<table>.*` stands for every column of that table: an Unchecked
    statement's or an Unchecked derived table's text names tables, never their columns. A
    Table reference's column has no own logic: its own hash fingerprints its type, so a
    retyped column changes the effective hash of each column reading it."""

    table: str
    column: str
    kind: str
    type: str
    own_logic: str
    reads: tuple[str, ...]
    rows_that_count: str
    own_hash: str
    effective_hash: str
    opaque: bool = False


@dataclass(frozen=True)
class ProjectLogic:
    """Every recorded column of a Project, by (table, column); each table or Scheduled run
    that didn't build, by its name, with why; and the Building blocks each table's logic
    imports, by table, as their names."""

    columns: dict[tuple[str, str], ColumnLogic]
    not_built: dict[str, str] = field(default_factory=dict)
    blocks_of: dict[str, tuple[str, ...]] = field(default_factory=dict)


def project_logic(root: Path) -> ProjectLogic:
    """Every recorded column of the Project at `root`, worked out without the warehouse.

    Each Table folder's write() comes through project.load, as run_tables reads it, and each
    Scheduled run is built as its Build cell builds it, with its parameters' defaults, sending
    nothing; every Run value gives a stand-in, its function never called, so nothing needs
    connect(...). A Table folder whose logic doesn't load, or a run that doesn't build, is in
    `not_built` with why, never raised, and the rest is worked out. A Building block is named
    by its file's path below building_blocks/, without .py, such as owner_on_day or
    prod/owner_on_day."""
    columns: dict[tuple[str, str], ColumnLogic] = {}
    with contextlib.chdir(root), stand_ins():
        registry = Registry(root)
        tables = project_tables(registry, _CALL)
        not_built = {table: one_line_message(error)
                     for table, error in tables.passed_over.items()}
        references = _reference_tables(root)
        written: set[str] = set()
        for statement, _ in tables.writes:
            written.update(_tables_written(statement))
            _add_columns(columns, _written_columns(statement, references))
        for name in registry.in_force(RUN_FOLDER):
            built = _built_run(root, name, not_built)
            if built is None:
                continue
            _add_columns(columns, _run_columns(name, built, written, references))
            for step in built.steps:
                written.update(_tables_written(step.statement))
        blocks_of = {table: _building_blocks_imported(root, table)
                     for table in registry.in_force(TABLE_FOLDER) if table not in not_built}
    for name, table_columns in references.items():
        # A Table folder that didn't build is neither written nor a root: its rows stand.
        if name not in written and name not in not_built:
            _add_columns(columns, _reference_columns(name, table_columns))
    return ProjectLogic(_with_effective_hashes(columns), not_built, blocks_of)


def _built_run(root: Path, name: str, not_built: dict[str, str]) -> BuiltRun | None:
    """The Scheduled run `name`, built as its Build cell builds it, sending nothing; None,
    with why noted in `not_built`, when it doesn't build."""
    try:
        built, _ = built_run_of(root, name, _CALL)
    # Whatever stops a run's build, a <...> left or a refusal, is noted, never raised.
    except Exception as error:  # noqa: BLE001
        not_built[name] = one_line_message(error)
        return None
    return built


def _add_columns(columns: dict[tuple[str, str], ColumnLogic],
                 found: list[ColumnLogic]) -> None:
    """Add each column found, a second write of the same table's column joining its logic and
    reads to the first's, as two writes of one table make its rows together."""
    for column in found:
        key = (column.table, column.column)
        before = columns.get(key)
        if before is None:
            columns[key] = column
            continue
        columns[key] = _column_logic(
            column.table, column.column, before.kind, before.type or column.type,
            f"{before.own_logic}\n{column.own_logic}",
            tuple(sorted({*before.reads, *column.reads})),
            "; ".join(part for part in (before.rows_that_count, column.rows_that_count)
                      if part),
            before.opaque or column.opaque)


def _column_logic(table: str, column: str, kind: str, type_: str, own_logic: str,
                  reads: tuple[str, ...], rows_that_count: str, opaque: bool) -> ColumnLogic:
    """A recorded column with its own hash; its effective hash is worked out once every
    column is found (_with_effective_hashes)."""
    own_hash = _fingerprint(f"{own_logic}\n{rows_that_count}")
    return ColumnLogic(table, column, kind, type_, own_logic, reads, rows_that_count,
                       own_hash, "", opaque)


def _fingerprint(text: str) -> str:
    """A short fingerprint of a text: the first 16 hex digits of its SHA-256."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


# --- A Statement's columns --------------------------------------------------------------------


def _tables_written(statement: Statement | UncheckedStatement | PythonStep) -> list[str]:
    """The tables a write writes, or none for any other kind: a SELECT, a create_table(...)'s
    or an Admin statement."""
    if kinds.kind(statement) not in (kinds.WRITE, kinds.UNCHECKED, kinds.PYTHON):
        return []
    return tables_written(statement)


def _written_columns(statement: Statement | UncheckedStatement | PythonStep,
                     references: dict[str, dict[str, str]]) -> list[ColumnLogic]:
    """The columns a Table folder's write writes, each with its own logic; none for a
    Statement that writes no table."""
    if kinds.kind(statement) == kinds.UNCHECKED:
        return _unchecked_columns(statement, references)
    if kinds.kind(statement) == kinds.PYTHON:
        return _python_step_columns(statement)
    if kinds.kind(statement) != kinds.WRITE:
        return []
    table = statement._write
    found = _statement_columns(statement, table._name, SAVED_TABLE)
    return [replace(column, type=table._columns.get(column.column) or column.type)
            for column in found] + _static_partition_columns(statement)


def _statement_columns(statement: Statement, table: str, kind: str) -> list[ColumnLogic]:
    """Each output column of a checked Statement, as `table`'s, of `kind`: its own logic, the
    columns it reads and the rows that count, read from the Statement's Lineage."""
    graph = build_graph([(statement, table)])
    found = []
    for column, name in statement._outputs:
        upstream = deciding_boxes(graph, f"output:0:{name}")
        reads: set[str] = set()
        own = _output_text(statement, name, reads)
        rows = _statement_rows(statement)
        for box in graph.boxes:
            if box in upstream and graph.boxes[box]["kind"] == "condition":
                rows.append(_condition_logic_text(graph.boxes[box]["logic"], reads))
        opaque = any(read.endswith(f".{WHOLE_TABLE}") for read in reads)
        found.append(_column_logic(table, name, kind, column._type or "", own,
                                   tuple(sorted(reads)), "; ".join(rows), opaque))
    return found


def _statement_rows(statement: Statement) -> list[str]:
    """What decides the rows of every column of a Statement, past its conditions: how a write
    writes, as INSERT OVERWRITE replaces and INSERT INTO adds, and SELECT_DISTINCT."""
    rows = []
    if statement._write is not None:
        rows.append("INSERT OVERWRITE" if statement._replaces_rows else "INSERT INTO")
    if statement._distinct:
        rows.append("SELECT DISTINCT")
    return rows


def _static_partition_columns(statement: Statement) -> list[ColumnLogic]:
    """Each partition column a write fills with one value, such as dt = '2026-09-24': its own
    logic is that value, a Run value written as its function."""
    partitions = statement._partitions
    if partitions is None or partitions.tree is None:
        return []
    table = statement._write
    found = []
    for part in partitions.tree.parts["expressions"]:
        if part.kind != "EQ":
            continue
        name = part.parts["this"].parts["name"]
        reads: set[str] = set()
        own = _expression_text(statement, part.parts["expression"], reads)
        found.append(_column_logic(table._name, name, SAVED_TABLE,
                                   table._columns.get(name) or "", own, tuple(sorted(reads)),
                                   "; ".join(_statement_rows(statement)), False))
    return found


def _unchecked_columns(statement: UncheckedStatement,
                       references: dict[str, dict[str, str]]) -> list[ColumnLogic]:
    """Each column of each table an Unchecked statement writes, as its Table reference names
    them, or one column `*` for a table with none: all one opaque step, its text the own logic
    of each, reading every column of each table its text reads."""
    reads = tuple(sorted(f"{table}.{WHOLE_TABLE}" for table in tables_read(statement)))
    found = []
    for table in _tables_written(statement):
        for column, type_ in (references.get(table) or {WHOLE_TABLE: ""}).items():
            found.append(_column_logic(table, column, SAVED_TABLE, type_, statement._text,
                                       reads, "", True))
    return found


def _python_step_columns(step: PythonStep) -> list[ColumnLogic]:
    """Each column of the table a Python step writes: all one opaque step, where its function
    lives and its source the own logic of each, reading each column it read."""
    own = f"{step_place(step)}\n{_function_text(step._function)}"
    reads = tuple(sorted(step_columns_read(step)))
    table = step._writes
    return [_column_logic(table._name, column, SAVED_TABLE, type_ or "", own, reads, "", True)
            for column, type_ in table._columns.items()]


def _function_text(function: object) -> str:
    """A Python step's function as its source; for one whose source Python can't find, as a
    function defined by a logic cell run from its notebook, a fingerprint of its compiled
    code, which changes when its code does."""
    try:
        return inspect.getsource(function)
    except (OSError, TypeError):
        code = getattr(function, "__code__", None)
        if code is None:
            return repr(function)
        return f"compiled {_fingerprint(repr(_code_parts(code)))}"


def _code_parts(code: object) -> tuple[object, ...]:
    """What a function's compiled code is made of, its inner functions' too, as a fingerprint
    reads it: its bytecode, its constants and the names it uses."""
    constants = tuple(_code_parts(each) if inspect.iscode(each) else repr(each)
                      for each in code.co_consts)
    return (code.co_code, constants, code.co_names)


# --- A column's own logic, written out --------------------------------------------------------


def _output_text(step: Statement, name: str, reads: set[str]) -> str:
    """An output column's own logic: its calculation written out, and, for one that adds up
    rows, what it gives one value for; a Stack's, each of its Statements' column of that name
    within its call. Each table column it names is added to `reads`."""
    if step._stack is not None:
        call, branches = step._stack
        written = [_output_text(branch, name, reads) for branch in branches]
        return f"{call}(" + ", ".join(written) + ")"
    for column, output in step._outputs:
        if output == name:
            text = _expression_text(step, column._tree, reads)
            if column._aggregate and step._group_by:
                groups = ", ".join([_expression_text(step, each._tree, reads)
                                    for each in step._group_by])
                text += f" GROUP BY {groups}"
                if step._subtotals_call is not None:
                    text += f" {step._subtotals_call}"
            return text
    return name  # an output name a Stack's other Statement doesn't hold


def _condition_logic_text(logic: ConditionLogic, reads: set[str]) -> str:
    """A condition's clause and its Hive written out, as an output's own logic is; a Stack's
    INTERSECT or EXCEPT, each other Statement whose rows it keeps or leaves out. Each table
    column it names is added to `reads`."""
    if logic.tree is None:
        _, branches = logic.step._stack
        others = []
        for branch in branches[1:]:
            written = [_output_text(branch, name, reads) for _, name in branch._outputs]
            others.append(", ".join(written))
        return f"{logic.clause}: " + " | ".join(others)
    text = _expression_text(logic.step, logic.tree, reads)
    return " ".join(part for part in (f"{logic.clause}:", text, logic.then) if part)


def _expression_text(step: Statement, tree: Node, reads: set[str]) -> str:
    """A calculation or condition of `step` as Hive, written as its own logic compares it:
    each table's column by the table's name, each Derived table's column written out in its
    place, a Run value as its function and what it was given, a Hivevar by its name. Each
    table column it names is added to `reads`."""
    pieces: dict[str, str] = {}

    def stand_in(node: Node) -> Node | None:
        """A Node to write in place of one whose text is written out after the Hive."""
        text = _stand_in_text(step, node, reads)
        if text is None:
            return None
        token = f"__piece_{len(pieces)}__"
        pieces[token] = text
        return Node(SCRIPT_TAG, text=token)

    hive = hive_text(Node("Paren", this=tree).replaced(stand_in).parts["this"])
    for token, text in pieces.items():
        hive = hive.replace(f"`{token}`", text).replace(token, text)
    return hive


def _stand_in_text(step: Statement, node: Node, reads: set[str]) -> str | None:
    """The text a Node of `step` is written as in its own logic, or None for one written as
    Hive is: a Hivevar's name, a Run value's function and what it was given, a table's column
    by its table's name and a Derived table's written out."""
    hivevar = node.meta.get("hivevar")
    if hivevar is not None:
        return f"'${{hivevar:{hivevar}}}'"
    traced = node.meta.get("traced")
    if traced is not None:
        answers = f"{traced.tag} = " if traced.tag else ""
        return f"run_value({answers}{traced.function}({traced.arguments}))"
    if node.kind != "Column":
        return None
    for read in step._reads:
        if read.table._alias == node.table:
            return _read_text(read.table, node.name, reads)
    return None  # an output name, as in ORDER BY "runs"


def _read_text(table: Table, column: str, reads: set[str]) -> str:
    """A column a Statement reads, written out, and added to `reads`: a table's as
    <table>.<column>; a Derived table's own logic, in brackets unless it is a column copied;
    an Unchecked derived table's text and the column read, every column of each table its text
    reads added."""
    if table._statement is None:
        reads.add(f"{table._name}.{column}")
        return f"{table._name}.{column}"
    if is_unchecked(table):
        reads.update(f"{name}.{WHOLE_TABLE}" for name in table._statement._tables)
        return f"(unchecked_derived: {table._statement._text}).{column}"
    text = _output_text(table._statement, column, reads)
    if table._statement._distinct:
        return f"(DISTINCT {text})"
    if _COPIED.fullmatch(text):
        return text
    return f"({text})"


# --- Scheduled runs, Table references and Building blocks -------------------------------------


def _run_columns(name: str, built: BuiltRun, written: set[str],
                 references: dict[str, dict[str, str]]) -> list[ColumnLogic]:
    """The columns of a built Scheduled run: each SELECT's, as `<run>.<result>`, and each
    write's of a table no Table folder writes; a write the build added from a Table folder is
    that folder's, recorded there."""
    found = []
    for step in built.passed_over + built.steps:
        if kinds.kind(step.statement) == kinds.READ:
            result = step.result or step.name
            found += _statement_columns(step.statement, f"{name}.{result}", SCHEDULED_RUN)
        elif not set(_tables_written(step.statement)) & written:
            found += _written_columns(step.statement, references)
    return found


def _reference_tables(root: Path) -> dict[str, dict[str, str]]:
    """Each Table reference's table, by its name, with its columns and their types, for those
    the Reference sheet can read."""
    found = {}
    for path in table_references(root):
        read = reference_columns(path)
        if read is not None:
            found[read[0]] = read[1]
    return found


def _reference_columns(name: str, columns: dict[str, str]) -> list[ColumnLogic]:
    """A Table reference's columns, for a table the Project doesn't write: where every chain
    ends, each column's own hash its type's fingerprint."""
    return [ColumnLogic(name, column, REFERENCE, type_, "", (), "",
                        _fingerprint(f"type {type_}"), "") for column, type_ in columns.items()]


def _building_blocks_imported(root: Path, table: str) -> tuple[str, ...]:
    """The Building blocks a Table notebook's logic cell imports, by their path below
    building_blocks/, as building_blocks.prod.owner_on_day gives prod/owner_on_day."""
    notebook = root / table_notebook(table_stem(table))
    found = []
    for kind, text in read_cells(notebook):
        if kind == "code" and first_line(text) == LOGIC:
            found += _modules_imported(text)
    blocks = []
    for module in found:
        parts = module.split(".")
        if parts[0] == BLOCKS and (root / BLOCKS / f"{'/'.join(parts[1:])}.py").is_file():
            blocks.append("/".join(parts[1:]))
    return tuple(sorted(set(blocks)))


def _modules_imported(text: str) -> list[str]:
    """Each module a cell imports from, or imports, by its dotted name: from a.b import c gives
    a.b, and a.b.c too, since c may be a module; whether it is, its caller looks."""
    found = []
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.ImportFrom) and node.module:
            found.append(node.module)
            found += [f"{node.module}.{alias.name}" for alias in node.names]
        elif isinstance(node, ast.Import):
            found += [alias.name for alias in node.names]
    return found


# --- Effective hashes -------------------------------------------------------------------------


def _with_effective_hashes(columns: dict[tuple[str, str], ColumnLogic]
                           ) -> dict[tuple[str, str], ColumnLogic]:
    """Each column with its effective hash: the fingerprint of its own hash and the own hash
    of every column upstream of it, found by following each one's reads, so a change anywhere
    up the chain changes it, whatever order the columns are met in, a loop's included. A read
    of a column the Project doesn't record counts by its name alone."""
    of_table: dict[str, list[tuple[str, str]]] = {}
    for key in columns:
        of_table.setdefault(key[0], []).append(key)
    found = {}
    for key, column in columns.items():
        upstream = _upstream(key, columns, of_table)
        named = sorted(f"{name}={columns[each].own_hash if each in columns else ''}"
                       for name, each in upstream)
        found[key] = replace(column, effective_hash=_fingerprint(
            "\n".join([column.own_hash, *named])))
    return found


def _upstream(key: tuple[str, str], columns: dict[tuple[str, str], ColumnLogic],
              of_table: dict[str, list[tuple[str, str]]]) -> set[tuple[str, tuple[str, str]]]:
    """Every column upstream of `key`, as (its name, its key), following each reads, a table's
    `*` every recorded column of that table."""
    seen: set[tuple[str, tuple[str, str]]] = set()
    waiting = list(columns[key].reads)
    while waiting:
        read = waiting.pop()
        table, column = read.rsplit(".", 1)
        keys = of_table.get(table, []) if column == WHOLE_TABLE else [(table, column)]
        for each in keys or [(table, column)]:
            name = f"{each[0]}.{each[1]}"
            if (name, each) in seen:
                continue
            seen.add((name, each))
            if each in columns:
                waiting += columns[each].reads
    return seen
