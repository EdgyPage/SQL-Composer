"""The HTML standard's rules a test can hold, and the one page module every lineage page comes
from: Toolbox 8.7, ticket 04 (docs/agents/standards.md, "HTML pages").

export_lineage, project.export_run_lineage and project.export_project_lineage each write an
HTML page and its Markdown twin. Each page is built from `sqlglot_composer/html_page.py`, which
holds the colour tokens, each written once, the base CSS, the legend, the drawing's script and
the side panel's. The tests read the pages the three exports write, and the Toolbox's own files:
no colour is written outside the token table, no page has an inline style, every page loads
nothing from outside itself, and every page comes from the one module. Since ticket 06, a click
on a box opens a panel, and each line of a page's Markdown twin is on its HTML page too.
"""

from __future__ import annotations

import ast
import html
import json
import re
from pathlib import Path
from types import ModuleType

import pytest
from conftest import toolbox_folder, toolbox_module
from offline_policy import external_references
from test_lineage import BY_HAND, runs_per_team
from test_project_lineage import LOGIC, NOW, STEM, make_a_loop, new_run

from sqlglot_composer import export_lineage, project, set_admin_log, to_hive, unchecked_hive

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


def test_a_colour_changed_in_the_token_table_changes_the_page(
        pages: dict[str, tuple[str, str]], monkeypatch: pytest.MonkeyPatch,
        tmp_path: Path) -> None:
    monkeypatch.setitem(html_page().COLOURS, "folder", "#123456")
    project.export_project_lineage()
    page, _ = texts(project_page(tmp_path / "project"))
    assert "--folder:#123456" in TOKEN_BLOCK.search(page)[0]


# --- The rules each page keeps ----------------------------------------------------------------


def test_each_page_names_its_colours_only_through_the_tokens(
        pages: dict[str, tuple[str, str]]) -> None:
    tokens = html_page().COLOURS
    for made_by, (page, _) in pages.items():
        assert len(TOKEN_BLOCK.findall(page)) == 1, made_by
        rest = TOKEN_BLOCK.sub("", page)
        assert HEX.findall(rest) + COLOUR_FUNCTION.findall(rest) == [], made_by
        assert set(TOKEN_USE.findall(page)) <= set(tokens), made_by


def test_no_markdown_draws_or_colours(pages: dict[str, tuple[str, str]]) -> None:
    for made_by, (_, markdown) in pages.items():
        assert "```mermaid" not in markdown, made_by
        assert "classDef" not in markdown, made_by
        assert HEX.findall(markdown) == [], made_by


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


def test_the_drawings_and_the_panels_script_comes_from_the_module(
        pages: dict[str, tuple[str, str]]) -> None:
    module = html_page()
    for made_by, (page, _) in pages.items():
        for piece in (module.DRAWING_CSS, module.PANEL_CSS, module.DRAWING_SCRIPT,
                      module.PANEL_SCRIPT):
            assert piece in page, made_by


# --- The side panel and the Markdown: Toolbox 8.7, ticket 06 --------------------------------


def text_shown(page: str) -> str:
    """What a reader of an HTML page can read in it: its body, scripts left out, every tag
    taken away and every character code read."""
    body = page.split("<body>", 1)[1]
    body = re.sub(r"<script>.*?</script>", "", body, flags=re.DOTALL)
    return html.unescape(re.sub(r"<[^>]+>", "", body))


def markdown_text(line: str) -> str:
    """A line of Markdown as a reader reads it: its heading's #s, its list's "- ", its quote's
    "> ", its bold's ** and its inline code's backticks taken away."""
    line = re.sub(r"^(?:#+ |- |> )", "", line).replace("**", "")
    return re.sub(r"(`+) ?(.*?) ?\1", r"\2", line)


def markdown_lines(markdown: str) -> list[str]:
    """Each line of a Markdown page a reader reads, as markdown_text gives it: a fenced block's
    lines as they are, and no fence, rule or empty line."""
    lines, fenced = [], False
    for line in markdown.splitlines():
        if line.startswith("```"):
            fenced = not fenced
        elif fenced:
            lines.append(line)
        elif line.strip() and line != "---":
            lines.append(markdown_text(line))
    return lines


def test_every_line_of_each_markdown_is_in_its_html_too(
        pages: dict[str, tuple[str, str]]) -> None:
    for made_by, (page, markdown) in pages.items():
        shown = text_shown(page)
        assert [line for line in markdown_lines(markdown) if line not in shown] == [], made_by


def test_each_page_has_a_panel_and_no_report(pages: dict[str, tuple[str, str]]) -> None:
    for made_by, (page, _) in pages.items():
        assert '<aside id="panel"' in page, made_by
        assert 'id="report"' not in page, made_by


def test_the_markdown_keeps_each_step_what_it_reads_and_writes_and_its_hive(
        pages: dict[str, tuple[str, str]]) -> None:
    markdown = pages["export_lineage"][1]
    assert "\n## statement_1\n" in markdown
    assert ("- Reads: ops.job_runs, ops.jobs\n- Writes: no table, its rows come back to you"
            in markdown)
    assert "### Hive as submitted\n\n```sql\nSELECT\n" in markdown
    project_markdown = pages["export_project_lineage"][1]
    assert "\n## `mart.teams`\n" in project_markdown
    assert "- Written by Scheduled runs: weekly and daily ⚠" in project_markdown
    assert "INSERT OVERWRITE TABLE mart.teams" in project_markdown


def boxes_of(page: str) -> list[str]:
    """Each box a page draws in Python, as its <g ...> tag."""
    return re.findall(r'<g class="n [^"]*"[^>]*>', page)


def test_each_project_box_is_reached_with_tab_and_opens_its_part(
        pages: dict[str, tuple[str, str]]) -> None:
    for made_by in ("export_project_lineage", "export_project_lineage, a loop"):
        page = pages[made_by][0]
        boxes = boxes_of(page)
        assert boxes, made_by
        for box in boxes:
            assert 'tabindex="0"' in box and 'role="button"' in box, box
            for part in re.search(r'data-parts="([^"]*)"', box)[1].split():
                assert f'<div class="part" id="{part}">' in page, box


def test_each_statement_box_opens_a_part_of_its_step(
        pages: dict[str, tuple[str, str]]) -> None:
    for made_by in ("export_lineage", "export_run_lineage"):
        page = pages[made_by][0]
        data = json.loads(re.search(r"const graph = (\{.*\});\n", page)[1])
        for box in data["boxes"]:
            assert box["parts"], box
            for part in box["parts"]:
                assert f'<div class="part" id="{part}">' in page, box
            if box["entry"]:
                assert f'<div class="part" id="{box["entry"]}">' in page, box
        assert 'tabindex="0" role="button"' in page, made_by


def test_the_panel_shows_a_steps_hive_whole_with_a_copy_button(
        pages: dict[str, tuple[str, str]]) -> None:
    page = pages["export_lineage"][0]
    hive = html.escape(to_hive(runs_per_team()))
    button = '<button type="button" class="copy">Copy</button>'
    assert f'<div class="hive">{button}<pre>{hive}</pre>' in page
    assert "<li>Reads: ops.job_runs, ops.jobs</li>" in page


def test_the_project_panel_shows_each_table_its_runs_and_its_hive(
        pages: dict[str, tuple[str, str]]) -> None:
    page = pages["export_project_lineage"][0]
    team_jobs = page.split("<h2><code>mart.team_jobs</code></h2>", 1)[1].split("<h2>", 1)[0]
    assert "<li>Written by Scheduled runs: weekly and daily ⚠</li>" in team_jobs
    assert "<li>Run value: logic of mart.team_jobs.first_job() gave 1</li>" in team_jobs
    assert "<h3>Hive as submitted by its Table folder, the Scheduled run weekly and the " \
        "Scheduled run daily</h3>" in team_jobs
    assert '<button type="button" class="copy">Copy</button>' in team_jobs


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
