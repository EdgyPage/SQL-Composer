"""Hive that stays small (Toolbox 8.9, ticket 17): every SQL block the repo ships, and the Hive
the Excel conversion writes, read with sqlglot for four shapes that cost Hive work its rows
don't need.

- **A CTE read more than once in one query.** Hive works a CTE out again at each read: its
  `hive.optimize.cte.materialize.threshold` is -1, off, in 2.x, 3.1 and 4.0, and 3 from 4.1,
  for a CTE with totals alone.
- **`SELECT *` in a CTE**, which carries every column of what it reads, read after or not.
- **A CTE column nothing after it reads**, by its name; a CTE whose columns decide its rows, a
  DISTINCT or a UNION, is left alone.
- **An ORDER BY with no LIMIT in a CTE or a subquery**: Hive sorts every row through one
  reducer for it, and from 3.0 drops it (`hive.remove.orderby.in.subquery`).

What is read: each `hive` and `output` block of the pages in `docs/main/` (the how-tos, the
Example gallery, the Example projects page and the Workflows overview), which show the Hive each
Worked example and how-to writes; each ```sql block of `docs/` and `copilot/`; each `.hql` file
of the Example projects; and each final the code writes for the Excel evaluation's tasks
(`tools/excel_eval_tasks.py`, through `workbook_hive`) and for the workbook fixtures. The
evaluation's own reference Hive is not read yet: ticket 10 is making it lean.

A break that stays is in `KEPT`, by where it is and what it is, with the reason it stays.
"""

from __future__ import annotations

import functools
import html
import re
from collections.abc import Iterator
from pathlib import Path

import sqlglot
from sqlglot import exp

import formula_workbook
from excel_eval_tasks import TASKS
from sqlglot_composer.workbook_hive import workbook_hive
from sqlglot_composer.workbook_reader import LoopError, read_workbook

ROOT = Path(__file__).resolve().parents[2]
FIXTURES = ROOT / "tests" / "fixtures" / "workbook_text"
PAGE_BLOCK = re.compile(r'<pre(?: class="(?:hive|output)")?>(.*?)</pre>', re.DOTALL)
SQL_FENCE = re.compile(r"^```sql\n(.*?)^```", re.DOTALL | re.MULTILINE)
# A statement's first word, after its comments and SET lines, that makes it a query to read.
QUERY_START = re.compile(r"(?:EXPLAIN\s+)?(WITH|SELECT|INSERT|FROM)\s", re.IGNORECASE)
HIVE_VARIABLE = re.compile(r"\$\{[^}]*\}")
PLACEHOLDER = re.compile(r"<(\w+)>")

# Each break that stays: where it is, a file or an Excel final, and what it is, as `breaks`
# says it, with the reason.
KEPT = {
    ("docs/main/how_to.html", "CTE runs_per_job carries dt, runs, minutes, which nothing "
                              "after it reads"):
        "Share Building blocks' step 7: the Building block runs_per_job serves several "
        "Statements, each reading its own columns of it, one row for each job and day, as "
        "step 6's check of one day reads it. Hive's column pruner, always on since 0.13 "
        "(HIVE-4113), drops runs and minutes from the CTE it works out in place; dt, which the "
        "block groups by, gives the team Statement a row a day to add up, the same totals",
    ("workbook fixture 06_pivot_query_sheet, final job_hours", "CTE ok_runs is read 2 times"):
        "rule PF5 (ticket 06): a Top or Bottom value filter keeps its items with an IN "
        "over a RANK of the step's rows, read again, since a total of the kept items, an "
        "Average or a Distinct Count, needs the kept rows before they are grouped",
}


# --- The four shapes --------------------------------------------------------------------------


def breaks(query: exp.Expression) -> list[str]:
    """Each of the four shapes in one query, said as KEPT says it."""
    found = []
    for held in query.find_all(exp.With):
        for cte in held.expressions:
            found += cte_breaks(cte, held)
    found += unlimited_orders(query)
    return found


def cte_breaks(cte: exp.CTE, held: exp.With) -> list[str]:
    """A CTE read more than once by the query its WITH starts, a `SELECT *` in it, and its
    columns nothing after it reads."""
    found = []
    reads = [table for table in held.parent.find_all(exp.Table)
             if table.name == cte.alias and not table.db]
    if len(reads) > 1:
        found.append(f"CTE {cte.alias} is read {len(reads)} times")
    if has_star(cte.this):
        found.append(f"CTE {cte.alias} has SELECT *")
        return found
    body = cte.this
    if not isinstance(body, exp.Select) or body.args.get("distinct"):
        return found
    read, star = names_read_after(cte, held)
    unread = [name for name in body.named_selects if name and name not in read]
    if unread and not star:
        found.append(f"CTE {cte.alias} carries {', '.join(unread)}, which nothing after it "
                     "reads")
    return found


def has_star(query: exp.Expression) -> bool:
    """Whether any SELECT in `query` selects `*` or `t.*`; a `COUNT(*)` is no star."""
    return any(isinstance(column, exp.Star) or (
        isinstance(column, exp.Column) and isinstance(column.this, exp.Star))
        for select in query.find_all(exp.Select) for column in select.expressions)


def names_read_after(cte: exp.CTE, held: exp.With) -> tuple[set[str], bool]:
    """Every column's name read after `cte`, in the CTEs after it and the query its WITH
    starts, and whether any of them selects `*`, which reads every column."""
    after = held.expressions[held.expressions.index(cte) + 1:]
    query = held.parent.copy()
    query.set("with_", None)
    parts = [each.this for each in after] + [query]
    read = {column.name for part in parts for column in part.find_all(exp.Column)}
    return read, any(has_star(part) for part in parts)


def unlimited_orders(query: exp.Expression) -> list[str]:
    """Each ORDER BY with no LIMIT in a CTE or a subquery: any but the outermost query's."""
    outermost = query.expression if isinstance(query, exp.Insert) else query
    found = []
    for select in query.find_all(exp.Select, exp.Union):
        if select is outermost or not select.args.get("order") or select.args.get("limit"):
            continue
        cte = select.find_ancestor(exp.CTE)
        inside = f"CTE {cte.alias}" if cte else "a subquery"
        found.append(f"ORDER BY with no LIMIT in {inside}")
    return found


# --- Where the SQL is -------------------------------------------------------------------------


def queries_of(text: str) -> Iterator[exp.Expression]:
    """Each query of a block of Hive, its comments and SET lines left out, a Hive variable and
    a `<placeholder>` made plain names; a statement that is no query, such as CREATE TABLE, is
    passed over, and so is a line of one, as a page shows a query's first line alone."""
    for statement in re.split(r";[ \t]*(?:\n|$)", text):
        lines = [line for line in statement.splitlines()
                 if not line.lstrip().startswith(("--", "SET ", "execute: SET"))]
        plain = "\n".join(lines).strip().removeprefix("execute: ")
        start = QUERY_START.match(plain)
        if start is None:
            continue
        plain = PLACEHOLDER.sub(r"\1", HIVE_VARIABLE.sub("hivevar", plain[start.start(1):]))
        try:
            yield from (each for each in sqlglot.parse(plain, read="hive") if each)
        except sqlglot.errors.SqlglotError:
            continue


def sql_blocks() -> Iterator[tuple[str, int, str]]:
    """Each block of SQL the repo ships: its file, its number in the file, and its text."""
    for page in sorted((ROOT / "docs" / "main").glob("*.html")):
        text = page.read_text(encoding="utf-8")
        for number, block in enumerate(PAGE_BLOCK.findall(text), 1):
            yield _relative(page), number, html.unescape(re.sub(r"<[^>]+>", "", block))
    written = sorted((ROOT / "docs").rglob("*.md")) + sorted((ROOT / "copilot").glob("*.txt"))
    for path in written:
        for number, block in enumerate(SQL_FENCE.findall(path.read_text(encoding="utf-8")), 1):
            yield _relative(path), number, block
    for path in sorted((ROOT / "example_projects").rglob("*.hql")):
        yield _relative(path), 1, path.read_text(encoding="utf-8")


def _relative(path: Path) -> str:
    """A file's path from the repo's top, with forward slashes."""
    return path.relative_to(ROOT).as_posix()


def excel_finals() -> Iterator[tuple[str, exp.Query]]:
    """Each final the code writes for each Excel evaluation task and each workbook fixture,
    named by its task or fixture and its final."""
    for task in TASKS:
        book = read_workbook(formula_workbook.saved(task.workbook))
        for name, query in workbook_hive(book).finals.items():
            yield f"Excel task {task.id}, final {name}", query
    for path in sorted(FIXTURES.glob("*.xlsx")):
        try:
            book = read_workbook(path)
        except LoopError:
            continue
        for name, query in workbook_hive(book).finals.items():
            yield f"workbook fixture {path.stem}, final {name}", query


@functools.cache
def found_in_excel_finals() -> set[tuple[str, str]]:
    """Each break of the Excel conversion's finals, by its final and what it is."""
    return {(where, each) for where, query in excel_finals() for each in breaks(query)}


def found_in_blocks() -> dict[tuple[str, str], list[str]]:
    """Each break of the blocks, by its file and what it is, and each block it is in."""
    found: dict[tuple[str, str], list[str]] = {}
    for where, number, text in sql_blocks():
        for query in queries_of(text):
            first = query.sql(dialect="hive")[:60]
            for each in breaks(query):
                found.setdefault((where, each), []).append(f"block {number}: {first}")
    return found


# --- The tests --------------------------------------------------------------------------------


def test_each_shape_is_found_and_lean_hive_passes() -> None:
    lean = ("WITH per_job AS (SELECT job_id, COUNT(*) AS runs FROM ops.job_runs "
            "WHERE dt = '2026-09-24' GROUP BY job_id) "
            "SELECT j.team, SUM(p.runs) AS runs FROM per_job p JOIN ops.jobs j "
            "ON j.job_id = p.job_id GROUP BY j.team ORDER BY runs DESC")
    assert [breaks(query) for query in queries_of(lean)] == [[]]
    twice = ("WITH r AS (SELECT job_id FROM ops.job_runs) "
             "SELECT a.job_id FROM r a JOIN r b ON a.job_id = b.job_id")
    assert breaks(sqlglot.parse_one(twice, read="hive")) == ["CTE r is read 2 times"]
    star = "WITH r AS (SELECT * FROM ops.job_runs) SELECT job_id FROM r"
    assert breaks(sqlglot.parse_one(star, read="hive")) == ["CTE r has SELECT *"]
    unread = ("INSERT OVERWRITE TABLE mart.t SELECT job_id FROM "
              "(WITH r AS (SELECT job_id, dt, run_id FROM ops.job_runs) SELECT job_id, dt "
              "FROM r) x")
    assert breaks(sqlglot.parse_one(unread, read="hive")) == [
        "CTE r carries run_id, which nothing after it reads"]
    ordered = ("WITH r AS (SELECT job_id FROM ops.job_runs ORDER BY job_id) "
               "SELECT job_id FROM (SELECT job_id FROM r ORDER BY job_id) x")
    assert sorted(breaks(sqlglot.parse_one(ordered, read="hive"))) == [
        "ORDER BY with no LIMIT in CTE r", "ORDER BY with no LIMIT in a subquery"]


def test_what_decides_a_cte_s_rows_is_left_whole() -> None:
    distinct = ("WITH r AS (SELECT DISTINCT job_id, dt FROM ops.job_runs) "
                "SELECT job_id, COUNT(*) AS days FROM r GROUP BY job_id")
    stacked = ("WITH r AS (SELECT job_id, dt FROM a UNION ALL SELECT job_id, dt FROM b) "
               "SELECT job_id FROM r")
    starred = "WITH r AS (SELECT job_id, dt FROM ops.job_runs) SELECT * FROM r"
    limited = ("WITH r AS (SELECT job_id FROM ops.job_runs ORDER BY job_id LIMIT 5) "
               "SELECT job_id FROM r")
    for text in (distinct, stacked, starred, limited):
        assert breaks(sqlglot.parse_one(text, read="hive")) == [], text


def test_a_page_shows_a_query_s_first_line_alone_and_it_is_passed_over() -> None:
    page = ("execute: SET hive.exec.dynamic.partition=true\n"
            "execute: INSERT OVERWRITE TABLE mart.t PARTITION(dt)\n1 of 2: mart.t  worked")
    assert list(queries_of(page)) == []
    shown = "-- 1 of 2: write()\nSET a=b;\nSELECT job_id FROM <database>.job_runs;\n"
    assert [query.sql() for query in queries_of(shown)] == [
        "SELECT job_id FROM database.job_runs"]


def test_the_blocks_read_hold_the_hive_of_each_kind_of_doc() -> None:
    files = {where for where, _, text in sql_blocks() if list(queries_of(text))}
    assert {"docs/main/how_to.html", "docs/main/examples.html",
            "docs/main/example_projects.html", "copilot/15_excel_workbook_steps.txt",
            "copilot/12_excel_power_query.txt"} <= files
    assert any(where.startswith("example_projects/") for where in files)


def test_no_sql_block_the_repo_ships_costs_hive_more_than_its_rows_need() -> None:
    found = found_in_blocks()
    new = {key: blocks for key, blocks in found.items() if key not in KEPT}
    assert not new, "\n".join(f"{where}, {', '.join(blocks)}: {each}"
                              for (where, each), blocks in sorted(new.items()))


def test_the_hive_the_excel_conversion_writes_costs_hive_no_more_than_its_rows_need() -> None:
    new = [f"{where}: {each}" for where, each in found_in_excel_finals() if (where, each)
           not in KEPT]
    assert not new, "\n".join(new)


def test_each_break_kept_is_still_there() -> None:
    found = set(found_in_blocks()) | found_in_excel_finals()
    assert [key for key in KEPT if key not in found] == []
