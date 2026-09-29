"""Export the Clean branch: build `main` from `dev`, check it, and commit it to `main` locally.

Run it with `dev` checked out and nothing uncommitted:

    python tools/export_clean.py

It builds the Clean tree in a temporary folder, from what `dev` has committed:

- it copies the `sql_composer/` folder and stamps line 1 of every file in it, for example
  `# SQL Composer 2.0, exported 2026-10-02 14:05 - generated from dev, do not edit`;
- it writes the list of the folder's files into `__init__.py`, for the import self-check;
- it writes `.github/README.md` from `docs/clean-branch-readme.md`, putting in the version and
  a cheat sheet: one line per public name, grouped by file, from each docstring's first line.

It then checks what it built: each Toolbox file imports only what work has (the standard
library, pandas, numpy, and sqlglot where `tools/editions.py` allows it), the stamped copy
imports in a fresh Python, and the tree holds
nothing outside its allowlist (`sql_composer/` and `.github/README.md`). Only then does it
commit the tree to `main`, as one new commit on top of the old `main`. It never checks `main`
out and never pushes: pushing `main` is your step.

It refuses, and leaves `main` as it was, while `.scratch/drift.md` has an open item.

To look at the Clean tree without committing anything, build it into an empty folder:

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
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path

import editions

ROOT = Path(__file__).resolve().parent.parent
DRIFT_LIST = ".scratch/drift.md"
TOOLBOX = "sql_composer"
README = ".github/README.md"
README_TEMPLATE = "docs/clean-branch-readme.md"
VERSION_MARKER = "<!-- VERSION -->"
CHEAT_SHEET_MARKER = "<!-- CHEAT SHEET -->"


class ExportRefused(Exception):
    """The export stopped before touching `main`; the message says why and what to do."""


def stamp_text(toolbox_version: str, when: datetime.datetime) -> str:
    """The line-1 stamp, such as "SQL Composer 2.0, exported 2026-10-02 14:05 - ..."."""
    exported = when.strftime("%Y-%m-%d %H:%M")
    return f"SQL Composer {toolbox_version}, exported {exported} - generated from dev, do not edit"


def stamped(name: str, text: str, stamp: str) -> str:
    """The file's text with the stamp as a comment on line 1, in that file's comment style."""
    if name.endswith(".py"):
        return f"# {stamp}\n{text}"
    if name.endswith((".md", ".html")):
        return f"<!-- {stamp} -->\n{text}"
    raise ExportRefused(
        f"{TOOLBOX}/{name} is neither Python, Markdown nor HTML, so the export can't stamp it. "
        "Remove it from the Toolbox, or teach stamped() its comment style."
    )


def toolbox_version_of(source: Path) -> str:
    text = (source / TOOLBOX / "__init__.py").read_text(encoding="utf-8")
    return re.search(r'^TOOLBOX_VERSION = "([^"]+)"$', text, re.MULTILINE).group(1)


def with_file_list(init_text: str, names: list[str]) -> str:
    """`__init__.py`'s text with `_FILES = None` replaced by the list of the Toolbox's files."""
    if init_text.count("\n_FILES = None\n") != 1:
        raise ExportRefused(
            f"{TOOLBOX}/__init__.py must have exactly one `_FILES = None` line for the export to "
            "write the file list into. Put it back."
        )
    listed = "".join(f'    "{name}",\n' for name in names)
    return init_text.replace("\n_FILES = None\n", f"\n_FILES = [\n{listed}]\n")


def describe_toolbox() -> dict:
    """Import `sql_composer` and describe it for the cheat sheet, grouped by the file each name is in.

    This runs in a fresh Python started inside the Clean tree (see `import_stamped`), so the
    `sql_composer` it imports is the stamped copy, and its import self-check runs on that copy.
    """
    import sql_composer

    groups: dict[str, dict] = {}
    for name in sql_composer.__all__:
        value = getattr(sql_composer, name)
        if isinstance(value, str):
            # The two constants: their docstring is the Toolbox's own, so show the value and
            # the sentence of that docstring which says what the constant is.
            module, line = sql_composer, f"= `{value!r}`"
            said = re.search(rf"\b{name} is (.+?\.)(\s|$)", " ".join(sql_composer.__doc__.split()))
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
        "folder": str(Path(sql_composer.__file__).parent),
        "version": sql_composer.VERSION,
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


def import_stamped(into: Path) -> dict:
    """Import the Clean tree's `sql_composer` in a fresh Python, and return `describe_toolbox()`."""
    environment = dict(os.environ, PYTHONPATH=str(Path(__file__).parent), PYTHONIOENCODING="utf-8")
    done = subprocess.run(
        [sys.executable, "-B", "-c",
         "import json, export_clean; print(json.dumps(export_clean.describe_toolbox()))"],
        cwd=into, env=environment, capture_output=True, text=True, encoding="utf-8",
    )
    if done.returncode != 0:
        raise ExportRefused(
            f"The stamped copy of the Toolbox doesn't import, so nothing was exported:\n"
            f"{last_error(done.stderr)}"
        )
    described = json.loads(done.stdout.strip().splitlines()[-1])
    if Path(described["folder"]).resolve() != (into / TOOLBOX).resolve():
        raise ExportRefused(f"The import check found another sql_composer: {described['folder']}")
    return described


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


def files_in(folder: Path) -> list[str]:
    """Every file under `folder`, as sorted paths relative to it, such as ".github/README.md"."""
    return sorted(path.relative_to(folder).as_posix() for path in folder.rglob("*")
                  if path.is_file())


def outside_allowlist(paths: list[str]) -> list[str]:
    """The paths `main` may not hold: it holds only the flat `sql_composer/` folder and the README."""
    return [
        path
        for path in paths
        if path != README and not (path.startswith(f"{TOOLBOX}/") and path.count("/") == 1)
    ]


def imports_outside_allowlist(folder: Path) -> list[str]:
    """Each import in the Toolbox of something work doesn't have, as "<file> imports <name>".

    What each file may import is in `tools/editions.py`.
    """
    edition = editions.EDITIONS[folder.name]
    found = []
    for path in sorted(folder.glob("*.py")):
        allowed = sys.stdlib_module_names | editions.may_import(edition, path.name)
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module or ""]
            else:
                continue
            found += [
                f"{path.name} imports {name}"
                for name in names
                if name.split(".")[0] not in allowed
            ]
    return found


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


def readme_text(template: str, described: dict, stamp: str) -> str:
    """The Clean branch's README: the template, with the version and the cheat sheet put in."""
    for marker in (VERSION_MARKER, CHEAT_SHEET_MARKER):
        if template.count(marker) != 1:
            raise ExportRefused(f"{README_TEMPLATE} must have `{marker}` exactly once.")
    text = template.replace(VERSION_MARKER, described["version"])
    text = text.replace(CHEAT_SHEET_MARKER, cheat_sheet(described["groups"]))
    return stamped("README.md", text, stamp)


def build(source: Path, into: Path, when: datetime.datetime) -> str:
    """Build the Clean tree from the `dev` folder `source` into the folder `into`.

    Returns the exported copy's `VERSION`.
    """
    if into.exists() and any(into.iterdir()):
        raise ExportRefused(f"{into} isn't empty. Build the Clean tree into an empty folder.")
    stamp = stamp_text(toolbox_version_of(source), when)
    names = sorted(
        path.name for path in (source / TOOLBOX).iterdir() if path.name != "__pycache__"
    )
    folders = [name for name in names if (source / TOOLBOX / name).is_dir()]
    if folders:
        raise ExportRefused(f"The Toolbox is one flat folder, but {TOOLBOX}/ holds {folders}.")
    (into / TOOLBOX).mkdir(parents=True)
    for name in names:
        text = (source / TOOLBOX / name).read_text(encoding="utf-8")
        if name == "__init__.py":
            text = with_file_list(text, names)
        (into / TOOLBOX / name).write_text(
            stamped(name, text, stamp), encoding="utf-8", newline="\n"
        )
    bad_imports = imports_outside_allowlist(into / TOOLBOX)
    if bad_imports:
        raise ExportRefused(
            f"The Toolbox may import only the standard library, pandas, numpy and its "
            f"Edition's library where tools/editions.py allows it, which is all work has: "
            f"{'; '.join(bad_imports)}."
        )
    described = import_stamped(into)
    template = (source / README_TEMPLATE).read_text(encoding="utf-8")
    (into / README).parent.mkdir()
    (into / README).write_text(
        readme_text(template, described, stamp), encoding="utf-8", newline="\n"
    )
    outside = outside_allowlist(files_in(into))
    if outside:
        raise ExportRefused(f"The Clean tree holds files outside its allowlist: {outside}.")
    return described["version"]


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
    """Write what `commit` holds of the Toolbox and the README template into `into`.

    The build reads these rather than the checkout, so a file git ignores (a stray log, say)
    can never reach `main`.
    """
    archive = subprocess.run(
        ["git", "-C", str(repo), "archive", "--format=tar", commit, TOOLBOX, README_TEMPLATE],
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
