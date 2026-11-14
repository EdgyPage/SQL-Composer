"""Export the Clean branch: build `main` from `dev`, check it, and commit it to `main` locally.

Run it with `dev` checked out and nothing uncommitted:

    python tools/export_clean.py

It builds the Clean tree in a temporary folder, from what `dev` has committed:

- it copies the Toolbox's folder, `sqlglot_composer/`, as dev holds it, and adds to its
  `version.txt` when it was exported, from which dev commit, and each file's git hash, for the
  import self-check (ADR 0013); no other file of the folder changes, so an export changes only
  the files whose content changed;
- it copies the pages, which dev writes into `docs/main/`, into main's `docs/`, as dev holds
  them: the how-tos, the Example gallery, the Workflows overview and the Example projects page
  (Toolbox 8.7, ticket 13); and beside them, in `docs/example_projects/`, each Example
  project's lineage pages, which the Example projects page links. Main holds no Example
  project, nor the Example database: a user reads them on the pages. The Templates ship inside
  the Toolbox, in `sqlglot_composer/project_templates.py`;
- it copies the Copilot files, `copilot/`, at the same paths: each .txt as dev holds it,
  unstamped, as Copilot counts every character; `count_characters.py` and `workbook_text.py`
  with line 1 stamped with the version alone, for example
  `# sqlglot Composer 7.2 - copy it, then edit your copy`; and the empty Formula workbook,
  `formula_workbook.xlsx`, and the examples of it, `examples/*.xlsx`, byte for byte, as main
  can't rebuild them;
- it writes `.github/README.md` from `docs/clean-branch-readme.md`, putting in the version, the
  list of how-tos, from `worked_examples/how_to/`, and a cheat sheet: one line per public name,
  grouped by file, from each docstring's first line;
- it copies `CHANGES.md`, what changed in each version, `LICENSE`, the MIT No Attribution
  license, and `requirements.txt`, what the Toolbox needs beyond the standard library, as dev
  holds them, with no stamp.

It then checks what it built:

- each Toolbox file imports only what work has (the standard library, pandas, numpy, and sqlglot
  where `tools/toolbox_registry.py` allows it);
- the exported folder imports in a fresh Python, in the Clean tree and copied on its own;
- each file is read by `tools/offline_policy.py`, as main would hold it, before anything in it
  is imported or run: the Toolbox and the Templates, the pages, the Copilot files, and the
  README, Markdown and plain text read as pages, so that none of it can reach the network;
- no file imports the Example database, which main doesn't hold;
- the folder's `version.txt` names the Toolbox and its version;
- the tree holds nothing outside its allowlist: the Toolbox's folder, flat, the pages and the
  lineage pages they link, the Copilot files, `.github/README.md`, `CHANGES.md`, `LICENSE` and
  `requirements.txt`.

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
import hashlib
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

import toolbox_registry
import offline_policy

ROOT = Path(__file__).resolve().parent.parent
DRIFT_LIST = ".scratch/drift.md"
README = ".github/README.md"
README_TEMPLATE = "docs/clean-branch-readme.md"
# The files main holds at its root, each dev's copy unchanged and unstamped: the change notes,
# the license, MIT No Attribution, which GitHub reads as is, and requirements.txt, which pip
# does.
CHANGES = "CHANGES.md"
LICENSE = "LICENSE"
REQUIREMENTS = "requirements.txt"
ROOT_FILES = (CHANGES, LICENSE, REQUIREMENTS)
VERSION_MARKER = "<!-- VERSION -->"
CHEAT_SHEET_MARKER = "<!-- CHEAT SHEET -->"
# The folder main holds a copy of, for the user to copy and edit, at the paths dev has it.
COPILOT = "copilot"
COPIED = (COPILOT,)
# The pages: dev writes them into DOCS_ON_DEV, and main holds them in DOCS, beside the lineage
# pages of dev's Example projects, which main holds no other file of (Toolbox 8.7, ticket 13).
DOCS = toolbox_registry.DOCS
DOCS_ON_DEV = toolbox_registry.DOCS_ON_DEV
EXAMPLE_PROJECTS = toolbox_registry.EXAMPLE_PROJECTS
# A line that imports the Example database, which main doesn't hold.
EXAMPLE_DATABASE_IMPORT = re.compile(
    rf"\bimport {toolbox_registry.EXAMPLE_DATABASE}\b"
    rf"|\bfrom {toolbox_registry.EXAMPLE_DATABASE}(\.\w+)* import\b")
# The copies with no stamp: a Copilot file, counted character by character, and the Formula
# workbook and its examples, which aren't text.
UNSTAMPED = (".txt", ".xlsx")
# The copies that aren't text: the empty Formula workbook and its examples, which main can't
# rebuild, since openpyxl, which builds them, is dev's alone.
BINARY = (".xlsx",)
# The how-tos, which how_to.html is written from, and which the README lists.
HOW_TOS = "worked_examples/how_to"
HOW_TOS_MARKER = "<!-- HOW-TOS -->"


class ExportRefused(Exception):
    """The export stopped before touching `main`; the message says why and what to do."""


def version_text(toolbox_version: str, when: datetime.datetime) -> str:
    """A version and the time it was exported, such as "3.0, exported 2026-10-02 14:05"."""
    return f"{toolbox_version}, exported {when.strftime('%Y-%m-%d %H:%M')}"


def stamp_text(product: str, toolbox_version: str, when: datetime.datetime) -> str:
    """The README's line-1 stamp, such as "sqlglot Composer 3.0, exported 2026-10-02 14:05 -
    ..."."""
    return f"{product} {version_text(toolbox_version, when)} - generated from dev, do not edit"


def copy_stamp_text(product: str, toolbox_version: str) -> str:
    """The line-1 stamp of an Example project's file, such as "sqlglot Composer 7.2 - copy it,
    then edit your copy". It names no export time, so an export changes it only when the
    version changes."""
    return f"{product} {toolbox_version} - copy it, then edit your copy"


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


# Dev's version.txt: one line, the Toolbox and its version, such as "sqlglot Composer 7.2".
DEV_VERSION_FILE = re.compile(
    rf"{re.escape(toolbox_registry.PRODUCT)} (?P<version>\d+\.\d+)\n?")


def toolbox_version_of(source: Path, folder: str) -> str | None:
    """The version dev's `version.txt` names, such as "7.2", or None if it holds anything but
    the one line `DEV_VERSION_FILE` reads."""
    path = source / folder / toolbox_registry.VERSION_FILE
    if not path.is_file():
        return None
    found = DEV_VERSION_FILE.fullmatch(path.read_text(encoding="utf-8"))
    return found["version"] if found else None


def git_hash(data: bytes) -> str:
    """The hash `git hash-object` gives a file holding `data`, with its line endings as LF, as
    the import self-check works it out (`checks.git_hash`)."""
    data = data.replace(b"\r\n", b"\n")
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def version_file_text(product: str, toolbox_version: str, when: datetime.datetime, commit: str,
                      hashes: dict[str, str]) -> str:
    """The exported folder's version.txt: the Toolbox and its version, when and from which dev
    commit it was exported, and each other file of the folder with its git hash."""
    note = (
        "# Each file of this folder, and a code worked out from its contents (its git hash),\n"
        "# so the import can warn about a file that differs. Written by the export: don't\n"
        "# edit it.\n")
    listed = "".join(f"{hashes[name]}  {name}\n" for name in sorted(hashes))
    return (f"{product} {toolbox_version}\n"
            f"exported {when.strftime('%Y-%m-%d %H:%M')} from dev commit {commit}\n"
            + note + listed)


def describe_toolbox(folder: str) -> dict[str, str | list[dict[str, str | list[list[str]]]]]:
    """Import the Toolbox's folder and describe it for the cheat sheet, grouped by file.

    This runs in a fresh Python started inside the Clean tree (see `import_exported`), so the
    folder it imports is the exported copy, and its import self-check runs on that copy.
    """
    toolbox = __import__(folder)
    groups: dict[str, dict[str, str | list[list[str]]]] = {}
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
    # The admin and project modules, imported by name: their functions, as admin.<name>, after
    # any name of the star import the file holds, such as project.py's database_settings.
    for module_name in ("admin", "project"):
        module = getattr(toolbox, module_name)
        group = groups.setdefault(Path(module.__file__).name, {
            "file": Path(module.__file__).name, "about": first_line(module.__doc__),
            "names": []})
        group["names"] += [[f"{module_name}.{name}",
                            "- " + first_line(inspect.getdoc(getattr(module, name)))]
                           for name in module.__all__]
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


def fresh_python(folder: Path, code: str, path: str | None = None
                 ) -> subprocess.CompletedProcess[str]:
    """Run `code` in a fresh Python started in `folder`, with `path`, if given, as its
    PYTHONPATH, and nothing else on it."""
    environment = {name: value for name, value in os.environ.items() if name != "PYTHONPATH"}
    environment["PYTHONIOENCODING"] = "utf-8"
    if path is not None:
        environment["PYTHONPATH"] = path
    return subprocess.run(
        [sys.executable, "-B", "-c", code],
        cwd=folder, env=environment, capture_output=True, text=True, encoding="utf-8",
    )


def import_exported(into: Path) -> dict[str, str | list[dict[str, str | list[list[str]]]]]:
    """Import the exported folder in a fresh Python, and return `describe_toolbox()` of it."""
    folder = toolbox_registry.FOLDER
    done = fresh_python(
        into, "import json, export_clean; "
        f"print(json.dumps(export_clean.describe_toolbox({folder!r})))",
        path=str(Path(__file__).parent))
    if done.returncode != 0:
        raise ExportRefused(
            f"The exported copy of {toolbox_registry.PRODUCT} doesn't import, so nothing was "
            f"exported:\n{last_error(done.stderr)}"
        )
    described = json.loads(done.stdout.strip().splitlines()[-1])
    if Path(described["folder"]).resolve() != (into / folder).resolve():
        raise ExportRefused(f"The import check found another {folder}: {described['folder']}")
    return described


def check_imports_alone(into: Path) -> None:
    """Refuse an exported folder that imports only with something else beside it: at work it is
    copied on its own, into a folder of the user's."""
    folder = toolbox_registry.FOLDER
    with tempfile.TemporaryDirectory() as alone:
        shutil.copytree(into / folder, Path(alone) / folder)
        done = fresh_python(Path(alone), f"import {folder}")
    if done.returncode != 0:
        raise ExportRefused(f"{folder}, copied on its own, doesn't import, so nothing was "
                            f"exported:\n{last_error(done.stderr)}")


def docs_files(source: Path) -> dict[str, Path]:
    """Each file main's docs/ holds, by its path there, such as how_to.html, and the file on
    dev it is a copy of: each page dev wrote into DOCS_ON_DEV, and each Example project's
    lineage page, which the Example projects page links, at its path from dev's top."""
    pages = sorted(path.name for path in (source / DOCS_ON_DEV).iterdir())
    unlisted = [name for name in pages if name not in toolbox_registry.PAGES]
    if unlisted:
        raise ExportRefused(
            f"{DOCS_ON_DEV}/ holds {', '.join(unlisted)}, but tools/toolbox_registry.py's "
            "PAGES doesn't list it. Add it to PAGES there, or move it out of the folder on "
            "dev.")
    missing = [name for name in toolbox_registry.PAGES if name not in pages]
    if missing:
        raise ExportRefused(f"main's docs/ ships {', '.join(missing)}, but this commit's "
                            f"{DOCS_ON_DEV}/ doesn't have it. Write it with its tool, and "
                            "commit it on dev.")
    return {**{name: source / DOCS_ON_DEV / name for name in pages},
            **toolbox_registry.lineage_pages(source)}


def build_docs(source: Path, into: Path) -> None:
    """Write main's docs/ into `into`: each page as dev holds it, unstamped, and each lineage
    page it links beside it; then read them as main would."""
    for shipped, original in docs_files(source).items():
        target = into / DOCS / shipped
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(original.read_text(encoding="utf-8"), encoding="utf-8",
                          newline="\n")
    check_offline(into, [DOCS])


def example_database_imports(path: str, text: str) -> list[int]:
    """The lines of a file of main's that import the Example database, or show a line that
    does for a user to run: in Python, each import statement naming it, as a string that only
    names it, such as an older Upgrade step's text, imports nothing; in a page or other text,
    each such line it shows."""
    if path.endswith(".py"):
        return [node.lineno for node in ast.walk(ast.parse(text))
                if toolbox_registry.EXAMPLE_DATABASE in imported_by(node)]
    return [number for number, line in enumerate(text.splitlines(), 1)
            if EXAMPLE_DATABASE_IMPORT.search(line)]


def imported_by(node: ast.AST) -> list[str]:
    """The top modules an import statement imports by name, such as ["pandas"] for `import
    pandas as pd`; none for any other statement, or an import from its own folder."""
    if isinstance(node, ast.Import):
        return [alias.name.split(".")[0] for alias in node.names]
    if isinstance(node, ast.ImportFrom) and node.level == 0:
        return [(node.module or "").split(".")[0]]
    return []


def check_no_example_database(into: Path) -> None:
    """Refuse a Clean tree with a line that imports the Example database: main doesn't hold
    it, so a user reads its tables on the pages. CHANGES.md, what each version did, may name
    the imports it once wrote."""
    found = []
    for path in files_in(into):
        if path.endswith(BINARY) or path == CHANGES:
            continue
        found += [f"{path}:{number}" for number in example_database_imports(
            path, (into / path).read_text(encoding="utf-8"))]
    if found:
        raise ExportRefused(
            f"The Clean tree imports the Example database, which main doesn't hold, at "
            f"{', '.join(found)}. Show its tables on a page, and connect with connect(conn), "
            "as the how-tos do.")


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
    the network, as `tools/offline_policy.py` reads it under main's path: in the Toolbox, only
    the reviewed sites in its ALLOWED; in the pages and the Copilot files, nothing. Markdown
    and plain text are read as pages, for what a preview of one would load, and a Copilot file
    for a link Copilot might follow."""
    found = offline_policy.scan(into, paths)
    for path in files_in(into):
        if path.endswith((".md", ".txt")) and any(path == part or path.startswith(f"{part}/")
                                                  for part in paths):
            found += offline_policy.page_findings(
                (into / path).read_text(encoding="utf-8"), path)
    if found:
        raise ExportRefused(
            "The Clean tree holds something that could reach the network, but the Toolbox, "
            "its Templates, its pages and its Copilot files reach nothing but the "
            "user's query and execute. "
            "tools/offline_policy.py found, as main would hold it, line 1 being the export's "
            "stamp where the file has one:\n"
            + "".join(f"  {finding}\n" for finding in found)
            + "Take each out on dev. A Toolbox site that must stay needs a reviewed entry in "
            "ALLOWED in tools/offline_policy.py, with the user's OK.")


def files_in(folder: Path) -> list[str]:
    """Every file under `folder`, as sorted paths relative to it, such as
    ".github/README.md"."""
    return sorted(path.relative_to(folder).as_posix() for path in folder.rglob("*")
                  if path.is_file())


def outside_allowlist(paths: list[str]) -> list[str]:
    """The paths `main` may not hold: it holds the Toolbox's flat folder, the Templates inside
    it, the pages in docs/ and the Example projects' lineage pages beside them, the Copilot
    files, the README, the change notes, the license and requirements.txt."""
    def allowed(path: str) -> bool:
        parts = path.split("/")
        return (path == README or path in ROOT_FILES
                or (len(parts) == 2 and parts[0] == toolbox_registry.FOLDER)
                or (len(parts) == 2 and parts[0] == DOCS and parts[1] in toolbox_registry.PAGES)
                or (len(parts) > 4 and parts[:2] == [DOCS, EXAMPLE_PROJECTS]
                    and parts[-2] == "lineage" and path.endswith(".html"))
                or (len(parts) > 1 and parts[0] in COPIED))

    return [path for path in paths if not allowed(path)]


def cheat_sheet(groups: list[dict[str, str | list[list[str]]]]) -> str:
    """One Markdown section per Toolbox file, with one line per public name in it."""
    sections = []
    for group in groups:
        lines = [f"### `{group['file']}`", "", group["about"], ""]
        lines += [f"- `{name}` {line}" for name, line in group["names"]]
        sections.append("\n".join(lines))
    return "\n\n".join(sections)


def how_tos_text(source: Path) -> str:
    """Each how-to's number and title, linked to it on how_to.html, under its group, such as
    "Getting started, how-tos 1 to 8:", read from the docstrings in worked_examples/how_to/ that
    how_to.html is written from. The README is at .github/README.md, so a link goes up one
    folder.

    Each docstring's line 1 is its title and line 3 names its group, as `For: Getting started`,
    and the files' numbers give each group's first and last: the how-tos are numbered 1, 2, 3
    and on, each group's in a row. tools/how_to_page.py reads them the same way and checks
    their numbers, but importing it loads the Toolbox into this Python, so the two lines are
    read here again. The page is main's docs/how_to.html.
    """
    groups: dict[str, list[tuple[int, str, str]]] = {}
    for path in sorted((source / HOW_TOS).glob("[0-9][0-9]_*.py")):
        doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) or ""
        laid_out = re.match(r"(?P<title>[^\n]+)\n\nFor: (?P<group>[^\n]+)\n", doc)
        if laid_out is None:
            raise ExportRefused(f"{HOW_TOS}/{path.name}'s docstring must start with its title "
                                "on line 1 and `For: <its group>` on line 3, as "
                                "tools/how_to_page.py reads it.")
        groups.setdefault(laid_out["group"], []).append(
            (int(path.name[:2]), laid_out["title"], path.stem[3:]))
    if not groups:
        raise ExportRefused(f"There are no how-tos in {HOW_TOS}/ for the README to list.")
    numbers = []
    for how_tos in groups.values():
        numbers += [number for number, _, _ in how_tos]
    if numbers != list(range(1, len(numbers) + 1)):
        raise ExportRefused(f"The how-tos in {HOW_TOS}/ must be numbered 1, 2, 3 and on, each "
                            "group's in a row, as tools/how_to_page.py checks.")
    page = f"../{DOCS}/how_to.html"
    sections = []
    for group, how_tos in groups.items():
        links = "\n".join(f"{number}. [{title}]({page}#{slug})"
                          for number, title, slug in how_tos)
        sections.append(f"{group}, how-tos {how_tos[0][0]} to {how_tos[-1][0]}:\n\n{links}")
    return "\n\n".join(sections)


def readme_text(template: str, groups: list[dict[str, str | list[list[str]]]], version: str,
                stamp: str, source: Path) -> str:
    """The Clean branch's README: the template, with the version, such as "3.0, exported
    2026-10-02 14:05", the how-tos and the cheat sheet put in, the how-tos read from
    `source`."""
    for marker in (VERSION_MARKER, HOW_TOS_MARKER, CHEAT_SHEET_MARKER):
        if template.count(marker) != 1:
            raise ExportRefused(f"{README_TEMPLATE} must have `{marker}` exactly once.")
    text = template.replace(VERSION_MARKER, version)
    text = text.replace(HOW_TOS_MARKER, how_tos_text(source))
    text = text.replace(CHEAT_SHEET_MARKER, cheat_sheet(groups))
    return stamped("README.md", text, stamp)


# --- Checks on the commit ------------------------------------------------------------------


def check_folder(source: Path) -> None:
    """Refuse a commit without the Toolbox's folder, or whose `version.txt` doesn't hold the
    Toolbox and its version alone, as dev's does."""
    folder, product = toolbox_registry.FOLDER, toolbox_registry.PRODUCT
    if not (source / folder).is_dir():
        raise ExportRefused(f"The export ships {folder}, but this commit doesn't have it. "
                            "Commit the folder on dev.")
    if toolbox_version_of(source, folder) is None:
        raise ExportRefused(
            f"{folder}/{toolbox_registry.VERSION_FILE} must hold one line on dev, the Toolbox "
            f'and its version, such as "{product} 7.2": the export adds the rest. Put it back, '
            "and commit.")


# --- Building and committing ---------------------------------------------------------------


def copied_files(folder: Path) -> list[str]:
    """Each file of one of the COPIED folders, as a sorted path inside it, such as
    "starter/README.md", leaving out Python's caches."""
    return sorted(path.relative_to(folder).as_posix() for path in folder.rglob("*")
                  if path.is_file() and "__pycache__" not in path.parts)


def build_copies(source: Path, into: Path, stamp: str) -> None:
    """Write the Copilot files into `into`, at dev's paths, its Python stamped. A Copilot file
    is counted character by character, so each is copied as it is, and the empty Formula
    workbook and its examples, which aren't text, byte for byte."""
    for folder in COPIED:
        for relative in copied_files(source / folder):
            where = f"{folder}/{relative}"
            target = into / folder / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            if relative.endswith(BINARY):
                target.write_bytes((source / folder / relative).read_bytes())
                continue
            text = (source / folder / relative).read_text(encoding="utf-8")
            if not relative.endswith(UNSTAMPED):
                text = stamped(where, text, stamp)
            target.write_text(text, encoding="utf-8", newline="\n")


def build_folder(source: Path, into: Path, folder: str) -> dict[str, str]:
    """Copy one Toolbox folder into `into` as dev holds it, all but its version.txt, which
    `build` writes, check its imports, and return each file's git hash by name."""
    names = sorted(path.name for path in (source / folder).iterdir()
                   if path.name != "__pycache__")
    folders = [name for name in names if (source / folder / name).is_dir()]
    if folders:
        raise ExportRefused(f"The Toolbox is one flat folder, but {folder}/ holds {folders}. "
                            "Move them out of it on dev.")
    unlisted = [f"{folder}/{name}" for name in names if name not in toolbox_registry.FILES]
    if unlisted:
        raise ExportRefused(
            f"{', '.join(unlisted)} {'is' if len(unlisted) == 1 else 'are'} in the Toolbox's "
            "folder, but tools/toolbox_registry.py doesn't list it. Add it to FILES there, or "
            "move it out of the folder on dev.")
    (into / folder).mkdir(parents=True)
    hashes: dict[str, str] = {}
    for name in names:
        if name == toolbox_registry.VERSION_FILE:
            continue
        text = (source / folder / name).read_text(encoding="utf-8")
        (into / folder / name).write_text(text, encoding="utf-8", newline="\n")
        hashes[name] = git_hash((into / folder / name).read_bytes())
    bad_imports = toolbox_registry.imports_outside(into / folder)
    if bad_imports:
        raise ExportRefused(
            f"The Toolbox may import only the standard library, pandas, numpy and sqlglot "
            f"where tools/toolbox_registry.py allows it, which is all work has: "
            f"{'; '.join(f'{folder}/{bad}' for bad in bad_imports)}."
        )
    check_offline(into, [folder])
    return hashes


def check_root_files(source: Path) -> None:
    """Refuse a dev commit without each file main holds at its root."""
    missing = [name for name in ROOT_FILES if not (source / name).is_file()]
    if missing:
        raise ExportRefused(f"main ships dev's {' and '.join(missing)}, but this commit "
                            "doesn't have it. Commit it on dev.")


def copy_root_files(source: Path, into: Path) -> None:
    """Copy each file main holds at its root as dev holds it, and read it as main would."""
    for name in ROOT_FILES:
        (into / name).write_text((source / name).read_text(encoding="utf-8"),
                                 encoding="utf-8", newline="\n")
    check_offline(into, list(ROOT_FILES))


def build(source: Path, into: Path, when: datetime.datetime, commit: str) -> str:
    """Build the Clean tree from the `dev` folder `source`, the dev commit `commit`, into the
    folder `into`.

    Returns what the tree is, as main's commit names it, such as "sqlglot Composer 6.0,
    exported 2026-10-20 14:05".
    """
    if into.exists() and any(into.iterdir()):
        raise ExportRefused(f"{into} isn't empty. Build the Clean tree into an empty folder.")
    check_folder(source)
    missing = [path for path in (*COPIED, DOCS_ON_DEV, EXAMPLE_PROJECTS, HOW_TOS)
               if not (source / path).is_dir()]
    if missing:
        raise ExportRefused(
            f"The export ships {' and '.join(COPIED)}, the pages in {DOCS_ON_DEV} and the "
            f"lineage pages of {EXAMPLE_PROJECTS}, and the README lists the how-tos, but this "
            f"commit doesn't have {', '.join(missing)}. Commit it on dev.")
    check_root_files(source)
    template = (source / README_TEMPLATE).read_text(encoding="utf-8")
    folder, product = toolbox_registry.FOLDER, toolbox_registry.PRODUCT
    version = toolbox_version_of(source, folder)
    hashes = build_folder(source, into, folder)
    (into / folder / toolbox_registry.VERSION_FILE).write_text(
        version_file_text(product, version, when, commit, hashes), encoding="utf-8",
        newline="\n")
    described = import_exported(into)
    check_imports_alone(into)
    build_copies(source, into, copy_stamp_text(product, version))
    check_offline(into, list(COPIED))
    build_docs(source, into)
    (into / README).parent.mkdir()
    (into / README).write_text(
        readme_text(template, described["groups"], version_text(version, when),
                    stamp_text(product, version, when), source),
        encoding="utf-8", newline="\n")
    check_offline(into, [README])
    copy_root_files(source, into)
    check_no_example_database(into)
    outside = outside_allowlist(files_in(into))
    if outside:
        raise ExportRefused(f"The Clean tree holds files outside its allowlist: {outside}.")
    return f"{product} {version_text(version, when)}"


def git(repo: Path, *args: str, **options: dict[str, str]) -> str:
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


def store_tree(repo: Path, into: Path, index: Path) -> str:
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
    """Write what `commit` holds of the Toolbox's folder, the Copilot files, the pages, the
    Example projects, whose lineage pages ship, the how-tos, the README template, the change
    notes, the license and requirements.txt into `into`.

    The build reads these rather than the checkout, so a file git ignores (a stray log, say)
    can never reach `main`. A folder the commit lacks is left out, for the build to refuse.
    """
    held = git(repo, "ls-tree", "--name-only", commit).splitlines()
    paths = [folder for folder in [toolbox_registry.FOLDER, *COPIED, EXAMPLE_PROJECTS]
             if folder in held]
    if git(repo, "ls-tree", "--name-only", commit, f"{DOCS_ON_DEV}/"):
        paths.append(DOCS_ON_DEV)
    paths.append(README_TEMPLATE)
    paths += [name for name in ROOT_FILES if name in held]
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
        version = build(committed, Path(temporary) / "clean", when, dev)
        tree = store_tree(repo, Path(temporary) / "clean", Path(temporary) / "index")
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
            # A preview builds the checkout, which may hold changes no commit has.
            head = git(ROOT, "rev-parse", "HEAD")
            version = build(ROOT, Path(arguments[1]), datetime.datetime.now(),
                            f"{head} (a preview of the checkout)")
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
