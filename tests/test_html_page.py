"""The HTML standard's rules a test can hold, and the one page module every lineage page comes
from: Toolbox 8.7, ticket 04 (docs/agents/standards.md, "HTML pages"); and its bold colours,
ticket 05.

export_lineage, project.export_run_lineage and project.export_project_lineage each write an
HTML page and its Markdown twin. Each page is built from `sqlglot_composer/html_page.py`, which
holds the colour tokens, each written once, the base CSS, the legend, the Mermaid classDef lines
and the drawing's script. The tests read the pages the three exports write, and the Toolbox's
own files: no colour is written outside the token table, no page has an inline style, every
page loads nothing from outside itself, and every page comes from the one module.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from types import ModuleType

import pytest
from conftest import toolbox_folder, toolbox_module
from offline_policy import external_references
from test_lineage import BY_HAND, runs_per_team
from test_project_lineage import LOGIC, NOW, STEM, make_a_loop, new_run

from sqlglot_composer import export_lineage, project, set_admin_log, unchecked_hive

TOOLBOX = toolbox_folder()
# The name project.export_run_lineage gives the run weekly's page, at the time the tests pin.
RUN_STEM = "20261109-093000-weekly"
# A colour written as hex, #rgb to #rrggbbaa, but not an HTML character code such as &#9888;.
HEX = re.compile(r"(?<![&\w])#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6}|[0-9a-fA-F]{3,4})\b")
# A colour written as a CSS function.
COLOUR_FUNCTION = re.compile(r"\b(?:rgba?|hsla?)\(")
# A style attribute, in markup or in markup a script writes.
STYLE_ATTRIBUTE = re.compile(r"\sstyle\s*=", re.IGNORECASE)
# The block of the page's CSS that defines each token, and a CSS line that names one.
TOKEN_BLOCK = re.compile(r":root\{[^}]*\}")
TOKEN_USE = re.compile(r"var\(--([\w-]+)\)")


def html_page() -> ModuleType:
    """The page module, sqlglot_composer/html_page.py."""
    return toolbox_module("html_page")


@pytest.fixture
def pages(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, tuple[str, str]]:
    """Each page the three exports write, by what wrote it: the HTML, then its Markdown twin.
    The Project's page is written twice, read as soon as it is written: with a loop, then with
    a table two Scheduled runs write."""
    html_file, _ = export_lineage(runs_per_team(), unchecked_hive(BY_HAND),
                                  to=tmp_path / "statements" / "lineage.html")
    read = {"export_lineage": texts(html_file)}
    root = tmp_path / "project"
    root.mkdir()
    monkeypatch.setattr(toolbox_module("unchecked"), "now", lambda: NOW)
    set_admin_log()
    monkeypatch.chdir(root)
    project.start()
    for name, logic in LOGIC.items():
        template = name.replace(".", "_")
        (root / "admin" / "templates" / f"{template}.py").write_text(
            f"# %%\n# logic\n{logic}", encoding="utf-8")
        project.new_table(name, template=template)
    monkeypatch.chdir(root / "admin")
    notebook = root / "tables" / "mart__team_jobs" / "mart__team_jobs.ipynb"
    without_a_loop = notebook.read_bytes()
    make_a_loop(root)
    project.export_project_lineage()
    read["export_project_lineage, a loop"] = texts(project_page(root))
    notebook.write_bytes(without_a_loop)
    new_run(root, "weekly")
    new_run(root, "daily", scheduled='''# scheduled
def statements():
    return {"count": project.load("mart.team_count").write()}
''')
    project.export_run_lineage("weekly")
    read["export_run_lineage"] = texts(
        root / "scheduled_runs" / "weekly" / "lineage" / f"{RUN_STEM}.html")
    project.export_project_lineage()
    read["export_project_lineage"] = texts(project_page(root))
    return read


def project_page(root: Path) -> Path:
    """The page project.export_project_lineage writes, at the time the tests pin."""
    return root / "admin" / "lineage" / f"{STEM}.html"


def texts(html_file: Path) -> tuple[str, str]:
    """An HTML page and its Markdown twin, as text."""
    return (html_file.read_text(encoding="utf-8"),
            html_file.with_suffix(".md").read_text(encoding="utf-8"))


def toolbox_files() -> list[Path]:
    """Each Python file of the Toolbox's folder."""
    return sorted(TOOLBOX.glob("*.py"))


def token_table_lines() -> range:
    """The lines of html_page.py that the token table, COLOURS, takes up."""
    tree = ast.parse((TOOLBOX / "html_page.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.AnnAssign | ast.Assign) and "COLOURS" in ast.unparse(node):
            return range(node.lineno, node.end_lineno + 1)
    raise AssertionError("html_page.py has no COLOURS")


# --- The token table --------------------------------------------------------------------------


@pytest.mark.parametrize("path", toolbox_files(), ids=lambda path: path.name)
def test_no_colour_is_written_outside_the_token_table(path: Path) -> None:
    table = token_table_lines() if path.name == "html_page.py" else range(0)
    found = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        colours = HEX.findall(line) + COLOUR_FUNCTION.findall(line)
        if colours and number not in table:
            found.append(f"line {number}: {', '.join(colours)}")
    assert found == []


def test_each_token_is_a_colour_and_each_kind_names_tokens() -> None:
    module = html_page()
    assert all(HEX.fullmatch(value) for value in module.COLOURS.values())
    for kind in module.KINDS.values():
        assert {kind.fill, kind.edge} - {None} <= set(module.COLOURS)


def test_a_colour_changed_in_the_token_table_changes_the_page_and_the_markdown(
        pages: dict[str, tuple[str, str]], monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path) -> None:
    monkeypatch.setitem(html_page().COLOURS, "folder", "#123456")
    project.export_project_lineage()
    page, markdown = texts(project_page(tmp_path / "project"))
    assert "--folder:#123456" in TOKEN_BLOCK.search(page)[0]
    assert "  classDef folder fill:#123456,stroke:#888" in markdown


# --- The rules each page keeps ----------------------------------------------------------------


def test_each_page_names_its_colours_only_through_the_tokens(
        pages: dict[str, tuple[str, str]]) -> None:
    tokens = html_page().COLOURS
    for made_by, (page, _) in pages.items():
        assert len(TOKEN_BLOCK.findall(page)) == 1, made_by
        rest = TOKEN_BLOCK.sub("", page)
        assert HEX.findall(rest) + COLOUR_FUNCTION.findall(rest) == [], made_by
        assert set(TOKEN_USE.findall(page)) <= set(tokens), made_by


def test_each_markdown_writes_only_the_tokens_colours(
        pages: dict[str, tuple[str, str]]) -> None:
    tokens = set(html_page().COLOURS.values())
    for made_by, (_, markdown) in pages.items():
        assert set(HEX.findall(markdown)) <= tokens, made_by


def test_no_page_has_an_inline_style(pages: dict[str, tuple[str, str]]) -> None:
    for made_by, (page, _) in pages.items():
        assert STYLE_ATTRIBUTE.findall(page) == [], made_by


def test_every_page_loads_nothing_from_outside_itself(
        pages: dict[str, tuple[str, str]]) -> None:
    for made_by, (page, _) in pages.items():
        assert external_references(page) == [], made_by


# --- One page module --------------------------------------------------------------------------


def test_every_page_comes_from_the_one_module(pages: dict[str, tuple[str, str]]) -> None:
    module = html_page()
    assert set(pages) >= {"export_lineage", "export_run_lineage", "export_project_lineage"}
    for made_by, (page, _) in pages.items():
        assert page.startswith("<!doctype html>\n<html><head><meta charset=\"utf-8\">"), made_by
        assert module.BASE_CSS in page, made_by
        assert '<div class="key">' in page, made_by


def test_the_drawings_script_comes_from_the_module(pages: dict[str, tuple[str, str]]) -> None:
    module = html_page()
    for made_by in ("export_lineage", "export_run_lineage"):
        page = pages[made_by][0]
        assert module.DRAWING_CSS in page, made_by
        assert module.DRAWING_SCRIPT in page, made_by


def test_the_projects_markdown_colours_its_boxes_with_the_modules_classdefs(
        pages: dict[str, tuple[str, str]]) -> None:
    lines = html_page().mermaid_class_defs(["folder", "saved", "read", "shared", "loop"])
    assert lines[0] == "  classDef folder fill:#56b4e9,stroke:#888"
    for made_by in ("export_project_lineage", "export_project_lineage, a loop"):
        markdown = pages[made_by][1]
        assert "\n".join(lines) in markdown, made_by


# --- Bold colours (ticket 05) -----------------------------------------------------------------

def six_digits(colour: str) -> str:
    """A hex colour written #rrggbb in lower case, however the token table writes it."""
    digits = colour.lstrip("#").lower()
    if len(digits) == 3:
        digits = "".join(digit * 2 for digit in digits)
    return f"#{digits}"


def luminance(colour: str) -> float:
    """A colour's relative luminance, as WCAG 2 works it out from its sRGB value."""
    digits = six_digits(colour)[1:]
    channels = []
    for start in (0, 2, 4):
        value = int(digits[start:start + 2], 16) / 255
        channels.append(value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4)
    red, green, blue = channels
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast(one: str, other: str) -> float:
    """WCAG 2's contrast ratio of two colours, from 1 to 21."""
    lighter, darker = sorted([luminance(one), luminance(other)], reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def page_kinds(made_by: str) -> list[str]:
    """The kinds of box the page made by `made_by` draws, as its legend names them."""
    builder = toolbox_module("project_lineage" if "project" in made_by else "lineage")
    return [kind for kind, _ in builder.LEGEND if kind is not None]


def kind_colour(name: str) -> str:
    """A kind's colour, the one that tells it apart: its fill, or its edge if it has none."""
    kind = html_page().KINDS[name]
    return six_digits(html_page().COLOURS[kind.fill or kind.edge])


def test_the_contrast_is_worked_out_as_wcag_says() -> None:
    assert contrast("#000", "#fff") == pytest.approx(21)
    assert contrast("#777", "#fff") == pytest.approx(4.48, abs=0.01)


def test_a_boxs_text_reads_on_every_kinds_fill() -> None:
    colours = html_page().COLOURS
    for name, kind in html_page().KINDS.items():
        if kind.fill is None:
            continue
        for text in ("ink", "box-text"):  # a box's first line, and its others
            assert contrast(colours[text], colours[kind.fill]) >= 4.5, (name, text)
    assert contrast(colours["loop-text"], colours["page"]) >= 4.5


def test_no_two_kinds_on_one_page_share_a_colour(pages: dict[str, tuple[str, str]]) -> None:
    for made_by in pages:
        colours = [kind_colour(name) for name in page_kinds(made_by)]
        assert len(colours) == len(set(colours)), made_by


def test_the_loops_red_is_used_for_nothing_else() -> None:
    colours = html_page().COLOURS
    red = six_digits(colours["loop"])
    assert [name for name, value in colours.items() if six_digits(value) == red] == ["loop"]


@pytest.mark.parametrize("path", toolbox_files(), ids=lambda path: path.name)
def test_only_the_page_module_starts_a_page_or_its_css(path: Path) -> None:
    if path.name == "html_page.py":
        return
    text = path.read_text(encoding="utf-8").lower()
    assert ("<!doctype" not in text and "<style" not in text and ":root{" not in text)


def test_the_legend_draws_each_kind_by_its_class() -> None:
    legend = html_page().legend([("table", "table column"), (None, "an <arrow> & a note")])
    assert legend == ('<div class="key">\n<span><i class="sw table"></i>table column</span>\n'
                      "<span>an &lt;arrow&gt; &amp; a note</span>\n</div>")
