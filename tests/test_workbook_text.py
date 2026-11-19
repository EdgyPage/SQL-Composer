"""copilot/workbook_text.py, which writes an Excel workbook as text for a Copilot chat, its
pieces in the order each reads the others.

Toolbox 8.2's ticket 22. It reads a workbook as Excel saves it, with nothing but Python: each
Table, row by row, its formulas, and each Power Query's M, from the DataMashup Excel saves or
from a Power Query sheet. Since Toolbox 8.9 (ticket 01) the reading is the Toolbox's workbook
reader, sqlglot_composer/workbook_reader.py, which the script loads alone by its folder's path
(tests/test_workbook_reader.py); the script writes the same text of it. Its view of every
Excel evaluation task is the one openpyxl gives, so the evaluations measure the text the
script writes.
"""

from __future__ import annotations

import ast
import datetime
import io
import sys
import zipfile
from pathlib import Path

import openpyxl
import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "copilot"), str(ROOT / "tools")]

import workbook_fixtures  # noqa: E402
import workbook_text  # noqa: E402
from excel_eval_tasks import TASKS, ExcelTask, runs_table  # noqa: E402
from formula_workbook import FormulaWorkbook, as_text, openpyxl_text, saved  # noqa: E402
from pivot_tables import Pivot, Value  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "workbook_text"
ORDER = "Order, each piece after every piece it reads:\n"


def order_of(path: Path) -> list[str]:
    text = workbook_text.workbook_text(path)
    return [line.strip() for line in text.split(ORDER)[1].splitlines()]


# openpyxl reads no PivotTable, only the cells a pivot fills, so a pivot task's text has nothing
# of openpyxl's to match: the reader's tests (tests/test_workbook_pivots.py) and the pivot
# tasks' stored-values test (tests/test_excel_eval.py) hold it.
FORMULA_TASKS = [task for task in TASKS if not task.workbook.pivots]


@pytest.mark.parametrize("task", FORMULA_TASKS, ids=[task.id for task in FORMULA_TASKS])
def test_each_tasks_text_is_the_one_openpyxl_reads_its_queries_read_back(
        task: ExcelTask) -> None:
    # Its queries saved as Excel saves them, then read back from the DataMashup and the
    # connections: the same Tables, rows, cells, queries and names openpyxl reads.
    text = as_text(task.workbook)
    body = text.split(ORDER)[0]
    notes = "".join(f"{line}\n" for line in text.splitlines()
                    if line.startswith("Also in the workbook: "))
    assert body + notes == openpyxl_text(task.workbook)


def test_a_query_comes_before_its_table_and_the_table_before_the_formulas_reading_it() -> None:
    assert order_of(FIXTURES / "01_query_table_formula.xlsx") == [
        '1. Excel Table "Parameters"',
        '2. Excel Table "Keys"',
        '3. Excel Table "job_runs"',
        '4. Power Query "ok_runs", reads Excel Table "job_runs"',
        '5. Excel Table "ok_runs", loaded by Power Query "ok_runs"',
        '6. Excel Table "ok_by_job", its formulas read Excel Table "ok_runs"',
        "Each final's query reads the steps it needs as CTEs in this order, each CTE after "
        "every CTE it reads.",
    ]
    text = workbook_text.workbook_text(FIXTURES / "01_query_table_formula.xlsx")
    assert '  Excel Table "ok_runs", A1:C6, loaded by Power Query "ok_runs"' in text
    assert 'Power Query "ok_runs" (loads into Excel Table "ok_runs"):' in text
    assert "    Row 2: 1 | =SUMIFS(ok_runs[duration_mins],ok_runs[job_id],[@job_id])" in text


def test_a_query_comes_after_the_connection_only_query_it_reads() -> None:
    assert order_of(FIXTURES / "02_query_reads_query.xlsx")[4:7] == [
        '5. Power Query "staffed", reads Excel Table "jobs", Excel Table "job_owners"',
        '6. Power Query "owners_by_team", reads Power Query "staffed"',
        '7. Excel Table "owners_by_team", loaded by Power Query "owners_by_team"',
    ]
    text = workbook_text.workbook_text(FIXTURES / "02_query_reads_query.xlsx")
    assert 'Power Query "staffed" (connection only):' in text


def test_a_loop_is_refused_naming_each_link_in_excels_words() -> None:
    with pytest.raises(workbook_text.LoopError) as refused:
        workbook_text.workbook_text(FIXTURES / "03_loop.xlsx")
    assert str(refused.value).startswith(
        'Its pieces read each other in a loop: Power Query "back" reads Excel Table "looped"; '
        'Power Query "back" loads Excel Table "back"; Excel Table "looped"\'s formulas read '
        'Excel Table "back".\nWhy: ')


def test_each_fixture_and_its_text_is_what_the_builder_writes() -> None:
    for name, described in workbook_fixtures.FIXTURES.items():
        held = (FIXTURES / f"{name}.xlsx").read_bytes()
        built = workbook_fixtures.saved(described)
        assert workbook_fixtures.contents(held) == workbook_fixtures.contents(built), name
        assert ((FIXTURES / f"{name}.txt").read_text(encoding="utf-8")
                == workbook_fixtures.expected(held)), name


def test_each_pivot_is_written_with_its_fields_filters_totals_and_cells() -> None:
    # Toolbox 8.9, ticket 03: in place of "A PivotTable", each pivot as Copilot reads it.
    for name in workbook_fixtures.FIXTURES:
        assert "A PivotTable" not in (FIXTURES / f"{name}.txt").read_text(encoding="utf-8")
    text = workbook_text.workbook_text(FIXTURES / "05_pivot_slicer_two_pivots.xlsx")
    pivot = text.split('Sheet "Pivot"\n')[1].split('  PivotTable "runs_by_day"')[0]
    assert pivot.splitlines() == [
        '  PivotTable "PivotTable1", A3:B7',
        '    Source: Excel Table "job_runs"',
        "    Rows: job_id",
        '    Value "Sum of duration_mins": Sum of duration_mins',
        '    Slicer "status" on sheet "Pivot", field status: selected FAILED, SUCCESS; '
        "connected to PivotTable1, runs_by_day",
        "    Totals shown: Grand Total row",
        "    Cells: each value cell, what Excel last stored in it, then the Value it shows and "
        "the Rows and Columns items it stands for:",
        "      B4: 62 (Sum of duration_mins; Rows job_id 1)",
        "      B5: 38 (Sum of duration_mins; Rows job_id 2)",
        "      B6: 60 (Sum of duration_mins; Rows job_id 3)",
        "      B7: 160 (Sum of duration_mins; Rows Grand Total)"]
    # The slicer's defined name is the slicer's own, and the pivot's cells aren't the sheet's.
    assert "Defined name Slicer_status" not in text
    assert "  A3: Row Labels" not in text


def test_each_kind_of_pivot_line_in_excels_words() -> None:
    def text_of(name: str) -> str:
        return workbook_text.workbook_text(FIXTURES / f"{name}.xlsx")
    hours = text_of("06_pivot_query_sheet")
    assert "    Value Filter on job_id: Top 2 Items by Sum of hours\n" in hours
    assert '    Calculated Field "hours" = duration_mins/60\n' in hours
    groups = text_of("07_pivot_groups")
    # A date is written as its day, as Excel shows it, with no time of day.
    assert ('    Field "Years" groups dt By Years, Starting at 2026-09-23, Ending at '
            "2026-09-25\n") in groups
    assert ('    Field "duration_mins" groups duration_mins By 10, Starting at 0, Ending at '
            "49\n") in groups
    assert ("    Totals shown: Grand Total row, Grand Total column, subtotals of Years\n"
            in groups)
    assert ("      C5: 55 (Sum of duration_mins; Rows Years 2026; Columns duration_mins "
            "10-19)\n") in groups
    filtered = text_of("08_pivot_timeline_filters")
    assert ('    Value "Sum of duration_mins": Sum of duration_mins, Show Values As % of '
            "Column Total\n") in filtered
    assert "    Filter avg_retry_secs: (All)\n    Items hidden on status: TEST\n" in filtered
    # One day once, where the Timeline's first and last day are the same.
    assert ('    Timeline "dt" on sheet "Pivot", field dt: selected 2026-09-24; connected to '
            "PivotTable1\n") in filtered
    assert "      B5: empty (Sum of duration_mins; Rows job_id 1; Columns status FAILED)\n" in (
        filtered)
    # A Value shown as a % gives the percentage Excel shows beside the number it stores.
    assert ("      C5: 0.625 (62.50%; Sum of duration_mins; Rows job_id 1; Columns status "
            "SUCCESS)\n") in filtered
    ranged = text_of("09_pivot_plain_range")
    assert ("    Source: the range Runs!A1:F10, read as the Table it would be: run_id | job_id "
            "| status | duration_mins | avg_retry_secs | dt\n") in ranged
    assert "    Columns: Values\n    Value \"Count of run_id\": Count of run_id\n" in ranged
    assert "    Totals shown: none\n" in ranged
    ranked = text_of("10_pivot_calculated_item_rank")
    assert '    Calculated Item "done" on status = SUCCESS+FAILED\n' in ranked
    assert ('    Value "Sum of duration_mins": Sum of duration_mins, Show Values As Rank '
            "Largest to Smallest, Base field job_id\n") in ranked
    assert "    Filter status: SUCCESS\n" in ranked
    assert "      B8: 160 (Sum of duration_mins; Rows status done)\n" in ranked


def test_a_pivot_in_the_order_after_its_source_and_before_getpivotdata() -> None:
    assert order_of(FIXTURES / "06_pivot_query_sheet.xlsx")[3:7] == [
        '4. Power Query "ok_runs", reads Excel Table "job_runs"',
        '5. Excel Table "ok_runs", loaded by Power Query "ok_runs"',
        '6. PivotTable "PivotTable1", reads Excel Table "ok_runs"',
        '7. Excel Table "job_hours", its formulas read PivotTable "PivotTable1"']
    assert order_of(FIXTURES / "09_pivot_plain_range.xlsx")[2:4] == [
        '3. Range "Runs!A1:F10"', '4. PivotTable "PivotTable1", reads Range "Runs!A1:F10"']


def test_a_data_model_pivot_says_its_model_and_what_loads_it() -> None:
    described = FormulaWorkbook((runs_table(),), pivots=(
        Pivot("job_runs", ("dt",), (Value("job_id", "distinctCount"),), data_model=True),))
    text = workbook_text.workbook_text(saved(described))
    assert ('    Source: the Data Model, its tables job_runs, loaded from Excel Table '
            '"job_runs"\n') in text
    assert '    Value "Distinct Count of job_id": Distinct Count of job_id\n' in text
    assert '  4. PivotTable "PivotTable1", reads Excel Table "job_runs"\n' in text


def test_a_power_query_sheet_gives_each_query_loading_the_table_of_its_name() -> None:
    text = workbook_text.workbook_text(ROOT / "copilot" / "examples" / "03_power_query.xlsx")
    assert 'Power Query "ok_runs" (loads into Excel Table "ok_runs"):' in text
    assert '  Excel Table "ok_by_job", A1:B4, loaded by Power Query "ok_by_job"' in text
    assert "Query ok_runs:" not in text
    assert text.split(ORDER)[1].splitlines()[-3:-1] == [
        '  6. Power Query "ok_by_job", reads Power Query "ok_runs"',
        '  7. Excel Table "ok_by_job", loaded by Power Query "ok_by_job"']


def test_a_date_shows_as_openpyxl_shows_it_and_a_formula_as_typed() -> None:
    book = openpyxl.Workbook()
    book.active.title = "Data"
    book.active["A1"] = datetime.datetime(2026, 9, 24)
    book.active["A2"] = "=_xlfn.XLOOKUP(t[[#This Row],[job_id]],j[job_id],j[name])"
    held = io.BytesIO()
    book.save(held)
    text = workbook_text.workbook_text(held.getvalue())
    assert "  A1: 2026-09-24 00:00:00\n" in text
    assert "  A2: =XLOOKUP([@job_id],j[job_id],j[name])\n" in text


def test_the_script_writes_each_text_beside_its_workbook_and_refuses_what_it_cant(
        tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    workbook = tmp_path / "costs.xlsx"
    workbook.write_bytes((FIXTURES / "01_query_table_formula.xlsx").read_bytes())
    assert workbook_text.main([str(workbook)]) == 0
    assert (tmp_path / "costs.txt").read_text(encoding="utf-8") == (
        FIXTURES / "01_query_table_formula.txt").read_text(encoding="utf-8")
    loop = tmp_path / "loop.xlsx"
    loop.write_bytes((FIXTURES / "03_loop.xlsx").read_bytes())
    (tmp_path / "not.xlsx").write_text("a,b\n", encoding="utf-8")
    assert workbook_text.main([str(loop), str(tmp_path / "not.xlsx")]) == 1
    assert not (tmp_path / "loop.txt").exists()
    said = capsys.readouterr().err
    assert "loop.xlsx: nothing was written. Its pieces read each other in a loop" in said
    assert "not.xlsx can't be read as an Excel workbook (.xlsx)." in said
    assert workbook_text.main([]) == 2


def imported_by(path: Path) -> set[str]:
    """Each module a file imports by name, by its first part."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imported = {alias.name.split(".")[0] for node in ast.walk(tree)
                if isinstance(node, ast.Import) for alias in node.names}
    return imported | {node.module.split(".")[0] for node in ast.walk(tree)
                       if isinstance(node, ast.ImportFrom) and node.module}


def test_the_script_imports_nothing_but_pythons_own_modules_and_the_reader() -> None:
    # Main ships it for people with nothing installed beside Python. The reader is loaded
    # alone from the Toolbox's folder, and imports Python's own modules alone, none relatively
    # (tests/repo/test_toolbox_checks.py holds that).
    imported = imported_by(ROOT / "copilot" / "workbook_text.py")
    assert imported - {"__future__"} <= set(sys.stdlib_module_names) | {"workbook_reader"}
    reader = imported_by(ROOT / "sqlglot_composer" / "workbook_reader.py")
    assert reader - {"__future__"} <= set(sys.stdlib_module_names)
    assert Path(workbook_text.workbook_reader.__file__).resolve() == (
        ROOT / "sqlglot_composer" / "workbook_reader.py")
    assert str(ROOT / "sqlglot_composer") not in sys.path


def test_the_script_copied_without_the_toolbox_beside_it_says_where_the_reader_is(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "copilot").mkdir()
    (tmp_path / "copilot" / "workbook_text.py").write_bytes(
        (ROOT / "copilot" / "workbook_text.py").read_bytes())
    monkeypatch.delitem(sys.modules, "workbook_text")
    monkeypatch.delitem(sys.modules, "workbook_reader")
    monkeypatch.syspath_prepend(str(tmp_path / "copilot"))
    with pytest.raises(SystemExit) as stopped:
        import workbook_text  # noqa: F401
    assert str(stopped.value).startswith(
        "workbook_text.py can't find the workbook reader, sqlglot_composer/workbook_reader.py."
        "\nWhy: ")
    assert f"looks for in {tmp_path.resolve() / 'sqlglot_composer'}.\n" in str(stopped.value)
    assert str(tmp_path / "sqlglot_composer") not in sys.path


def test_each_part_the_builder_adds_is_a_part_excel_saves_for_a_query() -> None:
    with zipfile.ZipFile(FIXTURES / "01_query_table_formula.xlsx") as parts:
        names = set(parts.namelist())
        types = parts.read("[Content_Types].xml").decode("utf-8")
    assert {"customXml/item1.xml", "customXml/itemProps1.xml", "xl/connections.xml",
            "xl/queryTables/queryTable1.xml"} <= names
    assert 'PartName="/xl/queryTables/queryTable1.xml"' in types
