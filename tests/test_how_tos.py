"""The how-tos, and the page each Edition ships them on, `how_to.html`.

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
import json
import re
import shutil
import subprocess
import textwrap
import warnings
from pathlib import Path

import pytest

import editions
import how_to_page
import sqlglot_composer
from conftest import edition, gallery_sections, page_text, toolbox_folder
from test_example_gallery import TagCounter

ROOT = Path(__file__).resolve().parent.parent
PAGE = toolbox_folder() / "how_to.html"
HOW_TOS = how_to_page.how_to_paths()
SLUGS = [how_to_page.slug_of(path) for path in HOW_TOS]
PUBLIC = set(sqlglot_composer.__all__)
# Names a how-to may use without defining them: what a notebook at work has (its `spark`
# session, the query API a send calls), the Example database's database, and the Toolbox's
# folders.
OUTSIDE_NAMES = {"spark", "my_api", "ops", editions.CORE, *editions.EDITIONS}


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
        f"{PAGE.relative_to(ROOT).as_posix()} is out of date: run python tools/how_to_page.py "
        f"--edition {edition().option}"
    )


def test_there_is_a_how_to_and_how_to_1_starts_a_notebook() -> None:
    assert SLUGS[:1] == ["start_a_notebook"]
    assert HOW_TOS[0].stem.startswith("01_")


# --- Each how-to's source --------------------------------------------------------------------


@pytest.mark.needs_example_database
@pytest.mark.parametrize("path", HOW_TOS, ids=lambda path: path.stem)
def test_each_how_to_runs_as_a_doctest(path: Path, tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    text = how_to_page.edition_text(how_to_page.docstring_of(path), edition())
    test = doctest.DocTestParser().get_doctest(text, {}, path.stem, str(path), 0)
    runner = doctest.DocTestRunner(optionflags=doctest.NORMALIZE_WHITESPACE | doctest.ELLIPSIS)
    report = []
    # A Warning is shown on the page; here it may not stop the step it comes from.
    with warnings.catch_warnings(record=True):
        warnings.simplefilter("always")
        runner.run(test, out=report.append)
    assert runner.failures == 0, "".join(report)


@pytest.mark.parametrize("path", HOW_TOS, ids=lambda path: path.stem)
def test_a_how_to_has_its_title_its_level_and_the_fixed_headings_in_order(path: Path) -> None:
    doc = how_to_page.docstring_of(path)
    lines = doc.splitlines()
    assert lines[0].strip() and lines[1] == "" and lines[3] == ""
    level = re.fullmatch(r"Level: (.+)", lines[2]).group(1)
    assert int(path.stem[:2]) in how_to_page.LEVELS[level][1]
    assert re.findall(r"^## (.+)$", doc, re.MULTILINE) == list(how_to_page.HEADINGS)


def code_and_prose(path: Path) -> tuple[list[str], list[str]]:
    """A how-to's code, its >>> steps and indented code, and its `backticked` spans of prose,
    on both Editions' pages."""
    code, spans = [], []
    for each in editions.EDITIONS.values():
        text = how_to_page.edition_text(how_to_page.docstring_of(path), each)
        for part in doctest.DocTestParser().parse(text):
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
            if isinstance(node, ast.ImportFrom) and node.module in editions.EDITIONS:
                assert {alias.name for alias in node.names} - {"*"} <= PUBLIC, ast.unparse(node)
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
    return {target for each in editions.EDITIONS.values()
            for _, target in how_to_page.LINK.findall(
                how_to_page.edition_text(how_to_page.docstring_of(path), each))}


@pytest.mark.parametrize("path", HOW_TOS, ids=lambda path: path.stem)
def test_each_link_goes_to_a_how_to_or_a_gallery_entry_that_exists(path: Path) -> None:
    for target in link_targets(path):
        page_name, _, place = target.partition("#")
        if page_name == "":
            assert place in SLUGS, f"no how-to {place}"
        else:
            assert page_name == "examples.html", f"{target} is neither a how-to nor the gallery"
            for each in editions.EDITIONS.values():
                assert not place or place in gallery_sections(ROOT / each.folder), (
                    f"no entry {place} on {each.product}'s Example gallery")


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


def test_each_level_has_its_heading_and_contents_and_each_how_to_its_badge() -> None:
    text = page()
    for level, (level_id, numbers, _) in how_to_page.LEVELS.items():
        assert f'<h2 id="{level_id}">{level}</h2>' in text
        contents = re.search(rf'<a href="#{level_id}">{level}</a>.*?</div>', text, re.DOTALL)
        listed = re.findall(r'data-for="([^"]+)"', contents.group(0))
        at_level = [how_to_page.read_how_to(path) for path in HOW_TOS]
        assert listed == [how_to.slug for how_to in at_level if how_to.level == level]
        for how_to in at_level:
            if how_to.level == level:
                assert how_to.number in numbers
                assert (f'<h3>{how_to.number}. {how_to.title} <span class="badge {level_id}">'
                        f"{level}</span></h3>") in page_sections()[how_to.slug]
    # The levels come in order, with Getting started first.
    assert text.index('id="getting-started"') < text.index('id="intermediate"')


def test_every_how_to_is_on_the_page_in_number_order() -> None:
    assert list(page_sections()) == SLUGS


def test_the_page_needs_no_other_file() -> None:
    for outside in ("src=", "<link", "@import", "url(", "http://", "https://"):
        assert outside not in page()


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
    """Common mistakes show the refusal the step really gives, not text pasted in."""
    from composer_core.refusals import refuse_a_spark_dataframe

    class SparkDataFrame:
        def toPandas(self):  # noqa: N802 - Spark's own name
            return None

    with pytest.raises(TypeError) as refused:
        refuse_a_spark_dataframe(SparkDataFrame())
    shown = re.findall(r'<pre class="refusal">(.*?)</pre>', page_sections()["start_a_notebook"],
                       re.DOTALL)
    assert page_text(f"<p>TypeError:\n{refused.value}</p>") in [page_text(f"<p>{block}</p>")
                                                               for block in shown]


def test_a_step_that_prints_hive_shows_it_as_hive_ready_to_paste() -> None:
    section = page_sections()["start_a_notebook"]
    assert ('<p class="label">Hive, ready to paste</p><pre class="hive">SELECT' in section)
    assert "&#x27;2026-09-24&#x27;;</pre>" in section


def test_a_result_shows_as_a_table() -> None:
    cells = re.findall(r"<td>(.*?)</td>", page_sections()["start_a_notebook"])
    assert cells[:6] == ["97", "3", "2026-09-23", "102", "2", "2026-09-24"]


# --- The page's script -----------------------------------------------------------------------


def the_script() -> str:
    scripts = re.findall(r"<script>\n(.*?)</script>", page(), re.DOTALL)
    assert len(scripts) == 1
    return scripts[0]


def test_the_page_has_one_short_script() -> None:
    assert len(the_script().strip().splitlines()) <= 30


# A stand-in for the browser: the page's elements the script reaches, its clipboard and its
# selection. It runs the script, then checks what it did, and prints "ok".
BROWSER = """
const script = __SCRIPT__;
function element(tag, more = {}) {
  return Object.assign({tag, hidden: false, textContent: "", className: "", children: [],
    append(...items) { this.children.push(...items); },
    replaceWith(other) { this.replacedBy = other; }}, more);
}
const input = element("input", {value: ""}), count = element("span");
const filter = element("p", {hidden: true, querySelector: () => input});
const entries = [element("section", {id: "start", textContent: "Start a notebook: send"}),
                 element("section", {id: "join", textContent: "Join tables safely"})];
const items = {start: element("li"), join: element("li")};
const blocks = [element("pre", {className: "python", textContent: "x = 1"}),
                element("pre", {className: "hive", textContent: "SELECT 1;"})];
const copied = [];
let selected = null;
globalThis.document = {
  getElementById: id => ({filter, count})[id],
  querySelectorAll: selector => ({".entry": entries, "pre.python, pre.hive": blocks})[selector],
  querySelector: selector => items[/data-for="([^"]+)"/.exec(selector)[1]],
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
  input.value = "  notebook SEND ";
  input.oninput();
  check(!entries[0].hidden && entries[1].hidden, "only the how-to with every word shows");
  check(!items.start.hidden && items.join.hidden, "its contents line hides with it");
  check(count.textContent === "1 of 2 shown", "the count: " + count.textContent);
  input.value = "";
  input.oninput();
  check(!entries[1].hidden && !items.join.hidden && count.textContent === "2 of 2 shown",
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


def test_the_script_filters_the_how_tos_and_puts_a_copy_button_on_each_block(tmp_path) -> None:
    node = shutil.which("node")
    if node is None:
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


def a_how_to(tmp_path: Path, steps: str, name: str = "01_try_it.py", level: str = "Getting "
             "started", headings=how_to_page.HEADINGS) -> Path:
    """A how-to's file with `steps` under Steps, and a line of prose under each other heading."""
    body = "".join(f"## {heading}\n\n" + (steps if heading == "Steps" else "Some words.") + "\n\n"
                   for heading in headings)
    path = tmp_path / name
    path.write_text(f'"""Try it\n\nLevel: {level}\n\n{body}"""\n', encoding="utf-8")
    return path


@pytest.mark.needs_example_database
def test_a_file_a_step_writes_is_shown_in_full_or_by_name(tmp_path) -> None:
    path = a_how_to(tmp_path, """>>> from sqlglot_composer import *
>>> path = write_table_reference("ops.run_alerts", send=example_database.send)
>>> job_runs = example_database.job_runs
>>> failed = statement(
...     SELECT(job_runs.run_id),
...     FROM(job_runs),
...     WHERE(equals(job_runs.dt, "2026-09-24"), equals(job_runs.status, "FAILED")),
... )
>>> html_file, markdown_file = export_lineage(failed)""")
    shown = how_to_page.how_to_html(how_to_page.read_how_to(path))
    table_reference = re.search(r'<p class="label">It writes run_alerts.py</p>\n'
                                r'<pre class="python">(.*?)</pre>', shown, re.DOTALL)
    assert f"from {edition().folder} import Table" in page_text(table_reference.group(1))
    assert "key=None, # TODO" in page_text(table_reference.group(1))
    stem = "lineage/20260925-090000_1a2b3c4_lineage_notebook_failed"
    markdown = re.search(rf'<p class="label">It writes {stem}.md</p>\n<pre class="file">(.*?)'
                         "</pre>", shown, re.DOTALL)
    assert (f"Made by export_lineage on 2026-09-25 09:00, from your scripts at commit 1a2b3c4, "
            f"with {edition().product} {sqlglot_composer.TOOLBOX_VERSION}.") in page_text(
                markdown.group(1))
    assert (f'<p class="note">It writes <code>{stem}.html</code> too, a page to open in your '
            "browser.</p>") in shown
    assert str(tmp_path) not in shown


def test_an_edition_block_shows_only_on_its_own_editions_page() -> None:
    doc = ("Both: sqlglot_composer.\n[sqlglot_composer only]\nOnly sqlglot: spark_composer.\n"
           "[end]\n[spark_composer only]\nOnly Spark: sqlglot_composer.\n[end]\nBoth again.\n")
    assert how_to_page.edition_text(doc, editions.SQLGLOT_COMPOSER) == (
        "Both: sqlglot_composer.\nOnly sqlglot: spark_composer.\nBoth again.\n")
    assert how_to_page.edition_text(doc, editions.SPARK_COMPOSER, marked=True) == (
        "Both: spark_composer.\n[only]\nOnly Spark: sqlglot_composer.\n[end]\nBoth again.\n")
    shown = how_to_page.prose_html("Both.\n[only]\nMine.\n[end]\n")
    assert shown == '<p>Both.</p>\n<div class="only">\n<p>Mine.</p>\n</div>'


@pytest.mark.parametrize(("doc", "says"), [
    ("[sql_composr only]\nWords.\n[end]\n", "names no Edition"),
    ("[spark_composer only]\n>>> 1 + 1\n2\n[end]\n", "holds a >>> step"),
    ("[spark_composer only]\n### A heading\n[end]\n", "holds a >>> step, a heading"),
    ("Words.\n[end]\n", "opens or closes no block"),
])
def test_an_edition_block_that_breaks_the_rules_is_refused(doc: str, says: str) -> None:
    with pytest.raises(how_to_page.HowToRefused, match=says):
        how_to_page.edition_text(doc, edition())


def test_a_how_to_without_the_fixed_headings_in_order_is_refused(tmp_path) -> None:
    headings = list(how_to_page.HEADINGS)
    headings[0], headings[1] = headings[1], headings[0]
    path = a_how_to(tmp_path, "Words.", headings=headings)
    with pytest.raises(how_to_page.HowToRefused, match="must have the headings ## Goal"):
        how_to_page.sections(how_to_page.read_how_to(path))


@pytest.mark.parametrize(("name", "level", "says"), [
    ("19_try_it.py", "Getting started", "Getting started holds how-tos 1 to 18"),
    ("02_try_it.py", "Intermediate", "Intermediate holds how-tos 19 to 30"),
    ("02_try_it.py", "Advanced", "has the level 'Advanced'"),
])
def test_a_how_to_s_level_must_hold_its_number(tmp_path, name: str, level: str,
                                               says: str) -> None:
    with pytest.raises(how_to_page.HowToRefused, match=says):
        how_to_page.read_how_to(a_how_to(tmp_path, "Words.", name=name, level=level))


def test_a_step_that_shows_the_folder_it_ran_in_is_refused(tmp_path) -> None:
    path = a_how_to(tmp_path, ">>> import os\n>>> os.getcwd()")
    with pytest.raises(how_to_page.HowToRefused, match="differs from one computer to another"):
        how_to_page.how_to_html(how_to_page.read_how_to(path))


@pytest.mark.parametrize("target", ["https://example.com", "#no_such_how_to",
                                    "examples.html#no_such_entry", "README.md"])
def test_a_link_that_lands_nowhere_is_refused(target: str) -> None:
    with pytest.raises(how_to_page.HowToRefused, match="neither a how-to nor an entry"):
        how_to_page.check_links(f'<p id="here"><a href="{target}">there</a></p>')
