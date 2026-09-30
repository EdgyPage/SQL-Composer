"""The Example gallery, `sql_composer/examples.html`: every Worked example on one page.

`tools/example_gallery.py` writes it from the docstrings' examples and the Statement scripts in
`worked_examples/statements/`, running each Statement on the Example database. The page is
committed and ships with the Toolbox, so these tests read the committed copy, and one test
fails if writing it again would change it.
"""

from __future__ import annotations

import ast
import doctest
import html
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

import pytest

import sql_composer
from conftest import gallery_entries, page_text, toolbox_folder, toolbox_module

ROOT = Path(__file__).resolve().parent.parent
GALLERY = toolbox_folder() / "examples.html"
sys.path.insert(0, str(ROOT / "tools"))

import example_gallery  # noqa: E402


@pytest.mark.needs_example_database
def test_the_committed_gallery_is_what_the_generator_writes() -> None:
    committed = GALLERY.read_text(encoding="utf-8") if GALLERY.exists() else ""
    assert example_gallery.gallery_page() == committed, (
        f"{GALLERY.relative_to(ROOT).as_posix()} is out of date: run python "
        "tools/example_gallery.py"
    )


def toolbox_docstrings() -> list[doctest.DocTest]:
    """Every docstring in the Toolbox that holds a >>> example."""
    finder = doctest.DocTestFinder()
    modules = [toolbox_module()] + [
        toolbox_module(path.stem)
        for path in sorted(toolbox_folder().glob("*.py")) if path.stem != "__init__"
    ]
    return [test for module in modules for test in finder.find(module) if test.examples]


@pytest.mark.parametrize("name", sql_composer.__all__)
def test_every_public_name_has_an_entry_named_after_it(name: str) -> None:
    titled = [title for title, _ in gallery_entries().values()
              if re.search(rf"(?<![\w.]){name}(?![\w.])", title)]
    assert titled, f"no entry is titled {name}"


@pytest.mark.parametrize("docstring", toolbox_docstrings(), ids=lambda test: test.name)
def test_every_docstring_example_is_on_the_page(docstring: doctest.DocTest) -> None:
    shown = page_text(GALLERY.read_text(encoding="utf-8"))
    for example in docstring.examples:
        assert " ".join(example.source.split()) in shown, example.source
        # <BLANKLINE> is how a doctest writes an empty line; the page shows the empty line.
        want = example.want.replace("<BLANKLINE>", "")
        assert " ".join(want.split()) in shown, example.want


def entry_section(entry_id: str) -> str:
    found = re.search(rf'<section class="entry" id="{re.escape(entry_id)}">(.*?)</section>',
                      GALLERY.read_text(encoding="utf-8"), re.DOTALL)
    assert found, f"no entry {entry_id}"
    return found.group(1)


def sides(entry_id: str) -> tuple[str, str]:
    """A Worked example's careless side and its fixed side, as HTML."""
    pair = entry_section(entry_id).split('<div class="pair">', 1)[1]
    careless, fixed = pair.split("<h4>Fixed</h4>", 1)
    assert "<h4>Careless" in careless
    return careless, fixed


def cells(html_text: str) -> list[str]:
    return [page_text(cell) for cell in re.findall(r"<td>(.*?)</td>", html_text, re.DOTALL)]


STATEMENT_SCRIPTS = sorted((ROOT / "worked_examples" / "statements").glob("*.py"))


@pytest.mark.parametrize("path", STATEMENT_SCRIPTS, ids=lambda path: path.stem)
def test_every_statement_script_has_an_entry_with_its_title_and_why(path: Path) -> None:
    doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8")))
    title, text = gallery_entries()[path.stem]
    assert title == page_text(html.escape(doc.splitlines()[0]))
    why = next(paragraph for paragraph in doc.split("\n\n") if paragraph.startswith("Why: "))
    assert " ".join(why.replace("`", "").split()) in text


@pytest.mark.parametrize(
    ("entry_id", "careless", "fixed"),
    [
        # The numbers "Build the Example database's demonstrations" checked against pandas.
        ("repeated_rows", ["150", "7"], ["100", "7"]),
        ("regrouping", ["2026-09-21", "6"], ["2026-09-21", "3"]),
        ("left_join_then_where", ["invoice_sync", "3", "nightly_load", "4", "report_build", "2"],
         ["cache_warm", "0", "invoice_sync", "3", "nightly_load", "4", "report_build", "2"]),
        ("none_in_equals", [], ["1"]),
        ("nan_in_a_list", [], ["3"]),
        ("not_equals_drops_null", ["3"], ["4"]),
        ("latest_and_top_n", ["1", "104", "TEST", "2", "102", "SUCCESS", "3", "103", "SUCCESS"],
         ["1", "104", "SUCCESS", "2", "102", "FAILED", "3", "103", "SUCCESS"]),
    ],
)
def test_careless_and_fixed_sit_side_by_side_with_their_results(
    entry_id: str, careless: list[str], fixed: list[str]
) -> None:
    careless_side, fixed_side = sides(entry_id)
    assert cells(careless_side) == careless
    assert cells(fixed_side.split("<h4>Also in this script")[0]) == fixed
    for side in (careless_side, fixed_side):
        assert "def " in side and ">Hive<" in side or "no opt-out" in side


@pytest.mark.parametrize(
    ("entry_id", "message"),
    [
        ("repeated_rows", "RepeatedRowsWarning: What happened: JOIN(run_alerts) matches on run_id"),
        ("regrouping", "GuardRefused: What happened: sum_of(jobs_per_day.jobs_that_ran) adds up"),
        ("left_join_then_where", "GuardRefused: What happened: WHERE has job_runs.dt BETWEEN"),
        ("none_in_equals", "GuardRefused: What happened: equals(job_runs.status, None)"),
        ("nan_in_a_list", "GuardRefused: What happened: is_not_in(job_runs.job_id, ...)"),
    ],
)
def test_the_refusal_or_warning_shows_under_the_careless_statement(
    entry_id: str, message: str
) -> None:
    careless, fixed = sides(entry_id)
    assert message in page_text(careless)
    assert "What happened" not in page_text(fixed)


def test_a_common_job_shows_each_step_with_its_hive_and_no_careless_side() -> None:
    section = entry_section("saved_table")
    assert '<div class="pair">' not in section
    text = page_text(section)
    assert "The Table reference it imports, table_references/runs_to_review.py" in text
    steps = ["create()", "create_if_missing()", "failed_runs()", "alerted_runs()",
             "backfill()", "rebuild()"]
    assert [text.index(step) for step in steps] == sorted(text.index(step) for step in steps)
    assert "Hive of Statement 1 of 2 DROP TABLE IF EXISTS mart.runs_to_review" in text
    assert "INSERT INTO mart.runs_to_review PARTITION(dt = '2026-09-24')" in text


def test_common_jobs_come_before_the_wrong_numbers() -> None:
    page = GALLERY.read_text(encoding="utf-8")
    assert page.index('id="common-jobs"') < page.index('id="saved_table"') < page.index(
        'id="wrong-numbers"') < page.index('id="repeated_rows"')


def test_an_opt_out_shows_the_wrong_result_hive_would_give() -> None:
    careless, _ = sides("left_join_then_where")
    assert "careless(keeps_only_matches=True)" in page_text(careless)
    assert "cache_warm" not in cells(careless)


def test_row_number_shows_the_latest_run_of_each_job() -> None:
    assert cells(entry_section("row_number")) == ["1", "104", "SUCCESS", "2", "102", "FAILED",
                                               "3", "103", "SUCCESS"]


def test_a_docstring_statement_shows_its_result_on_the_example_database() -> None:
    # The two FAILED runs, as run's own docstring shows them.
    assert cells(entry_section("WHERE")) == ["97", "102"]


def test_a_statement_the_example_database_cannot_run_says_why() -> None:
    _, text = gallery_entries()["INSERT_OVERWRITE"]
    assert "No result here. The Example database only answers SELECT" in text


def test_a_statement_given_to_run_shows_its_hive() -> None:
    _, text = gallery_entries()["run"]
    assert "The Hive of the Statement given to run(...) SELECT job_runs.run_id," in text


@pytest.mark.parametrize(
    ("entry_id", "names"),
    [
        ("row_number", ["SELECT", "AS", "FROM", "WHERE", "statement", "derived", "equals",
                        "last_n_days", "row_number", "descending", "to_hive"]),
        ("repeated_rows", ["SELECT", "AS", "FROM", "JOIN", "LEFT_JOIN", "WHERE", "GROUP_BY",
                           "statement", "derived", "equals", "between", "count_rows",
                           "sum_of", "example_database"]),
    ],
)
def test_each_entry_lists_the_toolbox_names_its_python_uses(
    entry_id: str, names: list[str]
) -> None:
    listed = re.search(r'<p class="names">Toolbox names used: (.*?)</p>', entry_section(entry_id))
    assert sorted(re.findall(r"<code>(\w+)</code>", listed.group(1))) == sorted(names)


def test_the_page_needs_no_other_file() -> None:
    page = GALLERY.read_text(encoding="utf-8")
    for outside in ("src=", "<link", "@import", "url(", "http://", "https://"):
        assert outside not in page
    scripts = re.findall(r"<script>(.*?)</script>", page, re.DOTALL)
    assert len(scripts) == 1 and len(scripts[0].strip().splitlines()) <= 15


def test_without_scripts_every_entry_is_plain_html() -> None:
    page = GALLERY.read_text(encoding="utf-8")
    assert re.search(r'<p id="filter" hidden>', page)
    assert page.count(" hidden") == 1
    assert len(gallery_entries()) == len(STATEMENT_SCRIPTS) + len(toolbox_docstrings())


class TagCounter(HTMLParser):
    """Every tag opened is closed, in order; an empty element (<meta>, <input>) needs none."""

    EMPTY = {"meta", "input", "br", "hr", "img"}

    def __init__(self) -> None:
        super().__init__()
        self.open: list[str] = []
        self.problems: list[str] = []

    def handle_starttag(self, tag, attrs) -> None:
        if tag not in self.EMPTY:
            self.open.append(tag)

    def handle_endtag(self, tag) -> None:
        if not self.open or self.open.pop() != tag:
            self.problems.append(f"</{tag}> at line {self.getpos()[0]}")


def test_every_tag_on_the_page_is_closed() -> None:
    parser = TagCounter()
    parser.feed(GALLERY.read_text(encoding="utf-8"))
    assert parser.problems == [] and parser.open == []


def test_no_box_on_the_page_is_empty() -> None:
    assert not re.search(r"<pre[^>]*></pre>", GALLERY.read_text(encoding="utf-8"))


def test_a_pandas_result_does_not_claim_to_come_from_the_example_database() -> None:
    assert "on the Example database, computed in pandas" not in GALLERY.read_text(
        encoding="utf-8")


def test_a_statement_given_to_run_also_shows_its_result_as_a_table() -> None:
    # The two FAILED runs, as run's own docstring shows them, without pandas' index.
    assert cells(entry_section("run")) == ["97", "3", "2026-09-23", "102", "2", "2026-09-24"]


def test_the_page_says_what_to_paste_for_last_n_days_and_it_reads_the_same_days() -> None:
    from sql_composer import between, example_database, last_n_days

    shown = page_text(GALLERY.read_text(encoding="utf-8"))
    assert 'write between(job_runs.dt, "2026-09-23", "2026-09-24") in its place' in shown
    runs = example_database.job_runs
    assert repr(between(runs.dt, "2026-09-23", "2026-09-24")) == repr(last_n_days(runs.dt, 2))


def test_the_page_names_no_folder_a_toolbox_user_does_not_have() -> None:
    assert "worked_examples/" not in GALLERY.read_text(encoding="utf-8")
