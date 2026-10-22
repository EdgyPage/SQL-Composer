"""The how-tos, and the page the Toolbox ships them on, `how_to.html`.

`tools/how_to_page.py` writes the page from the how-tos in `worked_examples/how_to/`, running
each step on the Example database. The page is committed and ships with the Toolbox, so these
tests read the committed copy, and one fails if writing it again would change it. Each how-to
also runs as a doctest, as one fresh notebook in a folder of its own, with today pinned.
"""

from __future__ import annotations

import ast
import builtins
import contextlib
import doctest
import html
import json
import os
import re
import shutil
import subprocess
import textwrap
import warnings
from collections.abc import Sequence
from pathlib import Path

import pytest

import example_gallery
import how_to_page
import sqlglot_composer
from offline_policy import external_references
from conftest import FOLDER, PRODUCT, gallery_sections, page_text, toolbox_folder
from test_example_gallery import TagCounter

ROOT = Path(__file__).resolve().parent.parent
PAGE = toolbox_folder() / "how_to.html"
HOW_TOS = how_to_page.how_to_paths()
SLUGS = [how_to_page.slug_of(path) for path in HOW_TOS]
PUBLIC = set(sqlglot_composer.__all__)
# Names a how-to may use without defining them: what a notebook at work has (the query API or
# database cursor a query or execute calls, and the Project's warehouse.py, which holds them,
# named in prose as `warehouse.py`), the Example database's database, the Toolbox's folders,
# and its project module, which a how-to may name in prose, such as `project.check()`.
OUTSIDE_NAMES = {"my_api", "cursor", "ops", FOLDER, "project", "warehouse", "query", "execute"}


def page() -> str:
    return PAGE.read_text(encoding="utf-8")


def page_sections() -> dict[str, str]:
    """Each how-to on the committed page, by its id: its HTML."""
    return dict(re.findall(r'<section class="entry" id="([^"]+)">(.*?)</section>', page(),
                           re.DOTALL))


@pytest.mark.needs_example_database
def test_the_committed_page_is_what_the_tool_writes() -> None:
    committed = page() if PAGE.exists() else ""
    assert how_to_page.how_to_page() == committed, (
        f"{PAGE.relative_to(ROOT).as_posix()} is out of date: run python tools/how_to_page.py"
    )


def test_there_is_a_how_to_and_how_to_1_starts_a_project() -> None:
    assert SLUGS[:1] == ["start_a_project"]
    assert HOW_TOS[0].stem.startswith("01_")


# --- Each how-to's source --------------------------------------------------------------------


@pytest.mark.needs_example_database
@pytest.mark.parametrize("path", HOW_TOS, ids=lambda path: path.stem)
def test_each_how_to_runs_as_a_doctest(
        path: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    text = how_to_page.docstring_of(path)
    test = doctest.DocTestParser().get_doctest(text, {}, path.stem, str(path), 0)
    runner = doctest.DocTestRunner(optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS)
    report = []
    # A Warning is shown on the page; here it may not stop the step it comes from. A pandas
    # stand-in answers as on the page.
    with (warnings.catch_warnings(record=True), how_to_page.times_pinned(),
          how_to_page.pandas_standing_in(how_to_page.stand_ins_of(path), test.globs, [])):
        warnings.simplefilter("always")
        runner.run(test, out=report.append)
    assert runner.failures == 0, "".join(report)


@pytest.mark.parametrize("path", HOW_TOS, ids=lambda path: path.stem)
def test_a_how_to_has_its_title_its_group_and_its_headings_in_order(path: Path) -> None:
    doc = how_to_page.docstring_of(path)
    lines = doc.splitlines()
    assert lines[0].strip() and lines[1] == "" and lines[3] == ""
    group = re.fullmatch(r"For: (.+)", lines[2]).group(1)
    assert int(path.stem[:2]) in how_to_page.GROUP_NAMED[group].numbers
    assert re.findall(r"^## (.+)$", doc, re.MULTILINE) == list(how_to_page.HEADINGS)


def code_and_prose(path: Path) -> tuple[list[str], list[str]]:
    """A how-to's code, its >>> steps and indented code, and its `backticked` spans of prose."""
    code, spans = [], []
    for part in doctest.DocTestParser().parse(how_to_page.docstring_of(path)):
        if not isinstance(part, str):
            code.append(part.source)
            continue
        for paragraph in how_to_page.paragraphs(part):
            if how_to_page.is_code(paragraph):
                code.append(paragraph)
            else:
                spans += re.findall(r"`([^`]+)`", paragraph)
    return [textwrap.dedent(block) for block in code], spans


def names_of(tree: ast.AST) -> tuple[set[str], set[str]]:
    """The names a piece of code defines, and those it reads."""
    defined, read = set(), set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            (read if isinstance(node.ctx, ast.Load) else defined).add(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            defined.add(node.name)
        elif isinstance(node, ast.arg):
            defined.add(node.arg)
        elif isinstance(node, ast.ExceptHandler) and node.name:  # except ... as name:
            defined.add(node.name)
        elif isinstance(node, (ast.Import, ast.ImportFrom)):
            defined |= {(alias.asname or alias.name).split(".")[0] for alias in node.names}
            if any(alias.name == "*" for alias in node.names):
                defined |= PUBLIC
    return defined, read


@pytest.mark.parametrize("path", HOW_TOS, ids=lambda path: path.stem)
def test_every_name_a_how_to_uses_exists(path: Path) -> None:
    code, spans = code_and_prose(path)
    trees = [ast.parse(block) for block in code]
    defined = set(dir(builtins)) | OUTSIDE_NAMES
    for tree in trees:
        defined |= names_of(tree)[0]
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module == FOLDER:
                # The admin and project modules are imported by name: the star
                # import leaves them out.
                imported = {alias.name for alias in node.names} - {"*"}
                assert imported <= PUBLIC | {"admin", "project"}, ast.unparse(node)
            if (isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)
                    and node.value.id == "example_database"):
                assert hasattr(sqlglot_composer.example_database, node.attr), ast.unparse(node)
    read = {name for tree in trees for name in names_of(tree)[1]}
    for span in spans:
        with contextlib.suppress(SyntaxError):
            read |= names_of(ast.parse(span))[1]
    assert read - defined == set(), (
        "These names are neither Toolbox names, nor made in the how-to, nor Python's own")


def link_targets(path: Path) -> set[str]:
    return {target for _, target in how_to_page.LINK.findall(how_to_page.docstring_of(path))}


@pytest.mark.parametrize("path", HOW_TOS, ids=lambda path: path.stem)
def test_each_link_goes_to_a_how_to_or_a_gallery_entry_that_exists(path: Path) -> None:
    for target in link_targets(path):
        page_name, _, place = target.partition("#")
        if page_name == "":
            assert place in SLUGS, f"no how-to {place}"
        else:
            assert page_name == "examples.html", f"{target} is neither a how-to nor the gallery"
            assert not place or place in gallery_sections(toolbox_folder()), (
                f"no entry {place} on the Example gallery")


def test_every_link_on_the_page_lands() -> None:
    ids = set(re.findall(r'\bid="([^"]+)"', page()))
    for target in re.findall(r'href="([^"]*)"', page()):
        page_name, _, place = target.partition("#")
        if page_name == "":
            assert place in ids, target
        else:
            assert page_name == "examples.html", target
            assert not place or place in gallery_sections(toolbox_folder()), target


# --- The page --------------------------------------------------------------------------------


def test_each_group_has_its_heading_and_contents_and_each_how_to_its_badge() -> None:
    text = page()
    how_tos = [how_to_page.read_how_to(path) for path in HOW_TOS]
    for group in how_to_page.GROUPS:
        assert f'<h2 id="{group.id}">{group.name}</h2>' in text
        contents = re.search(rf'<a href="#{group.id}">{group.name}</a>.*?</div>', text, re.DOTALL)
        listed = re.findall(r'data-for="([^"]+)"', contents.group(0))
        in_group = [how_to for how_to in how_tos if how_to.group == group.name]
        assert listed == [how_to.slug for how_to in in_group]
        if not in_group:
            assert f'<p class="note">No {group.name.lower()} how-tos yet.</p>' in text
        for how_to in in_group:
            assert how_to.number in group.numbers
            # A title is plain text on the page, so a ' in it, as in "a table's", is escaped.
            title = html.escape(how_to.title)
            assert (f'<h3>{how_to.number}. {title} <span class="badge {group.id}">'
                    f"{group.name}</span></h3>") in page_sections()[how_to.slug]
    # Getting started comes first.
    assert text.index('id="getting-started"') < text.index('id="intermediate"')


def test_every_how_to_is_on_the_page_in_number_order() -> None:
    assert list(page_sections()) == SLUGS


def test_the_example_gallery_beside_the_page_points_to_it() -> None:
    gallery = (toolbox_folder() / "examples.html").read_text(encoding="utf-8")
    header = gallery.split("</header>")[0]
    assert f'<a href="{PAGE.name}">how-tos</a>' in header


def test_the_page_needs_no_other_file() -> None:
    assert external_references(page()) == []


def test_without_its_script_the_page_is_plain_html() -> None:
    assert '<p id="filter" hidden>' in page()
    assert page().count(" hidden") == 1
    assert "<button" not in page()


def test_every_tag_on_the_page_is_closed() -> None:
    parser = TagCounter()
    parser.feed(page())
    assert parser.problems == [] and parser.open == []


def test_no_box_on_the_page_is_empty() -> None:
    assert not re.search(r"<pre[^>]*></pre>", page())


def test_the_page_names_no_folder_a_toolbox_user_does_not_have() -> None:
    assert "worked_examples" not in page()


def test_a_refusal_on_the_page_is_the_toolbox_s_own_message() -> None:
    """Common mistakes show the message the step really stops with, not text pasted in."""
    toolbox = sqlglot_composer
    job_runs = toolbox.example_database.job_runs
    with pytest.raises(toolbox.LoadRefused) as refused:
        toolbox.statement(toolbox.SELECT(job_runs.run_id), toolbox.FROM(job_runs),
                          toolbox.WHERE(toolbox.equals(job_runs.status, "FAILED")))
    shown = re.findall(r'<pre class="refusal">.*?</pre>', page_sections()["start_a_project"],
                       re.DOTALL)
    assert example_gallery.code_html(example_gallery.message_text(refused.value),
                                     "refusal") in shown


def test_the_query_mistake_shows_the_numbered_columns_it_gives() -> None:
    section = page_sections()["start_a_project"]
    assert "<tr><th>0</th><th>1</th><th>2</th></tr>" in section


def test_a_step_that_prints_hive_shows_it_as_hive_ready_to_paste() -> None:
    section = page_sections()["start_a_project"]
    assert ('<p class="label">Hive, ready to paste</p><pre class="hive">SELECT' in section)
    assert "&#x27;2026-09-24&#x27;;</pre>" in section


def test_a_result_shows_as_a_table() -> None:
    cells = re.findall(r"<td>(.*?)</td>", page_sections()["start_a_project"])
    assert cells[:6] == ["97", "3", "2026-09-23", "102", "2", "2026-09-24"]


# --- The page's script -----------------------------------------------------------------------


def the_script() -> str:
    scripts = re.findall(r"<script>\n(.*?)</script>", page(), re.DOTALL)
    assert len(scripts) == 1
    return scripts[0]


def test_the_page_has_one_short_script() -> None:
    assert len(the_script().strip().splitlines()) <= 35


def test_the_script_is_the_example_gallery_s_filter_then_the_page_s_own_lines() -> None:
    gallery = (toolbox_folder() / "examples.html").read_text(encoding="utf-8")
    assert re.findall(r"<script>\n(.*?)</script>", gallery, re.DOTALL) == [
        example_gallery.FILTER_SCRIPT]
    assert the_script() == example_gallery.FILTER_SCRIPT + how_to_page.HOW_TO_SCRIPT


def test_every_element_the_script_reaches_is_on_the_page() -> None:
    """What the browser test below holds, as far as the page's text can hold it everywhere."""
    text = page()
    assert re.search(r'<p id="filter" hidden><label>[^<]*\n<input type="search"[^>]*></label>\n'
                     r'<span id="count"></span></p>', text)
    # Each how-to's line in the contents names it, which the script finds by its id.
    ids = re.findall(r'<section class="entry" id="([^"]+)">', text)
    assert re.findall(r'<li data-for="([^"]+)">', text) == ids
    assert len(set(re.findall(r'\bid="([^"]+)"', text))) == len(re.findall(r'\bid="', text))
    for selector in ('getElementById("filter")', 'querySelector("input")',
                     'querySelectorAll(".entry")', 'getElementById("count")',
                     'querySelectorAll("[data-for]")', "getElementById(item.dataset.for)",
                     'querySelectorAll("pre.python, pre.hive")'):
        assert selector in the_script()


# A stand-in for the browser: the page's elements the script reaches, its clipboard and its
# selection. It runs the script, then checks what it did, and prints "ok".
BROWSER = """
const script = __SCRIPT__;
function element(tag, more = {}) {
  return Object.assign({tag, hidden: false, textContent: "", className: "", children: [],
    append(...items) { this.children.push(...items); },
    replaceWith(other) { this.replacedBy = other; }}, more);
}
const input = element("input", {value: "", listeners: [],
  addEventListener(kind, listener) { if (kind === "input") this.listeners.push(listener); }});
function type(text) {
  input.value = text;
  input.oninput();
  for (const listener of input.listeners) listener();
}
const count = element("span");
const filter = element("p", {hidden: true, querySelector: () => input});
const entries = [element("section", {id: "start", textContent: "Start a notebook: send"}),
                 element("section", {id: "join", textContent: "Join tables safely"})];
const items = [element("li", {dataset: {for: "start"}}), element("li", {dataset: {for: "join"}})];
const blocks = [element("pre", {className: "python", textContent: "x = 1"}),
                element("pre", {className: "hive", textContent: "SELECT 1;"})];
const copied = [];
let selected = null;
globalThis.document = {
  getElementById: id => ({filter, count})[id] || entries.find(entry => entry.id === id),
  querySelectorAll: selector => ({".entry": entries, "[data-for]": items,
                                  "pre.python, pre.hive": blocks})[selector],
  createElement: tag => element(tag),
};
// Node has a navigator of its own, which a plain assignment can't replace.
const browserHas = (name, value) =>
  Object.defineProperty(globalThis, name, {value, configurable: true, writable: true});
browserHas("navigator", {clipboard: {writeText: async text => { copied.push(text); }}});
browserHas("window", {getSelection: () => ({selectAllChildren: node => { selected = node; }})});
function check(ok, what) { if (!ok) throw new Error(what); }
(async () => {
  new Function(script)();
  check(filter.hidden === false, "the search box shows");
  type("  notebook SEND ");
  check(!entries[0].hidden && entries[1].hidden, "only the how-to with every word shows");
  check(!items[0].hidden && items[1].hidden, "its contents line hides with it");
  check(count.textContent === "1 of 2 shown", "the count: " + count.textContent);
  type("");
  check(!entries[1].hidden && !items[1].hidden && count.textContent === "2 of 2 shown",
        "an empty box shows every how-to");
  for (const block of blocks) {
    const holder = block.replacedBy, button = holder && holder.children[1];
    check(holder && holder.className === "code" && holder.children[0] === block, "wrapped");
    check(button.tag === "button" && button.type === "button" && button.className === "copy"
          && button.textContent === "Copy", "a Copy button on each block");
  }
  await blocks[0].replacedBy.children[1].onclick();
  check(copied.join() === "x = 1", "Copy copies the block's own text: " + copied);
  check(blocks[0].replacedBy.children[1].textContent === "Copied", "it says it copied");
  browserHas("navigator", {});
  await blocks[1].replacedBy.children[1].onclick();
  check(selected === blocks[1], "without a clipboard, it selects the block");
  check(blocks[1].replacedBy.children[1].textContent === "Press Ctrl+C", "and says so");
  console.log("ok");
})().catch(error => { console.error(error.message); process.exit(1); });
"""


def test_the_script_filters_the_how_tos_and_puts_a_copy_button_on_each_block(
        tmp_path: Path) -> None:
    node = shutil.which("node")
    if node is None:
        # GitHub's ubuntu-latest runners come with node, so CI always runs this test.
        if os.environ.get("CI"):
            pytest.fail("node isn't installed on this CI runner, so the page's script can't be "
                        "run: add actions/setup-node to .github/workflows/dev.yml")
        pytest.skip("node isn't installed, so the page's script can't be run here")
    harness = tmp_path / "browser.js"
    harness.write_text(BROWSER.replace("__SCRIPT__", json.dumps(the_script())),
                       encoding="utf-8")
    ran = subprocess.run([node, str(harness)], capture_output=True, text=True)
    assert ran.returncode == 0 and ran.stdout.strip() == "ok", ran.stderr


def test_the_script_gives_every_block_of_python_and_hive_a_copy_button_and_nothing_else() -> None:
    assert 'querySelectorAll("pre.python, pre.hive")' in the_script()
    kinds = set(re.findall(r'<pre class="([a-z]+)">', page()))
    assert {"python", "hive"} <= kinds
    assert kinds <= {"python", "hive", "output", "refusal", "file"}


# --- What the tool shows, and refuses --------------------------------------------------------


def a_how_to(tmp_path: Path, steps: str, name: str = "01_try_it.py",
             group: str = "Getting started", headings: Sequence[str] = how_to_page.HEADINGS,
             stand_ins: str = "") -> Path:
    """A how-to's file with `steps` under Steps, a line of prose under each other heading, and
    `stand_ins` after its docstring."""
    body = "".join(f"## {heading}\n\n" + (steps if heading == "Steps" else "Some words.") + "\n\n"
                   for heading in headings)
    path = tmp_path / name
    path.write_text(f'"""Try it\n\nFor: {group}\n\n{body}"""\n{stand_ins}', encoding="utf-8")
    return path


def test_a_warning_a_step_gives_is_shown_with_its_message(tmp_path: Path) -> None:
    """Common mistakes show the repeated-rows Warning as the step really gives it."""
    path = a_how_to(tmp_path, """>>> from sqlglot_composer import *
>>> job_runs = example_database.job_runs
>>> run_alerts = example_database.run_alerts
>>> alerts = statement(
...     SELECT(job_runs.run_id, run_alerts.alert_id),
...     FROM(job_runs),
...     JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id)),
...     WHERE(equals(job_runs.dt, "2026-09-24"), equals(run_alerts.dt, "2026-09-24")),
... )""")
    shown = how_to_page.how_to_html(how_to_page.read_how_to(path))
    assert '<p class="label">It builds, with a Warning</p>' in shown
    assert ("JOIN(run_alerts) matches on run_id, but a run_alerts row is told apart only by "
            "its Key (alert_id).") in page_text(shown)


@pytest.mark.needs_example_database
def test_a_file_a_step_writes_is_shown_in_full_or_by_name(tmp_path: Path) -> None:
    path = a_how_to(tmp_path, """>>> from sqlglot_composer import *
>>> path = write_table_reference("ops.run_alerts", query=example_database.query)
>>> job_runs = example_database.job_runs
>>> failed = statement(
...     SELECT(job_runs.run_id),
...     FROM(job_runs),
...     WHERE(equals(job_runs.dt, "2026-09-24"), equals(job_runs.status, "FAILED")),
... )
>>> html_file, markdown_file = export_lineage(failed)""")
    shown = how_to_page.how_to_html(how_to_page.read_how_to(path))
    table_reference = re.search(r'<p class="label">It writes ops__run_alerts.py</p>\n'
                                r'<pre class="python">(.*?)</pre>', shown, re.DOTALL)
    assert f"from {FOLDER} import Table" in page_text(table_reference.group(1))
    assert "key=None, # TODO" in page_text(table_reference.group(1))
    stem = "lineage/20260925-090000_1a2b3c4_lineage_notebook_failed"
    markdown = re.search(rf'<p class="label">It writes {stem}.md</p>\n<pre class="file">(.*?)'
                         "</pre>", shown, re.DOTALL)
    assert (f"Made by export_lineage on 2026-09-25 09:00, from your scripts at commit 1a2b3c4, "
            f"with {PRODUCT} {sqlglot_composer.TOOLBOX_VERSION}.") in page_text(
                markdown.group(1))
    assert (f'<p class="note">It writes <code>{stem}.html</code> too, a page to open in your '
            "browser.</p>") in shown
    assert str(tmp_path) not in shown


def test_a_long_file_a_step_writes_is_folded_and_a_file_shown_before_is_not_shown_again(
        tmp_path: Path) -> None:
    lines = how_to_page.FOLD_AFTER + 1
    path = a_how_to(tmp_path, f""">>> from pathlib import Path
>>> long_text = "".join(f"line {{number}}" + chr(10) for number in range({lines}))
>>> size = Path("short.md").write_text("A short file." + chr(10))
>>> size = Path("long.md").write_text(long_text)
>>> size = Path("again.md").write_text(long_text)""")
    shown = how_to_page.how_to_html(how_to_page.read_how_to(path))
    assert '<p class="label">It writes short.md</p>\n<pre class="file">A short file.</pre>' in shown
    assert (f'<p class="label">It writes long.md</p>\n<details><summary>Show its '
            f'{lines} lines</summary>\n<pre class="file">line 0\n') in shown
    assert shown.count("line 0\n") == 1
    assert ('<p class="note">It writes <code>again.md</code> too, line for line the same as '
            "<code>long.md</code> above.</p>") in shown


def test_a_step_that_writes_many_files_names_them_in_one_list(tmp_path: Path) -> None:
    path = a_how_to(tmp_path, """>>> from sqlglot_composer import project
>>> project.start()
Started a Project in the folder you're working in: admin/, references/, building_blocks/,
tables/ and warehouse.py. Next: write your query and execute in warehouse.py.""")
    shown = how_to_page.how_to_html(how_to_page.read_how_to(path))
    files = re.search(r'<p class="label">It writes (\d+) files</p>\n<pre class="file">(.*?)'
                      "</pre>", shown, re.DOTALL)
    assert int(files.group(1)) > how_to_page.LIST_AFTER
    assert page_text(files.group(2)).split()[-1] == "warehouse.py"
    assert "admin/templates/saved_table.py" in page_text(files.group(2))
    assert "It writes warehouse.py" not in shown


def test_a_warning_a_clause_gives_is_shown_with_its_message(tmp_path: Path) -> None:
    path = a_how_to(tmp_path, """>>> from sqlglot_composer import *
>>> job_runs = example_database.job_runs
>>> run_alerts = example_database.run_alerts
>>> joined = JOIN(run_alerts, ON=equals(run_alerts.run_id, job_runs.run_id))""")
    shown = how_to_page.how_to_html(how_to_page.read_how_to(path))
    warned = re.search(r'<p class="label">It builds, with a Warning</p>\n?'
                       r'<pre class="refusal">(.*?)</pre>', shown, re.DOTALL)
    assert page_text(warned.group(1)).startswith(
        "RepeatedRowsWarning: What happened: JOIN(run_alerts) matches on run_id")


# A Statement the Example database can't run: its executor has no week_start.
WEEKS = """>>> from sqlglot_composer import *
>>> job_runs = example_database.job_runs
>>> weeks = statement(
...     SELECT_DISTINCT(job_runs.dt, AS(week_start(job_runs.dt), "week")),
...     FROM(job_runs),
...     WHERE(between(job_runs.dt, "2026-09-23", "2026-09-24")),
... )
>>> run(weeks, query=example_database.query)"""
WEEKS_IN_PANDAS = '''
import pandas as pd


def weeks_in_pandas():
    return pd.DataFrame({"dt": ["2026-09-23", "2026-09-24"], "week": ["stand", "in"]})
'''


@pytest.mark.needs_example_database
def test_a_pandas_stand_in_gives_what_the_example_database_cannot(tmp_path: Path) -> None:
    path = a_how_to(tmp_path, WEEKS, stand_ins=WEEKS_IN_PANDAS)
    shown = how_to_page.how_to_html(how_to_page.read_how_to(path))
    cells = re.findall(r"<td>(.*?)</td>", shown)
    assert f'<p class="label">Result, {example_gallery.PANDAS_LABEL}</p>' in shown
    assert cells == ["2026-09-23", "stand", "2026-09-24", "in"]
    assert "stops" not in shown


@pytest.mark.needs_example_database
def test_without_its_stand_in_the_statement_shows_why_it_cannot_run(tmp_path: Path) -> None:
    shown = how_to_page.how_to_html(how_to_page.read_how_to(a_how_to(tmp_path, WEEKS)))
    assert "The Example database can&#x27;t run this Hive" in shown


def test_a_stand_in_for_no_statement_is_refused(tmp_path: Path) -> None:
    path = a_how_to(tmp_path, ">>> weeks = 1", stand_ins=WEEKS_IN_PANDAS)
    with pytest.raises(how_to_page.HowToRefused, match="makes a Statement weeks"):
        how_to_page.how_to_html(how_to_page.read_how_to(path))


def test_a_how_to_without_the_fixed_headings_in_order_is_refused(tmp_path: Path) -> None:
    headings = list(how_to_page.HEADINGS)
    headings[0], headings[1] = headings[1], headings[0]
    path = a_how_to(tmp_path, "Words.", headings=headings)
    with pytest.raises(how_to_page.HowToRefused, match="must have the headings ## Goal"):
        how_to_page.sections(how_to_page.read_how_to(path))


@pytest.mark.parametrize(("name", "group", "says"), [
    ("22_try_it.py", "Getting started", "the Getting started how-tos are 1 to 21"),
    ("02_try_it.py", "Intermediate", "the Intermediate how-tos are 22 to 40"),
    ("02_try_it.py", "Advanced", "says `For: Advanced`"),
])
def test_a_how_to_s_for_line_must_name_a_group_holding_its_number(tmp_path: Path, name: str,
                                                                  group: str, says: str) -> None:
    with pytest.raises(how_to_page.HowToRefused, match=says):
        how_to_page.read_how_to(a_how_to(tmp_path, "Words.", name=name, group=group))


def test_a_step_that_shows_the_folder_it_ran_in_is_refused(tmp_path: Path) -> None:
    path = a_how_to(tmp_path, ">>> import os\n>>> os.getcwd()")
    with pytest.raises(how_to_page.HowToRefused, match="differs from one computer to another"):
        how_to_page.how_to_html(how_to_page.read_how_to(path))


@pytest.mark.parametrize("target", ["https://example.com", "#no_such_how_to",
                                    "examples.html#no_such_entry", "README.md"])
def test_a_link_that_lands_nowhere_is_refused(target: str) -> None:
    with pytest.raises(how_to_page.HowToRefused, match="neither a how-to nor an entry"):
        how_to_page.check_links(f'<p id="here"><a href="{target}">there</a></p>')
