"""A Formula workbook given to a Conversion (Toolbox 8.9, ticket 07; ADR 0016).

`project.convert(..., files=["runs.xlsx"])` reads a workbook beside any `.hql` scripts.
`converted_workbook` gives what the Conversion needs of it: each final's Hive, as
`workbook_hive.py` writes it with the batch's database filled in, under the name of the Saved
table it becomes; what the workbook's map says of each final, in plain words, for that
table's checklist; what it says of no one final, for batch.md; each source a final reads, a
Table of typed rows or a plain range, whose database table is a Decision of its table (ticket
20); and each Pivot filter of each final, for its Decision (ticket 08). The Conversion then
keeps each final's Hive in the batch's scripts/, as it keeps Hive given as text, and converts
it as it converts any batch's.

A final's table is named for it: a Table's name, or a pivot's (PN1), in snake case. Two names
are proposed, each a Decision of its table, the table made under the proposal until the
person answers "name" in the decisions cell: a pivot keeping Excel's default name, named for
its sheet (PN2); and a final named as a database table the batch reads, as a Table with
formula columns over its own rows is, `<name>_report`. A Total Row is named for its Table's
table, `job_runs_report_total_row`, and renamed with it; a pivot's totals are no table of
their own (file 20's PL1). Converted again, a batch keeps the name each final's table has.

A source's database table is proposed from its name, `<database>.<name>`: a Table's name in
lower case, which is its snake case, or a range's defined name or sheet in snake case (PS3),
so a Table needn't be named as the warehouse names its table. The person answers "sources"
with the table it samples, such as `{"ops.table1": "ops.job_runs"}`, each in any database.
Where DESCRIBE finds no table of the name proposed, its Table reference is written from the
source's own rows, so the final converts before the answer.
"""

from __future__ import annotations

import re
import zipfile
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import NoReturn

from .refusals import refuse
from .shared import in_words, split_table_name
from .workbook_check import FinalHive
from .workbook_formulas import (
    KEYS,
    LEFT_ALONE,
    MARK,
    PARAMETERS,
    PLAIN_NAME,
    REFUSED,
    TO_FILL_IN,
    TYPED_OVER,
    WRITTEN_IN,
    Note,
    snake_case,
    tables_of,
)
from .workbook_hive import (
    DATABASE,
    SETTINGS,
    WorkbookHive,
    hive_texts,
    is_summary,
    workbook_hive,
)
from .workbook_pivot_hive import (
    DEFAULT_NAME,
    ConvertedPivotFilter,
    pivot_filters,
    pivot_of,
    pivot_table_names,
    range_table_name,
)
from .workbook_reader import (
    EXCEL_TABLE,
    PIVOT_TABLE,
    RANGE,
    TYPED,
    Column,
    LoopError,
    Piece,
    Workbook,
    read_workbook,
)
from .workflows import batch_record

# The files a Conversion reads as a workbook, by their ending; an .xls, Excel's older kind, it
# can't read.
WORKBOOK_SUFFIXES = (".xlsx", ".xlsm")
OLD_WORKBOOK = ".xls"
# What a final's name is proposed with, where it is named as a database table the batch reads.
REPORT = "_report"
# Where a batch's written.json keeps the workbook and the final each table came from.
WORKBOOK_FINALS = "workbook_finals"
# What each kind of the map's notes is, as a checklist says it, in file 15's Output's words,
# and what the person does about it.
NOTE_WORDS = {WRITTEN_IN: "written in", TYPED_OVER: "typed over a formula", MARK: "marked",
              REFUSED: "refused", LEFT_ALONE: "left alone", TO_FILL_IN: "to fill in"}
NEXT_STEPS = {
    WRITTEN_IN: "check it still holds for the database's rows, which may hold more",
    TYPED_OVER: "the value typed over the formula is kept, as Excel shows it: check it is "
                "still wanted",
    MARK: "check the values it gives are the ones you want, as the compare step shows them",
    REFUSED: "it is NULL, or left out, in the table: if you need it, write it yourself in the "
             "table's logic cell",
    LEFT_ALONE: "nothing to do",
    TO_FILL_IN: "write the database's name in its place",
}
# What the person does about a PivotTable's total, left out of its table (file 20's PL2), in
# place of its kind's.
TOTAL_LEFT_OUT = "PL2"
TOTAL_NEXT_STEP = ("nothing to do, unless you need it: run the query, or keep every total in "
                   "one table as Copilot file 21's R9 says")
# The Copilot file each rule's ID is explained in, by its first letters: a rule M or X is in
# file 11 for a formula, and in file 12 for a Power Query; a total's (T) in file 23 and a Pivot
# filter's (PF) in file 24, split out of files 12 and 20 to fit (Toolbox 8.9, ticket 14).
RULE_FILES = (("PR", "20"), ("PV", "20"), ("PC", "20"), ("PL", "20"), ("PF", "24"),
              ("PG", "20"), ("PS", "20"), ("PN", "20"), ("PX", "20"), ("P", "15"),
              ("R", "15"), ("W", "15"), ("N", "11"), ("F", "11"), ("I", "11"), ("V", "11"),
              ("Q", "12"), ("G", "12"), ("S", "12"), ("T", "23"), ("M", "11 or 12"),
              ("X", "11 or 12"))
# A note's place, such as `Power Query "ok_runs"`, and its column after it, such as `[hours]`.
_PLACE_NAMED = re.compile(r'[A-Za-z ]+ "(?P<name>.*)"')
_COLUMN_AFTER = re.compile(r"\[[^\]]*\]$")
# The type a range's column is guessed as, by the kind of value its cells hold.
_GUESSED_TYPES = ((bool, "boolean"), (int, "bigint"), (float, "double"))


@dataclass(frozen=True)
class FinalName:
    """The name of the table a final becomes, its plain lowercase name, and why it was
    proposed: "" where it is the final's own, or the one its table has from an answer."""

    table: str
    proposed: str = ""


@dataclass(frozen=True)
class FinalOrigin:
    """Where a converted table came from: its workbook, by its path as the batch names it, and
    its final's name in the workbook, such as `PivotTable1`, for the Workbook check (ticket
    09)."""

    workbook: str
    final: str


@dataclass(frozen=True)
class WorkbookSource:
    """A database table a source a final reads samples, a Table of typed rows or a plain
    range, proposed from its name, a Decision of the final's table: its name in the database,
    `ops.table1`; where in the workbook it is, `Table1 of runs.xlsx` or `Runs!A1:F10`; and its
    columns, each typed as its cells suggest, for its Table reference where the database has
    no such table."""

    table: str
    where: str
    columns: dict[str, str]


@dataclass
class WorkbookFinal:
    """One final of a workbook, as a Conversion takes it: its name in the workbook, such as
    `PivotTable1`; the Saved table it becomes, its plain lowercase name, which its script is
    named for; its Hive; why that name was proposed, "" where it is the final's own; each line
    of the workbook's map about it, for its table's checklist; each `<...>` its Hive still
    holds, which stops it converting; each Pivot filter its rows go through, its `final` the
    workbook's name of the pivot it is in; its workbook's file's name; each source it reads,
    a Table of typed rows or a plain range; and, for a PivotTable, the name its notes' queries
    of its totals read its table by, as the map writes it (`notes_retargeted_to`)."""

    final: str
    table: str
    hive: str
    proposed: str = ""
    notes: list[str] = field(default_factory=list)
    to_fill_in: list[str] = field(default_factory=list)
    filters: list[ConvertedPivotFilter] = field(default_factory=list)
    workbook: str = ""
    sources: list[WorkbookSource] = field(default_factory=list)
    totals_read: str = ""

    @property
    def script(self) -> str:
        """The name its Hive is kept under, in the batch's scripts/: its table's, as a query
        alone in a batch is a Saved table named for its file."""
        return f"{self.table}.hql"


@dataclass
class ConvertedWorkbook:
    """A workbook as a Conversion takes it: its file's name, each final, and each line of its
    map about no one final, such as a chart left alone or a pivot refused, for batch.md."""

    file: str
    finals: list[WorkbookFinal]
    notes: list[str] = field(default_factory=list)


@dataclass
class BatchWorkbooks:
    """The workbooks a batch reads, where each is, by its file's name, its path as the batch
    names it; and what each of its scripts stands for: each script named for a workbook's
    final, as Copilot names one, by its name, and the final it is the Hive of, which the batch
    converts from the script in place of the workbook. A batch holding a workbook names each
    query alone for its file."""

    workbooks: list[ConvertedWorkbook] = field(default_factory=list)
    places: dict[str, str] = field(default_factory=dict)
    copilot_finals: dict[str, WorkbookFinal] = field(default_factory=dict)

    def every_final(self) -> list[WorkbookFinal]:
        """Each final of each workbook, in order."""
        finals = []
        for workbook in self.workbooks:
            finals += workbook.finals
        return finals

    def finals_kept(self, workbook: ConvertedWorkbook | None = None) -> list[WorkbookFinal]:
        """Each final of each workbook, or of `workbook`, whose Hive the batch keeps in its
        scripts/: each but one a script of the batch is the Hive of."""
        stood_for = [id(final) for final in self.copilot_finals.values()]
        finals = self.every_final() if workbook is None else workbook.finals
        return [final for final in finals if id(final) not in stood_for]

    def finals_converted(self) -> list[WorkbookFinal]:
        """Each final the batch converts from its workbook: each it keeps but one whose Hive
        holds a `<...>`."""
        return [final for final in self.finals_kept() if not final.to_fill_in]

    def final_of_script(self) -> dict[str, WorkbookFinal]:
        """Each final the batch converts from its workbook, by its script's name."""
        return {final.script: final for final in self.finals_converted()}

    def copilot_script_of(self, final: WorkbookFinal) -> str:
        """The script Copilot wrote that stands for `final`, by its name, or ""."""
        for script, stood_for in self.copilot_finals.items():
            if stood_for is final:
                return script
        return ""

    def finals_to_check(self, workbook: ConvertedWorkbook, texts: dict[str, str],
                        dev: str) -> list[FinalHive]:
        """Each final of `workbook` the batch converted, as the Workbook check (ticket 09)
        takes it, its table in `dev`: from the script Copilot wrote for it, by the scripts'
        texts `texts`, where one stands for it, else from the workbook's own Hive."""
        finals = []
        converted = self.finals_converted()
        for final in workbook.finals:
            table = f"{dev}.{final.table}"
            script = self.copilot_script_of(final)
            if script:
                finals.append(FinalHive(final.final, table, texts[script], script))
            elif final in converted:
                finals.append(FinalHive(final.final, table, final.hive))
        return finals


def is_workbook(file: str) -> bool:
    """Whether a file a Conversion is given is a workbook, by its ending."""
    return Path(file).suffix.lower() in WORKBOOK_SUFFIXES


def converted_workbook(call: str, path: Path, database: str,
                       names_kept: dict[str, str]) -> ConvertedWorkbook:
    """A workbook as a Conversion takes it, its sources in `database`, each final's table
    named as `names_kept` names it, by the final's name in the workbook, as a batch converted
    before named it, or else for itself, as the module docstring says. Refused for a file that
    isn't a workbook the reader reads, such as one whose pieces read each other in a loop, and
    for a workbook with no final."""
    workbook = read_workbook_or_refuse(call, path)
    hive = workbook_hive(workbook, database=database)
    if not hive.finals:
        _refuse_nothing_to_convert(call, path.name, hive)
    names = final_table_names(workbook, hive, names_kept)
    owned, of_no_final = notes_by_final(workbook, hive)
    filters = pivot_filters(workbook)
    pivots = pivot_table_names(workbook)
    finals = []
    for final, text in hive_texts(hive).items():
        name = names[final]
        notes = []
        if name.proposed:
            notes.append(proposed_name_note(name))
        notes += [checklist_note_text(note) for note in owned[final] if note.rule != "PN2"]
        read = _pieces_a_final_reads(final, workbook)
        to_fill_in = [note.where for note in owned[final] if note.kind == TO_FILL_IN]
        read_names = {piece.name.lower() for piece in read}
        finals.append(WorkbookFinal(
            final, name.table, text, name.proposed, notes, to_fill_in,
            [each for each in filters if each.final.lower() in read_names], path.name,
            sources_of(text, read, workbook, database, path.name), pivots.get(final, "")))
    return ConvertedWorkbook(path.name, finals,
                             [checklist_note_text(note) for note in of_no_final])


def read_workbook_or_refuse(call: str, path: Path) -> Workbook:
    """The workbook at `path`, read; refused where it can't be: a file that isn't a workbook,
    or one whose pieces read each other in a loop."""
    try:
        return read_workbook(path)
    except LoopError as loop:
        refuse(what=f"{call}: {path.name}: {loop.what}", why=loop.why, fix=loop.fix,
               error=ValueError)
    except (zipfile.BadZipFile, KeyError):
        refuse(what=f"{call}: {path.name} ends in {path.suffix}, but isn't a workbook Excel "
               "saved.",
               why="A Conversion reads a workbook's Tables, formulas, Power Queries and "
               "PivotTables from the file Excel saves; this one it can't open as one.",
               fix="Open it in Excel and save it again as an Excel Workbook (.xlsx), then "
               "convert it again.", error=ValueError)


def refuse_an_old_workbook(call: str, file: str) -> NoReturn:
    """Refuse an .xls, Excel's older kind of workbook, which the reader can't read."""
    refuse(what=f"{call}: {Path(file).name} is an .xls, Excel's older kind of workbook.",
           why="A Conversion reads the kind of workbook Excel saves since 2007, an .xlsx, "
           "which holds its Tables, Power Queries and PivotTables as it reads them.",
           fix="Open it in Excel, save it as an Excel Workbook (.xlsx), and give that file.",
           error=ValueError)


def _refuse_nothing_to_convert(call: str, file: str, hive: WorkbookHive) -> NoReturn:
    """Refuse a workbook with no final, naming what of it was refused, if anything was."""
    refused = [f"{note.where} ({note.text})" for note in hive.notes if note.kind == REFUSED]
    found = ""
    if refused:
        found = f" Refused: {'; '.join(refused)}."
    refuse(what=f"{call}: {file} holds nothing to convert: no Table with a formula column, "
           f"no Power Query loading a Table, and no PivotTable that converts.{found}",
           why="A Conversion makes a Saved table of each calculation nothing else in the "
           "workbook reads; a Table of typed values alone stands for a database table "
           "already, so it makes none.",
           fix="Put the calculation in the workbook, as a formula column in a Table, a Power "
           "Query loading a Table, or a PivotTable, save it, and convert it again.",
           error=ValueError)


# --- Each final's table's name --------------------------------------------------------------


def final_table_names(workbook: Workbook, hive: WorkbookHive,
                      names_kept: dict[str, str]) -> dict[str, FinalName]:
    """Each final's table's name, by the final's name in the workbook, as the module
    docstring says, a number after a name two finals would share."""
    read = _database_tables_read(workbook, hive)
    pivots = pivot_table_names(workbook)
    names: dict[str, FinalName] = {}
    for final in hive.finals:
        name = _final_name(final, workbook, pivots, read, names_kept)
        taken = [each.table for each in names.values()]
        names[final] = replace(name, table=_free_name(name.table, taken))
    return names


def _final_name(final: str, workbook: Workbook, pivots: dict[str, str], read: set[str],
                names_kept: dict[str, str]) -> FinalName:
    """One final's table's name: the one the batch kept for it; else, for a Total Row, its
    Table's table's name and `total_row`; else its own, or the one proposed for it."""
    if final in names_kept:
        return FinalName(names_kept[final])
    base, _, level = final.partition(" (")
    name = _own_name(base, workbook, pivots, read)
    if base in names_kept:
        name = FinalName(names_kept[base])
    if level:
        return FinalName(f"{name.table}_{snake_case(level)}")
    return name


def _own_name(final: str, workbook: Workbook, pivots: dict[str, str],
              read: set[str]) -> FinalName:
    """A Table's or a pivot's own final's table's name, and why it was proposed."""
    if final in pivots:
        pivot = pivot_of(Piece(PIVOT_TABLE, final), workbook)
        if DEFAULT_NAME.fullmatch(pivot.name):
            return FinalName(pivots[final], f"{pivot.name} is Excel's default name, so it is "
                                            f"named for its sheet, {pivot.sheet}")
        return FinalName(pivots[final])
    name = snake_case(final)
    if name in read:
        return FinalName(name + REPORT, f"{final} is the name of a table in the database it "
                                        "reads, which a Saved table of yours can't share")
    return FinalName(name)


def _free_name(name: str, taken: list[str]) -> str:
    """`name`, or with a number after it, `_2` and on, where a table has it already."""
    free, number = name, 2
    while free in taken:
        free = f"{name}_{number}"
        number += 1
    return free


def _database_tables_read(workbook: Workbook, hive: WorkbookHive) -> set[str]:
    """The name of each database table the Hive reads, in lower case: each Table but a setting,
    a summary or one a query loads, read as `<database>.<table>`, where its name is a plain
    one."""
    read = set()
    for piece, role in hive.roles.items():
        if piece.kind != EXCEL_TABLE or role == SETTINGS:
            continue
        if PLAIN_NAME.fullmatch(piece.name) and is_read_from_the_database(piece.name, workbook):
            read.add(piece.name.lower())
    return read


def is_read_from_the_database(table: str, workbook: Workbook) -> bool:
    """Whether a Table's rows are its database table's: not a summary's, nor a query's."""
    found = tables_of(workbook)[table.lower()]
    return not found.loaded_by and not is_summary(found)


def proposed_name_note(name: FinalName) -> str:
    """A table's checklist note saying its name was proposed, a Decision, and how to answer
    it."""
    return (f"Its name, {name.table}, is proposed: {name.proposed}. It is a Decision: answer "
            '"name" in the decisions cell, "proposed" to keep it, or a name of your own, such '
            'as "runs_by_job", which renames the table, and its Total Row\'s table, if it has '
            "one, with it.")


def names_kept_of(origins: dict[str, FinalOrigin], workbook: str) -> dict[str, str]:
    """The name each final of `workbook`, by its path as the batch names it, has as its
    table's, by the final's name: as a batch converted before named it, `origins` being what
    its written.json keeps."""
    return {origin.final: split_table_name(table)[1] for table, origin in origins.items()
            if origin.workbook == workbook}


def final_origins_of_batch(root: Path, name: str) -> dict[str, FinalOrigin]:
    """Where each table the batch `name` made from a workbook came from, by the table, as its
    written.json keeps it: none for a batch with no workbook, or that isn't there."""
    kept = batch_record(root, name).get(WORKBOOK_FINALS, {})
    return {table: FinalOrigin(origin["workbook"], origin["final"])
            for table, origin in kept.items()}


# --- Each source's database table -----------------------------------------------------------


def sources_of(hive: str, read: set[Piece], workbook: Workbook, database: str,
               file: str) -> list[WorkbookSource]:
    """Each source a final's Hive, `hive`, reads in `database`, of the pieces it reads at any
    depth, `read`: each Table whose typed rows stand for a database table, and each plain range
    a pivot reads, in the order the Hive first names them."""
    candidates: dict[str, WorkbookSource] = {}
    for piece in read:
        if piece.kind == RANGE:
            source = range_source(piece, workbook, database)
        elif piece.kind == EXCEL_TABLE and _stands_for_a_database_table(piece.name, workbook):
            source = table_source(piece, workbook, database, file)
        else:
            continue
        candidates[source.table] = source
    named = {}
    for name, source in candidates.items():
        found = re.search(rf"(?<![\w.]){re.escape(name)}(?!\w)", hive, re.IGNORECASE)
        if found:
            named[found.start()] = source
    return [named[place] for place in sorted(named)]


def _stands_for_a_database_table(name: str, workbook: Workbook) -> bool:
    """Whether a Table's typed rows stand for a database table, read as `<database>.<name>`:
    a plain name, neither Parameters nor Keys, and rows neither a summary's nor a query's."""
    if not PLAIN_NAME.fullmatch(name) or name.lower() in (PARAMETERS.lower(), KEYS.lower()):
        return False
    return is_read_from_the_database(name, workbook)


def table_source(piece: Piece, workbook: Workbook, database: str,
                 file: str) -> WorkbookSource:
    """The database table a Table's typed rows sample, proposed as its name in lower case,
    with each typed column, typed as its cells suggest."""
    table = tables_of(workbook)[piece.name.lower()]
    typed = [column for column in table.columns if column.kind == TYPED]
    return WorkbookSource(f"{database}.{piece.name.lower()}", f"{piece.name} of {file}",
                          _guessed_columns(typed))


def range_source(piece: Piece, workbook: Workbook, database: str) -> WorkbookSource:
    """The database table a plain range samples, proposed for its sheet (PS3), with its
    columns, each typed as its cells suggest."""
    table = None
    for pivot in workbook.pivot_tables:
        if pivot.source.pieces == [piece]:
            table = pivot.source.table
    return WorkbookSource(f"{database}.{range_table_name(piece, workbook)}", piece.name,
                          _guessed_columns(table.columns if table is not None else []))


def _guessed_columns(columns: list[Column]) -> dict[str, str]:
    """Each column of a source's rows, by its name in snake case, its type as its cells
    suggest: "boolean", "bigint", "double" or else "string"."""
    guessed_columns: dict[str, str] = {}
    for column in columns:
        kinds = {type(cell) for cell in column.cells if cell is not None}
        guessed = "string"
        for kind, name in _GUESSED_TYPES:
            if kinds == {kind}:
                guessed = name
        if kinds == {int, float}:
            guessed = "double"
        guessed_columns[snake_case(column.header)] = guessed
    return guessed_columns


# --- What the map says, table by table -----------------------------------------------------


def checklist_note_text(note: Note) -> str:
    """One line of the workbook's map in plain words, as a checklist or batch.md lists it: what
    it is, the rule and the Copilot file that explains it, and what to do about it."""
    next_step = NEXT_STEPS[note.kind]
    if note.rule == TOTAL_LEFT_OUT:
        next_step = TOTAL_NEXT_STEP
    return (f"From the workbook, {NOTE_WORDS[note.kind]} (rule {note.rule}, in Copilot file "
            f"{_rule_file(note.rule)}): {note.where}: {note.text}. Next: {next_step}.")


def _rule_file(rule: str) -> str:
    """The Copilot file a rule's ID is explained in, by its first letters."""
    for start, file in RULE_FILES:
        if rule.startswith(start):
            return file
    return "15"


def notes_by_final(workbook: Workbook,
                   hive: WorkbookHive) -> tuple[dict[str, list[Note]], list[Note]]:
    """Each line of the workbook's map, by each final it is about (`_finals_a_note_is_about`),
    and the lines about no one final, such as a chart left alone, or a pivot refused, with no
    final."""
    texts = hive_texts(hive)
    owned: dict[str, list[Note]] = {final: [] for final in hive.finals}
    of_no_final = []
    for note in hive.notes:
        owners = _finals_a_note_is_about(note, workbook, texts)
        for final in owners:
            owned[final].append(note)
        if not owners and not (note.kind == TO_FILL_IN and note.where == DATABASE):
            of_no_final.append(note)
    return owned, of_no_final


def _finals_a_note_is_about(note: Note, workbook: Workbook, texts: dict[str, str]) -> list[str]:
    """The finals one line of the map is about: for a `<...>` to fill in, each whose Hive holds
    it; for any other, each that is, or reads at any depth, the piece its place names."""
    if note.kind == TO_FILL_IN:
        return [final for final, text in texts.items() if note.where in text]
    named = _named_in(note.where)
    owners = []
    for final in texts:
        read = {piece.name.lower() for piece in _pieces_a_final_reads(final, workbook)}
        if named in read or named == final.lower():
            owners.append(final)
    return owners


def _named_in(where: str) -> str:
    """The piece a note's place names, in lower case: `job_runs` of `job_runs[hours]`, and
    `ok_runs` of `Power Query "ok_runs"`."""
    piece = _COLUMN_AFTER.sub("", where)
    found = _PLACE_NAMED.fullmatch(piece)
    if found:
        piece = found["name"]
    return piece.lower()


def _pieces_a_final_reads(final: str, workbook: Workbook) -> set[Piece]:
    """The piece a final is, a Total Row's its Table's, and every piece it reads, at any
    depth."""
    base = final.partition(" (")[0]
    start = [piece for piece in workbook.order if piece.name.lower() == base.lower()]
    found: set[Piece] = set()
    waiting = list(start)
    while waiting:
        piece = waiting.pop()
        if piece in found:
            continue
        found.add(piece)
        waiting += workbook.order.get(piece, [])
    return found


def filters_retargeted_to(final: WorkbookFinal, table: str) -> list[ConvertedPivotFilter]:
    """Each Pivot filter a final's rows go through, its `final` the name of the table the final
    became, as the Copilot path's Hive gives it."""
    return [replace(each, final=table) for each in final.filters]


def notes_retargeted_to(final: WorkbookFinal, table: str) -> list[str]:
    """Each line of the map about a final, for its table's checklist, each query of a
    PivotTable's total reading the table the final became, `table`, by its full name, which a
    rename writes again (file 20's PL2)."""
    if not final.totals_read:
        return list(final.notes)
    read = re.compile(rf"FROM {re.escape(final.totals_read)}(?=`| GROUP BY )")
    return [read.sub(f"FROM {table}", note) for note in final.notes]


def not_converted_text(final: WorkbookFinal) -> str:
    """Why a final whose Hive holds a `<...>` isn't converted, as convert's report says it."""
    return (f"its Hive holds {in_words(final.to_fill_in)}, a name to fill in: in the workbook, "
            "name the Table or the column as the database names it, and convert again, or "
            f"fill each in the Hive kept in scripts/, {final.script}, and convert that file")


def is_copilots_hive_of(script: str, final: WorkbookFinal) -> bool:
    """Whether a script is a workbook final's Hive, as Copilot writes it: named for the final,
    by its name in the workbook or its table's, such as pivot.hql or PivotTable1.hql."""
    stem = Path(script).stem.lower()
    return stem in (final.table, snake_case(final.final))
