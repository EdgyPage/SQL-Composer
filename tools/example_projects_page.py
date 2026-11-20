"""Write the Example projects page, `docs/main/example_projects.html`, from dev's Example
projects.

Run it on `dev` after `tools/example_project.py` has written the Example projects again:

    python tools/example_projects_page.py

A test fails while the committed page differs from what this writes.

Main holds no Example project to copy since Toolbox 8.7 (ticket 13): the user reads them here,
in place of their code. For each Example project, `example_projects/<name>/`, the page shows:

- what it is: its README.md, down to its "Running it" part, which is about running the folder;
- its folders: every file, as a tree, each a link to where the page shows it;
- each notebook's cells, each code cell with what it gave when the notebook was run here top to
  bottom, as Jupyter's Run All runs it: what it printed, any Warning, the value its last line
  gave (a result table for a DataFrame), or the message it stopped with, after which no cell
  runs. A Workflow's notebook starts with its names cell empty, so run as it is, it stops at
  the first step that needs a name;
- each Excel workbook as its text, folded, as `copilot/workbook_text.py` writes it for a
  Copilot chat: its Tables, formulas, PivotTables and Power Queries, and the order each reads
  the others in;
- each other text file, folded, to open;
- each lineage page, linked: it ships beside this page, in docs/example_projects/, at the path
  `toolbox_registry.lineage_pages` gives it.

Each notebook runs in this Python, one at a time, in a fresh copy of its Project, from its own
folder and with the Project's folder first on Python's path, as a kernel started there runs it,
its Project's own modules put away afterwards (`how_to_page.project_on_the_path`). It is
connected to the Example database, today is 2026-09-25, and a lineage's time, commit and
version are pinned (`how_to_page.times_pinned`), so the page comes out the same on every run
and every computer. The copy's folder is named in no output: `PROJECT_FOLDER` stands for it.

On dev, a notebook's setup cell connects with `import example_database` then
`connect(example_database)`. Main doesn't hold the Example database, so the page shows those
lines as a notebook of yours holds them, `connect(conn)`, with `conn` your team's connection.
"""

from __future__ import annotations

import ast
import contextlib
import datetime
import io
import json
import re
import shutil
import sys
import tempfile
import warnings
from collections.abc import Iterator
from html import escape
from pathlib import Path
from typing import NamedTuple
from unittest import mock

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "copilot"))

import how_to_page  # noqa: E402
import toolbox_registry  # noqa: E402
from example_gallery import cell_html, run_step  # noqa: E402
from example_project import PINNED_COMMIT, PINNED_TIME  # noqa: E402
from how_to_page import project_on_the_path, times_pinned  # noqa: E402
from notebook_runner import code_cells  # noqa: E402
from workbook_text import workbook_text  # noqa: E402

from sqlglot_composer import conditions, html_page  # noqa: E402

PAGE_PATH = ROOT / toolbox_registry.DOCS_ON_DEV / "example_projects.html"
EXAMPLE_PROJECTS = ROOT / toolbox_registry.EXAMPLE_PROJECTS
# The Example projects, in the order the page shows them.
PROJECTS = ("starter", "intermediate")
# How a notebook's setup cell connects on dev, and how the page shows it.
DEV_CONNECT = "connect(example_database)"
DEV_CONNECTION = f"import example_database\n{DEV_CONNECT}"
SHOWN_CONNECTION = "connect(conn)  # conn: your team's connection; here, the Example database's"
# What stands for the Project's folder in what a cell prints, in place of the copy's.
PROJECT_FOLDER = "<the Project's folder>"
# Today, while the notebooks run, as on the how-tos and the Example gallery.
TODAY = datetime.date(2026, 9, 25)
# An Example project's note, and its part the page leaves out: how to run the folder.
README = "README.md"
# What a code cell after one that stopped shows.
NOT_RUN = '<p class="muted">Not run: a cell above stopped, as Run All stops.</p>'
RUNNING_IT = "\n## Running it\n"


# --- Running a notebook ----------------------------------------------------------------------


def message_text(error: BaseException) -> str:
    """A refusal or error as Python prints it: its kind, then its message."""
    return f"{type(error).__name__}:\n" + str(error).strip("\n")


def shown_value(value: object) -> dict[str, object] | None:
    """What a cell's last line gave, as the page shows it: a DataFrame's columns and rows, any
    other value as Python shows it, or None for nothing."""
    if value is None:
        return None
    if isinstance(value, pd.DataFrame):
        rows = value.astype(object).where(value.notna(), None).values.tolist()
        return {"columns": [str(column) for column in value.columns], "rows": rows}
    return {"text": repr(value)}


class Ran(NamedTuple):
    """What one code cell gave: what it printed, its Toolbox Warnings, each as its message, the
    value its last line gave, as shown_value shows it, and the message it stopped with, or
    None when it ran to its end."""

    printed: str
    warnings: list[str]
    value: dict[str, object] | None
    stopped: str | None


def value_or_error(source: str, namespace: dict[str, object], printed: io.StringIO) -> object:
    """Run one code cell in `namespace`, as a kernel does, what it prints going to `printed`:
    the value of its last line when that line is an expression, as Jupyter shows it, the error
    it stopped with, or None. Each part runs as the Example gallery runs a step."""
    body = ast.parse(source).body
    last = body.pop() if body and isinstance(body[-1], ast.Expr) else None
    if body:
        before = run_step(ast.unparse(ast.Module(body, [])), namespace, printed)
        if isinstance(before, Exception):
            return before
    if last is None:
        return None
    return run_step(ast.unparse(last), namespace, printed)


def run_cells(notebook: Path) -> list[Ran]:
    """Run each code cell of `notebook` in turn, in one namespace, as Run All does, and give
    what each gave. The cells after one that stops don't run, and aren't listed."""
    namespace: dict[str, object] = {"__name__": "__main__"}
    ran = []
    for source in code_cells(notebook):
        printed = io.StringIO()
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            value = value_or_error(source, namespace, printed)
        toolbox_warnings = [message_text(warning.message) for warning in caught
                            if warning.category.__module__.startswith(toolbox_registry.FOLDER)]
        if isinstance(value, Exception):
            ran.append(Ran(printed.getvalue(), toolbox_warnings, None, message_text(value)))
            break
        ran.append(Ran(printed.getvalue(), toolbox_warnings, shown_value(value), None))
    return ran


def pinned_today() -> datetime.date:
    """Today, while the notebooks run: TODAY."""
    return TODAY


@contextlib.contextmanager
def in_its_folder(notebook: Path) -> Iterator[None]:
    """While it lasts, Python works in the notebook's folder, with the Project's folder, two
    up from a Table notebook, put first on the path by its own setup cell, and the Project's
    modules put away afterwards; today, and a lineage's time, commit and version, pinned as
    tools/example_project.py pins them, so a lineage a cell writes is named as the Example
    project's own."""
    # sys.path is put back afterwards, as a setup cell adds the Project's folder to it.
    with (mock.patch.object(sys, "path", list(sys.path)), contextlib.chdir(notebook.parent),
          project_on_the_path(notebook.parent),
          mock.patch.object(how_to_page, "LINEAGE_TIME", PINNED_TIME),
          mock.patch.object(how_to_page, "LINEAGE_COMMIT", PINNED_COMMIT), times_pinned(),
          mock.patch.object(conditions, "today", pinned_today)):
        yield


def run_one(project: str, notebook: str) -> list[Ran]:
    """What each cell of the notebook at `notebook`, a path inside the Example project
    `project`, gave, run in a fresh copy of the Project, each path inside the copy shown as
    PROJECT_FOLDER."""
    with tempfile.TemporaryDirectory() as temporary:
        copy = Path(temporary) / project
        shutil.copytree(EXAMPLE_PROJECTS / project, copy,
                        ignore=shutil.ignore_patterns("__pycache__"))
        with in_its_folder(copy / notebook):
            ran = run_cells(copy / notebook)
        text = json.dumps([cell._asdict() for cell in ran], default=str)
        forms = {str(copy), copy.as_posix(), str(copy.resolve()), copy.resolve().as_posix()}
        for form in sorted(forms, key=len, reverse=True):
            text = text.replace(json.dumps(form)[1:-1], PROJECT_FOLDER)
    return [Ran(**cell) for cell in json.loads(same_on_every_computer(text))]


# The classes a path a cell gives is printed with, which name the computer it ran on: the page
# is written on Windows, and CI writes it again on Linux.
PATH_CLASSES = re.compile(r"\b(?:Windows|Posix)Path\(")


def same_on_every_computer(text: str) -> str:
    """`text` with each path a cell printed shown as `Path(...)`, on any computer."""
    return PATH_CLASSES.sub("Path(", text)


def project_files(project: str) -> list[str]:
    """Each file of the Example project, as a path inside it, sorted, Python's caches left
    out."""
    folder = EXAMPLE_PROJECTS / project
    return sorted(path.relative_to(folder).as_posix() for path in folder.rglob("*")
                  if path.is_file() and "__pycache__" not in path.parts)


# --- The page --------------------------------------------------------------------------------


def shown_as_yours(text: str) -> str:
    """A file's text as a Project of yours holds it: connected with `connect(conn)`, not to
    the Example database, which main doesn't hold. A setup cell's two lines become one, with
    a comment; the call named in prose, such as a README's, becomes `connect(conn)`."""
    one_line = text.replace(DEV_CONNECTION, SHOWN_CONNECTION)
    return one_line.replace(DEV_CONNECT, "connect(conn)")


def anchor(project: str, path: str) -> str:
    """The id of a file's place on the page, such as starter/admin/run_tables.ipynb."""
    return f"{project}/{path}"


def lineage_link(project: str, path: str) -> str:
    """Where main's docs/ holds a lineage page of an Example project, from this page."""
    return f"{toolbox_registry.EXAMPLE_PROJECTS}/{project}/{path}"


def tree_html(project: str, paths: list[str]) -> str:
    """Every file of the Project, as nested lists of its folders, each file a link to its
    place on the page."""
    tree: dict[str, object] = {}
    for path in paths:
        level = tree
        for folder in path.split("/")[:-1]:
            level = level.setdefault(f"{folder}/", {})
        level[path.split("/")[-1]] = path

    def listed(level: dict[str, object]) -> str:
        items = []
        for name, below in level.items():
            if isinstance(below, dict):
                items.append(f"<li>{escape(name)}{listed(below)}</li>")
            else:
                items.append(f'<li><a href="#{escape(anchor(project, below))}">'
                             f"{escape(name)}</a></li>")
        return "<ul>" + "".join(items) + "</ul>"

    return f'<div class="tree">{listed(tree)}</div>'


def inline_markdown(text: str) -> str:
    """One line of Markdown: `code` and **bold** shown, the rest escaped."""
    shown = re.sub(r"`([^`]+)`", r"<code>\1</code>", escape(text))
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", shown)


def table_html(head: list[str], rows: list[list[str]]) -> str:
    """A table: `head`, then each of `rows`, each cell HTML already."""
    lines = ["<tr>" + "".join(f"<th>{cell}</th>" for cell in head) + "</tr>"]
    for row in rows:
        lines.append("<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>")
    return f'<div class="scroll"><table>{"".join(lines)}</table></div>'


def markdown_table_html(lines: list[str]) -> str:
    """A Markdown pipe table: its head, then its rows, the line of dashes under the head left
    out."""
    rows = []
    for line in lines:
        if not re.fullmatch(r"\|[-| ]+\|", line.strip()):
            cells = line.strip().strip("|").split("|")
            rows.append([inline_markdown(cell.strip()) for cell in cells])
    return table_html(rows[0], rows[1:])


def markdown_html(text: str) -> str:
    """Markdown, a README's or a text cell's: headings, paragraphs, "- " lists and pipe
    tables."""
    shown = []
    for block in re.split(r"\n\s*\n", text.strip()):
        if block.startswith("#"):
            level = min(len(block) - len(block.lstrip("#")) + 2, 5)
            title = inline_markdown(" ".join(block.lstrip("#").split()))
            shown.append(f"<h{level}>{title}</h{level}>")
        elif block.startswith("|"):
            shown.append(markdown_table_html(block.split("\n")))
        elif block.startswith("- "):
            items = [inline_markdown(" ".join(item[2:].split()))
                     for item in re.split(r"\n(?=- )", block)]
            shown.append("<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>")
        else:
            shown.append(f"<p>{inline_markdown(' '.join(block.split()))}</p>")
    return "\n".join(shown)


def frame_html(columns: list[str], rows: list[list[object]]) -> str:
    """A DataFrame a cell gave, as a table."""
    if not rows:
        return '<p class="muted">No rows.</p>'
    cells = []
    for row in rows:
        cells.append([cell_html(value) for value in row])
    return table_html([escape(column) for column in columns], cells)


def output_html(cell: Ran) -> str:
    """What one code cell gave: what it printed, its Warnings, its value, and the message it
    stopped with, each under a label."""
    shown = []
    printed = cell.printed.strip("\n")
    if printed.strip():
        shown.append(f'<p class="label">It prints</p><pre class="out">{escape(printed)}</pre>')
    for warning in cell.warnings:
        shown.append('<p class="label">It gives a Warning</p>'
                     f'<pre class="stop">{escape(warning)}</pre>')
    if cell.value and "columns" in cell.value:
        shown.append('<p class="label">It gives</p>'
                     + frame_html(cell.value["columns"], cell.value["rows"]))
    elif cell.value:
        shown.append('<p class="label">It gives</p>'
                     f'<pre class="out">{escape(cell.value["text"])}</pre>')
    if cell.stopped is not None:
        shown.append('<p class="label">It stops with this message</p>'
                     f'<pre class="stop">{escape(cell.stopped)}</pre>')
    return "\n".join(shown) or '<p class="muted">It shows nothing.</p>'


def notebook_html(notebook: Path, ran: list[Ran]) -> str:
    """A notebook's cells: each text cell as its Markdown, each code cell with what it gave,
    or, after a cell that stopped, a line saying it didn't run."""
    cells = json.loads(notebook.read_text(encoding="utf-8"))["cells"]
    shown, number = [], 0
    for cell in cells:
        source = shown_as_yours("".join(cell["source"]))
        if cell["cell_type"] != "code":
            shown.append(f'<div class="md">{markdown_html(source)}</div>')
            continue
        number += 1
        shown.append(f'<p class="label">Code cell {number}</p><pre>{escape(source)}</pre>')
        if number <= len(ran):
            shown.append(output_html(ran[number - 1]))
        else:
            shown.append(NOT_RUN)
    return "\n".join(shown)


# An Excel workbook's suffix: the page shows one as its text.
WORKBOOK_SUFFIX = ".xlsx"


def is_lineage(path: str) -> bool:
    """Whether a file is one of a Lineage's two, its page or its Markdown twin."""
    return "/lineage/" in f"/{path}"


def file_html(project: str, path: str) -> str:
    """One file of the Project at its place on the page: a notebook's cells and what each
    gave, a lineage page's link, a workbook's text, or any other file's text, folded."""
    source = EXAMPLE_PROJECTS / project / path
    heading = f'<h3 id="{escape(anchor(project, path))}"><code>{escape(path)}</code></h3>'
    if path.endswith(".ipynb"):
        shown = notebook_html(source, run_one(project, path))
    elif is_lineage(path) and path.endswith(".html"):
        shown = (f'<p>A Lineage page: <a href="{escape(lineage_link(project, path))}">open '
                 "it</a>, from the download's docs folder. Its Markdown twin, the .md file of "
                 "the same name, holds the same text.</p>")
    elif path == README:
        shown = (f'<p>The note at <a href="#{project}">the top of this Project\'s part</a>. '
                 "Its last part, on running the Project's folder, is left out: the download "
                 "holds the Project as this page, not as a folder.</p>")
    elif is_lineage(path) and path.endswith(".md"):
        page = lineage_link(project, path.removesuffix(".md") + ".html")
        shown = (f'<p>The Markdown twin of the Lineage page <a href="{escape(page)}">beside '
                 "it</a>: the same text, without the drawing.</p>")
    elif path.endswith(WORKBOOK_SUFFIX):
        text = workbook_text(source)
        shown = ("<p>An Excel workbook, shown as its text, as <code>python "
                 "copilot/workbook_text.py</code> writes it for a Copilot chat.</p>"
                 f"<details><summary>Show its {len(text.splitlines())} lines</summary>"
                 f"<pre>{escape(text)}</pre></details>")
    else:
        text = shown_as_yours(source.read_text(encoding="utf-8"))
        shown = (f"<details><summary>Show its {len(text.splitlines())} lines</summary>"
                 f"<pre>{escape(text)}</pre></details>")
    return f'<section class="file">{heading}\n{shown}</section>'


def about_html(project: str) -> str:
    """What the Project is: its README, down to the part about running its folder."""
    readme = (EXAMPLE_PROJECTS / project / README).read_text(encoding="utf-8")
    return markdown_html(shown_as_yours(readme.split(RUNNING_IT, 1)[0]))


def project_html(project: str) -> str:
    """One Example project: what it is, its folders, then each file."""
    paths = project_files(project)
    files = "\n".join(file_html(project, path) for path in paths)
    return (f'<section class="project" id="{project}">\n'
            f'<h2>The {project} Example project</h2>\n<div class="about">'
            f"{about_html(project)}</div>\n<h3>Its folders</h3>\n"
            + tree_html(project, paths) + f"\n{files}\n</section>")


CSS = """\
main{max-width:1180px} p,li{overflow-wrap:anywhere;line-height:1.5}
h2{font-size:19px;margin:32px 0 8px;border-bottom:2px solid var(--rule)}
h3{font-size:15px;margin:22px 0 4px}
.file{border-top:1px solid var(--faint-rule);padding-top:4px}
.md h3,.md h4,.md h5{margin:8px 0 2px}
pre{white-space:pre-wrap;margin:4px 0} pre.out{border-left:3px solid var(--rule)}
pre.stop{border-left:3px solid var(--unchecked)}
.label{margin:8px 0 0;color:var(--muted);font-size:12px;font-weight:600}
.scroll{overflow-x:auto} td,th{font-size:13px}
.tree ul{margin:0;padding-left:18px} .tree{columns:2;column-gap:24px}
@media (max-width:800px){.tree{columns:1}}
details summary{cursor:pointer;color:var(--muted)}"""


def intro_html() -> str:
    """The page's header: what an Example project is, and how the outputs were made."""
    contents = " and ".join(f'<a href="#{project}">the {project} Example project</a>'
                            for project in PROJECTS)
    return f"""<header>
<h1>{escape(toolbox_registry.PRODUCT)}: Example projects</h1>
<p>An Example project is a Project made for the Example database's tables, laid out as yours
is: made by the <code>project</code> module's Project actions, then filled in by hand. The
Example database is nine made-up tables the Toolbox's makers keep, which the download doesn't
hold, so the Example projects are shown here, not shipped as folders: read one to see what a
Project holds once filled in. To start your own, run <code>project.start()</code>, as the
README's step 1 says; the <a href="how_to.html">how-tos</a> show each table the Example
database holds.</p>
<p>For each: what it is, its folders, then each file. Each notebook was run top to bottom, as
Jupyter's Run All runs it, in a fresh copy of its Project, and each code cell shows what it
gave. A notebook connects at its top with <code>connect(conn)</code>, your team's connection;
here, it was the Example database's, which can be read but not written, so a write shows its
Hive and changes nothing. A Workflow's notebook starts with its names cell empty, so it stops
at the first step that needs a name: the how-tos run each one with names filled in, and the
<a href="workflows.html">Workflows overview</a> draws them. Each table's Lineage page is
linked, to open in your browser.</p>
<p>Jump to {contents}.</p>
</header>"""


def page_text() -> str:
    """The whole page, as one HTML string."""
    body = (intro_html() + "\n<main>\n"
            + "\n".join(project_html(project) for project in PROJECTS) + "\n</main>")
    return html_page.page(f"{toolbox_registry.PRODUCT}: Example projects", body, [CSS], [])


def main() -> int:
    PAGE_PATH.write_text(page_text(), encoding="utf-8", newline="\n")
    print(f"Wrote {PAGE_PATH.relative_to(ROOT).as_posix()}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
