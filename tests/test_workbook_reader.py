"""sqlglot_composer/workbook_reader.py, the one reader of an Excel workbook (Toolbox 8.9,
ticket 01; ADR 0016).

It reads a workbook as Excel saves it, with nothing but Python, and gives back data: each
sheet's Excel Tables, each column typed or a formula column, with its Total Row's cell; the
sheet's other cells; the defined names; each Power Query's M, from the DataMashup Excel saves or
from a Power Query sheet; and the Order, each piece after every piece it reads, a loop refused.
`copilot/workbook_text.py` writes its text from that data (tests/test_workbook_text.py).
"""

from __future__ import annotations

import datetime
import io
from pathlib import Path

import openpyxl
import pytest
from openpyxl.worksheet.table import Table as OpenpyxlTable

from sqlglot_composer import workbook_reader
from sqlglot_composer.workbook_reader import Column, Piece, Query, Table, Workbook

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "tests" / "fixtures" / "workbook_text"
PARAMETERS = Piece("Excel Table", "Parameters")
KEYS = Piece("Excel Table", "Keys")


def read(name: str) -> Workbook:
    return workbook_reader.read_workbook(FIXTURES / f"{name}.xlsx")


def tables_of(workbook: Workbook) -> dict[str, Table]:
    """Each Table of the workbook, by its name."""
    found = {}
    for sheet in workbook.sheets:
        for table in sheet.tables:
            found[table.name] = table
    return found


def columns_of(table: Table) -> list[tuple[str, str]]:
    """Each column of a Table as its header and its kind."""
    return [(column.header, column.kind) for column in table.columns]


def row_of(table: Table, number: int) -> list[object]:
    """The cells of a Table's row `number`, counting its first row below the headers as 0."""
    return [column.cells[number] for column in table.columns]


def test_the_first_fixtures_sheets_tables_and_their_columns() -> None:
    workbook = read("01_query_table_formula")
    assert [sheet.title for sheet in workbook.sheets] == [
        "Steps", "Parameters", "Keys", "job_runs", "ok_runs", "ok_by_job"]
    tables = tables_of(workbook)
    assert list(tables) == ["Parameters", "Keys", "job_runs", "ok_runs", "ok_by_job"]
    runs = tables["job_runs"]
    assert (runs.ref, runs.loaded_by, runs.has_total_row) == ("A1:F10", "", False)
    assert columns_of(runs) == [
        ("run_id", "typed"), ("job_id", "typed"), ("status", "typed"),
        ("duration_mins", "typed"), ("avg_retry_secs", "typed"), ("dt", "typed")]
    assert row_of(runs, 0) == [95, 1, "SUCCESS", 12, 2, "2026-09-23"]
    assert row_of(runs, 3) == [98, 2, None, 15, None, "2026-09-23"]
    assert [len(column.cells) for column in runs.columns] == [9] * 6
    assert [column.total for column in runs.columns] == [None] * 6
    ok_runs = tables["ok_runs"]
    assert (ok_runs.ref, ok_runs.loaded_by) == ("A1:C6", "ok_runs")
    assert ok_runs.columns[0].cells == [95, 96, 101, 103, 104]
    by_job = tables["ok_by_job"]
    assert columns_of(by_job) == [("job_id", "typed"), ("ok_mins", "formula")]
    assert by_job.columns[0].cells == [1, 2, 3]
    # A formula as the workbook saves it, the row it is on as [#This Row].
    assert by_job.columns[1].cells == [
        "=SUMIFS(ok_runs[duration_mins],ok_runs[job_id],"
        "ok_by_job[[#This Row],[job_id]])"] * 3
    assert tables["Parameters"].columns == [Column("name", "typed", [None]),
                                            Column("value", "typed", [None])]


def test_the_first_fixtures_other_cells_query_names_and_order() -> None:
    workbook = read("01_query_table_formula")
    sheets = {sheet.title: sheet for sheet in workbook.sheets}
    assert list(sheets["Parameters"].cells) == [(1, 4)]
    assert sheets["Parameters"].cells[(1, 4)].startswith("Parameters: the fixed values")
    assert sheets["Steps"].cells[(1, 1)] == "Formula workbook: how to fill it in"
    assert [(sheet.charts, sheet.pivot_tables) for sheet in workbook.sheets] == [([], 0)] * 6
    assert workbook.defined_names == {}
    assert workbook.queries == [Query("ok_runs", (
        'let\n    Source = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],\n'
        '    Ok = Table.SelectRows(Source, each [status] = "SUCCESS"),\n'
        '    Kept = Table.SelectColumns(Ok, {"run_id", "job_id", "duration_mins"})\n'
        "in\n    Kept"), loads="ok_runs")]
    runs, query = Piece("Excel Table", "job_runs"), Piece("Power Query", "ok_runs")
    assert workbook.order == {
        PARAMETERS: [], KEYS: [], runs: [], query: [runs],
        Piece("Excel Table", "ok_runs"): [query],
        Piece("Excel Table", "ok_by_job"): [Piece("Excel Table", "ok_runs")]}


def test_the_second_fixtures_connection_only_query_and_the_query_reading_it() -> None:
    workbook = read("02_query_reads_query")
    tables = tables_of(workbook)
    assert list(tables) == ["Parameters", "Keys", "jobs", "job_owners", "owners_by_team"]
    owners = tables["job_owners"]
    assert (owners.ref, len(owners.columns[0].cells)) == ("A1:D57", 56)
    assert row_of(owners, 3) == [4, "web", None, "2026-09-11"]
    assert row_of(owners, 54) == [3, "finance", "chloe", "2026-09-24"]
    assert row_of(owners, 55) == [4, "web", None, "2026-09-24"]
    assert columns_of(tables["jobs"]) == [("job_id", "typed"), ("job_name", "typed"),
                                          ("team", "typed"), ("region", "typed")]
    by_team = tables["owners_by_team"]
    assert (by_team.loaded_by, by_team.columns[1].cells) == (
        "owners_by_team", ["ana", "ana", "ben", "chloe", None])
    assert [(query.name, query.loads) for query in workbook.queries] == [
        ("staffed", ""), ("owners_by_team", "owners_by_team")]
    assert workbook.queries[1].m == (
        'let\n    Source = staffed,\n'
        '    Kept = Table.Distinct(Table.SelectColumns(Source, {"team", "owner"}))\n'
        "in\n    Kept")
    jobs, job_owners = Piece("Excel Table", "jobs"), Piece("Excel Table", "job_owners")
    staffed = Piece("Power Query", "staffed")
    loading = Piece("Power Query", "owners_by_team")
    assert workbook.order == {
        PARAMETERS: [], KEYS: [], jobs: [], job_owners: [], staffed: [jobs, job_owners],
        loading: [staffed], Piece("Excel Table", "owners_by_team"): [loading]}


def test_a_loop_is_refused_naming_each_link_in_excels_words() -> None:
    with pytest.raises(workbook_reader.LoopError) as refused:
        read("03_loop")
    assert str(refused.value) == (
        'Its pieces read each other in a loop: Power Query "back" reads Excel Table "looped"; '
        'Power Query "back" loads Excel Table "back"; Excel Table "looped"\'s formulas read '
        'Excel Table "back".\n'
        "Why: each piece must come after every piece it reads, and in a loop none can, so no "
        "Hive gives the same rows.\n"
        "Usual fix: in Excel, break one of these links, such as a query reading the raw data's "
        "Table in place of a Table in the loop; save the workbook, and run this again.")


def test_a_power_query_sheet_gives_each_query_loading_the_table_of_its_name() -> None:
    workbook = workbook_reader.read_workbook(
        ROOT / "copilot" / "examples" / "03_power_query.xlsx")
    tables = tables_of(workbook)
    assert [(query.name, query.loads) for query in workbook.queries] == [
        ("ok_runs", "ok_runs"), ("ok_by_job", "ok_by_job")]
    assert tables["ok_by_job"].loaded_by == "ok_by_job"
    assert all("Query ok_runs:" not in sheet.cells.values() for sheet in workbook.sheets)


def test_a_total_row_gives_each_columns_last_cell_and_a_formula_column_is_one() -> None:
    book = openpyxl.Workbook()
    sheet = book.active
    sheet.title = "sales"
    for row in (("region", "sales", "doubled"), ("East", 10, "=[@sales]*2"),
                ("West", 5.5, 4), ("Total", "=SUBTOTAL(109,[sales])", None)):
        sheet.append(row)
    sheet["A6"] = datetime.datetime(2026, 9, 24)
    sheet.add_table(OpenpyxlTable(displayName="sales", ref="A1:C4", totalsRowCount=1))
    book.defined_names["tax_rate"] = openpyxl.workbook.defined_name.DefinedName(
        "tax_rate", attr_text="0.2")
    held = io.BytesIO()
    book.save(held)
    workbook = workbook_reader.read_workbook(held.getvalue())
    table = workbook.sheets[0].tables[0]
    assert table.has_total_row
    # A value typed over a formula keeps the column a formula column.
    assert table.columns == [
        Column("region", "typed", ["East", "West"], "Total"),
        Column("sales", "typed", [10, 5.5], "=SUBTOTAL(109,[sales])"),
        Column("doubled", "formula", ["=[@sales]*2", 4], None)]
    assert workbook.sheets[0].cells == {(6, 1): datetime.datetime(2026, 9, 24)}
    assert workbook.defined_names == {"tax_rate": "0.2"}
    assert workbook.order == {Piece("Excel Table", "sales"): []}


def test_a_section_documents_queries_are_read_past_strings_comments_and_quoted_names() -> None:
    m = ('section Section1;\r\n\r\nshared #"Jobs; kept" = let\r\n    // a ; in a comment\r\n'
         '    Source = "a;b" & "say ""hi"";",\r\n    /* and ; here */ Kept = Source\r\n'
         'in\r\n    Kept;\r\n\r\nshared plain = #"Jobs; kept";')
    assert workbook_reader.section_queries(m) == [
        ("Jobs; kept", 'let\r\n    // a ; in a comment\r\n    Source = "a;b" & "say ""hi"";",'
                       "\r\n    /* and ; here */ Kept = Source\r\nin\r\n    Kept"),
        ("plain", '#"Jobs; kept"')]


def test_a_shared_formulas_later_cells_move_each_reference_not_held_with_a_dollar() -> None:
    assert workbook_reader.shifted_formula("A2*$B$1+C$3+$D4", 2, 1) == "B4*$B$1+D$3+$D6"
    assert (workbook_reader.shifted_formula("SUMIFS(t[a],t[b],[@b])", 3, 0)
            == "SUMIFS(t[a],t[b],[@b])")


def test_a_cells_coordinate_and_a_pieces_name() -> None:
    assert [workbook_reader.coordinate(2, 3), workbook_reader.coordinate(10, 28)] == [
        "C2", "AB10"]
    assert workbook_reader.piece_name(Piece("Excel Table", "job_runs")) == (
        'Excel Table "job_runs"')
