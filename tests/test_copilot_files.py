"""The Copilot files, `copilot/` (Toolbox 7.2, ticket 13).

Each file is what tools/copilot_files.py writes from its source, keeps to the 9,000 characters
each file is held to, spaces and line breaks included, and teaches only what is true:
every Python block in it runs on the Example database in a stand-in Project (a block calling a
Project action, which changes the Project, is read and its names checked, not run), every
Toolbox name it uses is public, and it uses none of the words the glossary avoids that can only
mean the wrong thing here, AVOIDED below: others, such as "import" or "case", are everyday
words too.
"""

from __future__ import annotations

import ast
import builtins
import inspect
import re
import sys
from pathlib import Path

import copilot_eval
import copilot_files
import excel_eval
import offline_policy
import pytest
import toolbox_registry

import example_database
import sqlglot_composer
from sqlglot_composer import admin, project

ROOT = Path(__file__).resolve().parents[1]
COPILOT = ROOT / "copilot"
sys.path.insert(0, str(COPILOT))

import count_characters  # noqa: E402
import merge_copilot_files  # noqa: E402

FILES = sorted(COPILOT.glob("*.txt"))
OBJECTIVE_FILES = [path for path in FILES if not path.name.startswith("00_")]
BLOCK = re.compile(r"```python\n(.*?)```", re.DOTALL)
# The Saved table file 06's worked example writes, which the stand-in Project needs.
JOB_DAY_EVENTS = '''from sqlglot_composer import Table

job_day_events = Table(
    "mart.job_day_events",
    columns={"job_id": "bigint", "events": "bigint", "dt": "string"},
    partitioned_by=["dt"],
    key=["job_id", "dt"],
    location="/data/your_team/mart.db/job_day_events",
)
'''
# Project actions, which change the user's Project: a block calling one is read, not run.
ACTIONS = frozenset(project.__all__) - {"load", "check"}
# Names the files call that the user's own code defines, or Python has.
OWN_CALLS = frozenset({"connect", "query", "execute", "rows", "preview", "write", "create",
                       "write_days", "converted", "recent_runs", "statements"}
                      ) | frozenset(dir(builtins))
# Hive's own functions, which file 07 quotes from the Hive it converts: allowed as Hive's
# words in backticks, so a file writing COUNT(x) as a Toolbox name would pass this test; the
# block tests, which run the code, are what catch it.
HIVE_WORDS = frozenset({"COALESCE", "IN", "UPPER", "COUNT", "SUM", "AVG", "MIN", "MAX",
                        "ROW_NUMBER"})
# The Excel files, which turn a Formula workbook into Hive, loaded together, as the Excel
# evaluation names them: those every workbook loads, and the one for a workbook with a pivot.
EXCEL_NUMBERS = (*excel_eval.EXCEL_FILES, excel_eval.PIVOT_FILE)
EXCEL_FILES = tuple(path.name for number in EXCEL_NUMBERS
                    for path in sorted(COPILOT.glob(f"{number}_*.txt")))
# File 19 writes a Metric request, plain text for the user's chatbot: no code, and no SQL.
METRIC_REQUEST = "19_metric_request.txt"
# Files 21 and 22 grow a table convert made from a PivotTable, its add-ons and its Pivot
# filters, each loaded with the files whose functions it uses, as the Copilot evaluation loads
# them (Toolbox 8.9, ticket 12).
GROWING_A_PIVOT = "21_growing_a_converted_pivot.txt"
PIVOT_FILTERS = "22_pivot_filters_at_scale.txt"
# Words the glossary says to avoid that can only mean the wrong thing in these files.
AVOIDED = ("raw SQL", "guardrail", "predicate", "schema file", "table config", "snippet",
           "boilerplate", "materialized view", "temp table", "set operation", "OVER clause",
           "framework", "library", "helper", "analytic function")


def blocks() -> list[tuple[str, int, str]]:
    """Each Python block of each Copilot file: (file, its number in the file, its code)."""
    return [(path.name, number, code) for path in FILES
            for number, code in enumerate(BLOCK.findall(path.read_text(encoding="utf-8")), 1)]


def test_each_file_is_what_its_source_writes() -> None:
    written = copilot_files.copilot_files()
    assert sorted(written) == [path.name for path in FILES]
    for path in FILES:
        assert path.read_text(encoding="utf-8") == written[path.name], path.name


def test_the_folder_holds_the_files_the_counter_the_workbooks_and_all_in_one() -> None:
    assert sorted(path.name for path in COPILOT.iterdir() if path.name != "__pycache__") == (
        sorted([path.name for path in FILES]
               + ["all_in_one", "count_characters.py", "examples", "formula_workbook.xlsx",
                  "workbook_text.py"]))
    assert all(path.suffix == ".xlsx" for path in (COPILOT / "examples").iterdir())
    assert ([path.name for path in (COPILOT / "all_in_one").iterdir()]
            == ["all_copilot_files.txt"])
    assert [path.name[:2] for path in FILES] == [f"{n:02d}" for n in range(23)]


def test_all_in_one_merges_every_file_in_order() -> None:
    text = merge_copilot_files.MERGED.read_text(encoding="utf-8")
    assert text == merge_copilot_files.merged()
    assert [line[6:-6] for line in text.splitlines() if line.startswith("===== ")] == [
        path.name for path in FILES]
    for path in FILES:
        assert path.read_text(encoding="utf-8").rstrip() in text


@pytest.mark.parametrize("path", FILES, ids=lambda path: path.name)
def test_each_file_fits_what_copilot_takes_spaces_and_line_breaks_included(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert count_characters.characters(text) <= count_characters.LIMIT == 9000
    assert count_characters.characters_on_windows(text) <= count_characters.LIMIT


@pytest.mark.parametrize("path", OBJECTIVE_FILES, ids=lambda path: path.name)
def test_each_objective_file_has_the_same_parts(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    version = f"{toolbox_registry.PRODUCT} {sqlglot_composer.TOOLBOX_VERSION}"
    assert version in text.splitlines()[0]
    # Each is written to docs/agents/instruction-rules.md: it defines its Terms and ends on a
    # Self-check; each but the Excel files, which write Hive, and file 19, which writes a Metric
    # request, names its Toolbox functions.
    parts: tuple[str, ...] = ("Objective: ", "Load this file when", "## Terms", "## Self-check")
    if path.name not in (*EXCEL_FILES, METRIC_REQUEST):
        parts += ("## Names for this objective, with their arguments",)
    assert re.findall(r"^## (.+)$", text, re.MULTILINE)[-1] == "Self-check"
    for part in parts:
        assert part in text, part
    # The Excel files write Hive, no Toolbox code; files 13, 14 and 16 give steps, each a cell,
    # and the file of the step's objective the code; file 17 gives a Workflow's decisions cell
    # and the Run value's function it imports, and leaves a Statement inside one to file 03;
    # file 18 gives a Scheduled run's cells, and leaves a Statement of its own to file 03 too;
    # file 19 writes no code at all; files 21 and 22 are loaded with files that hold the
    # block, 03, 05 and 06 and 06 and 17, and hold A11 themselves (Toolbox 8.9, ticket 12).
    if path.name in (GROWING_A_PIVOT, PIVOT_FILTERS):
        assert copilot_files.LEAN.read_text(encoding="utf-8").strip() in text
    if path.name not in (*EXCEL_FILES, "13_workflows.txt",
                         "14_workflows_new_tables_and_upkeep.txt", "16_workflows_promote.txt",
                         "17_run_values_and_seed_limits.txt", "18_scheduled_runs.txt",
                         METRIC_REQUEST, GROWING_A_PIVOT, PIVOT_FILTERS):
        assert copilot_files.ALWAYS.read_text(encoding="utf-8").strip() in text
        # Ticket 17: rule A11, Hive that stays small, right after the block; the shared one,
        # or a file's own shorter one where the shared one doesn't fit.
        after = text.split(copilot_files.ALWAYS.read_text(encoding="utf-8").strip())[1]
        assert after.startswith("\n- **A11** Read each Derived table once; SELECT in it only")


# Ticket 06's pivot rules, by their IDs (.scratch/toolbox-8-9/issues/06-pivots-in-code.md):
# file 20 holds each, so the Copilot path and the code path give the same Hive.
PIVOT_RULES = ([f"PR{n}" for n in range(1, 6)] + [f"PV{n}" for n in range(1, 9)]
               + [f"PC{n}" for n in range(1, 4)] + ["PL1", "PL2"]
               + [f"PF{n}" for n in range(1, 6)] + ["PG1", "PG2"]
               + [f"PS{n}" for n in range(1, 5)] + ["PN1", "PN2"]
               + [f"PX{n}" for n in range(1, 8)])


def test_file_20_holds_every_pivot_rule() -> None:
    text = (COPILOT / "20_excel_pivot_tables.txt").read_text(encoding="utf-8")
    assert [rule for rule in PIVOT_RULES if f"- **{rule}** " not in text] == []


def test_file_20_has_copilot_mark_each_pivot_filter() -> None:
    text = (COPILOT / "20_excel_pivot_tables.txt").read_text(encoding="utf-8")
    assert "`-- Pivot filter: <kind> <field>`" in text


def test_start_here_loads_the_excel_files_the_evaluation_loads() -> None:
    # A workbook with a pivot loads every Excel file, as arm C of the Excel evaluation gives it.
    text = (COPILOT / "00_start_here.txt").read_text(encoding="utf-8")
    assert f"| {', '.join(EXCEL_NUMBERS)} |" in text


@pytest.mark.parametrize("objective", sorted(copilot_eval.LOADED_WITH))
def test_start_here_loads_files_21_and_22_with_the_files_the_evaluation_loads(
        objective: str) -> None:
    text = (COPILOT / "00_start_here.txt").read_text(encoding="utf-8")
    assert f"| {', '.join(copilot_eval.objective_files(objective))} |" in text


def test_file_22_says_what_the_pivot_filter_decision_does_and_the_users_words() -> None:
    # Ticket 08's four answers in its words, how it answers, its proposals and its names, both
    # paths equal; and the user's (2026-11-19): "emphasize how many different tables it would
    # create".
    text = " ".join((COPILOT / PIVOT_FILTERS).read_text(encoding="utf-8").split())
    for said in ('"keep", proposed: 1 table', '"fold", like dragging the field from Filters '
                 "to Rows: 1 table", '"batch": 1 table partitioned on the field, a Partition '
                 "per value", '"tables", like Show Report Filter Pages: a table per value',
                 "Region 3 and Site 100 make at least 300",
                 "A filter with 100 conditions would make 100 tables, but the higher layer "
                 "filter may have only 3, which is manageable.",
                 "a blank `_blank`, a day `_2026_09_23`, a clash `_2`",
                 "A Timeline's days each make a table",
                 'project.new_run_value("latest_dt", latest_partition="ops.job_runs.dt")',
                 'hivevar("STATUS", default="FAILED")', '`"key": "proposed"` accepts it',
                 "Once the table is created in dev, another answer is refused",
                 'undoes "tables"', "a filter in a step",
                 'A value filter (Top 10) has only "keep" or "fold"',
                 "converted without its workbook has no count"):
        assert said in text, said


def test_file_21_names_convert_s_total_level_tables_and_what_months_gave() -> None:
    # Ticket 07's names for a total level's table, and ticket 06's PR3 label for Months.
    text = " ".join((COPILOT / GROWING_A_PIVOT).read_text(encoding="utf-8").split())
    for said in ("`<table>_by_<field>` and `<table>_grand_total`",
                 "where convert's Months grouping gave a label, Sep"):
        assert said in text, said


def test_start_here_names_every_other_file() -> None:
    text = (COPILOT / "00_start_here.txt").read_text(encoding="utf-8")
    for path in OBJECTIVE_FILES:
        assert f"`{path.name}`" in text


@pytest.mark.parametrize("path", FILES, ids=lambda path: path.name)
def test_no_file_reaches_off_this_computer_or_hides_text(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert not offline_policy.URL.search(text)
    assert offline_policy.external_references(text) == []
    assert text.isascii()


@pytest.mark.parametrize("path", FILES, ids=lambda path: path.name)
def test_no_file_uses_a_word_the_glossary_avoids(path: Path) -> None:
    text = path.read_text(encoding="utf-8").lower()
    assert [word for word in AVOIDED if word.lower() in text] == []


@pytest.mark.parametrize(("name", "number", "code"), blocks(),
                         ids=[f"{name}-{number}" for name, number, _ in blocks()])
def test_every_block_imports_public_names_by_name(name: str, number: int, code: str) -> None:
    tree = ast.parse(code)
    invented, star = copilot_eval.invented_names(tree)
    assert invented == [] and not star
    assert copilot_eval.unsafe(tree) is None


def _called_names(text: str) -> set[str]:
    """Each function the Python in backticks calls, as name or module.name."""
    called = set()
    for span in re.findall(r"`([^`\n]+)`", text):
        try:
            tree = ast.parse(span.strip())
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                called.add(node.func.id)
            elif (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                  and isinstance(node.func.value, ast.Name)
                  and node.func.value.id in ("project", "admin")):
                called.add(f"{node.func.value.id}.{node.func.attr}")
    return called


@pytest.mark.parametrize("path", FILES, ids=lambda path: path.name)
def test_every_function_named_in_backticks_is_the_toolboxs_or_the_users(path: Path) -> None:
    public = (set(sqlglot_composer.__all__) | {f"project.{n}" for n in project.__all__}
              | {f"admin.{n}" for n in admin.__all__} | OWN_CALLS | HIVE_WORDS)
    assert sorted(_called_names(path.read_text(encoding="utf-8")) - public) == []


@pytest.fixture(scope="module")
def ran() -> dict[tuple[str, int], str | None]:
    """Each block run in one stand-in Project: None where it ran, else what stopped it. A
    block calling a Project action is read, not run; a logic cell's functions are called."""
    found = {}
    with copilot_eval.example_setting(), copilot_eval.times_pinned():
        folder = Path.cwd()
        with copilot_eval.project_on_the_path(folder), copilot_eval.answers_kept_in(folder):
            copilot_eval.stand_in(folder, saved={"job_day_events": JOB_DAY_EVENTS})
            for name, number, code in blocks():
                if copilot_eval.calls(ast.parse(code)) & ACTIONS:
                    found[(name, number)] = None
                    continue
                try:
                    with copilot_eval._quiet():
                        logic, _ = copilot_eval.loaded(code, f"block_{name[:2]}_{number}",
                                                       "None")
                        for function_name, function in logic._functions.items():
                            takes_nothing = not [
                                one for one in inspect.signature(function).parameters.values()
                                if one.default is one.empty]
                            if takes_nothing and not function_name.startswith("_"):
                                function()
                    found[(name, number)] = None
                except Exception as error:
                    found[(name, number)] = copilot_eval._error_note(error)
    return found


@pytest.mark.parametrize(("name", "number", "code"), blocks(),
                         ids=[f"{name}-{number}" for name, number, _ in blocks()])
def test_every_block_runs_on_the_example_database(
        ran: dict[tuple[str, int], str | None], name: str, number: int, code: str) -> None:
    assert ran[(name, number)] is None


HIVE_BLOCK = re.compile(r"```sql\n(.*?)```", re.DOTALL)


@pytest.mark.parametrize("path", FILES, ids=lambda path: path.name)
def test_every_hive_block_runs_on_the_example_database_once_filled_in(path: Path) -> None:
    for hive in HIVE_BLOCK.findall(path.read_text(encoding="utf-8")):
        assert not example_database.query(
            hive.replace("<database>", "ops")).empty
