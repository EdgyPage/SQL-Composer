"""Session settings, Hive written by hand, and the Admin log: Hive sent as you chose it.

hive_settings(...) gives the SET lines of a named set of Session settings, and
unchecked_hive(...) wraps a whole statement of Hive you wrote by hand. Neither is a Statement,
but to_hive, show_hive, run_execute and export_lineage accept them too, and run_query an
Unchecked statement. Smaller pieces of Hive written by hand sit inside a Statement:
unchecked_column(...) and unchecked_condition(...) stand for one Column or one Condition, and
unchecked_derived(...) for a Derived table. Each run of an Unchecked statement, of a Statement
holding one of those pieces, and of an Admin statement, adds an entry to the Admin log, a
Markdown file set_admin_log can move; inside a Project, it is the Project's admin/admin_log.md,
which logs its Project actions too.
"""

from __future__ import annotations

import datetime
import os
import re
import string
from collections.abc import Callable
from pathlib import Path
from types import FrameType

from . import kinds
from .conditions import Condition
from .keys import Found, Keys
from .refusals import callers_frame, in_words, refuse, warn_at_callers_line
from .tables import Column, Table, UncheckedSelect, python_text
from .trees import SIMPLE_NAME, Node
from .writing import (
    ExpressionFacts,
    SelectFacts,
    read_unchecked_expression,
    read_unchecked_select,
    with_placeholders,
)

# A time as the logs and a Project's files show it, such as 2026-10-22 09:30:00, and as a
# file's name holds it, such as 20261022-093000.
TIME_SHOWN = "%Y-%m-%d %H:%M:%S"
TIME_IN_A_NAME = "%Y%m%d-%H%M%S"


# --- Session settings ------------------------------------------------------------------------

# The sets the Toolbox ships, by name: why each one helps, and its settings. hive_settings'
# docstring says the same for each, so the two are changed together.
SHIPPED = {
    "dynamic_partitions": {
        "hive.exec.dynamic.partition": "true",
        "hive.exec.dynamic.partition.mode": "nonstrict",
    },
    "map_joins": {
        "hive.auto.convert.join": "true",
        "hive.auto.convert.join.noconditionaltask": "true",
        "hive.ignore.mapjoin.hint": "false",
    },
    "statistics_on_write": {
        "hive.stats.autogather": "true",
        "hive.stats.column.autogather": "true",
    },
    "merge_small_files": {
        "hive.merge.mapfiles": "true",
        "hive.merge.mapredfiles": "true",
        "hive.merge.tezfiles": "true",
    },
}

# What a setting's name may hold: letters, digits, dots, underscores, hyphens and colons.
_SETTING_NAME = re.compile(r"[A-Za-z0-9_.:\-]+")


class SessionSettings:
    """The SET lines of one or more named sets, made by hive_settings(...).

    >>> hive_settings("map_joins")
    <Session settings map_joins - show_hive(...) shows their SET lines>

    It isn't a Statement, but run_execute sends it, one line at a time, and show_hive shows it. Make
    one with hive_settings(...). Write the name in a type hint, to say that a function of
    yours gives back Session settings:

    >>> def settings_for_joins() -> SessionSettings:
    ...     return hive_settings("map_joins")
    >>> settings_for_joins()
    <Session settings map_joins - show_hive(...) shows their SET lines>
    """

    _kind = kinds.SETTINGS  # what it is, as kinds.py names it

    def __init__(self, names: list[str], lines: list[str]) -> None:
        self._names = names  # the sets' names, in the order given
        self._lines = lines  # each "SET name=value", without a ;

    def __repr__(self) -> str:
        return (f"<Session settings {', '.join(self._names)} - show_hive(...) shows their "
                "SET lines>")


def hive_settings(*names: str,
                  sets: dict[str, dict[str, str | int | float | bool]] | None = None
                  ) -> SessionSettings:
    """The SET lines of Session settings, by name, to send before your Statements.

    >>> print(to_hive(hive_settings("dynamic_partitions")))
    SET hive.exec.dynamic.partition=true
    SET hive.exec.dynamic.partition.mode=nonstrict

    Hive keeps a Session setting for the rest of the session, so send them first, then your
    Statements: run_execute(hive_settings(...), execute) sends each SET line through your execute,
    as a call of its own, and gives back None. They hold only while your query and execute
    share one session across their calls: if each call opens a new session, each SET is
    gone before your Statement runs. show_hive prints them, and export_lineage, passed them
    with the Statements, writes them at the foot of both its files.

    Name one or more sets. The Toolbox ships four:

    - "dynamic_partitions": hive.exec.dynamic.partition=true and
      hive.exec.dynamic.partition.mode=nonstrict. A write that fills a partition column from
      its rows' own values, as INSERT_OVERWRITE(t) does for each one partition= doesn't name,
      runs only with these on; show_hive prints them ahead of such a write.
    - "map_joins": hive.auto.convert.join=true,
      hive.auto.convert.join.noconditionaltask=true and hive.ignore.mapjoin.hint=false. Hive
      then joins a small table by copying it to every worker, which skips sorting the big one,
      and chooses this by itself from the tables' statistics; and it heeds the hint that
      JOIN(..., broadcast=True) writes, which it ignores otherwise. explain(s) shows whether
      it made one: a Map Join in the plan.
    - "statistics_on_write": hive.stats.autogather=true and hive.stats.column.autogather=true.
      Each write then gathers the statistics of the Partitions it writes, which Hive picks
      its join plans from, so they are never out of date. compute_statistics(t, partition=...)
      counts a Partition written without them.
    - "merge_small_files": hive.merge.mapfiles=true, hive.merge.mapredfiles=true and
      hive.merge.tezfiles=true. A write then merges its small files into fewer, larger ones,
      since many small files slow down every later read.

    Keep your own sets in a dict, each a name and its settings, such as
    HIVE_SETTINGS = {"nightly": {"hive.exec.parallel": True}}, and pass them as sets=: at the
    top of a notebook, or, for several notebooks of a Project to share, in a Building block
    that project.new_block("hive_sets") makes, written over its Template's code. True and
    False are written true and false.

    >>> HIVE_SETTINGS = {"nightly": {"hive.exec.parallel": True, "mapreduce.job.reduces": 8}}
    >>> text = show_hive(hive_settings("map_joins", "nightly", sets=HIVE_SETTINGS))
    -- Session settings: map_joins, nightly, sent one line at a time
    SET hive.auto.convert.join=true;
    SET hive.auto.convert.join.noconditionaltask=true;
    SET hive.ignore.mapjoin.hint=false;
    SET hive.exec.parallel=true;
    SET mapreduce.job.reduces=8;
    """
    own = _own_sets(sets)
    if not names:
        refuse(
            what="hive_settings() was given no set.",
            why="It writes the SET lines of the sets it is given, by name.",
            fix='Name one or more, such as hive_settings("dynamic_partitions").',
        )
    lines, given = [], {}
    for name in names:
        settings = _named_set(name, names, own)
        for setting, value in settings.items():
            written = _value(name, setting, value)
            if given.get(setting, written) != written:
                refuse(
                    what=f"hive_settings{_call(names)} sets {setting} to "
                    f"{given[setting]} and to {written}.",
                    why="Hive keeps the last SET of a setting, so one of the two would be "
                    "quietly lost.",
                    fix=f"Take {setting} out of one of the two sets.",
                    error=ValueError,
                )
            if setting not in given:
                given[setting] = written
                lines.append(f"SET {setting}={written}")
    return SessionSettings(list(names), lines)


def _call(names: tuple[object, ...]) -> str:
    """How hive_settings was called, for a message: ("a", "b") is ("a", "b")."""
    return "(" + ", ".join(_quoted(name) for name in names) + ")"


def _quoted(name: object) -> str:
    """A set's name as a message writes it: text in double quotes, anything else as Python
    shows it."""
    return f'"{name}"' if isinstance(name, str) else repr(name)


def _own_sets(sets: object) -> dict[object, dict[object, object]]:
    """The user's own sets, as given to sets=, each checked to be a dict of settings."""
    if sets is None:
        return {}
    example = 'HIVE_SETTINGS = {"nightly": {"hive.exec.parallel": True}}'
    if not isinstance(sets, dict):
        refuse(
            what=f"hive_settings(..., sets={sets!r}): sets= takes a dict, each set's name and "
            "its settings.",
            why="It names your own sets, so hive_settings can find one by its name.",
            fix=f"Keep them in a dict, as {example}, and pass sets=HIVE_SETTINGS.",
        )
    for name, settings in sets.items():
        if name in SHIPPED:
            refuse(
                what=f'Your sets= has a set named "{name}", which the Toolbox ships.',
                why=f'hive_settings("{name}") would be one set or the other, and you couldn\'t '
                "tell which from the call.",
                fix="Give your set a name of its own, such as "
                f'"{name}_ours".',
                error=ValueError,
            )
        if not isinstance(settings, dict):
            refuse(
                what=f'hive_settings(..., sets=...): the set "{name}" is {settings!r}, where '
                "a dict goes, each setting's name and its value.",
                why="Each set is written as one SET line per setting.",
                fix=f"Write each set as a dict, as in {example}.",
            )
        if not settings:
            refuse(
                what=f'hive_settings(..., sets=...): the set "{name}" has no settings.',
                why="There would be no SET line to send.",
                fix=f"Give it at least one, as in {example}, or take it out.",
                error=ValueError,
            )
    return sets


def _named_set(name: object, names: tuple[object, ...],
               own: dict[object, dict[object, object]]) -> dict[object, object]:
    """The settings of one set, the user's own or the Toolbox's, or a refusal naming them all."""
    if isinstance(name, str) and name in own:
        return own[name]
    if isinstance(name, str) and name in SHIPPED:
        return SHIPPED[name]
    if isinstance(name, (list, tuple)):
        refuse(
            what=f"hive_settings{_call(names)} was given a list, where the sets' names go.",
            why="It takes each set's name as text, one after the other.",
            fix="Pass the names one by one: hive_settings("
            + ", ".join(_quoted(each) for each in name) + ").",
        )
    yours = (f"and your sets= gives {', '.join(own)}" if own
             else "and no sets= of your own was given")
    refuse(
        what=f"hive_settings{_call(names)}: there is no set named {_quoted(name)}. The Toolbox "
        f"ships {', '.join(SHIPPED)}, {yours}.",
        why="It writes the SET lines of the sets it is given, by name.",
        fix="Check the spelling against the sets above. For a set of your own, keep it in a "
        'dict, as HIVE_SETTINGS = {"nightly": {"hive.exec.parallel": True}}, and pass it: '
        'hive_settings("nightly", sets=HIVE_SETTINGS).',
        error=ValueError,
    )


def _value(name: str, setting: object, value: object) -> str:
    """A setting's value as a SET line writes it, or a refusal of what can't be one."""
    where = f'hive_settings(...): the set "{name}"'
    if not isinstance(setting, str) or not _SETTING_NAME.fullmatch(setting):
        refuse(
            what=f"{where} has a setting named {setting!r}, which can't be written in a SET "
            "line.",
            why="A setting's name is written as it is, as in SET hive.exec.parallel=true, so "
            "it may hold only letters, digits, dots, underscores, hyphens and colons.",
            fix="Write the name as Hive's documentation spells it, such as "
            "hive.exec.parallel.",
            error=ValueError,
        )
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if not isinstance(value, str):
        refuse(
            what=f"{where} sets {setting} to {value!r}.",
            why="A setting's value is written as text, a number, True or False.",
            fix=f'Write it as one of those, such as "{setting}": True.',
        )
    for character, called in ((";", "';'"), ("\n", "a line break"), ("\r", "a line break")):
        if character in value:
            refuse(
                what=f"{where} sets {setting} to {value!r}, which holds {called}.",
                why="Each SET line is sent as it is written, and ; or a line break would end "
                "it early and start another command.",
                fix="Take it out of the value.",
                error=ValueError,
            )
    return value


def settings_text(settings: SessionSettings) -> str:
    """What show_hive prints for Session settings: a comment naming them, then each SET line."""
    return "\n".join([f"-- Session settings: {', '.join(settings._names)}, sent one line at a "
                      "time"] + [line + ";" for line in settings._lines])


# --- Unchecked statements --------------------------------------------------------------------


class UncheckedStatement:
    """Hive written by hand, made by unchecked_hive(...).

    >>> unchecked_hive("SELECT COUNT(*) AS runs FROM ops.job_runs")
    <Unchecked statement - show_hive(...) shows its Hive>

    It isn't a Statement, but run_query or run_execute sends it, and show_hive shows it, marked
    as unchecked. Make
    one with unchecked_hive(...). Write the name in a type hint, to say that a function of
    yours gives back an Unchecked statement:

    >>> def count_all_runs() -> UncheckedStatement:
    ...     return unchecked_hive("SELECT COUNT(*) AS runs FROM ops.job_runs")
    >>> count_all_runs()
    <Unchecked statement - show_hive(...) shows its Hive>
    """

    _kind = kinds.UNCHECKED  # what it is, as kinds.py names it

    def __init__(self, text: str) -> None:
        self._text = text  # the Hive as written, without a last ;

    def __repr__(self) -> str:
        return "<Unchecked statement - show_hive(...) shows its Hive>"


class UncheckedNote(UserWarning):
    """An Unchecked statement changes a table: the note says which admin function does it."""


def unchecked_hive(text: str) -> UncheckedStatement:
    """Hive you write by hand, to send when no Toolbox function writes it yet.

    >>> by_hand = unchecked_hive(
    ...     "SELECT COUNT(*) AS runs FROM ops.job_runs WHERE dt = '2026-09-24'")
    >>> text = show_hive(by_hand)
    -- Unchecked statement, written by hand: no Guard, Warning or Load limit looked inside
    SELECT COUNT(*) AS runs FROM ops.job_runs WHERE dt = '2026-09-24';

    You send it with the call that suits it: run_query(by_hand, query) for Hive that gives back
    rows, such as SELECT or SHOW, which come back as a DataFrame; run_execute(by_hand, execute)
    for Hive that changes something, such as ALTER or INSERT, which gives back nothing.

    No Guard, Warning or Load limit looks inside it: the Toolbox sends the text as you wrote
    it, dropping a ; you end it with, and can't tell whether it gives the right answer. Use it for
    the one statement you need now, and keep using the clause functions for the rest. show_hive
    marks it, export_lineage draws it as one step it can't see inside, and each run of it adds
    an entry to the Admin log (help(set_admin_log) says where), whose Unchecked statements are
    the list of what the Toolbox should learn to write next.

    Text that starts DROP, ALTER or TRUNCATE gets a note at your line, naming the admin
    function that does the same job with its checks, where one does. For example, Hive refuses
    TRUNCATE on an external table (one whose files stay where you put them), and every Saved
    table of yours is one; admin.drop_partitions does that job.

    Write one command in each: send several as several unchecked_hive(...), one after the
    other. When the last line ends in a -- comment, show_hive puts the ; on a line of its own,
    since after the comment it would be part of it.

    A Table reference's text drops into the Hive you write, in an f-string, so the names are
    spelt as the Table reference spells them. A table's text is its name as FROM writes it,
    ops.jobs AS jobs, for after FROM or JOIN; DESCRIBE and SHOW PARTITIONS take the name
    alone, ops.jobs, which you write yourself. A column's is jobs.job_id, not ops.jobs.job_id:
    Hive names a column by its table's name after AS, and refuses a three-part name in a
    SELECT. In a Project, from references import ops gives the table as ops.jobs and the
    column as ops.jobs.job_id, whose texts are the same. A table alone on a cell's last line
    shows its repr instead, its name and its columns. Below, jobs is the Example database's:

    >>> by_hand = unchecked_hive(f"SELECT {jobs.job_id}, {jobs.job_name} FROM {jobs}")
    >>> text = show_hive(by_hand)
    -- Unchecked statement, written by hand: no Guard, Warning or Load limit looked inside
    SELECT jobs.job_id, jobs.job_name FROM ops.jobs AS jobs;
    >>> run_query(by_hand, example_database.query)
       job_id      job_name
    0       1  nightly_load
    1       2  invoice_sync
    2       3  report_build
    3       4    cache_warm
    """
    if not isinstance(text, str):
        refuse(
            what=f"unchecked_hive was given {text!r}, which isn't Hive text.",
            why="It sends the Hive you write by hand, as you wrote it.",
            fix='Write the Hive as a string: unchecked_hive("ALTER TABLE ..."). To send a '
            "Statement, pass it to run_query(...) or run_execute(...) itself.",
            given=text, call="unchecked_hive",
        )
    written = text.strip().rstrip(";").rstrip()
    if not written:
        refuse(
            what=f"unchecked_hive({text!r}) has no Hive in it.",
            why="There would be nothing to send.",
            fix='Write the Hive to send, as in unchecked_hive("ALTER TABLE ...").',
            error=ValueError,
        )
    _note_a_change(written)
    return UncheckedStatement(written)


def unchecked_text(unchecked: UncheckedStatement) -> str:
    """What show_hive prints for an Unchecked statement: a comment marking it, then its Hive."""
    said = SAID.sub(lambda found: found.group() if found.group().startswith("--") else "''",
                     unchecked._text)
    # After a comment on the last line, a ; would be part of the comment.
    end = "\n;" if "--" in said.splitlines()[-1] else ";"
    return f"{UNCHECKED_MARK}\n{unchecked._text}{end}"


# The comment show_hive heads an Unchecked statement with, in a dry run too.
UNCHECKED_MARK = ("-- Unchecked statement, written by hand: no Guard, Warning or Load limit "
                  "looked inside")


# A string in quotes, a name in backticks, or a comment: what Hive text says, as opposed to
# what it does. Whichever starts first wins, as when Hive reads it.
SAID = re.compile(r"""'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*"|`(?:[^`]|``)*`|--[^\n]*""")


def _what_it_does(text: str) -> str:
    """The text in capitals with its strings and comments blanked out, and names in backticks
    kept without them, so a keyword is found only where it is one."""
    def blank(found: re.Match[str]) -> str:
        said = found.group()
        if said.startswith("`"):
            return said[1:-1].replace("``", "`")
        return "" if said.startswith("--") else "''"
    return SAID.sub(blank, text).upper()


# The admin function that does each job, as the note writes its call, and what the text that
# does it by hand starts with, after ALTER TABLE <name>.
_ALTERED_BY = (
    (r"\bDROP\s+(IF\s+EXISTS\s+)?PARTITION\b", "admin.drop_partitions(t, where=...)"),
    (r"\bADD\s+COLUMNS\b", "admin.add_columns(t, query=...)"),
    (r"\bSET\s+TBLPROPERTIES\b", "admin.set_properties(t)"),
    (r"\bSET\s+LOCATION\b", "admin.move_to_own_folder(t, query=...)"),
)


def _note_a_change(text: str) -> None:
    """Note, at the user's line, text that drops, alters or truncates, naming the admin
    function that does that job checked, where one does."""
    does = _what_it_does(text)
    words = re.findall(r"[A-Z_]+", does)
    command, then = (words + ["", ""])[:2]
    if command == "TRUNCATE":
        note = ("This Unchecked statement truncates a table. Hive refuses TRUNCATE on an "
                "external table (one whose files stay where you put them), and every Saved "
                "table of yours is one. admin.drop_partitions(t, where=...) drops a Saved "
                "table's Partitions with its checks, and writing a Partition again with "
                "INSERT_OVERWRITE "
                "replaces it.")
    elif command in ("DROP", "ALTER"):
        function = None
        if command == "DROP" and then == "TABLE":
            function = "admin.drop_table(t)"
        elif command == "ALTER" and then == "TABLE":
            function = next((call for pattern, call in _ALTERED_BY
                             if re.search(pattern, does)), None)
        verb = "drops" if command == "DROP" else "alters"
        if function is not None:
            note = (f"This Unchecked statement {verb} a table. {function} does the same job "
                    "with its checks: it refuses a table that isn't one of your Saved tables, "
                    "and says first what it changes and what can't be undone.")
        else:
            note = (f"This Unchecked statement {verb} something, and no admin function does "
                    "that job yet. It runs as you wrote it, and the Admin log keeps it as "
                    "something the Toolbox should learn to write.")
    else:
        return
    warn_at_callers_line(note, UncheckedNote)


# --- Unchecked expressions and Unchecked derived tables ----------------------------------------


def unchecked_column(text: str, /, **columns: Column) -> Column:
    """Hive you write by hand for one column that no Toolbox function writes yet.

    >>> quarter_hours = unchecked_column("{minutes} DIV 15", minutes=job_runs.duration_mins)
    >>> runs = statement(
    ...     SELECT(job_runs.run_id, job_runs.duration_mins, AS(quarter_hours, "quarter_hours")),
    ...     FROM(job_runs),
    ...     WHERE(equals(job_runs.dt, "2026-09-24")),
    ... )
    >>> print(to_hive(runs))
    SELECT
      job_runs.run_id,
      job_runs.duration_mins,
      job_runs.duration_mins DIV 15 AS quarter_hours
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt = '2026-09-24'
    >>> run_query(runs, example_database.query)
       run_id  duration_mins  quarter_hours
    0     101             10              0
    1     102             20              1
    2     103             30              2
    3     104             40              2

    Hive's DIV divides and drops what is left over, which no Toolbox function writes yet.
    Write each column the text reads as a placeholder, its own name in braces, such as
    {minutes}, and pass the column itself by that name, as minutes=job_runs.duration_mins
    above: the Toolbox fills each placeholder with the column's Hive, as str.format does, so
    Lineage traces the text to its real columns and statement(...) checks they are columns of
    the tables it reads. A brace you mean as a brace is written twice, as in
    "regexp_extract({job_name}, '[a-z]{{2}}', 0)". A column passed as a calculation, such as
    job_runs.duration_mins + 1, is put in round brackets.

    It gives back a Column, used like any other: give it a name with AS. For a condition, in
    WHERE, HAVING or ON=, use unchecked_condition(...). Text that adds rows up, such as
    percentile({minutes}, 0.5), is treated as count_rows() is: it needs GROUP_BY for the other
    columns. The Hive is written as sqlglot reads your text, so it may come out in capitals,
    with an argument left out that means the same, as hive_function's does, or in Hive's own
    words for what Hive has no word for: {job_name} ILIKE 'a%' becomes LOWER(...) LIKE
    LOWER('a%').

    It refuses text that, its placeholders filled, doesn't read as one Hive expression, or that
    sqlglot reads but can't write back as Hive, such as braces not doubled, which it reads as
    a struct; text that names a column itself rather than through a placeholder, saying how to
    write it; a placeholder with no column passed, or a column passed that no placeholder
    names; and text that reads a table of its own, as a sub-query does, which
    unchecked_derived(...) is for.

    No Guard, Warning or Load limit looks inside the text, though they check the rest of the
    Statement as ever, and where one can't tell what the text does, it says so in a Warning.
    Lineage marks it with the same badge as an Unchecked statement, and each run of a Statement
    holding one adds an entry to the Admin log (help(set_admin_log)). Like unchecked_hive, each
    one marks something the Toolbox should learn to write: a search for unchecked_ finds them
    all. Where a Toolbox function does the job, as hive_function does for a function call, use
    that instead: the Toolbox checks it.
    """
    tree = _unchecked_tree("unchecked_column", text, columns)
    because = next((column._not_adding_up_because for column in columns.values()
                    if not column._adds_up), None)
    return Column(tree, adds_up=because is None, not_adding_up_because=because)


def unchecked_condition(text: str, /, **columns: Column) -> Condition:
    """Hive you write by hand for one condition that no Toolbox function writes yet.

    >>> failing = unchecked_condition("{status} RLIKE '^FAIL'", status=job_runs.status)
    >>> print(to_hive(statement(
    ...     SELECT(job_runs.run_id),
    ...     FROM(job_runs),
    ...     WHERE(equals(job_runs.dt, "2026-09-24"), failing),
    ... )))
    SELECT
      job_runs.run_id
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt = '2026-09-24' AND job_runs.status RLIKE '^FAIL'

    The Example database can't run this one: its executor has no RLIKE, which Hive has. A
    condition it can run, such as unchecked_condition("{job_name} LIKE '%sync'",
    job_name=jobs.job_name), runs on it as on Hive.

    It gives back a Condition, for WHERE, HAVING or ON=, and for all_of(...) and any_of(...).
    Its text is written as unchecked_column's is: each column it reads as a placeholder in
    braces, such as {status}, with the column itself passed by that name, a brace you mean
    doubled, and the same refusals; help(unchecked_column) says more. The Toolbox doesn't check
    that the text is a condition, one that is true or false for each row: Hive refuses one
    that isn't when it runs.

    The Guards and Load limits check the rest of the Statement, and say so where they can't
    tell what the text does. A read of a partitioned table whose partition columns are
    filtered only in an Unchecked condition gets a Warning rather than the Load limit's refusal,
    since the text may filter them or not: check that it does, and add reads_all_partitions=True
    to the read to silence it, which there says you have checked it; or filter them with a
    condition function too. A WHERE that reads a LEFT_JOIN's table only inside one gets a
    Warning in place of the Guard's refusal, for the same reason.
    """
    return Condition(_unchecked_tree("unchecked_condition", text, columns))


def _unchecked_tree(call: str, text: object, columns: dict[str, object]) -> Node:
    """An Unchecked expression's Node, once its text and columns are checked. `call` is the
    function it is made by, unchecked_column or unchecked_condition."""
    written = _hive_written(call, text)
    names = _placeholders(call, written)
    _check_columns(call, written, names, columns)
    stand_ins = [f"unchecked_placeholder_{number}" for number in range(len(names))]
    filled = written.format(**dict(zip(names, stand_ins)))
    facts = read_unchecked_expression(filled, stand_ins)
    _check_expression(call, written, facts)
    _check_columns_named(call, written, facts, filled, dict(zip(stand_ins, names)), columns)
    missing = [name for name, stand_in in zip(names, stand_ins) if stand_in not in facts.found]
    if missing:
        refuse(
            what=f"{call}({python_text(written)}, ...) has {{{missing[0]}}} inside quotes, "
            "where Hive reads it as text.",
            why="A placeholder stands for a column, and inside quotes the column's name would "
            "be written as text, never read as the column.",
            fix=f"Write {{{missing[0]}}} outside the quotes, as in concat('run ', "
            f"{{{missing[0]}}}).",
            error=ValueError,
        )
    tree = Node("Unchecked", text=written, names=names,
                columns=[columns[name]._tree.copy() for name in names],
                aggregate=facts.aggregate, window=facts.window)
    passed = "".join(f", {name}={python_text(columns[name])}" for name in names)
    tree.meta["call"] = f"{call}({python_text(written)}{passed})"
    return tree


# A call of each function that takes Hive written by hand, for a refusal's fix to show: each
# runs on the Example database.
_EXAMPLES = {
    "unchecked_column": 'unchecked_column("upper({team})", team=jobs.team)',
    "unchecked_condition": "unchecked_condition(\"{job_name} LIKE '%sync'\", "
                           "job_name=jobs.job_name)",
    "unchecked_derived": 'unchecked_derived("teams", "SELECT DISTINCT team FROM ops.jobs", '
                         'columns={"team": "string"})',
}


def _hive_written(call: str, text: object) -> str:
    """The Hive text `call` was given, without spaces around it or a last ;, or a refusal of
    what isn't text, or holds none."""
    if not isinstance(text, str):
        refuse(
            what=f"{call} was given {text!r}, which isn't Hive text.",
            why="It is Hive you write by hand, which it keeps as you wrote it.",
            fix=f"Write the Hive as a string, as in {_EXAMPLES[call]}.",
            given=text, call=call,
        )
    written = text.strip().rstrip(";").rstrip()
    if not written:
        refuse(
            what=f"{call}({text!r}) has no Hive in it.",
            why="There would be nothing to write.",
            fix=f"Write the Hive, as in {_EXAMPLES[call]}.",
            error=ValueError,
        )
    return written


def _placeholders(call: str, text: str) -> list[str]:
    """The name of each {name} placeholder in the text, each once, in the order written; a
    refusal of braces str.format can't read, and of a placeholder with no plain name."""
    try:
        parsed = list(string.Formatter().parse(text))
    except ValueError as error:
        refuse(
            what=f"{call}({python_text(text)}, ...) has braces it can't read: {error}.",
            why="Each {name} is a placeholder for a column, so a brace on its own is read as "
            "the start or end of one.",
            fix="Write a brace you mean as a brace twice, {{ or }}, as in "
            "'[a-z]{{2}}', and name each placeholder, as in {team}.",
            error=ValueError,
        )
    for _, field, spec, conversion in parsed:
        if field is None:
            continue
        if field == "":
            refuse(
                what=f"{call}({python_text(text)}, ...): its placeholder {{}} has no name.",
                why="Each placeholder is filled with the column passed by its name.",
                fix=f"Name it, and pass the column by that name, as in {_EXAMPLES[call]}.",
            )
        if spec or conversion or not SIMPLE_NAME.fullmatch(field):
            shown = "{" + field + (f"!{conversion}" if conversion else "") + (
                f":{spec}" if spec else "") + "}"
            refuse(
                what=f"{call}({python_text(text)}, ...) has the placeholder {shown}.",
                why="A placeholder is a plain name, filled with the column passed by that name; "
                "the Toolbox writes the column's Hive itself.",
                fix="Write it as a plain name, as in {team}, and pass the column by that name. "
                "A brace you mean as a brace is written twice, {{ or }}.",
                error=ValueError,
            )
    return list(dict.fromkeys(field for _, field, _, _ in parsed if field))


def _check_columns(call: str, text: str, names: list[str], columns: dict[str, object]) -> None:
    """Refuse a placeholder with no column passed, a column passed that no placeholder names,
    and a value passed that isn't a column."""
    for name in names:
        if name not in columns:
            refuse(
                what=f"{call}({python_text(text)}) has {{{name}}}, and no {name}= was given.",
                why="Each placeholder is filled with the column passed by its name.",
                fix=f"Pass the column it stands for, as {name}=jobs.{name} if it is a column "
                "of jobs.",
            )
    for name, column in columns.items():
        if name not in names:
            refuse(
                what=f"{call}({python_text(text)}, ...) was given {name}=, which its text "
                "doesn't name.",
                why="Each column passed fills the placeholder of its name, as {"
                f"{name}}}, and Lineage would trace the text to a column it doesn't read.",
                fix=f"Write {{{name}}} where the text reads it, or leave {name}= out.",
            )
        if not isinstance(column, Column):
            refuse(
                what=f"{call}(...): {name}= is {column!r}, where a column goes.",
                why="A placeholder is filled with a column's Hive, which the Toolbox writes "
                "itself, so it can trace and check it.",
                fix=f"Pass the column itself, as {name}=jobs.team, not its name as text.",
                given=column, call=call,
            )


def _check_expression(call: str, text: str, facts: ExpressionFacts) -> None:
    """Refuse text that isn't one expression, holds a sub-query or names itself."""
    said = f"{call}({python_text(text)}, ...)"
    if facts.reads_a_table and facts.unreadable is None:
        refuse(
            what=f"{said} reads a table of its own.",
            why="An Unchecked expression stands for one column or condition of the tables "
            "the Statement reads, which the Toolbox traces; a table it reads itself would be "
            "hidden from Lineage and the Load limits.",
            fix="Write the sub-query as an Unchecked derived table, as in "
            f"{_EXAMPLES['unchecked_derived']}, which Lineage draws, and JOIN it, or "
            "SEMI_JOIN it to keep the rows with a match.",
            error=ValueError,
        )
    if facts.unreadable is not None:
        refuse(
            what=f"{said} doesn't read as one Hive expression: {facts.unreadable}.",
            why="The Toolbox reads the text, its placeholders filled, to find what it does, "
            "and the warehouse would stop the whole Statement with an error.",
            fix="Check the text: its brackets and quotes, and that it is one expression, as "
            "you would write it between commas in a SELECT.",
            error=ValueError,
        )
    if facts.count != 1:
        refuse(
            what=f"{said} holds {facts.count} expressions.",
            why=f"It stands for one {'column' if call == 'unchecked_column' else 'condition'}.",
            fix=f"Write one {call}(...) for each.",
            error=ValueError,
        )
    if facts.named:
        refuse(
            what=f"{said} gives it a name, with AS.",
            why="A column is named where SELECT shows it, so the name is checked like any "
            "other.",
            fix=f'Leave the name out of the text and name the column with AS: AS({call}(...), '
            '"team_upper").',
            error=ValueError,
        )
    _refuse_unwritable(said, facts.unwritable)


def _refuse_unwritable(said: str, unwritable: str | None) -> None:
    """Refuse Hive sqlglot reads but can't write back as Hive, saying why in its words: at the
    call, rather than at to_hive. `said` is the call, as a message writes it."""
    if unwritable is None:
        return
    refuse(
        what=f"{said}: sqlglot reads it, but can't write it back as Hive: {unwritable}.",
        why="to_hive writes every Statement's Hive through sqlglot, so it would stop there, "
        "and the warehouse never gets Hive the Toolbox can't write.",
        fix="Write it another way Hive reads. A brace sqlglot reads as a struct, as in "
        "{'k': 1}: a brace you mean as a brace is doubled, {{ or }}, and only unchecked_column "
        "and unchecked_condition take placeholders: unchecked_derived's text names its "
        "columns itself.",
        error=ValueError,
    )


def _check_columns_named(call: str, text: str, facts: ExpressionFacts, filled: str,
                         stand_ins: dict[str, str], columns: dict[str, object]) -> None:
    """Refuse text that names a column itself, rather than through a placeholder, writing
    the call as it should be: each such column a placeholder, as sqlglot writes the text, and
    the columns passed already kept. `filled` is the text with each placeholder filled with
    its stand-in, and `stand_ins` gives each stand-in's placeholder name."""
    if not facts.columns:
        return
    instead, added = with_placeholders(filled, stand_ins)
    passed = [f"{name}={python_text(columns[name])}" for name in stand_ins.values()]
    passed += [f"{name}={table or '<table>'}.{column}" for name, table, column in added]
    unknown = (", with <table> the Table reference of the table it is a column of"
               if any(not table for _, table, _ in added) else "")
    refuse(
        what=f"{call}({python_text(text)}) names {in_words(facts.columns)} itself, rather than "
        "through a placeholder.",
        why="The Toolbox can't tell which table's column text names, so Lineage couldn't trace "
        "it and a table renamed with AS would leave it pointing at the old name.",
        fix=f"Write each column it names as a placeholder, and pass the column itself: "
        f"{call}({python_text(instead)}, {', '.join(passed)}){unknown}.",
        error=ValueError,
    )


def unchecked_derived(name: str, text: str, columns: dict[str, str | None],
                      key: list[str] | None = None) -> Table:
    """A Derived table whose SELECT is Hive you write by hand, its columns declared.

    >>> steps = unchecked_derived("steps", '''
    ...     SELECT r.run_id, s AS step
    ...     FROM ops.job_runs r
    ...     LATERAL VIEW explode(split(r.status, '_')) t AS s
    ...     WHERE r.dt = '2026-09-24'
    ... ''', columns={"run_id": "bigint", "step": "string"})
    >>> print(to_hive(statement(
    ...     SELECT(steps.step, AS(count_rows(), "runs")),
    ...     FROM(steps, reads_all_partitions=True),
    ...     GROUP_BY(steps.step),
    ... )))
    WITH steps AS (
      SELECT
        r.run_id,
        s AS step
      FROM ops.job_runs AS r
      LATERAL VIEW
      EXPLODE(SPLIT(r.status, '_')) t AS s
      WHERE
        r.dt = '2026-09-24'
    )
    SELECT
      steps.step,
      COUNT(*) AS runs
    FROM steps
    GROUP BY
      steps.step

    Each run's status is split at each _ (explode(split(r.status, '_'))), and LATERAL VIEW
    gives one row for each part, named s, beside the rest of the run's row: steps has a row
    for each run and each part of its status, which no Clause function writes yet. The
    Example database can't run it, as its executor has no LATERAL VIEW; Hive can.

    It gives back a Table, read as a Derived table made by derived(...) is: its columns are
    the ones `columns` declares, each with its Hive type or None, so steps.step works and a
    column it doesn't declare is refused at once. The text is one SELECT, written at the top
    of the Hive as WITH steps AS (...), laid out as the Toolbox lays out its Hive. When sqlglot
    can tell the names of the columns the SELECT gives, they must be the ones declared. The
    text names its columns itself, with no {placeholders}: a brace in it is refused, since
    sqlglot reads it as a struct, which it can't write back as Hive.

    No Guard, Warning or Load limit looks inside the text, so it has no Key the Toolbox can
    see unless you name one: key=["run_id"] says one row has each run_id, as a GROUP BY
    run_id in its text makes it, and a Table reference's key= says. A JOIN on its Key is then
    checked as on any Derived table with one, and a write reading it isn't refused for a Key
    it can't prove. The Toolbox can't check that the text makes it so: name a Key only when
    it does. Without one, a JOIN on it warns as on any table without a Key.

    A read of it warns that the Load limit can't see whether its text filters the partition
    columns of the tables it reads, those partitioned and those the Toolbox has no Table
    reference for: check that it does, then add reads_all_partitions=True to the FROM or JOIN
    that reads it, as above, which there says you have checked it. Lineage draws it as one box
    it can't see inside, marked with the Unchecked statement's badge, over the tables its text
    reads, and each run of a Statement reading it adds an entry to the Admin log
    (help(set_admin_log)). Like unchecked_hive, it marks something the Toolbox should learn to
    write: a search for unchecked_ finds it.
    """
    if not isinstance(name, str) or not SIMPLE_NAME.fullmatch(name):
        refuse(what=f"unchecked_derived({name!r}, ...) needs a plain name.",
               why="The name is how the SQL calls it.",
               fix='Use letters, digits and _, such as unchecked_derived("steps", ...).',
               error=ValueError)
    written = _hive_written("unchecked_derived", text)
    if not isinstance(columns, dict) or not columns:
        refuse(
            what=f"unchecked_derived({name!r}, ..., columns={columns!r}) needs a dict of column "
            "names and types.",
            why="The Toolbox can't look inside the text, so the columns you declare are the "
            "ones a Statement can read from it.",
            fix='Write columns={"run_id": "bigint", "step": "string"}, with None for a type '
            "you don't know.",
            error=ValueError,
        )
    _check_key(name, key, columns)
    facts = read_unchecked_select(written)
    _check_select(name, written, facts, columns)
    table = Table(name, columns=columns)
    table._statement = UncheckedSelect(written, facts.tables)
    if key:
        table._key = list(key)
        table._keys = Keys(found=[Found(list(key), f"its key=[...] says its rows are told "
                                        f"apart by {in_words(list(key))}", "not by")],
                           lost=None)
    else:
        table._keys = Keys(found=[], lost="its Hive is written by hand in "
                           "unchecked_derived(...), which the Toolbox can't look inside")
    return table


def _check_key(name: str, key: object, columns: dict[str, str | None]) -> None:
    """Refuse a key= that isn't a list of the columns declared."""
    if key is None:
        return
    if not isinstance(key, (list, tuple)) or not key or not all(
            isinstance(column, str) for column in key):
        refuse(
            what=f"unchecked_derived({name!r}, ..., key={key!r}) needs a list of column names.",
            why="key= names the columns that tell its rows apart, as a Table reference's does.",
            fix='Write it like key=["run_id"], or leave it out.',
            given=key, call="unchecked_derived",
        )
    for column in key:
        if column not in columns:
            refuse(
                what=f"unchecked_derived({name!r}, ...): key names {column!r}, which isn't one "
                "of its columns.",
                why="Every name in key= must be a column it declares in columns={...}.",
                fix=f"Use one of: {', '.join(columns)}.",
                error=ValueError,
            )


def _check_select(name: str, text: str, facts: SelectFacts,
                  columns: dict[str, str | None]) -> None:
    """Refuse an Unchecked derived table's text that isn't one SELECT, or whose columns, where
    sqlglot can tell them, aren't the ones declared."""
    if facts.not_a_select is not None:
        refuse(
            what=f"unchecked_derived({name!r}, ...): its text isn't one SELECT: "
            f"{facts.not_a_select}.",
            why="A Derived table is the rows one SELECT gives, which the Statement that reads "
            "it reads as a table.",
            fix="Write one SELECT, with no ; inside it. A command that changes something is "
            "sent with unchecked_hive(...) instead.",
            error=ValueError,
        )
    declared = [str(column) for column in columns]
    if facts.outputs is not None and {n.lower() for n in facts.outputs} != {
            n.lower() for n in declared}:
        refuse(
            what=f"unchecked_derived({name!r}, ...) declares the columns {', '.join(declared)}, "
            f"and its SELECT gives {', '.join(facts.outputs)}.",
            why="A Statement reads the columns declared, which the warehouse would look for in "
            "the SELECT's rows.",
            fix="Declare each column the SELECT gives, under the name it gives it.",
            error=ValueError,
        )
    _refuse_unwritable(f"unchecked_derived({name!r}, ...)", facts.unwritable)


# --- The Admin log ---------------------------------------------------------------------------

# Where the Admin log is written: set by set_admin_log, None for the usual place, admin_log.md
# beside the script or notebook that runs, or in a Project, its admin/admin_log.md.
_admin_log = {"path": None}


def set_admin_log(path: str | Path | None = None) -> Path | None:
    """Set where the Admin log is written, such as "logs/admin_log.md".

    >>> set_admin_log("logs/admin_log.md").name
    'admin_log.md'
    >>> set_admin_log()  # back to the usual place

    The Admin log is a Markdown file the Toolbox adds an entry to each time run_query or
    run_execute sends an Unchecked statement, an Admin statement, or a Statement holding an
    Unchecked expression or an Unchecked derived table (unchecked_column, unchecked_condition
    or unchecked_derived), and each time compare_with_original compares such a Statement:
    when, the call, the Hive sent, the script and its git commit, and whether it worked. It
    only ever adds to the file. Its Unchecked statements and Unchecked pieces are the list of
    what the Toolbox should learn to write next.

    Left unset, the log is admin_log.md beside the script or notebook that sends it, or
    inside a Project the Project's admin/admin_log.md (help(project)). A path you give that
    isn't absolute, such as "logs/admin_log.md", starts from the folder of the
    script or notebook that calls set_admin_log. Call it at the top of each notebook or
    pipeline: a restarted kernel forgets it. It returns the path now in force, or None for the
    default.
    """
    if path is None:
        _admin_log["path"] = None
        return None
    if not isinstance(path, (str, os.PathLike)):
        refuse(
            what=f"set_admin_log({path!r}): that isn't a path.",
            why="It takes the path of the Markdown file the Admin log is written to.",
            fix='Write it like set_admin_log("admin_log.md"), or call set_admin_log() for '
            "the usual place: admin_log.md beside your script or notebook, or in a Project, "
            "its admin/admin_log.md.",
        )
    if Path(path).suffix.lower() != ".md":
        refuse(
            what=f"set_admin_log({path!r}): the Admin log is a Markdown file, so its path "
            "ends in .md.",
            why="It is written as Markdown, which reads as plain text and shows as a page.",
            fix='Write it like set_admin_log("admin_log.md"), or call set_admin_log() for '
            "the usual place: admin_log.md beside your script or notebook, or in a Project, "
            "its admin/admin_log.md.",
            error=ValueError,
        )
    path = Path(path)
    if not path.is_absolute():
        from .lineage import caller_folder, calling_file  # lineage.py imports this file

        path = caller_folder(calling_file(callers_frame())) / path
    _admin_log["path"] = path
    return path


HEADER = (
    "# Admin log\n"
    "\n"
    "Each Admin statement, Unchecked statement, Statement holding an Unchecked expression or "
    "Unchecked derived table, and Project action the Toolbox has run, oldest first. The "
    "Toolbox only ever adds to this file. Its Unchecked statements, expressions and derived "
    "tables are the list of what the Toolbox should learn to write next.\n"
)

# How much of an Unchecked statement's first line an entry's call shows.
_CALL_LENGTH = 65


def unchecked_call(unchecked: UncheckedStatement) -> str:
    """How an entry names an Unchecked statement's call: its first line, cut short."""
    whole = unchecked._text
    first = whole.splitlines()[0][:_CALL_LENGTH]
    quoted = '"' + first.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return f"unchecked_hive({quoted}{' ...' if first != whole else ''})"


def logged_run(kind: str, call: str, hive: str,
               warehouse_call: Callable[[str], object]) -> object:
    """Send `hive`, then add its entry to the Admin log: worked, or failed with its error,
    which is raised again once the entry is written. `kind` is "Unchecked statement",
    "Admin statement", or a Statement with an Unchecked expression or derived table, as
    "Statement with an Unchecked expression"."""
    frame = callers_frame()
    try:
        result = warehouse_call(hive)
    except Exception as error:
        _append(kind, call, hive, frame,
                f"failed, with {type(error).__name__}: {' '.join(str(error).split())}")
        raise
    _append(kind, call, hive, frame, "worked")
    return result


def _append(kind: str, call: str, hive: str, frame: FrameType, result: str) -> None:
    """Add one entry to the end of the Admin log, writing its heading first if it is new."""
    from .lineage import caller_folder, calling_file  # it imports this file
    from .project import project_folder, project_log  # it imports this file

    caller = calling_file(frame)
    # The Project the script is in, or else the one Python is working in.
    project = project_folder(caller_folder(caller)) or project_folder(Path.cwd())
    path = _admin_log["path"] or (project_log(project) if project is not None
                                  else caller_folder(caller) / "admin_log.md")
    tables = tables_named(hive)
    fence = "`" * max(3, _longest_backticks(hive) + 1)
    lines = ["", f"## {now().strftime(TIME_SHOWN)}, {kind}", "", f"- Call: {inline_code(call)}"]
    if tables:
        lines.append(f"- Tables named: {', '.join(tables)}")
    lines += [script_line(caller), f"- Result: {result}", "", f"{fence}sql", hive, fence, ""]
    write_entry(path, lines)


def script_line(caller: Path | None) -> str:
    """An entry's Script line: the script or notebook that ran, and its git commit."""
    from .lineage import caller_folder, scripts_commit  # it imports this file

    script = caller.name if caller is not None else "a notebook"
    return f"- Script: {script}, at commit {scripts_commit(caller_folder(caller))}"


def write_entry(path: Path, lines: list[str]) -> None:
    """Add an entry's lines to the end of the Admin log at `path`, its heading first if new."""
    path.parent.mkdir(parents=True, exist_ok=True)
    new = not path.exists()
    with open(path, "a", encoding="utf-8", newline="\n") as log:
        if new:
            log.write(HEADER)
        log.write("\n".join(lines))


def _longest_backticks(text: str) -> int:
    """The length of the longest run of backticks in the text, 0 when it has none."""
    return max((len(run) for run in re.findall(r"`+", text)), default=0)


def inline_code(text: str) -> str:
    """Markdown inline code, with a fence that survives backticks inside it."""
    fence = "`" * (_longest_backticks(text) + 1)
    pad = " " if text.startswith("`") or text.endswith("`") else ""
    return f"{fence}{pad}{text}{pad}{fence}"


def now() -> datetime.datetime:
    """The time now: an Admin log entry's, a Project action's and an exported lineage's, from
    this one clock, which the page tools and tests pin by patching unchecked.now."""
    return datetime.datetime.now()


# The words after which Hive text names a table: FROM and JOIN read one; INSERT, and ALTER,
# CREATE, DROP, TRUNCATE, MSCK REPAIR or ANALYZE TABLE, write or change one.
_READS = re.compile(r"\b(?:FROM|JOIN)\s+([\w.]+)")
_WRITES = re.compile(r"\b(?:INSERT\s+(?:OVERWRITE|INTO)(?:\s+TABLE)?"
                     r"|(?:ALTER|CREATE(?:\s+EXTERNAL)?|DROP|TRUNCATE|MSCK\s+REPAIR|ANALYZE)"
                     r"\s+TABLE(?:\s+IF\s+(?:NOT\s+)?EXISTS)?)\s+([\w.]+)")


def tables_named(hive: str) -> list[str]:
    """The tables Hive text names, in the order it names them: each it reads or writes."""
    return list(dict.fromkeys(name for name, _ in tables_read_and_written(hive)))


def tables_read_and_written(hive: str) -> list[tuple[str, str]]:
    """Each table Hive text names, as (name, "reads" or "writes"), in order, found by the
    words before it, in small letters, as Hive keeps a table's name. A name given to a
    Derived table by WITH name AS (...) is left out, since it isn't a table."""
    does = _what_it_does(hive)
    derived = set(re.findall(r"(?:\bWITH|,)\s*(\w+)\s+AS\s*\(", does))
    found = [(match.start(), match.group(1), "reads") for match in _READS.finditer(does)]
    found += [(match.start(), match.group(1), "writes") for match in _WRITES.finditer(does)]
    return [(name.lower(), how) for _, name, how in sorted(found) if name not in derived]


__all__ = ["hive_settings", "unchecked_hive", "unchecked_column", "unchecked_condition",
           "unchecked_derived", "set_admin_log", "SessionSettings", "UncheckedStatement"]
