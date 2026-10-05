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
The file holds only a docstring, written for sqlglot Composer as the Worked examples are (Spark
Composer's page names its own folder). It is laid out like this:

    Start a notebook                    <- the title, on line 1

    Level: Getting started              <- Getting started (how-tos 1-18) or Intermediate (19-30)

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
  such as the send. It holds prose and indented code only.

While the steps run, today is 2026-09-25, as on the Example gallery, and each how-to works in a
folder of its own, deleted afterwards. A lineage's time, your scripts' commit and the Toolbox
version are pinned, so the page comes out the same on every run.
"""

from __future__ import annotations

import ast
import contextlib
import datetime
import doctest
import io
import os
import re
import sys
import textwrap
import warnings
from dataclasses import dataclass
from html import escape, unescape
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import editions  # noqa: E402

if __name__ == "__main__":
    # Before any Toolbox import: `import sqlglot_composer` then gives the Edition asked for.
    editions.use(editions.edition_on_command_line(sys.argv))

import pandas as pd  # noqa: E402

import sqlglot_composer  # noqa: E402
from composer_core import lineage  # noqa: E402
from example_gallery import (  # noqa: E402
    EDITION,
    REFUSALS,
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
# Each level, by the id of its heading on the page, with the how-to numbers it holds and what
# its contents list says it is for.
LEVELS = {
    "Getting started": ("getting-started", range(1, 19),
                        "your first notebooks: from one Statement to a daily pipeline and its "
                        "lineage"),
    "Intermediate": ("intermediate", range(19, 31),
                     "work over many days and many tables: snapshots, rollups, layered "
                     "pipelines, quality checks and testing"),
}
# What a lineage written on the page says of when, from which commit and with which Toolbox.
LINEAGE_TIME = datetime.datetime(2026, 9, 25, 9, 0)
LINEAGE_COMMIT = "1a2b3c4"


class HowToRefused(Exception):
    """A how-to can't go on the page as written; the message says what to change."""


# --- Reading a how-to ------------------------------------------------------------------------


@dataclass(frozen=True)
class HowTo:
    number: int
    slug: str
    title: str
    level: str
    # The rest of its docstring, for this Edition's page: see edition_text.
    text: str


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


# A block only one Edition's page shows, and the lines that open or close one.
ONLY = re.compile(r"^\[(\w+) only\]\n(.*?)^\[end\]\n?", re.MULTILINE | re.DOTALL)
MARKER = re.compile(r"^\[(\w+ only|end)\]$", re.MULTILINE)


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
        if re.search(r"^(>>>|#)", body, re.MULTILINE) or MARKER.search(body):
            raise HowToRefused(f"A [{folder} only] block holds a >>> step, a heading or another "
                               "block. It may hold only prose and indented code: put a step "
                               "both Editions run outside it.")
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


LAYOUT = re.compile(r"(?P<title>[^\n]+)\n\nLevel: (?P<level>[^\n]+)\n\n(?P<rest>.*)", re.DOTALL)


def read_how_to(path: Path, edition: editions.Edition = EDITION) -> HowTo:
    """A how-to, read from its file, for `edition`'s page."""
    laid_out = LAYOUT.fullmatch(docstring_of(path))
    if laid_out is None:
        raise HowToRefused(f"{path.name} must start with its title on line 1 and a line such as "
                           "`Level: Getting started` on line 3, each followed by a blank line.")
    level, number = laid_out["level"], int(path.stem[:2])
    if level not in LEVELS:
        raise HowToRefused(f"{path.name} has the level {level!r}: write "
                           f"{' or '.join(repr(name) for name in LEVELS)}.")
    if number not in LEVELS[level][1]:
        numbers = LEVELS[level][1]
        raise HowToRefused(f"{path.name} is how-to {number}, but {level} holds how-tos "
                           f"{numbers.start} to {numbers.stop - 1}.")
    return HowTo(number, slug_of(path), laid_out["title"], level,
                 edition_text(laid_out["rest"], edition, marked=True))


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
    """Prose: paragraphs, "- " lists, indented code, and the blocks only this Edition shows."""
    blocks = []
    pieces = re.split(r"^\[only\]\n(.*?)^\[end\]\n?", text, flags=re.MULTILINE | re.DOTALL)
    for position, piece in enumerate(pieces):
        shown = []
        for paragraph in paragraphs(piece):
            if is_code(paragraph):
                shown.append(code_html(textwrap.dedent(paragraph)))
            elif paragraph.startswith("- "):
                items = re.split(r"\n(?=- )", paragraph)
                shown.append("<ul>" + "".join(f"<li>{linked(item[2:])}</li>" for item in items)
                             + "</ul>")
            else:
                shown.append(f"<p>{linked(paragraph)}</p>")
        if position % 2:  # a block only this Edition's page shows
            shown = ['<div class="only">', *shown, "</div>"]
        blocks += shown
    return "\n".join(blocks)


# --- A step, run -----------------------------------------------------------------------------


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


def value_html(source: str, value) -> str:
    """What a step gives: a result table, the refusal it stops with, or the value Python shows."""
    if value is None:
        return ""
    if isinstance(value, Exception):
        heading = "Refused" if isinstance(value, REFUSALS) else "Python stops with an error"
        return label(heading) + code_html(message_text(value), "refusal")
    if isinstance(value, pd.DataFrame):
        on = ("Result on the Example database" if "example_database.send" in source
              else "Python shows")
        return label(on) + table_html(value)
    return label("Python shows") + code_html(repr(value), "output")


def toolbox_warnings(caught: list) -> list:
    """The Toolbox's own Warnings among those a step gave."""
    return [warning.message for warning in caught
            if warning.category.__module__.startswith(editions.CORE)]


def step_output_html(source: str, scope: dict, folder: Path) -> str:
    """Run one `>>>` step: what it prints, warns, gives and writes, or "" if nothing."""
    before, printed = files_in(folder), io.StringIO()
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        value = run_step(source, scope, printed)
    shown = [printed_html(source, printed.getvalue())]
    shown += [label("It builds, with a Warning") + code_html(message_text(message), "refusal")
              for message in toolbox_warnings(caught)]
    shown += [value_html(source, value), written_files_html(folder, before, files_in(folder))]
    html = "\n".join(part for part in shown if part)
    # The folder's name is made up afresh on every run.
    for differs in (folder.name, "WindowsPath(", "PosixPath("):
        if differs in html:
            raise HowToRefused(f"The step {source.strip()!r} shows {differs}, which differs "
                               "from one computer to another, so the page would too. Show a "
                               "path's .name, or a path relative to the folder it works in.")
    return html


def chunk_html(text: str, scope: dict, folder: Path, sources: list[str]) -> str:
    """Prose and `>>>` steps; each step's source is added to `sources`.

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
        sources.append(part.source)
        waiting.append(part.source)
        output = step_output_html(part.source, scope, folder)
        if output:
            shown += [code_html("".join(waiting)), output]
            waiting = []
    if waiting:
        shown.append(code_html("".join(waiting)))
    return "\n".join(block for block in shown if block)


def section_html(text: str, scope: dict, folder: Path, sources: list[str]) -> str:
    """One fixed heading's text: its steps or mistakes each under its own heading."""
    parts = re.split(r"^### (.+)\n", text, flags=re.MULTILINE)
    shown = [chunk_html(parts[0], scope, folder, sources)]
    for heading, chunk in zip(parts[1::2], parts[2::2]):
        shown += [f"<h5>{linked(heading)}</h5>", chunk_html(chunk, scope, folder, sources)]
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
    scope, sources, shown = {}, [], []
    with example_setting(), lineage_pinned():
        folder = Path.cwd()
        for heading, text in sections(how_to):
            shown += [f"<h4>{escape(heading)}</h4>", section_html(text, scope, folder, sources)]
    badge = (f'<span class="badge {LEVELS[how_to.level][0]}">{escape(how_to.level)}</span>')
    return (f'<section class="entry" id="{how_to.slug}">\n'
            f"<h3>{how_to.number}. {inline(how_to.title)} {badge}</h3>\n"
            + "\n".join(block for block in shown if block) + "\n"
            + names_html(names_in("\n".join(sources))) + "\n</section>")


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
    levels, contents = [], []
    for level, (level_id, _, for_what) in LEVELS.items():
        at_level = [how_to for how_to in how_tos if how_to.level == level]
        contents.append(f'<div>\n<p><b><a href="#{level_id}">{level}</a></b>: {for_what}.</p>'
                        f"\n{contents_html(at_level)}\n</div>")
        entries = [how_to_html(how_to) for how_to in at_level] or [
            '<p class="note">No how-tos at this level yet.</p>']
        levels.append(f'<h2 id="{level_id}">{level}</h2>\n' + "\n".join(entries))
    filled = {
        "STYLE": STYLE + HOW_TO_STYLE,
        "PRODUCT": escape(EDITION.product),
        "FOLDER": escape(EDITION.folder),
        "VERSION": escape(sqlglot_composer.TOOLBOX_VERSION),
        "CONTENTS": "\n".join(contents),
        "LEVELS": "\n".join(levels),
    }
    # One pass, so text that happens to look like a marker is never filled in itself.
    page = re.sub(r"__([A-Z]+)__", lambda found: filled[found[1]], PAGE)
    check_links(page)
    return page


HOW_TO_STYLE = """h5{font-size:15px;margin:16px 0 4px;color:#333}
.levels{display:grid;grid-template-columns:1fr 1fr;gap:18px}
@media (max-width:800px){.levels{grid-template-columns:1fr}}
.levels ul{margin:4px 0}
.badge{font-size:12px;font-weight:600;border-radius:10px;padding:1px 8px;margin-left:6px;vertical-align:2px}
.badge.getting-started{color:#1f5a2a;background:#e6f4e8} .badge.intermediate{color:#6b4500;background:#fbefdc}
.only{margin:0}
pre.file{white-space:pre-wrap}
.code{position:relative} .code pre{padding-right:64px}
.copy{position:absolute;top:4px;right:4px;font:12px system-ui,sans-serif;padding:1px 8px;cursor:pointer}
"""

# The page. how_to_page fills in each __NAME__ marker. The script shows the search box, which
# keeps the how-tos holding every word typed, and puts a Copy button on each block of Python
# and Hive. This is an ordinary Python string, so a backslash in the script is written twice.
PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__PRODUCT__ __VERSION__: How-tos</title>
<style>
__STYLE__</style></head><body>
<header>
<h1>__PRODUCT__ __VERSION__: How-tos</h1>
<p>Each how-to walks through one job from start to finish: its goal, when you'd use it, its
steps, how to check it worked, the mistakes people make first, and where to go next. Its steps
are one notebook: paste them in order, starting with the import. Each step shows its Python,
then what it gives: the Hive, ready to paste into another program, a result from the Example
database, the three made-up tables that ship inside the Toolbox, and any file it writes. Every
Hive, result, refusal and Warning here comes from running the steps.</p>
<p>The steps take today as 2026-09-25, the day after the Example database's last day. Pasted
into your notebook, a step that uses <code>last_n_days</code> counts back from your own today
and finds no rows here: write <code>between</code> with the days its Hive shows in its place.
The <a href="examples.html">Example gallery</a>, beside this page in the <code>__FOLDER__</code>
folder, holds every Worked example, and the how-tos link to it.</p>
</header>
<p id="filter" hidden><label>Show only the how-tos holding every word:
<input type="search" placeholder="for example: show_hive or send"></label>
<span id="count"></span></p>
<main>
<nav class="levels">
__CONTENTS__
</nav>
__LEVELS__
</main>
<script>
const filter = document.getElementById("filter"), box = filter.querySelector("input");
const entries = [...document.querySelectorAll(".entry")];
filter.hidden = false;
box.oninput = () => {
  const words = box.value.toLowerCase().split(/\\s+/).filter(Boolean);
  for (const entry of entries) {
    entry.hidden = !words.every(word => entry.textContent.toLowerCase().includes(word));
    document.querySelector('[data-for="' + entry.id + '"]').hidden = entry.hidden;
  }
  const shown = entries.filter(entry => !entry.hidden).length;
  document.getElementById("count").textContent = shown + " of " + entries.length + " shown";
};
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
</script>
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
