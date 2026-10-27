"""Score answers to the Copilot evaluation's tasks, offline, on the Example database.

The Copilot files (`copilot/`) are meant to make Copilot write Toolbox code that works. This
measures it: the same tasks (`tools/copilot_eval_tasks.py`) are answered with and without the
files, by Copilot in its web chat or by a proxy model in a Claude session, each reply is kept
in an answers file, and this scores the replies against the tasks' reference answers.

    python tools/copilot_eval.py prompts --split dev
    python tools/copilot_eval.py template --split dev > answers.md
    python tools/copilot_eval.py score answers.md --record .scratch/copilot-eval/results.md

An answers file starts with its header lines, `arm: C`, `model: haiku`, `files: <hash>`, then
holds a `## T07` heading for each task, followed by the reply as it came. The last Python code
block under a heading is the answer.

Each answer is scored on these checks, in order:

- found: there is a code block;
- parses: it is Python;
- real names: every name imported from the Toolbox, and every project.x and admin.x, is a
  public one; a star import is noted;
- builds: run as a Conversion's logic cell in a stand-in Project, it gives what the task asks
  for (a Statement s, a Table reference t, a Verdict v, or a logic cell's write()) with no
  Guard or Load limit refusing it;
- runs: it runs on the Example database;
- correct: it gives the reference's rows (or, for a write, writes them into the same table
  the same way; for Hive the Example database can't run, the same Hive; for a Table
  reference, the same name, columns, partitions, Key and location; for a check, a Verdict
  that holds);
- style: no opt-out or Unchecked piece the reference doesn't need, and a run_query where the
  request asks to run it.

An answer passes when it is correct, invents no name and adds no opt-out the reference
doesn't need.

The answers are a model's code, so each is read first: it may import only the Toolbox, the
Project's own modules, pandas, datetime, math, typing and collections.abc, and may not call
open, eval, exec, compile, __import__ or the like, or reach a name that starts with two
underscores. What passes runs through project.load, as a Conversion's logic cell runs, with
its run_query and run_execute calls taken out, as load refuses a cell that sends Hive. The
stand-in Project's Table references are the Example database's tables, and its warehouse.py
sends to the Example database; today is 2026-09-25, as on the how-to page.
"""

from __future__ import annotations

import argparse
import ast
import json
import math
import re
import sys
import warnings
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT)]

import sqlglot_composer  # noqa: E402
from copilot_eval_tasks import BY_ID, GIVES, OBJECTIVES, TASKS, Task  # noqa: E402
from example_gallery import example_setting  # noqa: E402
from how_to_page import project_on_the_path  # noqa: E402
from sqlglot_composer import (  # noqa: E402
    Statement,
    Table,
    Verdict,
    compare_hive,
    compare_with_original,
    example_database,
    project,
    run_query,
    to_hive,
)
from sqlglot_composer import admin as admin_module  # noqa: E402

# The Example database's tables, which the stand-in Project has as references/ops__<name>.py.
EXAMPLE_TABLES = ("jobs", "job_runs", "run_alerts", "scheduler_runs", "job_events",
                  "job_owners", "region_costs", "region_budgets", "team_notes")
# The modules an answer may import, by their first part.
ALLOWED_MODULES = frozenset({"sqlglot_composer", "references", "building_blocks", "warehouse",
                             "pandas", "datetime", "math", "re", "typing", "collections",
                             "__future__"})
# The builtins an answer may not call, which reach outside the answer.
FORBIDDEN_NAMES = frozenset({"open", "eval", "exec", "compile", "__import__", "globals",
                             "locals", "vars", "getattr", "setattr", "delattr", "input",
                             "breakpoint", "exit", "quit", "memoryview"})
# The keywords a user passes to tell a Guard or a Load limit they have checked what it refuses.
OPT_OUTS = frozenset({"reads_all_partitions", "many_matches", "keeps_only_matches", "adds_up",
                      "sorts_everything", "unproven_key", "returns_all_rows"})
UNCHECKED = frozenset({"unchecked_hive", "unchecked_column", "unchecked_condition",
                       "unchecked_derived"})
SENDERS = frozenset({"run_query", "run_execute"})
PUBLIC = frozenset(sqlglot_composer.__all__) | {"project", "admin"}
MODULE_NAMES = {"project": frozenset(project.__all__), "admin": frozenset(admin_module.__all__)}

WAREHOUSE = '''"""warehouse - the stand-in Project's two calls, both to the Example database."""

import pandas as pd

from sqlglot_composer import example_database


def query(hive: str) -> pd.DataFrame:
    return example_database.query(hive)


def execute(hive: str) -> None:
    example_database.execute(hive)
'''

CONTRACT = {
    "s": "Answer with one Python code block that builds it and assigns the Statement to `s`.",
    "write()": "Answer with one Python code block: the logic cell, its imports and functions.",
    "t": "Answer with one Python code block that assigns the Table reference to `t`.",
    "v": "Answer with one Python code block that assigns the check's result to `v`.",
}


# --- The prompts ---------------------------------------------------------------------------


def table_context(name: str) -> str:
    """One line of a prompt's context: an Example database table, as the Project has it."""
    table = getattr(example_database, name)
    columns = ", ".join(f"{column} {kind}" for column, kind in table._columns.items())
    partitions = (f"; partitioned by {', '.join(table._partitioned_by)}"
                  if table._partitioned_by else "")
    key = f"; Key {', '.join(table._key)}" if table._key else "; no Key"
    return (f"- `from references.ops__{name} import {name}` gives {table._name}: {columns}"
            f"{partitions}{key}.")


def prompt(task: Task) -> str:
    """What the user sends Copilot for a task: their Project's context, then the request."""
    version = sqlglot_composer.TOOLBOX_VERSION
    lines = [f"I work in a sqlglot Composer {version} Project. Its references:"]
    lines += [table_context(name) for name in task.tables]
    if task.tables:
        lines.append("- `from references import ops` gives each ops table above by its name, "
                     "as ops.job_runs.")
    for name, code in task.saved.items():
        lines.append(f"- references/mart__{name}.py holds:\n\n{code}")
    lines.append("- `from warehouse import query, execute` gives my two calls to the "
                 "warehouse.")
    return "\n".join(lines) + f"\n\n{task.request}\n\n{CONTRACT[GIVES[task.kind]]}"


def tasks_of(split: str) -> list[Task]:
    return [task for task in TASKS if split == "all" or task.split == split]


# The most text a user loads into a chat before asking, in characters, spaces included.
LIMIT = 8000
README_TEMPLATE = ROOT / "docs" / "clean-branch-readme.md"
COPILOT = ROOT / "copilot"
ARMS = {
    "A0": "nothing: the request alone",
    "A1": "the README's opening, cut to the same limit: what a user could share before the files",
    "C": "the Copilot file for the task's objective",
    "R": "copilot/00_start_here.txt, which says which file to load",
}


def baseline_text() -> str:
    """Arm A1's text: the README's opening, cut at the last whole line that fits the limit."""
    lines, size = [], 0
    for line in README_TEMPLATE.read_text(encoding="utf-8").splitlines(keepends=True):
        if size + len(line) > LIMIT:
            break
        lines.append(line)
        size += len(line)
    return "".join(lines)


def shared_text(arm: str, objective: str | None) -> str | None:
    """What a user shares in an arm before asking, or None for the request alone."""
    if arm == "A0":
        return None
    if arm == "A1":
        return baseline_text()
    name = "00" if arm == "R" else objective
    [path] = sorted(COPILOT.glob(f"{name}_*.txt"))
    return path.read_text(encoding="utf-8")


def proxy_message(arm: str, tasks: list[Task]) -> str:
    """The message a proxy model is given for one arm: what the user shared, then each task's
    prompt, as if each came in a chat of its own. In arm C every task has the same objective,
    as a user loads one file at a time; in arm R the proxy only names the file it would load."""
    objectives = {task.objective for task in tasks}
    if arm == "C" and len(objectives) != 1:
        raise ValueError("arm C takes the tasks of one objective, as one file is loaded")
    shared = shared_text(arm, next(iter(objectives)))
    head = ("You are standing in for Microsoft Copilot in a web chat. Use no tools: answer "
            "from what is written here and what you already know.\n\n")
    if shared is not None:
        head += ("Before asking anything, the user pasted this as their first message:\n\n"
                 "<<<\n" + shared + "\n>>>\n\n")
    if arm == "R":
        ask = ("For each task below, reply with its `## T..` heading and the one file name "
               "you would load for it, such as 03_build_a_statement.txt, and nothing else.")
    else:
        ask = ("Each task below is a separate request the user sends next. Answer each as you "
               "would in that chat: reply with its `## T..` heading, then your answer, with "
               "the code in a ```python block.")
    return head + ask + "\n\n" + "\n\n".join(f"## {task.id}\n\n{prompt(task)}"
                                             for task in tasks)


def template(split: str) -> str:
    """An answers file to fill in: its header, then a heading and an empty block per task."""
    head = "arm: <A0, A1, C or R>\nmodel: <the model>\nfiles: <the Copilot files' hash>\n"
    return head + "".join(f"\n## {task.id}\n\n```python\n```\n" for task in tasks_of(split))


# --- Reading an answers file ---------------------------------------------------------------


def read_answers(text: str) -> tuple[dict[str, str], dict[str, str]]:
    """An answers file's header, by name, and each reply, by its task's id."""
    parts = re.split(r"^## (T\d+)\s*$", text, flags=re.MULTILINE)
    header = dict(re.findall(r"^(\w+):[ \t]*(.*?)[ \t]*$", parts[0], re.MULTILINE))
    replies = {parts[i]: parts[i + 1] for i in range(1, len(parts), 2)}
    return header, replies


def answer_code(reply: str) -> str | None:
    """The last Python code block of a reply, or of any code block where none says Python."""
    blocks = re.findall(r"```[ \t]*(\w*)[ \t]*\n(.*?)```", reply, re.DOTALL)
    python = [code for language, code in blocks if language.lower() in ("python", "py", "")]
    return python[-1] if python and python[-1].strip() else None


# --- Scoring one answer --------------------------------------------------------------------


@dataclass
class Score:
    """How one answer did on each check."""

    task: str
    found: bool = False
    parses: bool = False
    invented: list[str] = field(default_factory=list)
    star: bool = False
    builds: bool = False
    runs: bool = False
    correct: bool = False
    needless: list[str] = field(default_factory=list)
    unrun: bool = False  # the request asked to run it, and the answer doesn't
    note: str = ""

    @property
    def passed(self) -> bool:
        return self.correct and not self.invented and not self.needless


def _toolbox_imports(tree: ast.Module) -> tuple[list[str], bool, dict[str, str]]:
    """What an answer imports from the Toolbox: each name that isn't public, whether it
    imports with *, and the name each Toolbox module it can reach a name through is bound to,
    as {"project": "project", "sc": "sqlglot_composer"}."""
    invented, star, bound = [], False, {}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "sqlglot_composer":
            for alias in node.names:
                star = star or alias.name == "*"
                if alias.name in MODULE_NAMES:
                    bound[alias.asname or alias.name] = alias.name
                elif alias.name not in PUBLIC | {"*"}:
                    invented.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
                "sqlglot_composer.") and node.module != "sqlglot_composer.example_database":
            invented.append(node.module)
        elif isinstance(node, ast.Import):
            bound.update({alias.asname or alias.name: alias.name for alias in node.names
                          if alias.name == "sqlglot_composer"})
    return invented, star, bound


def invented_names(tree: ast.Module) -> tuple[list[str], bool]:
    """Each Toolbox name an answer uses that isn't public, and whether it imports with *."""
    invented, star, bound = _toolbox_imports(tree)
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg == "send":
            invented.append("send=")  # 7.0 replaced it with query and execute
        if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
            module = bound.get(node.value.id)
            known = PUBLIC if module == "sqlglot_composer" else MODULE_NAMES.get(module or "")
            if known is not None and node.attr not in known:
                invented.append(f"{node.value.id}.{node.attr}")
    return sorted(set(invented)), star


def unsafe(tree: ast.Module) -> str | None:
    """What makes an answer unsafe to run, or None: an import from outside the allowed
    modules, a forbidden builtin, or a name with two underscores in front."""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots = [alias.name.split(".")[0] for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            roots = [(node.module or "").split(".")[0]] if not node.level else ["."]
        else:
            roots = []
        outside = [root for root in roots if root not in ALLOWED_MODULES]
        if outside:
            return f"it imports {outside[0]}, which an answer may not"
        if isinstance(node, ast.Name) and node.id in FORBIDDEN_NAMES:
            return f"it uses {node.id}, which an answer may not"
        name = node.attr if isinstance(node, ast.Attribute) else (
            node.id if isinstance(node, ast.Name) else "")
        if name.startswith("__") and name != "__name__":
            return f"it reaches {name}, which an answer may not"
    return None


class _SendersOut(ast.NodeTransformer):
    """Each call to run_query made a call to _scored_read, which reads the Example database
    the same way, and each run_execute None: load refuses a logic cell that sends Hive, and
    an answer's code after a read, such as df.sort_values(...), still needs the rows."""

    def visit_Call(self, node: ast.Call) -> ast.AST:
        self.generic_visit(node)
        called = node.func.id if isinstance(node.func, ast.Name) else (
            node.func.attr if isinstance(node.func, ast.Attribute) else "")
        if called == "run_query":
            return ast.copy_location(ast.Call(ast.Name("_scored_read", ast.Load()), node.args,
                                              node.keywords), node)
        return ast.copy_location(ast.Constant(None), node) if called in SENDERS else node


# What a run_query in an answer becomes: the same read, on the Example database.
_SCORED_READ = '''from sqlglot_composer import example_database as _scored_database
from sqlglot_composer import to_hive as _scored_hive


def _scored_read(statement, *_, **__):
    return _scored_database.query(_scored_hive(statement))
'''


def calls(tree: ast.Module) -> set[str]:
    """The name of every function an answer calls."""
    return {node.func.id if isinstance(node.func, ast.Name) else node.func.attr
            for node in ast.walk(tree) if isinstance(node, ast.Call)
            and isinstance(node.func, (ast.Name, ast.Attribute))}


def opt_outs(tree: ast.Module) -> set[str]:
    """The opt-outs an answer passes, and the Unchecked pieces it uses."""
    passed = {keyword.arg for node in ast.walk(tree) if isinstance(node, ast.Call)
              for keyword in node.keywords if keyword.arg in OPT_OUTS}
    return passed | (calls(tree) & UNCHECKED)


def loaded(code: str, name: str, gives: str) -> tuple[object, object]:
    """What an answer gives, run as a Conversion's logic cell in the stand-in Project."""
    tree = _SendersOut().visit(ast.parse(code))
    future = [node for node in tree.body
              if isinstance(node, ast.ImportFrom) and node.module == "__future__"]
    rest = ast.Module([node for node in tree.body if node not in future], [])
    cell = "\n".join(["# logic", *(ast.unparse(node) for node in future), _SCORED_READ,
                      ast.unparse(rest), "", "", f"def converted():\n    return {gives}\n"])
    folder = Path("admin") / "conversions" / name
    folder.mkdir(parents=True, exist_ok=True)
    notebook = {"cells": [{"cell_type": "code", "execution_count": None, "metadata": {},
                           "outputs": [], "source": cell.splitlines(keepends=True)}],
                "metadata": {}, "nbformat": 4, "nbformat_minor": 5}
    (folder / f"{name}.ipynb").write_text(json.dumps(notebook), encoding="utf-8")
    logic = project.load(name)
    return logic, logic.converted()


def _value(value: object) -> object:
    """A value as rows are compared: NULL and NaN alike, numbers by value."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    if isinstance(value, float):
        return round(value, 6)
    if hasattr(value, "item"):  # a numpy number
        return _value(value.item())
    return value


def rows_of(s: Statement) -> tuple[list[str], list[tuple[object, ...]]]:
    """A read's column names, and its rows in a fixed order, on the Example database."""
    found = run_query(s, example_database.query)
    rows = [tuple(_value(value) for value in row) for row in found.itertuples(index=False)]
    return [str(column).lower() for column in found.columns], sorted(rows, key=repr)


def _insert_line(s: Statement) -> str:
    """The INSERT line of a write's Hive, as compared: the table and the way it writes."""
    line = next((one for one in to_hive(s).splitlines() if one.startswith("INSERT")), "")
    return " ".join(line.split())


def _same_write(answer: object, reference: Statement, task: Task) -> bool:
    if not isinstance(answer, Statement) or _insert_line(answer) != _insert_line(reference):
        return False
    return bool(compare_with_original(answer, to_hive(reference), query=example_database.query,
                                      partition=task.partition))


def _same_table(answer: object, reference: Table) -> bool:
    if not isinstance(answer, Table):
        return False
    parts = ("_name", "_partitioned_by", "_key", "_does_not_add_up", "_location")
    columns = {name: str(kind).lower() for name, kind in answer._columns.items()}
    wanted = {name: str(kind).lower() for name, kind in reference._columns.items()}
    return columns == wanted and all(
        getattr(answer, part) == getattr(reference, part) for part in parts)


def correct(answer: object, logic: object, reference: object, task: Task) -> bool:
    """Whether an answer gives what the reference gives, by the task's kind."""
    if task.kind in ("read", "convert", "fix"):
        return isinstance(answer, Statement) and rows_of(answer) == rows_of(reference)
    if task.kind == "hive":
        return isinstance(answer, Statement) and bool(compare_hive(answer, to_hive(reference)))
    if task.kind == "write":
        return _same_write(answer, reference, task)
    if task.kind == "logic":
        create = getattr(logic, "create", None)
        made = create() if callable(create) else None
        return (_same_write(answer, reference, task) and isinstance(made, Statement)
                and to_hive(made).startswith("CREATE"))
    if task.kind == "table":
        return _same_table(answer, reference)
    return isinstance(answer, Verdict) and bool(answer)


def gives_the_kind(answer: object, task: Task) -> bool:
    """Whether an answer gives the kind of thing its task asks for."""
    kind = {"table": Table, "verdict": Verdict}.get(task.kind, Statement)
    return isinstance(answer, kind)


def score(task: Task, reply: str, reference: object) -> Score:
    """One answer, scored check by check against the reference's result."""
    result = Score(task.id)
    code = answer_code(reply)
    if code is None:
        result.note = "no code block"
        return result
    result.found = True
    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        result.note = f"doesn't parse: {error.msg}"
        return result
    result.parses = True
    result.invented, result.star = invented_names(tree)
    result.needless = sorted(opt_outs(tree) - opt_outs(ast.parse(task.reference)))
    result.unrun = task.runs_it and "run_query" not in calls(tree)
    danger = unsafe(tree)
    if danger:
        result.note = f"not run: {danger}"
        return result
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            logic, answer = loaded(code, task.id.lower(), GIVES[task.kind])
    except Exception as error:  # a refusal, or the answer's own mistake
        result.note = f"doesn't build: {_said(error)}"
        return result
    result.builds = gives_the_kind(answer, task)
    if not result.builds:
        result.note = f"gives {type(answer).__name__}, not what the task asks for"
        return result
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            result.correct = correct(answer, logic, reference, task)
        result.runs = True
    except Exception as error:
        result.note = f"doesn't run: {_said(error)}"
        return result
    if not result.correct:
        result.note = "runs, but gives something else"
    return result


def _said(error: Exception) -> str:
    """The first line of an error, or the What happened line of a four-part message."""
    found = re.search(r"What happened:\s*(.+)", str(error))
    said = found.group(1) if found else (str(error).strip().splitlines() or [""])[0]
    return f"{type(error).__name__}: {said.strip()}"[:200]


# --- The stand-in Project, and scoring a whole file ----------------------------------------


def stand_in(folder: Path) -> None:
    """A Project in `folder` whose Table references are the Example database's tables, and the
    writing tasks' Saved tables, and whose warehouse.py sends to the Example database."""
    project.start()
    (folder / "warehouse.py").write_text(WAREHOUSE, encoding="utf-8")
    references = folder / "references"
    for name in EXAMPLE_TABLES:
        (references / f"ops__{name}.py").write_text(
            f'"""ops.{name}, the Example database\'s."""\n\n'
            f"from sqlglot_composer.example_database import {name}\n", encoding="utf-8")
    (references / "ops.py").write_text("".join(
        f"from references.ops__{name} import {name}\n" for name in EXAMPLE_TABLES),
        encoding="utf-8")
    saved = {name: code for task in TASKS for name, code in task.saved.items()}
    for name, code in saved.items():
        (references / f"mart__{name}.py").write_text(code, encoding="utf-8")
    (references / "mart.py").write_text("".join(
        f"from references.mart__{name} import {name}\n" for name in saved), encoding="utf-8")


def scored(replies: dict[str, str]) -> list[Score]:
    """Each reply, by its task's id, scored against its task's reference, in task order."""
    return scored_pairs([(task_id, replies[task_id]) for task_id in BY_ID if task_id in replies])


def scored_pairs(pairs: list[tuple[str, str]]) -> list[Score]:
    """Each (task id, reply) scored, in one fresh stand-in Project, against its task's
    reference; a task may come more than once."""
    results, references = [], {}
    with example_setting():
        folder = Path.cwd()
        with project_on_the_path(folder):
            stand_in(folder)
            for task_id, reply in pairs:
                task = BY_ID[task_id]
                if task_id not in references:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        logic, reference = loaded(task.reference,
                                                  f"reference_{task_id.lower()}",
                                                  GIVES[task.kind])
                    references[task_id] = logic.write() if task.kind == "logic" else reference
                results.append(score(task, reply, references[task_id]))
    return results


CHECKS = ("found", "parses", "builds", "runs", "correct")


def summary(results: list[Score]) -> dict[str, object]:
    """The pass rate, each check's rate, and the pass rate of each objective, in percent."""
    def rate(values: list[bool]) -> int:
        return round(100 * sum(values) / len(values)) if values else 0

    objectives = {}
    for objective in OBJECTIVES:
        mine = [one for one in results if BY_ID[one.task].objective == objective]
        if mine:
            objectives[objective] = rate([one.passed for one in mine])
    return {
        "answers": len(results),
        "passed": rate([one.passed for one in results]),
        **{check: rate([getattr(one, check) for one in results]) for check in CHECKS},
        "invented": rate([bool(one.invented) for one in results]),
        "needless": sum(len(one.needless) for one in results),
        "star": sum(one.star for one in results),
        "unrun": sum(one.unrun for one in results),
        "objectives": objectives,
    }


def report(header: dict[str, str], results: list[Score]) -> str:
    """The scores as text: a line per answer, then the summary."""
    lines = [f"{one.task}  {'pass' if one.passed else 'FAIL'}  "
             + " ".join(check for check in CHECKS if getattr(one, check))
             + (f"  invented: {', '.join(one.invented)}" if one.invented else "")
             + (f"  needless: {', '.join(one.needless)}" if one.needless else "")
             + (f"  ({one.note})" if one.note else "") for one in results]
    total = summary(results)
    lines.append(f"\n{header.get('arm', '?')} on {header.get('model', '?')}: "
                 f"{total['passed']}% passed of {total['answers']}; " + ", ".join(
                     f"{check} {total[check]}%" for check in CHECKS)
                 + f"; invented names in {total['invented']}%; needless opt-outs "
                 f"{total['needless']}; per objective {total['objectives']}")
    return "\n".join(lines)


def results_row(header: dict[str, str], split: str, results: list[Score]) -> str:
    """One row of .scratch/copilot-eval/results.md for a scored answers file."""
    total = summary(results)
    objectives = " ".join(f"{name}:{rate}" for name, rate in total["objectives"].items())
    return (f"| {header.get('date', '?')} | {header.get('files', '?')} | "
            f"{header.get('model', '?')} | {header.get('arm', '?')} | {split} | "
            f"{total['passed']} | " + " | ".join(str(total[check]) for check in CHECKS)
            + f" | {total['invented']} | {total['needless']} | {objectives} |")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("prompts", "template"):
        command = commands.add_parser(name)
        command.add_argument("--split", choices=("dev", "held_out", "all"), default="dev")
        command.add_argument("--objective", choices=sorted(OBJECTIVES))
    proxy = commands.add_parser("proxy")
    proxy.add_argument("arm", choices=sorted(ARMS))
    proxy.add_argument("--split", choices=("dev", "held_out", "all"), default="dev")
    proxy.add_argument("--objective", choices=sorted(OBJECTIVES))
    scoring = commands.add_parser("score")
    scoring.add_argument("answers", type=Path)
    scoring.add_argument("--record", type=Path)
    given = parser.parse_args(argv)
    if given.command == "prompts":
        tasks = [task for task in tasks_of(given.split)
                 if given.objective in (None, task.objective)]
        print("\n\n".join(f"## {task.id}\n\n{prompt(task)}" for task in tasks))
    elif given.command == "template":
        print(template(given.split), end="")
    elif given.command == "proxy":
        tasks = [task for task in tasks_of(given.split)
                 if given.objective in (None, task.objective)]
        print(proxy_message(given.arm, tasks))
    else:
        header, replies = read_answers(given.answers.read_text(encoding="utf-8"))
        results = scored(replies)
        print(report(header, results))
        if given.record:
            splits = {BY_ID[one.task].split for one in results}
            row = results_row(header, "+".join(sorted(splits)), results)
            with given.record.open("a", encoding="utf-8") as record:
                record.write(row + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
