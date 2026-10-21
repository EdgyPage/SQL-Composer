"""The README is a tutorial, and the version history is in CHANGES.md.

`docs/clean-branch-readme.md`, which the export fills in as main's README, walks a new user
through numbered steps, from installing the Toolbox to the Lineage of a Saved table, each
pointing to the how-to that walks through it in full. What changed in each version, and how to
update from it, lives in `CHANGES.md`, at the repo's top, so the README holds no section about
one version.
"""

from __future__ import annotations

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


def test_each_step_after_install_points_to_a_how_to_or_a_section() -> None:
    sections = re.split(r"^## ", TEMPLATE, flags=re.MULTILINE)[1:]
    for section in sections:
        title = section.splitlines()[0]
        if re.match(r"\d+\. ", title) and not title.startswith("1. "):
            assert HOW_TO_LINK.search(section) or "](#" in section, title


def test_every_how_to_the_readme_links_exists() -> None:
    slugs = {path.stem[3:] for path in HOW_TOS.glob("[0-9][0-9]_*.py")}
    linked = HOW_TO_LINK.findall(TEMPLATE)
    assert linked
    assert [slug for slug in linked if slug not in slugs] == []


def test_the_readme_points_to_the_change_notes() -> None:
    assert "`CHANGES.md`" in TEMPLATE
    assert (ROOT / "CHANGES.md").is_file()
