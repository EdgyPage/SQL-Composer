"""Write the Copilot files, `copilot/*.txt`, from their sources in `tools/copilot_sources/`.

Run it on `dev` after changing a source, a public name's signature or the version:

    python tools/copilot_files.py

A test fails while a committed file differs from what this writes.

A user loads one Copilot file into Microsoft Copilot's web chat before asking it for Toolbox
code: one file for each objective, such as building a Statement or converting Hive, and
`00_start_here.txt`, which says which to load. Copilot takes at most 8,000 characters before
a chat, so each file must fit, as `copilot/count_characters.py` counts them, spaces and line
breaks included; this refuses to write one that doesn't.

A source is the file's text, with three kinds of placeholder, each on a line of its own:

- `{version}`: the Toolbox's name and version, from its version.txt;
- `{always}`: the block every objective file shares, `tools/copilot_sources/_always.txt`;
- `{names: SELECT, FROM, project.convert, ...}`: a list of those names, each with its
  signature as the Toolbox defines it, so a file never names a function that isn't there or
  calls one with arguments it doesn't take.
"""

from __future__ import annotations

import inspect
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "copilot")]

import count_characters  # noqa: E402
import toolbox_registry  # noqa: E402

import sqlglot_composer  # noqa: E402
from sqlglot_composer import admin, project  # noqa: E402

SOURCES = ROOT / "tools" / "copilot_sources"
COPILOT = ROOT / "copilot"
ALWAYS = SOURCES / "_always.txt"
NAMES = re.compile(r"^\{names: ([^}]*)\}$", re.MULTILINE)


class CopilotFileRefused(Exception):
    """A source that can't be written as a Copilot file: a name the Toolbox doesn't have, or a
    file over the limit."""


def named(name: str) -> object:
    """The Toolbox's object a name in a {names: ...} list stands for, such as project.convert."""
    module, _, attribute = name.rpartition(".")
    owner = {"": sqlglot_composer, "project": project, "admin": admin}.get(module)
    public = {"": sqlglot_composer.__all__, "project": project.__all__,
              "admin": admin.__all__}.get(module, [])
    if owner is None or attribute not in public:
        raise CopilotFileRefused(f"{name} isn't a public name of the Toolbox.")
    return getattr(owner, attribute)


def signature(name: str) -> str:
    """A name as a Copilot file lists it: its arguments and their defaults, without types."""
    found = named(name)
    if inspect.isclass(found) and found.__init__ is object.__init__:
        return name
    try:
        parameters = inspect.signature(found).parameters.values()
    except (TypeError, ValueError):
        return name
    shown, keyword_only = [], False
    for parameter in parameters:
        if parameter.name.startswith("_") or parameter.kind is parameter.VAR_KEYWORD and (
                parameter.name == "removed"):
            continue
        if parameter.kind is parameter.KEYWORD_ONLY and not keyword_only:
            shown.append("*")
            keyword_only = True
        text = parameter.name
        if parameter.kind is parameter.VAR_POSITIONAL:
            text, keyword_only = f"*{parameter.name}", True
        elif parameter.kind is parameter.VAR_KEYWORD:
            text = f"**{parameter.name}"
        elif parameter.default is not parameter.empty:
            text += f"={parameter.default!r}"
        shown.append(text)
    return f"{name}({', '.join(shown)})"


def names_block(names: str) -> str:
    """The lines a {names: ...} placeholder becomes."""
    return "\n".join(f"- {signature(name.strip())}" for name in names.split(",") if name.strip())


def rendered(source: str) -> str:
    """A Copilot file's text, its placeholders filled in."""
    version = f"{toolbox_registry.PRODUCT} {sqlglot_composer.TOOLBOX_VERSION}"
    text = source.replace("{version}", version)
    text = text.replace("{always}", ALWAYS.read_text(encoding="utf-8").strip())
    return NAMES.sub(lambda found: names_block(found.group(1)), text)


def copilot_files() -> dict[str, str]:
    """Each Copilot file, by its name, as this writes it; refused if one is over the limit."""
    files = {}
    for source in sorted(SOURCES.glob("[0-9][0-9]_*.txt")):
        text = rendered(source.read_text(encoding="utf-8"))
        most = max(count_characters.characters(text))
        if most > count_characters.LIMIT:
            raise CopilotFileRefused(
                f"{source.name} comes to {most:,} characters, over the {count_characters.LIMIT:,} "
                "Copilot takes: shorten its source.")
        files[source.name] = text
    return files


def main() -> int:
    for name, text in copilot_files().items():
        (COPILOT / name).write_text(text, encoding="utf-8", newline="\n")
    print(f"Wrote {len(copilot_files())} Copilot files in copilot/.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
