"""Write the golden corpus, `tests/hive_corpus/sqlglot_composer.txt`: what the Toolbox shows today.

Run it on `dev` only when a change is meant to alter what the Toolbox writes, then review the diff:

    python tools/hive_corpus.py

`tests/test_hive_corpus.py` fails while the committed file differs from what this writes. It is
written only at the sqlglot pin in requirements-dev.txt, since another sqlglot writes some Hive
differently.

The file pins, for each case under a stable id, what the Toolbox shows through its public
names:

- each Statement's Hive, from `to_hive(...)`, or the refusal it stops with, and for Session
  settings, an Unchecked statement and an Admin statement, what `show_hive(...)` prints too;
- the repr of each output and condition, of the Statement and of each Derived table it reads;
- the commands `write_table_reference`, `check_table_reference` and `check_key` send;
- `export_lineage`'s Markdown report of the case's Statements, without its dated last line,
  but for the Session settings it names.

The cases are every docstring example that hands a Statement to `to_hive`, `run_query`,
`run_execute` or `export_lineage`; every Statement function of the Worked examples; the edge cases and the
generated Statements in `tests/hive_corpus_cases.py`; and the Table references of both.
"""

from __future__ import annotations

import contextlib
import doctest
import io
import re
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "tools"), str(ROOT / "tests")]

import toolbox_registry  # noqa: E402

import example_gallery as gallery  # noqa: E402
import hive_corpus_cases  # noqa: E402
import sqlglot_composer  # noqa: E402
from sqlglot_composer import example_database  # noqa: E402
from sqlglot_composer.clauses import Statement, derived_tables  # noqa: E402
from sqlglot_composer.describe import StandIn  # noqa: E402
from sqlglot_composer.tables import Table  # noqa: E402
from sqlglot_composer.unchecked import SessionSettings, UncheckedStatement  # noqa: E402

# Where the golden corpus is committed.
GOLDEN = ROOT / "tests" / "hive_corpus" / f"{toolbox_registry.FOLDER}.txt"
# The command that writes the golden.
COMMAND = "python tools/hive_corpus.py"

PIN = re.search(r"^sqlglot==(\S+)$",
                (ROOT / "requirements-dev.txt").read_text(encoding="utf-8"), re.MULTILINE)[1]
# The exception types a Toolbox refusal comes as; is_refusal tells a refusal from a bug.
REFUSAL_TYPES = (sqlglot_composer.GuardRefused, sqlglot_composer.LoadRefused, TypeError,
                 ValueError)
# The lines that start a case and a part of a case in the file.
CASE_MARK = "== "
PART_MARK = "-- "


# --- The cases -------------------------------------------------------------------------------


def docstring_cases(
) -> list[tuple[str, Callable[..., list[Statement | SessionSettings | UncheckedStatement]]]]:
    """Each docstring example that hands a Statement on, as a function that replays it."""
    found = []
    for names, doc in gallery.docstrings():
        parts = [part for part in doctest.DocTestParser().parse(doc) if not isinstance(part, str)]
        if any(name + "(" in part.source for part in parts for name in gallery.HANDED_TO):
            found.append((f"doc:{names[0]}", _replaying(parts)))
    return found


def _replaying(
    parts: list[doctest.Example],
) -> Callable[..., list[Statement | SessionSettings | UncheckedStatement]]:
    def build() -> list[Statement | SessionSettings | UncheckedStatement]:
        handed = []
        scope = gallery.example_scope(handed)
        for part in parts:
            gallery.run_step(part.source, scope)
        return _unique([s for _, s in handed])
    return build


def worked_example_cases() -> list[tuple[str, Callable[..., list[Statement]]]]:
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


def _opted_out(function: Callable[..., Statement | list[Statement]],
               keyword: str) -> Callable[..., Statement | list[Statement]]:
    """`function` called with its Guard's opt-out keyword set."""
    return lambda: function(**{keyword: True})


def _listed(
    function: Callable[..., Statement | list[Statement]],
) -> Callable[..., list[Statement]]:
    """`function`'s Statements as a list: it returns one, or a list of them."""
    def build() -> list[Statement]:
        built = function()
        return list(built) if isinstance(built, list) else [built]
    return build


def cases(
) -> list[tuple[str, Callable[..., list[Statement | SessionSettings | UncheckedStatement]]]]:
    """Every case, in a fixed order: docstrings, Worked examples, edge cases, generated ones,
    then Session settings and Unchecked statements."""
    found = (docstring_cases() + worked_example_cases() + hive_corpus_cases.edge_cases()
             + hive_corpus_cases.generated_cases() + hive_corpus_cases.by_hand_cases())
    ids = [case_id for case_id, _ in found]
    repeated = sorted({case_id for case_id in ids if ids.count(case_id) > 1})
    if repeated:
        raise ValueError(f"Two cases share an id: {', '.join(repeated)}")
    return found


def _unique(statements: list[Statement | SessionSettings | UncheckedStatement]
            ) -> list[Statement | SessionSettings | UncheckedStatement]:
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


def case_text(
    case_id: str, build: Callable[..., list[Statement | SessionSettings | UncheckedStatement]],
) -> str:
    """One case: each of its Statements, then the lineage report of all of them."""
    lines = [CASE_MARK + case_id]
    with gallery.example_setting():
        try:
            statements = build()
        except REFUSAL_TYPES as error:
            return "\n".join(lines + [PART_MARK + "refused", refusal_or_raise(error), ""])
        for number, s in enumerate(statements, 1):
            lines += statement_lines(number, s)
        lines += lineage_lines([s for s in statements
                                if not isinstance(s, Statement) or s._ddl is None])
    return "\n".join(lines + [""])


def statement_lines(number: int,
                    s: Statement | SessionSettings | UncheckedStatement) -> list[str]:
    """A Statement's Hive, then the repr of its outputs and conditions, and each Derived table's.

    Session settings and an Unchecked statement aren't Statements: their Hive, and what
    show_hive prints for them, with the comment that names or marks them. An Admin statement
    shows what show_hive prints too: what it changes, ahead of its Hive.
    """
    lines = [PART_MARK + f"Statement {number}: to_hive"]
    try:
        lines.append(sqlglot_composer.to_hive(s))
    except Exception as error:  # noqa: BLE001 - what to_hive stops with is part of the output
        lines.append(refused_text(error))
    if isinstance(s, (SessionSettings, UncheckedStatement)) or (
            isinstance(s, Statement) and s._admin_call is not None):
        with contextlib.redirect_stdout(io.StringIO()) as printed:
            sqlglot_composer.show_hive(s)
        return lines + [PART_MARK + f"Statement {number}: show_hive",
                        printed.getvalue().rstrip("\n")]
    for step, name in [(s, "the Statement")] + [
            (table._statement, f"Derived table {table._name}") for table in derived_tables(s)]:
        shown = parts_shown(step)
        if shown:
            lines += [PART_MARK + f"Statement {number}: {name}", *shown]
    return lines


def parts_shown(step: Statement) -> list[str]:
    """The repr of each output and condition of one step, as a notebook shows it."""
    shown = [f"output {name}: {column!r}" for column, name in step._outputs]
    shown += [f"read {number} ON: {read.on!r}"
              for number, read in enumerate(step._reads, 1) if read.on is not None]
    shown += [f"WHERE: {condition!r}" for condition in step._where]
    shown += [f"HAVING: {condition!r}" for condition in step._having]
    return shown


def lineage_lines(statements: list[Statement | SessionSettings | UncheckedStatement]
                  ) -> list[str]:
    """export_lineage's Markdown report of the Statements, without its dated last line."""
    if all(isinstance(s, SessionSettings) for s in statements):
        return []  # none, or only Session settings, which it draws nothing for
    with tempfile.TemporaryDirectory() as folder:
        try:
            _, markdown = sqlglot_composer.export_lineage(*statements, to=Path(folder) / "case.html")
        except Exception as error:  # noqa: BLE001 - as for to_hive
            return [PART_MARK + "export_lineage", refused_text(error)]
        text = markdown.read_text(encoding="utf-8")
    kept = [_undated(line) for line in text.splitlines()]
    return [PART_MARK + "export_lineage", *[line for line in kept if line is not None]]


def _undated(line: str) -> str | None:
    """A line of a lineage as the corpus keeps it: its dated last line left out, all but the
    Session settings it names, if any."""
    if not line.startswith("Made by export_lineage on"):
        return line
    settings = line.find(" Session settings ")
    return line[settings + 1:] if settings != -1 else None


# --- The commands sent to the warehouse ------------------------------------------------------


def warehouse_text(t: Table) -> str:
    """The commands write_table_reference, check_table_reference and check_key send for `t`,
    each through a stand-in warehouse holding the table, which keeps them; any query but
    DESCRIBE gives back nothing, so check_key's is refused for its answer's lack of columns."""
    lines = [CASE_MARK + f"warehouse:{t._name}"]
    helpers = [("write_table_reference", _write_table_reference),
               ("check_table_reference", sqlglot_composer.check_table_reference),
               ("check_key", _check_key)]
    with gallery.example_setting():
        for name, helper in helpers:
            query = StandIn(t)
            try:
                helper(t, query=query)
            except REFUSAL_TYPES as error:
                query.sent.append(refusal_or_raise(error))
            lines += [PART_MARK + name, *query.sent]
    return "\n".join(lines + [""])


def _check_key(t: Table, *, query: StandIn) -> None:
    """check_key, reading every Partition of a partitioned table, which picks none itself."""
    sqlglot_composer.check_key(t, query=query, reads_all_partitions=bool(t._partitioned_by))


def _write_table_reference(t: Table, *, query: StandIn) -> None:
    """write_table_reference, in a folder of its own, so its file never meets another."""
    with tempfile.TemporaryDirectory() as folder, contextlib.chdir(folder):
        sqlglot_composer.write_table_reference(t._name, query=query)


def tables() -> list[Table]:
    """The Example database's Table references, then the edge cases' own."""
    return [example_database.jobs, example_database.job_runs, example_database.run_alerts,
            *hive_corpus_cases.edge_tables()]


# --- The file --------------------------------------------------------------------------------


def corpus_text() -> str:
    """The whole golden corpus, as one string."""
    header = (f"# What {toolbox_registry.PRODUCT} shows today, written by tools/hive_corpus.py. Don't "
              "edit it by hand.\n")
    blocks = [case_text(case_id, build) for case_id, build in cases()]
    blocks += [warehouse_text(t) for t in tables()]
    return header + "\n".join(blocks)


def cannot_write() -> str | None:
    """Why this Python can't write the golden, or None when it can."""
    import sqlglot

    if sqlglot.__version__ != PIN:
        return (f"the golden is written at the sqlglot pin, {PIN}, and this is "
                f"{sqlglot.__version__}: another sqlglot writes some Hive differently")
    return None


def cases_in(text: str) -> dict[str, str]:
    """A golden corpus, case by case: each case's id, and what it shows."""
    blocks = text.split("\n" + CASE_MARK)[1:]
    return {block.split("\n", 1)[0]: block for block in blocks}


def main() -> int:
    reason = cannot_write()
    if reason is not None:
        print(f"Nothing was written: {reason}.")
        return 1
    text = corpus_text()
    GOLDEN.parent.mkdir(parents=True, exist_ok=True)
    with open(GOLDEN, "w", encoding="utf-8", newline="\n") as file:
        file.write(text)
    print(f"Wrote {GOLDEN.relative_to(ROOT)}: {text.count(chr(10) + CASE_MARK)} cases.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
