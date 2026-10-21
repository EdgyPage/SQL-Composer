"""Export the Clean branch: build `main` from `dev`, check it, and commit it to `main` locally.

Run it with `dev` checked out and nothing uncommitted:

    python tools/export_clean.py

It builds the Clean tree in a temporary folder, from what `dev` has committed:

- it copies the Toolbox's folder, `sqlglot_composer/`, and stamps line 1 of every file in it, for
  example `# sqlglot Composer 6.0, exported 2026-10-20 14:05 - generated from dev, do not edit`;
- it writes the list of the folder's files into its `__init__.py`, for the import self-check;
- it copies the Example projects, `example_projects/`, at the same paths, with line 1
  stamped, for example
  `# sqlglot Composer 6.0, exported 2026-10-20 14:05 - copy it, then edit your copy`; the
  Templates ship inside the Toolbox, in `sqlglot_composer/project_templates.py`;
- it writes `.github/README.md` from `docs/clean-branch-readme.md`, putting in the version, the
  list of how-tos, from `worked_examples/how_to/`, and a cheat sheet: one line per public name,
  grouped by file, from each docstring's first line;
- it copies `CHANGES.md`, what changed in each version, `LICENSE`, the MIT No Attribution
  license, and `requirements.txt`, what the Toolbox needs beyond the standard library, as dev
  holds them, with no stamp.

It then checks what it built:

- each Toolbox file imports only what work has (the standard library, pandas, numpy, and sqlglot
  where `tools/toolbox_registry.py` allows it);
- the stamped folder imports in a fresh Python, in the Clean tree and copied on its own;
- each Example project's `run_pipeline.py` runs its dry run, in a fresh Python, finding the
  Toolbox as its README says, and leaves no file behind; a dry run prints every step's Hive and
  sends nothing;
- each file is read by `tools/offline_policy.py`, as main would hold it, before anything in it
  is imported or run: the Toolbox, the Example projects and the Templates, and the README,
  pages included and Markdown read as pages, so that none of it can reach the network;
- the folder has one version;
- the tree holds nothing outside its allowlist: the Toolbox's folder, flat, the Example projects
  and the Templates, `.github/README.md`, `CHANGES.md`, `LICENSE` and `requirements.txt`.

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
# The folders main holds a copy of, for the user to copy and edit, at the paths dev has them.
EXAMPLE_PROJECTS = "example_projects"
COPIED = (EXAMPLE_PROJECTS,)
# The how-tos, which how_to.html is written from, and which the README lists.
HOW_TOS = "worked_examples/how_to"
HOW_TOS_MARKER = "<!-- HOW-TOS -->"


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
    """Import the Toolbox's folder and describe it for the cheat sheet, grouped by file.

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
    # The admin and project modules, imported by name: their functions, as admin.<name>.
    for module_name in ("admin", "project"):
        module = getattr(toolbox, module_name)
        groups[Path(module.__file__).name] = {
            "file": Path(module.__file__).name, "about": first_line(module.__doc__),
            "names": [[f"{module_name}.{name}",
                       "- " + first_line(inspect.getdoc(getattr(module, name)))]
                      for name in module.__all__]}
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


def fresh_python(folder: Path, code: str, path: str | None = None) -> subprocess.CompletedProcess:
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


def import_stamped(into: Path) -> dict:
    """Import the stamped folder in a fresh Python, and return `describe_toolbox()` of it."""
    folder = toolbox_registry.FOLDER
    done = fresh_python(
        into, "import json, export_clean; "
        f"print(json.dumps(export_clean.describe_toolbox({folder!r})))",
        path=str(Path(__file__).parent))
    if done.returncode != 0:
        raise ExportRefused(
            f"The stamped copy of {toolbox_registry.PRODUCT} doesn't import, so nothing was "
            f"exported:\n{last_error(done.stderr)}"
        )
    described = json.loads(done.stdout.strip().splitlines()[-1])
    if Path(described["folder"]).resolve() != (into / folder).resolve():
        raise ExportRefused(f"The import check found another {folder}: {described['folder']}")
    return described


def check_imports_alone(into: Path) -> None:
    """Refuse a stamped folder that imports only with something else beside it: at work it is
    copied on its own, into a folder of the user's."""
    folder = toolbox_registry.FOLDER
    with tempfile.TemporaryDirectory() as alone:
        shutil.copytree(into / folder, Path(alone) / folder)
        done = fresh_python(Path(alone), f"import {folder}")
    if done.returncode != 0:
        raise ExportRefused(f"{folder}, copied on its own, doesn't import, so nothing was "
                            f"exported:\n{last_error(done.stderr)}")


# Where an Example project on main finds the Toolbox: the Clean tree's top folder, two up.
TOOLBOX_FROM_A_PROJECT = os.path.join(os.pardir, os.pardir)


def check_dry_runs(into: Path) -> None:
    """Run each Example project's run_pipeline.py, as its README says, in a fresh Python, and
    refuse one that stops or prints no Hive. Its dry run prints the Hive of every step and
    sends nothing."""
    for script in sorted((into / EXAMPLE_PROJECTS).glob("*/run_pipeline.py")):
        before = files_in(into)
        done = fresh_python(
            script.parent, "import runpy; runpy.run_path('run_pipeline.py', run_name='__main__')",
            path=TOOLBOX_FROM_A_PROJECT)
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
    the network, as `tools/offline_policy.py` reads it under main's path: in the Toolbox, only
    the reviewed sites in its ALLOWED; in a copy the user takes, nothing. Markdown is read as a
    page, for what a preview of it would load."""
    found = offline_policy.scan(into, paths)
    for path in files_in(into):
        if path.endswith(".md") and any(path == part or path.startswith(f"{part}/")
                                        for part in paths):
            found += offline_policy.page_findings(
                (into / path).read_text(encoding="utf-8"), path)
    if found:
        raise ExportRefused(
            "The Clean tree holds something that could reach the network, but the Toolbox, "
            "its Example projects and its Templates reach nothing but the user's send. "
            "tools/offline_policy.py found, as main would hold it, line 1 being the export's "
            "stamp:\n"
            + "".join(f"  {finding}\n" for finding in found)
            + "Take each out on dev. A Toolbox site that must stay needs a reviewed entry in "
            "ALLOWED in tools/offline_policy.py, with the user's OK.")


def files_in(folder: Path) -> list[str]:
    """Every file under `folder`, as sorted paths relative to it, such as ".github/README.md"."""
    return sorted(path.relative_to(folder).as_posix() for path in folder.rglob("*")
                  if path.is_file())


def outside_allowlist(paths: list[str]) -> list[str]:
    """The paths `main` may not hold: it holds the Toolbox's flat folder, the Example projects
    and the Templates, the README, the change notes, the license and requirements.txt."""
    def allowed(path: str) -> bool:
        parts = path.split("/")
        return (path == README or path in ROOT_FILES
                or (len(parts) == 2 and parts[0] == toolbox_registry.FOLDER)
                or (len(parts) > 1 and parts[0] in COPIED))

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


def how_tos_text(source: Path) -> str:
    """Each how-to's number and title, linked to it on how_to.html, under its group, such as
    "Getting started, how-tos 1 to 18:", read from the docstrings in worked_examples/how_to/ that
    how_to.html is written from. The README is at .github/README.md, so a link goes up one folder.

    Each docstring's line 1 is its title and line 3 names its group, as `For: Getting started`.
    tools/how_to_page.py reads them the same way, but importing it loads the Toolbox into
    this Python, so the two lines are read here again.
    """
    groups: dict[str, list[tuple[int, str, str]]] = {}
    for path in sorted((source / HOW_TOS).glob("[0-9][0-9]_*.py")):
        doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8"))) or ""
        laid_out = re.match(r"(?P<title>[^\n]+)\n\nFor: (?P<group>[^\n]+)\n", doc)
        if laid_out is None:
            raise ExportRefused(f"{HOW_TOS}/{path.name}'s docstring must start with its title on "
                                "line 1 and `For: <its group>` on line 3, as tools/how_to_page.py "
                                "reads it.")
        groups.setdefault(laid_out["group"], []).append(
            (int(path.name[:2]), laid_out["title"], path.stem[3:]))
    if not groups:
        raise ExportRefused(f"There are no how-tos in {HOW_TOS}/ for the README to list.")
    return "\n\n".join(
        f"{group}, how-tos {how_tos[0][0]} to {how_tos[-1][0]}:\n\n"
        + "\n".join(f"{number}. [{title}](../{toolbox_registry.FOLDER}/how_to.html#{slug})"
                    for number, title, slug in how_tos)
        for group, how_tos in groups.items())


def readme_text(template: str, groups: list[dict], version: str, stamp: str,
                source: Path) -> str:
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


# --- Checks on the commit ----------------------------------------------------------------------


def check_folder(source: Path) -> None:
    """Refuse a commit without the Toolbox's folder, or whose files declare more than one
    version."""
    folder = toolbox_registry.FOLDER
    if not (source / folder).is_dir():
        raise ExportRefused(f"The export ships {folder}, but this commit doesn't have it. "
                            "Commit the folder on dev.")
    versions = {path.name: re.search(r'^TOOLBOX_VERSION = "([^"]+)"$',
                                     path.read_text(encoding="utf-8"), re.MULTILINE)
                for path in sorted((source / folder).glob("*.py"))}
    found = {name: version.group(1) for name, version in versions.items() if version}
    if "__init__.py" not in found:
        raise ExportRefused(f"{folder}/__init__.py declares no TOOLBOX_VERSION. Put its "
                            '`TOOLBOX_VERSION = "..."` line back, and commit.')
    if len(set(found.values())) > 1:
        said = " and ".join(f"{name} is {version}" for name, version in found.items()
                            if version != found["__init__.py"])
        raise ExportRefused(
            f"The Toolbox's files share one version, but __init__.py is {found['__init__.py']} "
            f"and {said}. Set TOOLBOX_VERSION in every .py file of {folder}/, and commit.")


# --- Building and committing ---------------------------------------------------------------------


def copied_files(folder: Path) -> list[str]:
    """Each file of one of the COPIED folders, as a sorted path inside it, such as
    "starter/README.md", leaving out Python's caches."""
    return sorted(path.relative_to(folder).as_posix() for path in folder.rglob("*")
                  if path.is_file() and "__pycache__" not in path.parts)


def build_copies(source: Path, into: Path, stamp: str) -> None:
    """Write the Example projects and the Templates into `into`, at dev's paths, stamped."""
    for folder in COPIED:
        for relative in copied_files(source / folder):
            where = f"{folder}/{relative}"
            text = (source / folder / relative).read_text(encoding="utf-8")
            target = into / folder / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(stamped(where, text, stamp), encoding="utf-8", newline="\n")


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
    bad_imports = toolbox_registry.imports_outside(into / folder)
    if bad_imports:
        raise ExportRefused(
            f"The Toolbox may import only the standard library, pandas, numpy and sqlglot "
            f"where tools/toolbox_registry.py allows it, which is all work has: "
            f"{'; '.join(f'{folder}/{bad}' for bad in bad_imports)}."
        )
    check_offline(into, [folder])


def check_root_files(source: Path) -> None:
    """Refuse a dev commit without each file main holds at its root."""
    missing = [name for name in ROOT_FILES if not (source / name).is_file()]
    if missing:
        raise ExportRefused(f"main ships dev's {' and '.join(missing)}, but this commit doesn't "
                            "have it. Commit it on dev.")


def copy_root_files(source: Path, into: Path) -> None:
    """Copy each file main holds at its root as dev holds it, and read it as main would."""
    for name in ROOT_FILES:
        (into / name).write_text((source / name).read_text(encoding="utf-8"),
                                 encoding="utf-8", newline="\n")
    check_offline(into, list(ROOT_FILES))


def build(source: Path, into: Path, when: datetime.datetime) -> str:
    """Build the Clean tree from the `dev` folder `source` into the folder `into`.

    Returns what the tree is, as main's commit names it, such as "sqlglot Composer 6.0,
    exported 2026-10-20 14:05".
    """
    if into.exists() and any(into.iterdir()):
        raise ExportRefused(f"{into} isn't empty. Build the Clean tree into an empty folder.")
    check_folder(source)
    missing = [path for path in (*COPIED, HOW_TOS) if not (source / path).is_dir()]
    if missing:
        raise ExportRefused(
            f"The export ships {' and '.join(COPIED)}, and the README lists the how-tos, but "
            f"this commit doesn't have {', '.join(missing)}. Commit it on dev.")
    check_root_files(source)
    template = (source / README_TEMPLATE).read_text(encoding="utf-8")
    folder, product = toolbox_registry.FOLDER, toolbox_registry.PRODUCT
    version = toolbox_version_of(source, folder)
    build_folder(source, into, folder, stamp_text(product, version, when))
    described = import_stamped(into)
    check_imports_alone(into)
    build_copies(source, into, copy_stamp_text(product, version, when))
    check_offline(into, list(COPIED))
    check_dry_runs(into)
    (into / README).parent.mkdir()
    (into / README).write_text(
        readme_text(template, described["groups"], version_text(version, when),
                    stamp_text(product, version, when), source),
        encoding="utf-8", newline="\n")
    check_offline(into, [README])
    copy_root_files(source, into)
    outside = outside_allowlist(files_in(into))
    if outside:
        raise ExportRefused(f"The Clean tree holds files outside its allowlist: {outside}.")
    return f"{product} {version_text(version, when)}"


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
    """Write what `commit` holds of the Toolbox's folder, the Example projects, the Templates,
    the how-tos, the README template, the change notes, the license and requirements.txt into
    `into`.

    The build reads these rather than the checkout, so a file git ignores (a stray log, say)
    can never reach `main`. A folder the commit lacks is left out, for the build to refuse.
    """
    held = git(repo, "ls-tree", "--name-only", commit).splitlines()
    paths = [folder for folder in [toolbox_registry.FOLDER, *COPIED] if folder in held]
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
