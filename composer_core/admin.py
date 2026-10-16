"""The admin module: changes to your own Saved tables, written and checked for you.

It isn't brought by `from sqlglot_composer import *`. Import it by name:

    from sqlglot_composer import admin

Each function makes an Admin statement, an ordinary Statement that run(s, send=...) sends like
any other; admin.move_to_own_folder makes a list of them, sent one at a time. show_hive prints,
before an Admin statement's Hive, what it changes, what can't be undone, and what to check
first. Each refuses a table that isn't one of your Saved tables: a Table reference with no
location= is a table someone else owns. Each run of one adds an entry to the Admin log
(help(set_admin_log)).
"""

from __future__ import annotations

import copy
import json
import urllib.parse

from .clauses import Statement
from .edition import hive_text
from .refusals import refuse, refuse_what_isnt_a_dataframe
from .tables import (
    FILE_FORMATS,
    PURGE,
    ROWS_WITH_NO_DAY,
    Table,
    _ask,
    _column_definition,
    _describe,
    _same_folder,
    as_date,
    create_table,
    day_text,
    need_saved_table,
    partition_columns,
    table_node,
)
from .trees import Node

TOOLBOX_VERSION = "5.0"


# --- Pieces every Admin statement shares ------------------------------------------------------


def _admin_statement(call: str, about: list[str], ddl: Node, hive: str | None = None,
                     check=None) -> Statement:
    """An Admin statement: `ddl` is its tree, or, for an ALTER TABLE, the table it changes,
    whose Hive is `hive`. `about` is what show_hive prints first, an item to a sentence or
    two; `check`, given the result of a check, refuses it when the check fails."""
    s = Statement()
    s._ddl = ddl
    s._admin_hive = hive
    s._admin_call = call
    s._admin_about = about
    s._admin_check = check
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
    """What dropping does to the files, `whose` being "the table's" or "those days'", by the
    Table reference's purge=."""
    if t._purge:
        return (f"Can't be undone when the table itself has {PURGE} true, as purge=True in its "
                f"Table reference asks: then {whose} files go too, and nothing brings them back.")
    if t._date_partition is None:
        found_again = "A table made there again reads them back"
    else:
        found_again = ("The warehouse reads them again once repair_partitions(t) lists their "
                       "days, even in a table made there again, and an INSERT_INTO of one of "
                       "those days adds to its old rows")
    return (f"{whose[0].upper()}{whose[1:]} files stay in the table's folder, {t._location}, "
            f"unless the table itself has {PURGE} true: purge=True isn't in its Table "
            f"reference. {found_again}; only someone with access to the folder can delete "
            "them.")


def _check_purge(t: Table) -> str:
    return (f"Check first: DESCRIBE FORMATTED {_name(t)} shows, under Table Parameters, whether "
            f"{PURGE} is true in the table itself: that, not the Table reference, decides "
            "whether the files go.")


# --- Dropping ---------------------------------------------------------------------------------


def drop_table(t):
    """Drop one of your Saved tables: the DROP TABLE IF EXISTS Statement.

    The warehouse forgets the table, and every Statement that reads it fails until it is
    created again. Whether its files go too is up to the table itself: they go, every day of
    it, when the table has external.table.purge true, which purge=True in its Table reference
    asks for. create_table writes it into the table it makes; for a table made before you
    gave its Table reference purge=True, send admin.set_properties(t) first. Otherwise the
    warehouse only forgets the table: its files stay in its folder, and a table created there
    again gets their days back once repair_partitions(t) lists them, or adds to a day's old
    rows with INSERT_INTO; one with no Date partition reads them back at once. It refuses
    a table that isn't one of your Saved tables, a Table reference with no location=, such
    as job_runs, which others fill.

    The usual reason is a change to a Saved table's columns that admin.add_columns can't
    make, such as removing or renaming one: drop the table, create it again, and write its
    days again, with purge=True set in the table first, or the old days come back. IF EXISTS
    means that sending it for a table that isn't there does nothing, rather than failing.

    >>> from sqlglot_composer import admin
    >>> daily_runs = Table("mart.daily_runs", date_partition="dt",
    ...     columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
    ...     location="/data/your_team/tables", purge=True)
    >>> text = show_hive(admin.drop_table(daily_runs))
    -- admin.drop_table(mart.daily_runs) drops the table mart.daily_runs: the warehouse forgets
    -- it, and every Statement that reads it fails until it is created again.
    -- Can't be undone when the table itself has external.table.purge true, as purge=True in its
    -- Table reference asks: then the table's files go too, and nothing brings them back.
    -- Check first: DESCRIBE FORMATTED mart.daily_runs shows, under Table Parameters, whether
    -- external.table.purge is true in the table itself: that, not the Table reference, decides
    -- whether the files go.
    DROP TABLE IF EXISTS mart.daily_runs;
    """
    t = need_saved_table(t, "admin.drop_table(...)")
    call = f"admin.drop_table({t._name})"
    about = [f"{call} drops the table {t._name}: the warehouse forgets it, and every Statement "
             "that reads it fails until it is created again.",
             _purge_note(t, "the table's"), _check_purge(t)]
    return _admin_statement(call, about, Node("Drop", target=table_node(t._name)))


def drop_days(t, before):
    """Drop a Saved table's days before a given day: an ALTER TABLE Statement.

    Each day of the table before `before`, a datetime.date or a day written as the Table
    reference writes days, goes: every row of it, so no Statement reads it again. It is how a
    Saved table keeps only so many days, and does the job TRUNCATE can't: Hive refuses TRUNCATE
    on an external table, a table whose files are in a folder you give, and every table
    create_table makes is one. The days' files go too when the table has external.table.purge
    true, which purge=True in its Table reference asks for (help(admin.drop_table)); otherwise
    they stay in the table's folder. It refuses a table with no Date partition, and one that
    isn't one of your Saved tables.

    Hive takes a comparison such as dt < '2025-01-01' in DROP PARTITION, so one Statement drops
    them all. Spark takes only = there, one day at a time, so Spark refuses this Statement: if
    Spark rather than Hive runs your tables, ask whoever looks after them. The Example
    database, which is never written to, doesn't run it either.

    >>> from sqlglot_composer import admin
    >>> daily_runs = Table("mart.daily_runs", date_partition="dt",
    ...     columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
    ...     location="/data/your_team/tables", purge=True)
    >>> text = show_hive(admin.drop_days(daily_runs, before="2025-01-01"))
    -- admin.drop_days(mart.daily_runs, before="2025-01-01") drops each day of mart.daily_runs
    -- before 2025-01-01, every row of it, so no Statement reads it again.
    -- Can't be undone when the table itself has external.table.purge true, as purge=True in its
    -- Table reference asks: then those days' files go too, and nothing brings them back.
    -- Check first: SHOW PARTITIONS mart.daily_runs lists its days: the ones before 2025-01-01
    -- go.
    ALTER TABLE mart.daily_runs DROP IF EXISTS PARTITION (dt < '2025-01-01');
    """
    t = need_saved_table(t, "admin.drop_days(...)")
    day_column = t._date_partition
    if day_column is None:
        refuse(
            what=f"admin.drop_days(...) was given {t._name}, whose Table reference has no Date "
            "partition.",
            why="It drops whole days, and a table with no Date partition keeps none.",
            fix=f"To keep fewer rows, write the table again with INSERT_OVERWRITE({t._alias}), "
            "which replaces all its rows with the ones its Statement gives. To empty it, drop "
            f"it with admin.drop_table({t._alias}) and create it again, after "
            f"admin.set_properties({t._alias}) with purge=True in its Table reference, so its "
            "files go too.",
            error=ValueError,
        )
    day = as_date(before, t._column(day_column), "admin.drop_days(...)")
    text = day_text(day, t._date_format)
    call = f"admin.drop_days({t._name}, before={json.dumps(text)})"
    earlier = Node("LT", this=Node("Column", name=day_column),
                   expression=Node("Literal", this=text, is_string=True))
    hive = f"ALTER TABLE {_name(t)} DROP IF EXISTS PARTITION ({hive_text(earlier)})"
    about = [f"{call} drops each day of {t._name} before {text}, every row of it, so no "
             "Statement reads it again.",
             _purge_note(t, "those days'"),
             f"Check first: SHOW PARTITIONS {_name(t)} lists its days: the ones before {text} "
             "go."]
    return _admin_statement(call, about, table_node(t._name), hive)


# --- Adding columns ---------------------------------------------------------------------------


def add_columns(t, send):
    """Add the new columns of a Saved table's Table reference to the table itself.

    It sends DESCRIBE through your `send` as it is made, and adds each column of the Table
    reference that the table doesn't have yet. So you add a column by adding its line to the
    Table reference first, after the table's other columns (its Date partition's line may
    stay last, as Partitions aren't among them): Hive adds new columns after the table's own,
    and a write fills a table's columns in their order. Then run the Statement it gives, with
    the same send. The rows already in the table read NULL in a new column until their day is
    written again. For a table with a Date partition it writes CASCADE: each day already there
    gets the new columns too. Without it, each of those days would keep its old list of
    columns, and a day written again would lose the new columns' values. Spark refuses
    CASCADE, so if Spark rather than Hive runs your tables, ask whoever looks after them first.

    It refuses a table that isn't one of your Saved tables, a Table reference with no new
    column, a new column that isn't after the table's own, and a new Partition, which a table
    can't gain: create a new table with it, and copy the days in.

    >>> import pandas as pd
    >>> from sqlglot_composer import admin
    >>> def send_at_work(hive):  # the warehouse's answer to DESCRIBE mart.daily_runs
    ...     return pd.DataFrame([
    ...         ("job_id", "bigint", ""), ("runs", "bigint", ""),
    ...         ("# Partition Information", None, None), ("dt", "string", ""),
    ...     ], columns=["col_name", "data_type", "comment"])
    >>> daily_runs = Table("mart.daily_runs", date_partition="dt",
    ...     columns={"job_id": "bigint", "runs": "bigint", "fails": "bigint", "dt": "string"},
    ...     location="/data/your_team/tables")
    >>> text = show_hive(admin.add_columns(daily_runs, send=send_at_work))
    -- admin.add_columns(mart.daily_runs, send=...) adds the column fails to mart.daily_runs,
    -- after its other columns. The rows already there read NULL in it until their day is written
    -- again.
    -- CASCADE adds it to each day already in the table too, so a day written again keeps its
    -- values.
    -- Hard to undo: Hive drops a column only when every other column is listed again by hand,
    -- with ALTER TABLE ... REPLACE COLUMNS.
    -- Check first: DESCRIBE mart.daily_runs lists the table's columns now.
    ALTER TABLE mart.daily_runs ADD COLUMNS (
      fails BIGINT
    ) CASCADE;
    """
    t = need_saved_table(t, "admin.add_columns(...)")
    call = f"admin.add_columns({t._name}, send=...)"
    described = _describe(t._name, send, "admin.add_columns(...)")
    new = _new_columns(t, described.columns, call)
    definitions = [hive_text(_column_definition(t, column, call)) for column in new]
    hive = f"ALTER TABLE {_name(t)} ADD COLUMNS {_listed(definitions)}"
    named, them, its = (
        f"the columns {', '.join(new[:-1])} and {new[-1]}", "them", "their") if len(new) > 1 else (
        f"the column {new[0]}", "it", "its")
    about = [f"{call} adds {named} to {t._name}, after its other columns. The rows already "
             f"there read NULL in {them} until their day is written again."]
    if t._date_partition is not None:
        hive += " CASCADE"
        about.append(f"CASCADE adds {them} to each day already in the table too, so a day "
                     f"written again keeps {its} values.")
    about += ["Hard to undo: Hive drops a column only when every other column is listed again "
              "by hand, with ALTER TABLE ... REPLACE COLUMNS.",
              f"Check first: DESCRIBE {_name(t)} lists the table's columns now."]
    return _admin_statement(call, about, table_node(t._name), hive)


def _new_columns(t: Table, columns: dict, call: str) -> list[str]:
    """The Table reference's columns the table doesn't have, refused where they can't be
    added: none, a Partition, one without a type, or one before a column the table has."""
    if not columns:
        refuse(
            what=f"{call}: DESCRIBE listed no columns for {t._name}.",
            why="It adds the Table reference's columns that the table doesn't have, and can't "
            "tell which those are.",
            fix="Check the table's name, and that send returns what DESCRIBE prints.",
            error=ValueError,
        )
    partitions = partition_columns(t)
    missing = [column for column in partitions if column not in columns]
    if missing:
        refuse(
            what=f"{call}: {missing[0]} is a Partition in the Table reference, but not in the "
            "table.",
            why="A table can't gain a Partition: each Partition is a folder, and the table's "
            "files are already laid out without it.",
            fix="Create a new table with it, and write its days into it again; or, if the "
            "table's Partition has another name, correct the Table reference.",
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
            fix=f'Give it its Hive type, such as {json.dumps(untyped[0])}: "string".',
            error=ValueError,
        )
    return new


# --- Table properties -------------------------------------------------------------------------


def set_properties(t):
    """Set a Saved table's properties as its Table reference gives them.

    It sets the table's properties to its Table reference's: purge= as external.table.purge,
    compression= and properties=. Change the Table reference, then send this, and
    check_table_reference finds the two alike again. Properties the Table reference doesn't
    give stay as they are, and so do the rows. A compression applies to the files written
    from then on; the files already there keep theirs. It refuses a table that isn't one of
    your Saved tables, and a Table reference that gives none of the three.

    >>> from sqlglot_composer import admin
    >>> daily_runs = Table("mart.daily_runs", date_partition="dt",
    ...     columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
    ...     location="/data/your_team/tables", purge=True)
    >>> text = show_hive(admin.set_properties(daily_runs))
    -- admin.set_properties(mart.daily_runs) sets 1 table property of mart.daily_runs, as its
    -- Table reference says. Its other properties, and its rows, stay as they are.
    -- With external.table.purge true, dropping the table or its days deletes their files too,
    -- from now on.
    -- Can be undone: change purge=, compression= or properties= in the Table reference back to
    -- what the table had, and send this again.
    -- Check first: DESCRIBE FORMATTED mart.daily_runs lists the table's properties now, under
    -- Table Parameters.
    ALTER TABLE mart.daily_runs SET TBLPROPERTIES (
      'external.table.purge'='true'
    );
    """
    t = need_saved_table(t, "admin.set_properties(...)")
    call = f"admin.set_properties({t._name})"
    pairs = [] if t._purge is None else [(PURGE, "true" if t._purge else "false")]
    compression = FILE_FORMATS[t._stored_as][0]
    if t._compression is not None:
        pairs.append((compression, t._compression))
    pairs += list(t._properties.items())
    if not pairs:
        refuse(
            what=f"{call}: its Table reference gives no purge=, compression= or properties=.",
            why="It sets the table's properties to what its Table reference gives.",
            fix="Add purge=, compression= or properties= to its Table(...) call, such as "
            "purge=True, then call it again.",
            error=ValueError,
        )
    hive = _set_tblproperties(t, pairs)
    count = f"{len(pairs)} table propert{'y' if len(pairs) == 1 else 'ies'}"
    about = [f"{call} sets {count} of {t._name}, as its Table reference says. Its other "
             "properties, and its rows, stay as they are."]
    if t._purge is not None:
        about.append(f"With {PURGE} true, dropping the table or its days deletes their files "
                     "too, from now on." if t._purge else
                     f"With {PURGE} false, dropping the table or its days leaves their files "
                     "in its folder, from now on.")
    if t._compression is not None:
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


def move_to_own_folder(t, send):
    """Move a Saved table to a folder of its own: a list of Statements to run.

    A Saved table belongs in its own folder, under its Table reference's location=: in a
    folder it shares, two tables read each other's files, and an INSERT OVERWRITE of a day in
    one can delete the other's files for that day. This sends DESCRIBE FORMATTED and SHOW
    PARTITIONS through your `send` to find where the table is and which days it holds, and
    returns the Statements that move it, to send in order with run, one at a time:

    - create a copy, named like the table with _moving added, at the folder the Table
      reference gives the table, its own, stored as the Table reference says;
    - copy each day into it with INSERT OVERWRITE, one Statement for each day;
    - compare each day's rows in the two, and stop the move, before anything is dropped,
      if any day differs or is missing from the copy, such as one written since the steps
      were made;
    - set external.table.purge to false on the old table, whose folder may hold other
      tables' files, so that dropping it leaves them. A managed table, one whose files the
      warehouse keeps where it chooses, as create_table made them before 5.0, skips this
      step: its files are its own, and go with it;
    - drop the old table;
    - give the copy the table's name: its files stay at its own folder.

    So a table with two days takes seven Statements, moves[0] to moves[6]. Each can be sent
    again until the old table is dropped: if one fails, fix what it says, and send them again
    from the first. Rows with no day aren't copied, and go with the old table. The rows are
    copied as the old table reads them, so where two tables shared a day's folder, each read
    the other's rows too: check them first, or write the days again from their source
    instead. It refuses a table that isn't one of your Saved tables, one already at its own
    folder, and one that lacks a column of its Table reference. The Example database is never
    written to, so it doesn't run the steps.

    >>> import pandas as pd
    >>> from sqlglot_composer import admin
    >>> def send_at_work(hive):  # the warehouse, with mart.daily_runs in a shared folder
    ...     if hive.startswith("SHOW PARTITIONS"):
    ...         return pd.DataFrame({"partition": ["dt=2026-09-23", "dt=2026-09-24"]})
    ...     return pd.DataFrame([
    ...         ("job_id", "bigint", ""), ("runs", "bigint", ""),
    ...         ("# Partition Information", None, None), ("dt", "string", ""),
    ...         ("# Detailed Table Information", None, None),
    ...         ("Location:", "hdfs://namenode:8020/data/your_team/tables", None),
    ...         ("Table Type:", "EXTERNAL_TABLE", None),
    ...     ], columns=["col_name", "data_type", "comment"])
    >>> daily_runs = Table("mart.daily_runs", date_partition="dt",
    ...     columns={"job_id": "bigint", "runs": "bigint", "dt": "string"},
    ...     location="/data/your_team/tables")
    >>> moves = admin.move_to_own_folder(daily_runs, send=send_at_work)
    >>> len(moves)
    7
    >>> print(to_hive(moves[1]))
    INSERT OVERWRITE TABLE mart.daily_runs_moving PARTITION(dt = '2026-09-23')
    SELECT
      daily_runs.job_id,
      daily_runs.runs
    FROM mart.daily_runs AS daily_runs
    WHERE
      daily_runs.dt = '2026-09-23'

    show_hive(moves) prints every step, and at work each is sent in turn:

        for step in moves:
            run(step, send=send)
    """
    t = need_saved_table(t, "admin.move_to_own_folder(...)")
    call = f"admin.move_to_own_folder({t._name}, send=...)"
    described = _describe(t._name, send, "admin.move_to_own_folder(...)", formatted=True)
    managed = _check_movable(t, described, call)
    days, no_day = _days(t, send) if t._date_partition is not None else ([None], False)
    copy_of = copy.copy(t)
    copy_of._name, copy_of._alias = t._name + _MOVING, t._alias + _MOVING
    steps = [_create_step(t, copy_of, call, len(days), managed, no_day)]
    steps += [_copy_step(t, copy_of, day) for day in days]
    steps.append(_count_step(t, copy_of))
    if not managed:
        steps.append(_keep_files_step(t))
    steps += [_drop_step(t, managed, no_day), _rename_step(t, copy_of)]
    for number, step in enumerate(steps):
        step._admin_call = f"{call}[{number}]"
    return steps


def _check_movable(t: Table, described, call: str) -> bool:
    """Refuse a table the move can't, or needn't, move; True for a managed table."""
    location = described.details.get("location")
    if not location:
        refuse(
            what=f"{call}: DESCRIBE FORMATTED listed no Location for {t._name}.",
            why="It moves the table only when it isn't at its own folder already.",
            fix="Check that send returns everything DESCRIBE FORMATTED prints.",
            error=ValueError,
        )
    kind = (described.details.get("table type") or described.details.get("type") or "")
    managed = "MANAGED" in kind.upper()
    if not managed and t._date_partition is None and _inside(t._location, location):
        refuse(
            what=f"{call}: {t._name}'s own folder, {t._location}, is inside the folder it is "
            f"in now, {location}.",
            why="A table with no Date partition reads every file under its folder, the folders "
            "inside it too where the warehouse is set to, so the old table could read the "
            "copy's files as its own while the move runs.",
            fix="Give its Table reference a location= outside that folder, and move it there.",
            error=ValueError,
        )
    if not managed and _same_folder(location, t._location):
        refuse(
            what=f"{call}: {t._name} is at its own folder already, {location}.",
            why="There is nothing to move.",
            fix="Leave it where it is; check_table_reference(t, send=...) says whether "
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
            "check_table_reference(t, send=...) lists what differs.",
            error=ValueError,
        )
    return managed


def _inside(folder: str, other: str) -> bool:
    """Whether `folder` is inside `other`, compared without their storage's name."""
    path = urllib.parse.urlsplit(folder).path.rstrip("/")
    return path.startswith(urllib.parse.urlsplit(other).path.rstrip("/") + "/")


def _days(t: Table, send) -> tuple[list[str], bool]:
    """The days SHOW PARTITIONS lists, each once, oldest first, and whether it lists rows with
    no day, which aren't among them."""
    frame = _ask(send, f"SHOW PARTITIONS {_name(t)}", "admin.move_to_own_folder(...)")
    days, no_day = set(), False
    for text in frame.iloc[:, 0]:
        for part in str(text).split("/"):
            key, _, value = part.partition("=")
            if key != t._date_partition:
                continue
            if value == ROWS_WITH_NO_DAY:
                no_day = True
            else:
                days.add(urllib.parse.unquote(value))
    return sorted(days), no_day


def _create_step(t: Table, copy_of: Table, call: str, days: int, managed: bool,
                 no_day: bool) -> Statement:
    folder = copy_of._location
    copies = "the table's rows" if t._date_partition is None else (
        f"each of its {days} day{'' if days == 1 else 's'}")
    about = [f"{call} moves {t._name} to its own folder, {folder}. This first step creates "
             f"{copy_of._name} there; the steps after it copy {copies} into it, compare the "
             f"two, then drop {t._name} and give the copy its name. Send them in order, one at "
             "a time."]
    if no_day:
        about.append(f"The rows with no {t._date_partition}, which SHOW PARTITIONS lists as "
                     f"{ROWS_WITH_NO_DAY}, aren't copied, and go with the old table.")
    if t._partitioned_by:
        about.append(f"Each copy fills {', '.join(t._partitioned_by)} from its rows, which "
                     'needs the Session setting "dynamic_partitions": send '
                     'run(hive_settings("dynamic_partitions"), send=...) first.')
    about.append("The old table's files are dropped with it: it is managed, so its files "
                 "are its own." if managed else
                 "The old table's files stay where they are, since its folder may hold other "
                 "tables' files too: ask whoever looks after the folder before deleting any.")
    statement = create_table(copy_of, may_exist=True)
    statement._admin_about = about
    return statement


def _column(t: Table, column: str) -> Node:
    return Node("Column", name=column, table=t._alias)


def _copy_step(t: Table, copy_of: Table, day: str | None) -> Statement:
    partitions = partition_columns(t)
    columns = [column for column in t._columns if column not in partitions]
    columns += t._partitioned_by
    where, partition = None, None
    if day is not None:
        written = Node("Literal", this=day, is_string=True)
        where = Node("EQ", this=_column(t, t._date_partition), expression=written)
        partition = Node("Partition", expressions=[
            Node("EQ", this=Node("Column", name=t._date_partition), expression=written.copy()),
            *[Node("Column", name=column) for column in t._partitioned_by]])
    select = Node("Select", outputs=[_column(t, column) for column in columns],
                  source=table_node(t._name, alias=t._alias), where=where)
    tree = Node("Insert", target=table_node(copy_of._name, partition=partition), select=select,
                overwrite=True)
    about = [f"Copies {t._name}'s rows into {copy_of._name}." if day is None else
             f"Copies {t._name}'s rows on {day} into {copy_of._name}."]
    return _admin_statement("", about, tree)


def _counts(t: Table, name: str) -> Node:
    """Each day's count of rows in a table, as a Derived table named `name`."""
    counted = Node("Alias", this=Node("Count", this=Node("Star")), alias="row_count")
    source = table_node(t._name, alias=t._alias)
    if t._date_partition is None:
        select = Node("Select", outputs=[counted], source=source)
    else:
        day = _column(t, t._date_partition)
        select = Node("Select", outputs=[day, counted], source=source,
                      where=Node("Not", this=Node("Is", this=day.copy(),
                                                  expression=Node("Null"))),
                      group_by=[day.copy()])
    return Node("CTE", this=select, alias=name)


def _count_step(t: Table, copy_of: Table) -> Statement:
    """The check: each day whose rows differ between the table and its copy."""
    old, new = Node("Column", name="row_count", table="old_days"), Node(
        "Column", name="row_count", table="copied_days")
    outputs = [Node("Alias", this=old.copy(), alias="old_rows"),
               Node("Alias", this=new.copy(), alias="copied_rows")]
    on = None
    if t._date_partition is not None:
        outputs.insert(0, Node("Column", name=t._date_partition, table="old_days"))
        on = Node("EQ", this=Node("Column", name=t._date_partition, table="copied_days"),
                  expression=Node("Column", name=t._date_partition, table="old_days"))
    differs = Node("Or", this=Node("Is", this=new.copy(), expression=Node("Null")),
                   expression=Node("NEQ", this=new.copy(), expression=old.copy()))
    tree = Node("Select", derived_tables=[_counts(t, "old_days"), _counts(copy_of, "copied_days")],
                outputs=outputs, source=table_node("old_days"),
                joins=[Node("Join", how="LEFT JOIN" if on else "CROSS JOIN",
                            this=table_node("copied_days"), on=on)],
                where=differs)
    rows, differs_text = ("each day's rows", "any day differs or is missing from the copy") if (
        t._date_partition is not None) else ("the rows", "they differ")
    about = [f"Compares {rows} in {t._name} and {copy_of._name}, and stops the move, before "
             f"anything is dropped, if {differs_text}. It gives back no rows when they match."]
    return _admin_statement("", about, tree, check=_counts_match(t, copy_of))


def _counts_match(t: Table, copy_of: Table):
    """The check run hands the count step's result to: it refuses any day that differs."""
    def check(result):
        refuse_what_isnt_a_dataframe(result)
        if len(result) == 0:
            return result
        refuse(
            what=f"The move of {t._name} stopped: its copy, {copy_of._name}, doesn't hold the "
            "same number of rows" + ("" if t._date_partition is None else
                                     f" on {len(result)} day{'' if len(result) == 1 else 's'}")
            + ":\n" + result.to_string(index=False),
            why="The old table is dropped only once every day is copied whole, so nothing was "
            "dropped.",
            fix="A day whose copied_rows is empty (NaN) is missing from the copy: it was "
            "written since the steps were made, so make them again with "
            "admin.move_to_own_folder(t, send=...), and send them from the first. A day that "
            "differs: send that day's copy step again (show_hive(moves) names each step's "
            "day), then this one and the rest.",
            error=ValueError,
        )
    return check


def _keep_files_step(t: Table) -> Statement:
    hive = _set_tblproperties(t, [(PURGE, "false")])
    about = [f"Sets {PURGE} to false on {t._name}, so that dropping it next leaves the "
             "files in its folder, which other tables may read."]
    return _admin_statement("", about, table_node(t._name), hive)


def _drop_step(t: Table, managed: bool, no_day: bool) -> Statement:
    gone = ("its files go too, since it is managed" if managed else
            "its files stay in the folder it shared")
    if no_day:
        gone += ", and its rows with no day, which weren't copied, go with it"
    about = [f"Drops the old {t._name}: {gone}. Can't be undone, so send it only after the "
             "step before it, the comparison, gave back no rows."]
    return _admin_statement("", about, Node("Drop", target=table_node(t._name)))


def _rename_step(t: Table, copy_of: Table) -> Statement:
    hive = f"ALTER TABLE {_name(copy_of)} RENAME TO {_name(t)}"
    about = [f"Gives {copy_of._name} the name {t._name}. Its files stay at its own folder, "
             f"{copy_of._location}. If this step fails, send it alone again."]
    return _admin_statement("", about, table_node(copy_of._name), hive)


__all__ = ["drop_table", "drop_days", "add_columns", "set_properties", "move_to_own_folder"]
