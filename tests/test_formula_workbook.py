"""The Formula workbook template, `copilot/formula_workbook.xlsx` (Toolbox 7.2, ticket 15).

main can't rebuild it: tools/formula_workbook.py builds it with openpyxl, which only dev
installs, and the export copies the file. It holds a sheet of steps and two empty Excel Tables,
Parameters and Keys, and nothing a person could half-edit: no data Table, no formula, no row.
The offline policy and the code audit read it as they read the repo (tests/repo/).
"""

from __future__ import annotations

import openpyxl
import pytest

import formula_workbook
from test_copilot_files import AVOIDED

TEMPLATE = formula_workbook.TEMPLATE
# The glossary's words to avoid for a Formula workbook.
NOT_ITS_NAME = ("state table", "Excel template", "mapping sheet")


@pytest.fixture(scope="module")
def committed() -> openpyxl.Workbook:
    return openpyxl.load_workbook(TEMPLATE)


def test_the_template_is_what_the_tool_builds(committed: openpyxl.Workbook) -> None:
    # Compared by what a person sees, not by bytes: a zip's times change with every build.
    assert formula_workbook.contents(committed) == formula_workbook.contents(
        formula_workbook.template())


def test_it_holds_the_steps_and_two_empty_tables(committed: openpyxl.Workbook) -> None:
    assert committed.sheetnames == ["Steps", "Parameters", "Keys"]
    tables = {name: (sheet.title, sheet.tables[name].ref) for sheet in committed.worksheets
              for name in sheet.tables}
    assert tables == {"Parameters": ("Parameters", "A1:B2"), "Keys": ("Keys", "A1:B2")}
    headers = {sheet.title: [cell.value for cell in sheet[1]]
               for sheet in committed.worksheets[1:]}
    assert headers == {"Parameters": ["name", "value"], "Keys": ["table", "key_columns"]}
    for sheet in committed.worksheets[1:]:
        assert [cell.value for row in sheet.iter_rows(min_row=2) for cell in row
                if cell.value is not None] == [], sheet.title


def test_no_cell_holds_a_formula(committed: openpyxl.Workbook) -> None:
    formulas = [f"{sheet.title}!{cell.coordinate}" for sheet in committed.worksheets
                for row in sheet.iter_rows() for cell in row
                if isinstance(cell.value, str) and cell.value.startswith("=")]
    assert formulas == []


def test_the_steps_use_no_word_the_glossary_avoids(committed: openpyxl.Workbook) -> None:
    text = "\n".join(str(cell.value) for row in committed["Steps"].iter_rows() for cell in row
                     if cell.value is not None)
    assert [word for word in (*AVOIDED, *NOT_ITS_NAME) if word.lower() in text.lower()] == []
