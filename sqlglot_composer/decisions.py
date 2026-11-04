"""Decisions: what only you decide about one table, which its Table reference shows made or not.

A Decision is one line of a table's Table reference that the Toolbox can't fill in itself,
open while it holds a `TODO:` or a `<...>`, or, for `location=`, while it is None:

- location: its `location=` line, the folder its files go in;
- Key: its `key=` line, the columns whose values name one row, or None when none do;
- guessed type: a column's line in `columns={...}` written "string" because nothing told the
  Toolbox its type;
- tag: a Script tag's line in `TAGS = {...}`, open while it holds the tag itself, which a
  Conversion writes for each <PARM="NAME"/> in the table's Hive;
- placeholder: any other `<...>` left in its code, as a Template leaves them, filled in by
  hand.

A `key=` line project.convert proposed from a table's query, or project.reference_from_logic
from its logic, marked `# proposed`, is made, but an answer may still change it; so may an
answer change a tag's value again. Any other
`TODO:` line, such as the docstring's first line or `does_not_add_up=`, is no Decision: it
waits on nothing. You answer each in the decisions cell of a Workflow's notebook,
`DECISIONS = {"mart_dev.x": {"location": "/data/...", "key": ["a"], "types": {"b": "int"},
"tags": {"PERIOD_END": "'2026-10-31'"}}}`,
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
TAG = "tag"
PLACEHOLDER = "placeholder"
# Every kind that waits for you, in the order check() names them.
KINDS = (LOCATION, KEY, GUESSED_TYPE, TAG, PLACEHOLDER)
# What check() and step 1's report write for each answer still to give, in the DECISIONS
# they print to paste: an answer left so is no answer.
FILL_IN = "<FILL IN>"
# The decisions cell's name, as a Workflow's notebook holds it.
DECISIONS_NAME = "DECISIONS"
# The kinds the decisions cell answers, each by its name there; a placeholder is filled in by
# hand.
ANSWERS = {LOCATION: "location", KEY: "key", GUESSED_TYPE: "types", TAG: "tags"}
ANSWERED_KINDS = tuple(ANSWERS)
# What a line still to decide holds.
OPEN = re.compile(r"TODO:|<[A-Z][A-Z_]*>")
PLACEHOLDER_WORD = re.compile(r"<[A-Z][A-Z_]*>")
# A column's line in columns={...}, such as         "team": "string",
COLUMN_LINE = re.compile(r'^        "(?P<column>[^"]+)": "(?P<type>[^"]*)",')
# A Script tag's line in TAGS = {...}, as converting.tags_block writes it, such as
#     "PERIOD_END": "'2026-10-31'",  # bare, at daily.hql, line 4. Answer it with ...
# in three parts: its NAME and its value, each a Python string; and its comment, which says
# whether the tag stands bare or inside quotes, and where it first stands in the scripts.
_TAG_NAME = r'(?P<name>"(?:[^"\\]|\\.)*")'
_TAG_VALUE = r"(?P<value>.*?)"
_TAG_COMMENT = (r"(?P<comment># (?P<how>bare|inside quotes)(?:, at (?P<where>.*?))?\. "
                r"Answer .*)")
TAG_LINE = re.compile(f"^    {_TAG_NAME}: {_TAG_VALUE},  {_TAG_COMMENT}$")
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
# The same, after the Key project.reference_from_logic worked out of a table's logic, for a
# table new_table made with no query.
PROPOSED_FROM_LOGIC = ('  # proposed from its logic; if it is wrong, answer "key" in the '
                       "decisions cell")


@dataclass(frozen=True)
class Decision:
    """One open Decision: its table, its kind, and what it is about: a guessed type's column,
    a tag's NAME, or a placeholder's <...>; and, for a tag, where it is in the scripts, such as
    "daily.hql, line 4", when its line says, and whether it stands inside quotes."""

    table: str
    kind: str
    subject: str = ""
    where: str = ""
    quoted: bool = False

    def question(self) -> str:
        """What it asks of you, as check() names it."""
        if self.kind == LOCATION:
            return "location: the folder its files go in"
        if self.kind == KEY:
            return "key: the columns whose values name one row, or None when none do"
        if self.kind == GUESSED_TYPE:
            return f'types: {self.subject}\'s type, written "string" as a guess'
        if self.kind == TAG:
            return tag_question(self.subject, self.quoted, self.where)
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
    # A line for each tag answered before whose answer this one changed.
    changed: list[str] = field(default_factory=list)


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
    if TAG_LINE.match(line):
        return TAG
    if PLACEHOLDER_WORD.search(line):
        return PLACEHOLDER
    return ""


def is_open(line: str) -> bool:
    """Whether a line is a Decision still to make: it holds a TODO: or a <...>, it is a
    location= left None, or it is a Script tag's line in TAGS still holding the tag itself,
    <PARM="NAME"/>; a comment is none, as the Aliases' examples are."""
    if line.strip().startswith("#"):
        return False
    if kind_of(line) == TAG:
        return _tag_value_of(line) == f'<PARM="{_tag_name_of(line)}"/>'
    return bool(OPEN.search(line)) or line.strip().startswith(NO_LOCATION)


def _tag_name_of(line: str) -> str:
    """A tag line's NAME, as Python reads its string."""
    return ast.literal_eval(TAG_LINE.match(line)["name"])


def _tag_value_of(line: str) -> object:
    """The value a tag line holds, as Python reads it, or None when it doesn't read."""
    try:
        return ast.literal_eval(TAG_LINE.match(line)["value"])
    except (ValueError, SyntaxError):
        return None


def tag_names(text: str) -> list[str]:
    """The NAME of each Script tag a Table reference's text holds in its TAGS, answered or
    not."""
    return [_tag_name_of(line) for line in code_of(text).split("\n") if kind_of(line) == TAG]


def _tag_is_quoted(line: str) -> bool:
    """Whether a tag line's comment says its tag stands inside quotes."""
    return TAG_LINE.match(line)["how"] == "inside quotes"


def tag_question(name: str, quoted: bool, where: str = "") -> str:
    """What a Script tag's Decision asks, as check() names it: its NAME, then tag_hint's."""
    return f"tags: {name}, {tag_hint(name, quoted, where)}"


def tag_hint(name: str, quoted: bool, where: str = "") -> str:
    """How a Script tag's answer is written, saying where it stands: a bare tag's with the
    value's own quotes, a quoted one's with none."""
    at = f" at {where}" if where else ""
    if quoted:
        return (f'inside quotes{at}: answer what <PARM="{name}"/> stands for with no quotes, '
                'such as "2026-10-31" or "failed"')
    return (f'bare{at}: answer the Hive <PARM="{name}"/> stands for with its quotes, such as '
            "\"'2026-10-31'\", or a number, such as \"5\"")


# A date written with no quotes, which Hive reads as a subtraction: 2026-10-31 is 1985.
_BARE_DATE = re.compile(r"\d{4}-\d{1,2}-\d{1,2}")


def tag_answer_problem(value: object, quoted: bool) -> str | None:
    """Why a tag's answer can't be written where the tag stood, or None when it can: it must
    be Python text, not <FILL IN>; a bare tag's date needs its quotes, and a quoted tag's
    answer has none."""
    if value == FILL_IN:
        return still_to_fill_in("its answer")
    if not isinstance(value, str):
        return (f"is given {value!r}, a Python {type(value).__name__}: give the Hive as Python "
                "text, such as \"'2026-10-31'\" or \"5\" (a date typed with no quotes is "
                "a subtraction to Python)")
    if not value.strip():
        return "is given empty text: give the Hive the program put where the tag stood"
    if not quoted and _BARE_DATE.fullmatch(value.strip()):
        return (f"stands bare, so a date needs its own quotes, or Hive reads it as a "
                f"subtraction: answer \"'{value.strip()}'\"")
    if quoted and len(value) > 1 and value.startswith("'") and value.endswith("'"):
        return (f"stands inside quotes already, so its answer has none: answer "
                f"{escaped_literal(value[1:-1])}")
    return None


def open_decisions(text: str, table: str, kinds: tuple[str, ...] = KINDS) -> list[Decision]:
    """Each Decision of `kinds` a Table reference's text leaves open, top to bottom."""
    still_open = []
    for line in code_of(text).split("\n"):
        kind = kind_of(line)
        if kind in kinds and is_open(line):
            where, quoted = "", False
            if kind == TAG:
                where = TAG_LINE.match(line)["where"] or ""
                quoted = _tag_is_quoted(line)
            still_open.append(Decision(table, kind, _subject_of(kind, line), where, quoted))
    return still_open


def _subject_of(kind: str, line: str) -> str:
    """What a Decision's line is about: a guessed type's column, or the <...> a placeholder's
    line holds first."""
    if kind == GUESSED_TYPE:
        return COLUMN_LINE.match(line)["column"]
    if kind == TAG:
        return _tag_name_of(line)
    if kind == PLACEHOLDER:
        return PLACEHOLDER_WORD.search(line).group()
    return ""


def todo_lines(text: str) -> list[tuple[int, str]]:
    """Each TODO: line of a Table reference that is no Decision, such as its docstring's
    first line or does_not_add_up=, by its number in the file, from 1, and its text, a
    docstring's without its quote marks: it waits on nothing."""
    # The lines before its code are its docstring's: a TODO there is never a Decision.
    docstring_lines = text.count("\n") - code_of(text).count("\n")
    found = []
    for number, line in enumerate(text.split("\n"), 1):
        if "TODO:" not in line:
            continue
        if number <= docstring_lines:
            found.append((number, line.strip().strip('"').strip()))
        elif not kind_of(line) and not line.strip().startswith("#"):
            found.append((number, line.strip()))
    return found


def still_to_fill_in(what: str) -> str:
    """What a report says of an answer left <FILL IN>, as check() printed it: `what`, such as
    "its answer", is still to write."""
    return f"is still {FILL_IN}: write {what} there"


def is_answered(decision: Decision, answer: dict[str, object]) -> bool:
    """Whether a table's answer in the decisions cell answers this Decision: one left
    <FILL IN>, as check() prints it to paste, doesn't."""
    if decision.kind in (GUESSED_TYPE, TAG):
        answers = answer.get(ANSWERS[decision.kind])
        return (isinstance(answers, dict) and decision.subject in answers
                and answers[decision.subject] != FILL_IN)
    return (decision.kind in ANSWERS and ANSWERS[decision.kind] in answer
            and answer[ANSWERS[decision.kind]] != FILL_IN)


def answered_text(text: str, answer: dict[str, object], reference: str) -> Answered:
    """A Table reference's text, at `reference`, with each open Decision the answer answers
    written into its line, a key= line marked # proposed and a tag's line too, answered or not,
    and each answer left unwritten named: one for any other Decision made already, a type for
    a column that wasn't guessed, or a tag's answer in a form that can't stand where the tag
    stood. An answer that matches no Decision at all, project.write_decisions refuses before
    this runs."""
    answered = Answered(text)
    lines = text.split("\n")
    for number, line in enumerate(lines):
        changeable = (PROPOSED in line or PROPOSED_FROM_LOGIC in line
                      or kind_of(line) == TAG)
        if not is_open(line) and not changeable:
            continue
        written, name = _answered_line(line, answer)
        if written is None:
            continue
        if kind_of(line) == TAG and not is_open(line) and written != line:
            answered.changed.append(f"tags: {_tag_name_of(line)} is "
                                    f"{_tag_value_of(written)} now, in place of "
                                    f"{_tag_value_of(line)}")
        lines[number] = written
        answered.written.append(name)
    answered.text = "\n".join(lines)
    answered.unwritten += _unwritten(answer, answered.written, reference)
    answered.unwritten += _tags_unwritten(answer, text)
    return answered


def _unwritten(answer: dict[str, object], written: list[str], reference: str) -> list[str]:
    """A line naming each answer `answer` gives that wasn't written into `reference`, and
    why."""
    unwritten = []
    for name in (ANSWERS[LOCATION], ANSWERS[KEY]):
        if answer.get(name) == FILL_IN:
            unwritten.append(f"{name} {still_to_fill_in('its answer')}")
        elif name in answer and name not in written:
            unwritten.append(
                f"{name}: kept as {reference} holds it, made already; to change it, edit its "
                f"{name}= line there (the decisions cell says {escaped_literal(answer[name])})")
    types = answer.get(ANSWERS[GUESSED_TYPE])
    if isinstance(types, dict):
        for column, value in types.items():
            if value == FILL_IN:
                unwritten.append(f"types: {column} {still_to_fill_in('its type')}")
            elif f"types: {column}" not in written:
                unwritten.append(f"types: {column} is no type the Toolbox guessed in "
                                 f"{reference}; to change it, edit its line there")
    return unwritten


def _tags_unwritten(answer: dict[str, object], text: str) -> list[str]:
    """A line naming each tag answer left unwritten, and why: "tags" not a dict, or an answer
    in a form that can't stand where its tag stood, its line in the Table reference's text,
    `text`."""
    tags = answer.get(ANSWERS[TAG])
    if ANSWERS[TAG] not in answer:
        return []
    if not isinstance(tags, dict):
        return [f"tags: give a dict of each tag's answer by its NAME, such as "
                f"{{\"PERIOD_END\": \"'2026-10-31'\"}}, not {tags!r}"]
    tag_lines = {_tag_name_of(line): line for line in text.split("\n")
                 if kind_of(line) == TAG}
    unwritten = []
    for name, value in tags.items():
        if name not in tag_lines:
            continue  # project.write_decisions refuses it first
        problem = tag_answer_problem(value, _tag_is_quoted(tag_lines[name]))
        if problem is not None:
            unwritten.append(f"tags: {name} {problem}")
    return unwritten


def _answered_line(line: str, answer: dict[str, object]) -> tuple[str | None, str]:
    """An open Decision's line written with its answer, and the answer's name, or None when
    the answer doesn't answer it."""
    kind = kind_of(line)
    for named in (LOCATION, KEY):
        name = ANSWERS[named]
        if kind == named and name in answer and answer[name] != FILL_IN:
            return f"    {name}={escaped_literal(answer[name])},", name
    if kind == TAG:
        return _answered_tag(line, answer.get(ANSWERS[TAG]))
    types = answer.get(ANSWERS[GUESSED_TYPE])
    if kind != GUESSED_TYPE or not isinstance(types, dict):
        return None, ""
    column = _subject_of(kind, line)
    if column not in types or types[column] == FILL_IN:
        return None, ""
    written = f"        {escaped_literal(column)}: {escaped_literal(types[column])},"
    return written, f"types: {column}"


def _answered_tag(line: str, tags: object) -> tuple[str | None, str]:
    """A tag's line written with its answer, its comment kept, and the answer's name, or None
    when `tags` gives it none, or one in a form that can't stand where the tag stood."""
    name = _tag_name_of(line)
    if not isinstance(tags, dict) or name not in tags:
        return None, ""
    value = tags[name]
    if tag_answer_problem(value, _tag_is_quoted(line)) is not None:
        return None, ""
    found = TAG_LINE.match(line)
    return (f"    {found['name']}: {escaped_literal(value)},  {found['comment']}",
            f"tags: {name}")


def paste_lines(still_open: list[Decision]) -> list[str]:
    """The lines of a whole DECISIONS = {...} to paste into a decisions cell: each Decision of
    `still_open` the cell answers, by its table, each value still to give <FILL IN>, a guessed
    type's proposal "string", and a comment beside each saying what to write."""
    by_table: dict[str, list[Decision]] = {}
    for decision in still_open:
        if decision.kind in ANSWERS:
            by_table.setdefault(decision.table, []).append(decision)
    lines = [f"{DECISIONS_NAME} = {{"]
    for table, decided in by_table.items():
        lines.append(f"    {escaped_literal(table)}: {{")
        kinds = {decision.kind for decision in decided}
        if LOCATION in kinds:
            lines.append(f'        "location": "{FILL_IN}",  # the folder its files go in')
        if KEY in kinds:
            lines.append(f'        "key": "{FILL_IN}",  # the columns that name one row, such '
                         'as ["job_id", "dt"], or None when none do')
        lines += _types_lines([each for each in decided if each.kind == GUESSED_TYPE])
        lines += _tags_lines([each for each in decided if each.kind == TAG])
        lines.append("    },")
    return [*lines, "}"]


def _types_lines(guessed: list[Decision]) -> list[str]:
    """The lines of one table's "types" in DECISIONS to paste: each guessed type's proposal,
    "string"."""
    if not guessed:
        return []
    lines = [f'        "{ANSWERS[GUESSED_TYPE]}": {{']
    for decision in guessed:
        lines.append(f"            {escaped_literal(decision.subject)}: \"string\",  # "
                     'guessed: its type, if not string, such as "bigint"')
    return [*lines, "        },"]


def _tags_lines(tags: list[Decision]) -> list[str]:
    """The lines of one table's "tags" in DECISIONS to paste: each tag's <FILL IN>, with how
    its answer is written."""
    if not tags:
        return []
    lines = [f'        "{ANSWERS[TAG]}": {{']
    for decision in tags:
        hint = tag_hint(decision.subject, decision.quoted, decision.where)
        lines.append(f'            {escaped_literal(decision.subject)}: "{FILL_IN}",  # {hint}')
    return [*lines, "        },"]
