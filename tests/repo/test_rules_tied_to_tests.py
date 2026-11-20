"""The two paths tied, rule by rule (Toolbox 8.9, ticket 13; ADR 0016: "Both paths, equal").

A Formula workbook converts two ways: by Copilot, loaded with the Excel files (15, 11, 12; 23
for a total; 20 for a PivotTable and 24 for its Pivot filters, as `tools/excel_eval.py`'s
`ALL_EXCEL_FILES` names them), and by the Toolbox's code. Neither is the other's reference,
so each rule ID an Excel file holds is tied to a test of the code giving the Hive the rule
gives, and the test names the ID:

- an Excel file's rule IDs are read by `copilot_files.rule_ids`: each `- **ID** ` line under a
  `## Rules` heading, and each row of a Patterns table that gives a role (file 15's P1 to P13);
  a Patterns table pointing at rules (files 11, 12, 20, 23 and 24) holds no rule of its own;
- a test names an ID by its name's start: `test_f9_...`, a range `test_p5_to_p8_...`, or, for
  an ID more than one Excel file holds (11's and 12's M1, M2 and X1) or a Worked pattern,
  `test_file_12_m1_...`; the tests read are the workbook tests of the code,
  `tests/**/test_*workbook*.py`.

It fails on a rule ID no test names, on a test naming an ID no Excel file holds (a rule, or a
Worked pattern for a `file_NN_` name), and on an ID named bare that two files hold. A rule
changes in the code and its Copilot file in one commit (`docs/agents/standards.md`).
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import copilot_files
import excel_eval

ROOT = Path(__file__).resolve().parents[2]
EXCEL_NUMBERS = excel_eval.ALL_EXCEL_FILES
CODE_TESTS = sorted((ROOT / "tests").rglob("test_*workbook*.py"))
# A test's name naming IDs: test_, then file_NN_ or not, then an ID or a range of them.
NAMED = re.compile(r"test_(?:file_(\d+)_)?([a-z]{1,2})(\d{1,2})(?:_to_([a-z]{1,2})(\d{1,2}))?_")


def excel_file_texts() -> dict[str, str]:
    """Each Excel file's text, by its number."""
    return {number: next((ROOT / "copilot").glob(f"{number}_*.txt")).read_text(encoding="utf-8")
            for number in EXCEL_NUMBERS}


def rules_by_file() -> dict[str, list[str]]:
    """Each Excel file's rule IDs, by its number."""
    return {number: copilot_files.rule_ids(text) for number, text in excel_file_texts().items()}


def code_test_names() -> list[str]:
    """Every test function's name in the workbook tests of the code."""
    names = []
    for path in CODE_TESTS:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names += [node.name for node in ast.walk(tree)
                  if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")]
    return names


def ids_named(name: str) -> tuple[str | None, list[str]]:
    """The file number a test's name gives, if any, and the IDs it names, a range
    spelled out."""
    found = NAMED.match(name)
    if found is None:
        return None, []
    number, prefix, first, last_prefix, last = found.groups()
    if last is None:
        return number, [f"{prefix.upper()}{first}"]
    if last_prefix != prefix:
        return number, [f"{prefix.upper()}{first}", f"{last_prefix.upper()}{last}"]
    return number, [f"{prefix.upper()}{each}" for each in range(int(first), int(last) + 1)]


def tied_ids() -> tuple[set[tuple[str, str]], list[str]]:
    """Each (file number, rule ID) some test names, and each test name that names an ID no
    Excel file holds, or names bare one that two hold, with why."""
    rules = rules_by_file()
    worked = {number: copilot_files.worked_pattern_ids(text)
              for number, text in excel_file_texts().items()}
    tied, wrong = set(), []
    for name in code_test_names():
        number, ids = ids_named(name)
        for rule in ids:
            if number is not None:
                if rule in rules.get(number, []):
                    tied.add((number, rule))
                elif rule not in worked.get(number, []):
                    wrong.append(f"{name}: file {number} holds no {rule}")
                continue
            holders = [each for each, held in rules.items() if rule in held]
            if len(holders) == 1:
                tied.add((holders[0], rule))
            elif holders:
                wrong.append(f"{name}: files {' and '.join(holders)} both hold {rule}: name it "
                             f"test_file_{holders[0]}_{rule.lower()}_...")
            else:
                wrong.append(f"{name}: no Excel file holds {rule}")
    return tied, wrong


def test_the_reader_finds_each_excel_files_rules() -> None:
    rules = rules_by_file()
    assert rules["11"][:3] == ["N1", "N2", "F1"] and rules["11"][-1] == "X1"
    assert rules["12"][:2] == ["Q1", "Q2"] and "T4" not in rules["12"]
    assert rules["23"] == ["T1", "T2", "T3", "T4"]
    assert rules["24"] == ["PF1", "PF2", "PF3", "PF4", "PF5"]
    assert rules["15"][:13] == [f"P{n}" for n in range(1, 14)]
    assert rules["15"][13:] == ["R1", "R2", "R3", "H1", "H2", "H3", "H4", "H5"]
    assert rules["20"][:2] == ["PS1", "PS2"] and rules["20"][-1] == "PX7"
    # A Patterns table pointing at rules, as file 11's, holds no rule of its own.
    assert "P1" not in rules["11"] + rules["12"] + rules["20"] + rules["23"] + rules["24"]


def test_a_tests_name_gives_its_ids_a_range_spelled_out() -> None:
    assert ids_named("test_f9_an_ifs_form") == (None, ["F9"])
    assert ids_named("test_p5_to_p8_a_query") == (None, ["P5", "P6", "P7", "P8"])
    assert ids_named("test_file_12_m1_a_source") == ("12", ["M1"])
    assert ids_named("test_m_is_a_let_of_named_steps") == (None, [])
    assert ids_named("test_fixture_01_a_query") == (None, [])


def test_every_rule_of_the_excel_files_has_a_test_of_the_code_naming_it() -> None:
    tied, _ = tied_ids()
    untied = []
    for number, held in rules_by_file().items():
        untied += [f"file {number}'s {rule}" for rule in held if (number, rule) not in tied]
    assert untied == []


def test_every_id_a_test_of_the_code_names_is_an_excel_files() -> None:
    _, wrong = tied_ids()
    assert wrong == []
