"""Write the Example gallery, `sqlglot_composer/examples.html`, from the Worked examples.

Run it on `dev` after changing a docstring's example, a Statement script in
`worked_examples/statements/`, or anything that changes the Hive the Toolbox writes:

    python tools/example_gallery.py

A test fails while a committed page differs from what this writes. It runs every Statement on
the Example database, which runs on every sqlglot the Toolbox supports; the committed page is
written on the pin in requirements-dev.txt.

The page holds two kinds of Worked example:

- each Statement script in `worked_examples/statements/`. A script with `careless()` and
  `fixed()` shows the two side by side: each one's Python, Hive and result, with the Guard's
  refusal or the Warning's message under the careless one. Any other script shows each of its
  Statement functions in turn, as the steps of a common job;
- every docstring's `>>>` example, in the cheat sheet's order, step by step as the docstring
  shows it, then the Hive and the result of each Statement it hands to `to_hive(...)`,
  `run_query(...)`, `run_execute(...)` or `export_lineage(...)` (the Hive only when the
  docstring doesn't print it).

Each entry lists the Toolbox names its Python uses. Where the Example database can't run a
Statement, as it can't run week_start, a pandas result from the Worked example that builds the
same Hive stands in, labelled as such. Everything is plain HTML; a few lines of script add a
filter box.
"""

from __future__ import annotations

import ast
import contextlib
import datetime
import doctest
import importlib
import inspect
import io
import os
import re
import sys
import tempfile
import textwrap
import warnings
from collections.abc import Callable, Iterator
from html import escape
from pathlib import Path
from types import ModuleType
from typing import NoReturn
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
WORKED_EXAMPLES = ROOT / "worked_examples"
sys.path[:0] = [str(ROOT), str(WORKED_EXAMPLES)]

import toolbox_registry  # noqa: E402
import pandas as pd  # noqa: E402

import sqlglot_composer  # noqa: E402
from sqlglot_composer import conditions, example_database, kinds  # noqa: E402
from sqlglot_composer.clauses import Statement  # noqa: E402
from sqlglot_composer.python_steps import PythonStep  # noqa: E402
from sqlglot_composer.unchecked import SessionSettings, UncheckedStatement  # noqa: E402

GALLERY = ROOT / toolbox_registry.FOLDER / "examples.html"

# Today on the page, as in the doctests: last_n_days(job_runs.dt, 2) reads both of the
# Example database's days.
TODAY = datetime.date(2026, 9, 25)
PANDAS_LABEL = "computed in pandas, not by running this Hive"
PUBLIC = list(sqlglot_composer.__all__)
# The admin module's functions, imported by name rather than by the star import.
ADMIN = [f"admin.{name}" for name in sqlglot_composer.admin.__all__]
# The project module's functions, imported by name too.
ADMIN += [f"project.{name}" for name in sqlglot_composer.project.__all__]
CONSTANTS = ["TOOLBOX_VERSION", "VERSION"]
REFUSALS = (sqlglot_composer.GuardRefused, sqlglot_composer.LoadRefused)


# --- Reading the Worked examples ------------------------------------------------------------


def statement_scripts() -> list[ModuleType]:
    """Every Statement script in worked_examples/statements/, imported, in file-name order."""
    return [
        importlib.import_module(f"statements.{path.stem}")
        for path in sorted((WORKED_EXAMPLES / "statements").glob("*.py"))
    ]


def toolbox_modules() -> list[ModuleType]:
    """The Toolbox's folder, then every other Toolbox file by name."""
    stems = {path.stem for path in (ROOT / toolbox_registry.FOLDER).glob("*.py")}
    return [sqlglot_composer] + [importlib.import_module(f"sqlglot_composer.{stem}")
                                 for stem in sorted(stems) if stem != "__init__"]


def docstrings() -> list[tuple[list[str], str]]:
    """Every docstring with a >>> example, with the names it is about, in the cheat sheet's
    order.

    The two constants share the Toolbox's own docstring. A docstring that isn't a public
    name's, such as example_database.query's, comes after the public names.
    """
    found = [(CONSTANTS, inspect.cleandoc(sqlglot_composer.__doc__))]
    found += [([name], inspect.getdoc(getattr(sqlglot_composer, name)))
              for name in PUBLIC if name not in CONSTANTS]
    seen = {doc for _, doc in found}
    for module in toolbox_modules():
        for test in doctest.DocTestFinder().find(module):
            doc = inspect.cleandoc(test.docstring or "")
            if test.examples and doc not in seen:
                found.append(([test.name.removeprefix(f"{toolbox_registry.FOLDER}.")], doc))
                seen.add(doc)
    return found


def names_in(code: str) -> list[str]:
    """The Toolbox's public names that `code` uses, in the cheat sheet's order, then the admin
    module's, as admin.drop_table."""
    tree = ast.parse(code)
    used = {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}
    used |= {f"{node.value.id}.{node.attr}" for node in ast.walk(tree)
             if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
             and node.value.id in ("admin", "project")}
    return [name for name in PUBLIC + ADMIN if name in used]


# --- Running a Statement on the Example database ---------------------------------------------


def _example_today() -> datetime.date:
    """Today on the page, 2026-09-25, standing in for conditions.today."""
    return TODAY


@contextlib.contextmanager
def example_setting() -> Iterator[None]:
    """Today is 2026-09-25, and a file an example writes goes to a folder deleted afterwards."""
    real_today, here = conditions.today, os.getcwd()
    with tempfile.TemporaryDirectory() as folder, warnings.catch_warnings():
        warnings.simplefilter("ignore")
        conditions.today = _example_today
        os.chdir(folder)
        # An example that runs an Unchecked statement logs it there too, not beside this file.
        sqlglot_composer.set_admin_log(Path(folder) / "admin_log.md")
        try:
            yield
        finally:
            os.chdir(here)
            conditions.today = real_today
            sqlglot_composer.set_load_limits()
            sqlglot_composer.set_admin_log()


def what_happened(error: Exception) -> str:
    """The "What happened" line of one of the Toolbox's four-part messages."""
    found = re.search(r"What happened:\s*(.+)", str(error))
    return found.group(1).strip() if found else str(error).strip().splitlines()[0]


def result_html(s: Statement | SessionSettings | UncheckedStatement,
                pandas_result: Callable[..., pd.DataFrame] | None = None,
                which: str = "", call: str = "") -> str:
    """The result of running `s` on the Example database, or why the Example database can't.

    `pandas_result`, a function computing the same result in pandas, stands in when the
    Example database can't run the Statement. `which` says which Statement, when there are
    several, such as " of Statement 1 of 2". `call` is the function the docstring handed it
    to: run_execute sends it through the Example database's execute, and anything else through
    run_query, unless it changes something.
    """
    executes = call == "run_execute" or kinds.sent_by(s) == kinds.EXECUTE
    try:
        with contextlib.redirect_stdout(io.StringIO()):  # execute prints each line it is given
            if executes:
                result = sqlglot_composer.run_execute(s, example_database.execute)
            else:
                result = sqlglot_composer.run_query(s, example_database.query)
        if result is None:
            return _no_result_html(s, pandas_result, which)
        if isinstance(result, str):
            # explain's plan, as text: only its heading.
            heading = result.splitlines()[0] if result else ""
            return (label(f"Result{which} on the Example database, its first line")
                    + table_html(pd.DataFrame({"plan": [heading]})))
        return label(f"Result{which} on the Example database") + table_html(result)
    except (RuntimeError, ValueError) as error:
        if pandas_result is not None:
            return label(f"Result{which}, {PANDAS_LABEL}") + table_html(pandas_result())
        return f'<p class="note">No result here. {inline(what_happened(error))}</p>'


def _no_result_html(s: Statement | SessionSettings | UncheckedStatement,
                    pandas_result: Callable[..., pd.DataFrame] | None, which: str) -> str:
    """What stands for the result when running `s` gives back None."""
    if isinstance(s, SessionSettings):  # each SET line to execute
        return ('<p class="note">Sent to the Example database one SET line at a time; '
                "run_execute gives back None.</p>")
    if pandas_result is not None:
        return label(f"Result{which}, {PANDAS_LABEL}") + table_html(pandas_result())
    # A write, or other Hive that changes something, sent to execute.
    return ('<p class="note">No result here. The Example database is never written to: '
            "its execute prints the Hive's first line and changes nothing, and "
            "run_execute gives back None.</p>")


def table_html(frame: pd.DataFrame) -> str:
    if frame.empty:
        return '<p class="note">No rows.</p>'
    head = "".join(f"<th>{escape(str(column))}</th>" for column in frame.columns)
    rows = ""
    for row in frame.itertuples(index=False):
        rows += "<tr>" + "".join(f"<td>{cell_html(value)}</td>" for value in row) + "</tr>\n"
    return f'<div class="scroll"><table class="result">\n<tr>{head}</tr>\n{rows}</table></div>'


def cell_html(value: object) -> str:
    return "<i>NULL</i>" if pd.isna(value) else escape(str(value))


# --- Pieces of HTML ---------------------------------------------------------------------------


def label(text: str) -> str:
    return f'<p class="label">{escape(text)}</p>'


def code_html(text: str, kind: str = "python") -> str:
    return f'<pre class="{kind}">{escape(text.strip(chr(10)).rstrip())}</pre>'


def source_html(text: str) -> str:
    """A Worked example's Python."""
    return code_html(text)


def hive_html(text: str) -> str:
    """A Statement's Hive."""
    return code_html(text, "hive")


def inline(text: str) -> str:
    """One line of prose, with `backticks` shown as code."""
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", escape(" ".join(text.split())))


def paragraphs(text: str) -> list[str]:
    """Paragraphs, with indented code that has blank lines in it kept as one."""
    found = []
    for paragraph in re.split(r"\n\s*\n", text.strip("\n")):
        if not paragraph.strip():
            continue
        if found and is_code(paragraph) and is_code(found[-1]):
            found[-1] += "\n\n" + paragraph
        else:
            found.append(paragraph)
    return found


def is_code(paragraph: str) -> bool:
    """Whether every line is indented four spaces, or blank."""
    return all(line.startswith("    ") or not line.strip() for line in paragraph.splitlines())


def is_chart(paragraph: str) -> bool:
    """Whether a paragraph is a Mermaid chart, fenced as ```mermaid and ```, which a page shows
    as its text, as an LLM reads it, where GitHub and VS Code draw it."""
    return paragraph.startswith("```mermaid\n") and paragraph.endswith("\n```")


def prose_html(text: str, line: Callable[[str], str] = inline) -> str:
    """Prose: paragraphs, "- " lists, indented code and Mermaid charts, each line of words
    shown by `line`."""
    shown = []
    for paragraph in paragraphs(text):
        if is_chart(paragraph):
            shown.append(f'<pre class="chart">{escape(paragraph)}</pre>')
        elif is_code(paragraph):
            shown.append(code_html(textwrap.dedent(paragraph)))
        elif paragraph.startswith("- "):
            items = re.split(r"\n(?=- )", paragraph)
            shown.append("<ul>" + "".join(f"<li>{line(item[2:])}</li>" for item in items)
                         + "</ul>")
        else:
            shown.append(f"<p>{line(paragraph)}</p>")
    return "\n".join(shown)


def names_html(names: list[str]) -> str:
    listed = ", ".join(f"<code>{name}</code>" for name in names) or "none"
    return f'<p class="names">Toolbox names used: {listed}</p>'


def entry_html(entry_id: str, title: str, body: str) -> str:
    return (f'<section class="entry" id="{escape(entry_id)}">\n<h3>{title}</h3>\n{body}\n'
            "</section>")


# --- A docstring's example --------------------------------------------------------------------


def run_step(source: str, scope: dict[str, object],
             printed: io.StringIO | None = None) -> object:
    """Run one step of an example as a doctest would; return its value, or the error it raised.

    What the step prints goes to `printed`, when given, and is otherwise dropped.
    """
    with contextlib.redirect_stdout(io.StringIO() if printed is None else printed):
        try:
            tree = ast.parse(source, mode="eval")
        except SyntaxError:
            try:
                exec(compile(source, "<example>", "exec"), scope)
            except Exception as error:  # noqa: BLE001 - an example may stop, and that is shown
                return error
            return None
        try:
            return eval(compile(tree, "<example>", "eval"), scope)
        except Exception as error:  # noqa: BLE001
            return error


def output_label(source: str, value: object) -> str:
    """What a step's output is, said plainly above it."""
    if isinstance(value, REFUSALS):
        return "Refused"
    if isinstance(value, Exception):
        return "Python stops with an error"
    if "to_hive(" in source or type(value).__name__ in {"Condition", "Column", "Named"}:
        return "Hive"
    return "Python shows"


# The Toolbox functions a docstring's example hands a Statement to, which note each one.
HANDED_TO = ("to_hive", "run_query", "run_execute", "export_lineage")


def example_scope(
    handed: list[tuple[str, Statement | SessionSettings | UncheckedStatement]],
) -> dict[str, object]:
    """What the doctests have in scope; to_hive, run_query, run_execute and export_lineage
    note each Statement.

    `handed` gets one (function name, Statement) pair per Statement handed to them. A Python
    step has no Hive and runs nothing, so it isn't noted.
    """

    def noting(name: str) -> Callable[..., object]:
        def call(*statements: Statement | SessionSettings | UncheckedStatement | PythonStep,
                 **options: object) -> object:
            # run_query and run_execute take one Statement, then your call.
            given = statements[:1] if name.startswith("run_") else statements
            handed.extend((name, s) for s in given if not isinstance(s, PythonStep))
            if name == "export_lineage":
                # It would write beside its caller, this script; keep to the temporary folder.
                options.setdefault("to", Path.cwd() / "lineage" / "example.html")
            return getattr(sqlglot_composer, name)(*statements, **options)
        return call

    scope = {name: getattr(sqlglot_composer, name) for name in PUBLIC}
    scope.update(jobs=example_database.jobs, job_runs=example_database.job_runs)
    scope.update({name: noting(name) for name in HANDED_TO})
    return scope


def steps_html(parts: list[str | doctest.Example], scope: dict[str, object]
               ) -> tuple[list[str], list[str]]:
    """A docstring's example, step by step: each step's Python and what the docstring shows."""
    body, sources = [], []
    for part in parts:
        if isinstance(part, str):
            body.append(prose_html(part))
            continue
        sources.append(part.source)
        value = run_step(part.source, scope)
        body.append(code_html(part.source))
        if part.want:
            shown = part.want.replace("<BLANKLINE>", "")
            body += [label(output_label(part.source, value)), code_html(shown, "output")]
    return body, sources


def handed_html(handed: list[tuple[str, Statement | SessionSettings | UncheckedStatement]],
                pandas_results: dict[str, Callable[..., pd.DataFrame]]) -> list[str]:
    """Each Statement's Hive, unless the docstring prints it, and its result."""
    body = []
    for number, (name, s) in enumerate(handed, 1):
        hive = sqlglot_composer.to_hive(s)
        if name != "to_hive":
            body += [label(f"The Hive of the Statement given to {name}(...)"),
                     code_html(hive, "hive")]
        which = f" of Statement {number} of {len(handed)}" if len(handed) > 1 else ""
        body.append(result_html(s, pandas_results.get(hive), which, name))
    return body


def docstring_entry(names: list[str], doc: str,
                    pandas_results: dict[str, Callable[..., pd.DataFrame]],
                    used_by: dict[str, list[tuple[str, str]]]) -> str:
    first, _, rest = doc.partition("\n")
    handed = []
    scope = example_scope(handed)
    with example_setting():
        steps, sources = steps_html(doctest.DocTestParser().parse(rest), scope)
        body = [f'<p class="why">{inline(first)}</p>', *steps,
                *handed_html(handed, pandas_results), week_start_on_each_day(names)]
    used = [name for name in PUBLIC if name in names] + [
        name for name in names_in("\n".join(sources)) if name not in names]
    body.append(names_html(used))
    body.append(used_by_html([used_by.get(name, []) for name in names]))
    title = " and ".join(f"<code>{escape(name)}</code>" for name in names)
    return entry_html(names[0], title, "\n".join(block for block in body if block))


def week_start_on_each_day(names: list[str]) -> str:
    """week_start's example builds no Statement, so show what it gives on each day.

    The Example database runs it where it can; where it can't, pandas computes it.
    """
    if names != ["week_start"]:
        return ""
    from statements import regrouping

    runs = example_database.job_runs
    toolbox = sqlglot_composer
    s = toolbox.statement(
        toolbox.SELECT_DISTINCT(runs.dt, toolbox.AS(toolbox.week_start(runs.dt), "week")),
        toolbox.FROM(runs),
        toolbox.WHERE(toolbox.between(runs.dt, regrouping.FIRST_DAY, regrouping.LAST_DAY)),
    )
    shown = "week_start(job_runs.dt) on each day of the Example database"
    try:
        weeks = sqlglot_composer.run_query(s, example_database.query)
    except (RuntimeError, ValueError):
        weeks = regrouping.with_week(regrouping.every_run())[["dt", "week"]].drop_duplicates()
        shown += f", {PANDAS_LABEL}"
    return label(shown) + table_html(weeks.rename(columns={"week": "week_start(dt)"}))


def used_by_html(found: list[list[tuple[str, str]]]) -> str:
    links = []
    for per_name in found:
        links += [f'<a href="#{escape(entry_id)}">{inline(title)}</a>'
                  for entry_id, title in per_name]
    if not links:
        return ""
    return f'<p class="names">Worked examples that use it: {"; ".join(links)}</p>'


# --- A Statement script's entry ---------------------------------------------------------------


def script_parts(module: ModuleType) -> tuple[str, str, list[str]]:
    """A Statement script's title, its why, and the other paragraphs of its docstring."""
    parts = inspect.cleandoc(module.__doc__).split("\n\n")
    title = parts[0]
    why = next(p for p in parts if p.startswith("Why: "))
    return title, why, [p for p in parts[1:] if p is not why]


def script_top(module: ModuleType) -> str:
    """The top of a script: its imports and settings, between its docstring and first
    function."""
    source = Path(module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    start = tree.body[0].end_lineno
    end = next(node.lineno for node in tree.body if isinstance(node, ast.FunctionDef))
    return "\n".join(source.splitlines()[start:end - 1]).strip("\n")


# The lower Levels a Statement script may import, and how the page names each one.
LOWER_LEVELS = {"references": "The Table reference", "building_blocks": "The Building block"}


def lower_levels_of(module: ModuleType) -> list[tuple[str, Path]]:
    """The Table references and Building blocks a script imports: how each is named, its
    file."""
    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    found = []
    for node in tree.body:
        if not isinstance(node, ast.ImportFrom) or node.module is None:
            continue
        folder = node.module.split(".")[0]
        if folder in LOWER_LEVELS:
            path = WORKED_EXAMPLES / Path(*node.module.split(".")).with_suffix(".py")
            found.append((LOWER_LEVELS[folder], path))
    return found


def built_by(function: Callable[..., Statement | list[Statement]],
             **options: bool) -> tuple[Statement | list[Statement] | None, str, str]:
    """What calling `function` gives: the Statement (None if refused), and what it said.

    What it said is a heading and the message, both empty when it built quietly.
    """
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            s = function(**options)
        except sqlglot_composer.GuardRefused as refusal:
            return None, "A Guard refuses it", message_text(refusal)
        except sqlglot_composer.LoadRefused as refusal:
            return None, "A Load limit refuses it", message_text(refusal)
    if caught:
        return s, "It builds, with a Warning", message_text(caught[0].message)
    return s, "", ""


def message_text(message: Exception) -> str:
    """A refusal or Warning as Python prints it: its kind, then its four lines."""
    return f"{type(message).__name__}:\n" + str(message).strip("\n")


def opt_out_of(function: Callable[..., Statement | list[Statement]]) -> str | None:
    """The Guard's opt-out keyword a careless() takes, if it takes one."""
    keywords = [name for name, p in inspect.signature(function).parameters.items()
                if p.default is False]
    return keywords[0] if keywords else None


def statement_html(built: Statement | list[Statement], module: ModuleType, name: str) -> str:
    """The Hive and result of what a function built: one Statement, or a list of them."""
    if isinstance(built, Statement):
        return (label("Hive") + hive_html(sqlglot_composer.to_hive(built))
                + result_html(built, getattr(module, f"{name}_in_pandas", None)))
    parts = []
    for number, s in enumerate(built, 1):
        which = f" of Statement {number} of {len(built)}"
        parts += [label(f"Hive{which}"), hive_html(sqlglot_composer.to_hive(s)),
                  result_html(s, which=which)]
    return "".join(parts)


def careless_html(module: ModuleType) -> str:
    s, heading, message = built_by(module.careless)
    body = ['<h4>Careless: what most people write first</h4>',
            source_html(inspect.getsource(module.careless))]
    if message:
        body += [label(heading), code_html(message, "refusal")]
    if s is None:
        opt_out = opt_out_of(module.careless)
        if opt_out is None:
            return "\n".join(body + ['<p class="note">It has no opt-out, so there is no Hive '
                                     "to run.</p>"])
        s, _, _ = built_by(module.careless, **{opt_out: True})
        body.append(f'<p class="note">With the opt-out added, as <code>careless({opt_out}=True)'
                    "</code>, it builds, and gives the wrong result:</p>")
    return "\n".join(body) + statement_html(s, module, "careless")


def builds_statements(value: object) -> bool:
    """Whether a function's value is a Statement, or a list of them."""
    if isinstance(value, list):
        return bool(value) and all(isinstance(item, Statement) for item in value)
    return isinstance(value, Statement)


class _SentAQuery(Exception):
    """What the Example database's query raises while other_statements looks at a function."""


def _refuse_to_query(text: str) -> NoReturn:
    raise _SentAQuery(text)


def other_statements(
    module: ModuleType,
) -> list[tuple[str, Callable[..., Statement | list[Statement]]]]:
    """The script's other Statement functions besides careless() and fixed(), in file order.

    A function that sends a query, such as the every_run() a pandas twin reads, isn't one. Its
    query isn't run: the Example database's query refuses while each function is looked at.
    """
    found = []
    for name, function in inspect.getmembers(module, inspect.isfunction):
        if (function.__module__ != module.__name__ or name in {"careless", "fixed"}
                or name.endswith("_in_pandas")):
            continue
        parameters = inspect.signature(function).parameters.values()
        if all(p.default is not p.empty for p in parameters):
            with example_setting(), mock.patch.object(example_database, "query",
                                                      _refuse_to_query):
                try:
                    value = function()
                except _SentAQuery:
                    continue
            if builds_statements(value):
                found.append((name, function))
    return sorted(found, key=lambda pair: pair[1].__code__.co_firstlineno)


def is_demonstration(module: ModuleType) -> bool:
    """Whether a script shows a wrong number and its fix, with careless() and fixed()."""
    return hasattr(module, "careless") and hasattr(module, "fixed")


def function_html(heading: str, function: Callable[..., Statement | list[Statement]],
                  module: ModuleType, name: str) -> str:
    """One Statement function of a script: a heading, its source, then its Hive and result."""
    return (f"<h4>{heading}<code>{name}()</code></h4>"
            + source_html(inspect.getsource(function))
            + statement_html(function(), module, name))


def script_entry(module: ModuleType) -> tuple[str, str, list[str], str]:
    """A Statement script's entry: its id, title, the names it uses, and its HTML."""
    title, why, notes = script_parts(module)
    entry_id = module.__name__.split(".")[-1]
    top = script_top(module)
    lower = [(kind, path.name, path.parent.name, path.read_text(encoding="utf-8"))
             for kind, path in lower_levels_of(module)]
    others = other_statements(module)
    with example_setting():
        if is_demonstration(module):
            steps = ('<div class="pair">\n<div>' + careless_html(module) + "</div>\n<div>"
                     + "<h4>Fixed</h4>" + source_html(inspect.getsource(module.fixed))
                     + statement_html(module.fixed(), module, "fixed") + "</div>\n</div>")
            steps += "".join(function_html("Also in this script: ", function, module, name)
                             for name, function in others)
        else:
            steps = "".join(function_html("", function, module, name)
                            for name, function in others)
    functions = [function for _, function in others]
    if is_demonstration(module):
        functions = [module.careless, module.fixed] + functions
    names = names_in("\n".join([top] + [text for *_, text in lower]
                               + [inspect.getsource(function) for function in functions]))
    body = [f'<p class="why">{inline(why)}</p>', *(f"<p>{inline(note)}</p>" for note in notes),
            label(f"The top of its script, {entry_id}.py, a Table notebook's logic cell in a "
                  "Project"),
            source_html(top)]
    for kind, name, folder, text in lower:
        body += [label(f"{kind} it imports, {folder}/{name}"), source_html(text)]
    body += [steps, names_html(names)]
    return entry_id, title, names, entry_html(entry_id, inline(title), "\n".join(body))


# --- The page ---------------------------------------------------------------------------------


def pandas_results_by_hive(scripts: list[ModuleType]) -> dict[str, Callable[..., pd.DataFrame]]:
    """The pandas result of each Worked example Statement that has one, by the Statement's Hive.

    A docstring's Statement with the same Hive, which the Example database can't run, shows
    that result instead.
    """
    found = {}
    with example_setting():
        for module in scripts:
            for name, function in inspect.getmembers(module, inspect.isfunction):
                pandas_result = getattr(module, f"{name}_in_pandas", None)
                if pandas_result is None:
                    continue
                s, _, _ = built_by(function)
                if s is not None:
                    found[sqlglot_composer.to_hive(s)] = pandas_result
    return found


def gallery_page() -> str:
    """The whole page, as one HTML string."""
    scripts = statement_scripts()
    pandas_results = pandas_results_by_hive(scripts)
    # Common jobs first, then the wrong numbers and their fixes; each list in file-name order.
    scripts = sorted(scripts, key=is_demonstration)
    common, fixes, used_by = [], [], {}
    for module in scripts:
        entry_id, title, names, entry = script_entry(module)
        # Each entry travels as (its id, its title, its HTML).
        if is_demonstration(module):
            fixes.append((entry_id, title, entry))
        else:
            common.append((entry_id, title, entry))
        for name in names:
            used_by.setdefault(name, []).append((entry_id, title))
    # A name every Worked example uses (SELECT, statement) gets no links: they'd say nothing.
    used_by = {name: found for name, found in used_by.items() if len(found) < len(scripts)}
    documented = [(names, docstring_entry(names, doc, pandas_results, used_by))
                  for names, doc in docstrings()]
    # Only a page with a pandas result says where pandas stands in.
    every_entry = [entry for *_, entry in common + fixes] + [entry for _, entry in documented]
    or_pandas, but_not_pandas = "", ""
    if any(PANDAS_LABEL in entry for entry in every_entry):
        or_pandas = ", or computed in pandas where the Example database can't\nrun it"
        but_not_pandas = (", but not\nthe pandas that computes a result the Example database "
                          "can't run")
    return PAGE.format(
        style=STYLE,
        product=escape(toolbox_registry.PRODUCT),
        folder=escape(toolbox_registry.FOLDER),
        or_pandas=or_pandas,
        but_not_pandas=but_not_pandas,
        version=escape(sqlglot_composer.TOOLBOX_VERSION),
        worked_count=len(common) + len(fixes),
        docstring_count=len(documented),
        common_contents=contents_html(common),
        fixes_contents=contents_html(fixes),
        docstring_contents=", ".join(f'<a href="#{escape(names[0])}"><code>'
                                     f'{" and ".join(names)}</code></a>'
                                     for names, _ in documented),
        common="\n".join(entry for _, _, entry in common),
        fixes="\n".join(entry for _, _, entry in fixes),
        documented="\n".join(entry for _, entry in documented),
        filter_script=FILTER_SCRIPT,
    )


def contents_html(entries: list[tuple[str, str, str]]) -> str:
    """The list of links to entries, each shown by its title."""
    return "\n".join(f'<li><a href="#{escape(entry_id)}">{inline(title)}</a></li>'
                     for entry_id, title, _ in entries)


# The page's look, which the how-to page (tools/how_to_page.py) shares.
STYLE = ("""body{margin:0;font:15px/1.5 system-ui,sans-serif;color:#222;background:#fff}
header,main,#filter{max-width:1180px;margin:0 auto;padding:0 16px} header{padding-top:12px}
h1{font-size:22px;margin:8px 0} """
         """h2{font-size:19px;margin:32px 0 8px;border-bottom:2px solid #ddd}
h3{font-size:17px;margin:0 0 4px} h4{font-size:15px;margin:12px 0 4px}
.entry{border:1px solid #ddd;border-radius:6px;padding:12px 16px;margin:14px 0}
.entry[hidden]{display:none} .why{font-weight:600;margin:0 0 6px}
p,li,h3,h4{overflow-wrap:anywhere}
pre{background:#f6f6f6;padding:8px 10px;overflow-x:auto;margin:4px 0;font-size:13px}
pre.output,pre.hive{background:#f1f6fd} pre.refusal{background:#fdf1f1;white-space:pre-wrap}
code{font-family:ui-monospace,Consolas,monospace;font-size:13px}
.label{margin:8px 0 0;color:#555;font-size:13px;font-weight:600}
.note,.names{color:#555;font-size:14px}
.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px} .pair>div{min-width:0}
@media (max-width:800px){.pair{grid-template-columns:1fr}}
table.result{border-collapse:collapse;margin:4px 0;font-size:13px} .scroll{overflow-x:auto}
table.result th,table.result td{border:1px solid #ddd;padding:2px 8px;text-align:left}
#filter{position:sticky;top:0;z-index:1;background:#fff;padding:8px 16px;"""
         """border-bottom:1px solid #eee}
#filter input{font:inherit;padding:4px 8px;width:22em;max-width:70%}
""")

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{product} {version}: Example gallery</title>
<style>
{style}</style></head><body>
<header>
<h1>{product} {version}: Example gallery</h1>
<p>Every Worked example on one page: {worked_count} Worked examples on their own, and the
{docstring_count} examples from the Toolbox's docstrings. Each shows its Python and, for each
Statement it builds, the Hive and any result: from the Example database, the made-up tables
that ship inside the Toolbox{or_pandas}. Press Ctrl+F to search the page.</p>
<p>New to the Toolbox? Start with the <a href="how_to.html">how-tos</a>, on the page beside
this one in the <code>{folder}</code> folder: the first, Start a Project, starts one.</p>
<p>The examples take today as 2026-09-25, the day after the Example database's last day, so
<code>last_n_days(job_runs.dt, 2)</code> reads 2026-09-23 and 2026-09-24. Pasted into your
notebook, an example uses your own today, so <code>last_n_days</code> reads other days and finds
no rows here: write <code>between(job_runs.dt, "2026-09-23", "2026-09-24")</code> in its place
to get the results shown.</p>
<p>To paste a docstring's example, first run <code>from {folder} import *</code> and
<code>jobs, job_runs = example_database.jobs, example_database.job_runs</code>. The Worked
examples on their own are scripts the Toolbox's makers keep, which the download doesn't hold, so
each entry shows the Python that builds its Statements{but_not_pandas}. A script plays a Table
notebook's logic cell: in a Project, its lines would go in a Table notebook, the Table reference
it imports in <code>references/</code> and the Building block in <code>building_blocks/</code>,
and its
<code>from references ...</code> or <code>from building_blocks ...</code> line then imports it
from there. To try one in a plain notebook, paste the top of its script, with the whole file
that line imports pasted in place of the line, then the functions. The ops tables it reads come
from <code>example_database</code>, whose Table references ship inside the Toolbox.</p>
</header>
<p id="filter" hidden><label>Show only the entries holding every word:
<input type="search" placeholder="for example: row_number or LEFT_JOIN"></label>
<span id="count"></span></p>
<main>
<p><b>Worked examples of common jobs,</b> each built in steps that say why:</p>
<ul>
{common_contents}
</ul>
<p><b>Worked examples of a wrong number,</b> each showing a Statement that gives a wrong
number beside its fix:</p>
<ul>
{fixes_contents}
</ul>
<p><b>Examples from the docstrings:</b> {docstring_contents}</p>
<h2 id="common-jobs">Worked examples of common jobs</h2>
{common}
<h2 id="wrong-numbers">Worked examples of a wrong number and its fix</h2>
{fixes}
<h2 id="docstrings">Examples from the docstrings</h2>
{documented}
</main>
<script>
{filter_script}</script>
</body></html>
"""

# The script that shows the filter box, `<p id="filter" hidden>`, and keeps only the entries
# holding every word typed in it, which the how-to page (tools/how_to_page.py) shares. This is
# an ordinary Python string, so a backslash in the script is written twice.
FILTER_SCRIPT = ('const filter = document.getElementById("filter"), '
                 """box = filter.querySelector("input");
const entries = [...document.querySelectorAll(".entry")];
filter.hidden = false;
box.oninput = () => {
  const words = box.value.toLowerCase().split(/\\s+/).filter(Boolean);
  let shown = 0;
  for (const entry of entries) {
    entry.hidden = !words.every(word => entry.textContent.toLowerCase().includes(word));
    shown += !entry.hidden;
  }
  document.getElementById("count").textContent = shown + " of " + entries.length + " shown";
};
""")


def main() -> int:
    try:
        page = gallery_page()
    except RuntimeError as why:
        print(why, file=sys.stderr)
        return 1
    GALLERY.write_text(page, encoding="utf-8", newline="\n")
    print(f"Wrote {GALLERY.relative_to(ROOT).as_posix()}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
