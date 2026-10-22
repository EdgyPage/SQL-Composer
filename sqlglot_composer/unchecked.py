"""Session settings, Unchecked statements and the Admin log: Hive sent as you chose it.

hive_settings(...) gives the SET lines of a named set of Session settings, and
unchecked_hive(...) wraps Hive you wrote by hand. Neither is a Statement, but to_hive,
show_hive, run and export_lineage accept them too. Each run of an Unchecked statement, and of
an Admin statement, adds an entry to the Admin log, a Markdown file set_admin_log can move;
inside a Project, it is the Project's admin/admin_log.md, which logs its Project actions too.
"""

from __future__ import annotations

import datetime
import os
import re
from collections.abc import Callable
from pathlib import Path
from types import FrameType

from .refusals import callers_frame, refuse, warn_at_callers_line

TOOLBOX_VERSION = "7.0"


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

    It isn't a Statement, but run sends it, one line at a time, and show_hive shows it. Make
    one with hive_settings(...). Write the name in a type hint, to say that a function of
    yours gives back Session settings:

    >>> def settings_for_joins() -> SessionSettings:
    ...     return hive_settings("map_joins")
    >>> settings_for_joins()
    <Session settings map_joins - show_hive(...) shows their SET lines>
    """

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

    Hive keeps a Session setting for the rest of the session, so send them first, then your
    Statements: run(hive_settings(...), send=...) sends each SET line as a call of its own, and
    gives back None. They hold only while your send keeps one session across its calls: if
    each call of your send opens a new session, each SET is
    gone before your Statement runs. show_hive prints them, and export_lineage, passed them
    with the Statements, writes them at the foot of both its files.

    Name one or more sets. The Toolbox ships four:

    - "dynamic_partitions": hive.exec.dynamic.partition=true and
      hive.exec.dynamic.partition.mode=nonstrict. For a table partitioned by more than its
      day, such as by region too: a write gives the day, and Hive fills the other Partitions
      from each row's own values only with these on.
    - "map_joins": hive.auto.convert.join=true,
      hive.auto.convert.join.noconditionaltask=true and hive.ignore.mapjoin.hint=false. Hive
      then joins a small table by copying it to every worker, which skips sorting the big one,
      and chooses this by itself from the tables' statistics; and it heeds the hint that
      JOIN(..., broadcast=True) writes, which it ignores otherwise. explain(s) shows whether
      it made one: a Map Join in the plan.
    - "statistics_on_write": hive.stats.autogather=true and hive.stats.column.autogather=true.
      Each write then gathers the statistics of the day it writes, which Hive picks its join
      plans from, so they are never out of date. compute_statistics(t, day) counts a day
      written without them.
    - "merge_small_files": hive.merge.mapfiles=true, hive.merge.mapredfiles=true and
      hive.merge.tezfiles=true. A write then merges its small files into fewer, larger ones,
      since many small files slow down every later read.

    Keep your own sets in a settings.py of your own, beside your notebook, each a name and its
    settings, such as HIVE_SETTINGS = {"nightly": {"hive.exec.parallel": True}}, and pass them
    as sets=. True and False are written true and false.

    >>> print(to_hive(hive_settings("dynamic_partitions")))
    SET hive.exec.dynamic.partition=true
    SET hive.exec.dynamic.partition.mode=nonstrict
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
            fix=f"Keep them in a settings.py of your own as {example}, and pass "
            "sets=HIVE_SETTINGS.",
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
        'settings.py of your own, as HIVE_SETTINGS = {"nightly": {"hive.exec.parallel": '
        'True}}, and pass it: hive_settings("nightly", sets=HIVE_SETTINGS).',
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

    It isn't a Statement, but run sends it and show_hive shows it, marked as unchecked. Make
    one with unchecked_hive(...). Write the name in a type hint, to say that a function of
    yours gives back an Unchecked statement:

    >>> def count_all_runs() -> UncheckedStatement:
    ...     return unchecked_hive("SELECT COUNT(*) AS runs FROM ops.job_runs")
    >>> count_all_runs()
    <Unchecked statement - show_hive(...) shows its Hive>
    """

    def __init__(self, text: str) -> None:
        self._text = text  # the Hive as written, without a last ;

    def __repr__(self) -> str:
        return "<Unchecked statement - show_hive(...) shows its Hive>"


class UncheckedNote(UserWarning):
    """An Unchecked statement changes a table: the note says which admin function does it."""


def unchecked_hive(text: str) -> UncheckedStatement:
    """Hive you write by hand, for run to send when no clause function writes it yet.

    No Guard, Warning or Load limit looks inside it: the Toolbox sends the text as you wrote
    it, dropping a ; you end it with, and can't tell whether it gives the right answer. Use it for
    the one statement you need now, and keep using the clause functions for the rest. show_hive
    marks it, export_lineage draws it as one step it can't see inside, and each run of it adds
    an entry to the Admin log (see set_admin_log), whose Unchecked statements are the list of
    what the Toolbox should learn to write next.

    Text that starts DROP, ALTER or TRUNCATE gets a note at your line, naming the admin
    function that does the same job with its checks, where one does. For example, Hive refuses
    TRUNCATE on an external table (one whose files stay where you put them), and every Saved
    table of yours is one; admin.drop_days does that job.

    Write one command in each: send several as several unchecked_hive(...), one after the
    other. When the last line ends in a -- comment, show_hive puts the ; on a line of its own,
    since after the comment it would be part of it.

    >>> by_hand = unchecked_hive(
    ...     "SELECT COUNT(*) AS runs FROM ops.job_runs WHERE dt = '2026-09-24'")
    >>> text = show_hive(by_hand)
    -- Unchecked statement, written by hand: no Guard, Warning or Load limit looked inside
    SELECT COUNT(*) AS runs FROM ops.job_runs WHERE dt = '2026-09-24';
    """
    if not isinstance(text, str):
        refuse(
            what=f"unchecked_hive was given {text!r}, which isn't Hive text.",
            why="It sends the Hive you write by hand, as you wrote it.",
            fix='Write the Hive as a string: unchecked_hive("ALTER TABLE ..."). To run a '
            "Statement, pass it to run(...) itself.",
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
    said = _SAID.sub(lambda found: found.group() if found.group().startswith("--") else "''",
                     unchecked._text)
    # After a comment on the last line, a ; would be part of the comment.
    end = "\n;" if "--" in said.splitlines()[-1] else ";"
    return f"{UNCHECKED_MARK}\n{unchecked._text}{end}"


# The comment show_hive heads an Unchecked statement with, in a dry run too.
UNCHECKED_MARK = ("-- Unchecked statement, written by hand: no Guard, Warning or Load limit "
                  "looked inside")


# A string in quotes, a name in backticks, or a comment: what Hive text says, as opposed to
# what it does. Whichever starts first wins, as when Hive reads it.
_SAID = re.compile(r"""'(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*"|`(?:[^`]|``)*`|--[^\n]*""")


def _what_it_does(text: str) -> str:
    """The text in capitals with its strings and comments blanked out, and names in backticks
    kept without them, so a keyword is found only where it is one."""
    def blank(found: re.Match[str]) -> str:
        said = found.group()
        if said.startswith("`"):
            return said[1:-1].replace("``", "`")
        return "" if said.startswith("--") else "''"
    return _SAID.sub(blank, text).upper()


# The admin function that does each job, as the note writes its call, and what the text that
# does it by hand starts with, after ALTER TABLE <name>.
_ALTERED_BY = (
    (r"\bDROP\s+(IF\s+EXISTS\s+)?PARTITION\b", "admin.drop_days(t, before=...)"),
    (r"\bADD\s+COLUMNS\b", "admin.add_columns(t, send=...)"),
    (r"\bSET\s+TBLPROPERTIES\b", "admin.set_properties(t)"),
    (r"\bSET\s+LOCATION\b", "admin.move_to_own_folder(t, send=...)"),
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
                "table of yours is one. admin.drop_days(t, before=...) drops a Saved table's "
                "old days with its checks, and writing a day again with INSERT_OVERWRITE "
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


# --- The Admin log ---------------------------------------------------------------------------

# Where the Admin log is written: set by set_admin_log, None for the usual place, admin_log.md
# beside the script or notebook that runs, or in a Project, its admin/admin_log.md.
_admin_log = {"path": None}


def set_admin_log(path: str | Path | None = None) -> Path | None:
    """Set where the Admin log is written, such as ADMIN_LOG from your own settings.py.

    The Admin log is a Markdown file the Toolbox adds an entry to each time run sends an
    Unchecked statement or an Admin statement: when, the call, the Hive sent, the script and
    its git commit, and whether it worked. It only ever adds to the file.

    Left unset, the log is admin_log.md beside the script or notebook that calls run, or
    inside a Project the Project's admin/admin_log.md (help(project)). A path you give that
    isn't absolute, such as "logs/admin_log.md", starts from the folder of the
    script or notebook that calls set_admin_log. Call it at the top of each notebook or
    pipeline: a restarted kernel forgets it. It returns the path now in force, or None for the
    default.

    >>> set_admin_log("logs/admin_log.md").name
    'admin_log.md'
    >>> set_admin_log()  # back to the usual place
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
    "Each Admin statement, Unchecked statement and Project action the Toolbox has run, oldest "
    "first. The Toolbox only ever adds to this file. Its Unchecked statements are the list of "
    "what the Toolbox should learn to write next.\n"
)

# How much of an Unchecked statement's first line an entry's call shows.
_CALL_LENGTH = 65


def unchecked_call(unchecked: UncheckedStatement) -> str:
    """How an entry names an Unchecked statement's call: its first line, cut short."""
    whole = unchecked._text
    first = whole.splitlines()[0][:_CALL_LENGTH]
    quoted = '"' + first.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return f"unchecked_hive({quoted}{' ...' if first != whole else ''})"


def logged_run(kind: str, call: str, hive: str, send: Callable[[str], object]) -> object:
    """Send `hive`, then add its entry to the Admin log: worked, or failed with its error,
    which is raised again once the entry is written. `kind` is "Unchecked statement" or
    "Admin statement"."""
    frame = callers_frame()
    try:
        result = send(hive)
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
    lines = ["", f"## {_now():%Y-%m-%d %H:%M:%S}, {kind}", "", f"- Call: {_code(call)}"]
    if tables:
        lines.append(f"- Tables named: {', '.join(tables)}")
    lines += [_script_line(caller), f"- Result: {result}", "", f"{fence}sql", hive, fence, ""]
    _write_entry(path, lines)


def _script_line(caller: Path | None) -> str:
    """An entry's Script line: the script or notebook that ran, and its git commit."""
    from .lineage import caller_folder, scripts_commit  # it imports this file

    script = caller.name if caller is not None else "a notebook"
    return f"- Script: {script}, at commit {scripts_commit(caller_folder(caller))}"


def _write_entry(path: Path, lines: list[str]) -> None:
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


def _code(text: str) -> str:
    """Markdown inline code, with a fence that survives backticks inside it."""
    fence = "`" * (_longest_backticks(text) + 1)
    pad = " " if text.startswith("`") or text.endswith("`") else ""
    return f"{fence}{pad}{text}{pad}{fence}"


def _now() -> datetime.datetime:
    """The time an entry is made."""
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


__all__ = ["hive_settings", "unchecked_hive", "set_admin_log", "SessionSettings",
           "UncheckedStatement"]
