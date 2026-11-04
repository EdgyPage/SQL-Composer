"""Script tags: a <PARM="NAME"/> in Hive someone else wrote, which the program that ran it
filled in before Hive read it (Toolbox 8.3).

NAME is whatever name that program gave the tag. A tag stands for a value in one table's
statements alone, so a Conversion reads past it: sqlglot can't read a bare tag, as in
WHERE dt <= <PARM="PERIOD_END"/>, so `readable_tags` writes each one in backticks first, a name
sqlglot reads as a column, and `tags_as_written` takes the backticks off again. A tag inside
quotes, as in '<PARM="PERIOD_END"/>', is part of a string, which sqlglot reads as it is.

In a converted table's logic, a bare tag's place is script_tag(TAGS["PERIOD_END"]), and a quoted
one's is TAGS["PERIOD_END"] itself, a string; TAGS, in the table's Table reference, holds what
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
# Text that starts as a tag does, in any case: one that isn't a whole TAG is a shape no
# Conversion reads.
TAG_START = re.compile(r"<PARM", re.IGNORECASE)
# What a bare tag is written as for sqlglot: a name in backticks.
_IN_BACKTICKS = re.compile(r'`(<PARM="[^"`\n]+"/>)`')
# How each kind of quote, and each comment, opens and closes.
_CLOSING = {"'": "'", '"': '"', "`": "`", "--": "\n", "/*": "*/"}


@dataclass
class FoundTag:
    """One Script tag in Hive text: its NAME, where it starts, its line, counted from 1, and
    whether it sits inside quotes, part of a string."""

    name: str
    start: int
    line: int
    quoted: bool


def tags_in(text: str) -> list[FoundTag]:
    """Each Script tag in Hive text, in order, but those in a comment or already in backticks.
    A tag's own quotes are passed over: only those around it count."""
    found = []
    masked = TAG.sub(lambda match: "x" * len(match.group()), text)
    quotes = _quote_at_each_tag(masked, [match.start() for match in TAG.finditer(text)])
    for match, quote in zip(TAG.finditer(text), quotes, strict=True):
        if quote in ("'", '"', None):
            found.append(FoundTag(match.group(1), match.start(),
                                  text.count("\n", 0, match.start()) + 1, quote is not None))
    return found


def _quote_at_each_tag(masked: str, starts: list[int]) -> list[str | None]:
    """What each start in `masked` sits inside: a quote, ', " or `, a comment, -- or /*, or
    None, outside them all. Inside quotes, a backslash keeps the next character from closing
    them."""
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
    """The line, counted from 1, of the first text in `text` that starts as a Script tag does,
    <PARM in any case, but isn't one; None when there is none."""
    whole = {match.start() for match in TAG.finditer(text)}
    for match in TAG_START.finditer(text):
        if match.start() not in whole:
            return text.count("\n", 0, match.start()) + 1
    return None


def readable_tags(text: str) -> str:
    """Hive text with each bare Script tag in backticks, so sqlglot reads it as a name where a
    value goes; a tag inside quotes, or in a comment, is left as it is."""
    for tag in reversed([one for one in tags_in(text) if not one.quoted]):
        end = TAG.match(text, tag.start).end()
        text = text[:tag.start] + "`" + text[tag.start:end] + "`" + text[end:]
    return text


def tags_as_written(text: str) -> str:
    """Hive text with each Script tag `readable_tags` put in backticks written bare again, as
    the script wrote it."""
    return _IN_BACKTICKS.sub(r"\1", text)


def tag_name(text: str) -> str | None:
    """The NAME of a Script tag, when `text` is one whole tag, such as a name sqlglot read in
    backticks; None for any other text."""
    found = TAG.fullmatch(text)
    return found.group(1) if found else None


def script_tag(text: str) -> Column:
    """What a Script tag stands for, as Hive, where a value goes in a converted table's logic.

    >>> from sqlglot_composer import example_database
    >>> runs = example_database.job_runs
    >>> TAGS = {"PERIOD_END": "'2026-09-24'"}
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
    filled in before Hive read it, such as <PARM="PERIOD_END"/>. A Conversion writes
    script_tag(TAGS["PERIOD_END"]) where the tag stood bare, and TAGS, in the table's Table
    reference, holds what each tag stands for: you answer it in the convert notebook's
    decisions cell, under "tags", as the Hive the program put there, such as '2026-09-24' with
    its quotes, 5, or ${hivevar:period_end}. Until you do, TAGS holds the tag itself, which
    script_tag writes in backticks, `<PARM="PERIOD_END"/>`, and Hive refuses to run.

    It is a value, never a condition or a column of a table: text that names a column, holds
    more than one expression or reads a table of its own is refused. No Guard looks inside it,
    though a comparison with it holds a partition column to a value, as one with a plain value
    does.
    """
    call = f"script_tag({python_text(text)})"
    if not isinstance(text, str) or not text.strip():
        refuse(
            what=f"{call} was given {text!r}, not the Hive a Script tag stands for.",
            why="script_tag writes the text it is given where the tag stood in the original.",
            fix='Give it the table\'s TAGS entry, as in script_tag(TAGS["PERIOD_END"]), and '
            "answer the tag in the decisions cell.",
            given=text, call=call,
        )
    if tag_name(text) is not None:
        node = Node("ScriptTag", text=f"`{text}`")
    else:
        _check_tag_value(call, text)
        node = Node("ScriptTag", text=text)
    node.meta["call"] = call
    return Column(node)


def _check_tag_value(call: str, text: str) -> None:
    """Refuse a Script tag's answer that isn't one value sqlglot reads as Hive."""
    facts = read_unchecked_expression(text, [])
    problem = facts.unreadable
    if problem is None and (facts.count != 1 or facts.named or facts.reads_a_table):
        problem = "it isn't one value"
    if problem is None and facts.columns:
        problem = f"it names a column, {facts.columns[0]}"
    if problem is not None:
        refuse(
            what=f"{call}: {problem}.",
            why="A Script tag stands for one value, such as a date or a number, written where "
            "the tag stood.",
            fix="Answer it in the decisions cell as the Hive the program put there, such as "
            "'2026-09-24' with its quotes, 5, or ${hivevar:period_end}.",
            error=ValueError,
        )
