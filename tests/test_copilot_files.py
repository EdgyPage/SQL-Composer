"""The Copilot files, `copilot/` (Toolbox 7.2, ticket 13).

Each file is what tools/copilot_files.py writes from its source, fits the 8,000 characters
Copilot takes at once, spaces and line breaks included, and teaches only what is true:
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
import offline_policy
import pytest
import toolbox_registry

import sqlglot_composer
from sqlglot_composer import admin, project

ROOT = Path(__file__).resolve().parents[1]
COPILOT = ROOT / "copilot"
sys.path.insert(0, str(COPILOT))

import count_characters  # noqa: E402

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
OWN_CALLS = frozenset({"query", "execute", "rows", "preview", "write", "create", "converted",
                       "recent_runs"}) | frozenset(dir(builtins))
# Hive's own functions, which file 07 quotes from the Hive it converts: allowed as Hive's
# words in backticks, so a file writing COUNT(x) as a Toolbox name would pass this test; the
# block tests, which run the code, are what catch it.
HIVE_WORDS = frozenset({"COALESCE", "IN", "UPPER", "COUNT", "SUM", "AVG", "MIN", "MAX",
                        "ROW_NUMBER"})
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


def test_the_folder_holds_the_files_and_the_counter_only() -> None:
    assert sorted(path.name for path in COPILOT.iterdir() if path.name != "__pycache__") == (
        sorted([path.name for path in FILES] + ["count_characters.py"]))
    assert [path.name[:2] for path in FILES] == [f"{n:02d}" for n in range(11)]


@pytest.mark.parametrize("path", FILES, ids=lambda path: path.name)
def test_each_file_fits_what_copilot_takes_spaces_and_line_breaks_included(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    assert count_characters.characters(text) <= count_characters.LIMIT == 8000
    assert count_characters.characters_on_windows(text) <= count_characters.LIMIT


@pytest.mark.parametrize("path", OBJECTIVE_FILES, ids=lambda path: path.name)
def test_each_objective_file_has_the_same_parts(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    version = f"{toolbox_registry.PRODUCT} {sqlglot_composer.TOOLBOX_VERSION}"
    assert version in text.splitlines()[0]
    for part in ("Objective: ", "Load this file when", "## Always",
                 "## Names for this objective, with their arguments", "## Worked example",
                 "## Do and don't", "## Before you answer"):
        assert part in text, part
    assert copilot_files.ALWAYS.read_text(encoding="utf-8").strip() in text


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
                    found[(name, number)] = copilot_eval._said(error)
    return found


@pytest.mark.parametrize(("name", "number", "code"), blocks(),
                         ids=[f"{name}-{number}" for name, number, _ in blocks()])
def test_every_block_runs_on_the_example_database(
        ran: dict[tuple[str, int], str | None], name: str, number: int, code: str) -> None:
    assert ran[(name, number)] is None
