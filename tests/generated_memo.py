"""The memo of each "committed is generated" test: regenerate only when an input changed.

The how-to page, the Example gallery, each Example project and the Hive corpus are generated,
and a test regenerates each and compares it with what is committed (Toolbox 8.7, ticket 03).
On this computer, a test that passed regenerates again only when the hash of its inputs changed:

- the files and folders it is generated from, `INPUTS`, beside `SHARED_INPUTS`: the Toolbox,
  which the generators run, the tools, the Worked examples, the snapshot's recorder and the
  pins;
- the committed output itself, so an edit by hand is caught;
- the test's own file;
- the Python's version, and the versions of sqlglot, pandas and numpy installed.

Where the environment sets `CI`, as GitHub does on every runner and `dev.yml` says too, every
one regenerates whole, as on a fresh checkout, which keeps no memo. The memo is kept in
`.pytest_cache/memo/generated/`, git-ignored.

A memo also keeps the snapshot's hashes the test made when it last regenerated, and gives them
to the run again when it doesn't, so the snapshot's check of a whole run
(`tests/snapshot_recorder.py`) still finds them; one the snapshot no longer knows regenerates,
so the test checks its texts again.

    memo = generated_memo.Memo("how_to_page")
    if memo.is_unchanged():
        return
    assert ...  # regenerate and compare
    memo.keep()
"""

from __future__ import annotations

import hashlib
import importlib.metadata
import json
import os
import sys
from pathlib import Path

import snapshot_recorder

ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT / ".pytest_cache" / "memo" / "generated"
SHARED_INPUTS = ("sqlglot_composer", "example_database", "tools", "worked_examples",
                 "tests/conftest.py", "tests/snapshot_recorder.py", "tests/generated_memo.py",
                 "requirements-dev.txt")
# Each generated output: what it is generated from beside SHARED_INPUTS, the committed output
# and its test's file.
INPUTS = {
    "how_to_page": ("docs/main/how_to.html", "example_projects", "tests/test_how_tos.py"),
    "example_gallery": ("docs/main/examples.html", "tests/test_example_gallery.py"),
    "example_projects_page": ("docs/main/example_projects.html", "example_projects",
                              "tests/test_example_projects_page.py"),
    "example_project_starter": ("example_projects/starter", "tests/test_example_projects.py"),
    "example_project_intermediate": ("example_projects/intermediate",
                                     "tests/test_example_projects.py"),
    "hive_corpus": ("tests/hive_corpus", "tests/hive_corpus_cases.py",
                    "tests/test_hive_corpus.py"),
}
LIBRARIES = ("sqlglot", "pandas", "numpy")


def is_on_ci() -> bool:
    """Whether the environment says this is CI, where every generated output regenerates."""
    return bool(os.environ.get("CI"))


def inputs_hash(paths: tuple[str, ...]) -> str:
    """The hash of each file under `paths`, from the repo's root, by its path and bytes, and of
    the versions of Python and the LIBRARIES; a `__pycache__` is left out."""
    digest = hashlib.sha256(f"Python {sys.version}".encode())
    for library in LIBRARIES:
        digest.update(f"{library} {importlib.metadata.version(library)}".encode())
    for path in sorted(paths):
        top = ROOT / path
        files = [top] if top.is_file() else sorted(top.rglob("*"))
        for file in files:
            if file.is_file() and "__pycache__" not in file.parts:
                digest.update(file.relative_to(ROOT).as_posix().encode() + b"\0")
                digest.update(hashlib.sha256(file.read_bytes()).digest())
    return digest.hexdigest()


class Memo:
    """One generated output's memo, by its name in INPUTS."""

    def __init__(self, name: str) -> None:
        self.memo_file = FOLDER / f"{name}.json"
        self.inputs = inputs_hash(SHARED_INPUTS + INPUTS[name])

    def is_unchanged(self) -> bool:
        """Whether its inputs hash as they did when the test last passed, and not on CI: then
        the snapshot's hashes it made then are made again here, and the test is done."""
        if is_on_ci():
            return False
        try:
            memo_json = json.loads(self.memo_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return False
        if not isinstance(memo_json, dict) or memo_json.get("inputs") != self.inputs:
            return False
        made = set(memo_json.get("snapshot", []))
        known = snapshot_recorder.known_hashes()  # None on a sqlglot with no snapshot
        if not snapshot_recorder.WRITING and known is not None and not made <= known:
            return False  # the snapshot changed since: the test checks its texts again
        snapshot_recorder.hashes_made_in_this_run.update(made)
        return True

    def keep(self) -> None:
        """Keep its inputs' hash, the test having passed, with the snapshot's hashes of what the
        test made so far."""
        made = sorted({snapshot_recorder.hash_of(kind, text)
                       for kind, text in snapshot_recorder.texts_made_by_this_test})
        self.memo_file.parent.mkdir(parents=True, exist_ok=True)
        part_file = self.memo_file.with_name(f"{self.memo_file.name}.{os.getpid()}.part")
        part_file.write_text(json.dumps({"inputs": self.inputs, "snapshot": made}),
                             encoding="utf-8")
        os.replace(part_file, self.memo_file)
