"""Write an Edition's golden corpus, `tests/hive_corpus/<its folder>.txt`: what it shows today.

Run it on `dev` only when a change is meant to alter what the Toolbox writes, then review the diff:

    python tools/hive_corpus.py
    python tools/hive_corpus.py --edition spark

`tests/sqlglot_edition/test_sqlglot_hive_corpus.py` fails while the committed file differs from
what this writes. Both work only at the sqlglot pin in requirements-dev.txt, since another sqlglot
writes some Hive differently. The file pins, for each case under a stable id, what the Toolbox shows through its
public names:

- each Statement's Hive, from `to_hive(...)`, or the refusal it stops with;
- the repr of each output and condition, of the Statement and of each Derived table it reads;
- the commands `write_table_reference`, `check_table_reference` and `check_key` send;
- `export_lineage`'s Markdown report of the case's Statements, without its dated last line.

The cases are every docstring example that hands a Statement to `to_hive`, `run` or
`export_lineage`; every Statement function of the Worked examples; the edge cases and the
generated Statements in `tests/hive_corpus_cases.py`; and the Table references of both.
"""

from __future__ import annotations

import contextlib
import datetime
import doctest
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "tools"), str(ROOT / "tests")]

import editions  # noqa: E402

if __name__ == "__main__":
    # Before any Toolbox import: `import sql_composer` then gives the Edition asked for.
    editions.use(editions.chosen(sys.argv))

import pandas as pd  # noqa: E402

import example_gallery as gallery  # noqa: E402
import hive_corpus_cases  # noqa: E402
import sql_composer  # noqa: E402
from sql_composer import example_database  # noqa: E402
from sql_composer.clauses import derived_tables  # noqa: E402

EDITION = editions.EDITIONS[sql_composer.__name__]
GOLDEN = ROOT / "tests" / "hive_corpus" / f"{EDITION.folder}.txt"

PIN = re.search(r"^sqlglot==(\S+)$",
                (ROOT / "requirements-dev.txt").read_text(encoding="utf-8"), re.MULTILINE)[1]
# The exception types a Toolbox refusal comes as; is_refusal tells a refusal from a bug.
REFUSAL_TYPES = (sql_composer.GuardRefused, sql_composer.LoadRefused, TypeError, ValueError)
# The warehouse's newest day, as the recording send lists it.
NEWEST_DAY = datetime.date(2026, 9, 24)
# The lines that start a case and a part of a case in the file.
CASE_MARK = "== "
PART_MARK = "-- "


# --- The cases -------------------------------------------------------------------------------


def docstring_cases() -> list[tuple[str, object]]:
    """Each docstring example that hands a Statement on, as a function that replays it."""
    found = []
    for names, doc in gallery.docstrings():
        parts = [part for part in doctest.DocTestParser().parse(doc) if not isinstance(part, str)]
        if any(name + "(" in part.source for part in parts for name in gallery.HANDED_TO):
            found.append((f"doc:{names[0]}", _replaying(parts)))
    return found


def _replaying(parts: list):
    def build() -> list:
        handed = []
        scope = gallery.example_scope(handed)
        for part in parts:
            gallery.run_step(part.source, scope)
        return _unique([s for _, s in handed])
    return build


def worked_example_cases() -> list[tuple[str, object]]:
    """Each Statement function of each Worked example script, careless() with its opt-out too."""
    found = []
    for module in gallery.statement_scripts():
        script = module.__name__.split(".")[-1]
        functions = gallery.other_statements(module)
        if gallery.is_demonstration(module):
            functions = [("careless", module.careless), ("fixed", module.fixed)] + functions
            opt_out = gallery.opt_out_of(module.careless)
            if opt_out is not None:
                functions.append((f"careless_{opt_out}", _opted_out(module.careless, opt_out)))
        found += [(f"worked:{script}:{name}", _listed(function)) for name, function in functions]
    return found


def _opted_out(function, keyword: str):
    """`function` called with its Guard's opt-out keyword set."""
    return lambda: function(**{keyword: True})


def _listed(function):
    """`function`'s Statements as a list: it returns one, or a list of them as by_day does."""
    def build() -> list:
        built = function()
        return list(built) if isinstance(built, list) else [built]
    return build


def cases() -> list[tuple[str, object]]:
    """Every case, in a fixed order: docstrings, Worked examples, edge cases, generated ones."""
    found = (docstring_cases() + worked_example_cases() + hive_corpus_cases.edge_cases()
             + hive_corpus_cases.generated_cases())
    ids = [case_id for case_id, _ in found]
    repeated = sorted({case_id for case_id in ids if ids.count(case_id) > 1})
    if repeated:
        raise ValueError(f"Two cases share an id: {', '.join(repeated)}")
    return found


def _unique(statements: list) -> list:
    found = []
    for s in statements:
        if not any(s is seen for seen in found):
            found.append(s)
    return found


# --- What a case shows -----------------------------------------------------------------------


def is_refusal(error: Exception) -> bool:
    """Whether the Toolbox stopped on purpose, with one of its four-part messages."""
    return isinstance(error, REFUSAL_TYPES) and "What happened:" in str(error)


def refused_text(error: Exception) -> str:
    """A Toolbox refusal in full; any other error by its type alone, marked as not a refusal.

    Another library's message can carry terminal colours or change between its versions, and
    what matters here is that the Toolbox let it through.
    """
    if is_refusal(error):
        return f"{type(error).__name__}:{error}"
    return f"{type(error).__module__}.{type(error).__name__}, not a Toolbox refusal"


def refusal_or_raise(error: Exception) -> str:
    """A refusal met while building a case, as text; any other error is a bug, so it stops."""
    if not is_refusal(error):
        raise error
    return refused_text(error)


def case_text(case_id: str, build) -> str:
    """One case: each of its Statements, then the lineage report of all of them."""
    lines = [CASE_MARK + case_id]
    with gallery.example_setting():
        try:
            statements = build()
        except REFUSAL_TYPES as error:
            return "\n".join(lines + [PART_MARK + "refused", refusal_or_raise(error), ""])
        for number, s in enumerate(statements, 1):
            lines += statement_lines(number, s)
        lines += lineage_lines([s for s in statements if s._ddl is None])
    return "\n".join(lines + [""])


def statement_lines(number: int, s) -> list[str]:
    """A Statement's Hive, then the repr of its outputs and conditions, and each Derived table's."""
    lines = [PART_MARK + f"Statement {number}: to_hive"]
    try:
        lines.append(sql_composer.to_hive(s))
    except Exception as error:  # noqa: BLE001 - what to_hive stops with is part of the output
        lines.append(refused_text(error))
    for step, name in [(s, "the Statement")] + [
            (table._statement, f"Derived table {table._name}") for table in derived_tables(s)]:
        shown = parts_shown(step)
        if shown:
            lines += [PART_MARK + f"Statement {number}: {name}", *shown]
    return lines


def parts_shown(step) -> list[str]:
    """The repr of each output and condition of one step, as a notebook shows it."""
    shown = [f"output {name}: {column!r}" for column, name in step._outputs]
    shown += [f"read {number} ON: {read.on!r}"
              for number, read in enumerate(step._reads, 1) if read.on is not None]
    shown += [f"WHERE: {condition!r}" for condition in step._where]
    shown += [f"HAVING: {condition!r}" for condition in step._having]
    return shown


def lineage_lines(statements: list) -> list[str]:
    """export_lineage's Markdown report of the Statements, without its dated last line."""
    if not statements:
        return []
    with tempfile.TemporaryDirectory() as folder:
        try:
            _, markdown = sql_composer.export_lineage(*statements, to=Path(folder) / "case.html")
        except Exception as error:  # noqa: BLE001 - as for to_hive
            return [PART_MARK + "export_lineage", refused_text(error)]
        text = markdown.read_text(encoding="utf-8")
    kept = [line for line in text.splitlines() if not line.startswith("Made by export_lineage on")]
    return [PART_MARK + "export_lineage", *kept]


# --- The commands sent to the warehouse ------------------------------------------------------


class Recording:
    """A send that notes each command and answers like the warehouse, without running a query.

    DESCRIBE and SHOW PARTITIONS are answered from the Table reference itself, as Hive lists
    them, with NEWEST_DAY written in the table's date_format; any other command gets an empty
    frame, so check_key finds no repeats.
    """

    def __init__(self, t):
        self.table = t
        self.sent = []

    def __call__(self, text: str) -> pd.DataFrame:
        self.sent.append(text)
        if text.startswith("DESCRIBE"):
            return describe_frame(self.table)
        if text.startswith("SHOW PARTITIONS"):
            day = NEWEST_DAY.strftime(self.table._date_format)
            return pd.DataFrame({"partition": [f"{self.table._date_partition}={day}"]})
        return pd.DataFrame()


def describe_frame(t) -> pd.DataFrame:
    """What Hive's DESCRIBE lists for a Table reference: its columns, then its partition."""
    rows = [(name, kind, "") for name, kind in t._columns.items()]
    if t._date_partition is not None:
        rows += [("", None, None), ("# Partition Information", None, None),
                 ("# col_name", "data_type", "comment"),
                 (t._date_partition, t._columns[t._date_partition], "")]
    return pd.DataFrame(rows, columns=["col_name", "data_type", "comment"])


def warehouse_text(t) -> str:
    """The commands write_table_reference, check_table_reference and check_key send for `t`."""
    lines = [CASE_MARK + f"warehouse:{t._name}"]
    helpers = [("write_table_reference", _write_table_reference),
               ("check_table_reference", sql_composer.check_table_reference),
               ("check_key", sql_composer.check_key)]
    with gallery.example_setting():
        for name, helper in helpers:
            send = Recording(t)
            try:
                helper(t, send)
            except REFUSAL_TYPES as error:
                send.sent.append(refusal_or_raise(error))
            lines += [PART_MARK + name, *send.sent]
    return "\n".join(lines + [""])


def _write_table_reference(t, send) -> None:
    """write_table_reference, in a folder of its own, so its file never meets another."""
    with tempfile.TemporaryDirectory() as folder, contextlib.chdir(folder):
        sql_composer.write_table_reference(t._name, send=send)


def tables() -> list:
    """The Example database's Table references, then the edge cases' own."""
    return [example_database.jobs, example_database.job_runs, example_database.run_alerts,
            *hive_corpus_cases.edge_tables()]


# --- The file --------------------------------------------------------------------------------


def corpus_text() -> str:
    """The whole golden corpus, as one string."""
    header = (f"# What {EDITION.product} shows today, written by tools/hive_corpus.py. Don't "
              "edit it by hand.\n")
    blocks = [case_text(case_id, build) for case_id, build in cases()]
    blocks += [warehouse_text(t) for t in tables()]
    return header + "\n".join(blocks)


def main() -> int:
    if EDITION is editions.SQL_COMPOSER:
        import sqlglot

        if sqlglot.__version__ != PIN:
            print(f"The golden is written at the sqlglot pin, {PIN}, and this is "
                  f"{sqlglot.__version__}: another sqlglot writes some Hive differently.")
            return 1
    text = corpus_text()
    GOLDEN.parent.mkdir(parents=True, exist_ok=True)
    with open(GOLDEN, "w", encoding="utf-8", newline="\n") as file:
        file.write(text)
    print(f"Wrote {GOLDEN.relative_to(ROOT)}: {text.count(chr(10) + CASE_MARK)} cases.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
