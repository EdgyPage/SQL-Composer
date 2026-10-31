"""Write the Copilot files, `copilot/*.txt`, from their sources in `tools/copilot_sources/`.

Run it on `dev` after changing a source, a public name's signature or the version:

    python tools/copilot_files.py

A test fails while a committed file differs from what this writes.

A user loads one Copilot file into Microsoft Copilot's web chat before asking it for Toolbox
code: one file for each objective, such as building a Statement or converting Hive, and
`00_start_here.txt`, which says which to load. For an Excel workbook they load five:
`11_excel_formula_workbooks.txt` and `12_excel_power_query.txt` with 03, 04 and 05. Copilot
takes at most 8,000 characters at once, so each file must fit, as `copilot/count_characters.py`
counts them, spaces and line breaks included; this refuses to write one that doesn't.

A source is the file's text, with three kinds of placeholder, each on a line of its own:

- `{version}`: the Toolbox's name and version, from its version.txt;
- `{always}`: the block each objective file holds, `tools/copilot_sources/_always.txt`, all
  but files 11 and 12, which are loaded with 03, 04 and 05 and so have it already;
- `{names: SELECT, FROM, project.convert, ...}`: a list of those names, each with its
  signature as the Toolbox defines it, so a file never names a function that isn't there or
  calls one with arguments it doesn't take;
- `{workflow: convert}`: a Workflow's steps as a numbered list, each its kind and its call,
  as `tools/workflow_graph.py` lists them from `sqlglot_composer/workflows.py`, so a file's
  steps are always the ones its notebook runs.
"""

from __future__ import annotations

import inspect
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT), str(ROOT / "copilot")]

import count_characters  # noqa: E402
import formula_workbook  # noqa: E402
import formula_workbook_examples  # noqa: E402
import merge_copilot_files  # noqa: E402
import toolbox_registry  # noqa: E402
import workflow_graph  # noqa: E402

import sqlglot_composer  # noqa: E402
from sqlglot_composer import admin, project  # noqa: E402

SOURCES = ROOT / "tools" / "copilot_sources"
COPILOT = ROOT / "copilot"
ALWAYS = SOURCES / "_always.txt"
NAMES = re.compile(r"^\{names: ([^}]*)\}$", re.MULTILINE)
WORKFLOW = re.compile(r"^\{workflow: (\w+)\}$", re.MULTILINE)


class CopilotFileRefused(Exception):
    """A source that can't be written as a Copilot file: a name the Toolbox doesn't have, or a
    file over the limit."""


# The modules a {names: ...} list may name from, by the name a file writes before the dot.
MODULES = {"": sqlglot_composer, "project": project, "admin": admin}
# The catch-all a Toolbox function keeps for arguments it no longer takes, to say what replaced
# them: no file lists it.
REPLACED_ARGUMENTS = "removed"


def named(name: str) -> object:
    """The Toolbox's object a name in a {names: ...} list stands for, such as
    project.convert."""
    module, _, attribute = name.rpartition(".")
    owner = MODULES.get(module)
    if owner is None or attribute not in owner.__all__:
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
        replaced = (parameter.kind is parameter.VAR_KEYWORD
                    and parameter.name == REPLACED_ARGUMENTS)
        if parameter.name.startswith("_") or replaced:
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
    return "\n".join(f"- {signature(name.strip())}" for name in names.split(",")
                     if name.strip())


def rendered(source: str) -> str:
    """A Copilot file's text, its placeholders filled in."""
    version = f"{toolbox_registry.PRODUCT} {sqlglot_composer.TOOLBOX_VERSION}"
    text = source.replace("{version}", version)
    text = text.replace("{always}", ALWAYS.read_text(encoding="utf-8").strip())
    text = WORKFLOW.sub(_steps_of, text)
    return NAMES.sub(_names_block_of, text)


def _steps_of(placeholder: re.Match[str]) -> str:
    """The lines a {workflow: NAME} placeholder, as WORKFLOW finds it, becomes."""
    workflow = next(each for each in workflow_graph.workflows.WORKFLOWS
                    if each.name == placeholder.group(1))
    return "\n".join(workflow_graph.steps_listed(workflow))


def _names_block_of(placeholder: re.Match[str]) -> str:
    """The lines a {names: ...} placeholder, as NAMES finds it, becomes."""
    return names_block(placeholder.group(1))


def copilot_files() -> dict[str, str]:
    """Each Copilot file, by its name, as this writes it; refused if one is over the limit."""
    files = {}
    for source in sorted(SOURCES.glob("[0-9][0-9]_*.txt")):
        text = rendered(source.read_text(encoding="utf-8"))
        most = max(count_characters.characters(text),
                   count_characters.characters_on_windows(text))
        if most > count_characters.LIMIT:
            raise CopilotFileRefused(
                f"{source.name} comes to {most:,} characters, over the "
                f"{count_characters.LIMIT:,} Copilot takes: shorten its source.")
        files[source.name] = text
    return files


def main() -> int:
    """Write every Copilot file into copilot/, the document that merges them, the empty
    Formula workbook and the examples of it filled in."""
    files = copilot_files()
    for name, text in files.items():
        (COPILOT / name).write_text(text, encoding="utf-8", newline="\n")
    print(f"Wrote {len(files)} Copilot files in copilot/.")
    merge_copilot_files.main()
    status = formula_workbook.main()
    if status != 0:
        return status
    return formula_workbook_examples.main()


if __name__ == "__main__":
    sys.exit(main())
