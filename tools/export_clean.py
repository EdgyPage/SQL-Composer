"""Export the Clean branch: build `main` from `dev`, check it, and commit it to `main` locally.

Run it with `dev` checked out and nothing uncommitted:

    python tools/export_clean.py

It builds the Clean tree in a temporary folder, from what `dev` has committed: the Composer
core, `composer_core/`, and each Edition `tools/editions.py` names in EXPORTED:

- it copies each folder, such as `sqlglot_composer/`, and stamps line 1 of every file in it with
  its name, for example
  `# sqlglot Composer 2.0, exported 2026-10-02 14:05 - generated from dev, do not edit` or
  `# Composer core 2.0, exported ...`, every folder with the same time;
- it writes the list of the folder's files into its `__init__.py`, for the import self-check;
- for each Edition, it writes a copy of the Example projects and the Templates, which dev holds
  for sqlglot Composer in `example_projects/` and `templates/`, into
  `example_projects/<Edition's folder>/` and `templates/<Edition's folder>/`: each file named
  for that Edition with `named_for`, each place it names, such as
  `example_projects/starter/`, as main has it, and line 1 stamped, for example
  `# Spark Composer 2.0, exported 2026-10-02 14:05 - copy it, then edit your copy`;
- it writes `.github/README.md` from `docs/clean-branch-readme.md`, putting in the version, the
  places the two Editions' Hive differs, from `DECLARED_DIFFERENCES` in `tools/editions.py`,
  the list of how-tos, from `worked_examples/how_to/`, the list of Templates, as
  `templates/README.md`'s tables give them, and a cheat sheet: one line per public name, grouped by file,
  from each docstring's first line.

It then checks what it built:

- each Toolbox file imports only what work has (the standard library, pandas, numpy, and its
  Edition's library where `tools/editions.py` allows it);
- each stamped Edition, with the Composer core beside it, imports in a fresh Python that can't
  import the other Edition's library, and, copied without the Composer core, stops on import
  and says to copy `composer_core`;
- importing both Editions in one Python stops;
- each Example project's `run_pipeline.py` runs its dry run, in a fresh Python that can't
  import the other Edition's library, finding the Toolbox as its README says, and leaves no
  file behind; a dry run prints every step's Hive and sends nothing, so Spark Composer's needs
  no Java;
- each file is read by `tools/offline_policy.py`, as main would hold it, before anything in it
  is imported or run: the Toolbox and each Edition's copies of the Example projects and the
  Templates, their pages included, so that none of it can reach the network. The README is
  Markdown, which nothing runs;
- the folders have one version, and both Editions describe the same public names the same way;
- the tree holds nothing outside its allowlist: the Composer core's folder and each Edition's,
  flat, each Edition's copies of the Example projects and the Templates, and
  `.github/README.md`.

Only then does it commit the tree to `main`, as one new commit on top of the old `main`. It
never checks `main` out and never pushes: pushing `main` is your step.

It refuses, and leaves `main` as it was, while `.scratch/drift.md` has an open item.

To look at the Clean tree without committing anything, build it into an empty folder; this
builds what the checkout holds, and runs while a drift item is open:

    python tools/export_clean.py --preview <folder>
"""

from __future__ import annotations

import ast
import datetime
import inspect
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import editions
import offline_policy

ROOT = Path(__file__).resolve().parent.parent
DRIFT_LIST = ".scratch/drift.md"
README = ".github/README.md"
README_TEMPLATE = "docs/clean-branch-readme.md"
VERSION_MARKER = "<!-- VERSION -->"
DIFFERENCES_MARKER = "<!-- DIFFERENCES -->"
CHEAT_SHEET_MARKER = "<!-- CHEAT SHEET -->"
# The folders main holds a copy of for each Edition, for the user to copy and edit: on dev they
# hold sqlglot Composer's, and on main each Edition's copy sits in a folder named for it, such as
# example_projects/spark_composer/.
EXAMPLE_PROJECTS = "example_projects"
TEMPLATES = "templates"
COPIED = (EXAMPLE_PROJECTS, TEMPLATES)
TEMPLATES_README = "templates/README.md"
# The how-tos, which each Edition's how_to.html is written from, and which the README lists.
HOW_TOS = "worked_examples/how_to"
HOW_TOS_MARKER = "<!-- HOW-TOS -->"
TEMPLATES_MARKER = "<!-- TEMPLATES -->"


class ExportRefused(Exception):
    """The export stopped before touching `main`; the message says why and what to do."""


def version_text(toolbox_version: str, when: datetime.datetime) -> str:
    """A version and the time it was exported, such as "3.0, exported 2026-10-02 14:05"."""
    return f"{toolbox_version}, exported {when.strftime('%Y-%m-%d %H:%M')}"


def stamp_text(product: str, toolbox_version: str, when: datetime.datetime) -> str:
    """The line-1 stamp, such as "sqlglot Composer 3.0, exported 2026-10-02 14:05 - ..."."""
    return f"{product} {version_text(toolbox_version, when)} - generated from dev, do not edit"


def copy_stamp_text(product: str, toolbox_version: str, when: datetime.datetime) -> str:
    """The line-1 stamp of an Example project's or a Template's file, such as "sqlglot Composer
    3.0, exported 2026-10-02 14:05 - copy it, then edit your copy"."""
    return f"{product} {version_text(toolbox_version, when)} - copy it, then edit your copy"


def stamped(name: str, text: str, stamp: str) -> str:
    """The file's text with the stamp as a comment on line 1, in that file's comment style."""
    if name.endswith(".py"):
        return f"# {stamp}\n{text}"
    if name.endswith((".md", ".html")):
        return f"<!-- {stamp} -->\n{text}"
    raise ExportRefused(
        f"{name} is neither Python, Markdown nor HTML, so the export can't stamp it. Remove it "
        "from the Toolbox, or teach stamped() its comment style."
    )


def toolbox_version_of(source: Path, folder: str) -> str:
    text = (source / folder / "__init__.py").read_text(encoding="utf-8")
    return re.search(r'^TOOLBOX_VERSION = "([^"]+)"$', text, re.MULTILINE).group(1)


def with_file_list(init_text: str, names: list[str], folder: str) -> str:
    """`__init__.py`'s text with `_FILES = None` replaced by the list of the folder's files."""
    if init_text.count("\n_FILES = None\n") != 1:
        raise ExportRefused(
            f"{folder}/__init__.py must have exactly one `_FILES = None` line for the export to "
            "write the file list into. Put it back."
        )
    listed = "".join(f'    "{name}",\n' for name in names)
    return init_text.replace("\n_FILES = None\n", f"\n_FILES = [\n{listed}]\n")


def describe_toolbox(folder: str) -> dict:
    """Import an Edition's folder and describe it for the cheat sheet, grouped by file.

    This runs in a fresh Python started inside the Clean tree (see `import_stamped`), so the
    folder it imports is the stamped copy, and its import self-check runs on that copy.
    """
    toolbox = __import__(folder)
    groups: dict[str, dict] = {}
    for name in toolbox.__all__:
        value = getattr(toolbox, name)
        if isinstance(value, str):
            # The two constants: their docstring is the Toolbox's own, so show the value and
            # the sentence of that docstring which says what the constant is.
            module, line = toolbox, f"= `{value!r}`"
            said = re.search(rf"\b{name} is (.+?\.)(\s|$)", " ".join(toolbox.__doc__.split()))
            if said:
                line += " - " + said.group(1)
        else:
            module = value if inspect.ismodule(value) else sys.modules[value.__module__]
            line = "- " + first_line(inspect.getdoc(value))
        file = Path(module.__file__).name
        group = groups.setdefault(file, {"file": file, "about": first_line(module.__doc__),
                                         "names": []})
        group["names"].append([name, line])
    return {
        "folder": str(Path(toolbox.__file__).parent),
        "version": toolbox.VERSION,
        "groups": list(groups.values()),
    }


def first_line(docstring: str | None) -> str:
    return (docstring or "").strip().splitlines()[0]


def last_error(stderr: str) -> str:
    """The error at the end of a traceback, with every line of its message.

    An import stop's message runs over several indented lines, the four parts, so this keeps
    everything from the last unindented line on.
    """
    lines = stderr.strip().splitlines() or ["Python gave no message"]
    start = max((i for i, line in enumerate(lines) if not line[:1].isspace()), default=0)
    return "\n".join(lines[start:])


def other_libraries(edition: editions.Edition) -> list[str]:
    """The libraries of the Editions other than `edition`, such as ["pyspark"]."""
    return [other.library for other in editions.EDITIONS.values() if other is not edition]


def fresh_python(folder: Path, code: str, blocked: list[str] | None = None,
                 path: str | None = None) -> subprocess.CompletedProcess:
    """Run `code` in a fresh Python started in `folder`, which can't import the libraries
    `blocked` names, with `path`, if given, as its PYTHONPATH, and nothing else on it."""
    environment = {name: value for name, value in os.environ.items() if name != "PYTHONPATH"}
    environment["PYTHONIOENCODING"] = "utf-8"
    if path is not None:
        environment["PYTHONPATH"] = path
    # A None in sys.modules makes any import of that library fail loudly.
    return subprocess.run(
        [sys.executable, "-B", "-c",
         f"import sys; sys.modules.update(dict.fromkeys({blocked or []!r})); {code}"],
        cwd=folder, env=environment, capture_output=True, text=True, encoding="utf-8",
    )


def import_stamped(into: Path, edition: editions.Edition) -> dict:
    """Import an Edition's stamped folder in a fresh Python that can't import the other
    Edition's library, and return `describe_toolbox()` of it."""
    done = fresh_python(
        into, "import json, export_clean; "
        f"print(json.dumps(export_clean.describe_toolbox({edition.folder!r})))",
        blocked=other_libraries(edition), path=str(Path(__file__).parent))
    if done.returncode != 0:
        raise ExportRefused(
            f"The stamped copy of {edition.product} doesn't import, so nothing was exported:\n"
            f"{last_error(done.stderr)}"
        )
    described = json.loads(done.stdout.strip().splitlines()[-1])
    if Path(described["folder"]).resolve() != (into / edition.folder).resolve():
        raise ExportRefused(
            f"The import check found another {edition.folder}: {described['folder']}")
    return described


# What an Edition says when it is imported with no composer_core beside it: its fix.
COPY_THE_CORE = "Copy the composer_core folder from the same download beside the"


def check_needs_the_core(into: Path, edition: editions.Edition) -> None:
    """Refuse an Edition that, copied on its own, doesn't stop on import and say to copy
    composer_core beside it."""
    with tempfile.TemporaryDirectory() as alone:
        shutil.copytree(into / edition.folder, Path(alone) / edition.folder)
        done = fresh_python(Path(alone), f"import {edition.folder}",
                            blocked=other_libraries(edition))
    if done.returncode == 0:
        said = "imported, so another composer_core must be on this Python's path"
    elif COPY_THE_CORE not in done.stderr:
        said = f"gave:\n{last_error(done.stderr)}"
    else:
        return
    raise ExportRefused(f"{edition.folder}, copied without composer_core beside it, must stop on "
                        f"import and say to copy composer_core, but it {said}")


def check_one_edition_per_python(into: Path) -> None:
    """Refuse a Clean tree whose two Editions can be imported in one Python: the Composer core
    holds one Edition at a time, so importing the second must stop."""
    if len(editions.EXPORTED) < 2:
        return
    first, second = (edition.folder for edition in editions.EXPORTED[:2])
    done = fresh_python(into, f"import {first}, {second}")
    if done.returncode == 0:
        raise ExportRefused(
            f"Importing {first} and then {second} in one Python must stop, but it didn't. "
            "composer_core/edition.py's plug() stops the second Edition plugged in: put that "
            "back.")
    if f"{second} was imported after {first}" not in done.stderr:
        raise ExportRefused(
            f"Importing {first} and then {second} in one Python must stop and say to use one "
            f"Edition, but it gave:\n{last_error(done.stderr)}")


# Where an Example project on main finds the Toolbox: the Clean tree's top folder, three up.
TOOLBOX_FROM_A_PROJECT = os.path.join(os.pardir, os.pardir, os.pardir)


def check_dry_runs(into: Path, edition: editions.Edition) -> None:
    """Run each of `edition`'s Example projects' run_pipeline.py, as its README says, in a
    fresh Python that can't import the other Edition's library, and refuse one that stops or
    prints no Hive. Its dry run prints the Hive of every step and sends nothing, so it needs
    no Java."""
    for script in sorted((into / EXAMPLE_PROJECTS / edition.folder).glob("*/run_pipeline.py")):
        before = files_in(into)
        done = fresh_python(
            script.parent, "import runpy; runpy.run_path('run_pipeline.py', run_name='__main__')",
            blocked=other_libraries(edition), path=TOOLBOX_FROM_A_PROJECT)
        where = script.relative_to(into).as_posix()
        # It runs inside the Clean tree, so anything it writes would ship unstamped.
        left = [path for path in files_in(into) if path not in before]
        if left:
            raise ExportRefused(f"{where}'s dry run left files in the Clean tree: {left}. A dry "
                                "run only prints: take out what writes them.")
        if done.returncode != 0:
            raise ExportRefused(f"{where} doesn't run its dry run on main, so nothing was "
                                f"exported:\n{last_error(done.stderr)}")
        if "-- 1 of " not in done.stdout:
            raise ExportRefused(f"{where}'s dry run printed no step's Hive, which show_hive "
                                f"heads with `-- 1 of `. It printed:\n{done.stdout[:500]}")


def open_drift_items(drift_text: str) -> list[str]:
    """The open items in `.scratch/drift.md`, such as ["D5"], read only under `## Items`.

    The indented lines above that heading show the format and are not items.
    """
    if "\n## Items\n" not in "\n" + drift_text:
        raise ExportRefused(
            f"{DRIFT_LIST} has no `## Items` heading, so the export can't tell whether a drift "
            "item is open. Put the heading back."
        )
    items = ("\n" + drift_text).split("\n## Items\n", 1)[1].split("\n## ", 1)[0]
    return re.findall(r"^- \[ \] (D\d+) ", items, re.MULTILINE)


def check_offline(into: Path, paths: list[str]) -> None:
    """Refuse the Clean tree if a file under `paths`, in `into`, holds anything that could reach
    the network, as `tools/offline_policy.py` reads it under main's path: nothing but the
    reviewed sites in its ALLOWED in the Toolbox, and nothing at all in a copy the user takes."""
    found = offline_policy.scan(into, paths)
    if found:
        raise ExportRefused(
            "The Clean tree holds code that could reach the network, and the Toolbox, its "
            "Example projects and its Templates reach nothing but the user's send. "
            "tools/offline_policy.py found, as main would hold it:\n"
            + "".join(f"  {finding}\n" for finding in found)
            + "Line 1 on main is the export's stamp, so each is one line up on dev, and a copy "
            "in example_projects/<Edition>/ or templates/<Edition>/ is dev's in "
            "example_projects/ or templates/. Take it out on dev. A Toolbox site that must stay "
            "needs a reviewed entry in ALLOWED in tools/offline_policy.py, with the user's OK; "
            "a copy the user takes may hold none.")


def files_in(folder: Path) -> list[str]:
    """Every file under `folder`, as sorted paths relative to it, such as ".github/README.md"."""
    return sorted(path.relative_to(folder).as_posix() for path in folder.rglob("*")
                  if path.is_file())


def outside_allowlist(paths: list[str]) -> list[str]:
    """The paths `main` may not hold: it holds the Composer core's and each exported Edition's
    flat folder, each exported Edition's copy of the Example projects and the Templates, in a
    folder named for it, and the README."""
    folders = set(exported_folders())
    shipped = {edition.folder for edition in editions.EXPORTED}

    def allowed(path: str) -> bool:
        parts = path.split("/")
        return (path == README
                or (len(parts) == 2 and parts[0] in folders)
                or (len(parts) > 2 and parts[0] in COPIED and parts[1] in shipped))

    return [path for path in paths if not allowed(path)]


def cheat_sheet(groups: list[dict]) -> str:
    """One Markdown section per Toolbox file, with one line per public name in it."""
    sections = []
    for group in groups:
        lines = [f"### `{group['file']}`", ""]
        # A file line that only repeats a name's own line (example_database.py) is left out.
        if f"- {group['about']}" not in [line for _, line in group["names"]]:
            lines += [group["about"], ""]
        lines += [f"- `{name}` {line}" for name, line in group["names"]]
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


def differences_text() -> str:
    """One item for each place the two Editions' Hive differs, from DECLARED_DIFFERENCES."""
    return "\n".join(
        f"- **{row.title}** {row.why} sqlglot Composer writes `{row.sqlglot_composer}` where Spark "
        f"Composer writes `{row.spark_composer}`."
        for row in editions.DECLARED_DIFFERENCES.values())


def how_tos_text(source: Path) -> str:
    """Each how-to's number and title, under its group, such as "Getting started, how-tos 1 to
    18:", read from the docstrings in worked_examples/how_to/ that how_to.html is written from.

    Each docstring's line 1 is its title and line 3 names its group, as `For: Getting started`.
    tools/how_to_page.py reads them the same way, but importing it loads an Edition into this
    Python, so the two lines are read here again.
    """
    groups: dict[str, list[tuple[int, str]]] = {}
    for path in sorted((source / HOW_TOS).glob("[0-9][0-9]_*.py")):
        doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) or ""
        laid_out = re.match(r"(?P<title>[^\n]+)\n\nFor: (?P<group>[^\n]+)\n", doc)
        if laid_out is None:
            raise ExportRefused(f"{HOW_TOS}/{path.name}'s docstring must start with its title on "
                                "line 1 and `For: <its group>` on line 3, as tools/how_to_page.py "
                                "reads it.")
        groups.setdefault(laid_out["group"], []).append((int(path.name[:2]), laid_out["title"]))
    if not groups:
        raise ExportRefused(f"There are no how-tos in {HOW_TOS}/ for the README to list.")
    return "\n\n".join(
        f"{group}, how-tos {how_tos[0][0]} to {how_tos[-1][0]}:\n\n"
        + "\n".join(f"{number}. {title}" for number, title in how_tos)
        for group, how_tos in groups.items())


def templates_text(source: Path) -> str:
    """Each Template, by its path inside templates/, with what it is, as templates/README.md's
    tables give them and in their order, each set under its folder's name."""
    rows = re.findall(r"^\| `(\w+/\w+\.py)` \| ([^|]+?) \|",
                      (source / TEMPLATES_README).read_text(encoding="utf-8"), re.MULTILINE)
    files = [path.relative_to(source / TEMPLATES).as_posix()
             for path in (source / TEMPLATES).glob("*/*.py")]
    if sorted(relative for relative, _ in rows) != sorted(files):
        raise ExportRefused(
            f"{TEMPLATES_README}'s tables must name each Template once, and only those, for the "
            f"README to list them in that order: it names {sorted(row[0] for row in rows)}, and "
            f"{TEMPLATES}/ holds {sorted(files)}.")
    sets: dict[str, list[str]] = {}
    for relative, what in rows:
        sets.setdefault(relative.split("/")[0], []).append(f"- `{relative}` - {what}")
    return "\n\n".join(f"In `{folder}/`:\n\n" + "\n".join(lines)
                       for folder, lines in sets.items())


def readme_text(template: str, groups: list[dict], version: str, stamp: str,
                source: Path) -> str:
    """The Clean branch's README: the template, with the version, such as "3.0, exported
    2026-10-02 14:05", the Editions' differences, the how-tos, the Templates and the cheat sheet
    put in, the how-tos and the Templates read from `source`."""
    for marker in (VERSION_MARKER, DIFFERENCES_MARKER, HOW_TOS_MARKER, TEMPLATES_MARKER,
                   CHEAT_SHEET_MARKER):
        if template.count(marker) != 1:
            raise ExportRefused(f"{README_TEMPLATE} must have `{marker}` exactly once.")
    text = template.replace(VERSION_MARKER, version)
    text = text.replace(DIFFERENCES_MARKER, differences_text())
    text = text.replace(HOW_TOS_MARKER, how_tos_text(source))
    text = text.replace(TEMPLATES_MARKER, templates_text(source))
    text = text.replace(CHEAT_SHEET_MARKER, cheat_sheet(groups))
    return stamped("README.md", text, stamp)


# --- Checks across the exported Editions -----------------------------------------------------


def exported_folders() -> list[str]:
    """The Toolbox folders the export ships: the Composer core, then each Edition's."""
    return [editions.CORE] + [edition.folder for edition in editions.EXPORTED]


def check_editions(source: Path) -> None:
    """Refuse an export whose folders don't belong together: each must be in the commit, and
    they must have one version."""
    missing = [folder for folder in exported_folders() if not (source / folder).is_dir()]
    if missing:
        raise ExportRefused(
            f"The export ships {', '.join(exported_folders())}, but this commit doesn't have "
            f"{', '.join(missing)}. Commit the folder on dev, or take its Edition out of "
            "EXPORTED in tools/editions.py.")
    versions = {folder: toolbox_version_of(source, folder) for folder in exported_folders()}
    if len(set(versions.values())) > 1:
        said = " and ".join(f"{folder} is {version}" for folder, version in versions.items())
        raise ExportRefused(
            f"The Toolbox's folders share one version, but {said}. Set TOOLBOX_VERSION in "
            f"every .py file of {', '.join(f'{folder}/' for folder in exported_folders())}, "
            "and commit.")


def cheat_sheet_lines(described: dict) -> list[str]:
    """Each line of the cheat sheet a description gives, less the one holding VERSION's value."""
    lines = []
    for group in described["groups"]:
        lines.append(f"{group['file']}: {group['about']}")
        lines += [f"{group['file']}: `{name}` {line}" for name, line in group["names"]
                  if name != "VERSION"]
    return lines


def check_described_alike(described: list[dict]) -> None:
    """Refuse Editions whose cheat sheets would differ: the README shows only the first's."""
    first = cheat_sheet_lines(described[0])
    for edition, one in zip(editions.EXPORTED[1:], described[1:]):
        theirs = cheat_sheet_lines(one)
        if theirs != first:
            ours = next((line for line in first if line not in theirs), "(nothing)")
            differs = next((line for line in theirs if line not in first), "(nothing)")
            raise ExportRefused(
                f"{edition.product}'s cheat sheet differs from "
                f"{editions.EXPORTED[0].product}'s: it has {differs!r} where "
                f"{editions.EXPORTED[0].product} has {ours!r}. The README shows one cheat sheet "
                "for both, from each file's and each name's docstring's first line, so reword "
                "that line to read the same in both, and commit.")


# How any spelling of each Edition's name is found, such as "Spark Composer" or "spark_composer".
_NAMED = {editions.SQLGLOT_COMPOSER: editions.SQLGLOT_COMPOSER_NAME,
          editions.SPARK_COMPOSER: editions.SPARK_COMPOSER_NAME}


def check_readme(template: str) -> None:
    """Refuse a README template that names an Edition this export doesn't ship."""
    unshipped = [edition.product for edition in editions.EDITIONS.values()
                 if edition not in editions.EXPORTED and _NAMED[edition].search(template)]
    if unshipped:
        raise ExportRefused(
            f"{README_TEMPLATE} names {', '.join(unshipped)}, which this export doesn't ship. "
            "Leave it out of the README until it ships.")


# --- Building and committing ---------------------------------------------------------------------


def copied_files(folder: Path) -> list[str]:
    """Each file of one of the COPIED folders, as a sorted path inside it, such as
    "starter/README.md", leaving out Python's caches."""
    return sorted(path.relative_to(folder).as_posix() for path in folder.rglob("*")
                  if path.is_file() and "__pycache__" not in path.parts)


# What an Example project's README gives PYTHONPATH to find the Toolbox: the folder two up on
# dev, such as `PYTHONPATH=../..` or, for the Windows command prompt, `set PYTHONPATH=..\..`.
DEVS_PYTHONPATH = re.compile(r"(PYTHONPATH=\.\.([/\\])\.\.)(?![/\\.\w])")


def with_mains_paths(text: str, source: Path, edition: editions.Edition) -> str:
    """A copied file's text with each place it names as main has it.

    On main, each Edition's copy sits one folder deeper than on dev, in a folder named for it:
    dev's example_projects/starter/ is main's example_projects/sqlglot_composer/starter/, and
    an Example project's PYTHONPATH reaches one folder further up for the Toolbox.
    """
    for folder in COPIED:
        inside = "|".join(sorted(path.name for path in (source / folder).iterdir()
                                 if path.is_dir() and path.name != "__pycache__"))
        if inside:
            text = re.sub(rf"\b{folder}/(?=(?:{inside})\b)", f"{folder}/{edition.folder}/", text)
    return DEVS_PYTHONPATH.sub(r"\1\2..", text)


def build_copies(source: Path, into: Path, edition: editions.Edition, stamp: str) -> None:
    """Write `edition`'s copy of the Example projects and the Templates into `into`: each file
    named for `edition`, with main's paths, and stamped."""
    for folder in COPIED:
        for relative in copied_files(source / folder):
            where = f"{folder}/{relative}"
            text = (source / folder / relative).read_text(encoding="utf-8")
            try:
                text = editions.named_for(edition, text, where)
            except editions.SwapRefused as why:
                raise ExportRefused(f"{why} Write it so it names sqlglot Composer one way.")
            target = into / folder / edition.folder / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(stamped(where, with_mains_paths(text, source, edition), stamp),
                              encoding="utf-8", newline="\n")


def build_folder(source: Path, into: Path, folder: str, stamp: str) -> None:
    """Copy and stamp one Toolbox folder into `into`, and check its imports."""
    names = sorted(path.name for path in (source / folder).iterdir()
                   if path.name != "__pycache__")
    folders = [name for name in names if (source / folder / name).is_dir()]
    if folders:
        raise ExportRefused(f"The Toolbox is one flat folder, but {folder}/ holds {folders}. "
                            "Move them out of it on dev.")
    (into / folder).mkdir(parents=True)
    for name in names:
        text = (source / folder / name).read_text(encoding="utf-8")
        if name == "__init__.py":
            text = with_file_list(text, names, folder)
        (into / folder / name).write_text(stamped(f"{folder}/{name}", text, stamp),
                                          encoding="utf-8", newline="\n")
    bad_imports = editions.imports_outside(into / folder)
    if bad_imports:
        raise ExportRefused(
            f"The Toolbox may import only the standard library, pandas, numpy and its "
            f"Edition's library where tools/editions.py allows it, which is all work has: "
            f"{'; '.join(f'{folder}/{bad}' for bad in bad_imports)}."
        )
    check_offline(into, [folder])


def build(source: Path, into: Path, when: datetime.datetime) -> str:
    """Build the Clean tree from the `dev` folder `source` into the folder `into`, with each
    Edition EXPORTED in tools/editions.py names.

    Returns what the tree is, as main's commit names it, such as "sqlglot Composer and Spark
    Composer 3.0, exported 2026-10-02 14:05".
    """
    if into.exists() and any(into.iterdir()):
        raise ExportRefused(f"{into} isn't empty. Build the Clean tree into an empty folder.")
    check_editions(source)
    missing = [path for path in (*COPIED, HOW_TOS) if not (source / path).is_dir()]
    if missing:
        raise ExportRefused(
            f"The export ships each Edition's copy of {' and '.join(COPIED)}, and the README "
            f"lists the how-tos, but this commit doesn't have {', '.join(missing)}. Commit it "
            "on dev.")
    template = (source / README_TEMPLATE).read_text(encoding="utf-8")
    check_readme(template)
    version = toolbox_version_of(source, editions.CORE)
    build_folder(source, into, editions.CORE, stamp_text(editions.CORE_PRODUCT, version, when))
    described = []
    for edition in editions.EXPORTED:
        build_folder(source, into, edition.folder, stamp_text(edition.product, version, when))
        described.append(import_stamped(into, edition))
        check_needs_the_core(into, edition)
        build_copies(source, into, edition, copy_stamp_text(edition.product, version, when))
        check_offline(into, [f"{folder}/{edition.folder}" for folder in COPIED])
        check_dry_runs(into, edition)
    check_one_edition_per_python(into)
    check_described_alike(described)
    # The README is every Edition's, so its stamp names them all.
    products = " and ".join(edition.product for edition in editions.EXPORTED)
    (into / README).parent.mkdir()
    (into / README).write_text(
        readme_text(template, described[0]["groups"], version_text(version, when),
                    stamp_text(products, version, when), source),
        encoding="utf-8", newline="\n")
    outside = outside_allowlist(files_in(into))
    if outside:
        raise ExportRefused(f"The Clean tree holds files outside its allowlist: {outside}.")
    return f"{products} {version_text(version, when)}"


def git(repo: Path, *args: str, **options) -> str:
    """Run git in `repo` and return what it prints; a failure stops the export."""
    done = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True,
                          encoding="utf-8", **options)
    if done.returncode != 0:
        raise ExportRefused(f"`git {' '.join(args)}` failed: {done.stderr.strip()}")
    return done.stdout.strip()


def refusal_before_export(repo: Path) -> str | None:
    """Why `dev` can't be exported as it stands, or None if it can."""
    if git(repo, "rev-parse", "--abbrev-ref", "HEAD") != "dev":
        return "The export copies what `dev` has committed. Check out dev first."
    if git(repo, "status", "--porcelain"):
        return ("There are uncommitted changes. Commit them on dev first, so that main gets "
                "exactly what dev has committed.")
    still_open = open_drift_items((repo / DRIFT_LIST).read_text(encoding="utf-8"))
    if still_open:
        return (f"Drift items {', '.join(still_open)} are still open in {DRIFT_LIST}. Fix them "
                "on dev first: drift never reaches main.")
    if "branch refs/heads/main" in git(repo, "worktree", "list", "--porcelain").splitlines():
        return ("main is checked out in one of this repo's worktrees. Check out another "
                "branch there first, since the export moves main.")
    return None


def tree_of(repo: Path, into: Path, index: Path) -> str:
    """Store the Clean tree in `into` in the repo's objects, and return the tree's hash.

    It uses its own index file, so the index of the `dev` checkout is never touched.
    """
    git_dir = git(repo, "rev-parse", "--absolute-git-dir")
    environment = dict(os.environ, GIT_INDEX_FILE=str(index))
    where = ["--git-dir", git_dir, "--work-tree", str(into)]
    git(into, *where, "add", "--all", env=environment)
    tree = git(into, *where, "write-tree", env=environment)
    built = files_in(into)
    stored = git(repo, "ls-tree", "-r", "--name-only", tree).splitlines()
    if stored != built or outside_allowlist(stored):
        raise ExportRefused(f"git stored {stored}, but the export built {built}.")
    return tree


def committed_files(repo: Path, commit: str, into: Path) -> Path:
    """Write what `commit` holds of the Toolbox's folders, the Example projects, the Templates,
    the how-tos and the README template into `into`.

    The build reads these rather than the checkout, so a file git ignores (a stray log, say)
    can never reach `main`. A folder the commit lacks is left out, for the build to refuse.
    """
    held = git(repo, "ls-tree", "--name-only", commit).splitlines()
    paths = [folder for folder in [*exported_folders(), *COPIED] if folder in held]
    paths.append(README_TEMPLATE)
    if HOW_TOS.split("/")[0] in held:
        paths.append(HOW_TOS)
    archive = subprocess.run(
        ["git", "-C", str(repo), "archive", "--format=tar", commit, *paths],
        capture_output=True,
    )
    if archive.returncode != 0:
        raise ExportRefused(f"`git archive` failed: {archive.stderr.decode(errors='replace')}")
    with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as files:
        files.extractall(into, filter="data")
    return into


def export(repo: Path, when: datetime.datetime) -> str:
    """Build the Clean tree from `dev` and commit it to `main`; return the new commit's hash."""
    why = refusal_before_export(repo)
    if why:
        raise ExportRefused(why)
    dev = git(repo, "rev-parse", "HEAD")
    old_main = subprocess.run(
        ["git", "-C", str(repo), "rev-parse", "--verify", "--quiet", "refs/heads/main"],
        capture_output=True, text=True, encoding="utf-8",
    ).stdout.strip()
    with tempfile.TemporaryDirectory() as temporary:
        committed = committed_files(repo, dev, Path(temporary) / "dev")
        version = build(committed, Path(temporary) / "clean", when)
        tree = tree_of(repo, Path(temporary) / "clean", Path(temporary) / "index")
    message = (f"{version}\n\nGenerated from dev {dev} by tools/export_clean.py. "
               "Never edit this branch by hand.")
    parent = ["-p", old_main] if old_main else []
    commit = git(repo, "commit-tree", tree, *parent, "-m", message)
    # Moves main only if it still points where it did when the export started.
    git(repo, "update-ref", "refs/heads/main", commit, old_main)
    return commit


def main(arguments: list[str]) -> int:
    try:
        if len(arguments) == 2 and arguments[0] == "--preview":
            version = build(ROOT, Path(arguments[1]), datetime.datetime.now())
            print(f"Built {version} into {arguments[1]}. Nothing was committed.")
        elif not arguments:
            commit = export(ROOT, datetime.datetime.now())
            print(f"main is now {commit[:7]}: {git(ROOT, 'log', '-1', '--format=%s', commit)}.")
            print("Nothing was pushed. Push it yourself: git push origin main")
        else:
            print(__doc__)
            return 2
    except ExportRefused as why:
        print(f"Export refused, and main is as it was: {why}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
