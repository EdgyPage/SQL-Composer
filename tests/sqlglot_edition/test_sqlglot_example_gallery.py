"""SQL Composer's Example gallery gives pandas results where its Example database can't run.
"""

from __future__ import annotations

import html
import re

import pytest

from conftest import toolbox_folder

GALLERY = toolbox_folder() / "examples.html"


def page_text(html_text: str) -> str:
    """What a reader sees: the tags taken out, entities read, and runs of spaces made one."""
    text = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html_text, flags=re.DOTALL)
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", text)).split())


def entries() -> dict[str, tuple[str, str]]:
    """Each entry on the page, by its id: its title and all its text, as a reader sees them."""
    found = re.findall(r'<section class="entry" id="([^"]+)">(.*?)</section>',
                       GALLERY.read_text(encoding="utf-8"), re.DOTALL)
    return {
        entry_id: (page_text(re.search(r"<h3>(.*?)</h3>", body, re.DOTALL).group(1)),
                   page_text(body))
        for entry_id, body in found
    }


@pytest.mark.parametrize(
    "entry_id", ["row_number", "week_start", "latest_and_top_n", "regrouping"])
def test_results_the_example_database_cannot_run_come_from_pandas_labelled(
    entry_id: str,
) -> None:
    assert "computed in pandas, not by running this Hive" in entries()[entry_id][1]
