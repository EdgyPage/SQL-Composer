"""A Formula workbook's Hive, written by the Toolbox (Toolbox 8.9, ticket 04; ADR 0016).

`workbook_hive` gives each piece the workbook reader finds its role, as Copilot file 15's
P1 to P11 and R1 to R3 give it (`piece_roles`), and writes each final's query as sqlglot's
tree: its sources as `<database>.<table>`, each step it reads as a CTE, after each CTE that
step reads, and its columns in its Table's order, each formula by file 11's rule
(`workbook_formulas.py`). What it gives back, a WorkbookHive, holds each final's query and a
list of what the map names, in file 15's map's words: each value written in, each value typed
over a formula, each mark, each refusal, each thing left alone and each `<...>` to fill in.
`map_text` writes that map as file 15's Output does.

A loop (P11) never reaches here: the reader refuses a workbook whose pieces read each other in
one, naming each link.

Where each kind of piece's Hive comes from is one function each, below: a Table's
(`_table_tree`), a Power Query's (`_power_query_tree`, by `workbook_power_query.py`, file 12's
rules), a Total Row's (`_total_row_finals`, the same file's), and any other kind's
(`_piece_tree`), so a file writing more of them, such as PivotTables, plugs in there, and adds
the functions a formula may call to `_functions`. Each final keeps in its CTEs only the columns
something after them reads (`lean_ctes`).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from sqlglot import exp

from .shared import counted, in_words
from .workbook_formulas import (
    FUNCTIONS,
    KEYS,
    LEFT_ALONE,
    MARK,
    PARAMETERS,
    REFUSED,
    TO_FILL_IN,
    TYPED_OVER,
    WRITTEN_IN,
    Book,
    Call,
    Note,
    Place,
    constant_hive,
    hive_name,
    identifier,
    summary_matches,
    table_query,
    tables_of,
)
from .workbook_formula_reader import Refused
from .workbook_power_query import (
    TOTAL_ROW,
    WHOLE_COLUMN_FUNCTIONS,
    lean_ctes,
    power_query_hive,
    total_row_finals,
    web_source,
)
from .workbook_reader import EXCEL_TABLE, POWER_QUERY, TYPED, Piece, Table, Workbook, coordinate
from .writing import sql_text

# Each piece's role, in file 15's words.
SOURCE = "source"
STEP = "step"
FINAL = "final"
SUMMARY_FINAL = "summary final"
SETTINGS = "settings"
LOADS = "loads its Table"
LEFT_OUT = "left out"
# The database each source is in, for the person to fill in (file 11's N1).
DATABASE = "<database>"
# What the map says of each kind of Note, in file 15's Output's order.
NOTE_HEADINGS = {WRITTEN_IN: "Written in", TYPED_OVER: "Typed over", MARK: "Marks",
                 REFUSED: "Refused", LEFT_ALONE: "Left alone", TO_FILL_IN: "To fill in"}


@dataclass
class WorkbookHive:
    """A Formula workbook's Hive: each piece's role; each final's query, by its name in the
    workbook, a Total Row's as `<Table> (Total Row)`; and what the map names."""

    roles: dict[Piece, str]
    finals: dict[str, exp.Query]
    notes: list[Note]


def piece_roles(workbook: Workbook) -> dict[Piece, str]:
    """Each piece's role, from what reads what, as file 15's Patterns give it: a Table of
    typed columns a source (P1); one with a formula column a step if another piece reads it
    (P2, R3), else a final (P3), or a summary final (P4, R1); a Table a query loads a step if
    another piece reads it, else a final (P6, P7); a query another query reads a step (P5),
    one loading a Table that Table's rows, any other left out (P8); Parameters and Keys
    settings (P10). A piece of any other kind is a step if another piece reads it, else a
    final."""
    readers: dict[Piece, list[Piece]] = {piece: [] for piece in workbook.order}
    for piece, read in workbook.order.items():
        for each in read:
            readers.setdefault(each, []).append(piece)
    tables = tables_of(workbook)
    roles = {}
    for piece in workbook.order:
        read_by = readers[piece]
        if piece.kind == EXCEL_TABLE:
            roles[piece] = _table_role(tables[piece.name.lower()], read_by)
        elif piece.kind == POWER_QUERY:
            roles[piece] = _query_role(piece, read_by, workbook)
        else:
            roles[piece] = STEP if read_by else FINAL
    return roles


def _table_role(table: Table, read_by: list[Piece]) -> str:
    if table.name.lower() in (PARAMETERS.lower(), KEYS.lower()):
        return SETTINGS
    has_formulas = any(column.kind != TYPED for column in table.columns)
    if not table.loaded_by and not has_formulas:
        return SOURCE
    if read_by:
        return STEP
    if not table.loaded_by and is_summary(table):
        return SUMMARY_FINAL
    return FINAL


def _query_role(piece: Piece, read_by: list[Piece], workbook: Workbook) -> str:
    if any(reader.kind == POWER_QUERY for reader in read_by):
        return STEP
    for query in workbook.queries:
        if query.name == piece.name and query.loads:
            return LOADS
    return LEFT_OUT


def is_summary(table: Table) -> bool:
    """Whether a Table is a summary: it has a formula column, and its only typed columns are
    the ones its -IF(S) forms over another Table match on with this row's value (P4, R1)."""
    typed = {column.header.lower() for column in table.columns if column.kind == TYPED}
    has_formulas = any(column.kind != TYPED for column in table.columns)
    return bool(typed) and has_formulas and typed <= summary_matches(table)


def workbook_hive(workbook: Workbook, database: str = DATABASE,
                  total_rows_left_out: tuple[str, ...] = ()) -> WorkbookHive:
    """A Formula workbook's Hive: each final's query, as sqlglot's tree, and what its map
    names. `database` is the database each source is in, `<database>` for the person to fill
    in where it is left out; `total_rows_left_out` names each Table whose Total Row the person
    said no one needs kept (file 12's T3)."""
    roles = piece_roles(workbook)
    book = Book(workbook, database, _functions())
    trees: dict[Piece, exp.Query] = {}
    for piece, role in roles.items():
        if role == SOURCE:
            book.reads[piece] = _database_table(piece.name, database)
        if role in (SOURCE, SETTINGS):
            continue
        tree = _piece_tree(piece, role, book)
        if tree is None:
            continue
        trees[piece] = tree
        book.reads[piece] = _read_of(piece, role, tree, roles)
    tables, finals = {}, {}
    for piece, role in roles.items():
        if piece not in trees:
            continue
        written = _with_steps(trees[piece], piece, roles, trees, workbook)
        if piece.kind == EXCEL_TABLE:
            tables[piece.name] = written
        if role in (FINAL, SUMMARY_FINAL):
            finals[piece.name] = lean_ctes(written)
    finals.update(_total_row_finals(workbook, tables, book, total_rows_left_out))
    notes = book.notes + _left_alone(workbook, roles) + _to_fill_in(workbook, finals, database)
    return WorkbookHive(roles, finals, notes)


def _functions() -> dict[str, Callable[[Call, Place], exp.Expression]]:
    """The function each name a formula calls is written by: file 11's (`FUNCTIONS`), and file
    12's whole-column totals (T1); a file writing more adds its own here. A copy, so adding
    them never changes `FUNCTIONS`, which holds file 11's alone."""
    return {**FUNCTIONS, **WHOLE_COLUMN_FUNCTIONS}


def _database_table(name: str, database: str) -> exp.Table:
    """A source as `<database>.<table>` (file 15's step 4)."""
    return exp.Table(this=identifier(name), db=exp.Identifier(this=database, quoted=False))


def _cte_name(piece: Piece, roles: dict[Piece, str]) -> str:
    """A step's CTE's name: its own (N1, N2), a query's with `_query` after it where a Table
    of its name is a step too, as a query and the Table it loads are two pieces."""
    name = hive_name(piece.name)
    if piece.kind != POWER_QUERY or roles.get(Piece(EXCEL_TABLE, piece.name)) != STEP:
        return name
    if name.endswith(">"):
        return name[:-1] + "_query>"
    return name + "_query"


def _read_of(piece: Piece, role: str, tree: exp.Query,
             roles: dict[Piece, str]) -> exp.Expression:
    """How another piece reads this one: a step by its CTE's name; a query loading a Table,
    as its rows, in place."""
    if role == STEP:
        return exp.Table(this=exp.Identifier(this=_cte_name(piece, roles), quoted=False))
    return tree


def _with_steps(tree: exp.Query, piece: Piece, roles: dict[Piece, str],
                trees: dict[Piece, exp.Query], workbook: Workbook) -> exp.Query:
    """A final's query with each step it reads, at any depth, as a CTE, each after each CTE it
    reads, in the Order (file 15's step 4, C7)."""
    needed: set[Piece] = set()
    waiting = list(workbook.order[piece])
    while waiting:
        each = waiting.pop()
        if each in needed or each not in trees:
            continue
        if roles[each] == STEP:
            needed.add(each)
        waiting += workbook.order.get(each, [])
    final = tree.copy()
    for each in workbook.order:
        if each in needed:
            final = final.with_(exp.Identifier(this=_cte_name(each, roles), quoted=False),
                                as_=trees[each].copy())
    return final


# --- Where each kind of piece's Hive comes from ---------------------------------------------


def _piece_tree(piece: Piece, role: str, book: Book) -> exp.Query | None:
    """A step's or a final's query, by its piece's kind; None, refused and named, where it has
    none."""
    if piece.kind == EXCEL_TABLE:
        return _table_tree(tables_of(book.workbook)[piece.name.lower()], book)
    if piece.kind == POWER_QUERY:
        return _power_query_tree(piece, role, book)
    book.notes.append(Note(REFUSED, "X1", f"{piece.kind} \"{piece.name}\"",
                           f"a {piece.kind} isn't converted by the code yet"))
    return None


def _table_tree(table: Table, book: Book) -> exp.Query | None:
    """A Table's query: a summary's from its groups, written in (R1); a Table a query loads
    from the query's rows (P6, P7); any other from `<database>.<table>` (file 15's step 4);
    with each formula column by file 11."""
    if table.loaded_by:
        rows = book.reads.get(Piece(POWER_QUERY, table.loaded_by))
        if rows is None:
            book.notes.append(Note(REFUSED, "P7", table.name,
                                   f"its rows are Power Query \"{table.loaded_by}\"'s, "
                                   "which has no Hive"))
            return None
        if all(column.kind == TYPED for column in table.columns) and not isinstance(
                rows, exp.Table):
            return rows.copy()
        return table_query(table, rows, book)
    if is_summary(table):
        return table_query(table, summary_groups(table, book), book)
    return table_query(table, _database_table(table.name, book.database), book)


def _power_query_tree(piece: Piece, role: str, book: Book) -> exp.Query | None:
    """A Power Query's rows, by file 12's rules (`power_query_hive`); refused and named, the
    query left out, where they can't be written. A query left out (P8) is only named, and
    refused too where it reads the web (X1)."""
    where = f"Power Query \"{piece.name}\""
    if role == LEFT_OUT:
        for query in book.workbook.queries:
            if query.name == piece.name and web_source(query.m) is not None:
                book.notes.append(Note(REFUSED, "X1", where, f"{web_source(query.m)} reads the "
                                       "web, so the query is left out"))
        return None
    try:
        tree, notes = power_query_hive(piece.name, book)
    except Refused as refusal:
        book.notes.append(Note(REFUSED, refusal.rule, where, f"left out: {refusal.why}"))
        return None
    book.notes += notes
    return tree


def _total_row_finals(workbook: Workbook, tables: dict[str, exp.Query], book: Book,
                      left_out: tuple[str, ...]) -> dict[str, exp.Query]:
    """Each Table's Total Row's final, `<Table> (Total Row)` (P9, R2), reading the Table's
    query, `tables` by its name, as a CTE: file 12's T2 to T4 (`total_row_finals`)."""
    return total_row_finals(workbook, tables, book, left_out)


def summary_groups(table: Table, book: Book) -> exp.Query:
    """A summary's groups, its typed rows, written into the Hive, each once, as file 15's W3
    writes them: `SELECT 1 AS job_id UNION ALL SELECT 2`; named in the map, since a later
    group won't be in the table (R1)."""
    typed = [column for column in table.columns if column.kind == TYPED]
    rows = list(dict.fromkeys(zip(*[column.cells for column in typed], strict=True)))
    rows = [row for row in rows if set(row) != {None}]
    if not rows:
        rows = [(None,) * len(typed)]
    first = exp.select(*[exp.alias_(constant_hive(value), identifier(column.header))
                         for value, column in zip(rows[0], typed, strict=True)])
    groups: exp.Query = first
    for row in rows[1:]:
        groups = exp.union(groups, exp.select(*[constant_hive(value) for value in row]),
                           distinct=False)
    shown = in_words([", ".join(map(str, row)) for row in rows])
    named = in_words([column.header for column in typed])
    book.notes.append(Note(WRITTEN_IN, "R1", table.name,
                           f"its groups, {named} {shown}: a later one won't be in the table"))
    return groups


# --- What the map names ----------------------------------------------------------------------


def _left_alone(workbook: Workbook, roles: dict[Piece, str]) -> list[Note]:
    """Each thing the conversion leaves alone, named (file 11's X1, file 15's P8): each query
    that loads nothing and nothing reads, each chart and PivotTable, and the cells outside a
    Table holding a number, a date or a formula."""
    notes = [Note(LEFT_ALONE, "P8", f"Power Query \"{piece.name}\"",
                  "it loads nothing and nothing reads it: left out")
             for piece, role in roles.items() if role == LEFT_OUT]
    for sheet in workbook.sheets:
        where = f"Sheet \"{sheet.title}\""
        notes += [Note(LEFT_ALONE, "X1", where, f"a {kind} chart: presentation")
                  for kind in sheet.charts]
        if sheet.pivot_tables:
            pivots = counted(len(sheet.pivot_tables), "PivotTable")
            notes.append(Note(LEFT_ALONE, "X1", where, f"{pivots}: presentation"))
        cells = [coordinate(*place) for place, value in sheet.cells.items()
                 if not isinstance(value, str) or value.startswith("=")]
        if cells:
            notes.append(Note(LEFT_ALONE, "X1", where,
                              f"{in_words(cells)}: {counted(len(cells), 'cell')} outside a "
                              "Table"))
    return notes


def _to_fill_in(workbook: Workbook, finals: dict[str, exp.Query], database: str) -> list[Note]:
    """Each `<...>` the Hive holds for the person to fill in, with the name it stands for (N1,
    N2)."""
    stands_for = {DATABASE: "the database each source is in"}
    for table in tables_of(workbook).values():
        stands_for.setdefault(hive_name(table.name),
                              f"Table {table.name}'s name in the database")
        for column in table.columns:
            stands_for.setdefault(hive_name(column.header), f"the column {column.header}")
    found: list[str] = []
    for tree in finals.values():
        found += [part.this for part in tree.find_all(exp.Identifier)
                  if str(part.this).startswith("<")]
    names = sorted(dict.fromkeys(found), key=lambda name: name != DATABASE)
    return [Note(TO_FILL_IN, "N1" if name == DATABASE else "N2", name,
                 stands_for.get(name, "a name to fill in"))
            for name in names]


def hive_texts(hive: WorkbookHive) -> dict[str, str]:
    """Each final's Hive, laid out, by its name."""
    return {name: sql_text(tree, pretty=True) for name, tree in hive.finals.items()}


def map_text(hive: WorkbookHive, workbook: Workbook) -> str:
    """The workbook's map, as file 15's Output writes it: Sources, Steps and Finals, each with
    its columns, its settings, then each value written in, each value typed over a formula,
    each mark, each refusal, what was left alone, and each `<...>` to fill in."""
    tables = tables_of(workbook)
    lines = [f"Sources: {'; '.join(_sources_shown(hive.roles, tables)) or 'none'}"]
    for heading, roles in (("Steps", (STEP,)), ("Finals", (FINAL, SUMMARY_FINAL)),
                           ("Settings", (SETTINGS,)), ("Queries loading a Table", (LOADS,))):
        named = [_piece_shown(piece, tables) for piece, role in hive.roles.items()
                 if role in roles]
        if heading == "Finals":
            named += [f"{name} ({', '.join(query.named_selects)})"
                      for name, query in hive.finals.items() if name.endswith(TOTAL_ROW)]
        if named:
            lines.append(f"{heading}: {'; '.join(named)}")
    for kind, heading in NOTE_HEADINGS.items():
        notes = [note for note in hive.notes if note.kind == kind]
        if notes:
            lines.append(f"{heading}:")
            lines += [f"- {note.where}: {note.text} ({note.rule})" for note in notes]
    return "\n".join(lines) + "\n"


def _sources_shown(roles: dict[Piece, str], tables: dict[str, Table]) -> list[str]:
    """Each database table the Hive reads, with the columns it reads: a source's every column,
    and a step's or a final's typed columns, as file 15's W1 names them."""
    shown = []
    for piece, role in roles.items():
        table = tables.get(piece.name.lower())
        if piece.kind != EXCEL_TABLE or role in (SETTINGS, SUMMARY_FINAL) or table.loaded_by:
            continue
        typed = [column.header for column in table.columns if column.kind == TYPED]
        if role == SOURCE:
            shown.append(f"{table.name} ({', '.join(typed)})")
        elif not is_summary(table):
            shown.append(f"{table.name} ({', '.join(typed)}: its typed columns)")
    return shown


def _piece_shown(piece: Piece, tables: dict[str, Table]) -> str:
    """A piece as the map names it: a Table with its columns, a query by its name."""
    if piece.kind == EXCEL_TABLE:
        table = tables[piece.name.lower()]
        return f"{table.name} ({', '.join(column.header for column in table.columns)})"
    return f"{piece.kind} \"{piece.name}\""
