"""The README is a tutorial, and the version history is in CHANGES.md.

`docs/clean-branch-readme.md`, which the export fills in as main's README, walks a new user
through numbered steps, from installing the Toolbox to a project of their own: step N is
Getting started how-to N, the same in title, order and number, and links it, so the how-to
walks through it in full. What changed in each version, and how to
update from it, lives in `CHANGES.md`, at the repo's top, so the README holds no section about
one version.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = (ROOT / "docs" / "clean-branch-readme.md").read_text(encoding="utf-8")
HOW_TOS = ROOT / "worked_examples" / "how_to"
# A link to a how-to on the how-to page, as [title](../sqlglot_composer/how_to.html#slug): the
# README is .github/README.md on main, so it goes up one folder.
HOW_TO_LINK = re.compile(r"\]\(\.\./sqlglot_composer/how_to\.html#(\w+)\)")


def headings() -> list[str]:
    return re.findall(r"^## (.+)$", TEMPLATE, re.MULTILINE)


def test_no_heading_is_about_one_version() -> None:
    about_a_version = [heading for heading in headings()
                       if re.search(r"\d+\.\d+|\d+\.x|Update from", heading)]
    assert about_a_version == [], "a version's notes belong in CHANGES.md"


def test_the_tutorial_steps_come_first_numbered_in_order() -> None:
    steps = [re.match(r"(\d+)\. ", heading) for heading in headings()]
    numbers = [int(step.group(1)) for step in steps if step]
    assert numbers == list(range(1, len(numbers) + 1)) and len(numbers) >= 5
    assert all(steps[: len(numbers)]), "the numbered steps come before every other section"


def getting_started() -> list[tuple[str, str]]:
    """The Getting started how-tos, in number order, as (title, slug), read from each how-to's
    title on line 1 and its `For:` line."""
    found = []
    for path in sorted(HOW_TOS.glob("[0-9][0-9]_*.py")):
        doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) or ""
        title, _, group = doc.splitlines()[:3]
        if group == "For: Getting started":
            found.append((title, path.stem[3:]))
    return found


def test_readme_step_n_is_getting_started_how_to_n() -> None:
    """The same in title, order and number, and each step links its how-to."""
    steps = {int(number): (title, body) for number, title, body in re.findall(
        r"^## (\d+)\. ([^\n]+)\n(.*?)(?=^## |\Z)", TEMPLATE, re.MULTILINE | re.DOTALL)}
    how_tos = getting_started()
    assert [title for _, (title, _) in sorted(steps.items())] == [
        title for title, _ in how_tos]
    for number, (title, slug) in enumerate(how_tos, start=1):
        assert slug in HOW_TO_LINK.findall(steps[number][1]), (
            f"README step {number}, {title}, links its how-to: (../sqlglot_composer/"
            f"how_to.html#{slug})")


def test_every_how_to_the_readme_links_exists() -> None:
    slugs = {path.stem[3:] for path in HOW_TOS.glob("[0-9][0-9]_*.py")}
    linked = HOW_TO_LINK.findall(TEMPLATE)
    assert linked
    assert [slug for slug in linked if slug not in slugs] == []


def test_the_readme_points_to_the_change_notes() -> None:
    assert "`CHANGES.md`" in TEMPLATE
    assert (ROOT / "CHANGES.md").is_file()
