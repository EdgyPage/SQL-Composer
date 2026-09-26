"""Write the Example gallery, `sql_composer/examples.html`, from the Worked examples.

Run it on `dev` after changing a docstring's example, a Statement script in
`worked_examples/statements/`, or anything that changes the Hive the Toolbox writes:

    python tools/example_gallery.py

A test fails while the committed page differs from what this writes. It runs every Statement
on the Example database, so it needs sqlglot 30.19.0, the pin in requirements-dev.txt.

The page holds two kinds of Worked example:

- each Statement script in `worked_examples/statements/`, with its `careless()` and `fixed()`
  Statements side by side: each one's Python, Hive and result, with the Guard's refusal or the
  Warning's message under the careless one;
- every docstring's `>>>` example, in the cheat sheet's order, step by step as the docstring
  shows it, then the Hive and the result of each Statement it hands to `to_hive(...)`,
  `run(...)` or `export_lineage(...)` (the Hive only when the docstring doesn't print it).

Each entry lists the Toolbox names its Python uses. Where the Example database can't run a
Statement, a pandas result from the Worked example that builds the same Hive stands in,
labelled as such. Everything is plain HTML; a few lines of script add a filter box.
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
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKED_EXAMPLES = ROOT / "worked_examples"
GALLERY = ROOT / "sql_composer" / "examples.html"
sys.path[:0] = [str(ROOT), str(WORKED_EXAMPLES)]

import pandas as pd  # noqa: E402
import sqlglot  # noqa: E402

import sql_composer  # noqa: E402
from sql_composer import conditions, example_database  # noqa: E402
from sql_composer.clauses import Statement  # noqa: E402

# Today on the page, as in the doctests: last_n_days(job_runs.dt, 2) reads both of the
# Example database's days.
TODAY = datetime.date(2026, 9, 25)
PANDAS_LABEL = "computed in pandas, not by running this Hive"
PUBLIC = list(sql_composer.__all__)
CONSTANTS = ["TOOLBOX_VERSION", "VERSION"]
REFUSALS = (sql_composer.GuardRefused, sql_composer.LoadRefused)


# --- Reading the Worked examples ------------------------------------------------------------


def statement_scripts() -> list:
    """Every Statement script in worked_examples/statements/, imported, in file-name order."""
    return [
        importlib.import_module(f"statements.{path.stem}")
        for path in sorted((WORKED_EXAMPLES / "statements").glob("*.py"))
    ]


def toolbox_modules() -> list:
    return [sql_composer] + [
        importlib.import_module(f"sql_composer.{path.stem}")
        for path in sorted((ROOT / "sql_composer").glob("*.py")) if path.stem != "__init__"
    ]


def docstrings() -> list[tuple[list[str], str]]:
    """Every docstring with a >>> example, with the names it is about, in the cheat sheet's order.

    The two constants share the Toolbox's own docstring. A docstring that isn't a public
    name's, such as example_database.send's, comes after the public names.
    """
    found = [(CONSTANTS, inspect.cleandoc(sql_composer.__doc__))]
    found += [([name], inspect.getdoc(getattr(sql_composer, name)))
              for name in PUBLIC if name not in CONSTANTS]
    seen = {doc for _, doc in found}
    for module in toolbox_modules():
        for test in doctest.DocTestFinder().find(module):
            doc = inspect.cleandoc(test.docstring or "")
            if test.examples and doc not in seen:
                found.append(([test.name.removeprefix("sql_composer.")], doc))
                seen.add(doc)
    return found


def names_in(code: str) -> list[str]:
    """The Toolbox's public names that `code` uses, in the cheat sheet's order."""
    used = {node.id for node in ast.walk(ast.parse(code)) if isinstance(node, ast.Name)}
    return [name for name in PUBLIC if name in used]


# --- Running a Statement on the Example database ---------------------------------------------


@contextlib.contextmanager
def example_setting():
    """Today is 2026-09-25, and a file an example writes goes to a folder deleted afterwards."""
    real_today, here = conditions.today, os.getcwd()
    with tempfile.TemporaryDirectory() as folder, warnings.catch_warnings():
        warnings.simplefilter("ignore")
        conditions.today = lambda: TODAY
        os.chdir(folder)
        try:
            yield
        finally:
            os.chdir(here)
            conditions.today = real_today
            sql_composer.set_load_limits()


def what_happened(error: Exception) -> str:
    """The "What happened" line of one of the Toolbox's four-part messages."""
    found = re.search(r"What happened:\s*(.+)", str(error))
    return found.group(1).strip() if found else str(error).strip().splitlines()[0]


def result_html(s, pandas_result=None, which: str = "") -> str:
    """The result of running `s` on the Example database, or why the Example database can't.

    `pandas_result`, a function computing the same result in pandas, stands in when the
    Example database can't run the Statement. `which` says which Statement, when there are
    several, such as " of Statement 1 of 2".
    """
    try:
        return (label(f"Result{which} on the Example database")
                + table_html(sql_composer.run(s, send=example_database.send)))
    except (RuntimeError, ValueError) as error:
        if pandas_result is not None:
            return label(f"Result{which}, {PANDAS_LABEL}") + table_html(pandas_result())
        return f'<p class="note">No result here. {inline(what_happened(error))}</p>'


def table_html(frame: pd.DataFrame) -> str:
    if frame.empty:
        return '<p class="note">No rows.</p>'
    head = "".join(f"<th>{escape(str(column))}</th>" for column in frame.columns)
    rows = "".join(
        "<tr>" + "".join(f"<td>{cell(value)}</td>" for value in row) + "</tr>\n"
        for row in frame.itertuples(index=False)
    )
    return f'<div class="scroll"><table class="result">\n<tr>{head}</tr>\n{rows}</table></div>'


def cell(value) -> str:
    return "<i>NULL</i>" if pd.isna(value) else escape(str(value))


# --- Pieces of HTML ---------------------------------------------------------------------------


def label(text: str) -> str:
    return f'<p class="label">{escape(text)}</p>'


def code_html(text: str, kind: str = "python") -> str:
    return f'<pre class="{kind}">{escape(text.strip(chr(10)).rstrip())}</pre>'


def inline(text: str) -> str:
    """One line of prose, with `backticks` shown as code."""
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", escape(" ".join(text.split())))


def prose_html(text: str) -> str:
    """Docstring prose: paragraphs, "- " lists, and indented code."""
    blocks = []
    for paragraph in re.split(r"\n\s*\n", text.strip("\n")):
        lines = paragraph.splitlines()
        if not paragraph.strip():
            continue
        if all(line.startswith("    ") for line in lines):
            blocks.append(code_html(textwrap.dedent(paragraph)))
        elif lines[0].startswith("- "):
            items = re.split(r"\n(?=- )", paragraph)
            blocks.append("<ul>" + "".join(f"<li>{inline(item[2:])}</li>" for item in items)
                          + "</ul>")
        else:
            blocks.append(f"<p>{inline(paragraph)}</p>")
    return "\n".join(blocks)


def names_html(names: list[str]) -> str:
    listed = ", ".join(f"<code>{name}</code>" for name in names) or "none"
    return f'<p class="names">Toolbox names used: {listed}</p>'


def entry_html(entry_id: str, title: str, body: str) -> str:
    return f'<section class="entry" id="{escape(entry_id)}">\n<h3>{title}</h3>\n{body}\n</section>'


# --- A docstring's example --------------------------------------------------------------------


def run_step(source: str, scope: dict):
    """Run one step of an example as a doctest would; return its value, or the error it raised."""
    with contextlib.redirect_stdout(io.StringIO()):
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


def output_label(source: str, value) -> str:
    """What a step's output is, said plainly above it."""
    if isinstance(value, REFUSALS):
        return "Refused"
    if isinstance(value, Exception):
        return "Python stops with an error"
    if "to_hive(" in source or type(value).__name__ in {"Condition", "Column", "Named"}:
        return "Hive"
    return "Python shows"


# The Toolbox functions a docstring's example hands a Statement to, which note each one.
HANDED_TO = ("to_hive", "run", "export_lineage")


def example_scope(handed: list) -> dict:
    """What the doctests have in scope; to_hive, run and export_lineage note each Statement.

    `handed` gets one (function name, Statement) pair per Statement handed to them.
    """

    def noting(name: str):
        def call(*statements, **options):
            handed.extend((name, s) for s in statements)
            if name == "export_lineage":
                # It would write beside its caller, this script; keep to the temporary folder.
                options.setdefault("to", Path.cwd() / "lineage" / "example.html")
            return getattr(sql_composer, name)(*statements, **options)
        return call

    scope = {name: getattr(sql_composer, name) for name in PUBLIC}
    scope.update(jobs=example_database.jobs, job_runs=example_database.job_runs)
    scope.update({name: noting(name) for name in HANDED_TO})
    return scope


def steps_html(parts: list, scope: dict) -> tuple[list[str], list[str]]:
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


def handed_html(handed: list, pandas_results: dict) -> list[str]:
    """Each Statement's Hive, unless the docstring prints it, and its result."""
    body = []
    for number, (name, s) in enumerate(handed, 1):
        hive = sql_composer.to_hive(s)
        if name != "to_hive":
            body += [label(f"The Hive of the Statement given to {name}(...)"),
                     code_html(hive, "hive")]
        which = f" of Statement {number} of {len(handed)}" if len(handed) > 1 else ""
        body.append(result_html(s, pandas_results.get(hive), which))
    return body


def docstring_entry(names: list[str], doc: str, pandas_results: dict, used_by: dict) -> str:
    first, _, rest = doc.partition("\n")
    handed = []
    scope = example_scope(handed)
    with example_setting():
        steps, sources = steps_html(doctest.DocTestParser().parse(rest), scope)
        body = [f'<p class="why">{inline(first)}</p>', *steps, *handed_html(handed, pandas_results),
                extra_pandas_result(names)]
    used = [name for name in PUBLIC if name in names] + [
        name for name in names_in("\n".join(sources)) if name not in names]
    body.append(names_html(used))
    body.append(used_by_html([used_by.get(name, []) for name in names]))
    title = " and ".join(f"<code>{escape(name)}</code>" for name in names)
    return entry_html(names[0], title, "\n".join(block for block in body if block))


def extra_pandas_result(names: list[str]) -> str:
    """week_start's example builds no Statement, so show what it gives each day, from pandas."""
    if names != ["week_start"]:
        return ""
    from statements import regrouping

    weeks = regrouping.with_week(regrouping.every_run())[["dt", "week"]].drop_duplicates()
    return (label(f"week_start(job_runs.dt) on each day of the Example database, {PANDAS_LABEL}")
            + table_html(weeks.rename(columns={"week": "week_start(dt)"})))


def used_by_html(found: list[list[tuple[str, str]]]) -> str:
    links = [f'<a href="#{escape(entry_id)}">{inline(title)}</a>'
             for per_name in found for entry_id, title in per_name]
    if not links:
        return ""
    return f'<p class="names">Worked examples that use it: {"; ".join(links)}</p>'


# --- A Statement script's entry ---------------------------------------------------------------


def script_parts(module) -> tuple[str, str, list[str]]:
    """A Statement script's title, its why, and the other paragraphs of its docstring."""
    paragraphs = inspect.cleandoc(module.__doc__).split("\n\n")
    title = paragraphs[0]
    why = next(p for p in paragraphs if p.startswith("Why: "))
    return title, why, [p for p in paragraphs[1:] if p is not why]


def script_top(module) -> str:
    """The top of a script: its imports and settings, between its docstring and first function."""
    source = Path(module.__file__).read_text(encoding="utf-8")
    tree = ast.parse(source)
    start = tree.body[0].end_lineno
    end = next(node.lineno for node in tree.body if isinstance(node, ast.FunctionDef))
    return "\n".join(source.splitlines()[start:end - 1]).strip("\n")


def building_blocks_of(module) -> list[Path]:
    tree = ast.parse(Path(module.__file__).read_text(encoding="utf-8"))
    return [WORKED_EXAMPLES / Path(*node.module.split(".")).with_suffix(".py")
            for node in tree.body
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
                "building_blocks.")]


def built_by(function, **options):
    """What calling `function` gives: the Statement (None if refused), and what it said.

    What it said is a heading and the message, both empty when it built quietly.
    """
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            s = function(**options)
        except sql_composer.GuardRefused as refusal:
            return None, "A Guard refuses it", message_text(refusal)
        except sql_composer.LoadRefused as refusal:
            return None, "A Load limit refuses it", message_text(refusal)
    if caught:
        return s, "It builds, with a Warning", message_text(caught[0].message)
    return s, "", ""


def message_text(message) -> str:
    """A refusal or Warning as Python prints it: its kind, then its four lines."""
    return f"{type(message).__name__}:\n" + str(message).strip("\n")


def opt_out_of(function) -> str | None:
    """The Guard's opt-out keyword a careless() takes, if it takes one."""
    keywords = [name for name, p in inspect.signature(function).parameters.items()
                if p.default is False]
    return keywords[0] if keywords else None


def statement_html(s, module, name: str) -> str:
    return (label("Hive") + code_html(sql_composer.to_hive(s), "hive")
            + result_html(s, getattr(module, f"{name}_in_pandas", None)))


def careless_html(module) -> str:
    s, heading, message = built_by(module.careless)
    body = ['<h4>Careless: what most people write first</h4>',
            code_html(inspect.getsource(module.careless))]
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


def other_statements(module) -> list[tuple[str, object]]:
    """The script's other Statement functions besides careless() and fixed(), in file order."""
    found = []
    for name, function in inspect.getmembers(module, inspect.isfunction):
        if (function.__module__ != module.__name__ or name in {"careless", "fixed"}
                or name.endswith("_in_pandas")):
            continue
        if all(p.default is not p.empty for p in inspect.signature(function).parameters.values()):
            value = function()
            if isinstance(value, Statement):
                found.append((name, function))
    return sorted(found, key=lambda pair: pair[1].__code__.co_firstlineno)


def script_entry(module) -> tuple[str, str, list[str], str]:
    """A Statement script's entry: its id, title, the names it uses, and its HTML."""
    title, why, notes = script_parts(module)
    entry_id = module.__name__.split(".")[-1]
    top = script_top(module)
    blocks = [(path.name, path.read_text(encoding="utf-8")) for path in building_blocks_of(module)]
    others = other_statements(module)
    with example_setting():
        pair = ('<div class="pair">\n<div>' + careless_html(module) + "</div>\n<div>"
                + "<h4>Fixed</h4>" + code_html(inspect.getsource(module.fixed))
                + statement_html(module.fixed(), module, "fixed") + "</div>\n</div>")
        more = "".join(
            f"<h4>Also in this script: <code>{name}()</code></h4>"
            + code_html(inspect.getsource(function))
            + statement_html(function(), module, name)
            for name, function in others
        )
    functions = [module.careless, module.fixed] + [function for _, function in others]
    names = names_in("\n".join([top] + [text for _, text in blocks]
                               + [inspect.getsource(function) for function in functions]))
    body = [f'<p class="why">{inline(why)}</p>', *(f"<p>{inline(note)}</p>" for note in notes),
            label(f"The top of its script, statements/{entry_id}.py"), code_html(top)]
    for name, text in blocks:
        body += [label(f"The Building block it imports, building_blocks/{name}"), code_html(text)]
    body += [pair, more, names_html(names)]
    return entry_id, title, names, entry_html(entry_id, inline(title), "\n".join(body))


# --- The page ---------------------------------------------------------------------------------


def pandas_results_by_hive(scripts: list) -> dict:
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
                    found[sql_composer.to_hive(s)] = pandas_result
    return found


def gallery_page() -> str:
    """The whole page, as one HTML string."""
    version = re.match(r"(\d+)\.(\d+)", sqlglot.__version__)
    if tuple(int(n) for n in version.groups()) < (30, 19):
        raise RuntimeError("The Example gallery runs the Example database, which needs sqlglot "
                           f"30.19.0 or newer; this is {sqlglot.__version__}.")
    scripts = statement_scripts()
    pandas_results = pandas_results_by_hive(scripts)
    worked, used_by = [], {}
    for module in scripts:
        entry_id, title, names, entry = script_entry(module)
        worked.append((entry_id, title, entry))
        for name in names:
            used_by.setdefault(name, []).append((entry_id, title))
    # A name every Worked example uses (SELECT, statement) gets no links: they'd say nothing.
    used_by = {name: found for name, found in used_by.items() if len(found) < len(scripts)}
    documented = [(names, docstring_entry(names, doc, pandas_results, used_by))
                  for names, doc in docstrings()]
    return PAGE.format(
        version=escape(sql_composer.TOOLBOX_VERSION),
        worked_count=len(worked),
        docstring_count=len(documented),
        worked_contents="\n".join(f'<li><a href="#{escape(i)}">{inline(t)}</a></li>'
                                  for i, t, _ in worked),
        docstring_contents=", ".join(f'<a href="#{escape(names[0])}"><code>'
                                     f'{" and ".join(names)}</code></a>'
                                     for names, _ in documented),
        worked="\n".join(entry for _, _, entry in worked),
        documented="\n".join(entry for _, entry in documented),
    )


PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SQL Composer {version}: Example gallery</title>
<style>
body{{margin:0;font:15px/1.5 system-ui,sans-serif;color:#222;background:#fff}}
header,main,#filter{{max-width:1180px;margin:0 auto;padding:0 16px}} header{{padding-top:12px}}
h1{{font-size:22px;margin:8px 0}} h2{{font-size:19px;margin:32px 0 8px;border-bottom:2px solid #ddd}}
h3{{font-size:17px;margin:0 0 4px}} h4{{font-size:15px;margin:12px 0 4px}}
.entry{{border:1px solid #ddd;border-radius:6px;padding:12px 16px;margin:14px 0}}
.entry[hidden]{{display:none}} .why{{font-weight:600;margin:0 0 6px}}
p,li,h3,h4{{overflow-wrap:anywhere}}
pre{{background:#f6f6f6;padding:8px 10px;overflow-x:auto;margin:4px 0;font-size:13px}}
pre.output,pre.hive{{background:#f1f6fd}} pre.refusal{{background:#fdf1f1;white-space:pre-wrap}}
code{{font-family:ui-monospace,Consolas,monospace;font-size:13px}}
.label{{margin:8px 0 0;color:#555;font-size:13px;font-weight:600}}
.note,.names{{color:#555;font-size:14px}}
.pair{{display:grid;grid-template-columns:1fr 1fr;gap:18px}} .pair>div{{min-width:0}}
@media (max-width:800px){{.pair{{grid-template-columns:1fr}}}}
table.result{{border-collapse:collapse;margin:4px 0;font-size:13px}} .scroll{{overflow-x:auto}}
table.result th,table.result td{{border:1px solid #ddd;padding:2px 8px;text-align:left}}
#filter{{position:sticky;top:0;z-index:1;background:#fff;padding:8px 16px;border-bottom:1px solid #eee}}
#filter input{{font:inherit;padding:4px 8px;width:22em;max-width:70%}}
</style></head><body>
<header>
<h1>SQL Composer {version}: Example gallery</h1>
<p>Every Worked example on one page: {worked_count} Worked examples on their own, and the
{docstring_count} examples from the Toolbox's docstrings. Each shows its Python and, for each
Statement it builds, the Hive and any result: from the Example database, the three made-up
tables that ship inside the Toolbox, or computed in pandas where the Example database can't
run it. Press Ctrl+F to search the page.</p>
<p>The examples take today as 2026-09-25, the day after the Example database's two days, so
<code>last_n_days(job_runs.dt, 2)</code> reads 2026-09-23 and 2026-09-24. Pasted into your
notebook, an example uses your own today, so <code>last_n_days</code> reads other days and finds
no rows here: write <code>between(job_runs.dt, "2026-09-23", "2026-09-24")</code> in its place
to get the results shown.</p>
<p>To paste a docstring's example, first run <code>from sql_composer import *</code> and
<code>jobs, job_runs = example_database.jobs, example_database.job_runs</code>. The Worked
examples on their own are scripts kept where the Toolbox is written, not in the
<code>sql_composer</code> folder. Each entry shows the Python that builds its Statements, but not
the pandas that computes a result the Example database can't run. To try one, paste the top of
its script, with the Building block it imports pasted in place of its
<code>from building_blocks ...</code> line, then the functions.</p>
</header>
<p id="filter" hidden><label>Show only the entries holding every word:
<input type="search" placeholder="for example: row_number or LEFT_JOIN"></label>
<span id="count"></span></p>
<main>
<p><b>Worked examples on their own,</b> each showing a Statement that gives a wrong number
and its fix:</p>
<ul>
{worked_contents}
</ul>
<p><b>Examples from the docstrings:</b> {docstring_contents}</p>
<h2 id="worked-examples">Worked examples on their own</h2>
{worked}
<h2 id="docstrings">Examples from the docstrings</h2>
{documented}
</main>
<script>
const filter = document.getElementById("filter"), box = filter.querySelector("input");
const entries = [...document.querySelectorAll(".entry")];
filter.hidden = false;
box.oninput = () => {{
  const words = box.value.toLowerCase().split(/\\s+/).filter(Boolean);
  let shown = 0;
  for (const entry of entries) {{
    entry.hidden = !words.every(word => entry.textContent.toLowerCase().includes(word));
    shown += !entry.hidden;
  }}
  document.getElementById("count").textContent = shown + " of " + entries.length + " shown";
}};
</script>
</body></html>
"""


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
