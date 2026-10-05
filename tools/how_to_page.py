"""Write an Edition's how-to page, `how_to.html` in its folder, from the how-tos.

Run it on `dev` after changing a how-to in `worked_examples/how_to/`, or anything that changes
what a how-to's steps show:

    python tools/how_to_page.py
    python tools/how_to_page.py --edition spark

The first writes `sqlglot_composer/how_to.html`, and the second `spark_composer/how_to.html`,
whose Example database needs Java 17. A test fails while a committed page differs from what
this writes.

A how-to walks through one job from start to finish, as one fresh notebook. Each is a file
`worked_examples/how_to/NN_slug.py`: NN is its number, and the page's link to it is `#slug`.
The file holds a docstring, written for sqlglot Composer as the Worked examples are (Spark
Composer's page names its own folder), and any pandas stand-ins (below). The docstring is laid
out like this:

    Start a notebook                    <- the title, on line 1

    For: Getting started                <- Getting started (how-tos 1-18) or Intermediate (19-30)

    ## Goal                             <- the six fixed headings, each once, in this order:
    ## When you'd use it                   Goal, When you'd use it, Steps, Check it worked,
    ## Steps                               Common mistakes and Next
    ### Import the Toolbox               <- a step, or a mistake, under its heading
    >>> from sqlglot_composer import *  <- Python that runs, as in a doctest

Under the headings go:

- prose: paragraphs, "- " lists, `code` in backticks, and links, written [text](#slug) to
  another how-to and [text](examples.html#entry) to an entry of the Example gallery;
- `>>>` steps, with what each shows written under it as a doctest has it. They run in order, as
  one notebook, and tests/test_how_tos.py runs each how-to as a doctest. The page shows what
  each step really gives, run again while it is written: what it prints (the Hive, when it
  calls to_hive or show_hive), a result table for a DataFrame, the refusal or Warning it stops
  with, and each file it writes: a .py or .md file in full, and an .html file by name;
- indented code, shown but not run, for what works only at work, such as your own send;
- a block that only one Edition's page shows, as written, between a line
  `[sqlglot_composer only]` or `[spark_composer only]` and a line `[end]`: for what differs,
  such as the send, or a mistake only one Edition's users make. It holds prose, indented code
  and `>>>` steps, but no heading and no other block. Its steps run only for its own Edition.

Where sqlglot Composer's Example database can't run a Statement's Hive, such as one with
row_number or week_start, the how-to's file gives a pandas stand-in after its docstring: a
function `NAME_in_pandas()`, which returns the DataFrame the Statement the steps call `NAME`
gives, as the Worked examples' `*_in_pandas` functions do. When the Example database's send
can't run that Statement's Hive, the stand-in's DataFrame comes back instead, both on the page,
labelled as computed in pandas as the Example gallery labels it, and in the doctest. Spark
Composer's Example database runs it, and the doctest's output, the same on both Editions, holds
the stand-in to Spark's result.

While the steps run, today is 2026-09-25, as on the Example gallery, and each how-to works in a
folder of its own, deleted afterwards. A lineage's time, your scripts' commit and the Toolbox
version are pinned, so the page comes out the same on every run.

A how-to links only to how-tos and the Example gallery: links to the example projects and the
templates come with tickets 11 and 13, once ticket 14 ships them on `main`, and check_links
widens to them then.
"""

from __future__ import annotations

import ast
import contextlib
import datetime
import doctest
import importlib.util
import io
import os
import re
import sys
import textwrap
import warnings
from dataclasses import dataclass, field
from html import escape, unescape
from pathlib import Path
from typing import Callable, NamedTuple
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import editions  # noqa: E402

if __name__ == "__main__":
    # Before any Toolbox import: `import sqlglot_composer` then gives the Edition asked for.
    editions.use(editions.edition_on_command_line(sys.argv))

import pandas as pd  # noqa: E402

import sqlglot_composer  # noqa: E402
from composer_core import example_database, lineage  # noqa: E402
from composer_core.clauses import Statement  # noqa: E402
from example_gallery import (  # noqa: E402
    EDITION,
    FILTER_SCRIPT,
    PANDAS_LABEL,
    ROOT,
    STYLE,
    code_html,
    example_setting,
    hive_html,
    inline,
    label,
    message_text,
    names_html,
    names_in,
    run_step,
    table_html,
)
from sqlglot_composer import engine  # noqa: E402

HOW_TOS = ROOT / "worked_examples" / "how_to"
PAGE_PATH = ROOT / EDITION.folder / "how_to.html"
GALLERY = ROOT / EDITION.folder / "examples.html"

HEADINGS = ("Goal", "When you'd use it", "Steps", "Check it worked", "Common mistakes", "Next")


class Group(NamedTuple):
    """Getting started how-tos or Intermediate how-tos: what a how-to's `For:` line names."""

    name: str
    # The id of its heading on the page, and its badges' class.
    id: str
    # The numbers of the how-tos it holds.
    numbers: range
    # What its contents list says it is for.
    for_what: str


GROUPS = (
    Group("Getting started", "getting-started", range(1, 19),
          "your first notebooks: from one Statement to a daily pipeline and its Lineage"),
    Group("Intermediate", "intermediate", range(19, 31),
          "work over many days and many tables: snapshots, rollups, layered pipelines, quality "
          "checks and testing"),
)
GROUP_NAMED = {group.name: group for group in GROUPS}
# What a lineage written on the page says of when, from which commit and with which Toolbox.
LINEAGE_TIME = datetime.datetime(2026, 9, 25, 9, 0)
LINEAGE_COMMIT = "1a2b3c4"
# What the Example database says when its executor can't run a query's Hive.
CANT_RUN = "The Example database can't run this Hive"


class HowToRefused(Exception):
    """A how-to can't go on the page as written; the message says what to change."""


# --- Reading a how-to ------------------------------------------------------------------------


@dataclass(frozen=True)
class HowTo:
    number: int
    slug: str
    title: str
    # The name of its Group: Getting started or Intermediate.
    group: str
    # The rest of its docstring, for this Edition's page: see edition_text.
    text: str
    # Its pandas stand-ins, by the name of the Statement each stands in for: see stand_ins_of.
    stand_ins: dict = field(default_factory=dict, compare=False)


def how_to_paths() -> list[Path]:
    """Every how-to's file, in number order."""
    return sorted(HOW_TOS.glob("[0-9][0-9]_*.py"))


def slug_of(path: Path) -> str:
    """A how-to's id on the page: its file's name without the number."""
    return path.stem[3:]


def docstring_of(path: Path) -> str:
    doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8")))
    if not doc:
        raise HowToRefused(f"{path.name} has no docstring, and a how-to is its docstring.")
    return doc


def stand_ins_of(path: Path) -> dict[str, Callable[[], pd.DataFrame]]:
    """A how-to's pandas stand-ins: each function `NAME_in_pandas` in its file, by NAME."""
    spec = importlib.util.spec_from_file_location(f"how_to_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return {name.removesuffix("_in_pandas"): function
            for name, function in vars(module).items()
            if name.endswith("_in_pandas") and callable(function)}


# A block only one Edition's page shows, and the lines that open or close one.
ONLY = re.compile(r"^\[(\w+) only\]\n(.*?)^\[end\]\n?", re.MULTILINE | re.DOTALL)
MARKER = re.compile(r"^\[(\w+ only|end)\]$", re.MULTILINE)
# The same block, in the text edition_text gives with `marked`.
MARKED = re.compile(r"^\[only\]\n(.*?)^\[end\]\n?", re.MULTILINE | re.DOTALL)


def edition_text(doc: str, edition: editions.Edition, marked: bool = False) -> str:
    """A how-to's text for `edition`: named for its folder, with only its own Edition's blocks.

    Everything outside a block is written for sqlglot Composer and is named for `edition`; a
    block is kept as written, or left out on the other Edition's page. `marked` keeps a block's
    edges, as lines `[only]` and `[end]`, for the page to show where it is.
    """
    pieces, outside, at = [], [], 0
    for found in ONLY.finditer(doc):
        folder, body = found.groups()
        if folder not in editions.EDITIONS:
            raise HowToRefused(f"[{folder} only] names no Edition: write [sqlglot_composer only] "
                               "or [spark_composer only].")
        if re.search(r"^#", body, re.MULTILINE) or MARKER.search(body):
            raise HowToRefused(f"A [{folder} only] block holds a heading or another block. It "
                               "may hold only prose, indented code and >>> steps: put the "
                               "heading outside it, and give each Edition's text a block of "
                               "its own.")
        outside.append(doc[at:found.start()])
        pieces.append(editions.named_for(edition, outside[-1]))
        if folder == edition.folder:
            pieces.append(f"[only]\n{body}[end]\n" if marked else body)
        at = found.end()
    outside.append(doc[at:])
    pieces.append(editions.named_for(edition, outside[-1]))
    stray = [found for piece in outside for found in MARKER.findall(piece)]
    if stray:
        raise HowToRefused(f"A line [{stray[0]}] opens or closes no block: a block is a line "
                           "[sqlglot_composer only] or [spark_composer only], then its text, "
                           "then a line [end].")
    return "".join(pieces)


LAYOUT = re.compile(r"(?P<title>[^\n]+)\n\nFor: (?P<group>[^\n]+)\n\n(?P<rest>.*)", re.DOTALL)


def read_how_to(path: Path, edition: editions.Edition = EDITION) -> HowTo:
    """A how-to, read from its file, for `edition`'s page."""
    laid_out = LAYOUT.fullmatch(docstring_of(path))
    if laid_out is None:
        raise HowToRefused(f"{path.name} must start with its title on line 1 and a line such as "
                           "`For: Getting started` on line 3, each followed by a blank line.")
    name, number = laid_out["group"], int(path.stem[:2])
    if name not in GROUP_NAMED:
        raise HowToRefused(f"{path.name} says `For: {name}`: write "
                           f"{' or '.join(f'`For: {group.name}`' for group in GROUPS)}.")
    numbers = GROUP_NAMED[name].numbers
    if number not in numbers:
        raise HowToRefused(f"{path.name} is how-to {number}, but the {name} how-tos are "
                           f"{numbers.start} to {numbers.stop - 1}.")
    return HowTo(number, slug_of(path), laid_out["title"], name,
                 edition_text(laid_out["rest"], edition, marked=True), stand_ins_of(path))


def sections(how_to: HowTo) -> list[tuple[str, str]]:
    """A how-to's six sections, as (heading, text), refused unless they are the fixed ones."""
    parts = re.split(r"^## (.+)\n", how_to.text, flags=re.MULTILINE)
    found = list(zip(parts[1::2], parts[2::2]))
    if parts[0].strip() or [heading for heading, _ in found] != list(HEADINGS):
        raise HowToRefused(f"How-to {how_to.number} must have the headings "
                           f"{', '.join('## ' + heading for heading in HEADINGS)}, each once, in "
                           "that order, with nothing before the first.")
    return found


# --- Prose ----------------------------------------------------------------------------------


LINK = re.compile(r"\[([^\]]+)\]\(([^)\s]+)\)")


def linked(text: str) -> str:
    """One line of prose, with `backticks` shown as code and [text](target) as a link."""
    return LINK.sub(r'<a href="\2">\1</a>', inline(text))


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
    return all(line.startswith("    ") or not line.strip() for line in paragraph.splitlines())


def prose_html(text: str) -> str:
    """Prose: paragraphs, "- " lists and indented code."""
    shown = []
    for paragraph in paragraphs(text):
        if is_code(paragraph):
            shown.append(code_html(textwrap.dedent(paragraph)))
        elif paragraph.startswith("- "):
            items = re.split(r"\n(?=- )", paragraph)
            shown.append("<ul>" + "".join(f"<li>{linked(item[2:])}</li>" for item in items)
                         + "</ul>")
        else:
            shown.append(f"<p>{linked(paragraph)}</p>")
    return "\n".join(shown)


# --- A step, run -----------------------------------------------------------------------------


@dataclass
class Notebook:
    """A how-to's steps, run in order as one notebook."""

    # What the steps have made, by name.
    scope: dict
    # The folder the steps run in, where any file they write goes.
    folder: Path
    # Each step's Python, in order.
    sources: list = field(default_factory=list)
    # The Hive of each query a pandas stand-in answered: see pandas_standing_in.
    answered: list = field(default_factory=list)


@contextlib.contextmanager
def pandas_standing_in(stand_ins: dict, scope: dict, answered: list):
    """While it lasts, a query the Example database can't run, from a Statement a pandas
    stand-in is for, gets the stand-in's DataFrame back.

    `stand_ins` are a how-to's, by the name of their Statement in `scope`, the steps' names.
    Each query a stand-in answers has its Hive added to `answered`.
    """
    real_send = example_database.send

    def send(hive):
        try:
            return real_send(hive)
        except RuntimeError as error:
            if CANT_RUN not in str(error):
                raise
            for name, in_pandas in stand_ins.items():
                s = scope.get(name)
                if isinstance(s, Statement) and sqlglot_composer.to_hive(s) == hive:
                    answered.append(hive)
                    return in_pandas()
            raise

    with mock.patch.object(example_database, "send", send):
        yield


def files_in(folder: Path) -> dict[Path, bytes]:
    return {path: path.read_bytes() for path in folder.rglob("*") if path.is_file()}


def written_files_html(folder: Path, before: dict, after: dict) -> str:
    """Each file a step writes in `folder`: a .py or .md file in full, any other by name.

    `before` and `after` are what files_in gave before and after the step.
    """
    written = sorted((path for path, text in after.items() if before.get(path) != text),
                     key=lambda path: (path.suffix not in (".py", ".md"), path.as_posix()))
    shown = []
    for path in written:
        name = path.relative_to(folder).as_posix()
        if path.suffix in (".py", ".md"):
            kind = "python" if path.suffix == ".py" else "file"
            shown += [label(f"It writes {name}"),
                      code_html(path.read_text(encoding="utf-8"), kind)]
        elif path.suffix == ".html":
            shown.append(f'<p class="note">It writes <code>{escape(name)}</code> too, a page '
                         "to open in your browser.</p>")
        else:
            shown.append(f'<p class="note">It writes <code>{escape(name)}</code> too.</p>')
    return "\n".join(shown)


def printed_html(source: str, printed: str) -> str:
    """What a step prints: Hive, when it prints the Hive."""
    if not printed.strip():
        return ""
    if "show_hive(" in source:
        return label("Hive, ready to paste") + hive_html(printed)
    if "to_hive(" in source:
        return label("Hive") + hive_html(printed)
    return label("Python prints") + code_html(printed, "output")


def value_html(source: str, value, in_pandas: bool) -> str:
    """What a step gives: a result table, the message it stops with, or the value Python shows.

    `in_pandas` says a pandas stand-in gave its result, in place of the Example database.
    """
    if value is None:
        return ""
    if isinstance(value, Exception):
        return label("Python stops with this message") + code_html(message_text(value),
                                                                   "refusal")
    if isinstance(value, pd.DataFrame):
        on = (f"Result, {PANDAS_LABEL}" if in_pandas
              else "Result on the Example database" if "example_database.send" in source
              else "Python shows")
        return label(on) + table_html(value)
    return label("Python shows") + code_html(repr(value), "output")


def toolbox_warnings(caught: list) -> list:
    """The Toolbox's own Warnings among those a step gave."""
    return [warning.message for warning in caught
            if warning.category.__module__.startswith(editions.CORE)]


def step_output_html(source: str, notebook: Notebook) -> str:
    """Run one `>>>` step: what it prints, warns, gives and writes, or "" if nothing."""
    before, printed, answered = files_in(notebook.folder), io.StringIO(), len(notebook.answered)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        value = run_step(source, notebook.scope, printed)
    shown = [printed_html(source, printed.getvalue())]
    shown += [label("It builds, with a Warning") + code_html(message_text(message), "refusal")
              for message in toolbox_warnings(caught)]
    shown += [value_html(source, value, len(notebook.answered) > answered),
              written_files_html(notebook.folder, before, files_in(notebook.folder))]
    html = "\n".join(part for part in shown if part)
    # The folder's name is made up afresh on every run.
    for differs in (notebook.folder.name, "WindowsPath(", "PosixPath("):
        if differs in html:
            raise HowToRefused(f"The step {source.strip()!r} shows {differs}, which differs "
                               "from one computer to another, so the page would too. Show a "
                               "path's .name, or a path relative to the folder it works in.")
    return html


def steps_html(text: str, notebook: Notebook) -> str:
    """Prose and `>>>` steps, run in `notebook`.

    Steps in a row that show nothing share one block of Python with the step after them.
    """
    shown, waiting = [], []
    for part in doctest.DocTestParser().parse(text):
        if isinstance(part, str):
            if part.strip() and waiting:
                shown.append(code_html("".join(waiting)))
                waiting = []
            shown.append(prose_html(part))
            continue
        notebook.sources.append(part.source)
        waiting.append(part.source)
        output = step_output_html(part.source, notebook)
        if output:
            shown += [code_html("".join(waiting)), output]
            waiting = []
    if waiting:
        shown.append(code_html("".join(waiting)))
    return "\n".join(block for block in shown if block)


def chunk_html(text: str, notebook: Notebook) -> str:
    """Text under one heading, with each block only this Edition's page shows marked as such."""
    shown = []
    for position, piece in enumerate(MARKED.split(text)):
        html = steps_html(piece, notebook)
        if position % 2 and html:  # a block only this Edition's page shows
            html = f'<div class="only">\n{html}\n</div>'
        shown.append(html)
    return "\n".join(block for block in shown if block)


def section_html(text: str, notebook: Notebook) -> str:
    """One fixed heading's text: its steps or mistakes each under its own heading."""
    parts = re.split(r"^### (.+)\n", text, flags=re.MULTILINE)
    shown = [chunk_html(parts[0], notebook)]
    for heading, chunk in zip(parts[1::2], parts[2::2]):
        shown += [f"<h5>{linked(heading)}</h5>", chunk_html(chunk, notebook)]
    return "\n".join(block for block in shown if block)


@contextlib.contextmanager
def lineage_pinned():
    """A lineage's time, your scripts' commit and the Toolbox version, the same on every run.

    Without a notebook's name in the environment, a lineage is named as from a notebook.
    """
    version = f"{EDITION.product} {sqlglot_composer.TOOLBOX_VERSION}"
    with (mock.patch.object(lineage, "_now", lambda: LINEAGE_TIME),
          mock.patch.object(lineage, "scripts_commit", lambda folder: LINEAGE_COMMIT),
          mock.patch.object(lineage, "_version", lambda: version),
          mock.patch.dict(os.environ)):
        os.environ.pop("JPY_SESSION_NAME", None)
        yield


def how_to_html(how_to: HowTo) -> str:
    """A how-to's entry on the page, its steps run in a fresh notebook's scope."""
    shown = []
    with example_setting(), lineage_pinned():
        notebook = Notebook(scope={}, folder=Path.cwd())
        with pandas_standing_in(how_to.stand_ins, notebook.scope, notebook.answered):
            for heading, text in sections(how_to):
                shown += [f"<h4>{escape(heading)}</h4>", section_html(text, notebook)]
    for name in how_to.stand_ins:
        if not isinstance(notebook.scope.get(name), Statement):
            raise HowToRefused(f"How-to {how_to.number} has {name}_in_pandas, but none of its "
                               f"steps makes a Statement {name} for it to stand in for.")
    group = GROUP_NAMED[how_to.group]
    badge = f'<span class="badge {group.id}">{escape(group.name)}</span>'
    return (f'<section class="entry" id="{how_to.slug}">\n'
            f"<h3>{how_to.number}. {inline(how_to.title)} {badge}</h3>\n"
            + "\n".join(block for block in shown if block) + "\n"
            + names_html(names_in("\n".join(notebook.sources))) + "\n</section>")


# --- The page --------------------------------------------------------------------------------


def gallery_ids() -> set[str]:
    """The id of each entry on the Example gallery beside the page."""
    page = GALLERY.read_text(encoding="utf-8") if GALLERY.exists() else ""
    return {unescape(found) for found in re.findall(r'<section class="entry" id="([^"]+)"', page)}


def check_links(page: str) -> None:
    """Refuse a link to anything but a place on the page or an entry of the Example gallery."""
    on_page = set(re.findall(r'\bid="([^"]+)"', page))
    entries = gallery_ids()
    for target in re.findall(r'href="([^"]*)"', page):
        page_name, _, place = unescape(target).partition("#")
        if (page_name == "" and place in on_page) or (
                page_name == "examples.html" and (not place or place in entries)):
            continue
        raise HowToRefused(f"A how-to links to {target}, which is neither a how-to nor an entry "
                           "of the Example gallery. Link to [text](#slug) or "
                           "[text](examples.html#entry).")


def contents_html(how_tos: list[HowTo]) -> str:
    if not how_tos:
        return '<p class="note">None yet.</p>'
    return "<ul>\n" + "\n".join(
        f'<li data-for="{how_to.slug}"><a href="#{how_to.slug}">{how_to.number}. '
        f"{inline(how_to.title)}</a></li>" for how_to in how_tos) + "\n</ul>"


def how_to_page() -> str:
    """The whole page, as one HTML string."""
    cannot_run = engine.example_database_cannot_run()
    if cannot_run is not None:
        raise RuntimeError(f"The how-to page runs every step on the Example database, and "
                           f"{cannot_run}.")
    how_tos = [read_how_to(path) for path in how_to_paths()]
    numbers = [how_to.number for how_to in how_tos]
    if len(set(numbers)) != len(numbers):
        raise HowToRefused("Two how-tos have the same number: give each its own.")
    groups, contents = [], []
    for group in GROUPS:
        in_group = [how_to for how_to in how_tos if how_to.group == group.name]
        contents.append(f'<div>\n<p><b><a href="#{group.id}">{group.name}</a></b>: '
                        f"{inline(group.for_what)}.</p>\n{contents_html(in_group)}\n</div>")
        entries = [how_to_html(how_to) for how_to in in_group] or [
            f'<p class="note">No {group.name.lower()} how-tos yet.</p>']
        groups.append(f'<h2 id="{group.id}">{group.name}</h2>\n' + "\n".join(entries))
    filled = {
        "STYLE": STYLE + HOW_TO_STYLE,
        "PRODUCT": escape(EDITION.product),
        "FOLDER": escape(EDITION.folder),
        "VERSION": escape(sqlglot_composer.TOOLBOX_VERSION),
        "CONTENTS": "\n".join(contents),
        "GROUPS": "\n".join(groups),
        "SCRIPT": FILTER_SCRIPT + HOW_TO_SCRIPT,
    }
    # One pass, so text that happens to look like a marker is never filled in itself.
    page = re.sub(r"__([A-Z]+)__", lambda found: filled[found[1]], PAGE)
    check_links(page)
    return page


HOW_TO_STYLE = """h5{font-size:15px;margin:16px 0 4px;color:#333}
.groups{display:grid;grid-template-columns:1fr 1fr;gap:18px}
@media (max-width:800px){.groups{grid-template-columns:1fr}}
.groups ul{margin:4px 0}
.badge{font-size:12px;font-weight:600;border-radius:10px;padding:1px 8px;margin-left:6px;vertical-align:2px}
.badge.getting-started{color:#1f5a2a;background:#e6f4e8} .badge.intermediate{color:#6b4500;background:#fbefdc}
.only{margin:0}
pre.file{white-space:pre-wrap}
.code{position:relative} .code pre{padding-right:64px}
.copy{position:absolute;top:4px;right:4px;font:12px system-ui,sans-serif;padding:1px 8px;cursor:pointer}
"""

# What the how-to page's script adds to the Example gallery's, FILTER_SCRIPT: each how-to's
# line in the contents hides with it, and each block of Python and Hive gets a Copy button.
HOW_TO_SCRIPT = """box.addEventListener("input", () => {
  for (const item of document.querySelectorAll("[data-for]")) {
    item.hidden = document.getElementById(item.dataset.for).hidden;
  }
});
for (const pre of document.querySelectorAll("pre.python, pre.hive")) {
  const text = pre.textContent, holder = document.createElement("div");
  const button = document.createElement("button");
  button.type = "button";
  button.className = "copy";
  button.textContent = "Copy";
  button.onclick = () => Promise.resolve().then(() => navigator.clipboard.writeText(text)).then(
    () => { button.textContent = "Copied"; },
    () => { window.getSelection().selectAllChildren(pre); button.textContent = "Press Ctrl+C"; });
  holder.className = "code";
  pre.replaceWith(holder);
  holder.append(pre, button);
}
"""

# The page. how_to_page fills in each __NAME__ marker.
PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__PRODUCT__ __VERSION__: How-tos</title>
<style>
__STYLE__</style></head><body>
<header>
<h1>__PRODUCT__ __VERSION__: How-tos</h1>
<p>Each how-to walks through one job from start to finish: its goal, when you'd use it, its
steps, how to check it worked, the mistakes people make first, and what to read next. Its steps
are one notebook: paste them in order, starting with the import. Each step shows its Python,
then what it gives: its Hive (ready to paste into another program), its result on the Example
database, or a file it writes. The Example database is six made-up tables that ship inside the
Toolbox. Every Hive, result, refusal and Warning here comes from running the steps.</p>
<p>The Example database holds two days of <code>ops.job_runs</code>, 2026-09-23 and
2026-09-24 (its newer tables hold 14 days), and the steps here were run as if today were
2026-09-25. In your own notebook, <code>last_n_days</code> counts back from your real today and
finds no rows on the Example database: write <code>between</code> with the dates instead.</p>
<p>The <a href="examples.html">Example gallery</a>, beside this page in the
<code>__FOLDER__</code> folder, holds every Worked example, and the how-tos link to it.</p>
</header>
<p id="filter" hidden><label>Show only the how-tos holding every word:
<input type="search" placeholder="for example: show_hive or send"></label>
<span id="count"></span></p>
<main>
<nav class="groups">
__CONTENTS__
</nav>
__GROUPS__
</main>
<script>
__SCRIPT__</script>
</body></html>
"""


def main() -> int:
    try:
        page = how_to_page()
    except (RuntimeError, HowToRefused, editions.SwapRefused) as why:
        print(why, file=sys.stderr)
        return 1
    PAGE_PATH.write_text(page, encoding="utf-8", newline="\n")
    print(f"Wrote {PAGE_PATH.relative_to(ROOT).as_posix()}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
