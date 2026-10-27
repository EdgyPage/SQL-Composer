"""copilot/count_characters.py, which counts each Copilot file against the 8,000 characters
Copilot takes at once (Toolbox 7.2, ticket 13)."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "copilot"))

import count_characters  # noqa: E402


def test_every_character_counts_spaces_and_line_breaks_included() -> None:
    assert count_characters.characters("a b\tc\n") == 6
    assert count_characters.characters_on_windows("a b\tc\n") == 7
    assert count_characters.characters("") == count_characters.characters_on_windows("") == 0


def test_a_windows_line_break_counts_two_either_way() -> None:
    for text in ("one\r\ntwo\r\n", "one\ntwo\n"):
        assert count_characters.characters(text) == 8
        assert count_characters.characters_on_windows(text) == 10


def test_a_file_at_the_limit_passes_and_one_over_fails(tmp_path: Path,
                                                      capsys: pytest.CaptureFixture[str]
                                                      ) -> None:
    (tmp_path / "fits.txt").write_text("x" * 8000, encoding="utf-8")
    assert count_characters.main([str(tmp_path / "fits.txt")]) == 0
    (tmp_path / "over.txt").write_text("x" * 7999 + "\n", encoding="utf-8")
    assert count_characters.main([str(tmp_path / "over.txt")]) == 1
    shown = capsys.readouterr().out
    assert "over.txt" in shown and "8,001" in shown and "OVER by 1" in shown


def test_a_folder_counts_each_txt_file_in_it(tmp_path: Path,
                                            capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "a.txt").write_text("hello", encoding="utf-8")
    (tmp_path / "b.txt").write_text("world\n", encoding="utf-8")
    (tmp_path / "c.py").write_text("print()", encoding="utf-8")
    assert count_characters.main([str(tmp_path)]) == 0
    shown = capsys.readouterr().out
    assert "a.txt" in shown and "b.txt" in shown and "c.py" not in shown


def test_with_no_argument_it_counts_the_files_beside_it(capsys: pytest.CaptureFixture[str]
                                                       ) -> None:
    assert count_characters.main([]) == 0
    assert "00_start_here.txt" in capsys.readouterr().out


def test_a_file_that_isnt_there_is_said_and_fails(tmp_path: Path,
                                                 capsys: pytest.CaptureFixture[str]) -> None:
    assert count_characters.main([str(tmp_path / "missing.txt")]) == 1
    assert "missing.txt: no such file" in capsys.readouterr().out
