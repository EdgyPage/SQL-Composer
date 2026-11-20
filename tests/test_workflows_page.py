"""The Workflows overview, `workflows.html`: one drawing of every Workflow and the Excel path,
an arrow for each hand-off, and, for each, its steps and its common tripping points (Toolbox
8.7, ticket 07).

`tools/workflows_page.py` writes the page, from `tools/workflow_graph.py`'s steps and its own
hand-written hand-offs and tripping points, built with the page module,
`sqlglot_composer/html_page.py`. The page is committed and ships beside the how-to page, so
these tests read the committed copy, and one fails if writing it again would change it.
"""

from __future__ import annotations

import html
import re
from pathlib import Path

import pytest
import toolbox_registry
import workflows_page
from conftest import docs_folder, toolbox_module
from offline_policy import external_references
from test_example_gallery import TagCounter
from test_html_page import COLOUR_FUNCTION, HEX, STYLE_ATTRIBUTE, TOKEN_BLOCK, TOKEN_USE

ROOT = Path(__file__).resolve().parent.parent
workflows = toolbox_module("workflows")
PAGE = docs_folder() / "workflows.html"
# Every Workflow the page draws, as the ticket names them, and the Excel path. The schedule
# Workflow is ticket 08's, built alongside this one.
EXPECTED = ("references", "new_table", "convert", "promote", "change_a_saved_table", "upgrade",
            "schedule", "excel")
# A box of the drawing: an SVG group of class "n", its id "box_" and the Workflow's name.
BOX = re.compile(r'<g class="n [^"]*" id="box_(\w+)"')
# An arrow of the drawing, by the boxes at its two ends.
ARROW = re.compile(r'<path class="e" data-a="box_(\w+)" data-b="box_(\w+)"')
# A Workflow's step heading in its notebook, such as "## 3. Create each table in dev".
STEP_HEADING = re.compile(r"^## \d+\. (.+)$")


def page() -> str:
    return PAGE.read_text(encoding="utf-8")


def part(name: str) -> str:
    """The part of the side panel about `name`: a Workflow, "excel" or "every"."""
    found = re.search(rf'<section id="{name}">(.*?)</section>', page(), re.DOTALL)
    assert found, f"the panel has no part for {name}"
    return found.group(1)


def steps_shown(name: str) -> list[str]:
    """The steps a part lists, in order, each its words without its tag."""
    found = re.search(r"<h3>Its steps</h3><ol[^>]*>(.*?)</ol>", part(name), re.DOTALL)
    assert found, f"{name}'s part lists no steps"
    items = re.findall(r"<li>(.*?)</li>", found.group(1), re.DOTALL)
    return [html.unescape(re.sub(r'<span class="tag[^"]*">.*?</span>|<[^>]+>', "", item))
            for item in items]


def test_the_committed_page_is_what_the_tool_writes() -> None:
    committed = page() if PAGE.exists() else ""
    assert workflows_page.page_text() == committed, (
        f"{PAGE.relative_to(ROOT).as_posix()} is out of date: run python "
        "tools/workflows_page.py")


def test_every_workflow_and_the_excel_path_is_a_box_of_the_drawing() -> None:
    assert sorted(BOX.findall(page())) == sorted(EXPECTED)


def test_every_workflow_workflows_py_holds_is_on_the_page() -> None:
    names = {workflow.name for workflow in workflows.WORKFLOWS}
    assert names <= set(BOX.findall(page()))


@pytest.mark.parametrize("notebook", sorted(
    (ROOT / "example_projects").glob("*/admin/workflows/*/*.ipynb")),
    ids=lambda path: path.relative_to(ROOT).as_posix())
def test_each_workflows_steps_are_its_notebooks_step_headings_in_order(notebook: Path) -> None:
    headings = []
    for kind, text in toolbox_module("notebooks").read_cells(notebook):
        found = STEP_HEADING.match(text.split("\n")[0]) if kind == "markdown" else None
        if found:
            headings.append(found.group(1))
    assert steps_shown(notebook.stem) == headings


def test_each_workflows_steps_are_its_steps_in_workflows_py() -> None:
    for workflow in workflows.WORKFLOWS:
        assert steps_shown(workflow.name) == [step.name for step in workflow.steps]


def test_the_excel_paths_steps_are_workflow_graphs() -> None:
    assert steps_shown("excel") == [
        "Fill in a Formula workbook, laid out as copilot/formula_workbook.xlsx is",
        "Save it in admin/workflows/convert/, beside the convert notebook, and give it to "
        "convert in FILES",
        "Or give Copilot files 15, 11, 12 and 20 with the workbook's text",
        "Read the Workbook check, in convert's report and the batch's batch.md",
        "Answer each table's Decisions, a PivotTable's name and each Pivot filter among them, "
        "then create, seed and write each in dev, as the Workflow's steps say",
        "Compare each with its query, the Hive it was converted from",
        "Promote them, and create and write each in prod, through the promote Workflow"]


def test_each_hand_off_is_an_arrow_between_two_boxes_and_said_on_both_parts() -> None:
    arrows = set(ARROW.findall(page()))
    assert len(workflows_page.HAND_OFFS) >= 6
    for hand_off in workflows_page.HAND_OFFS:
        assert (hand_off.source, hand_off.target) in arrows
        assert f'On to <a class="go" href="#{hand_off.target}">' in part(hand_off.source)
        assert f'From <a class="go" href="#{hand_off.source}">' in part(hand_off.target)
    assert ("convert", "promote") in arrows and ("excel", "convert") in arrows


@pytest.mark.parametrize("name", EXPECTED)
def test_each_box_has_its_tripping_points(name: str) -> None:
    found = re.search(r"<h3>Common tripping points</h3><ul>(.*?)</ul>", part(name), re.DOTALL)
    assert found and found.group(1).count("<li>") >= 2


def test_every_tripping_point_is_for_a_box_or_for_every_workflow() -> None:
    assert set(workflows_page.TRIPPING_POINTS) == {*EXPECTED, "every"}
    assert "Run All" in part("every")


def test_each_part_links_a_how_to_that_is_there() -> None:
    slugs = {path.stem[3:] for path in (ROOT / "worked_examples" / "how_to").glob("*.py")}
    linked = re.findall(r'href="how_to\.html#(\w+)"', page())
    assert len(linked) >= len(EXPECTED)
    assert [slug for slug in linked if slug not in slugs] == []


def test_each_link_inside_the_page_lands_on_a_part() -> None:
    for name in re.findall(r'href="#(\w+)"', page()):
        part(name)


def test_the_page_is_built_by_the_page_module_and_holds_to_the_html_standard() -> None:
    html_page = toolbox_module("html_page")
    text = page()
    assert text.startswith('<!doctype html>\n<html><head><meta charset="utf-8">')
    assert html_page.BASE_CSS in text and html_page.DRAWING_CSS in text
    assert html_page.DRAWING_SCRIPT in text
    assert external_references(text) == []
    assert not STYLE_ATTRIBUTE.search(text)
    outside_tokens = TOKEN_BLOCK.sub("", text)
    assert HEX.findall(outside_tokens) == [] and not COLOUR_FUNCTION.search(outside_tokens)
    assert set(TOKEN_USE.findall(text)) <= set(html_page.COLOURS)


def test_without_its_script_every_part_shows() -> None:
    """The script hides every part but the one shown; without it, each shows, in turn."""
    assert ".scripted .panel section:not(.shown){display:none}" in page()
    assert " hidden" not in page()


def test_every_tag_on_the_page_is_closed() -> None:
    parser = TagCounter()
    parser.feed(page())
    assert parser.problems == [] and parser.open == []


def test_the_readme_links_the_page_from_the_workflows() -> None:
    readme = (ROOT / "docs" / "clean-branch-readme.md").read_text(encoding="utf-8")
    workflows_section = readme.split("\n## The Workflows\n", 1)[1].split("\n## ", 1)[0]
    assert f"](../{toolbox_registry.DOCS}/workflows.html)" in workflows_section


def test_the_page_ships_in_mains_docs() -> None:
    assert "workflows.html" in toolbox_registry.PAGES
