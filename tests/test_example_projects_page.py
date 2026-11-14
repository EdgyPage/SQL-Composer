"""The Example projects page, `example_projects.html`: each Example project, shown in place of
the folder main no longer holds (Toolbox 8.7, ticket 13).

`tools/example_projects_page.py` writes the page from dev's `example_projects/`, running each
notebook top to bottom. These tests read the committed copy, and one fails if writing it again
would change it.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

import example_projects_page
import generated_memo
import toolbox_registry
from conftest import docs_folder, toolbox_module
from offline_policy import external_references
from test_example_gallery import TagCounter
from test_html_page import COLOUR_FUNCTION, HEX, STYLE_ATTRIBUTE, TOKEN_BLOCK, TOKEN_USE

ROOT = Path(__file__).resolve().parent.parent
PAGE = docs_folder() / "example_projects.html"
PROJECTS = example_projects_page.PROJECTS
project_files = example_projects_page.project_files


def page() -> str:
    return PAGE.read_text(encoding="utf-8")


def file_sections() -> dict[str, str]:
    """Each file's place on the page, by its id, such as starter/admin/run_tables.ipynb: its
    HTML."""
    return {html.unescape(found[0]): found[1] for found in re.findall(
        r'<section class="file"><h3 id="([^"]+)">(.*?)</section>', page(), re.DOTALL)}


def test_the_committed_page_is_what_the_tool_writes() -> None:
    # Locally only when an input changed since it last passed; on CI, always.
    memo = generated_memo.Memo("example_projects_page")
    if memo.is_unchanged():
        return
    committed = page() if PAGE.exists() else ""
    assert example_projects_page.page_text() == committed, (
        f"{PAGE.relative_to(ROOT).as_posix()} is out of date: run python "
        "tools/example_projects_page.py")
    memo.keep()


def test_it_shows_each_example_project_dev_holds() -> None:
    assert sorted(path.name for path in (ROOT / "example_projects").iterdir()) == sorted(
        PROJECTS)
    for project in PROJECTS:
        assert f'<section class="project" id="{project}">' in page()


def test_each_file_of_each_project_has_its_place_and_is_in_its_tree() -> None:
    sections = file_sections()
    for project in PROJECTS:
        tree = page().split(f'<section class="project" id="{project}">', 1)[1].split(
            '<div class="tree">', 1)[1].split("</div>", 1)[0]
        for path in project_files(project):
            assert f"{project}/{path}" in sections, path
            assert f'href="#{html.escape(f"{project}/{path}")}"' in tree, path


def code_cell_count(project: str, path: str) -> int:
    notebook = ROOT / "example_projects" / project / path
    cells = json.loads(notebook.read_text(encoding="utf-8"))["cells"]
    return sum(cell["cell_type"] == "code" for cell in cells)


def test_each_notebook_shows_each_code_cell_with_what_it_gave() -> None:
    """Each code cell, then what it gave, or that it didn't run after a cell that stopped."""
    for (key, section) in file_sections().items():
        if not key.endswith(".ipynb"):
            continue
        project, path = key.split("/", 1)
        count = code_cell_count(project, path)
        assert section.count('<p class="label">Code cell ') == count, key
        stops = section.count("It stops with this message")
        assert stops <= 1, key
        not_run = section.count("Not run: a cell above stopped")
        shown = len(re.findall(r'<p class="label">Code cell \d+</p><pre>.*?</pre>\n'
                               r'(?!<p class="muted">Not run)', section, re.DOTALL))
        assert shown + not_run == count, key


def test_each_table_notebook_runs_to_its_end() -> None:
    """A Table notebook reads what the Example database holds and prints each write's Hive,
    so none stops."""
    for key, section in file_sections().items():
        if "/tables/" in f"/{key}" and key.endswith(".ipynb"):
            assert "It stops with this message" not in section, key


def test_each_lineage_link_lands_on_a_lineage_page_main_ships() -> None:
    shipped = set(toolbox_registry.lineage_pages(ROOT))
    links = re.findall(r'href="(example_projects/[^"]+)"', page())
    assert links
    assert {html.unescape(link) for link in links} == shipped


def test_no_folder_of_the_copy_and_no_example_database_import_is_shown() -> None:
    text = page()
    assert "example_database" not in text
    # An Example project's note about running its folder, which the download doesn't hold.
    assert "Running it" not in text
    assert "AppData" not in text and "/tmp/" not in text and "\\Temp\\" not in text


def test_the_page_comes_from_the_page_module_and_keeps_the_html_standard() -> None:
    html_page = toolbox_module("html_page")
    text = page()
    assert text.startswith(html_page.page("x", "", [], []).split("<title>", 1)[0])
    assert external_references(text) == []
    assert not STYLE_ATTRIBUTE.search(text)
    outside_tokens = TOKEN_BLOCK.sub("", text)
    assert HEX.findall(outside_tokens) == [] and not COLOUR_FUNCTION.search(outside_tokens)
    assert set(TOKEN_USE.findall(text)) <= set(html_page.COLOURS)


def test_every_tag_on_the_page_is_closed() -> None:
    parser = TagCounter()
    parser.feed(page())
    assert parser.problems == [] and parser.open == []


def test_the_readme_links_the_page() -> None:
    readme = (ROOT / "docs" / "clean-branch-readme.md").read_text(encoding="utf-8")
    section = readme.split("\n## Example projects\n", 1)[1].split("\n## ", 1)[0]
    assert f"](../{toolbox_registry.DOCS}/example_projects.html)" in section


def test_a_cells_dev_connection_is_shown_as_yours() -> None:
    cell = "x = 1\nimport example_database\nconnect(example_database)\n"
    assert example_projects_page.shown_as_yours(cell) == (
        f"x = 1\n{example_projects_page.SHOWN_CONNECTION}\n")
