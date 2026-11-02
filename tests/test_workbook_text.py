"""copilot/workbook_text.py, which writes an Excel workbook as text for a Copilot chat, its
pieces in the order each reads the others.

Toolbox 8.2's ticket 22. It reads a workbook as Excel saves it, with nothing but Python: each
Table, row by row, its formulas, and each Power Query's M, from the DataMashup Excel saves or
from a Power Query sheet. Its view of every Excel evaluation task is the one openpyxl gives,
so the evaluations measure the text the script writes.
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
from excel_eval_tasks import TASKS, ExcelTask  # noqa: E402
from formula_workbook import as_text, openpyxl_text  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures" / "workbook_text"
ORDER = "Order, each piece after every piece it reads:\n"


def order_of(path: Path) -> list[str]:
    text = workbook_text.workbook_text(path)
    return [line.strip() for line in text.split(ORDER)[1].splitlines()]


@pytest.mark.parametrize("task", TASKS, ids=[task.id for task in TASKS])
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


def test_a_power_query_sheet_gives_each_query_loading_the_table_of_its_name() -> None:
    text = workbook_text.workbook_text(ROOT / "copilot" / "examples" / "03_power_query.xlsx")
    assert 'Power Query "ok_runs" (loads into Excel Table "ok_runs"):' in text
    assert '  Excel Table "ok_by_job", A1:B4, loaded by Power Query "ok_by_job"' in text
    assert "Query ok_runs:" not in text
    assert text.split(ORDER)[1].splitlines()[-3:-1] == [
        '  6. Power Query "ok_by_job", reads Power Query "ok_runs"',
        '  7. Excel Table "ok_by_job", loaded by Power Query "ok_by_job"']


def test_a_section_documents_queries_are_read_past_strings_comments_and_quoted_names() -> None:
    m = ('section Section1;\r\n\r\nshared #"Jobs; kept" = let\r\n    // a ; in a comment\r\n'
         '    Source = "a;b" & "say ""hi"";",\r\n    /* and ; here */ Kept = Source\r\n'
         'in\r\n    Kept;\r\n\r\nshared plain = #"Jobs; kept";')
    assert workbook_text.section_queries(m) == [
        ("Jobs; kept", 'let\r\n    // a ; in a comment\r\n    Source = "a;b" & "say ""hi"";",'
                       "\r\n    /* and ; here */ Kept = Source\r\nin\r\n    Kept"),
        ("plain", '#"Jobs; kept"')]


def test_a_shared_formulas_later_cells_move_each_reference_not_held_with_a_dollar() -> None:
    assert workbook_text._shifted("A2*$B$1+C$3+$D4", 2, 1) == "B4*$B$1+D$3+$D6"
    assert workbook_text._shifted("SUMIFS(t[a],t[b],[@b])", 3, 0) == "SUMIFS(t[a],t[b],[@b])"


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


def test_the_script_imports_nothing_but_pythons_own_modules() -> None:
    # Main ships it for people with nothing installed beside Python.
    tree = ast.parse((ROOT / "copilot" / "workbook_text.py").read_text(encoding="utf-8"))
    imported = {alias.name.split(".")[0] for node in ast.walk(tree)
                if isinstance(node, ast.Import) for alias in node.names}
    imported |= {node.module.split(".")[0] for node in ast.walk(tree)
                 if isinstance(node, ast.ImportFrom) and node.module}
    assert imported - {"__future__"} <= set(sys.stdlib_module_names)


def test_each_part_the_builder_adds_is_a_part_excel_saves_for_a_query() -> None:
    with zipfile.ZipFile(FIXTURES / "01_query_table_formula.xlsx") as parts:
        names = set(parts.namelist())
        types = parts.read("[Content_Types].xml").decode("utf-8")
    assert {"customXml/item1.xml", "customXml/itemProps1.xml", "xl/connections.xml",
            "xl/queryTables/queryTable1.xml"} <= names
    assert 'PartName="/xl/queryTables/queryTable1.xml"' in types
