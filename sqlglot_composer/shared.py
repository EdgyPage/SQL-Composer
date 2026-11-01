"""The functions many of the Toolbox's files share, one for each job they all do.

docs/agents/standards.md's "One way per job" lists each job and its function here; every place
that does the job calls it. Nothing here is a public name, and nothing here imports another of
the Toolbox's files, so any of them may import it.
"""

from __future__ import annotations

import json


def in_words(items: list[str], last: str = "and") -> str:
    """Items as a sentence lists them: "a", "a and b", or "a, b and c"; with last="or",
    "a, b or c"."""
    if len(items) < 2:
        return "".join(items)
    return f"{', '.join(items[:-1])} {last} {items[-1]}"


def singular_or_plural(count: int, singular: str, plural: str) -> str:
    """`singular` for a count of one, else `plural`: "is" or "are", "it" or "them"."""
    if count == 1:
        return singular
    return plural


def counted(count: int, noun: str, plural: str | None = None) -> str:
    """A count and its noun, plural but for one: "1 line", "25 lines". `plural` is the noun's
    plural where an s won't do: counted(2, "property", "properties")."""
    return f"{count} {singular_or_plural(count, noun, plural or f'{noun}s')}"


def python_literal(value: object) -> str:
    """A value written as Python, for code or a message the Toolbox writes: text in double
    quotes, escaped as Python reads it, and anything else as Python shows it."""
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    return repr(value)


def escaped_literal(value: object) -> str:
    """A value written as Python as a Table reference and its messages write it: as
    python_literal does, but with each letter outside ASCII as an escape, as they always
    have, and a list of names as a list of such text."""
    if isinstance(value, (str, list)):
        return json.dumps(value)
    return repr(value)


def split_table_name(name: str) -> tuple[str, str]:
    """A table's name split into its Database and its table: "ops.jobs" gives ("ops", "jobs"),
    and a name with no Database gives ("", its name)."""
    database, _, table = name.rpartition(".")
    return database, table


def with_article(noun: str) -> str:
    """The noun with "a" before it, or "an" when it starts with a vowel: "a list", "an
    object"."""
    if noun[0] in "aeiou":
        return f"an {noun}"
    return f"a {noun}"


def possessive(name: str) -> str:
    """A name with its 's, or only ' when it ends in s: "numbered's", "job_runs'"."""
    if name.endswith("s"):
        return f"{name}'"
    return f"{name}'s"
