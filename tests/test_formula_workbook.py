"""The empty Formula workbook, `copilot/formula_workbook.xlsx` (Toolbox 7.2, ticket 15), and the
examples of it filled in, `copilot/examples/`, each with the Hive it converts to.

main can't rebuild it: tools/formula_workbook.py builds it with openpyxl, which only dev
installs, and the export copies the file. It holds a sheet of steps and two empty Excel Tables,
Parameters and Keys, and nothing a person could half-edit: no data Table, no formula, no row.
The offline policy and the code audit read it as they read the repo (tests/repo/).
"""

from __future__ import annotations

import openpyxl
import pytest

import excel_eval
import formula_workbook
import formula_workbook_examples
from test_copilot_files import AVOIDED

EMPTY = formula_workbook.EMPTY
# The glossary's words to avoid for a Formula workbook.
NOT_ITS_NAME = ("state table", "Excel template", "mapping sheet")


@pytest.fixture(scope="module")
def committed() -> openpyxl.Workbook:
    return openpyxl.load_workbook(EMPTY)


def test_it_is_what_the_tool_builds(committed: openpyxl.Workbook) -> None:
    # Compared by what a person sees, not by bytes: a zip's times change with every build.
    assert formula_workbook.contents(committed) == formula_workbook.contents(
        formula_workbook.empty_workbook())


def test_it_holds_the_steps_and_two_empty_tables(committed: openpyxl.Workbook) -> None:
    assert committed.sheetnames == ["Steps", "Parameters", "Keys"]
    tables = {name: (sheet.title, sheet.tables[name].ref) for sheet in committed.worksheets
              for name in sheet.tables}
    assert tables == {"Parameters": ("Parameters", "A1:B2"), "Keys": ("Keys", "A1:B2")}
    headers = {sheet.title: [sheet["A1"].value, sheet["B1"].value]
               for sheet in committed.worksheets[1:]}
    assert headers == {"Parameters": ["name", "value"], "Keys": ["table", "key_columns"]}
    for sheet in committed.worksheets[1:]:
        assert [cell.value for row in sheet.iter_rows(min_row=2) for cell in row
                if cell.value is not None] == [], sheet.title


def test_each_tables_sheet_says_what_it_is_for_beside_it(committed: openpyxl.Workbook) -> None:
    for sheet in committed.worksheets[1:]:
        note = sheet["D1"].value
        assert note.startswith(f"{sheet.title}: "), sheet.title
        assert [cell.coordinate for row in sheet.iter_rows() for cell in row
                if cell.value is not None] == ["A1", "B1", "D1"], sheet.title
    steps = [cell.value for row in committed["Steps"].iter_rows() for cell in row]
    about = steps.index("The Parameters and Keys sheets:")
    assert about < steps.index("Your data:")
    assert "Parameters holds" in steps[about + 1] and "Keys is" in steps[about + 1]


def test_no_cell_holds_a_formula(committed: openpyxl.Workbook) -> None:
    formulas = [f"{sheet.title}!{cell.coordinate}" for sheet in committed.worksheets
                for row in sheet.iter_rows() for cell in row
                if isinstance(cell.value, str) and cell.value.startswith("=")]
    assert formulas == []


def test_the_steps_use_no_word_the_glossary_avoids(committed: openpyxl.Workbook) -> None:
    text = "\n".join(str(cell.value) for row in committed["Steps"].iter_rows() for cell in row
                     if cell.value is not None)
    assert [word for word in (*AVOIDED, *NOT_ITS_NAME) if word.lower() in text.lower()] == []


@pytest.mark.parametrize("name", list(formula_workbook_examples.EXAMPLES))
def test_each_example_is_what_the_tool_builds_and_its_hive_runs(name: str) -> None:
    task, map_text = formula_workbook_examples.EXAMPLES[name]
    committed = openpyxl.load_workbook(formula_workbook_examples.EXAMPLES_FOLDER / name)
    assert formula_workbook.contents(committed) == formula_workbook.contents(
        formula_workbook_examples.example_workbook(task, map_text))
    assert committed.sheetnames[:3] == ["Steps", "Parameters", "Keys"]
    assert committed.sheetnames[-1] == "Hive"
    assert ("Power Query" in committed.sheetnames) == bool(task.workbook.queries)
    shown = [cell.value for row in committed["Hive"].iter_rows() for cell in row]
    for sql in task.finals.values():
        assert formula_workbook_examples.shown(sql) in shown
        assert "ops." not in formula_workbook_examples.shown(sql)
    rows = excel_eval.reference_rows(excel_eval.stand_in_hive(), task)
    assert all(rows.values()), rows


def test_the_examples_start_from_the_empty_workbook(committed: openpyxl.Workbook) -> None:
    for name in formula_workbook_examples.EXAMPLES:
        example = openpyxl.load_workbook(formula_workbook_examples.EXAMPLES_FOLDER / name)
        assert [cell.value for row in example["Steps"].iter_rows() for cell in row] == [
            cell.value for row in committed["Steps"].iter_rows() for cell in row], name
        for title in ("Parameters", "Keys"):
            assert example[title]["D1"].value == committed[title]["D1"].value, name
