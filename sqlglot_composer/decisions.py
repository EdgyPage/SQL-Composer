"""Decisions: what only you decide about one table, which its Table reference shows made or not.

A Decision is one line of a table's Table reference that the Toolbox can't fill in itself,
open while it holds a `TODO:` or a `<...>`, or, for `location=`, while it is None:

- location: its `location=` line, the folder its files go in;
- Key: its `key=` line, the columns whose values name one row, or None when none do;
- guessed type: a column's line in `columns={...}` written "string" because nothing told the
  Toolbox its type;
- tag: a Script tag's line in `TAGS = {...}`, open while it holds the tag itself, which a
  Conversion writes for each <PARM="NAME"/> in the table's Hive;
- name: its `NAME = ...` line, the name proposed for a table a workbook's final became, as a
  pivot keeping Excel's default name (Toolbox 8.9), which an answer renames;
- source: a line of its `SOURCES = {...}`, the database table each source of the workbook it
  reads samples, a Table of typed rows or a plain range, proposed from its name (Toolbox 8.9),
  `ops.table1` for Table1, whatever the warehouse names it;
- Pivot filter: a line of its `PIVOT_FILTERS = {...}`, what the PivotTable it was made from
  leaves out, by the filter's field, kept as converted until answered (Toolbox 8.9), its other
  answers keeping every slice: "fold", "batch" or "tables";
- kind: its `KIND = ...` line, whether it is a Rebuilt table, which each write replaces whole,
  or a History table, which each write adds to and so needs a Seed (Toolbox 8.10), proposed
  from its write where the write says, open until an answer accepts or changes it;
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

`DECISIONS["all_tables"]` (Toolbox 8.4) answers for every table the Workflow's notebook names:
"seed", the limits of the seed's copy, "tags", each for the tables that hold it, and "kind"
(8.10), for each table with a KIND line.
`table_answer` gives one table's answer: all_tables' first, then the table's own over it, kind
by kind and, for tags, tag by tag. A Key, a type and a location are each table's own: the
folder every table's own goes under is a Database setting since 8.5, "location_root" in
admin/databases.py, which places a table with no location of its own as it is written.
"""

from __future__ import annotations

import ast
import datetime
import re
from collections.abc import Callable
from dataclasses import dataclass, field, replace
from enum import StrEnum

from .shared import escaped_literal, in_words, split_table_name
from .writing import tag_value_problem

LOCATION = "location"
KEY = "key"
GUESSED_TYPE = "guessed type"
TAG = "tag"
NAME = "name"
SOURCE = "source"
PIVOT_FILTER = "Pivot filter"
TABLE_KIND = "table kind"
PLACEHOLDER = "placeholder"
# Every kind that waits for you, in the order check() names them.
KINDS = (LOCATION, KEY, GUESSED_TYPE, TAG, NAME, SOURCE, PIVOT_FILTER, TABLE_KIND, PLACEHOLDER)
# What check() and step 1's report write for each answer still to give, in the DECISIONS
# they print to paste: an answer left so is no answer.
FILL_IN = "<FILL IN>"
# The decisions cell's name, as a Workflow's notebook holds it.
DECISIONS_NAME = "DECISIONS"
# The kinds the decisions cell answers, each by its name there; a placeholder is filled in by
# hand.
ANSWERS = {LOCATION: "location", KEY: "key", GUESSED_TYPE: "types", TAG: "tags", NAME: "name",
           SOURCE: "sources", PIVOT_FILTER: "pivot_filters", TABLE_KIND: "kind"}
ANSWERED_KINDS = tuple(ANSWERS)
# A table's name proposed for a workbook's final, as a Conversion writes it in the table's
# Table reference above its Aliases, open while it holds TODO: (Toolbox 8.9), such as
#     NAME = "pivot"  # TODO: proposed for PivotTable1 of runs.xlsx
NAME_LINE = re.compile(r'^NAME = "(?P<name>[a-z0-9_]*)"  # (?P<todo>TODO: )?(?:proposed )?'
                       r"(?P<what>.*)$")
NAME_COMMENT = (
    "# The name of this table, proposed for its final in the workbook. Answer \"name\" in the",
    '# decisions cell: "proposed" keeps it; a name of your own renames this table, and its',
    "# Total Row's table, if it has one, with it.",
)
# The database table each source a workbook's final reads samples, a Table of typed rows or a
# plain range, proposed from its name, a line each in SOURCES, open while it holds TODO:
# (Toolbox 8.9, tickets 07 and 20), such as
#     "ops.table1": "ops.table1",  # TODO: proposed: the database table Table1 of runs.xlsx
#     samples (the comment on one line)
#     "ops.runs": "ops.runs",  # TODO: proposed: the database table Runs!A1:F10 samples
SOURCES_START = "SOURCES = {"
SOURCE_LINE = re.compile(r'^    "(?P<proposed>[\w.]+)": "(?P<table>[\w.]+)",  '
                         r"# (?P<todo>TODO: proposed: )?the database table (?P<what>.+) "
                         r"samples$")
SOURCES_COMMENT = (
    "# The database table each Table or range of the workbook it reads samples, proposed from",
    "# its name, which needn't be the one your warehouse gives it. Answer \"sources\" in the",
    '# decisions cell with the table it samples, in any database, such as {"ops.table1":',
    '# "ops.job_runs"}, or {"ops.table1": "proposed"} to keep it.',
)


class PivotFilterAnswer(StrEnum):
    """Each answer a Pivot filter's Decision takes (Toolbox 8.9): keep the filter as
    converted, the selection alone; or keep every value, by folding its column into what one
    row is, by writing one batch per value, each run its value, into a Partition of its own,
    or by making a table per value. "proposed" answers KEEP."""

    KEEP = "keep"
    FOLD = "fold"
    BATCH = "batch"
    TABLES = "tables"


# Each Pivot filter of the PivotTable a table was made from, by its field, a line each in
# PIVOT_FILTERS, kept as converted and open while it holds TODO: (Toolbox 8.9), such as
#     "status": "keep",  # TODO: proposed: the slicer on status keeps FAILED and SUCCESS. ...
PIVOT_FILTERS_START = "PIVOT_FILTERS = {"
PIVOT_FILTER_LINE = re.compile(r'^    (?P<field>"(?:[^"\\]|\\.)*"): '
                               rf'"(?P<answer>{"|".join(PivotFilterAnswer)})",  '
                               r"# (?P<todo>TODO: proposed: )?(?P<what>.+)$")
PIVOT_FILTERS_COMMENT = (
    "# What the PivotTable this table was made from leaves out: each Pivot filter, by its",
    '# field, a Decision. Answer "pivot_filters" in the decisions cell: "keep" keeps the',
    '# selection as converted; "fold", "batch" or "tables" keeps every value instead, as its',
    "# checklist says.",
)


class TableKind(StrEnum):
    """Each kind a Saved table is (Toolbox 8.10), by what each write does to the rows already
    there: a Rebuilt table is replaced whole by each write; a History table keeps them, each
    write adding rows or replacing some, such as one day's Partition, so it needs a Seed."""

    REBUILT = "rebuilt"
    HISTORY = "history"


# A Saved table's kind, Rebuilt or History, a line of its Table reference above its Aliases,
# as convert and new_table write it, open while it holds TODO: (Toolbox 8.10), its proposal and
# why in the comment, or why nothing is proposed, such as
#     KIND = "history"  # TODO: proposed history: its INSERT OVERWRITE replaces one Partition
#     KIND = None  # TODO: nothing proposed: its INSERT OVERWRITE fills Partitions from ...
# Answered, its TODO is ANSWERED_KIND and the rest kept, so check() never lists it as a line
# marked # proposed, as in
#     KIND = "rebuilt"  # answered, proposed history: its INSERT OVERWRITE replaces one ...
# This line is the one place a table's kind is stored; table_kind reads it.
ANSWERED_KIND = "answered, "
NOTHING_PROPOSED = "nothing proposed"
_EACH_KIND = "|".join(TableKind)
KIND_LINE = re.compile(rf'^KIND = (?P<value>"(?:{_EACH_KIND})"|None)  '
                       rf"# (?:(?P<todo>TODO: )|{ANSWERED_KIND})"
                       rf"(?P<what>(?:proposed (?P<proposal>{_EACH_KIND})|{NOTHING_PROPOSED}): "
                       r"(?P<why>.+))$")
KIND_COMMENT = (
    '# Rebuilt or History: "rebuilt" if each write replaces the whole table; "history" if',
    "# each write keeps the rows already there, adding rows or replacing some, such as one",
    "# day's Partition, so the table needs its past rows loaded first, its Seed. Answer",
    '# "kind" in the decisions cell: "proposed" accepts the kind proposed below.',
)
# The decisions cell's answer for every table its Workflow's notebook names, beside each
# table's own (Toolbox 8.4), and the kinds it answers, each by its name there: "proposed" for
# the Key, accepting each table's proposed one (8.5), the limits of the seed's copy, Script
# tags, and the kind, Rebuilt or History, or "proposed", accepting each table's proposed one
# (8.10). A location is placed under its Database's location_root, a Database setting (8.5).
ALL_TABLES = "all_tables"
SEED = "seed"
ALL_TABLES_ANSWERS = (ANSWERS[KEY], SEED, ANSWERS[TAG], ANSWERS[TABLE_KIND])
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
# The answer a tag's comment proposes, as Python, at its end, and the call that writes it
# first, where it is a Run value project.new_run_value writes (Toolbox 8.9), as in
#     ... Answer it with the value each write inserts; proposed: hivevar("STATUS", ...)
TAG_PROPOSED = "; proposed: "
TAG_PROPOSAL = re.compile(rf"{re.escape(TAG_PROPOSED)}(?P<proposal>.+?)"
                          r"(?:, from (?P<set_up>project\.new_run_value\(.*\)))?$")
# The line a pasted DECISIONS needs above it for a Hivevar it proposes.
PROPOSED_HIVEVAR_IMPORT = "from sqlglot_composer import hivevar  # for a Hivevar proposed below"
# What a Conversion writes after a column whose type nothing told it.
GUESSED = "  # TODO: guessed: nothing told its type"
# What new_table's Table reference holds for a Saved table's columns, until
# project.reference_from_logic writes them from its logic.
COLUMNS = "<COLUMNS>"
# The line TAGS starts on in a Table reference, and the mark on the line above TAGS or SEED
# that imports a Run value's function for them (Toolbox 8.4).
TAGS_START = "TAGS = {"
# A Table reference's seed limits, SEED, as a Conversion writes them for a table that reads
# itself, and the line they start on: the Partitions its seed() copies (Toolbox 8.4).
SEED_START = "SEED = {"
SEED_COMMENT = (
    "# The Partitions seed() copies from the original, by partition column: {} copies them",
    '# all. Answer "seed" in the decisions cell, such as {"dt": {"from": "2026-01-01"}}.',
)
RUN_VALUE_MARK = "  # a Run value, for TAGS or SEED"
# The import above TAGS while it holds a Hivevar (Toolbox 8.7), and how each one's value
# starts in TAGS.
HIVEVAR_IMPORT = "from sqlglot_composer import hivevar  # for a Hivevar in TAGS"
HIVEVAR_CALL = "hivevar("
RUN_VALUE_IMPORT = re.compile(
    rf"from [\w.]+ import (?P<function>\w+){re.escape(RUN_VALUE_MARK)}")
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
# What project.add_references writes on a key= line for the Key it worked out of a table's
# rows and checked with check_key (Toolbox 8.5): a Decision still open, its proposal in the
# comment, until an answer accepts it, as in
#     key=None,  # TODO: proposed ["run_id"], checked: accept it in the decisions cell
PROPOSED_FROM_ROWS = "  # TODO: proposed "
# What follows the Key a Pivot filter's answer proposes again, still open, where the Key you
# answered no longer fits what one row is (Toolbox 8.9), as in
#     key=None,  # TODO: proposed ["job_id", "status"] from its query, as its Pivot ...
KEY_FROM_QUERY = "query"
# A key= line holding a Key, as an answer writes it, or by hand.
_ANSWERED_KEY = re.compile(r"^    key=(?P<value>.*?),(?:  #.*)?$")
PROPOSED_FROM_QUERY_AGAIN = (" from its query, as its Pivot filters' answers changed what one "
                             "row is: accept it in the decisions cell")
_PROPOSED_IN_COMMENT = re.compile(r"# TODO: proposed (?P<key>\[[^\]]*\])")
_KEY_VALUE = re.compile(r"^\s*key=(?P<value>.*?),  #")
# A line the Toolbox proposed and that is made, which check() names until it is accepted: a
# Key from a table's query or its logic, or a Table reference's first line or does_not_add_up=
# that project.add_references proposed (Toolbox 8.5).
PROPOSED_MARK = re.compile(r"#\s*proposed\b")
# The answer, under "all_tables" or a table's own name, that accepts each table's proposed
# Key as it is, written as if typed.
ACCEPT_PROPOSED = "proposed"
# A Table reference's first line, what one row is, as write_table_reference leaves it to
# fill in, and the mark after it once project.add_references proposed it from the Key.
ROW_TODO = "TODO: say in one line what one row is."
PROPOSED_ROW = "  # proposed from its Key"


@dataclass(frozen=True)
class Decision:
    """One open Decision: its table, its kind, and what it is about: a guessed type's column,
    a tag's NAME, a placeholder's <...>, or a Key's proposal; and, for a tag, where it is in
    the scripts, such as "daily.hql, line 4", when its line says, whether it stands inside
    quotes, and the answer proposed for it, as Python, where one is (Toolbox 8.9); for a Key,
    "query" where its proposal is from its query, made again."""

    table: str
    kind: str
    subject: str = ""
    where: str = ""
    quoted: bool = False
    proposal: str = ""
    set_up: str = ""

    def question(self) -> str:
        """What it asks of you, as check() names it."""
        if self.kind == LOCATION:
            return "location: the folder its files go in"
        if self.kind == KEY:
            return key_question(self.subject, self.where)
        if self.kind == GUESSED_TYPE:
            return f'types: {self.subject}\'s type, written "string" as a guess'
        if self.kind in LINE_KINDS:
            return self._named_question()
        if self.subject == COLUMNS:
            return (f"{COLUMNS}, which project.reference_from_logic writes from its logic, "
                    "once that runs")
        return f"{self.subject}, to fill in by hand"

    def _named_question(self) -> str:
        """What a Decision about a named thing asks: a Script tag's value, a table's name
        proposed, the database table a range samples, or a Pivot filter's answer."""
        if self.kind == TAG:
            return tag_question(self.subject, self.quoted, self.where, self.proposal)
        if self.kind == NAME:
            return (f'name: {self.subject}, proposed {self.where}: keep it with "proposed", '
                    "or answer a name of your own, which renames the table")
        if self.kind == PIVOT_FILTER:
            return (f"pivot_filters: {self.subject}, a Pivot filter. {_sentence(self.where)}. "
                    f'Answer "{PivotFilterAnswer.KEEP}" to keep its selection as converted, '
                    f'or "{PivotFilterAnswer.FOLD}", "{PivotFilterAnswer.BATCH}" or '
                    f'"{PivotFilterAnswer.TABLES}" to keep every value instead, as its '
                    "checklist says")
        if self.kind == TABLE_KIND:
            return kind_question(self.subject, self.where)
        return (f"sources: {self.subject}, proposed as the database table {self.where} "
                'samples: keep it with "proposed", or answer the table it samples')


def _sentence(text: str) -> str:
    """Text as a sentence starts: its first letter in capitals."""
    return text[:1].upper() + text[1:]


def kind_question(proposal: str, why: str) -> str:
    """What a table's kind asks, as check() names it: to accept `proposal`, "rebuilt" or
    "history", proposed from its write, saying why; or, with none, to answer it, saying why
    nothing was proposed. `why` is its KIND line's comment after "proposed <kind>: " or
    "nothing proposed: "."""
    answer = (f'"{TableKind.REBUILT}" if each write replaces the whole table, '
              f'"{TableKind.HISTORY}" if it keeps the rows already there')
    if proposal:
        return (f"kind: proposed a {_kind_words(proposal)}, as {why}: accept it with "
                f'"{ACCEPT_PROPOSED}", or answer {answer}')
    return f"kind: Rebuilt or History table, nothing proposed, as {why}: answer {answer}"


def _kind_words(kind: str) -> str:
    """A kind as the glossary names it: "Rebuilt table" or "History table"."""
    return f"{_sentence(kind)} table"


def key_question(proposal: str, made_from: str = "") -> str:
    """What an open Key's Decision asks, as check() names it: to accept its proposal, as
    Python, when the Toolbox proposed one, checked on the table's rows or, `made_from` "query",
    worked out of its query again, as a Pivot filter's answer changed what one row is; or else
    to answer it."""
    answer = "the columns whose values name one row, or None when none do"
    if proposal and made_from == KEY_FROM_QUERY:
        return (f"key: proposed {proposal} from its query, as its Pivot filters' answers "
                f"changed what one row is: accept it, or answer {answer}")
    if proposal:
        return (f"key: proposed {proposal}, which check_key found holds: accept it, or "
                f"answer {answer}")
    return f"key: {answer}"


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
    for kind, read in LINE_KINDS.items():
        if read.line.match(line):
            return kind
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
        return _tag_value_of(line) == f'<PARM="{tag_name_of(line)}"/>'
    return bool(OPEN.search(line)) or line.strip().startswith(NO_LOCATION)


def _tag_value_text(line: str) -> str:
    """A tag line's value as written: Hive text in quotes, or a Run value's function's
    name."""
    return TAG_LINE.match(line)["value"]


def _tag_answer_shown(line: str) -> str:
    """A tag line's answer as a report says it: the Hive text, or a Run value's function's
    name."""
    value = _tag_value_of(line)
    return value if isinstance(value, str) else _tag_value_text(line)


def _with_run_value_imports(text: str, answer: dict[str, object]) -> str:
    """A Table reference's text with an import above TAGS, or above SEED, for each Run value's
    function its TAGS or SEED names, a Hivevar's default among them, and none for one they no
    longer name; and the import of hivevar while TAGS holds a Hivevar, and none once it
    doesn't."""
    functions = [*_functions_in(answer.get(ANSWERS[TAG])), *_functions_in(answer.get(SEED))]
    lines = text.split("\n")
    values = [_tag_value_text(line) for line in lines if kind_of(line) == TAG]
    named = set(values)
    hivevars = [value for value in values if value.startswith(HIVEVAR_CALL)]
    for value in hivevars:
        named |= set(re.findall(r"\w+", value))
    seed_line = _seed_line_number(lines)
    if seed_line is not None:
        named |= set(re.findall(r"\w+", lines[seed_line]))
    lines = [line for line in lines if not _is_unused_import(line, named, bool(hivevars))]
    imports = [run_value_import(function) for function in functions]
    if hivevars:
        imports.append(HIVEVAR_IMPORT)
    for imported in imports:
        starts = [number for number, line in enumerate(lines)
                  if line.startswith((TAGS_START, SEED_START.removesuffix("{")))]
        if imported not in lines and starts:
            at = starts[0]
            while at > 0 and lines[at - 1].startswith("#"):  # above TAGS' own comment
                at -= 1
            lines.insert(at, imported)
    return "\n".join(lines)


def _functions_in(value: object) -> list[Callable[..., object]]:
    """Each function an answer holds, however deep in its dicts and lists, a Hivevar's default
    among them."""
    if callable(value):
        return [value]
    if _is_hivevar(value):
        return _functions_in(value.default)
    parts: list[object] = []
    if isinstance(value, dict):
        parts = list(value.values())
    elif isinstance(value, (list, tuple)):
        parts = list(value)
    functions = []
    for part in parts:
        functions += _functions_in(part)
    return functions


def _is_hivevar(value: object) -> bool:
    """Whether a tag's answer is a Hivevar, as hivevar(...) makes one (Toolbox 8.7)."""
    # tables.py imports this file, and run_values.py imports tables.py: it is read here.
    from .run_values import Hivevar

    return isinstance(value, Hivevar)


def seed_line(text: str) -> str | None:
    """A Table reference's SEED line, or None when it has none."""
    lines = text.split("\n")
    number = _seed_line_number(lines)
    return None if number is None else lines[number]


def with_run_value_imports_kept(text: str, kept_from: str) -> str:
    """A prod copy's Table reference text with each Run value's import of `kept_from`, the one
    promoted before, whose function its TAGS or SEED names, and none it no longer names."""
    lines = text.split("\n")
    imported = [line for line in kept_from.split("\n") if line.endswith(RUN_VALUE_MARK)]
    starts = [number for number, line in enumerate(lines)
              if line.startswith((TAGS_START, SEED_START.removesuffix("{")))]
    if starts:
        lines[starts[0]:starts[0]] = [line for line in imported if line not in lines]
    return _with_run_value_imports("\n".join(lines), {})


def _seed_line_number(lines: list[str]) -> int | None:
    """Where a Table reference's SEED line is among its lines, or None when it has none."""
    for number, line in enumerate(lines):
        if line.startswith(SEED_START.removesuffix("{")):
            return number
    return None


def _with_seed_written(text: str, answer: dict[str, object]) -> tuple[str, bool]:
    """A Table reference's text with its SEED line holding the answer's seed limits, and
    whether it was written: a table that doesn't read itself has no SEED line."""
    limits = answer.get(SEED)
    lines = text.split("\n")
    at = _seed_line_number(lines)
    if not isinstance(limits, dict) or at is None:
        return text, False
    lines[at] = SEED_START.removesuffix("{") + seed_python(limits)
    return "\n".join(lines), True


def seed_python(value: object) -> str:
    """Seed limits as a Table reference writes them: text and dates in quotes, numbers as they
    are, and a Run value's function by its name, which an import above SEED brings in."""
    if callable(value):
        return value.__qualname__
    if isinstance(value, dict):
        return "{" + ", ".join(f"{escaped_literal(str(key))}: {seed_python(each)}"
                               for key, each in value.items()) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(seed_python(each) for each in value) + "]"
    if isinstance(value, datetime.date):
        return escaped_literal(value.isoformat())
    if isinstance(value, str):
        return escaped_literal(value)
    return repr(value)


def seed_answer(answers: dict[str, dict[str, object]], table: str, text: str,
                answer: dict[str, object]) -> dict[str, object]:
    """One table's answer with its seed limits as they apply to it: its own as given, which
    the refusals check first; all_tables' for the partition columns it has; none for a table
    that doesn't read itself, which has no seed."""
    if not isinstance(answer.get(SEED), dict):
        return answer
    partitions = seed_partitions(text)
    own = answers.get(table)
    if partitions is None:
        return {kind: value for kind, value in answer.items() if kind != SEED}
    if isinstance(own, dict) and SEED in own:
        return answer
    limits = {column: limit for column, limit in answer[SEED].items()
              if column in partitions}
    return {**answer, SEED: limits}


def seed_partitions(text: str) -> list[str] | None:
    """The partition columns a Table reference's text names, for its seed limits; None when
    it has no SEED, as a table that doesn't read itself has none."""
    if not any(line.startswith(SEED_START.removesuffix("{")) for line in text.split("\n")):
        return None
    found = re.search(r"partitioned_by=\[([^\]]*)\]", text)
    return re.findall(r'"([^"]+)"', found.group(1)) if found else []


def _is_unused_import(line: str, named: set[str], holds_a_hivevar: bool) -> bool:
    """Whether a line is an import above TAGS or SEED nothing uses any more: a Run value's of a
    function neither names, or hivevar's when TAGS holds no Hivevar."""
    if line == HIVEVAR_IMPORT:
        return not holds_a_hivevar
    return _is_unused_run_value_import(line, named)


def _is_unused_run_value_import(line: str, named: set[str]) -> bool:
    """Whether a line is an import run_value_import wrote of a function neither TAGS nor
    SEED names any more."""
    found = RUN_VALUE_IMPORT.fullmatch(line)
    return found is not None and found["function"] not in named


def tag_name_of(line: str) -> str:
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
    return [tag_name_of(line) for line in code_of(text).split("\n") if kind_of(line) == TAG]


def _tag_is_quoted(line: str) -> bool:
    """Whether a tag line's comment says its tag stands inside quotes."""
    return TAG_LINE.match(line)["how"] == "inside quotes"


def tag_question(name: str, quoted: bool, where: str = "", proposal: str = "") -> str:
    """What a Script tag's Decision asks, as check() names it: its NAME, the answer proposed
    for it, where one is, then tag_hint's."""
    if proposal:
        return (f"tags: {name}, proposed {proposal}: accept it, or answer another, "
                f"{tag_hint(quoted, where)}")
    return f"tags: {name}, {tag_hint(quoted, where)}"


def tag_proposal(line: str) -> str:
    """The answer a Script tag's line in TAGS proposes, as Python, such as
    hivevar("STATUS", default="FAILED"), or "" where it proposes none (Toolbox 8.9)."""
    found = TAG_PROPOSAL.search(TAG_LINE.match(line)["comment"])
    return found["proposal"] if found else ""


def tag_set_up(line: str) -> str:
    """The call a Script tag's proposal needs run first, such as project.new_run_value(...),
    which writes the Run value it names; "" where it needs none."""
    found = TAG_PROPOSAL.search(TAG_LINE.match(line)["comment"])
    if found is None or found["set_up"] is None:
        return ""
    return found["set_up"]


def tag_proposal_comment(proposal: str, set_up: str = "") -> str:
    """What a Script tag's line in TAGS says after how its answer is written, proposing an
    answer, and the call it needs run first, where it needs one."""
    if set_up:
        return f"{TAG_PROPOSED}{proposal}, from {set_up}"
    return f"{TAG_PROPOSED}{proposal}"


def _proposals_set_up(still_open: list[Decision]) -> list[str]:
    """The lines a pasted DECISIONS needs above it for each answer it proposes: the import of
    hivevar for a Hivevar, and, for a Run value, the call that writes it and its import."""
    lines = []
    for decision in still_open:
        if decision.set_up:
            function = decision.proposal
            lines += [decision.set_up,
                      f"from building_blocks.run_values import {function}  # its Run value"]
        elif decision.proposal.startswith(HIVEVAR_CALL):
            lines.append(PROPOSED_HIVEVAR_IMPORT)
    return list(dict.fromkeys(lines))


def tag_hint(quoted: bool, where: str = "") -> str:
    """How a Script tag's answer is written, saying where it stands: a bare tag's with the
    value's own quotes, a quoted one's with none."""
    at = f" at {where}" if where else ""
    if quoted:
        return f'inside quotes{at}: the value with no quotes, such as "failed"'
    return (f"bare{at}: the value with its own quotes, such as \"'2026-10-31'\", or a number, "
            'such as "5"')


def tag_answer_problem(value: object, quoted: bool) -> str | None:
    """Why a tag's answer can't be written where the tag stood, or None when it can: it must
    be Python text, not <FILL IN>, a Run value's function a Table reference can import
    (run_value_problem), or a Hivevar whose default is either; a bare tag's text is one value
    of a kind a program puts there (writing.tag_value_problem), and a quoted tag's has no
    quotes of its own."""
    if is_left_to_fill_in(value):
        return still_to_fill_in("its answer")
    if callable(value):
        return run_value_problem(value)
    if _is_hivevar(value) and callable(value.default):
        return run_value_problem(value.default)
    if _is_hivevar(value):
        return _text_answer_problem(value.default, quoted)
    if not isinstance(value, str):
        return (f"is given {value!r}, a Python {type(value).__name__}: give the Hive as Python "
                "text, such as \"'2026-10-31'\" or \"5\" (a date typed with no quotes is "
                "a subtraction to Python)")
    return _text_answer_problem(value, quoted)


def _text_answer_problem(value: str, quoted: bool) -> str | None:
    """Why a tag's answer given as text can't be written where the tag stood, or None when it
    can."""
    if not value.strip():
        return "is given empty text: give the Hive the program put where the tag stood"
    if not quoted:
        return _bare_answer_problem(value)
    return _quoted_answer_problem(value)


def _quoted_answer_problem(value: str) -> str | None:
    """Why a quoted tag's answer, text not empty, can't stand where the tag stood, or None when
    it can: it has no quotes of its own."""
    if len(value) > 1 and value.startswith("'") and value.endswith("'"):
        return (f"stands inside quotes already, so its answer has none: answer "
                f"{escaped_literal(value[1:-1])}")
    return None


def run_value_problem(function: object) -> str | None:
    """Why a function can't answer a Decision as a Run value, or None when it can: it must be
    a function of a file of the Project's, such as building_blocks/run_values.py, so a Table
    reference can import it by its module and name."""
    module = getattr(function, "__module__", None) or ""
    name = getattr(function, "__qualname__", "") or ""
    if module in ("__main__", "builtins") or not module or "<" in name or "." in name:
        shown = name or repr(function)
        return (f"is given {shown}, a function a Table reference can't import: write it in a "
                "file of the Project's, such as building_blocks/run_values.py, import it in "
                "the decisions cell, and answer with it")
    return None


def run_value_import(function: Callable[..., object]) -> str:
    """The line a Table reference imports a Run value's function by, marked as one."""
    return f"from {function.__module__} import {function.__qualname__}{RUN_VALUE_MARK}"


def _bare_answer_problem(value: str) -> str | None:
    """Why a bare tag's answer, text not empty, can't stand where the tag stood, or None when
    it can, as writing.tag_value_problem says."""
    problem = tag_value_problem(value)
    if problem is None:
        return None
    return f"stands bare, so {problem}"


def open_decisions(text: str, table: str, kinds: tuple[str, ...] = KINDS) -> list[Decision]:
    """Each Decision of `kinds` a Table reference's text leaves open, top to bottom."""
    still_open = []
    for line in code_of(text).split("\n"):
        kind = kind_of(line)
        if kind in kinds and is_open(line):
            where, quoted, proposal, set_up = "", False, "", ""
            if kind in LINE_KINDS:
                read = LINE_KINDS[kind]
                where = read.line.match(line)[read.where] or ""
            if kind == TAG:
                quoted, proposal, set_up = (_tag_is_quoted(line), tag_proposal(line),
                                            tag_set_up(line))
            if kind == KEY and PROPOSED_FROM_QUERY_AGAIN in line:
                where = KEY_FROM_QUERY
            still_open.append(Decision(table, kind, _subject_of(kind, line), where, quoted,
                                       proposal, set_up))
    return still_open


def _subject_of(kind: str, line: str) -> str:
    """What a Decision's line is about: a guessed type's column, the <...> a placeholder's
    line holds first, the Key proposed on an open key= line, as Python, such as '["run_id"]',
    or, for a kind of LINE_KINDS, what its line names: a tag's NAME, the name or table
    proposed, a Pivot filter's field, or the table's kind proposed, "" where none is."""
    if kind == GUESSED_TYPE:
        return COLUMN_LINE.match(line)["column"]
    if kind in LINE_KINDS:
        read = LINE_KINDS[kind]
        subject = read.line.match(line)[read.subject]
        if subject is None:  # a KIND line with nothing proposed
            return ""
        return ast.literal_eval(subject) if read.subject_in_quotes else subject
    if kind == PLACEHOLDER:
        return PLACEHOLDER_WORD.search(line).group()
    if kind == KEY:
        proposal = _PROPOSED_IN_COMMENT.search(line)
        return proposal["key"] if proposal else ""
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
    return (f"is still {FILL_IN}: write {what} in the decisions cell in its place, then run "
            "the step's cell that writes the answers again")


def is_left_to_fill_in(value: object) -> bool:
    """Whether an answer is <FILL IN> as check() printed it, or what is left of it, such as
    "FILL IN" with its brackets taken off: no answer."""
    return isinstance(value, str) and "fill in" in value.lower()


def is_answered(decision: Decision, answer: dict[str, object]) -> bool:
    """Whether a table's answer in the decisions cell answers this Decision: one left
    <FILL IN>, as check() prints it to paste, doesn't."""
    if decision.kind in ANSWERED_BY_SUBJECT:
        answers = answer.get(ANSWERS[decision.kind])
        return (isinstance(answers, dict) and decision.subject in answers
                and not is_left_to_fill_in(answers[decision.subject]))
    return (decision.kind in ANSWERS and ANSWERS[decision.kind] in answer
            and not is_left_to_fill_in(answer[ANSWERS[decision.kind]]))


def table_answer(answers: dict[str, object], table: str, text: str) -> dict[str, object]:
    """One table's answer in a decisions cell, `answers`, its Table reference's text being
    `text`: what "all_tables" answers for it first, then the table's own answer over that, kind
    by kind and, for tags, tag by tag. A "key" of "proposed" is the table's proposed Key, or
    no answer when it has none."""
    own = answers.get(table)
    if not isinstance(own, dict):
        own = {}
    every = answers.get(ALL_TABLES)
    answer = {}
    if isinstance(every, dict):
        answer = all_tables_answer(every, table, text)
    for kind, value in own.items():
        if kind == ANSWERS[TAG] and isinstance(value, dict) and kind in answer:
            answer[kind] = {**answer[kind], **value}
        else:
            answer[kind] = value
    if answer.get(ANSWERS[KEY]) == ACCEPT_PROPOSED:
        del answer[ANSWERS[KEY]]
        proposed = proposed_key(text)
        if proposed is not None:
            answer[ANSWERS[KEY]] = proposed
    if answer.get(ANSWERS[TABLE_KIND]) == ACCEPT_PROPOSED:
        del answer[ANSWERS[TABLE_KIND]]
        kind = proposed_kind(text)
        if kind is not None:
            answer[ANSWERS[TABLE_KIND]] = kind
    return answer


def proposed_kind(text: str) -> TableKind | None:
    """The kind a Table reference's KIND line proposes, which an answer of "proposed" accepts,
    or None when it proposes none, or has no KIND line."""
    for line in code_of(text).split("\n"):
        found = KIND_LINE.match(line)
        if found and found["proposal"]:
            return TableKind(found["proposal"])
    return None


def table_kind(text: str) -> TableKind | None:
    """A Saved table's kind as its Table reference's KIND line answers it, Rebuilt or History;
    None while it is open, or where the Table reference has no KIND line, as a table made before
    8.10 has none until it is upgraded. Each place that asks a table's kind asks it here."""
    for line in code_of(text).split("\n"):
        found = KIND_LINE.match(line)
        if found and not found["todo"]:
            return TableKind(ast.literal_eval(found["value"]))
    return None


def has_kind_line(text: str) -> bool:
    """Whether a Table reference holds a KIND line, open or answered."""
    return any(KIND_LINE.match(line) for line in code_of(text).split("\n"))


def proposed_key(text: str) -> list[str] | None:
    """The Key a Table reference's key= line holds as proposed, which an answer of "proposed"
    accepts: one worked out of its query or its logic, made already, or one worked out of its
    rows, still open with the proposal in its comment; None when its Key is no proposal."""
    for line in code_of(text).split("\n"):
        if kind_of(line) != KEY:
            continue
        in_comment = _PROPOSED_IN_COMMENT.search(line)
        if in_comment:
            return ast.literal_eval(in_comment["key"])
        written = _KEY_VALUE.match(line)
        if written and (PROPOSED in line or PROPOSED_FROM_LOGIC in line):
            return ast.literal_eval(written["value"])
    return None


def all_tables_answer(every: dict[str, object], table: str, text: str) -> dict[str, object]:
    """What "all_tables", `every`, answers for one table, its Table reference's text being
    `text`: its seed limits as they are, for the seed to read; each tag of "tags" the table
    holds; its kind, for a table with a KIND line; and, for a "key" or "kind" of "proposed",
    "proposed", which table_answer turns into its proposal.
    An answer left <FILL IN> answers none; write_decisions names it once, for all_tables."""
    answer: dict[str, object] = {}
    if every.get(ANSWERS[KEY]) == ACCEPT_PROPOSED:
        answer[ANSWERS[KEY]] = ACCEPT_PROPOSED
    kind = every.get(ANSWERS[TABLE_KIND])
    if kind is not None and not is_left_to_fill_in(kind) and has_kind_line(text):
        answer[ANSWERS[TABLE_KIND]] = kind
    if SEED in every:
        answer[SEED] = every[SEED]
    tags = every.get(ANSWERS[TAG])
    if isinstance(tags, dict):
        held = tag_names(text)
        answer[ANSWERS[TAG]] = {name: value for name, value in tags.items()
                                if name in held and not is_left_to_fill_in(value)}
    return answer


def with_proposals(text: str, table: str, columns: dict[str, str],
                   key: list[str] | None) -> str:
    """A Table reference's text, as write_table_reference wrote it, with what
    project.add_references proposes written in (Toolbox 8.5): its first line, what one row is,
    from `key`, the Key it worked out of the table's rows, such as "One row per run_id.", and
    its key= line holding that Key, still open, to accept; and its does_not_add_up= from its
    columns' names and types. Each is marked proposed. With no Key, its first line and key=
    stay TODO lines."""
    lines = text.split("\n")
    for number, line in enumerate(lines):
        if key is not None and line == f'"""{table} - {ROW_TODO}"""':
            lines[number] = f'"""{table} - One row per {in_words(key)}."""{PROPOSED_ROW}'
        elif key is not None and line.startswith("    key=None,  # TODO:"):
            lines[number] = (f"    key=None,{PROPOSED_FROM_ROWS}{escaped_literal(key)}, "
                             "checked: accept it in the decisions cell")
        elif line.startswith("    does_not_add_up=[],  # TODO:"):
            lines[number] = _does_not_add_up_line(proposed_does_not_add_up(columns))
    return "\n".join(lines)


def _with_row_line_proposed_again(text: str, key: object) -> str:
    """A Table reference's text with its first line, what one row is, proposed again from the
    Key just written, `key`, while it is still the one project.add_references proposed: a TODO
    again for a Key of None. Any other first line is kept, as yours."""
    lines = text.split("\n")
    found = re.fullmatch(r'"""(?P<table>\S+) - One row per .*\."""' + re.escape(PROPOSED_ROW),
                         lines[0])
    if found is None:
        return text
    if isinstance(key, list) and key:
        lines[0] = f'"""{found["table"]} - One row per {in_words(key)}."""{PROPOSED_ROW}'
    else:
        lines[0] = f'"""{found["table"]} - {ROW_TODO}"""'
    return "\n".join(lines)


def _does_not_add_up_line(proposed: list[str]) -> str:
    """A Table reference's does_not_add_up= line holding the columns proposed, marked so."""
    if not proposed:
        return ("    does_not_add_up=[],  # proposed: no name says average, ratio, percent or "
                "rate")
    return (f"    does_not_add_up={escaped_literal(proposed)},  # proposed from its columns' "
            "names")


def proposed_does_not_add_up(columns: dict[str, str]) -> list[str]:
    """The columns, of `columns` by name and type, whose names say their values don't add up
    across rows: an average, avg_*; a ratio, a percent or a rate, *_ratio, *_pct or *_rate;
    and a double named *_per_*, such as runs_per_day."""
    proposed = []
    for column, kind in columns.items():
        name = column.lower()
        if (name.startswith("avg_") or name.endswith(("_ratio", "_pct", "_rate"))
                or ("_per_" in name and str(kind).lower() == "double")):
            proposed.append(column)
    return proposed


def location_under(root: str, table: str) -> str:
    """A table's own folder under its Database's location_root, <root>/<db>.db/<table>:
    "/data/team" gives mart_dev.weekly_ops "/data/team/mart_dev.db/weekly_ops"."""
    database, short = split_table_name(table)
    return f"{root.rstrip('/')}/{database}.db/{short}"


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
                      or kind_of(line) in LINE_KINDS)
        if not is_open(line) and not changeable:
            continue
        written, name = _answered_line(line, answer)
        if written is None:
            continue
        if kind_of(line) == TAG and not is_open(line) and written != line:
            answered.changed.append(f"tags: {tag_name_of(line)} is "
                                    f"{_tag_answer_shown(written)} now, in place of "
                                    f"{_tag_answer_shown(line)}")
        lines[number] = written
        answered.written.append(name)
    seeded, wrote_seed = _with_seed_written("\n".join(lines), answer)
    if wrote_seed:
        answered.written.append(SEED)
    if ANSWERS[KEY] in answered.written:
        seeded = _with_row_line_proposed_again(seeded, answer[ANSWERS[KEY]])
    answered.text = _with_run_value_imports(seeded, answer)
    answered.unwritten += _unwritten(answer, answered.written, reference)
    answered.unwritten += _tags_unwritten(answer, text)
    return answered


def _unwritten(answer: dict[str, object], written: list[str], reference: str) -> list[str]:
    """A line naming each answer `answer` gives that wasn't written into `reference`, and
    why."""
    unwritten = []
    for name in (ANSWERS[LOCATION], ANSWERS[KEY]):
        if is_left_to_fill_in(answer.get(name)):
            unwritten.append(f"{name} {still_to_fill_in('its answer')}")
        elif name in answer and name not in written:
            unwritten.append(
                f"{name}: kept as {reference} holds it, made already; to change it, edit its "
                f"{name}= line there (the decisions cell says {escaped_literal(answer[name])})")
    types = answer.get(ANSWERS[GUESSED_TYPE])
    if isinstance(types, dict):
        for column, value in types.items():
            if is_left_to_fill_in(value):
                unwritten.append(f"types: {column} {still_to_fill_in('its type')}")
            elif f"types: {column}" not in written:
                unwritten.append(f"types: {column}'s type wasn't a guess: {reference} "
                                 "gives it already; to change it, edit its line there")
    return unwritten


def _tags_unwritten(answer: dict[str, object], text: str) -> list[str]:
    """A line naming each tag answer left unwritten, and why: an answer in a form that can't
    stand where its tag stood, its line in the Table reference's text, `text`. A "tags" that
    isn't a dict, project.write_decisions refuses first."""
    tags = answer.get(ANSWERS[TAG])
    if not isinstance(tags, dict):
        return []
    tag_lines = {tag_name_of(line): line for line in text.split("\n")
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
        if kind == named and name in answer and not is_left_to_fill_in(answer[name]):
            return f"    {name}={escaped_literal(answer[name])},", name
    if kind in LINE_KINDS:
        return LINE_KINDS[kind].answered(line, answer.get(ANSWERS[kind]))
    types = answer.get(ANSWERS[GUESSED_TYPE])
    if kind != GUESSED_TYPE or not isinstance(types, dict):
        return None, ""
    column = _subject_of(kind, line)
    if column not in types or is_left_to_fill_in(types[column]):
        return None, ""
    written = f"        {escaped_literal(column)}: {escaped_literal(types[column])},"
    return written, f"types: {column}"


def _answered_tag(line: str, tags: object) -> tuple[str | None, str]:
    """A tag's line written with its answer, its comment kept, and the answer's name, or None
    when `tags` gives it none, or one in a form that can't stand where the tag stood."""
    name = tag_name_of(line)
    if not isinstance(tags, dict) or name not in tags:
        return None, ""
    value = tags[name]
    if tag_answer_problem(value, _tag_is_quoted(line)) is not None:
        return None, ""
    found = TAG_LINE.match(line)
    if callable(value):
        written = value.__qualname__
    elif _is_hivevar(value):
        written = repr(value)
    else:
        written = escaped_literal(value)
    return f"    {found['name']}: {written},  {found['comment']}", f"tags: {name}"


def _answered_name(line: str, name: object) -> tuple[str | None, str]:
    """A NAME line written with its answer, its TODO taken off, and the answer's name: the
    name proposed kept for "proposed", or the name given; None for no answer."""
    if not isinstance(name, str) or is_left_to_fill_in(name):
        return None, ""
    found = NAME_LINE.match(line)
    if name == ACCEPT_PROPOSED:
        name = found["name"]
    return f'NAME = "{name}"  # {found["what"]}', ANSWERS[NAME]


def _answered_source(line: str, sources: object) -> tuple[str | None, str]:
    """A SOURCES line written with its answer, its TODO taken off, and the answer's name: the
    table proposed kept for "proposed", or the table given; None for no answer."""
    found = SOURCE_LINE.match(line)
    proposed = found["proposed"]
    if not isinstance(sources, dict) or proposed not in sources:
        return None, ""
    table = sources[proposed]
    if not isinstance(table, str) or is_left_to_fill_in(table):
        return None, ""
    if table == ACCEPT_PROPOSED:
        table = found["table"]
    return (f'    "{proposed}": "{table}",  # the database table {found["what"]} samples',
            f"sources: {proposed}")


def _answered_pivot_filter(line: str, filters: object) -> tuple[str | None, str]:
    """A PIVOT_FILTERS line written with its answer, its TODO taken off, and the answer's
    name: "keep" for "proposed"; None for no answer, or one that is none of the four, which
    project.write_decisions refuses first."""
    found = PIVOT_FILTER_LINE.match(line)
    field = ast.literal_eval(found["field"])
    if not isinstance(filters, dict) or field not in filters:
        return None, ""
    answer = filters[field]
    if answer == ACCEPT_PROPOSED:
        answer = PivotFilterAnswer.KEEP
    if answer not in tuple(PivotFilterAnswer):
        return None, ""
    return (f'    {found["field"]}: "{answer}",  # {found["what"]}',
            f"{ANSWERS[PIVOT_FILTER]}: {field}")


def _answered_kind(line: str, kind: object) -> tuple[str | None, str]:
    """A KIND line written with its answer, "rebuilt" or "history", marked answered in place of
    its TODO and what was proposed kept, and the answer's name; None for no answer, or one
    that is neither, which project.write_decisions refuses first. table_answer has turned
    "proposed" into the kind proposed already."""
    if kind not in tuple(TableKind):
        return None, ""
    found = KIND_LINE.match(line)
    return f'KIND = "{kind}"  # {ANSWERED_KIND}{found["what"]}', ANSWERS[TABLE_KIND]


def kind_block(proposal: TableKind | None, why: str) -> list[str]:
    """The lines of a table's kind, as convert and new_table write it into its Table reference:
    the kind proposed from its write and why, or, with none, why nothing is, an open Decision
    either way."""
    if proposal is None:
        return [*KIND_COMMENT, f"KIND = None  # TODO: {NOTHING_PROPOSED}: {why}"]
    return [*KIND_COMMENT, f'KIND = "{proposal}"  # TODO: proposed {proposal}: {why}']


def pivot_filter_answers(text: str) -> dict[str, str]:
    """Each Pivot filter's answer a Table reference's PIVOT_FILTERS gives, by its field: one
    still open is kept, "keep", as converted."""
    found = {}
    for line in code_of(text).split("\n"):
        pivot_filter = PIVOT_FILTER_LINE.match(line)
        if pivot_filter:
            found[ast.literal_eval(pivot_filter["field"])] = pivot_filter["answer"]
    return found


def pivot_filters_block(filters: dict[str, str]) -> list[str]:
    """The lines of PIVOT_FILTERS, as a Conversion writes it into a Table reference: each
    Pivot filter by its field, `filters` giving what it keeps in words, kept as converted,
    each an open Decision."""
    lines = [*PIVOT_FILTERS_COMMENT, PIVOT_FILTERS_START]
    lines += [f'    {escaped_literal(field)}: "{PivotFilterAnswer.KEEP}",  # TODO: proposed: '
              f"{what}"
              for field, what in filters.items()]
    return [*lines, "}"]


@dataclass(frozen=True)
class LogicColumns:
    """What a table's logic gives once a Pivot filter's answer rewrote it (Toolbox 8.9): its
    columns and types, "" for each nothing told; its partition columns; the Key proposed from
    its query, or None; the columns its answers added to what one row is; and its TAGS lines,
    as converting.tags_block writes them."""

    columns: dict[str, str]
    partitions: list[str]
    key: list[str] | None
    grain_added: list[str]
    tags: list[str]


def with_logic_columns(text: str, given: LogicColumns) -> str:
    """A Table reference's text with the columns, partition columns, Key and Script tags its
    logic gives, `given`: each column's line kept where it had one, a new one typed as it is
    given, "string" marked a guess where that is "", and one the logic no longer gives taken
    out; partitioned_by= for its partition columns, or none; its key= as key_line_kept says;
    and TAGS holding each tag given, each kept as answered where it was, with no TAGS once
    there is none."""
    lines = text.split("\n")
    start = lines.index("    columns={")
    end = lines.index("    },", start)
    had = {COLUMN_LINE.match(line)["column"]: line for line in lines[start + 1:end]}
    lines[start + 1:end] = [had.get(column) or _column_line(column, kind)
                            for column, kind in given.columns.items()]
    lines = [line for line in lines if not line.startswith("    partitioned_by=")]
    if given.partitions:
        lines.insert(lines.index("    },", start) + 1,
                     f"    partitioned_by={escaped_literal(given.partitions)},")
    key: object = given.key
    for number, line in enumerate(lines):
        if line.startswith("    key="):
            lines[number], key = key_line_kept(line, given)
    rewritten = _with_tags_block("\n".join(lines), given.tags)
    return _with_run_value_imports(_with_row_line_proposed_again(rewritten, key), {})


def key_line_kept(line: str, given: LogicColumns) -> tuple[str, object]:
    """A table's key= line once a Pivot filter's answer rewrote its logic, and the Key it
    holds: a Key you answered is kept while its columns still fit, every column a column of
    the table and holding each column the answers added to what one row is; where they no
    longer fit, the Key proposed from its query, open, to accept. A Key the Toolbox proposed,
    or one still open, is the one proposed from its query now, made, as convert writes it."""
    answered = _ANSWERED_KEY.match(line)
    if (answered is None or is_open(line) or PROPOSED in line
            or PROPOSED_FROM_LOGIC in line):
        return _proposed_key_line(given.key, next(iter(given.columns))), given.key
    try:
        kept = ast.literal_eval(answered["value"])
    except (ValueError, SyntaxError):  # a Key written by hand that isn't plain: kept
        return line, None
    if not isinstance(kept, list):
        return line, kept
    fits = all(column in given.columns for column in kept) and all(
        column in kept for column in given.grain_added)
    if fits or given.key is None:
        return line, kept
    return (f"    key=None,{PROPOSED_FROM_ROWS}{escaped_literal(given.key)}"
            f"{PROPOSED_FROM_QUERY_AGAIN}", None)


def _column_line(column: str, kind: str) -> str:
    """A column's line in a Table reference's columns={...}: "string", marked a guess, where
    nothing told its type."""
    if not kind:
        return f"        {escaped_literal(column)}: \"string\",{GUESSED}"
    return f"        {escaped_literal(column)}: {escaped_literal(kind)},"


def _proposed_key_line(key: list[str] | None, first: str) -> str:
    """A key= line holding the Key proposed from a table's query, or a Decision to make where
    none was."""
    if key is None:
        return ("    key=None,  # TODO: the columns that pick out one row, such as "
                f'key=["{first}"]')
    return f"    key={escaped_literal(key)},{PROPOSED}"


def _with_tags_block(text: str, tags: list[str]) -> str:
    """A Table reference's text with TAGS holding each tag line of `tags`, one answered
    already kept as it is; with none, no TAGS. A new TAGS goes above PIVOT_FILTERS and the
    comment over it."""
    lines = text.split("\n")
    new = {tag_name_of(line): line for line in tags if TAG_LINE.match(line)}
    if TAGS_START not in lines:
        if not new:
            return text
        at = lines.index(PIVOT_FILTERS_START)
        while at > 0 and lines[at - 1].startswith("#"):
            at -= 1
        return "\n".join([*lines[:at], *tags, "", *lines[at:]])
    start = lines.index(TAGS_START)
    end = lines.index("}", start)
    had = {tag_name_of(line): line for line in lines[start + 1:end] if TAG_LINE.match(line)}
    if new:
        lines[start + 1:end] = [had.get(name, line) for name, line in new.items()]
        return "\n".join(lines)
    above = start
    while above > 0 and lines[above - 1].startswith("#"):
        above -= 1
    del lines[above:end + 2]  # the comment above, TAGS and the blank line after it
    return "\n".join(lines)


def name_answered(text: str) -> str | None:
    """The name a Table reference's NAME line gives its table, or None where it has none."""
    for line in code_of(text).split("\n"):
        found = NAME_LINE.match(line)
        if found:
            return found["name"]
    return None


def sources_answered(text: str) -> dict[str, str]:
    """Each database table a Table reference's SOURCES gives, by the one it was proposed as."""
    found = {}
    for line in code_of(text).split("\n"):
        source = SOURCE_LINE.match(line)
        if source:
            found[source["proposed"]] = source["table"]
    return found


def name_block(table: str, final: str, workbook: str) -> list[str]:
    """The lines of a NAME Decision, as a Conversion writes it into a Table reference: the
    name `table`, proposed for the final `final` of `workbook`."""
    return [*NAME_COMMENT, f'NAME = "{table}"  # TODO: proposed for {final} of {workbook}']


def sources_block(sources: dict[str, str]) -> list[str]:
    """The lines of SOURCES, as a Conversion writes it into a Table reference: each database
    table proposed, by the range it is proposed for, each an open Decision."""
    lines = [*SOURCES_COMMENT, SOURCES_START]
    lines += [f'    "{table}": "{table}",  # TODO: proposed: the database table {where} samples'
              for table, where in sources.items()]
    return [*lines, "}"]


def paste_lines(still_open: list[Decision], proposed: list[str] | None = None) -> list[str]:
    """The lines of a whole DECISIONS = {...} to paste into a decisions cell: each Decision of
    `still_open` the cell answers, by its table, each value still to give <FILL IN>, a guessed
    type's proposal "string", an open Key's proposal, and a comment beside each saying what to
    write. A tag more than one table holds is offered once, under "all_tables", by its NAME,
    where it stands bare in each or inside quotes in each. When `proposed`, the tables whose
    Key the Toolbox proposed, names two or more, "all_tables" offers "key": "proposed", which
    accepts each, in place of each table's own."""
    accepts_every_key = len(set(proposed or [])) > 1
    answered = [decision for decision in still_open if decision.kind in ANSWERS
                and not (accepts_every_key and decision.kind == KEY and decision.subject)]
    shared = _shared_decisions(answered)
    shared_kinds = [_shared_kind(decision) for decision in shared]
    by_table: dict[str, list[Decision]] = {}
    for decision in answered:
        if _shared_kind(decision) not in shared_kinds:
            by_table.setdefault(decision.table, []).append(decision)
    lines = [*_proposals_set_up(answered), f"{DECISIONS_NAME} = {{",
             *_all_tables_lines(shared, accepts_every_key)]
    for table, decided in by_table.items():
        lines.append(f"    {escaped_literal(table)}: {{")
        kinds = {decision.kind for decision in decided}
        database, short = table.split(".", 1)
        if LOCATION in kinds:
            lines.append(f'        "location": "{FILL_IN}",  # its folder, such as '
                         f'"/data/your_team/{database}.db/{short}"')
        lines += _key_lines([each for each in decided if each.kind == KEY])
        lines += _types_lines([each for each in decided if each.kind == GUESSED_TYPE])
        lines += _tags_lines([each for each in decided if each.kind == TAG])
        lines += _name_lines([each for each in decided if each.kind == NAME])
        lines += _sources_lines([each for each in decided if each.kind == SOURCE])
        lines += _pivot_filters_lines([each for each in decided if each.kind == PIVOT_FILTER])
        lines += _kind_lines([each for each in decided if each.kind == TABLE_KIND])
        lines.append("    },")
    return [*lines, "}"]


def _shared_kind(decision: Decision) -> tuple[str, str, bool] | None:
    """What a Decision answered for several tables at once has in common: a tag's NAME and
    whether it stands inside quotes, or a kind with nothing proposed; None for a location, a
    Key, a type or a kind proposed, which each table answers itself."""
    if decision.kind == TAG:
        return (TAG, decision.subject, decision.quoted)
    if decision.kind == TABLE_KIND and not decision.subject:
        return (TABLE_KIND, "", False)
    return None


def _shared_decisions(still_open: list[Decision]) -> list[Decision]:
    """The first of each Decision of `still_open` that more than one table holds, which
    paste_lines offers under "all_tables"."""
    tables_of: dict[tuple[str, str, bool], list[Decision]] = {}
    for decision in still_open:
        kind = _shared_kind(decision)
        if kind is not None:
            tables_of.setdefault(kind, []).append(decision)
    shared = []
    for found in tables_of.values():
        tables = {decision.table for decision in found}
        if len(tables) > 1:
            shared.append(found[0])
    return shared


def _all_tables_lines(shared: list[Decision], accepts_every_key: bool) -> list[str]:
    """The lines of "all_tables" in DECISIONS to paste: "key": "proposed" when it
    `accepts_every_key`, each shared tag's <FILL IN>, with how its answer is written, and the
    kind's, where nothing is proposed for several tables."""
    if not shared and not accepts_every_key:
        return []
    lines = [f'    "{ALL_TABLES}": {{  # answers for every table of this notebook; a table\'s '
             "own answer, under its name, overrides it"]
    if accepts_every_key:
        lines.append(f'        "{ANSWERS[KEY]}": "{ACCEPT_PROPOSED}",  # accepts each table\'s '
                     "proposed Key, marked # proposed in its Table reference, as if typed")
    # Where a shared tag stands differs from table to table, so its hint names no place.
    lines += _tags_lines([replace(decision, where="") for decision in shared
                          if decision.kind == TAG])
    if any(decision.kind == TABLE_KIND for decision in shared):
        lines.append(f'        "{ANSWERS[TABLE_KIND]}": "{FILL_IN}",  # "{TableKind.REBUILT}" '
                     f'or "{TableKind.HISTORY}", for each table nothing was proposed for, as '
                     "check() says why")
    return [*lines, "    },"]


def _key_lines(keys: list[Decision]) -> list[str]:
    """The line of one table's "key" in DECISIONS to paste, for its open Key: its proposal,
    when the Toolbox proposed one, else <FILL IN>."""
    if not keys:
        return []
    if keys[0].subject and keys[0].where == KEY_FROM_QUERY:
        return [f'        "{ANSWERS[KEY]}": {keys[0].subject},  # proposed from its query, as '
                "its Pivot filters' answers changed what one row is: keep it to accept it, or "
                "write another, or None"]
    if keys[0].subject:
        return [f'        "{ANSWERS[KEY]}": {keys[0].subject},  # proposed, and check_key '
                "found it holds: keep it to accept it, or write another, or None"]
    return [f'        "{ANSWERS[KEY]}": "{FILL_IN}",  # a list, such as ["job_id", "dt"], or '
            "None when no columns name one row"]


def _name_lines(names: list[Decision]) -> list[str]:
    """The line of one table's "name" in DECISIONS to paste, for its name proposed: "proposed",
    which keeps it."""
    if not names:
        return []
    return [f'        "{ANSWERS[NAME]}": "{ACCEPT_PROPOSED}",  # keeps {names[0].subject}; or '
            'a name of your own, such as "runs_by_job", renames the table']


def _sources_lines(sources: list[Decision]) -> list[str]:
    """The lines of one table's "sources" in DECISIONS to paste: each database table proposed
    for a range, "proposed", which keeps it."""
    if not sources:
        return []
    lines = [f'        "{ANSWERS[SOURCE]}": {{']
    for decision in sources:
        lines.append(f"            {escaped_literal(decision.subject)}: \"{ACCEPT_PROPOSED}\","
                     f"  # the table {decision.where} samples, such as \"ops.job_runs\"")
    return [*lines, "        },"]


def _pivot_filters_lines(pivot_filters: list[Decision]) -> list[str]:
    """The lines of one table's "pivot_filters" in DECISIONS to paste: each Pivot filter
    "keep", which keeps it as converted, with what it keeps and its other answers."""
    if not pivot_filters:
        return []
    lines = [f'        "{ANSWERS[PIVOT_FILTER]}": {{']
    for decision in pivot_filters:
        lines.append(f'            {escaped_literal(decision.subject)}: '
                     f'"{PivotFilterAnswer.KEEP}",  # {_sentence(decision.where)}. Or '
                     f'answer "{PivotFilterAnswer.FOLD}", "{PivotFilterAnswer.BATCH}" or '
                     f'"{PivotFilterAnswer.TABLES}", as its checklist says.')
    return [*lines, "        },"]


def _kind_lines(kinds: list[Decision]) -> list[str]:
    """The line of one table's "kind" in DECISIONS to paste: the kind proposed, which keeps it
    to accept it, saying why; or, with none proposed, <FILL IN>, saying why."""
    if not kinds:
        return []
    decision = kinds[0]
    if decision.subject:
        return [f'        "{ANSWERS[TABLE_KIND]}": "{decision.subject}",  # proposed, as '
                f"{decision.where}: keep it to accept it, or answer "
                f'"{_other_kind(decision.subject)}"']
    return [f'        "{ANSWERS[TABLE_KIND]}": "{FILL_IN}",  # "{TableKind.REBUILT}" or '
            f'"{TableKind.HISTORY}": nothing proposed, as {decision.where}']


def _other_kind(kind: str) -> str:
    """The kind that isn't `kind`: "history" for "rebuilt", and "rebuilt" for "history"."""
    if kind == TableKind.REBUILT:
        return TableKind.HISTORY
    return TableKind.REBUILT


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
        hint = tag_hint(decision.quoted, decision.where)
        if decision.proposal:
            lines.append(f"            {escaped_literal(decision.subject)}: "
                         f"{decision.proposal},  # proposed: keep it to accept it, or "
                         f"answer another, {hint}")
        else:
            lines.append(f'            {escaped_literal(decision.subject)}: "{FILL_IN}",  '
                         f"# {hint}")
    return [*lines, "        },"]


# --- The kinds of Decision a line of their own names -----------------------------------------


@dataclass(frozen=True)
class LineKind:
    """How one kind of Decision is read from the line that holds it, and answered: the
    line's pattern; the group naming what it is about, a Python string where
    `subject_in_quotes`; the group saying where it is, or what it is; and the function that
    writes an answer into the line, giving the line written and the answer's name, or None."""

    line: re.Pattern[str]
    subject: str
    subject_in_quotes: bool
    where: str
    answered: Callable[[str, object], tuple[str | None, str]]


# Each kind of Decision whose line names what it is about: a Script tag, a name proposed for
# a workbook's final, the database table a range samples, a Pivot filter, and a table's kind.
# Each place that reads one reads it here.
LINE_KINDS = {
    TAG: LineKind(TAG_LINE, "name", True, "where", _answered_tag),
    NAME: LineKind(NAME_LINE, "name", False, "what", _answered_name),
    SOURCE: LineKind(SOURCE_LINE, "proposed", False, "what", _answered_source),
    PIVOT_FILTER: LineKind(PIVOT_FILTER_LINE, "field", True, "what", _answered_pivot_filter),
    TABLE_KIND: LineKind(KIND_LINE, "proposal", False, "why", _answered_kind),
}
# The kinds whose answer in the decisions cell is a dict, one answer by what each is about.
ANSWERED_BY_SUBJECT = (GUESSED_TYPE, TAG, SOURCE, PIVOT_FILTER)
