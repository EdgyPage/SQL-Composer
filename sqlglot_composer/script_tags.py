"""Script tags: a <PARM="NAME"/> in Hive someone else wrote, which the program that ran it
filled in before Hive read it (Toolbox 8.3).

NAME is whatever name that program gave the tag. A tag stands for a value in one table's
statements alone, so a Conversion reads past it. sqlglot can't read a bare tag, as in
WHERE dt <= <PARM="PERIOD_END"/>, so `readable_tags` writes each one in backticks first, a name
sqlglot reads as a column, and `tags_as_written` takes the backticks off again. A tag inside
quotes, as in '<PARM="PERIOD_END"/>', is part of a string, which sqlglot reads as it is.

In a converted table's logic, a bare tag's place is script_tag(TAGS["PERIOD_END"]), and a quoted
one's is tag_text(TAGS["PERIOD_END"]), a string. TAGS, in the table's Table reference, holds
what each tag stands for, a Decision answered in the decisions cell: Hive text, or a Run
value's function (Toolbox 8.4), which script_tag and tag_text call each time the Statement is
built.
"""

from __future__ import annotations

import datetime
import re
from collections.abc import Callable
from dataclasses import dataclass, field

from . import _four_part_message as four_part_message
from .refusals import RunValueWarning, callers_frame, refuse, warn_at_callers_line
from .tables import Column, Table, literal, python_text
from .trees import Node
from .writing import hive_text, tag_value_problem

# A Script tag, its NAME any text but a quote, a backtick or a line break.
TAG = re.compile(r'<PARM="([^"`\n]+)"/>')
# A tag as `readable_tags` writes a bare one for sqlglot: in backticks.
TAG_IN_BACKTICKS = re.compile(f"`({TAG.pattern})`")
# Text that starts as a tag does, <PARM as a word in any case: where it isn't a whole TAG, it
# is a shape no Conversion reads.
TAG_START = re.compile(r"<PARM\b", re.IGNORECASE)
# The kind of node script_tag makes.
SCRIPT_TAG = "ScriptTag"
# How each kind of quote, and each comment, opens and closes.
_CLOSING = {"'": "'", '"': '"', "`": "`", "--": "\n", "/*": "*/"}
_COMMENTS = ("--", "/*")


@dataclass
class FoundTag:
    """One Script tag in Hive text: its NAME, where it starts and ends, its line, counted from
    1, and whether it sits inside quotes, part of a string."""

    name: str
    start: int
    end: int
    line: int
    quoted: bool


def tags_in(text: str) -> list[FoundTag]:
    """Each Script tag in Hive text, in order, but those in a comment or already in backticks.
    A tag's own quotes are passed over: only those around it count."""
    matches = list(TAG.finditer(text))
    inside = _inside_at(_tags_masked(text, matches), [match.start() for match in matches])
    found = []
    for match, around in zip(matches, inside, strict=True):
        if around in ("'", '"', None):
            line = text.count("\n", 0, match.start()) + 1
            found.append(FoundTag(match.group(1), match.start(), match.end(), line,
                                  quoted=around is not None))
    return found


def _tags_masked(text: str, matches: list[re.Match[str]]) -> str:
    """`text` with each tag in `matches` written over with x's, so its own quotes open
    nothing."""
    pieces, at = [], 0
    for match in matches:
        pieces += [text[at:match.start()], "x" * len(match.group())]
        at = match.end()
    return "".join(pieces) + text[at:]


def _inside_at(masked: str, starts: list[int]) -> list[str | None]:
    """What each start in `masked`, in order, sits inside: a quote, ', " or `, a comment, --
    or /*, or None, outside them all. Inside quotes, a backslash keeps the next character from
    closing them."""
    inside: str | None = None
    at, kinds = 0, []
    for start in starts:
        while at < start:
            if inside is None:
                inside = _opening_at(masked, at)
                at += len(inside) if inside is not None else 1
            elif inside in ("'", '"') and masked[at] == "\\":
                at += 2
            elif masked.startswith(_CLOSING[inside], at):
                at += len(_CLOSING[inside])
                inside = None
            else:
                at += 1
        kinds.append(inside)
    return kinds


def _opening_at(masked: str, at: int) -> str | None:
    """The quote or comment that opens at `at` in `masked`, or None when none does."""
    for mark in _CLOSING:
        if masked.startswith(mark, at):
            return mark
    return None


def misshapen_tag_line(text: str) -> int | None:
    """The line, counted from 1, of the first text in `text` outside a comment that starts as
    a Script tag does, <PARM in any case, but isn't one; None when there is none."""
    whole = list(TAG.finditer(text))
    masked = _tags_masked(text, whole)
    starts = [match.start() for match in TAG_START.finditer(masked)]
    for start, around in zip(starts, _inside_at(masked, starts), strict=True):
        if around not in _COMMENTS:
            return text.count("\n", 0, start) + 1
    return None


def in_backticks(tag: str) -> str:
    """A whole Script tag's text written in backticks, a name sqlglot reads as a column."""
    return f"`{tag}`"


def readable_tags(text: str) -> str:
    """Hive text with each bare Script tag in backticks, so sqlglot reads it as a name where a
    value goes; a tag inside quotes, or in a comment, is left as it is."""
    for tag in reversed([one for one in tags_in(text) if not one.quoted]):
        text = text[:tag.start] + in_backticks(text[tag.start:tag.end]) + text[tag.end:]
    return text


def tags_as_written(text: str) -> str:
    """Hive text with each Script tag `readable_tags` put in backticks written bare again, as
    the script wrote it."""
    return TAG_IN_BACKTICKS.sub(r"\1", text)


def tag_pieces(text: str) -> list[tuple[str, str | None]]:
    """`text` cut at each Script tag, bare or in backticks: each piece with the tag's NAME, or
    None for the text between tags; no piece is empty."""
    pieces: list[tuple[str, str | None]] = []
    at = 0
    for match in re.finditer(f"`?{TAG.pattern}`?", text):
        if match.start() > at:
            pieces.append((text[at:match.start()], None))
        pieces.append((match.group(), match.group(1)))
        at = match.end()
    if at < len(text):
        pieces.append((text[at:], None))
    return pieces


def tag_name(text: str) -> str | None:
    """The NAME of a Script tag, when `text` is one whole tag, such as a name sqlglot read in
    backticks; None for any other text."""
    found = TAG.fullmatch(text)
    return found.group(1) if found else None


# The kinds of Node a value is built of: values, and sums of them in brackets.
_VALUE_KINDS = {"Literal", "Null", "Boolean", SCRIPT_TAG, "Paren", "Add", "Sub", "Mul"}
# The Hive functions that move a day by a number of days, whose call on values is a value.
_DAYS_MOVED = ("date_add", "date_sub")


def is_built_of_values(value: object) -> bool:
    """Whether `value` is a Column built of values alone: Script tags, literals, and sums or
    date_add or date_sub of them, such as date_sub(PERIOD_END, 14). It reads no column, so a
    condition holding a partition column to it bounds the Partitions read, as one holding it to
    a plain value does."""
    return isinstance(value, Column) and _is_built_of_values(value._tree)


def _is_built_of_values(node: Node) -> bool:
    if node.kind == "HiveFunction":
        return node.parts["name"] in _DAYS_MOVED and all(
            _is_built_of_values(arg) for arg in node.parts["args"])
    if node.kind not in _VALUE_KINDS:
        return False
    return all(_is_built_of_values(part) for part in node.parts.values()
               if isinstance(part, Node))


def script_tag(text: str) -> Column:
    """The value a Script tag stands for, written where the tag stood, as a Column.

    >>> from sqlglot_composer import example_database
    >>> runs = example_database.job_runs
    >>> TAGS = {"PERIOD_END": "'2026-09-24'"}  # the Hive the program put there, quotes and all
    >>> print(to_hive(statement(
    ...     SELECT(runs.run_id),
    ...     FROM(runs),
    ...     WHERE(at_most(runs.dt, script_tag(TAGS["PERIOD_END"]))),
    ... )))
    SELECT
      job_runs.run_id
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt <= '2026-09-24'

    A Script tag is a <PARM="NAME"/> in Hive someone else wrote, which the program that ran it
    filled in before Hive read it, such as <PARM="PERIOD_END"/>. Where a tag stood bare, a
    Conversion writes script_tag(TAGS["PERIOD_END"]): you give it the table's TAGS entry, and
    it gives back a Column, the type any value in a Statement has, as
    job_runs.duration_mins / 60 does. TAGS, in the table's Table reference, holds what each
    tag stands for: the Hive the program put there, such as '2026-09-24' with its quotes, 5,
    or '${hivevar:period_end}', a Hive variable your warehouse fills in when the query runs,
    in quotes when it holds a date; or a Run value's function, such as period_end, written in
    your Project, which script_tag calls each time the Statement is built. What it gives is
    written as Hive: a datetime.date as '2026-09-24', a number as it is, TRUE or FALSE, and
    text as the Hive it is. One that fails leaves `<period_end() failed>` in the value's
    place, with a Warning saying why, so show_hive still shows the rest; run_query and
    run_execute refuse to send it.

    You answer each tag in the convert notebook's decisions cell, under "tags", as in
    DECISIONS = {"mart_dev.daily_close": {"tags": {"PERIOD_END": "'2026-09-24'"}}}, and step
    3, project.write_decisions, writes the answer into TAGS; answering again changes it.
    Until then TAGS holds the tag itself, and the table isn't created: script_tag would write
    a bare one in backticks, `<PARM="PERIOD_END"/>`, which Hive refuses to run.

    Its text, given or given by a Run value, is one value of a kind a program puts in a tag's
    place: text or a date in quotes, a number, TRUE, FALSE, NULL or a Hive variable such as
    ${hivevar:period_end}. Anything else is refused: a column, a condition, a sum such as
    5 - 3, a function's call or a comment,
    which Hive would read with what stands beside the tag, and a date with no quotes,
    2026-09-24, which Hive reads as a subtraction. The Toolbox doesn't check
    the text inside it, but at_most(runs.dt, script_tag(...)) still filters dt, a partition
    column, as at_most(runs.dt, "2026-09-24") does.
    """
    call = f"script_tag({python_text(text)})"
    if callable(text):
        return _run_value_column(text)
    if not isinstance(text, str) or not text.strip():
        refuse(
            what=f"{call} was given {text!r}, not the Hive a Script tag stands for.",
            why="script_tag writes the text it is given where the tag stood in the original.",
            fix='Give it the table\'s TAGS entry, as in script_tag(TAGS["PERIOD_END"]).',
            given=text, call=call,
        )
    if tag_name(text) is not None:
        node = Node(SCRIPT_TAG, text=in_backticks(text))
    else:
        _check_tag_value(call, text)
        node = Node(SCRIPT_TAG, text=text)
    node.meta["call"] = call
    return Column(node)


def run_value_name(function: Callable[..., object]) -> str:
    """A Run value's function by its module and name, such as
    building_blocks.run_values.period_end."""
    return f"{function.__module__}.{function.__qualname__}"


@dataclass
class Traced:
    """What one call of a function of yours did as a Statement was built, for its lineage:
    the function by its module and name, the arguments it was given, the Script tag it
    answers, if it answers one, and each table, or partition column, the Toolbox read for it
    while it ran: (the Table, or a table's name for an Unchecked statement's, and the column,
    or None for the whole table)."""

    function: str
    arguments: str = ""
    tag: str = ""
    reads: list[tuple[Table | str, str | None]] = field(default_factory=list)


# The calls being traced, innermost last: each read the Toolbox makes is noted in each.
_TRACING: list[Traced] = []


def note_read(table: Table | str, column: str | None = None) -> None:
    """Note a read the Toolbox makes, of a table or one of its columns, in each call being
    traced: latest_partition notes the partition column it reads, run_query each table its
    Statement reads."""
    for traced in _TRACING:
        if (table, column) not in traced.reads:
            traced.reads.append((table, column))


def _traced_call(function: Callable[..., object], arguments: tuple[object, ...],
                 keywords: dict[str, object], tag: str = ""
                 ) -> tuple[object, Traced, str | None]:
    """Call a function of yours, tracing what the Toolbox reads for it: what it gave, what it
    did, and why it failed, or None when it didn't."""
    shown = ", ".join([*(repr(each) for each in arguments),
                       *(f"{name}={each!r}" for name, each in keywords.items())])
    traced = Traced(run_value_name(function), shown, tag)
    _TRACING.append(traced)
    try:
        return function(*arguments, **keywords), traced, None
    except Exception as error:  # the user's own function: whatever it raises is reported
        failed = f"{traced.function}({shown}) raised {type(error).__name__}: {error}"
        return None, traced, failed
    finally:
        _TRACING.remove(traced)


def run_value(function: Callable[..., object], *arguments: object,
              **keywords: object) -> Column:
    """What a function gives, worked out each time the Statement is built, and traced.

    >>> import datetime
    >>> from sqlglot_composer import example_database
    >>> runs = example_database.job_runs
    >>> def days_before(day: datetime.date, days: int) -> datetime.date:
    ...     return day - datetime.timedelta(days=days)
    >>> print(to_hive(statement(
    ...     SELECT(runs.run_id),
    ...     FROM(runs),
    ...     WHERE(at_least(runs.dt, run_value(days_before, datetime.date(2026, 9, 24), 1))),
    ... )))
    SELECT
      job_runs.run_id
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt >= '2026-09-23'

    It calls function(*arguments, **keywords) and writes what it gives as a value, as a
    plain one is written: a date as '2026-09-23', text in quotes, a number, True or False.
    Any function will do, one of your Project's or a library's. A partition column held to it
    is bounded, as by a plain value. The Statement's lineage draws a box for it, naming the
    function, what it was given and what it gave, with an arrow into it from each table the
    Toolbox read for it while it ran: the partition column latest_partition reads, and each
    table a Statement it sends through run_query reads. A function that fails leaves its name
    in backticks in the value's place, with a Warning saying why, so show_hive still shows the
    rest; run_query and run_execute refuse to send it. A Script tag answered with a function is
    one too: script_tag(TAGS["PERIOD_END"]) calls it so.
    """
    if not callable(function):
        refuse(
            what=f"run_value({function!r}, ...) was given a {type(function).__name__}, not a "
            "function.",
            why="It calls the function each time the Statement is built, and writes what it "
            "gives.",
            fix="Give it the function itself, with no brackets after its name, then what to "
            "call it with, as in run_value(days_before, day, 7).",
            error=TypeError,
        )
    call = f"run_value({function.__qualname__}, ...)"
    given, traced, failed = _traced_call(function, arguments, keywords)
    if failed is not None:
        return _failed_column(call, function, traced, failed)
    if given is None:
        refuse(
            what=f"{call}: {traced.function}() gave None.",
            why="A value written into the Hive is one value; NULL has no type of its own.",
            fix=f"Have {traced.function} give back a value, or use is_null(...).",
            error=TypeError,
        )
    node = literal(given, call=call, in_condition=False)
    node.meta.update(call=call, traced=traced, value=hive_text(node))
    return Column(node)


def _failed_column(call: str, function: Callable[..., object], traced: Traced,
                   failed: str) -> Column:
    """The Column standing where a traced function's value goes when it failed: its name in
    backticks, which a dry run shows and run_query and run_execute refuse, with a Warning."""
    placeholder = f"`<{function.__qualname__}() failed>`"
    node = Node(SCRIPT_TAG, text=placeholder)
    node.meta.update(call=call, traced=traced, failed=failed)
    warn_at_callers_line(four_part_message(
        what=f"{call}: {failed}.",
        why="A Run value is worked out each time the Statement is built: with none, the Hive "
        f"holds {placeholder} in its place, which run_query and run_execute refuse to send.",
        fix=f"Fix {traced.function}, or what it reads, and build the Statement again.",
        opt_out="none - this one can't be switched off.",
    ), RunValueWarning)
    return Column(node)


def _run_value_column(function: Callable[[], object]) -> Column:
    """The Column of a bare Script tag answered with a Run value's function: the function
    called now, traced, each time the Statement is built, and what it gives written as
    Hive."""
    call = f"script_tag({function.__qualname__})"
    given, traced, failed = _traced_call(function, (), {}, _tag_answered_by(function))
    if failed is not None:
        return _failed_column(call, function, traced, failed)
    text = _hive_of_run_value(call, traced.function, given)
    node = Node(SCRIPT_TAG, text=text)
    node.meta.update(call=call, traced=traced, value=text)
    return Column(node)


def _tag_answered_by(function: Callable[[], object]) -> str:
    """The NAME of the Script tag a Run value answers, as the TAGS its caller's logic reads
    holds it, or "" when that TAGS doesn't hold it."""
    frame = callers_frame()
    tags = frame.f_locals.get("TAGS", frame.f_globals.get("TAGS"))
    if isinstance(tags, dict):
        for tag, value in tags.items():
            if value is function:
                return str(tag)
    return ""


def _hive_of_run_value(call: str, name: str, given: object) -> str:
    """The Hive a Run value's function's result is written as: a date in quotes, a number as
    it is, TRUE or FALSE, and text as Hive, held to what a Script tag's answer is."""
    if isinstance(given, bool):
        return "TRUE" if given else "FALSE"
    if isinstance(given, datetime.datetime):
        return f"'{given:%Y-%m-%d %H:%M:%S}'"
    if isinstance(given, datetime.date):
        return f"'{given.isoformat()}'"
    if isinstance(given, (int, float)):
        return repr(given)
    if isinstance(given, str) and given.strip():
        _check_tag_value(call, given)
        return given
    refuse(
        what=f"{call}: {name}() gave {given!r}, a {type(given).__name__}.",
        why="A Run value is written where the Script tag stood, as one value: a date, a "
        "number, TRUE or FALSE, or text that is Hive.",
        fix=f"Have {name} give back a datetime.date, a number, or the Hive text, such as "
        "\"'2026-10-31'\" with its quotes.",
        error=TypeError,
    )


def latest_partition(column: Column,
                     query: Callable[[str], object] | None = None) -> datetime.date | int | str:
    """The newest value of a partition column, from the warehouse's SHOW PARTITIONS.

    >>> from sqlglot_composer import example_database
    >>> latest_partition(example_database.job_runs.dt, example_database.query)
    datetime.date(2026, 9, 24)

    It sends SHOW PARTITIONS for the column's table through your query, which lists each
    Partition, such as dt=2026-09-24, and reads no row. A value written as a date, 2026-09-24,
    comes back as a datetime.date, one of digits alone as a number, and any other as text;
    the newest is the latest date, the biggest number, or the last text in order. It is what a
    Run value's function usually gives, in your Project's building_blocks/run_values.py:

        from sqlglot_composer import latest_partition
        from references.ops__job_runs import job_runs
        from warehouse import query

        def period_end():
            return latest_partition(job_runs.dt, query)

    It refuses a column that isn't one of its table's partition columns, before anything is
    sent, and a table that holds no Partition yet.
    """
    call = f"latest_partition({python_text(column)}, ...)"
    table = column._table if isinstance(column, Column) else None
    if table is None or column._name not in table._partitioned_by:
        partitioned = table._partitioned_by if table is not None else []
        refuse(
            what=f"{call} was given {python_text(column)}, which isn't a partition column"
            + (f" of {table._name}: its partition columns are {', '.join(partitioned)}."
               if partitioned else "."),
            why="It reads the Partitions a table holds, which SHOW PARTITIONS lists by their "
            "partition columns alone.",
            fix="Give it a partition column of a Table reference, such as job_runs.dt.",
            error=ValueError,
        )
    from .describe import send_describe  # describe.py imports pandas, as running does

    listed = send_describe(query, f"SHOW PARTITIONS {table._name}", call)
    note_read(table, column._name)
    values = []
    for row in listed.itertuples(index=False):
        for part in str(row[0]).split("/"):
            name, _, value = part.partition("=")
            if name.strip().lower() == column._name.lower():
                values.append(_listed_value(value.strip()))
    if not values:
        refuse(
            what=f"{call}: {table._name} holds no Partition yet.",
            why="SHOW PARTITIONS listed none, so there is no newest one to give.",
            fix=f"Write {table._name} first, or give the Run value a day of its own.",
            error=ValueError,
        )
    if len({type(value) for value in values}) > 1:
        return max(str(value) for value in values)
    return max(values)


def _listed_value(text: str) -> datetime.date | int | str:
    """A value SHOW PARTITIONS lists, its %XX escapes undone, as a date, a number or text."""
    text = re.sub(r"%([0-9A-Fa-f]{2})", _unescaped, text)
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        return datetime.date.fromisoformat(text)
    if re.fullmatch(r"-?\d+", text):
        return int(text)
    return text


def _unescaped(escape: re.Match[str]) -> str:
    """The character a %XX escape of SHOW PARTITIONS stands for."""
    return chr(int(escape.group(1), 16))


def hive_date(day: datetime.date) -> str:
    """A date as Hive writes one, in quotes, for Hive text you write by hand.

    >>> import datetime
    >>> hive_date(datetime.date(2026, 10, 31))
    "'2026-10-31'"

    A Run value's function may give back a date itself, which script_tag writes so; hive_date
    is for a date you put in Unchecked text, as in unchecked_condition("{dt} <= " +
    hive_date(day), dt=job_runs.dt). It refuses anything that isn't a date.
    """
    if not isinstance(day, datetime.date):
        refuse(
            what=f"hive_date({day!r}) was given a {type(day).__name__}, not a date.",
            why="It writes a date as Hive reads one: '2026-10-31', in quotes.",
            fix="Give it a datetime.date, such as datetime.date(2026, 10, 31), or "
            "latest_partition(...)'s.",
            error=TypeError,
        )
    if isinstance(day, datetime.datetime):
        return f"'{day:%Y-%m-%d %H:%M:%S}'"
    return f"'{day.isoformat()}'"


def tag_text(value: str | Callable[[], object]) -> str:
    """The text a Script tag inside quotes stands for, as its place in a string.

    >>> TAGS = {"RUN_MONTH": "2026-09"}
    >>> "month " + tag_text(TAGS["RUN_MONTH"])
    'month 2026-09'

    A Conversion writes it where a tag inside quotes stood: tag_text(TAGS["RUN_MONTH"]).
    TAGS, in the table's Table reference, holds what each tag stands for: for a tag inside
    quotes, the text with no quotes of its own, or a Run value's function, which tag_text calls
    each time the Statement is built. A date it gives is written as 2026-10-31, a number as it
    is, and text as it is. A function that fails is refused, naming it.
    """
    if not callable(value):
        return value
    name = run_value_name(value)
    call = f"tag_text({value.__qualname__})"
    try:
        given = value()
    except Exception as error:  # the user's own function: whatever it raises is reported
        refuse(
            what=f"{call}: {name}() raised {type(error).__name__}: {error}.",
            why="A Run value is worked out each time the Statement is built, and a tag inside "
            "quotes has no place to show one that failed.",
            fix=f"Fix {name}, or what it reads, and build the Statement again.",
            error=ValueError,
        )
    if isinstance(given, datetime.datetime):
        return f"{given:%Y-%m-%d %H:%M:%S}"
    if isinstance(given, datetime.date):
        return given.isoformat()
    if isinstance(given, (int, float, str)) and not isinstance(given, bool):
        return str(given)
    refuse(
        what=f"{call}: {name}() gave {given!r}, a {type(given).__name__}.",
        why="A tag inside quotes stands for text: a date, a number or text.",
        fix=f"Have {name} give back a datetime.date, a number or text.",
        error=TypeError,
    )


def refuse_failed_run_values(tree: Node) -> None:
    """Refuse to send a Statement whose tree holds a Run value whose function failed as it was
    built, naming why, before anything is sent."""
    failed = [node.meta["failed"] for node in tree.walk() if "failed" in node.meta]
    if failed:
        refuse(
            what="Nothing was sent: the Statement holds a Run value that failed, "
            + "; ".join(failed) + ".",
            why="Its Hive holds the function's name in the value's place, which no warehouse "
            "can run.",
            fix="Fix the function, or what it reads, then build the Statement again and send "
            "it.",
            error=ValueError,
        )


def _check_tag_value(call: str, text: str) -> None:
    """Refuse a Script tag's answer that can't stand where the tag stood, for the reason
    writing.tag_value_problem gives."""
    problem = tag_value_problem(text)
    if problem is not None:
        refuse(
            what=f"{call} was refused: {problem}.",
            why="A Script tag stands for one value, written where the tag stood: Hive reads "
            "anything more with what stands beside the tag, and a date with no quotes as a "
            "subtraction.",
            fix="Give TAGS, or the convert notebook's decisions cell, the one value the "
            "program put there, such as '2026-09-24' with its quotes, 5, or "
            "'${hivevar:period_end}'.",
            error=ValueError,
        )
