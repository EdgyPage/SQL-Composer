"""The admin module: changes to your own Saved tables, written and checked for you.

It isn't brought by `from sqlglot_composer import *`. Import it by name:

    from sqlglot_composer import admin

Each function makes an Admin statement, an ordinary Statement that run_execute(s, execute) sends
like any other; admin.move_to_own_folder makes a list of them, sent one at a time, and
admin.check_the_copy compares the counts through your query before it gives the steps that
finish the move. show_hive prints, before an Admin statement's Hive, what it changes, what can't
be undone, and what to check first. Each refuses a table that isn't one of your Saved tables: a
Table reference with no location= is a table someone else owns. Each run of one adds an entry to
the Admin log (help(set_admin_log)).
"""

from __future__ import annotations

import copy
import urllib.parse
from collections.abc import Callable

import pandas as pd

from . import describe, kinds
from .clauses import Statement
from .unchecked import logged_run
from .upkeep import ddl_statement
from .conditions import Condition
from .writing import hive_statement, hive_text
from .refusals import (
    need_warehouse_call,
    refuse,
    refuse_removed_arguments,
    refuse_what_isnt_a_dataframe,
)
from .shared import counted, escaped_literal, in_words
from .tables import (
    FILE_FORMATS,
    PURGE,
    ROWS_WITH_NO_VALUE,
    Table,
    column_definition,
    create_table,
    need_saved_table,
    partitions_named,
    property_pairs,
    python_text,
    readable,
    same_folder,
    table_node,
)
from .trees import Node, combined


# --- Pieces every Admin statement shares ------------------------------------------------------


def _admin_statement(call: str, about: list[str], ddl: Node, hive: str | None = None
                     ) -> Statement:
    """An Admin statement: `ddl` is its tree, or, for an ALTER TABLE, the table it changes,
    whose Hive is `hive`. `about` is what show_hive prints first, an item to a sentence or
    two."""
    s = ddl_statement(kinds.ADMIN, ddl)
    s._admin_hive = hive
    s._admin_call = call
    s._admin_about = about
    return s


def _name(t: Table) -> str:
    """The table's name as the Hive writes it."""
    return hive_text(table_node(t._name))


def _value(text: str) -> str:
    """A value in quotes, as the Hive writes it."""
    return hive_text(Node("Literal", this=text, is_string=True))


def _listed(lines: list[str]) -> str:
    """Pieces in brackets, one to a line, as create_table writes its columns."""
    return "(\n" + ",\n".join(f"  {line}" for line in lines) + "\n)"


def _set_tblproperties(t: Table, pairs: list[tuple[str, str]]) -> str:
    """ALTER TABLE ... SET TBLPROPERTIES, each property a name and a value."""
    return (f"ALTER TABLE {_name(t)} SET TBLPROPERTIES "
            + _listed([f"{_value(name)}={_value(value)}" for name, value in pairs]))


def _purge_note(t: Table, whose: str) -> str:
    """What dropping does to the files, `whose` being "the table's" or "those Partitions'", by
    the Table reference's purge=."""
    if t._purge:
        return (f"Can't be undone when the table itself has {PURGE} true, as purge=True in its "
                f"Table reference asks: then {whose} files go too, and nothing brings them back.")
    if not t._partitioned_by:
        found_again = "A table made there again reads them back"
    else:
        found_again = ("The warehouse reads them again once repair_partitions(t) lists their "
                       "Partitions, even in a table made there again, and an INSERT_INTO of one "
                       "of those Partitions adds to its old rows")
    return (f"{whose[0].upper()}{whose[1:]} files stay in the table's folder, {t._location}, "
            f"unless the table itself has {PURGE} true: purge=True isn't in its Table "
            f"reference. {found_again}; only someone with access to the folder can delete "
            "them.")


def _check_purge(t: Table) -> str:
    return (f"Check first: DESCRIBE FORMATTED {_name(t)} shows, under Table Parameters, whether "
            f"{PURGE} is true in the table itself: that, not the Table reference, decides "
            "whether the files go.")


# --- Dropping ---------------------------------------------------------------------------------


def drop_table(t: Table) -> Statement:
    """Drop one of your Saved tables: the DROP TABLE IF EXISTS Statement.

    >>> from sqlglot_composer import admin
    >>> daily_runs = Table("mart.daily_runs", partitioned_by=["dt"],
    ...     columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
    ...     location="/data/your_team/mart.db/daily_runs", purge=True)
    >>> text = show_hive(admin.drop_table(daily_runs))
    -- admin.drop_table(mart.daily_runs) drops the table mart.daily_runs: the warehouse forgets
    -- it, and every Statement that reads it fails until it is created again.
    -- Can't be undone when the table itself has external.table.purge true, as purge=True in its
    -- Table reference asks: then the table's files go too, and nothing brings them back.
    -- Check first: DESCRIBE FORMATTED mart.daily_runs shows, under Table Parameters, whether
    -- external.table.purge is true in the table itself: that, not the Table reference, decides
    -- whether the files go.
    DROP TABLE IF EXISTS mart.daily_runs;

    The warehouse forgets the table, and every Statement that reads it fails until it is
    created again. Whether its files go too is up to the table itself: they go, every
    Partition of it, when the table has external.table.purge true, which purge=True in its
    Table reference asks for. create_table writes it into the table it makes; for a table made
    before you gave its Table reference purge=True, send admin.set_properties(t) first.
    Otherwise the warehouse only forgets the table: its files stay in its folder, and a table
    created there again gets their Partitions back once repair_partitions(t) lists them, or
    adds to a Partition's old rows with INSERT_INTO; one with no partitioned_by= reads them
    back at once. It refuses a table that isn't one of your Saved tables, a Table reference
    with no location=, such as job_runs, which others fill.

    The usual reason is a change to a Saved table's columns that admin.add_columns can't
    make, such as removing or renaming one: drop the table, create it again, and write its
    rows again, with purge=True set in the table first, or the old rows come back. IF EXISTS
    means that sending it for a table that isn't there does nothing, rather than failing.
    """
    t = need_saved_table(t, "admin.drop_table(...)")
    call = f"admin.drop_table({t._name})"
    about = [f"{call} drops the table {t._name}: the warehouse forgets it, and every Statement "
             "that reads it fails until it is created again.",
             _purge_note(t, "the table's"), _check_purge(t)]
    return _admin_statement(call, about, Node("Drop", target=table_node(t._name)))


def drop_partitions(t: Table, *, where: Condition | list[Condition]) -> Statement:
    """Drop some of a Saved table's Partitions: an ALTER TABLE Statement.

    >>> from sqlglot_composer import admin
    >>> daily_runs = Table("mart.daily_runs", partitioned_by=["dt"],
    ...     columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
    ...     location="/data/your_team/mart.db/daily_runs", purge=True)
    >>> text = show_hive(admin.drop_partitions(daily_runs,
    ...     where=less_than(daily_runs.dt, "2025-10-01")))
    -- admin.drop_partitions(mart.daily_runs, where=less_than(daily_runs.dt, "2025-10-01")) drops
    -- each Partition of mart.daily_runs where dt < '2025-10-01', every row of it, so no
    -- Statement reads it again.
    -- Can't be undone when the table itself has external.table.purge true, as purge=True in its
    -- Table reference asks: then those Partitions' files go too, and nothing brings them back.
    -- Check first: SHOW PARTITIONS mart.daily_runs lists its Partitions: the ones where dt <
    -- '2025-10-01' go.
    ALTER TABLE mart.daily_runs DROP IF EXISTS PARTITION (dt < '2025-10-01');

    Each Partition of the table that `where` picks goes: every row of it, so no Statement
    reads it again. It is how a Saved table keeps only so many Partitions, and does the job
    TRUNCATE can't: Hive refuses TRUNCATE on an external table, a table whose files are in a
    folder you give, and every table create_table makes is one. The Partitions' files go too
    when the table has external.table.purge true, which purge=True in its Table reference asks
    for (help(admin.drop_table)); otherwise they stay in the table's folder.

    `where` picks Partitions by the table's partition columns, as WHERE(...) picks rows: a
    condition, or a list of conditions that must all hold, each comparing a partition column
    with a value: equals, not_equals, at_least, at_most, more_than, less_than or between, or
    all_of(...) of them. Hive takes these in DROP PARTITION, so one Statement drops every
    Partition they pick. It refuses what DROP PARTITION can't take: any_of(...), a column that
    isn't one of the table's partition columns, a comparison with another column or a
    calculation, and any other condition. It refuses a table with no partitioned_by=, and one
    that isn't one of your Saved tables. The Example database, which is never written to,
    doesn't run it.

    DROP PARTITION has no BETWEEN, so between(...) becomes its two ends; a list's conditions
    are all written in the brackets, each of which must hold:

    >>> print(to_hive(admin.drop_partitions(daily_runs,
    ...     where=between(daily_runs.dt, "2025-01-01", "2025-01-31"))))
    ALTER TABLE mart.daily_runs DROP IF EXISTS PARTITION (dt >= '2025-01-01', dt <= '2025-01-31')
    >>> print(to_hive(admin.drop_partitions(daily_runs,
    ...     where=[at_least(daily_runs.dt, "2025-01-01"),
    ...            less_than(daily_runs.dt, "2025-02-01")])))
    ALTER TABLE mart.daily_runs DROP IF EXISTS PARTITION (dt >= '2025-01-01', dt < '2025-02-01')
    """
    t = need_saved_table(t, "admin.drop_partitions(...)")
    if not t._partitioned_by:
        refuse(
            what=f"admin.drop_partitions(...) was given {t._name}, whose Table reference has no "
            "partitioned_by=.",
            why="It drops whole Partitions, and a table with no partitioned_by= has none.",
            fix=f"To keep fewer rows, write the table again with INSERT_OVERWRITE({t._alias}), "
            "which replaces all its rows with the ones its Statement gives. To empty it, drop "
            f"it with admin.drop_table({t._alias}) and create it again, after "
            f"admin.set_properties({t._alias}) with purge=True in its Table reference, so its "
            "files go too.",
            error=ValueError,
        )
    call = f"admin.drop_partitions({t._name}, where=...)"
    if isinstance(where, tuple):
        refuse(
            what=f"{call} was given a tuple in where=.",
            why="where= is a condition, or a list of conditions that must all hold.",
            fix="Write the conditions in square brackets, as a list: where=[..., ...].",
            error=ValueError,
        )
    conditions = list(where) if isinstance(where, list) else [where]
    for condition in conditions:
        if not isinstance(condition, Condition):
            refuse(
                what=f"{call} was given {condition!r} in where=, which isn't a condition.",
                why="where= picks Partitions with conditions, as WHERE(...) picks rows.",
                fix=f"Pass a condition, such as where=less_than({t._alias}."
                f"{t._partitioned_by[0]}, ...).",
            )
    if not conditions:
        refuse(
            what=f"{call} was given no conditions in where=.",
            why="where= says which Partitions to drop.",
            fix=f"Pass at least one, such as where=less_than({t._alias}."
            f"{t._partitioned_by[0]}, ...).",
        )
    call = f"admin.drop_partitions({t._name}, where={python_text(where)})"
    spec = [hive_text(part) for condition in conditions
            for part in _dropped(t, condition._tree, call)]
    hive = f"ALTER TABLE {_name(t)} DROP IF EXISTS PARTITION ({', '.join(spec)})"
    picked = " and ".join(spec)
    about = [f"{call} drops each Partition of {t._name} where {picked}, every row of it, so no "
             "Statement reads it again.",
             _purge_note(t, "those Partitions'"),
             f"Check first: SHOW PARTITIONS {_name(t)} lists its Partitions: the ones where "
             f"{picked} go."]
    return _admin_statement(call, about, table_node(t._name), hive)


# The comparisons DROP PARTITION takes, by the kind of Node a condition holds.
_DROPPED_BY = ("EQ", "NEQ", "LT", "LTE", "GT", "GTE")


def _dropped(t: Table, tree: Node, call: str) -> list[Node]:
    """The comparisons of DROP PARTITION's brackets a condition's tree makes, each a partition
    column of `t`, named alone, against a value; refused where DROP PARTITION can't take it."""
    tree = tree.unnest()
    if tree.kind == "And":
        return [part for side in tree.flatten() for part in _dropped(t, side, call)]
    if tree.kind == "Between":
        name = _partition_compared(t, tree.parts["this"], call)
        return [Node("GTE", this=Node("Column", name=name),
                     expression=_value_compared(t, tree.parts["low"], name, call)),
                Node("LTE", this=Node("Column", name=name),
                     expression=_value_compared(t, tree.parts["high"], name, call))]
    if tree.kind in _DROPPED_BY:
        name = _partition_compared(t, tree.parts["this"], call)
        return [Node(tree.kind, this=Node("Column", name=name),
                     expression=_value_compared(t, tree.parts["expression"], name, call))]
    if tree.kind == "Or":
        refuse(
            what=f"{call}: where= holds any_of(...).",
            why="DROP PARTITION drops the Partitions where every comparison it is given holds, "
            "and has no OR.",
            fix="Drop each part with a Statement of its own: one admin.drop_partitions(...) "
            "for each condition any_of(...) joined.",
            error=ValueError,
        )
    refuse(
        what=f"{call}: where= holds {readable(tree)}, which DROP PARTITION can't take.",
        why="DROP PARTITION takes only comparisons of a partition column with a value: =, <>, "
        "<, <=, > and >=.",
        fix="Write the Partitions to drop with equals, not_equals, at_least, at_most, "
        "more_than, less_than or between, each of a partition column and a value.",
        error=ValueError,
    )


def _partition_compared(t: Table, column: Node, call: str) -> str:
    """The name of the partition column of `t` a comparison tests, refused when it tests
    anything else."""
    if column.kind == "Column" and column.table == t._alias and column.name in t._partitioned_by:
        return column.name
    if column.kind == "Column" and column.table == t._alias and column.name in t._columns:
        what = f"{t._alias}.{column.name} isn't one of {t._name}'s partition columns"
    elif column.kind == "Column":
        named = f"{column.table}.{column.name}" if column.table else column.name
        what = f"{named} isn't a column of {t._alias}"
    else:
        what = "it compares a calculation, not a partition column"
    refuse(
        what=f"{call}: {what}.",
        why="DROP PARTITION picks whole Partitions, by the values of the columns the table is "
        "partitioned by, and can't test any other column.",
        fix=f"Compare {t._alias}'s partition columns: {', '.join(t._partitioned_by)}.",
        error=ValueError,
    )


def _value_compared(t: Table, value: Node, name: str, call: str) -> Node:
    """The value a partition column is compared with, refused when it isn't a value."""
    if value.kind in ("Literal", "Boolean"):
        return value.copy()
    refuse(
        what=f"{call}: {name} is compared with {readable(value)}, which isn't a value.",
        why="DROP PARTITION compares a partition column with a value written out, such as "
        "'2025-10-01', never with another column or a calculation.",
        fix=f'Compare {name} with a value, such as less_than({t._alias}.{name}, "2025-10-01").',
        error=ValueError,
    )


# --- Adding columns ---------------------------------------------------------------------------


def add_columns(t: Table, *, query: Callable[[str], pd.DataFrame] | None = None,
                **removed: object) -> Statement:
    """Add the new columns of a Saved table's Table reference to the table itself.

    >>> import pandas as pd
    >>> from sqlglot_composer import admin
    >>> # the warehouse's answer to DESCRIBE mart.daily_runs
    >>> def query_at_work(hive: str) -> pd.DataFrame:
    ...     return pd.DataFrame([
    ...         ("job_id", "bigint", ""), ("runs", "bigint", ""),
    ...         ("# Partition Information", None, None), ("dt", "string", ""),
    ...     ], columns=["col_name", "data_type", "comment"])
    >>> daily_runs = Table("mart.daily_runs", partitioned_by=["dt"],
    ...     columns={"job_id": "bigint", "runs": "bigint", "fails": "bigint", "dt": "string"},
    ...     location="/data/your_team/mart.db/daily_runs")
    >>> text = show_hive(admin.add_columns(daily_runs, query=query_at_work))
    -- admin.add_columns(mart.daily_runs, query=...) adds the column fails to mart.daily_runs,
    -- after its other columns. The rows already there read NULL in it until they are written
    -- again.
    -- CASCADE adds it to each Partition already in the table too, so a Partition written again
    -- keeps its values.
    -- Hard to undo: Hive drops a column only when every other column is listed again by hand,
    -- with ALTER TABLE ... REPLACE COLUMNS.
    -- Check first: DESCRIBE mart.daily_runs lists the table's columns now.
    ALTER TABLE mart.daily_runs ADD COLUMNS (
      fails BIGINT
    ) CASCADE;

    It sends DESCRIBE through your `query` as it is made, and adds each column of the Table
    reference that the table doesn't have yet. So you add a column by adding its line to the
    Table reference first, after the table's other columns (the lines of its partition
    columns may stay last, as they aren't among them): Hive adds new columns after the table's
    own, and a write fills a table's columns in their order. Then run the Statement it gives,
    with your execute. The rows already in the table read NULL in a new column until they are
    written again. For a table with partitioned_by= it writes CASCADE: each Partition already
    there gets the new columns too. Without it, each of those Partitions would keep its old
    list of columns, and a Partition written again would lose the new columns' values.

    It refuses a table that isn't one of your Saved tables, a Table reference with no new
    column, a new column that isn't after the table's own, and a new partition column, which a
    table can't gain: create a new table with it, and copy the rows in.
    """
    refuse_removed_arguments("add_columns", removed, add_columns)
    need_warehouse_call("admin.add_columns", "query", query, "It sends DESCRIBE through your "
                        "query, to see which columns the table has.")
    t = need_saved_table(t, "admin.add_columns(...)")
    call = f"admin.add_columns({t._name}, query=...)"
    described = describe.ask(t._name, query, "admin.add_columns(...)")
    new = _new_columns(t, described.columns, call)
    definitions = [hive_text(column_definition(t, column, call)) for column in new]
    hive = f"ALTER TABLE {_name(t)} ADD COLUMNS {_listed(definitions)}"
    named, them, its = (
        f"the columns {in_words(new)}", "them", "their") if len(new) > 1 else (
        f"the column {new[0]}", "it", "its")
    about = [f"{call} adds {named} to {t._name}, after its other columns. The rows already "
             f"there read NULL in {them} until they are written again."]
    if t._partitioned_by:
        hive += " CASCADE"
        about.append(f"CASCADE adds {them} to each Partition already in the table too, so a "
                     f"Partition written again keeps {its} values.")
    about += ["Hard to undo: Hive drops a column only when every other column is listed again "
              "by hand, with ALTER TABLE ... REPLACE COLUMNS.",
              f"Check first: DESCRIBE {_name(t)} lists the table's columns now."]
    return _admin_statement(call, about, table_node(t._name), hive)


def _new_columns(t: Table, columns: dict[str, str], call: str) -> list[str]:
    """The Table reference's columns the table doesn't have, refused where they can't be
    added: none, a partition column, one without a type, or one before a column the table
    has."""
    if not columns:
        refuse(
            what=f"{call}: DESCRIBE listed no columns for {t._name}.",
            why="It adds the Table reference's columns that the table doesn't have, and can't "
            "tell which those are.",
            fix="Check the table's name, and that your query returns what DESCRIBE prints.",
            error=ValueError,
        )
    partitions = t._partitioned_by
    missing = [column for column in partitions if column not in columns]
    if missing:
        refuse(
            what=f"{call}: {missing[0]} is a partition column in the Table reference, but "
            "not in the table.",
            why="A table can't gain a partition column: each Partition is a folder, and the "
            "table's files are already laid out without it.",
            fix="Create a new table with it, and write its rows into it again; or, if the "
            "table's partition column has another name, correct the Table reference.",
            error=ValueError,
        )
    body = [column for column in t._columns if column not in partitions]
    new = [column for column in body if column not in columns]
    if not new:
        refuse(
            what=f"{call}: {t._name} has every column of its Table reference already.",
            why="It adds the columns the Table reference has and the table doesn't.",
            fix="Add the new column's line to the Table reference first, with its type, after "
            "the other columns.",
            error=ValueError,
        )
    kept = [column for column in body if column in columns]
    if kept and body.index(new[0]) < body.index(kept[-1]):
        refuse(
            what=f"{call}: the Table reference lists {new[0]} before {kept[-1]}, which the "
            "table has already.",
            why="Hive adds new columns after the table's own, and a write fills a table's "
            "columns in their order, so the Table reference lists them in the table's order.",
            fix=f"Move the line of {new[0]} after the line of {kept[-1]}.",
            error=ValueError,
        )
    untyped = [column for column in new if not t._columns[column]]
    if untyped:
        refuse(
            what=f"{call}: {untyped[0]} has no type: its line in the Table reference says "
            "None.",
            why="Hive needs each new column's type to add it.",
            fix=f'Give it its Hive type, such as {escaped_literal(untyped[0])}: "string".',
            error=ValueError,
        )
    return new


# --- Table properties -------------------------------------------------------------------------


def set_properties(t: Table) -> Statement:
    """Set a Saved table's properties as its Table reference gives them.

    >>> from sqlglot_composer import admin
    >>> daily_runs = Table("mart.daily_runs", partitioned_by=["dt"],
    ...     columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
    ...     location="/data/your_team/mart.db/daily_runs", purge=True)
    >>> text = show_hive(admin.set_properties(daily_runs))
    -- admin.set_properties(mart.daily_runs) sets 1 table property of mart.daily_runs, as its
    -- Table reference says. Its other properties, and its rows, stay as they are.
    -- With external.table.purge true, dropping the table or its Partitions deletes their files
    -- too, from now on.
    -- Can be undone: change purge=, compression= or properties= in the Table reference back to
    -- what the table had, and send this again.
    -- Check first: DESCRIBE FORMATTED mart.daily_runs lists the table's properties now, under
    -- Table Parameters.
    ALTER TABLE mart.daily_runs SET TBLPROPERTIES (
      'external.table.purge'='true'
    );

    It sets the table's properties to its Table reference's: purge= as external.table.purge,
    compression= and properties=. Change the Table reference, then send this, and
    check_table_reference finds the two alike again. Properties the Table reference doesn't
    give stay as they are, and so do the rows. A compression applies to the files written
    from then on; the files already there keep theirs. It refuses a table that isn't one of
    your Saved tables, and a Table reference that gives none of the three.
    """
    t = need_saved_table(t, "admin.set_properties(...)")
    call = f"admin.set_properties({t._name})"
    pairs = property_pairs(t)
    if not pairs:
        refuse(
            what=f"{call}: its Table reference gives no purge=, compression= or properties=.",
            why="It sets the table's properties to what its Table reference gives.",
            fix="Add purge=, compression= or properties= to its Table(...) call, such as "
            "purge=True, then call it again.",
            error=ValueError,
        )
    hive = _set_tblproperties(t, pairs)
    count = counted(len(pairs), "table property", "table properties")
    about = [f"{call} sets {count} of {t._name}, as its Table reference says. Its other "
             "properties, and its rows, stay as they are."]
    if t._purge is not None:
        about.append(f"With {PURGE} true, dropping the table or its Partitions deletes their "
                     "files too, from now on." if t._purge else
                     f"With {PURGE} false, dropping the table or its Partitions leaves their "
                     "files in its folder, from now on.")
    if t._compression is not None:
        compression = FILE_FORMATS[t._stored_as][0]
        about.append(f"{compression} applies to the files written from now on; the files "
                     "already there keep theirs.")
    about += ["Can be undone: change purge=, compression= or properties= in the Table "
              "reference back to what the table had, and send this again.",
              f"Check first: DESCRIBE FORMATTED {_name(t)} lists the table's properties now, "
              "under Table Parameters."]
    return _admin_statement(call, about, table_node(t._name), hive)


# --- Moving a table to its own folder ---------------------------------------------------------

# What the copy is called while the move runs: the table's name with this added.
_MOVING = "_moving"


def move_to_own_folder(t: Table, *, query: Callable[[str], pd.DataFrame] | None = None,
                       **removed: object) -> list[Statement]:
    """Move a Saved table to a folder of its own: the move's first two Statements.

    >>> import pandas as pd
    >>> from sqlglot_composer import admin
    >>> # the warehouse's answer to DESCRIBE FORMATTED, with mart.daily_runs in a shared folder
    >>> def query_at_work(hive: str) -> pd.DataFrame:
    ...     return pd.DataFrame([
    ...         ("job_id", "bigint", ""), ("runs", "bigint", ""),
    ...         ("# Partition Information", None, None), ("dt", "string", ""),
    ...         ("# Detailed Table Information", None, None),
    ...         ("Location:", "hdfs://namenode:8020/data/your_team/tables", None),
    ...         ("Table Type:", "EXTERNAL_TABLE", None),
    ...     ], columns=["col_name", "data_type", "comment"])
    >>> daily_runs = Table("mart.daily_runs", partitioned_by=["dt"],
    ...     columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
    ...     location="/data/your_team/mart.db/daily_runs")
    >>> moves = admin.move_to_own_folder(daily_runs, query=query_at_work)
    >>> len(moves)
    2
    >>> print(to_hive(moves[1]))
    INSERT OVERWRITE TABLE mart.daily_runs_moving PARTITION(dt)
    SELECT
      daily_runs.job_id,
      daily_runs.runs,
      daily_runs.dt
    FROM mart.daily_runs AS daily_runs

    A Saved table belongs in its own folder, the one its Table reference's location= names: in
    a folder it shares, two tables read each other's files, and an INSERT OVERWRITE of a
    Partition in one can delete the other's files for that Partition. This sends DESCRIBE
    FORMATTED through your `query` to find where the table is, and returns the first two
    Statements of the move, to send in order with run_execute, one at a time:

    - create a copy, named like the table with _moving added, at the folder the Table
      reference gives the table, its own, stored as the Table reference says;
    - copy the whole table into it with one INSERT OVERWRITE, which, for a table with
      partitioned_by=, fills each Partition from the rows' own values, as any write does, and
      needs the Session setting "dynamic_partitions" sent first.

    Then admin.check_the_copy(t, query=query) compares the rows in the two, Partition by
    Partition, and stops the move, before anything is dropped, if any Partition differs or is
    missing from the copy, such as one written since the copy. Once they match, it gives the
    Statements that finish the move:

    - set external.table.purge to false on the old table, whose folder may hold other
      tables' files, so that dropping it leaves them. A managed table, one whose files the
      warehouse keeps where it chooses, as create_table made them before 5.0, skips this
      step: its files are its own, and go with it;
    - drop the old table;
    - give the copy the table's name: its files stay at its own folder.

    So this gives two Statements, and admin.check_the_copy three more, or two for a managed
    table. Each can be sent again until the old table is dropped: if one fails, fix what it
    says, and send them again from the first. The drop comes only from admin.check_the_copy,
    once the copy holds every row. The rows are copied as the old table reads them, so where
    two tables shared a folder, each read the other's rows too: check them first, or write the
    table again from its source instead. It refuses a table that isn't one of your Saved
    tables, one already at its own folder, and one that lacks a column of its Table reference.
    The Example database is never written to, so it doesn't run the steps.

    show_hive(moves) prints both steps, and at work the move is sent in turn, after the
    Session setting the copy needs:

        run_execute(hive_settings("dynamic_partitions"), execute)
        for step in moves:
            run_execute(step, execute)
        for step in admin.check_the_copy(daily_runs, query=query):
            run_execute(step, execute)
    """
    refuse_removed_arguments("move_to_own_folder", removed, move_to_own_folder)
    need_warehouse_call("admin.move_to_own_folder", "query", query, "It sends DESCRIBE "
                        "FORMATTED through your query, to find the table's folder.")
    t = need_saved_table(t, "admin.move_to_own_folder(...)")
    call = f"admin.move_to_own_folder({t._name}, query=...)"
    described = describe.ask(t._name, query, "admin.move_to_own_folder(...)", formatted=True)
    managed = _check_movable(t, described, call)
    copy_of = _copy_of(t)
    return _numbered(call, [_create_step(t, copy_of, call, managed), _copy_step(t, copy_of)])


def check_the_copy(t: Table, *, query: Callable[[str], pd.DataFrame] | None = None,
                   **removed: object) -> list[Statement]:
    """Compare a moving table's rows with its copy's, then give the move's last steps.

    >>> import pandas as pd
    >>> from sqlglot_composer import admin
    >>> # the warehouse's answers: DESCRIBE FORMATTED of mart.daily_runs, in a shared folder,
    >>> # then the comparison of the counts, which gives back no rows when they match
    >>> def query_at_work(hive: str) -> pd.DataFrame:
    ...     if not hive.startswith("DESCRIBE"):
    ...         return pd.DataFrame(columns=["dt", "old_rows", "copied_rows"])
    ...     return pd.DataFrame([
    ...         ("job_id", "bigint", ""), ("runs", "bigint", ""),
    ...         ("# Partition Information", None, None), ("dt", "string", ""),
    ...         ("# Detailed Table Information", None, None),
    ...         ("Location:", "hdfs://namenode:8020/data/your_team/tables", None),
    ...         ("Table Type:", "EXTERNAL_TABLE", None),
    ...     ], columns=["col_name", "data_type", "comment"])
    >>> daily_runs = Table("mart.daily_runs", partitioned_by=["dt"],
    ...     columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
    ...     location="/data/your_team/mart.db/daily_runs")
    >>> finish = admin.check_the_copy(daily_runs, query=query_at_work)
    >>> print(to_hive(finish[1]))
    DROP TABLE IF EXISTS mart.daily_runs

    The middle of admin.move_to_own_folder(t, query=...): send its two steps first, the copy's
    create and the copy of the rows. This sends, through your `query`, the comparison of the
    rows in the table and its copy, Partition by Partition, and stops the move, before anything
    is dropped, if any Partition differs or is missing from the copy, such as one written since
    the copy: send the copy step again, then call it again. Each comparison adds an entry to
    the Admin log. Once they match, it gives the Statements that finish the move, to send in
    order with run_execute:

    - set external.table.purge to false on the old table, whose folder may hold other tables'
      files, so that dropping it leaves them; a managed table skips this step, since its files
      are its own, and go with it;
    - drop the old table;
    - give the copy the table's name: its files stay at its own folder.

    It sends DESCRIBE FORMATTED of the table through your `query` too, to tell a managed table,
    and refuses what admin.move_to_own_folder refuses. The Example database is never written
    to, so it can't make the copy to compare.
    """
    refuse_removed_arguments("check_the_copy", removed, check_the_copy)
    need_warehouse_call("admin.check_the_copy", "query", query, "It compares the rows in the "
                        "table and its copy through your query, which gives back rows.")
    t = need_saved_table(t, "admin.check_the_copy(...)")
    call = f"admin.check_the_copy({t._name}, query=...)"
    described = describe.ask(t._name, query, "admin.check_the_copy(...)", formatted=True)
    managed = _check_movable(t, described, call)
    copy_of = _copy_of(t)
    check = _counts_match(t, copy_of)
    logged_run("Admin statement", call, hive_statement(_counts_tree(t, copy_of)),
               lambda hive: check(query(hive)))
    steps = [] if managed else [_keep_files_step(t)]
    return _numbered(call, steps + [_drop_step(t, managed), _rename_step(t, copy_of)])


def _copy_of(t: Table) -> Table:
    """The copy a move writes the table into: its Table reference, named with _moving."""
    copy_of = copy.copy(t)
    copy_of._name, copy_of._alias = t._name + _MOVING, t._alias + _MOVING
    return copy_of


def _numbered(call: str, steps: list[Statement]) -> list[Statement]:
    """The steps, each an Admin statement the Admin log names by `call` and its place."""
    for number, step in enumerate(steps):
        step._kind = kinds.ADMIN  # the first step, made by create_table, was marked a create
        step._admin_call = f"{call}[{number}]"
    return steps


def _check_movable(t: Table, described: describe.Description, call: str) -> bool:
    """Refuse a table the move can't, or needn't, move; True for a managed table."""
    location = described.location
    if not location:
        refuse(
            what=f"{call}: DESCRIBE FORMATTED listed no Location for {t._name}.",
            why="It moves the table only when it isn't at its own folder already.",
            fix="Check that your query returns everything DESCRIBE FORMATTED prints.",
            error=ValueError,
        )
    managed = described.managed
    if not managed and not t._partitioned_by and _inside(t._location, location):
        refuse(
            what=f"{call}: {t._name}'s own folder, {t._location}, is inside the folder it is "
            f"in now, {location}.",
            why="A table with no partitioned_by= reads every file under its folder, the folders "
            "inside it too where the warehouse is set to, so the old table could read the "
            "copy's files as its own while the move runs.",
            fix="Give its Table reference a location= outside that folder, and move it there.",
            error=ValueError,
        )
    if not managed and same_folder(location, t._location):
        refuse(
            what=f"{call}: {t._name} is at its own folder already, {location}.",
            why="There is nothing to move.",
            fix="Leave it where it is; check_table_reference(t, query=...) says whether "
            "anything else differs.",
            error=ValueError,
        )
    lacking = [column for column in t._columns if column not in described.columns]
    if lacking:
        refuse(
            what=f"{call}: {t._name} has no column {lacking[0]}, which its Table reference "
            "lists.",
            why="The move copies the Table reference's columns from the table, so each must "
            "be there.",
            fix="Make the Table reference match the table first: "
            "check_table_reference(t, query=...) lists what differs.",
            error=ValueError,
        )
    return managed


def _inside(folder: str, other: str) -> bool:
    """Whether `folder` is inside `other`, compared without their storage's name."""
    path = urllib.parse.urlsplit(folder).path.rstrip("/")
    return path.startswith(urllib.parse.urlsplit(other).path.rstrip("/") + "/")


def _create_step(t: Table, copy_of: Table, call: str, managed: bool) -> Statement:
    folder = copy_of._location
    about = [f"{call} moves {t._name} to its own folder, {folder}. This first step creates "
             f"{copy_of._name} there, and the next copies the table's rows into it. Then "
             f"admin.check_the_copy compares the two and gives the steps that drop {t._name} "
             "and give the copy its name. Send them in order, one at a time."]
    about.append("The old table's files are dropped with it: it is managed, so its files "
                 "are its own." if managed else
                 "The old table's files stay where they are, since its folder may hold other "
                 "tables' files too: ask whoever looks after the folder before deleting any.")
    statement = create_table(copy_of, may_exist=True)
    statement._admin_about = about
    return statement


def _column(t: Table, column: str) -> Node:
    return Node("Column", name=column, table=t._alias)


def _copy_step(t: Table, copy_of: Table) -> Statement:
    """One INSERT OVERWRITE of the whole table into its copy, its Partitions filled from the
    rows, so the partition columns come last, in partitioned_by order."""
    partitions = t._partitioned_by
    columns = [column for column in t._columns if column not in partitions] + partitions
    # PARTITION(region, dt): none named, so each is filled from the rows.
    partition = partitions_named(t, None, "admin.move_to_own_folder",
                                 "then the copy fills each partition column from the rows").tree
    select = Node("Select", outputs=[_column(t, column) for column in columns],
                  source=table_node(t._name, alias=t._alias))
    tree = Node("Insert", target=table_node(copy_of._name, partition=partition), select=select,
                overwrite=True)
    about = [f"Copies all of {t._name}'s rows into {copy_of._name}."]
    if partitions:
        about.append(f"It fills {', '.join(partitions)} from the rows, which needs the Session "
                     'setting "dynamic_partitions": send run_execute(hive_settings('
                     '"dynamic_partitions"), execute) before it.')
    return _admin_statement("", about, tree)


def _partition_value(t: Table, column: str) -> Node:
    """A partition column's value as text, rows with none counted as Hive names their
    Partition, so that a comparison by = matches them too."""
    return Node("Coalesce", this=Node("Cast", this=_column(t, column), to="STRING"),
                expressions=[Node("Literal", this=ROWS_WITH_NO_VALUE, is_string=True)])


def _counts(t: Table, name: str) -> Node:
    """Each Partition's count of rows in a table, or the whole table's, as a Derived table
    named `name`."""
    counted = Node("Alias", this=Node("Count", this=Node("Star")), alias="row_count")
    source = table_node(t._name, alias=t._alias)
    partitions = t._partitioned_by
    if not partitions:
        select = Node("Select", outputs=[counted], source=source)
    else:
        values = [Node("Alias", this=_partition_value(t, column), alias=column)
                  for column in partitions]
        select = Node("Select", outputs=[*values, counted], source=source,
                      group_by=[_partition_value(t, column) for column in partitions])
    return Node("CTE", this=select, alias=name)


def _counts_tree(t: Table, copy_of: Table) -> Node:
    """The comparison: each Partition whose rows differ between the table and its copy."""
    old, new = Node("Column", name="row_count", table="old_counts"), Node(
        "Column", name="row_count", table="copied_counts")
    partitions = t._partitioned_by
    outputs = [*[Node("Column", name=column, table="old_counts") for column in partitions],
               Node("Alias", this=old.copy(), alias="old_rows"),
               Node("Alias", this=new.copy(), alias="copied_rows")]
    on = None
    if partitions:
        on = combined("And", [Node("EQ", this=Node("Column", name=column, table="copied_counts"),
                                   expression=Node("Column", name=column, table="old_counts"))
                              for column in partitions])
    differs = Node("Or", this=Node("Is", this=new.copy(), expression=Node("Null")),
                   expression=Node("NEQ", this=new.copy(), expression=old.copy()))
    return Node("Select",
                derived_tables=[_counts(t, "old_counts"), _counts(copy_of, "copied_counts")],
                outputs=outputs, source=table_node("old_counts"),
                joins=[Node("Join", how="LEFT JOIN" if on else "CROSS JOIN",
                            this=table_node("copied_counts"), on=on)],
                where=differs)


def _counts_match(t: Table, copy_of: Table) -> Callable[[object], pd.DataFrame]:
    """The check check_the_copy hands the comparison's result to: it refuses any Partition
    that differs. Rows with no value in a partition column are counted under
    ROWS_WITH_NO_VALUE, as Hive names their Partition."""
    def check(result: object) -> pd.DataFrame:
        refuse_what_isnt_a_dataframe(result)
        if len(result) == 0:
            return result
        many = len(result)
        refuse(
            what=f"The move of {t._name} stopped: its copy, {copy_of._name}, doesn't hold the "
            "same number of rows" + ("" if not t._partitioned_by else
                                     f" in {counted(many, 'Partition')}")
            + ":\n" + result.to_string(index=False),
            why="The old table is dropped only once all of it is copied, so nothing was "
            "dropped.",
            fix="Send the copy step again, moves[1], which copies the whole table as it is now, "
            "then call admin.check_the_copy again." + ("" if not t._partitioned_by else
                                             " Where copied_rows is empty (NaN), that Partition "
                                             "is missing from the copy: it was written since "
                                             "the copy was made."),
            error=ValueError,
        )
    return check


def _keep_files_step(t: Table) -> Statement:
    hive = _set_tblproperties(t, [(PURGE, "false")])
    about = [f"Sets {PURGE} to false on {t._name}, so that dropping it next leaves the "
             "files in its folder, which other tables may read."]
    return _admin_statement("", about, table_node(t._name), hive)


def _drop_step(t: Table, managed: bool) -> Statement:
    gone = ("its files go too, since it is managed" if managed else
            "its files stay in the folder it shared")
    about = [f"Drops the old {t._name}: {gone}. Can't be undone: admin.check_the_copy gives "
             "it only once the copy holds every row."]
    return _admin_statement("", about, Node("Drop", target=table_node(t._name)))


def _rename_step(t: Table, copy_of: Table) -> Statement:
    hive = f"ALTER TABLE {_name(copy_of)} RENAME TO {_name(t)}"
    about = [f"Gives {copy_of._name} the name {t._name}. Its files stay at its own folder, "
             f"{copy_of._location}. If this step fails, send it alone again."]
    return _admin_statement("", about, table_node(copy_of._name), hive)


__all__ = ["drop_table", "drop_partitions", "add_columns", "set_properties",
           "move_to_own_folder", "check_the_copy"]
