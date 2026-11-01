"""Decisions: what only you decide about one table, which its Table reference shows made or not.

A Decision is one line of a table's Table reference that the Toolbox can't fill in itself,
open while it holds a `TODO:` or a `<...>`, or, for `location=`, while it is None:

- location: its `location=` line, the folder its files go in;
- Key: its `key=` line, the columns whose values name one row, or None when none do;
- guessed type: a column's line in `columns={...}` written "string" because nothing told the
  Toolbox its type;
- placeholder: any other `<...>` left in its code, as a Template leaves them, filled in by
  hand.

A `key=` line project.convert proposed, marked `# proposed`, is made, but an answer may
still change it. Any other `TODO:` line, such as the docstring's first line or
`does_not_add_up=`, is no Decision: it waits on nothing. You
answer each in the decisions cell of a Workflow's notebook,
`DECISIONS = {"mart_dev.x": {"location": "/data/...", "key": ["a"], "types": {"b": "int"}}}`,
and `answered_text` gives the Table reference with each answer written into the line it
answers. It never writes over any other line that is made already, as yours is once you
change it: the answer is kept unwritten, to name.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field

from .shared import escaped_literal

LOCATION = "location"
KEY = "key"
GUESSED_TYPE = "guessed type"
PLACEHOLDER = "placeholder"
# Every kind that waits for you, in the order check() names them.
KINDS = (LOCATION, KEY, GUESSED_TYPE, PLACEHOLDER)
# The kinds the decisions cell answers, each by its name there; a placeholder is filled in by
# hand.
ANSWERS = {LOCATION: "location", KEY: "key", GUESSED_TYPE: "types"}
ANSWERED_KINDS = tuple(ANSWERS)
# What a line still to decide holds.
OPEN = re.compile(r"TODO:|<[A-Z][A-Z_]*>")
PLACEHOLDER_WORD = re.compile(r"<[A-Z][A-Z_]*>")
# A column's line in columns={...}, such as         "team": "string",
COLUMN_LINE = re.compile(r'^        "(?P<column>[^"]+)": "(?P<type>[^"]*)",')
# What a Conversion writes after a column whose type nothing told it.
GUESSED = "  # TODO: guessed: nothing told its type"
# What new_table's Table reference holds for a Saved table's columns, until
# project.reference_from_logic writes them from its logic.
COLUMNS = "<COLUMNS>"
# A location= line no one has filled in, its TODO taken off or not.
NO_LOCATION = "location=None,"
# What a Conversion writes after the Key it worked out of a table's query: a Decision made,
# which an answer in the decisions cell may still change while the line keeps this mark.
PROPOSED = ('  # proposed from its query; if it is wrong, answer "key" in the decisions '
            "cell")


@dataclass(frozen=True)
class Decision:
    """One open Decision: its table, its kind, and what it is about: a guessed type's column,
    or a placeholder's <...>."""

    table: str
    kind: str
    subject: str = ""

    def question(self) -> str:
        """What it asks of you, as check() names it."""
        if self.kind == LOCATION:
            return "location: the folder its files go in"
        if self.kind == KEY:
            return "key: the columns whose values name one row, or None when none do"
        if self.kind == GUESSED_TYPE:
            return f'types: {self.subject}\'s type, written "string" as a guess'
        if self.subject == COLUMNS:
            return (f"{COLUMNS}, which project.reference_from_logic writes from its logic, "
                    "once that runs")
        return f"{self.subject}, to fill in by hand"


@dataclass
class Answered:
    """A Table reference's text once answers are written into it: each answer written, by its
    name in the cell, and a line naming each answer left unwritten, and why."""

    text: str
    written: list[str] = field(default_factory=list)
    unwritten: list[str] = field(default_factory=list)


def has_columns_written(text: str) -> bool:
    """Whether a Table reference's code lists its columns: not new_table's <COLUMNS>, nor an
    older Template's <COLUMN> and <COLUMN_TYPE>, left for its logic to write."""
    return COLUMNS[:-2] not in code_of(text)


def code_of(text: str) -> str:
    """A Python file's text but its module docstring, which may name a <...> or a TODO of its
    own; read by its quotes when the file doesn't parse yet, as a <...> left stops Python."""
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return _after_docstring(text)
    if ast.get_docstring(tree, clean=False) is None:
        return text
    return "\n".join(text.split("\n")[tree.body[0].end_lineno:])


def _after_docstring(text: str) -> str:
    """A file's text after a module docstring that opens it, read by its quotes."""
    if not text.startswith('"""'):
        return text
    closing = text.find('"""', 3)
    if closing < 0:
        return text
    return text[closing + 3:]


def kind_of(line: str) -> str:
    """The kind of Decision a line is, open or made, or "" for a line that is none."""
    stripped = line.strip()
    if stripped.startswith("location="):
        return LOCATION
    if stripped.startswith("key="):
        return KEY
    if COLUMN_LINE.match(line) and "TODO: guessed" in line:
        return GUESSED_TYPE
    if PLACEHOLDER_WORD.search(line):
        return PLACEHOLDER
    return ""


def is_open(line: str) -> bool:
    """Whether a line is a Decision still to make: it holds a TODO: or a <...>, or it is a
    location= left None; a comment is none, as the Aliases' examples are."""
    if line.strip().startswith("#"):
        return False
    return bool(OPEN.search(line)) or line.strip().startswith(NO_LOCATION)


def open_decisions(text: str, table: str, kinds: tuple[str, ...] = KINDS) -> list[Decision]:
    """Each Decision of `kinds` a Table reference's text leaves open, top to bottom."""
    still_open = []
    for line in code_of(text).split("\n"):
        kind = kind_of(line)
        if kind in kinds and is_open(line):
            still_open.append(Decision(table, kind, _subject_of(kind, line)))
    return still_open


def _subject_of(kind: str, line: str) -> str:
    """What a Decision's line is about: a guessed type's column, or the <...> a placeholder's
    line holds first."""
    if kind == GUESSED_TYPE:
        return COLUMN_LINE.match(line)["column"]
    if kind == PLACEHOLDER:
        return PLACEHOLDER_WORD.search(line).group()
    return ""


def todo_lines(text: str) -> list[str]:
    """Each TODO: line of a Table reference that is no Decision, such as its docstring's
    first line or does_not_add_up=: it waits on nothing."""
    code = code_of(text)
    docstring = text[:len(text) - len(code)]
    in_docstring = [line for line in docstring.splitlines() if "TODO:" in line]
    in_code = [line for line in code.splitlines()
               if "TODO:" in line and not kind_of(line) and not line.strip().startswith("#")]
    return [line.strip() for line in in_docstring + in_code]


def is_answered(decision: Decision, answer: dict[str, object]) -> bool:
    """Whether a table's answer in the decisions cell answers this Decision."""
    if decision.kind == GUESSED_TYPE:
        types = answer.get(ANSWERS[GUESSED_TYPE])
        return isinstance(types, dict) and decision.subject in types
    return decision.kind in ANSWERS and ANSWERS[decision.kind] in answer


def answered_text(text: str, answer: dict[str, object], reference: str) -> Answered:
    """A Table reference's text, at `reference`, with each open Decision the answer answers
    written into its line, and a key= line marked # proposed too, and each answer left
    unwritten named: one for any other Decision made already, a type for a column that wasn't
    guessed, or one that names no Decision."""
    answered = Answered(text)
    answered.unwritten = [f"{name}: not a Decision a Table reference asks; the decisions cell "
                          "answers location, key and types" for name in answer
                          if name not in ANSWERS.values()]
    lines = text.split("\n")
    for number, line in enumerate(lines):
        if not is_open(line) and PROPOSED not in line:
            continue
        written, name = _answered_line(line, answer)
        if written is not None:
            lines[number] = written
            answered.written.append(name)
    answered.text = "\n".join(lines)
    for name in (ANSWERS[LOCATION], ANSWERS[KEY]):
        if name in answer and name not in answered.written:
            answered.unwritten.append(
                f"{name}: kept as {reference} holds it, made already; to change it, edit its "
                f"{name}= line there (the decisions cell says {escaped_literal(answer[name])})")
    types = answer.get(ANSWERS[GUESSED_TYPE])
    if isinstance(types, dict):
        for column in types:
            if f"types: {column}" not in answered.written:
                answered.unwritten.append(f"types: {column} is no type the Toolbox guessed in "
                                          f"{reference}; to change it, edit its line there")
    return answered


def _answered_line(line: str, answer: dict[str, object]) -> tuple[str | None, str]:
    """An open Decision's line written with its answer, and the answer's name, or None when
    the answer doesn't answer it."""
    kind = kind_of(line)
    for named in (LOCATION, KEY):
        name = ANSWERS[named]
        if kind == named and name in answer:
            return f"    {name}={escaped_literal(answer[name])},", name
    types = answer.get(ANSWERS[GUESSED_TYPE])
    if kind != GUESSED_TYPE or not isinstance(types, dict):
        return None, ""
    column = _subject_of(kind, line)
    if column not in types:
        return None, ""
    written = f"        {escaped_literal(column)}: {escaped_literal(types[column])},"
    return written, f"types: {column}"
