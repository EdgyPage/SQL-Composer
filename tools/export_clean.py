"""Export the Clean branch: build `main` from `dev`, check it, and commit it to `main` locally.

Run it with `dev` checked out and nothing uncommitted:

    python tools/export_clean.py

It builds the Clean tree in a temporary folder, from what `dev` has committed, for each Edition
`tools/editions.py` names in EXPORTED:

- it copies the Edition's folder, such as `sql_composer/`, and stamps line 1 of every file in
  it with that Edition's name, for example
  `# SQL Composer 2.0, exported 2026-10-02 14:05 - generated from dev, do not edit`, every
  folder with the same time;
- it writes the list of the folder's files into its `__init__.py`, for the import self-check;
- it writes `.github/README.md` from `docs/clean-branch-readme.md`, putting in the version and
  a cheat sheet: one line per public name, grouped by file, from each docstring's first line.

It then checks what it built: each Toolbox file imports only what work has (the standard
library, pandas, numpy, and its Edition's library where `tools/editions.py` allows it); each
stamped folder imports in a fresh Python that can't import the other Edition's library; the
Editions have one version, Spark Composer's shared files are current copies of SQL Composer's,
and both describe the same public names the same way; and the tree holds nothing outside its
allowlist (each Edition's folder and `.github/README.md`). Only then does it commit the tree to
`main`, as one new commit on top of the old `main`. It never checks `main` out and never pushes:
pushing `main` is your step.

It refuses, and leaves `main` as it was, while `.scratch/drift.md` has an open item.

To look at the Clean tree without committing anything, build it into an empty folder:

    python tools/export_clean.py --preview <folder>
"""

from __future__ import annotations

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
README = ".github/README.md"
README_TEMPLATE = "docs/clean-branch-readme.md"
VERSION_MARKER = "<!-- VERSION -->"
CHEAT_SHEET_MARKER = "<!-- CHEAT SHEET -->"


class ExportRefused(Exception):
    """The export stopped before touching `main`; the message says why and what to do."""


def stamp_text(product: str, toolbox_version: str, when: datetime.datetime) -> str:
    """The line-1 stamp, such as "SQL Composer 2.0, exported 2026-10-02 14:05 - ..."."""
    exported = when.strftime("%Y-%m-%d %H:%M")
    return f"{product} {toolbox_version}, exported {exported} - generated from dev, do not edit"


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


def toolbox_version_of(source: Path, edition: editions.Edition) -> str:
    text = (source / edition.folder / "__init__.py").read_text(encoding="utf-8")
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


def import_stamped(into: Path, edition: editions.Edition) -> dict:
    """Import an Edition's stamped folder in a fresh Python that can't import the other
    Edition's library, and return `describe_toolbox()` of it."""
    blocked = [other.library for other in editions.EDITIONS.values() if other is not edition]
    environment = dict(os.environ, PYTHONPATH=str(Path(__file__).parent), PYTHONIOENCODING="utf-8")
    done = subprocess.run(
        [sys.executable, "-B", "-c",
         f"import json, sys; sys.modules.update(dict.fromkeys({blocked!r})); "
         f"import export_clean; print(json.dumps(export_clean.describe_toolbox({edition.folder!r})))"],
        cwd=into, env=environment, capture_output=True, text=True, encoding="utf-8",
    )
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


def outside_allowlist(paths: list[str], exported=editions.EXPORTED) -> list[str]:
    """The paths `main` may not hold: it holds each exported Edition's flat folder and the
    README."""
    folders = {edition.folder for edition in exported}
    return [path for path in paths
            if path != README and not (path.count("/") == 1 and path.split("/")[0] in folders)]


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


# --- Checks across the exported Editions -----------------------------------------------------


def check_editions(source: Path, exported) -> None:
    """Refuse an export whose Editions don't belong together.

    Each must be in the commit; they must have one version; and Spark Composer's shared files
    must be the copies tools/make_spark_edition.py writes of SQL Composer's.
    """
    missing = [edition.folder for edition in exported if not (source / edition.folder).is_dir()]
    if missing:
        raise ExportRefused(
            f"EXPORTED in tools/editions.py names {', '.join(missing)}, which this commit "
            "doesn't have.")
    versions = {edition.product: toolbox_version_of(source, edition) for edition in exported}
    if len(set(versions.values())) > 1:
        raise ExportRefused(
            f"The Editions have different versions: {versions}. They share one version, so "
            "raise it in every file of both folders together.")
    if editions.SPARK_COMPOSER in exported and editions.SQL_COMPOSER in exported:
        stale = [name for name in editions.SHARED_FILES + editions.VERBATIM_FILES
                 if _copy_of(source, name) != (source / editions.SPARK_COMPOSER.folder
                                               / name).read_bytes()]
        if stale:
            raise ExportRefused(
                f"Spark Composer's {', '.join(stale)} aren't current copies of SQL Composer's. "
                "Run python tools/make_spark_edition.py and commit what it writes.")


def _copy_of(source: Path, name: str) -> bytes:
    """What tools/make_spark_edition.py writes into Spark Composer's folder for a file."""
    original = source / editions.SQL_COMPOSER.folder / name
    if name in editions.VERBATIM_FILES:
        return original.read_bytes()
    return editions.swap(original.read_text(encoding="utf-8"), name).encode("utf-8")


def _without_version(described: dict) -> list:
    """The cheat sheet a description gives, less the one line that holds VERSION's value."""
    return [[group["file"], group["about"],
             [line for line in group["names"] if line[0] != "VERSION"]]
            for group in described["groups"]]


def check_readme(template: str, exported) -> None:
    """Refuse a README template that names an Edition this export doesn't ship."""
    unshipped = [edition.product for edition in editions.EDITIONS.values()
                 if edition not in exported
                 and (edition.product in template or edition.folder in template)]
    if unshipped:
        raise ExportRefused(
            f"{README_TEMPLATE} names {', '.join(unshipped)}, which this export doesn't ship. "
            "Leave it out of the README until it ships.")


# --- Building and committing ---------------------------------------------------------------------


def build_edition(source: Path, into: Path, edition: editions.Edition,
                  when: datetime.datetime) -> dict:
    """Copy and stamp one Edition's folder into `into`, check its imports, and import it."""
    folder = edition.folder
    stamp = stamp_text(edition.product, toolbox_version_of(source, edition), when)
    names = sorted(path.name for path in (source / folder).iterdir()
                   if path.name != "__pycache__")
    folders = [name for name in names if (source / folder / name).is_dir()]
    if folders:
        raise ExportRefused(f"The Toolbox is one flat folder, but {folder}/ holds {folders}.")
    (into / folder).mkdir(parents=True)
    for name in names:
        text = (source / folder / name).read_text(encoding="utf-8")
        if name == "__init__.py":
            text = with_file_list(text, names, folder)
        (into / folder / name).write_text(stamped(name, text, stamp), encoding="utf-8",
                                          newline="\n")
    bad_imports = editions.imports_outside(into / folder)
    if bad_imports:
        raise ExportRefused(
            f"The Toolbox may import only the standard library, pandas, numpy and its "
            f"Edition's library where tools/editions.py allows it, which is all work has: "
            f"{'; '.join(bad_imports)}."
        )
    described = import_stamped(into, edition)
    described["stamp"] = stamp
    return described


def build(source: Path, into: Path, when: datetime.datetime,
          exported=editions.EXPORTED) -> str:
    """Build the Clean tree from the `dev` folder `source` into the folder `into`.

    Returns the first exported Edition's copy's `VERSION`.
    """
    if into.exists() and any(into.iterdir()):
        raise ExportRefused(f"{into} isn't empty. Build the Clean tree into an empty folder.")
    check_editions(source, exported)
    template = (source / README_TEMPLATE).read_text(encoding="utf-8")
    check_readme(template, exported)
    described = [build_edition(source, into, edition, when) for edition in exported]
    different = [exported[n].product for n, one in enumerate(described)
                 if _without_version(one) != _without_version(described[0])]
    if different:
        raise ExportRefused(
            f"{', '.join(different)} describes its public names differently from "
            f"{exported[0].product}. Both Editions have the same names, each with the same "
            "first line.")
    (into / README).parent.mkdir()
    (into / README).write_text(
        readme_text(template, described[0], described[0]["stamp"]), encoding="utf-8",
        newline="\n"
    )
    outside = outside_allowlist(files_in(into), exported)
    if outside:
        raise ExportRefused(f"The Clean tree holds files outside its allowlist: {outside}.")
    return described[0]["version"]


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


def tree_of(repo: Path, into: Path, index: Path, exported=editions.EXPORTED) -> str:
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
    if stored != built or outside_allowlist(stored, exported):
        raise ExportRefused(f"git stored {stored}, but the export built {built}.")
    return tree


def committed_files(repo: Path, commit: str, into: Path, exported=editions.EXPORTED) -> Path:
    """Write what `commit` holds of the exported Editions and the README template into `into`.

    The build reads these rather than the checkout, so a file git ignores (a stray log, say)
    can never reach `main`.
    """
    paths = [edition.folder for edition in exported] + [README_TEMPLATE]
    archive = subprocess.run(
        ["git", "-C", str(repo), "archive", "--format=tar", commit, *paths],
        capture_output=True,
    )
    if archive.returncode != 0:
        raise ExportRefused(f"`git archive` failed: {archive.stderr.decode(errors='replace')}")
    with tarfile.open(fileobj=io.BytesIO(archive.stdout)) as files:
        files.extractall(into, filter="data")
    return into


def export(repo: Path, when: datetime.datetime, exported=editions.EXPORTED) -> str:
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
        committed = committed_files(repo, dev, Path(temporary) / "dev", exported)
        version = build(committed, Path(temporary) / "clean", when, exported)
        tree = tree_of(repo, Path(temporary) / "clean", Path(temporary) / "index", exported)
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
