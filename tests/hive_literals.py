"""Reading a Hive string's values back by its characters alone, as Hive's own reader does.

The escaping tests read the Toolbox's Hive with this in both Editions. It knows nothing of the
Toolbox, of sqlglot or of Spark Composer's writer, so it checks all of them rather than repeat
one. A value in single quotes is decoded the way Hive decodes it: a backslash before n, t, r, b
or 0 stands for that control character, a backslash before % or _ is kept for LIKE, and a
backslash before any other character stands for that character itself.
"""

from __future__ import annotations

_CONTROL = {"n": "\n", "t": "\t", "r": "\r", "b": "\b", "0": "\0"}


def values(hive: str) -> list[str]:
    """Every value in single quotes in a Hive string, decoded, in order.

    It fails when the text outside the values starts a comment or a second statement, or a value
    doesn't end: what a value that escaped its quotes would do.
    """
    found, at = [], 0
    while at < len(hive):
        if hive[at] == "'":
            value, at = _value(hive, at + 1)
            found.append(value)
        elif hive[at] == "`":
            at = hive.index("`", at + 1) + 1
            while at < len(hive) and hive[at] == "`":  # a doubled backtick inside a name
                at = hive.index("`", at + 1) + 1
        else:
            assert hive[at] != ";", "a value started a second statement"
            assert not hive.startswith("--", at), "a value started a comment"
            at += 1
    return found


def outside_values(hive: str) -> str:
    """The Hive with every value in single quotes taken out: what the statement itself says."""
    kept, at = [], 0
    while at < len(hive):
        if hive[at] == "'":
            _, at = _value(hive, at + 1)
            kept.append("''")
        else:
            kept.append(hive[at])
            at += 1
    return "".join(kept)


def _value(hive: str, at: int) -> tuple[str, int]:
    """The value that starts at `at`, just after its opening quote, and where it ends."""
    decoded = []
    while True:
        assert at < len(hive), "a value doesn't end"
        character = hive[at]
        if character == "'":
            return "".join(decoded), at + 1
        if character == "\\":
            escaped = hive[at + 1]
            decoded.append("\\" + escaped if escaped in "%_" else _CONTROL.get(escaped, escaped))
            at += 2
        else:
            decoded.append(character)
            at += 1
