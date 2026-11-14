"""The cost report (evaluation system, ticket 09): `.eval-local/report.html`, built from a small
ledger, a sources file and a commits file in a temporary folder, so none touches the repo's
`.eval-local/`."""

from __future__ import annotations

import json
import re
from pathlib import Path

import eval_report
import eval_runs
import eval_sources
import pytest

COMMITS = """\
commit cccc333 2026-11-14 Merge branch 'x' into dev (eval-system ticket 07)

commit bbbb222 2026-11-13 feat(8.7): the Upgrade step and the raise to 8.7 (ticket 14)

sqlglot_composer/version.txt
tests/upgrade_from/8.6/a.txt

commit aaaa111 2026-11-12 docs: reword a pattern

copilot/11_excel.txt
README.md

commit 9999000 2026-11-09 feat(8.6): the raise to 8.6

sqlglot_composer/version.txt
"""


def a_run(**changed: str) -> eval_runs.Run:
    fields = {"date": "2026-11-14", "commit": "cccc333", "round": "r2", "pipeline": "copilot",
              "task": "T01", "arm": "C", "model": "haiku", "role": "proxy", "tokens": "1000",
              "seconds": "10", "result": "pass"}
    return eval_runs.Run(**{**fields, **changed})


def a_source(**changed: str) -> eval_sources.SourceRow:
    fields = {"date": "2026-11-14", "round": "r2", "pipeline": "copilot", "task": "T01",
              "arm": "C", "model": "haiku", "result": "fail", "files": "f", "loaded": "abc",
              "status": "cited", "cited": "11:F4", "unknown": ""}
    return eval_sources.SourceRow(**{**fields, **changed})


def ledger_rows() -> list[eval_runs.Run]:
    return [
        a_run(task="T01", tokens="1000", result="pass"),
        a_run(task="T02", tokens="3000", result="fail"),
        a_run(task="T03", tokens="2000", result="pass OVER CAP"),
        a_run(round="r1", commit="aaaa111", tokens="4000", model="sonnet", task="T01",
              result="pass"),
        a_run(round="r0", commit="9999000", pipeline="usability", role="user", task="W1",
              tokens="10000", result="done"),
        a_run(pipeline="maintainer", role="maintainer", task="drift-reviewer", round="t07",
              arm="-", model="opus", tokens="10000", result="opened D3"),
    ]


def built(sources: list[eval_sources.SourceRow] | None = None,
          baselines: list[eval_report.Baseline] | None = None) -> str:
    if sources is None:
        sources = [a_source(task="T02", cited="11:F4"),
                   a_source(task="T01", result="pass", cited="11:F9")]
    return eval_report.page_text(ledger_rows(), sources, eval_report.read_commits(COMMITS),
                                 baselines or [])


def text_of(page: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", page))


def test_the_commits_file_gives_each_commit_its_events() -> None:
    commits = eval_report.read_commits(COMMITS)
    assert [one.sha for one in commits] == ["cccc333", "bbbb222", "aaaa111", "9999000"]
    assert [eval_report.events_of(one) for one in commits] == [
        ["ticket merge: eval-system ticket 07"], ["version raise: 8.7"],
        ["Copilot file change"], ["version raise: 8.6"]]


def test_a_commit_s_version_is_the_latest_raise_at_or_before_it() -> None:
    commits = eval_report.read_commits(COMMITS)
    assert eval_report.version_at(commits, "cccc333") == "8.7"
    assert eval_report.version_at(commits, "aaaa111") == "8.6"
    assert eval_report.version_at(commits, "9999000") == "8.6"
    assert eval_report.version_at(commits, "unknown") == "-"


def test_a_sha_matches_by_its_start() -> None:
    commits = eval_report.read_commits(COMMITS)
    assert eval_report.version_at(commits, "bbbb222abcdef") == "8.7"


def test_the_page_has_each_section() -> None:
    page = built()
    for heading in ("Cost per round", "Eventful commits", "Pass rate beside cost",
                    "Doc ids that failing replies cite", "Maintainer agents&#x27; share",
                    "Baseline"):
        assert f"<h2>{heading}</h2>" in page


def test_cost_per_round_shows_tokens_version_commit_and_events() -> None:
    text = text_of(built())
    assert re.search(r"r2 copilot haiku 8\.7 cccc333 ticket merge: eval-system ticket 07 3 "
                     r"6,000 2,000", text)
    assert re.search(r"r1 copilot sonnet 8\.6 aaaa111 Copilot file change 1 4,000 4,000", text)


def test_pass_rates_sit_beside_cost_and_over_cap_runs_are_counted() -> None:
    text = text_of(built())
    assert re.search(r"r2 copilot 2 of 3 67% 1 6,000", text)


def test_a_round_with_no_pass_or_fail_takes_its_rate_from_the_sources() -> None:
    sources = [a_source(round="r0", pipeline="usability", task="W1", result="fail"),
               a_source(round="r0", pipeline="usability", task="W2", result="pass")]
    assert re.search(r"r0 usability 1 of 2 50%", text_of(built(sources)))


def test_eventful_commits_are_listed_with_the_tokens_recorded_on_them() -> None:
    text = text_of(built())
    assert "cccc333 2026-11-14 ticket merge: eval-system ticket 07" in text
    assert "bbbb222 2026-11-13 version raise: 8.7" in text
    assert re.search(r"aaaa111 2026-11-12 Copilot file change 1 4,000", text)


def test_the_failing_ids_are_ranked_per_file() -> None:
    text = text_of(built())
    assert "File 11" in text
    assert re.search(r"F4 1 failing", text)
    assert "F9" not in text


def test_failures_that_cited_nothing_are_counted() -> None:
    sources = [a_source(task="T02", status="no source", cited="")]
    assert "Failures that cited nothing: 1" in text_of(built(sources))


def test_no_sources_says_so() -> None:
    assert "No sources recorded." in text_of(built([]))


def test_the_maintainer_agents_share_of_all_tokens() -> None:
    text = text_of(built())
    assert re.search(r"Maintainer agents: 10,000 of 30,000 tokens \(33%\)", text)
    assert re.search(r"drift-reviewer opus 1 10,000", text)


def test_baseline_figures_passed_in_are_shown() -> None:
    baselines = [eval_report.Baseline("8.7 orchestration of a ticket", 580000, 720000)]
    text = text_of(built(baselines=baselines))
    assert re.search(r"8\.7 orchestration of a ticket 580,000 to 720,000 tokens", text)
    assert "No baseline figures passed in" not in text


def test_with_no_baseline_the_page_says_so() -> None:
    assert "No baseline figures passed in" in text_of(built())


def test_baseline_file_is_read_as_json(tmp_path: Path) -> None:
    path = tmp_path / "baseline.json"
    path.write_text(json.dumps([{"label": "x", "low": 1, "high": 2}]), encoding="utf-8")
    assert eval_report.read_baseline(path) == [eval_report.Baseline("x", 1, 2)]
    assert eval_report.read_baseline(tmp_path / "none.json") == []


def test_text_from_the_ledger_is_escaped() -> None:
    page = eval_report.page_text([a_run(round="<b>r</b>")], [], [], [])
    assert "<b>r</b>" not in page
    assert "&lt;b&gt;r&lt;/b&gt;" in page


def test_an_empty_ledger_still_builds_a_page() -> None:
    assert "No runs in the ledger." in text_of(eval_report.page_text([], [], [], []))


def test_the_command_writes_report_html_into_the_local_folder(tmp_path: Path) -> None:
    local = tmp_path / ".eval-local"
    for run in ledger_rows():
        eval_runs.record_run(run, local)
    eval_sources.keep_sources([a_source()], local)
    (local / "commits.txt").write_text(COMMITS, encoding="utf-8")
    assert eval_report.main(["--local", str(local)]) == 0
    page = (local / "report.html").read_text(encoding="utf-8")
    assert "<h2>Cost per round</h2>" in page
    assert "8.7" in page


def test_the_page_is_built_from_the_page_module_with_no_colour_or_style_of_its_own() -> None:
    page = built()
    assert "<style>" in page
    assert "--ink" in page
    assert "style=" not in page
    assert not re.search(r"https?://", page)
    assert not re.search(r"#[0-9a-fA-F]{3,6}\b", eval_report.CSS)


@pytest.mark.parametrize("line", ["commit abc", "commit abc 2026-11-14"])
def test_a_commits_line_with_no_subject_is_still_read(line: str) -> None:
    assert eval_report.read_commits(line)[0].sha == "abc"
