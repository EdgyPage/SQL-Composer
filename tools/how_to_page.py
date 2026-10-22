"""Write the how-to page, `sqlglot_composer/how_to.html`, from the how-tos.

Run it on `dev` after changing a how-to in `worked_examples/how_to/`, or anything that changes
what a how-to's steps show:

    python tools/how_to_page.py

A test fails while a committed page differs from what this writes.

A how-to walks through one job from start to finish, as one fresh notebook. Each is a file
`worked_examples/how_to/NN_slug.py`: NN is its number, and the page's link to it is `#slug`.
The how-tos are numbered 1, 2, 3 and on, every Getting started how-to before every Intermediate
one, so the groups' numbers come from the files. The file holds a docstring and any pandas
stand-ins (below). The docstring is laid out like this:

    Start a Project                     <- the title, on line 1

    For: Getting started                <- its group: Getting started or Intermediate

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
  with, and each file it writes: a .py or .md file in full, folded when it is longer than
  FOLD_AFTER lines, or named only when it is the same as one shown before, and an .html file
  by name;
- indented code, shown but not run, for what works only at work, such as your own query and
  execute;
- a file as it is after an edit: a line such as

      The file `references/ops__job_runs.py`, after you fill it in:

  then a blank line, then the whole file, indented four more than that line. Where it stands
  among the steps, the file is written, dedented, to that path in the folder the steps run in,
  and the page shows it in a box headed by its path. A `.ipynb` file is written as its cells,
  each starting at a `# %%` line as in a Template (a `# %% [markdown]` cell's lines start with
  `# `), and saved as the notebook Jupyter reads. Nothing else about it runs;
- a file as a Project action wrote it, before you fill it in: a line such as

      The file `references/mart__alerts_per_severity.py`, as project.new_table wrote it:

  then the file, laid out as above. Nothing writes it: where it stands among the steps, the
  file at that path must hold just that, or the how-to is refused, and the page shows it in a
  box headed by its path and the call. Its `<...>` placeholders needn't be Python yet.

Where the Example database can't run a Statement's Hive, such as one with
row_number or week_start, the how-to's file gives a pandas stand-in after its docstring: a
function `NAME_in_pandas()`, which returns the DataFrame the Statement the steps call `NAME`
gives, as the Worked examples' `*_in_pandas` functions do. When the Example database's query
can't run that Statement's Hive, the stand-in's DataFrame comes back instead, both on the page,
labelled as computed in pandas as the Example gallery labels it, and in the doctest.

While the steps run, today is 2026-09-25, as on the Example gallery, and each how-to works in a
folder of its own, deleted afterwards. A lineage's or a Project action's time, your scripts'
commit and the Toolbox version are pinned, so the page comes out the same on every run.

A how-to links only to how-tos and the Example gallery, and check_links refuses any other link.
It names the Example projects in prose, by their folder, which main holds beside the Toolbox's
folder.
"""

from __future__ import annotations

import ast
import contextlib
import datetime
import doctest
import importlib.util
import io
import json
import os
import re
import sys
import textwrap
import warnings
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from html import escape, unescape
from pathlib import Path
from typing import NamedTuple
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import toolbox_registry  # noqa: E402
import pandas as pd  # noqa: E402

import sqlglot_composer  # noqa: E402
from sqlglot_composer import example_database, lineage, project, unchecked  # noqa: E402
from sqlglot_composer.clauses import Statement  # noqa: E402
from example_gallery import (  # noqa: E402
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
PAGE_PATH = ROOT / toolbox_registry.FOLDER / "how_to.html"
GALLERY = ROOT / toolbox_registry.FOLDER / "examples.html"

HEADINGS = ("Goal", "When you'd use it", "Steps", "Check it worked", "Common mistakes", "Next")


class Group(NamedTuple):
    """Getting started how-tos or Intermediate how-tos: what a how-to's `For:` line names.

    Which how-tos a group holds, and so their numbers, comes from the how-tos' own `For:`
    lines: see check_numbering.
    """

    name: str
    # The id of its heading on the page, and its badges' class.
    id: str
    # What its contents list says it is for.
    for_what: str


# In the order their how-tos are numbered: every Getting started how-to comes first.
GROUPS = (
    Group("Getting started", "getting-started",
          "one story through one Project, a how-to for each of the README's steps: a "
          "Project, its Table references, Statements, Building blocks, Saved tables, their "
          "Lineage and the Project's upkeep"),
    Group("Intermediate", "intermediate",
          "a menu, each starting from the Intermediate Example project: one job each, such as "
          "rewriting some partitions, rollups, Keys, quality checks and testing"),
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
    # The rest of its docstring: its six sections.
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


LAYOUT = re.compile(r"(?P<title>[^\n]+)\n\nFor: (?P<group>[^\n]+)\n\n(?P<rest>.*)", re.DOTALL)


def read_how_to(path: Path) -> HowTo:
    """A how-to, read from its file."""
    laid_out = LAYOUT.fullmatch(docstring_of(path))
    if laid_out is None:
        raise HowToRefused(f"{path.name} must start with its title on line 1 and a line such as "
                           "`For: Getting started` on line 3, each followed by a blank line.")
    name = laid_out["group"]
    if name not in GROUP_NAMED:
        raise HowToRefused(f"{path.name} says `For: {name}`: write "
                           f"{' or '.join(f'`For: {group.name}`' for group in GROUPS)}.")
    return HowTo(int(path.stem[:2]), slug_of(path), laid_out["title"], name,
                 laid_out["rest"], stand_ins_of(path))


def check_numbering(how_tos: list[HowTo]) -> None:
    """Refuse how-tos, in number order, unless they are numbered 1, 2, 3 and on, each once, and
    every how-to of a group comes before every how-to of the groups after it in GROUPS."""
    numbers = [how_to.number for how_to in how_tos]
    if numbers != list(range(1, len(numbers) + 1)):
        raise HowToRefused(f"The how-tos' files are numbered {', '.join(map(str, numbers))}: "
                           "number them 1, 2, 3 and on, each once, with none left out.")
    for before, after in zip(how_tos, how_tos[1:]):
        if GROUPS.index(GROUP_NAMED[after.group]) < GROUPS.index(GROUP_NAMED[before.group]):
            raise HowToRefused(
                f"{after.number:02}_{after.slug}.py is {after.group}, after "
                f"{before.number:02}_{before.slug}.py, which is {before.group}: number every "
                f"{' how-to before every '.join(group.name for group in GROUPS)} how-to.")


# --- A file shown as it is after an edit -----------------------------------------------------


@dataclass(frozen=True)
class FileBlock:
    """A file a how-to shows as it is after an edit, which its steps write where it stands."""

    # Where it goes, from the folder the steps run in, such as references/ops__job_runs.py.
    path: str
    # What you did to it, such as "fill it in": its heading says "after you fill it in". ""
    # for a file shown as a Project action wrote it.
    what: str
    # The file's text, dedented.
    text: str
    # How many lines of the docstring it takes, its heading and blank line among them.
    lines: int = field(compare=False)
    # The call that wrote it, such as project.new_table, for a file shown as that call wrote
    # it, which the steps check rather than write; "" for a file shown after an edit.
    written_by: str = ""


FILE_HEADING = re.compile(r"The file `(?P<path>[^`]+)`, (?:after you (?P<what>[a-z ]+)"
                          r"|as (?P<written_by>[a-z_.]+) wrote it):")


def with_file_blocks(text: str) -> list[str | FileBlock]:
    """`text` cut at each file it shows: its prose and steps, with each FileBlock where it
    stands.

    A file is a line such as "The file `references/ops__job_runs.py`, after you fill it in:",
    a blank line, then the file, each of its lines indented four more than that line.
    """
    lines = text.splitlines(keepends=True)
    found: list[str | FileBlock] = []
    prose: list[str] = []
    at = 0
    while at < len(lines):
        heading = FILE_HEADING.fullmatch(lines[at].strip())
        if heading is None:
            prose.append(lines[at])
            at += 1
            continue
        indent = " " * (len(lines[at]) - len(lines[at].lstrip()) + 4)
        if at + 2 >= len(lines) or lines[at + 1].strip() or not lines[at + 2].startswith(indent):
            raise HowToRefused(f"{lines[at].strip()!r} must be followed by a blank line, then "
                               "the whole file, each line indented four more than it.")
        end = at + 2
        while end < len(lines) and (not lines[end].strip() or lines[end].startswith(indent)):
            end += 1
        while not lines[end - 1].strip():
            end -= 1
        path = heading["path"]
        if Path(path).is_absolute() or ".." in Path(path).parts:
            raise HowToRefused(f"The file `{path}` must be a path inside the Project, such as "
                               "references/ops__job_runs.py.")
        found += ["".join(prose), FileBlock(path, heading["what"] or "",
                                            textwrap.dedent("".join(lines[at + 2:end])),
                                            end - at, heading["written_by"] or "")]
        prose = []
        at = end
    return [*found, "".join(prose)]


def write_file(block: FileBlock, folder: Path) -> None:
    """Write a file a how-to shows as it is after an edit, into `folder`: a .ipynb file from
    its `# %%` cells, as project.new_table writes a Template's, and any other as its text."""
    path = folder / block.path
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.suffix != ".ipynb":
        path.write_text(block.text, encoding="utf-8", newline="\n")
        # The steps after it import the file, as a notebook would once you save it.
        importlib.invalidate_caches()
        return
    cells = project._template_cells(block.text)
    if not cells:
        raise HowToRefused(f"The file `{block.path}` is a notebook: write its cells, each "
                           "starting at a `# %%` line, as a Template does.")
    project._write_notebook(path, cells)


def check_written(block: FileBlock, folder: Path) -> None:
    """Refuse a file shown as a Project action wrote it, unless the file in `folder` holds just
    what the how-to shows: a .ipynb file the same cells, any other the same text."""
    path = folder / block.path
    if path.suffix == ".ipynb" and path.is_file():
        cells = [(cell["cell_type"], "".join(cell["source"]).strip("\n"))
                 for cell in json.loads(path.read_text(encoding="utf-8"))["cells"]]
        same = cells == project._template_cells(block.text)
    else:
        same = path.is_file() and (path.read_text(encoding="utf-8").strip("\n")
                                   == block.text.strip("\n"))
    if not same:
        raise HowToRefused(f"The file `{block.path}`, shown as {block.written_by} wrote it, "
                           "isn't what the folder holds there: show the file as the call "
                           "wrote it.")


def write_or_check(block: FileBlock, folder: Path) -> None:
    """Write a file shown after an edit, or check one shown as a Project action wrote it."""
    if block.written_by:
        check_written(block, folder)
    else:
        write_file(block, folder)


def file_block_html(block: FileBlock) -> str:
    """A file shown as it is after an edit, or as a Project action wrote it: a box headed by
    its path."""
    kind = "python" if Path(block.path).suffix in (".py", ".ipynb") else "file"
    after = (f"as <code>{escape(block.written_by)}</code> wrote it" if block.written_by
             else f"after you {escape(block.what)}")
    return (f'<p class="label">The file <code>{escape(block.path)}</code>, {after}</p>\n'
            + code_html(block.text, kind))


# The top folders and files of a Project a notebook imports by name.
PROJECT_MODULES = ("references", "building_blocks", "warehouse", "tables")


@contextlib.contextmanager
def project_on_the_path(folder: Path) -> Iterator[None]:
    """Import a Project's own scripts as a notebook started in `folder` does: references,
    building_blocks, warehouse and tables by their own names.

    The Worked examples have folders of the same names, so a module of those names is put away
    first, `folder` goes first on the path, and afterwards the Project's modules go and the
    others come back: no how-to sees another's references.
    """
    def is_the_projects(module: str) -> bool:
        return module.split(".")[0] in PROJECT_MODULES

    put_away = {name: sys.modules.pop(name) for name in list(sys.modules)
                if is_the_projects(name)}
    sys.path.insert(0, str(folder))
    try:
        yield
    finally:
        sys.path.remove(str(folder))
        for name in [name for name in sys.modules if is_the_projects(name)]:
            del sys.modules[name]
        sys.modules.update(put_away)


def run_as_doctest(path: Path) -> tuple[int, str]:
    """Run a how-to as a doctest in the folder you're working in, as one fresh notebook: its
    steps in order, each file it shows written where it stands, times pinned and its pandas
    stand-ins answering, as on the page. Gives the number of steps that failed, and what
    doctest reports of them.

    A Warning a step gives is shown on the page, and here doesn't stop the step.
    """
    scope: dict[str, object] = {}
    runner = doctest.DocTestRunner(optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS)
    report: list[str] = []
    line = 0
    with (warnings.catch_warnings(record=True), times_pinned(), project_on_the_path(Path.cwd()),
          pandas_standing_in(stand_ins_of(path), scope, [])):
        warnings.simplefilter("always")
        for number, part in enumerate(with_file_blocks(docstring_of(path)), start=1):
            if isinstance(part, FileBlock):
                write_or_check(part, Path.cwd())
                line += part.lines
                continue
            # Each part its own name: doctest finds a step's source by it, and a function an
            # earlier part defined would otherwise be looked up among this part's steps.
            test = doctest.DocTestParser().get_doctest(part, {}, f"{path.stem} part {number}",
                                                       str(path), line)
            # One scope for every part, as one notebook's, which the stand-ins read too.
            test.globs = scope
            runner.run(test, out=report.append, clear_globs=False)
            line += part.count("\n")
    return runner.failures, "".join(report)


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
    # Each .py or .md file the steps have shown, by its text: see written_files_html.
    files_shown: dict = field(default_factory=dict)


@contextlib.contextmanager
def pandas_standing_in(stand_ins: dict[str, Callable[[], pd.DataFrame]],
                       scope: dict[str, object], answered: list[str]) -> Iterator[None]:
    """While it lasts, a query the Example database can't run, from a Statement a pandas
    stand-in is for, gets the stand-in's DataFrame back.

    `stand_ins` are a how-to's, by the name of their Statement in `scope`, the steps' names.
    Each query a stand-in answers has its Hive added to `answered`.
    """
    real_query = example_database.query

    def query(hive: str) -> pd.DataFrame:
        try:
            return real_query(hive)
        except RuntimeError as error:
            if CANT_RUN not in str(error):
                raise
            for name, in_pandas in stand_ins.items():
                s = scope.get(name)
                if isinstance(s, Statement) and sqlglot_composer.to_hive(s) == hive:
                    answered.append(hive)
                    return in_pandas()
            raise

    with mock.patch.object(example_database, "query", query):
        yield


# A written file longer than this, in lines, is folded on the page, such as a Lineage file of
# several Statements.
FOLD_AFTER = 120
# A step that writes more files than this, such as project.start(), names them all in one list
# and shows none: later steps print the ones they need.
LIST_AFTER = 8


def files_in(folder: Path) -> dict[Path, bytes]:
    return {path: path.read_bytes() for path in folder.rglob("*") if path.is_file()}


def written_files_html(folder: Path, before: dict[Path, bytes], after: dict[Path, bytes],
                       shown_before: dict[str, str]) -> str:
    """Each file a step writes in `folder`: a .py or .md file in full, any other by name, or
    all of them in one list of names when there are more than LIST_AFTER.

    `before` and `after` are what files_in gave before and after the step. A file longer than
    FOLD_AFTER lines is folded, opened with a click. `shown_before` holds each .py or .md file
    the how-to has shown, by its text, so a file the same as one shown before is named only;
    this adds the files shown here to it.
    """
    written = sorted((path for path, text in after.items() if before.get(path) != text),
                     key=lambda path: (path.suffix not in (".py", ".md"), path.as_posix()))
    if len(written) > LIST_AFTER:
        names = sorted(path.relative_to(folder).as_posix() for path in written)
        return (label(f"It writes {len(names)} files") + "\n"
                + code_html("\n".join(names), "file"))
    shown = []
    for path in written:
        name = path.relative_to(folder).as_posix()
        if path.suffix in (".py", ".md"):
            text = path.read_text(encoding="utf-8")
            if text in shown_before:
                shown.append(f'<p class="note">It writes <code>{escape(name)}</code> too, line '
                             f"for line the same as <code>{escape(shown_before[text])}</code> "
                             "above.</p>")
                continue
            shown_before[text] = name
            kind = "python" if path.suffix == ".py" else "file"
            lines = len(text.splitlines())
            shown.append(label(f"It writes {name}"))
            shown.append(code_html(text, kind) if lines <= FOLD_AFTER else
                         f"<details><summary>Show its {lines} lines</summary>\n"
                         f"{code_html(text, kind)}\n</details>")
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


# A step that runs on the Example database: through its query, or through the Project's
# from warehouse.py, which runs on it on the page.
ON_THE_EXAMPLE_DATABASE = re.compile(r"\bquery=(?:example_database\.)?query\b")


def value_html(source: str, value: object, in_pandas: bool) -> str:
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
              else "Result on the Example database" if ON_THE_EXAMPLE_DATABASE.search(source)
              else "Python shows")
        return label(on) + table_html(value)
    return label("Python shows") + code_html(repr(value), "output")


def toolbox_warnings(caught: list[warnings.WarningMessage]) -> list[Warning]:
    """The Toolbox's own Warnings among those a step gave."""
    return [warning.message for warning in caught
            if warning.category.__module__.startswith(toolbox_registry.FOLDER)]


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
              written_files_html(notebook.folder, before, files_in(notebook.folder),
                                 notebook.files_shown)]
    html = "\n".join(part for part in shown if part)
    # The folder's name is made up afresh on every run.
    for differs in (notebook.folder.name, "WindowsPath(", "PosixPath("):
        if differs in html:
            raise HowToRefused(f"The step {source.strip()!r} shows {differs}, which differs "
                               "from one computer to another, so the page would too. Show a "
                               "path's .name, or a path relative to the folder it works in.")
    return html


def live_steps_html(text: str, notebook: Notebook) -> str:
    """Prose and `>>>` steps, run in `notebook`, each shown with what it really gives.

    The gallery's steps_html shows what a docstring writes under a step instead, and
    handed_html the Statements its example scope noted. Steps in a row that show nothing share
    one block of Python with the step after them. A file shown as it is after an edit is
    written where it stands: see with_file_blocks.
    """
    shown, waiting = [], []
    parts = []
    for piece in with_file_blocks(text):
        parts += [piece] if isinstance(piece, FileBlock) else doctest.DocTestParser().parse(piece)
    for part in parts:
        if isinstance(part, FileBlock):
            if waiting:
                shown.append(code_html("".join(waiting)))
                waiting = []
            write_or_check(part, notebook.folder)
            if Path(part.path).suffix in (".py", ".md"):
                notebook.files_shown.setdefault(part.text, part.path)
            shown.append(file_block_html(part))
            continue
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


def section_html(text: str, notebook: Notebook) -> str:
    """One fixed heading's text: its steps or mistakes each under its own heading."""
    parts = re.split(r"^### (.+)\n", text, flags=re.MULTILINE)
    shown = [live_steps_html(parts[0], notebook)]
    for heading, chunk in zip(parts[1::2], parts[2::2]):
        shown += [f"<h5>{linked(heading)}</h5>", live_steps_html(chunk, notebook)]
    return "\n".join(block for block in shown if block)


@contextlib.contextmanager
def times_pinned() -> Iterator[None]:
    """A lineage's or a Project action's time, your scripts' commit and the Toolbox version, the
    same on every run.

    Without a notebook's name in the environment, a lineage is named as from a notebook.
    """
    version = f"{toolbox_registry.PRODUCT} {sqlglot_composer.TOOLBOX_VERSION}"
    with (mock.patch.object(lineage, "_now", lambda: LINEAGE_TIME),
          mock.patch.object(project, "_now", lambda: LINEAGE_TIME),
          mock.patch.object(unchecked, "_now", lambda: LINEAGE_TIME),
          mock.patch.object(lineage, "scripts_commit", lambda folder: LINEAGE_COMMIT),
          mock.patch.object(lineage, "_version", lambda: version),
          mock.patch.dict(os.environ)):
        os.environ.pop("JPY_SESSION_NAME", None)
        yield


def how_to_html(how_to: HowTo) -> str:
    """A how-to's entry on the page, its steps run in a fresh notebook's scope."""
    shown = []
    with example_setting(), times_pinned(), project_on_the_path(Path.cwd()):
        # A notebook's own scope is named __main__.
        notebook = Notebook(scope={"__name__": "__main__"}, folder=Path.cwd())
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
    check_numbering(how_tos)
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
        "PRODUCT": escape(toolbox_registry.PRODUCT),
        "FOLDER": escape(toolbox_registry.FOLDER),
        "VERSION": escape(sqlglot_composer.TOOLBOX_VERSION),
        "CHAIN": chain_html(),
        "CONTENTS": "\n".join(contents),
        "GROUPS": "\n".join(groups),
        "SCRIPT": FILTER_SCRIPT + HOW_TO_SCRIPT,
    }
    # One pass, so text that happens to look like a marker is never filled in itself.
    page = re.sub(r"__([A-Z]+)__", lambda found: filled[found[1]], PAGE)
    check_links(page)
    return page


# The chain of types a Statement is built along, atop the page: each call, the type of the
# value it gives, in the type hints' names, and what that value is.
CHAIN = (
    ("`ops.jobs`, a Table reference", "Table", "a table: its columns, its Partitions and its Key"),
    ("`ops.jobs.job_id`", "Column", "one of its columns"),
    ("a test, such as `equals(...)`", "Condition", "a test of each row, for WHERE or ON"),
    ("`SELECT(...)`, `FROM(...)`, `WHERE(...)` and the others", "Clause",
     "one part of a query"),
    ("`statement(...)`", "Statement", "its Clauses, checked together as one query"),
    ("`to_hive(...)`", "str", "the Hive: the query's text, ready to paste"),
    ("`run(..., query=query)`", "DataFrame", "the rows your query gives back, in pandas"),
)


def chain_html() -> str:
    """The chain of types, as a table: each call and the type of what it gives."""
    rows = "\n".join(f"<tr><td>{inline(call)}</td><td><code>{escape(type_name)}</code></td>"
                     f"<td>{inline(what)}</td></tr>" for call, type_name, what in CHAIN)
    return ('<table class="chain">\n<tr><th>You write</th><th>It gives</th><th>Which is</th>'
            f"</tr>\n{rows}\n</table>")


HOW_TO_STYLE = """h5{font-size:15px;margin:16px 0 4px;color:#333}
.groups{display:grid;grid-template-columns:1fr 1fr;gap:18px}
@media (max-width:800px){.groups{grid-template-columns:1fr}}
.groups ul{margin:4px 0}
.badge{font-size:12px;font-weight:600;border-radius:10px;padding:1px 8px;margin-left:6px;vertical-align:2px}
.badge.getting-started{color:#1f5a2a;background:#e6f4e8} .badge.intermediate{color:#6b4500;background:#fbefdc}
pre.file{white-space:pre-wrap}
details summary{cursor:pointer;color:#555;margin:4px 0}
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
database, or a file it writes. The Example database is nine made-up tables that ship inside the
Toolbox. Every Hive, result, refusal and Warning here comes from running the steps.</p>
<p>The Example database holds two days of <code>ops.job_runs</code>, 2026-09-23 and
2026-09-24 (the three tables the Intermediate how-tos use hold 14 days), and the steps here were
run as if today were 2026-09-25. Where a step uses <code>last_n_days</code>, it counts back from
your real today, so in your own notebook it finds no rows on the Example database: write
<code>between</code> with the dates instead.</p>
<p>The <a href="examples.html">Example gallery</a>, beside this page in the
<code>__FOLDER__</code> folder, holds every Worked example, and the how-tos link to it.</p>
<p>A Statement is built along a chain of types, each made by a call on the one before. A step
says the type of each value it makes in a comment, such as <code># -&gt; Statement</code>.</p>
__CHAIN__
</header>
<p id="filter" hidden><label>Show only the how-tos holding every word:
<input type="search" placeholder="for example: show_hive or query"></label>
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
    except (RuntimeError, HowToRefused) as why:
        print(why, file=sys.stderr)
        return 1
    PAGE_PATH.write_text(page, encoding="utf-8", newline="\n")
    print(f"Wrote {PAGE_PATH.relative_to(ROOT).as_posix()}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
