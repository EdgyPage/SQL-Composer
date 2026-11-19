"""A Formula workbook given to a Conversion (Toolbox 8.9, ticket 07; ADR 0016).

`project.convert(..., files=["runs.xlsx"])` reads a workbook beside any `.hql` scripts.
`converted_workbook` gives what the Conversion needs of it: each final's Hive, as
`workbook_hive.py` writes it with the batch's database filled in, under the name of the Saved
table it becomes; what the workbook's map names of each final, in plain words, for that
table's checklist; what it names of no one final, for batch.md; and each Pivot filter of
each final, for its Decision (ticket 08). The Conversion then keeps each final's Hive in the
batch's scripts/, as it keeps Hive given as text, and converts it as it converts any batch's.

A final's table is named for it: a Table's name, or a pivot's (PN1), in snake case. Some names
are proposed, the table made under the proposal until the person names it otherwise: a pivot
keeping Excel's default name, `<sheet name>_pivot` (PN2); and a final named as a database
table the batch reads, as a Table with formula columns over its own rows is, `<name>_report`.
`rename=`, by the final's name in the workbook, names one otherwise. A total level or a Total
Row is named for its pivot's or its Table's table, `pivot_pivot_grand_total`.
"""

from __future__ import annotations

import datetime
import re
import zipfile
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import NoReturn

from .refusals import refuse
from .shared import in_words, python_literal
from .workbook_formulas import (
    LEFT_ALONE,
    MARK,
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
)
from .workbook_reader import (
    EXCEL_TABLE,
    PIVOT_TABLE,
    LoopError,
    Piece,
    Workbook,
    read_workbook,
)

# The files a Conversion reads as a workbook, by their ending; an .xls, Excel's older kind, it
# can't read.
WORKBOOK_SUFFIXES = (".xlsx", ".xlsm")
OLD_WORKBOOK = ".xls"
# What a final's name is proposed with, where it is named as a database table the batch reads.
REPORT = "_report"
# A Saved table's name a person gives a final: lowercase letters, digits and _.
PLAIN_TABLE_NAME = re.compile(r"[a-z][a-z0-9_]*")
# How a batch's written.json keeps a Pivot filter's date and time, and its date.
TIME_KEPT = "time"
DAY_KEPT = "day"
# What each kind of the map's notes is, as a checklist says it, in file 15's Output's words.
NOTE_WORDS = {WRITTEN_IN: "written in", TYPED_OVER: "typed over a formula", MARK: "marked",
              REFUSED: "refused", LEFT_ALONE: "left alone", TO_FILL_IN: "to fill in"}
# A note's place, such as `Power Query "ok_runs"`, and its column after it, such as `[hours]`.
_PLACE_NAMED = re.compile(r'[A-Za-z ]+ "(?P<name>.*)"')
_COLUMN_AFTER = re.compile(r"\[[^\]]*\]$")


@dataclass
class WorkbookFinal:
    """One final of a workbook, as a Conversion takes it: its name in the workbook, such as
    `PivotTable1`; the Saved table it becomes, its plain lowercase name, which its script is
    named for; its Hive; why that name was proposed, "" where it is the final's own; each line
    of the workbook's map about it, for its table's checklist; each `<...>` its Hive still
    holds, which stops it converting; each Pivot filter its rows go through, its `final` the
    workbook's name of the pivot it is in; and its workbook's file's name."""

    final: str
    table: str
    hive: str
    proposed: str = ""
    notes: list[str] = field(default_factory=list)
    to_fill_in: list[str] = field(default_factory=list)
    filters: list[ConvertedPivotFilter] = field(default_factory=list)
    workbook: str = ""

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


def is_workbook(file: str) -> bool:
    """Whether a file a Conversion is given is a workbook, by its ending."""
    return Path(file).suffix.lower() in WORKBOOK_SUFFIXES


def converted_workbook(call: str, path: Path, database: str,
                       rename: dict[str, str]) -> ConvertedWorkbook:
    """A workbook as a Conversion takes it, its sources in `database`, each final named as
    `rename` names it, by its name in the workbook, or else for itself, as the module
    docstring says. Refused for a file that isn't a workbook the reader reads, such as one
    whose pieces read each other in a loop, and for a workbook with no final."""
    workbook = _workbook_read(call, path)
    hive = workbook_hive(workbook, database=database)
    if not hive.finals:
        _refuse_nothing_to_convert(call, path.name, hive)
    texts = hive_texts(hive)
    _check_names_given(call, path.name, rename, list(texts))
    names = final_table_names(workbook, hive, rename)
    owned, of_no_final = _notes_by_final(workbook, hive)
    filters = pivot_filters(workbook)
    finals = []
    for final, text in texts.items():
        table, proposed = names[final]
        notes = [name_note(final, table, proposed)] if proposed else []
        notes += [note_said(note) for note in owned[final] if note.rule != "PN2"]
        reads = _pieces_a_final_reads(final, workbook)
        to_fill_in = [note.where for note in owned[final] if note.kind == TO_FILL_IN]
        finals.append(WorkbookFinal(final, table, text, proposed, notes, to_fill_in,
                                    [each for each in filters if each.final.lower() in reads],
                                    path.name))
    return ConvertedWorkbook(path.name, finals, [note_said(note) for note in of_no_final])


def every_final(workbooks: list[ConvertedWorkbook]) -> list[WorkbookFinal]:
    """Each final of each workbook, in order."""
    finals = []
    for workbook in workbooks:
        finals += workbook.finals
    return finals


def _workbook_read(call: str, path: Path) -> Workbook:
    """The workbook at `path`, read; refused where it can't be: a file that isn't a workbook,
    or one whose pieces read each other in a loop."""
    try:
        return read_workbook(path)
    except LoopError as loop:
        what, why, fix = str(loop).split("\n")
        refuse(what=f"{call}: {path.name}: {what}", why=why.removeprefix("Why: "),
               fix=fix.removeprefix("Usual fix: "), error=ValueError)
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
           why="A Conversion makes each final of a workbook, a calculation nothing else in it "
           "reads, a Saved table; a Table of typed values alone stands for a database table "
           "already, so it makes none.",
           fix="Put the calculation in the workbook, as a formula column in a Table, a Power "
           "Query loading a Table, or a PivotTable, save it, and convert it again.",
           error=ValueError)


# --- Each final's table's name --------------------------------------------------------------


def final_table_names(workbook: Workbook, hive: WorkbookHive,
                      rename: dict[str, str]) -> dict[str, tuple[str, str]]:
    """Each final's table's name, by the final's name in the workbook, with why it was
    proposed, "" where it is the final's own or `rename` gives it: as the module docstring
    says, a number after a name two finals would share."""
    read = _database_tables_read(workbook, hive)
    pivots = pivot_table_names(workbook)
    names: dict[str, tuple[str, str]] = {}
    for final in hive.finals:
        base, _, level = final.partition(" (")
        name, why = _own_name(base, workbook, pivots, read)
        # A total level or a Total Row is named for its pivot's or its Table's table, as
        # rename= names it too, unless rename= names the level itself.
        if base in rename:
            name, why = rename[base], ""
        if level:
            name, why = f"{name}_{snake_case(level)}", ""
        if final in rename:
            name, why = rename[final], ""
        names[final] = (_free_name(name, [each for each, _ in names.values()]), why)
    return names


def _check_names_given(call: str, file: str, rename: dict[str, str],
                       finals: list[str]) -> None:
    """Refuse a name rename= gives a workbook's final that isn't a plain lowercase name, as
    its Saved table's is."""
    for final in finals:
        name = rename.get(final)
        if name is None or (isinstance(name, str) and PLAIN_TABLE_NAME.fullmatch(name)):
            continue
        refuse(what=f"{call} was given rename={{{python_literal(final)}: "
               f"{python_literal(name)}}} for {final} of {file}, which isn't a plain lowercase "
               "name.",
               why="A workbook's final becomes a Saved table in your Dev Database, named as "
               "rename= names it, and its script in the batch's scripts/ too.",
               fix='Use lowercase letters, digits and _, starting with a letter, such as '
               '"runs_by_job".', error=ValueError)


def _own_name(final: str, workbook: Workbook, pivots: dict[str, str],
              read: set[str]) -> tuple[str, str]:
    """A Table's or a pivot's own final's table's name, and why it was proposed, "" where it is
    its own."""
    if final in pivots:
        pivot = pivot_of(Piece(PIVOT_TABLE, final), workbook)
        if DEFAULT_NAME.fullmatch(pivot.name):
            return pivots[final], (f"{pivot.name} is Excel's default name, so it is named "
                                   f"for its sheet, {pivot.sheet}")
        return pivots[final], ""
    name = snake_case(final)
    if name in read:
        return name + REPORT, (f"{final} is the name of a table in the database it reads, "
                               "which a Saved table of yours can't share")
    return name, ""


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
        if (piece.kind == EXCEL_TABLE and role != SETTINGS and PLAIN_NAME.fullmatch(piece.name)
                and is_read_from_the_database(piece.name, workbook)):
            read.add(piece.name.lower())
    return read


def is_read_from_the_database(table: str, workbook: Workbook) -> bool:
    """Whether a Table's rows are its database table's: not a summary's, nor a query's."""
    found = tables_of(workbook)[table.lower()]
    return not found.loaded_by and not is_summary(found)


def name_note(final: str, table: str, why: str) -> str:
    """A table's checklist note saying its name was proposed, and how to name it otherwise."""
    return (f"Its name, {table}, is proposed: {why}. If you want another, give it in RENAME in "
            "the convert notebook's names cell, by the name the workbook gives it, such as "
            f"RENAME = {{{python_literal(final)}: \"<a name>\"}}, and convert again: the table "
            f"made as {table} stays until project.remove_table removes it.")


# --- What the map names, table by table -----------------------------------------------------


def note_said(note: Note) -> str:
    """One line of the workbook's map in plain words, as a checklist or batch.md lists it."""
    return (f"From the workbook, {NOTE_WORDS[note.kind]} (rule {note.rule}): {note.where}: "
            f"{note.text}.")


def _notes_by_final(workbook: Workbook,
                    hive: WorkbookHive) -> tuple[dict[str, list[Note]], list[Note]]:
    """Each line of the workbook's map, by each final it is about: one about a piece the final
    is, or reads at any depth, or, for a `<...>` to fill in, one its Hive holds; and the lines
    about no one final, such as a chart left alone, or a pivot refused, with no final."""
    texts = hive_texts(hive)
    owned: dict[str, list[Note]] = {final: [] for final in hive.finals}
    of_no_final = []
    for note in hive.notes:
        if note.kind == TO_FILL_IN:
            owners = [final for final, text in texts.items() if note.where in text]
        else:
            named = _named_in(note.where)
            owners = [final for final in hive.finals
                      if named in _pieces_a_final_reads(final, workbook) | {final.lower()}]
        for final in owners:
            owned[final].append(note)
        if not owners and not (note.kind == TO_FILL_IN and note.where == DATABASE):
            of_no_final.append(note)
    return owned, of_no_final


def _named_in(where: str) -> str:
    """The piece a note's place names, in lower case: `job_runs` of `job_runs[hours]`, and
    `ok_runs` of `Power Query "ok_runs"`."""
    piece = _COLUMN_AFTER.sub("", where)
    found = _PLACE_NAMED.fullmatch(piece)
    if found:
        piece = found["name"]
    return piece.lower()


def _pieces_a_final_reads(final: str, workbook: Workbook) -> set[str]:
    """The name, in lower case, of the piece a final is, a total level's or a Total Row's its
    pivot's or its Table's, and of every piece it reads, at any depth."""
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
    return {piece.name.lower() for piece in found}


def pivot_filter_record(written: ConvertedPivotFilter) -> dict[str, object]:
    """A Pivot filter as a batch's written.json keeps it: each field of its record, each of
    its values as `json_value` writes it, as JSON holds no date."""
    record = asdict(written)
    for name in ("values", "field_values"):
        record[name] = [json_value(value) for value in record[name]]
    return record


def pivot_filter_of_record(record: dict[str, object]) -> ConvertedPivotFilter:
    """A Pivot filter read back from a batch's written.json, as `pivot_filter_record` kept it,
    each date and time as it was."""
    values = tuple(value_of_json(value) for value in record["values"])
    field_values = tuple(value_of_json(value) for value in record["field_values"])
    return ConvertedPivotFilter(str(record["final"]), str(record["kind"]),
                                str(record["field"]), values, field_values,
                                str(record["ranked_by"]), bool(record["bottom"]))


def json_value(value: object) -> object:
    """A value as JSON holds it: a date and time as {"time": its ISO text}, a date as {"day":
    its ISO text}, any other as it is."""
    if isinstance(value, datetime.datetime):
        return {TIME_KEPT: value.isoformat()}
    if isinstance(value, datetime.date):
        return {DAY_KEPT: value.isoformat()}
    return value


def value_of_json(value: object) -> object:
    """A value `json_value` wrote, as it was."""
    if isinstance(value, dict) and TIME_KEPT in value:
        return datetime.datetime.fromisoformat(value[TIME_KEPT])
    if isinstance(value, dict) and DAY_KEPT in value:
        return datetime.date.fromisoformat(value[DAY_KEPT])
    return value


def filters_of(final: WorkbookFinal, table: str) -> list[ConvertedPivotFilter]:
    """Each Pivot filter a final's rows go through, as the Hive of the table it became writes
    it, its `final` that table's name, as the Copilot path's Hive gives it."""
    return [replace(each, final=table) for each in final.filters]


def to_fill_in_said(final: WorkbookFinal) -> str:
    """Why a final whose Hive holds a `<...>` isn't converted, as convert's report says it."""
    return (f"its Hive holds {in_words(final.to_fill_in)}, a name to fill in: name the Table "
            "or the range in the workbook as its table is named in the database, as an Excel "
            "Table, and convert again, or fill each in the Hive kept in scripts/, "
            f"{final.script}, and convert that file")
