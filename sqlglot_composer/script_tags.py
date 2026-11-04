"""Script tags: a <PARM="NAME"/> in Hive someone else wrote, which the program that ran it
filled in before Hive read it (Toolbox 8.3).

NAME is whatever name that program gave the tag. A tag stands for a value in one table's
statements alone, so a Conversion reads past it. sqlglot can't read a bare tag, as in
WHERE dt <= <PARM="PERIOD_END"/>, so `readable_tags` writes each one in backticks first, a name
sqlglot reads as a column, and `tags_as_written` takes the backticks off again. A tag inside
quotes, as in '<PARM="PERIOD_END"/>', is part of a string, which sqlglot reads as it is.

In a converted table's logic, a bare tag's place is script_tag(TAGS["PERIOD_END"]), and a quoted
one's is TAGS["PERIOD_END"] itself, a string. TAGS, in the table's Table reference, holds what
each tag stands for, a Decision answered in the decisions cell.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .refusals import refuse
from .tables import Column, python_text
from .trees import Node
from .writing import read_unchecked_expression

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


def is_script_tag(value: object) -> bool:
    """Whether `value` is a Column script_tag made."""
    return isinstance(value, Column) and value._tree.kind == SCRIPT_TAG


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
    or ${hivevar:period_end}, a Hive variable your warehouse fills in when the query runs.

    You answer each tag in the convert notebook's decisions cell, under "tags", as in
    DECISIONS = {"mart_dev.daily_close": {"tags": {"PERIOD_END": "'2026-09-24'"}}}, and its
    next step writes the answer into TAGS; answering again changes it. Until then TAGS holds
    the tag itself, and the table isn't created: script_tag would write a bare one in
    backticks, `<PARM="PERIOD_END"/>`, which Hive refuses to run.

    It is a value, never a condition or a column of a table: text that names a column, holds
    more than one expression or reads a table of its own is refused. The Toolbox doesn't check
    the text inside it, but at_most(runs.dt, script_tag(...)) still filters dt, a partition
    column, as at_most(runs.dt, "2026-09-24") does.
    """
    call = f"script_tag({python_text(text)})"
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


def _check_tag_value(call: str, text: str) -> None:
    """Refuse a Script tag's answer that isn't one value sqlglot reads as Hive."""
    facts = read_unchecked_expression(text, [])
    problem = facts.unreadable
    if problem is None and (facts.count != 1 or facts.named or facts.reads_a_table):
        problem = "it isn't one value"
    if problem is None and facts.columns:
        problem = f"it isn't one value: it names a column, {facts.columns[0]}"
    if problem is not None:
        refuse(
            what=f"{call}: {problem}.",
            why="A Script tag stands for one value, such as a date or a number, written where "
            "the tag stood.",
            fix="Give TAGS the Hive the program put there, such as '2026-09-24' with its "
            "quotes, 5, or ${hivevar:period_end}.",
            error=ValueError,
        )
