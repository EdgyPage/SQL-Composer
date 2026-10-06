"""Every file path the standing docs name exists, so a doc can't point at something gone.

The standing docs are `CLAUDE.md` and everything in `docs/agents/`. The Clean branch's README
template, `docs/clean-branch-readme.md`, names paths as main holds them, so
tests/repo/test_export_clean.py checks its paths against the Clean tree instead. A path counts when it's written in backticks or as a
Markdown link target and ends in a known file extension or in `/` (a folder). It may be
relative to the repo root or to the doc's own folder. Anything with a placeholder
(`<effort>`), a space, a wildcard or a leading `/` (a slash command) is skipped.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
STANDING_DOCS = sorted([
    ROOT / "CLAUDE.md",
    *(ROOT / "docs" / "agents").glob("*.md"),
])

IN_BACKTICKS = re.compile(r"`([^`\n]+)`")
LINK_TARGET = re.compile(r"\]\(([^)\s]+)\)")
FILE_EXTENSION = re.compile(r"\.(md|py|txt|toml|json|yml|yaml|html|cfg|ini)$")
NOT_A_PATH = re.compile(r"[<>*\s:?]|^/")


def named_paths(text: str) -> list[str]:
    candidates = IN_BACKTICKS.findall(text) + LINK_TARGET.findall(text)
    return [
        candidate
        for candidate in candidates
        if not NOT_A_PATH.search(candidate)
        and (candidate.endswith("/") or FILE_EXTENSION.search(candidate))
    ]


def test_the_standing_docs_are_found() -> None:
    assert ROOT / "CLAUDE.md" in STANDING_DOCS
    assert len(STANDING_DOCS) > 1


@pytest.mark.parametrize("doc", STANDING_DOCS, ids=lambda doc: doc.relative_to(ROOT).as_posix())
def test_every_path_a_standing_doc_names_exists(doc: Path) -> None:
    missing = [
        path
        for path in named_paths(doc.read_text(encoding="utf-8"))
        if not any((folder / path.split("#")[0]).exists() for folder in (ROOT, doc.parent))
    ]
    assert not missing, f"{doc.name} names paths that don't exist: {missing}"


def test_a_missing_path_is_caught() -> None:
    text = "See `docs/agents/nowhere.md` and `docs/adr/`, not `<effort>/`, `/wayfinder` or `a/b`."
    assert named_paths(text) == ["docs/agents/nowhere.md", "docs/adr/"]
