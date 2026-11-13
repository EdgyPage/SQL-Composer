"""Run values: what a Python function gives each time a Statement is built, traced for its
lineage (Toolbox 8.4).

Any function will do: run_value(function, ...) calls it where a value goes, and a Script tag
answered with a function, script_tag(TAGS["PERIOD_END"]), calls it where the tag stood. Each
call is traced: while it runs, each read the Toolbox makes for it (latest_partition's
partition column, each table a Statement it sends through run_query reads) is noted, and the
Statement's lineage draws a box for the call, with an arrow from each read. A function that
fails leaves a placeholder in its value's place, with a Warning, so a dry run still shows the
rest, and the Statement is never sent. While project.build_run builds a Scheduled run, a
Run value its run_values= names, by its function's name, gives that value instead, its
function not called.

today, latest_partition and hive_date help write such a function.
"""

from __future__ import annotations

import datetime
import re
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import NamedTuple, NoReturn

from .describe import printed_answer
from .refusals import callers_frame, refuse, warn_run_value_failed
from .script_tags import SCRIPT_TAG, check_tag_value
from .shared import escaped_literal, with_article
from .tables import Column, Table, literal, python_text
from .trees import Node
from .writing import hive_text, tag_value_problem

# The Partition SHOW PARTITIONS lists for the rows whose partition column is NULL: no value.
HIVE_DEFAULT_PARTITION = "__HIVE_DEFAULT_PARTITION__"


@dataclass(frozen=True)
class TracedRead:
    """One read the Toolbox made for a traced call: a table, by its name, and its Table
    reference when it has one, and the column read, or None for the whole table."""

    name: str
    table: Table | None = None
    column: str | None = None


@dataclass
class Traced:
    """What one call of a function did as a Statement was built, for its lineage: the
    function by its module and name, the arguments it was given, the Script tag it answers,
    if it answers one, and each read the Toolbox made for it while it ran."""

    function: str
    arguments: str = ""
    tag: str = ""
    reads: list[TracedRead] = field(default_factory=list)


@dataclass
class ValuesGiven:
    """The Run values project.build_run gives a value while it builds (Toolbox 8.6): the value
    its run_values= gives each, by its function's name; how each is read for the function it
    stands in for, read(name, value, function); each value used, as read, by its name; and the
    name of each Run value met, called or given a value, in order."""

    given: dict[str, object]
    read: Callable[[str, object, Callable[..., object]], object]
    used: dict[str, object] = field(default_factory=dict)
    met: list[str] = field(default_factory=list)


# The calls being traced, innermost last: note_read notes each read in each of them.
_TRACING: list[Traced] = []
# While project.build_run builds, the Run values it gives a value; None at any other time.
_VALUES_GIVEN: ValuesGiven | None = None


@contextmanager
def values_given(given: dict[str, object],
                 read: Callable[[str, object, Callable[..., object]], object]
                 ) -> Iterator[ValuesGiven]:
    """While the block runs, each Run value whose function's name `given` holds gives that
    value in place of calling the function, a Script tag's and tag_text's too, as
    read(name, value, function) reads it for that function. What it gives holds each value
    used, as read, and the name of each Run value met while the block runs, in order.
    Afterwards, each function is called again."""
    global _VALUES_GIVEN  # one build at a time; the one before, if any, comes back after
    before = _VALUES_GIVEN
    _VALUES_GIVEN = ValuesGiven(dict(given), read)
    try:
        yield _VALUES_GIVEN
    finally:
        _VALUES_GIVEN = before


def function_name(function: Callable[..., object]) -> str:
    """A function by its module and name, such as building_blocks.run_values.period_end, or
    its name alone when it has no module, as one made in a doctest has none."""
    if not function.__module__:
        return function.__qualname__
    return f"{function.__module__}.{function.__qualname__}"


def note_read(name: str, table: Table | None = None, column: str | None = None) -> None:
    """Note a read the Toolbox makes, of a table or one of its columns, in each call being
    traced, if any is."""
    read = TracedRead(name, table, column)
    for traced in _TRACING:
        if read not in traced.reads:
            traced.reads.append(read)


def _traced_call(function: Callable[..., object], arguments: tuple[object, ...],
                 keywords: dict[str, object], tag: str = ""
                 ) -> tuple[object, Traced, str | None]:
    """Call a function, tracing what the Toolbox reads for it: what it gave, the trace, and
    why it failed, or None when it didn't."""
    shown = ", ".join([*(repr(each) for each in arguments),
                       *(f"{name}={each!r}" for name, each in keywords.items())])
    traced = Traced(function_name(function), shown, tag)
    name = getattr(function, "__name__", traced.function)
    if _VALUES_GIVEN is not None:
        _VALUES_GIVEN.met.append(name)
    if _VALUES_GIVEN is not None and name in _VALUES_GIVEN.given:
        value = _VALUES_GIVEN.read(name, _VALUES_GIVEN.given[name], function)
        _VALUES_GIVEN.used.setdefault(name, value)
        return value, traced, None
    _TRACING.append(traced)
    try:
        return function(*arguments, **keywords), traced, None
    except Exception as error:  # the user's own function: whatever it raises is reported
        failed = f"{traced.function}({shown}) raised {type(error).__name__}: {error}"
        return None, traced, failed
    finally:
        _TRACING.remove(traced)


def _traced_column(call: str, function: Callable[..., object], arguments: tuple[object, ...],
                   keywords: dict[str, object], tag: str,
                   written: Callable[[object, str, str], Node]) -> Column:
    """The Column of a traced call: the function called now, and what it gives written as the
    Node `written` makes of it; or, when it fails, a placeholder in its place, which a dry run
    shows and run_query and run_execute refuse to send, with a Warning saying why."""
    given, traced, failed = _traced_call(function, arguments, keywords, tag)
    if failed is None:
        node = written(given, call, traced.function)
        node.meta.update(call=call, traced=traced, value=hive_text(node))
        return Column(node)
    return _failed_column(call, traced, failed, tag or function.__qualname__ + "()")


def _failed_column(call: str, traced: Traced, failed: str, shown: str) -> Column:
    """The placeholder a traced call that failed leaves in its value's place, `shown` in it,
    such as `<PERIOD_END failed>`: a dry run shows it, and run_query and run_execute refuse to
    send it, with a Warning saying why."""
    placeholder = f"`<{shown} failed>`"
    node = Node(SCRIPT_TAG, text=placeholder)
    node.meta.update(call=call, traced=traced, failed=failed)
    warn_run_value_failed(call, failed, placeholder, traced.function)
    return Column(node)


def run_value(function: Callable[..., object], *arguments: object,
              **keywords: object) -> Column:
    """What a function gives, worked out each time the Statement is built, and traced.

    >>> import datetime
    >>> runs = job_runs
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
    is bounded, as by a plain value.

    A function that fails leaves its name in backticks in the value's place, such as
    `<days_before() failed>`, with a Warning saying why, so show_hive still shows the rest;
    run_query and run_execute refuse to send it. A Script tag answered with a function is a
    Run value too: script_tag(TAGS["PERIOD_END"]) calls it the same way.

    The Statement's lineage draws a box for each Run value: the function, what it was given
    and what it gave. An arrow goes into the box from each table the Toolbox read for it while
    it ran: the partition column latest_partition reads, and each table read by a Statement
    it sends through run_query.
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
    return _traced_column(f"run_value({function.__qualname__}, ...)", function, arguments,
                          keywords, "", _plain_value)


def _plain_value(given: object, call: str, function: str) -> Node:
    """What run_value's function gave, written as a plain value is."""
    if given is None:
        refuse(
            what=f"{call}: {function}() gave None.",
            why="A value written into the Hive is one value; NULL has no type of its own.",
            fix=f"Have {function} give back a value, or use is_null(...).",
            error=TypeError,
        )
    return literal(given, call=call, in_condition=False)


def tag_value_column(function: Callable[[], object]) -> Column:
    """The Column of a bare Script tag answered with a Run value's function: the function
    called now, traced, each time the Statement is built, and what it gives written as Hive.
    script_tag gives it."""
    return _traced_column(f"script_tag({function.__qualname__})", function, (), {},
                          _tag_answered_by(function), _tag_value)


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


def _tag_value(given: object, call: str, function: str) -> Node:
    """What a Script tag's function gave, written where the tag stood: a date in quotes, a
    number as it is, TRUE or FALSE, and text as Hive, held to what a Script tag's answer is."""
    if isinstance(given, bool):
        return Node(SCRIPT_TAG, text="TRUE" if given else "FALSE")
    if isinstance(given, datetime.date):
        return Node(SCRIPT_TAG, text=hive_date(given))
    if isinstance(given, (int, float)):
        return Node(SCRIPT_TAG, text=repr(given))
    if isinstance(given, str) and given.strip():
        check_tag_value(call, given)
        return Node(SCRIPT_TAG, text=given)
    refuse(
        what=f"{call}: {function}() gave {given!r}, a {type(given).__name__}.",
        why="A Run value is written where the Script tag stood, as one value: a date, a "
        "number, TRUE or FALSE, or text that is Hive.",
        fix=f"Have {function} give back a datetime.date, a number, or the Hive text, such as "
        "\"'2026-10-31'\" with its quotes.",
        error=TypeError,
    )


def tag_text(value: str | Callable[[], object] | Hivevar, *, quoted: bool = True) -> str:
    """The text a Script tag stands for, as its place in a string.

    >>> TAGS = {"RUN_MONTH": "2026-09", "PERIOD_END": "'2026-09-24'"}
    >>> "month " + tag_text(TAGS["RUN_MONTH"])
    'month 2026-09'
    >>> "dt <= " + tag_text(TAGS["PERIOD_END"], quoted=False)
    "dt <= '2026-09-24'"

    A Conversion writes it for you, where a tag stood in text it keeps:

    - if the tag stood inside quotes, as '<PARM="RUN_MONTH"/>', it writes
      tag_text(TAGS["RUN_MONTH"]): the quotes are the original's, so the text has none;
    - if the tag stood bare, in Hive kept whole as text, it writes
      tag_text(TAGS["PERIOD_END"], quoted=False): the text is the value as Hive, with its own
      quotes, as '2026-09-24'.

    TAGS, in the
    table's Table reference, holds what each tag stands for: text, or a Run value's function,
    which tag_text calls each time the Statement is built. A date it gives is written as
    2026-10-31 inside quotes and as '2026-10-31' bare, a number as it is, True or False bare as
    TRUE or FALSE, and text as it is: bare, it must be one value of a kind a program puts in a
    tag's place, as script_tag holds its answer to. A function that fails is refused, naming
    it. What it gives is text inside a string, so the
    Statement's lineage, which traces each value, doesn't draw it.

    Given a Hivevar (help(hivevar)), it gives the Hivevar, whose value the Toolbox sends
    before the Statement. For a tag inside quotes,
    tag_text(hivevar("RUN_MONTH", default="2026-09")) gives ${hivevar:RUN_MONTH}, and the
    original's quotes stay around it. For a bare tag,
    tag_text(hivevar("PERIOD_END", default="'2026-09-24'"), quoted=False) gives
    '${hivevar:PERIOD_END}'.
    """
    if isinstance(value, Hivevar):
        return _hivevar_text(value, quoted)
    if not callable(value):
        return value
    call = f"tag_text({value.__qualname__})"
    given, traced, failed = _traced_call(value, (), {})
    if failed is not None:
        _refuse_failed_tag_text(call, traced, failed)
    return _tag_text_written(given, call, traced.function, quoted=quoted)


def _refuse_failed_tag_text(call: str, traced: Traced, failed: str) -> NoReturn:
    """Refuse tag_text a Run value whose function failed: a string has no place to show it."""
    refuse(
        what=f"{call}: {failed}.",
        why="A Run value is worked out each time the Statement is built, and a tag in "
        "text kept as it is has no place to show one that failed.",
        fix=f"Fix {traced.function}, or what it reads, and build the Statement again.",
        error=ValueError,
    )


def _tag_text_written(given: object, call: str, function: str, *, quoted: bool) -> str:
    """What a Run value's function, `function`, gave, as tag_text writes it: inside quotes, a
    date as 2026-10-31, a number or text as it is; bare, a date as '2026-10-31', TRUE or
    FALSE, and text held to what a Script tag's answer is."""
    if isinstance(given, datetime.date) and not quoted:
        return hive_date(given)
    if isinstance(given, datetime.date):
        return hive_date(given).strip("'")
    if isinstance(given, bool) and not quoted:
        return "TRUE" if given else "FALSE"
    if isinstance(given, str) and not quoted:
        check_tag_value(call, given)
        return given
    if isinstance(given, (int, float, str)) and not isinstance(given, bool):
        return str(given)
    refuse(
        what=f"{call}: {function}() gave {given!r}, a {type(given).__name__}.",
        why="A tag in text kept as it is stands for one value: a date, a number or text, "
        "and, standing bare, TRUE or FALSE too.",
        fix=f"Have {function} give back a datetime.date, a number or text.",
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
            why="Its Hive holds a placeholder in the value's place, which no warehouse can "
            "run.",
            fix="Fix the function, or what it reads, then build the Statement again and send "
            "it.",
            error=ValueError,
        )


# --- Hivevars ------------------------------------------------------------------------------


# A Hivevar's NAME: a letter or _, then letters, digits and _.
_HIVEVAR_NAME = re.compile(r"[A-Za-z_]\w*")
# A Hivevar as it stands in Hive text, its NAME in the group.
HIVEVAR_IN_HIVE = re.compile(rf"\$\{{hivevar:({_HIVEVAR_NAME.pattern})\}}")


@dataclass(frozen=True)
class Hivevar:
    """A Script tag's answer that leaves the tag's place for whatever runs the Hive to fill in:
    its NAME, and its default, Hive text or a Run value's function. hivevar(...) makes one."""

    name: str
    default: str | Callable[[], object]

    def __repr__(self) -> str:
        """As a Table reference's TAGS writes it, such as
        hivevar("PERIOD_END", default="'2026-10-31'")."""
        default = _default_written(self.default)
        return f"hivevar({escaped_literal(self.name)}, default={default})"


def _default_written(default: str | Callable[[], object]) -> str:
    """A Hivevar's default as a Table reference writes it: its text in quotes, or its
    function's name."""
    if callable(default):
        return default.__qualname__
    return escaped_literal(default)


@dataclass
class HivevarsGiven:
    """The values project.build_run's hivevars= gives Hivevars while it builds, by NAME, and
    the NAME of each Hivevar met, in order."""

    given: dict[str, object]
    met: list[str] = field(default_factory=list)


class HivevarGiven(NamedTuple):
    """What a Hivevar is worked out from as a Statement is built: the value; the trace of its
    Run value's function, when one was called; why that function failed, or None; and what
    gave the value, as a refusal names it: the function, hivevars=, or the Hivevar's NAME for
    a text default."""

    value: object
    traced: Traced | None
    failed: str | None
    given_by: str


# While project.build_run builds, the values its hivevars= gives; None at any other time.
_HIVEVARS_GIVEN: HivevarsGiven | None = None
# The value each Hivevar was last worked out as, by its NAME. A Statement keeps a copy of it
# as it is made (last_hivevar_values), for the Hivevars tag_text wrote into its strings, which
# keep no note of their value.
_LAST_VALUE_BY_NAME: dict[str, str] = {}


@contextmanager
def hivevars_given(given: dict[str, object]) -> Iterator[HivevarsGiven]:
    """While the block runs, each Hivevar whose NAME `given` holds, with a value that isn't
    None, is worked out from that value in place of its default. What it gives holds the NAME
    of each Hivevar met while the block runs, in order."""
    global _HIVEVARS_GIVEN  # one build at a time; the one before, if any, comes back after
    before = _HIVEVARS_GIVEN
    _HIVEVARS_GIVEN = HivevarsGiven(dict(given))
    try:
        yield _HIVEVARS_GIVEN
    finally:
        _HIVEVARS_GIVEN = before


def hivevar(name: str, *, default: str | Callable[[], object]) -> Hivevar:
    """An answer to a Script tag that the warehouse fills in each time the Hive runs.

    >>> runs = job_runs
    >>> TAGS = {"PERIOD_END": hivevar("PERIOD_END", default="'2026-09-24'")}
    >>> print(to_hive(statement(
    ...     SELECT(runs.run_id),
    ...     FROM(runs),
    ...     WHERE(at_most(runs.dt, script_tag(TAGS["PERIOD_END"]))),
    ... )))
    SELECT
      job_runs.run_id
    FROM ops.job_runs AS job_runs
    WHERE
      job_runs.dt <= '${hivevar:PERIOD_END}'

    A Hivevar is a ${hivevar:NAME} in the Hive, which your warehouse fills in each time the
    Hive runs, from the value it is given then. The Script tag stays as it is: you answer it
    with hivevar(...) in place of the Hive text or the Run value's function, in the convert
    notebook's decisions cell, as in
    {"tags": {"PERIOD_END": hivevar("PERIOD_END", default="'2026-09-24'")}}, and
    project.write_decisions writes it into TAGS. Which to choose: a Run value is worked out
    when the Statement is built and written into the Hive; a Hivevar leaves ${hivevar:NAME} in
    the Hive, filled in by the Toolbox's SET line when the Toolbox sends it, and by your
    scheduler when it runs the .hql export_hive writes. Choose a Hivevar when that .hql runs
    outside the Toolbox.

    `name` is the Hivevar's NAME: a letter or _, then letters, digits and _, often the tag's
    own. `default=` is its value unless a Scheduled run's hivevars= gives another: the Hive
    the program put where the tag stood, written as a text answer is, such as "'2026-09-24'"
    with its quotes for a bare tag, or a Run value's function, called each time the Statement
    is built. If the default has quotes, as "'2026-09-24'" does, the quotes go around the
    Hivevar in the Hive, '${hivevar:PERIOD_END}', and the value sent is 2026-09-24, without
    them. A number or TRUE has none, so the Hive holds ${hivevar:DAYS} bare.

    The Toolbox sends the value before each Statement that holds it: run_execute(s, execute),
    project.run_tables and a Scheduled run's built.run first send
    SET hivevar:PERIOD_END=2026-09-24 through your execute, in a call of its own, and
    show_hive prints that line above the Statement. run_query writes the value in the
    Hivevar's place, since your query gives back rows and a SET line gives none. A Scheduled
    run gives another value by NAME, such as its parameter RUN_DATE:
    project.build_run(statements, hivevars={"PERIOD_END": RUN_DATE}).

    export_hive writes no SET line into its .hql file, since Hive lets a SET in the script
    beat a value given on its command line, as in hive --hivevar PERIOD_END=... -f daily.hql:
    it writes each value into a .hivevars file beside it, as --hivevar PERIOD_END=2026-09-24,
    for your scheduler to pass to Hive with the .hql.

    It refuses a NAME Hive can't read, and a default that is neither text, such as "5" for a
    number, nor a function. A text default is checked when script_tag or tag_text writes it,
    as a text answer is.
    """
    if not isinstance(name, str) or not _HIVEVAR_NAME.fullmatch(name):
        refuse(
            what=f"hivevar({name!r}, ...) was given {name!r}, which can't be a Hivevar's "
            "NAME.",
            why="Hive reads ${hivevar:NAME} where a NAME starts with a letter or _ and holds "
            "only letters, digits and _.",
            fix='Give it a name such as "PERIOD_END", often the Script tag\'s own.',
            error=ValueError,
        )
    is_text = isinstance(default, str) and bool(default.strip())
    if not is_text and not callable(default):
        given = "empty text"
        if not isinstance(default, str):
            given = with_article(type(default).__name__)
        refuse(
            what=f"hivevar({name!r}, default={default!r}) was given {given} for its default.",
            why="The default is the value the Toolbox sends unless a Scheduled run gives "
            "another: the Hive text a Script tag's answer is, or a Run value's function.",
            fix=f"Give default= the Hive text, such as hivevar({name!r}, "
            "default=\"'2026-10-31'\") for a date, with its quotes, or default=\"5\" for a "
            "number; or a Run value's function, with no brackets after its name.",
            error=TypeError,
        )
    return Hivevar(name, default)


def hivevar_column(answer: Hivevar) -> Column:
    """The Column of a bare Script tag answered hivevar(...): the Hivevar, standing in quotes
    when its value, worked out now, does, with a note of its NAME and value. A Run value's
    function that fails leaves a placeholder, as for any Run value. script_tag gives it."""
    call = f"script_tag({answer!r})"
    given = _hivevar_given(answer, call, bare=True)
    if given.failed is not None:
        return _failed_column(call, given.traced, given.failed, answer.name)
    hive = _tag_value(given.value, call, given.given_by).parts["text"]
    written, value = _hivevar_in_place(answer.name, hive)
    _keep_hivevar_value(call, answer.name, value)
    node = Node(SCRIPT_TAG, text=written)
    node.meta.update(call=call, hivevar=answer.name, hivevar_value=value,
                     hivevar_default=_default_traced(answer, given.traced))
    if given.traced is not None:
        node.meta["traced"] = given.traced
    return Column(node)


def _hivevar_text(answer: Hivevar, quoted: bool) -> str:
    """tag_text's text for a Script tag answered hivevar(...): ${hivevar:NAME} inside the
    original's quotes; bare, the Hivevar in quotes when its value, worked out now, is."""
    call = f"tag_text({answer!r})"
    given = _hivevar_given(answer, call, bare=not quoted)
    if given.failed is not None:
        _refuse_failed_tag_text(call, given.traced, given.failed)
    text = _tag_text_written(given.value, call, given.given_by, quoted=quoted)
    if quoted:
        written, value = f"${{hivevar:{answer.name}}}", text
    else:
        written, value = _hivevar_in_place(answer.name, text)
    _keep_hivevar_value(call, answer.name, value)
    return written


def _hivevar_given(answer: Hivevar, call: str, *, bare: bool) -> HivevarGiven:
    """What a Hivevar is worked out from now, where its tag stood bare or not: the value
    project.build_run's hivevars= gives it, else its default, a Run value's function called,
    traced."""
    if _HIVEVARS_GIVEN is not None:
        _HIVEVARS_GIVEN.met.append(answer.name)
        given = _HIVEVARS_GIVEN.given.get(answer.name)
        if given is not None:
            _check_hivevar_given(answer.name, given, call, bare=bare)
            return HivevarGiven(given, None, None, "hivevars=")
    if callable(answer.default):
        value, traced, failed = _traced_call(answer.default, (), {}, answer.name)
        return HivevarGiven(value, traced, failed, traced.function)
    return HivevarGiven(answer.default, None, None, answer.name)


def _check_hivevar_given(name: str, given: object, call: str, *, bare: bool) -> None:
    """Refuse a value hivevars= gives a Hivevar that a Script tag's place can't take: one of
    another type, and text that can't stand where a bare tag stood."""
    problem = None
    if isinstance(given, str) and given.strip() and bare:
        problem = tag_value_problem(given)
    elif not isinstance(given, (datetime.date, int, float, str)) or given == "":
        problem = f"{with_article(type(given).__name__)} is no value a Script tag stands for"
    if problem is None:
        return
    refuse(
        what=f"{call}: hivevars= gives {name} {python_text(given)}, which can't stand where "
        f"its tag stood: {problem}.",
        why="A Hivevar stands for one value where a Script tag stood: a date, a number, TRUE "
        "or FALSE, or the Hive text, such as \"'2026-10-31'\" with its quotes.",
        fix=f"In the Build cell's hivevars=, give {name} a datetime.date, such as "
        "datetime.date(2026, 10, 31), a number or the Hive text, or None to send its default.",
        error=TypeError,
    )


def _hivevar_in_place(name: str, hive: str) -> tuple[str, str]:
    """A Hivevar where a bare tag stood, its value's Hive `hive`, and the value it is sent as:
    in the value's own quotes, '${hivevar:NAME}' and the text inside them; else bare."""
    for quote in ("'", '"'):
        if len(hive) > 1 and hive.startswith(quote) and hive.endswith(quote):
            return f"{quote}${{hivevar:{name}}}{quote}", hive[1:-1]
    return f"${{hivevar:{name}}}", hive


def _keep_hivevar_value(call: str, name: str, value: str) -> None:
    """Keep the value a Hivevar was worked out as, by its NAME, once it is checked."""
    _check_hivevar_value(call, name, value)
    _LAST_VALUE_BY_NAME[name] = value


def _check_hivevar_value(call: str, name: str, value: str) -> None:
    """Refuse a Hivevar's value that a SET line can't hold: one with a ; or a line break."""
    if ";" in value or "\n" in value or "\r" in value:
        refuse(
            what=f"{call}: the Hivevar {name}'s value, {value!r}, holds a ; or a line break.",
            why=f"The Toolbox sends it as SET hivevar:{name}=<value>, one line, which a ; or a "
            "line break would end early.",
            fix="Give a value with neither.",
            error=ValueError,
        )


def _default_traced(answer: Hivevar, traced: Traced | None) -> str:
    """A Hivevar's default as its lineage box says it: its text, or its function's call."""
    if traced is not None:
        return f"{traced.function}()"
    return _default_written(answer.default)


def last_hivevar_values() -> dict[str, str]:
    """The value each Hivevar was last worked out as, by its NAME: a copy, which a Statement
    keeps as it is made, so the Hivevars tag_text wrote into its strings, worked out just
    before, are sent with their own values."""
    return dict(_LAST_VALUE_BY_NAME)


# --- Helpers for a Run value's function -----------------------------------------------------


def latest_partition(column: Column,
                     query: Callable[[str], object] | None = None) -> datetime.date | int | str:
    """The newest value of a partition column, from the warehouse's SHOW PARTITIONS.

    >>> latest_partition(job_runs.dt, query)
    datetime.date(2026, 9, 24)

    It sends SHOW PARTITIONS for the column's table through your query, which lists each
    Partition, such as dt=2026-09-24, and reads no row. When every value is a date, such as
    2026-09-24, it gives the latest as a datetime.date; when every value is digits alone, the
    biggest as a number; otherwise the last, in the order of their text. The Partition Hive
    keeps for rows with no value, __HIVE_DEFAULT_PARTITION__, is passed over. It is what a Run
    value's function usually gives, in your Project's building_blocks/run_values.py:

        import datetime

        from sqlglot_composer import latest_partition
        from references.ops__job_runs import job_runs
        from warehouse import query

        def period_end() -> datetime.date:
            return latest_partition(job_runs.dt, query)

    It refuses a column that isn't one of its table's partition columns, before anything is
    sent, and a table that holds no Partition yet.
    """
    call = f"latest_partition({python_text(column)}, ...)"
    table = column._table if isinstance(column, Column) else None
    if table is None or column._name not in table._partitioned_by:
        _refuse_not_a_partition_column(call, column, table)
    listed = printed_answer(query, f"SHOW PARTITIONS {table._name}", call)
    note_read(table._name, table, column._name)
    values = []
    for row in listed.itertuples(index=False):
        for part in str(row[0]).split("/"):
            name, _, value = part.partition("=")
            if name.strip().lower() == column._name.lower() and value != HIVE_DEFAULT_PARTITION:
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


def _refuse_not_a_partition_column(call: str, column: object, table: Table | None) -> None:
    """Refuse latest_partition a column that isn't one of its table's partition columns."""
    what = f"{call} was given {python_text(column)}, which isn't a partition column."
    if table is not None and table._partitioned_by:
        what = (f"{call} was given {python_text(column)}, which isn't a partition column of "
                f"{table._name}: its partition columns are {', '.join(table._partitioned_by)}.")
    refuse(
        what=what,
        why="It reads the Partitions a table holds, which SHOW PARTITIONS lists by their "
        "partition columns alone.",
        fix="Give it a partition column of a Table reference, such as job_runs.dt.",
        error=ValueError,
    )


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

    A Run value's function may give back a date itself, which script_tag writes in this form
    for you; hive_date is for a date you put in Unchecked text, as in
    unchecked_condition("{dt} <= " + hive_date(day), dt=job_runs.dt). A datetime is written
    with its time, '2026-10-31 06:30:00'. It refuses anything that isn't a date.
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
