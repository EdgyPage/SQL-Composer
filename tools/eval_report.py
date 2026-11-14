"""The cost report: one local HTML page from the ledger and the attribution records
(evaluation system, ticket 09).

    .venv/Scripts/python tools/eval_report.py [--local DIR] [--commits FILE] [--baseline FILE]

It writes `.eval-local/report.html`, which git ignores, and shows:

- **The cost per round**, pipeline, model, Toolbox version and commit: the tokens of the
  ledger's runs, and, beside each, what the commit was (an eventful one is marked).
- **Eventful commits**: a version raise, a change to a Copilot file, a ticket's merge, each with
  the tokens recorded on it.
- **The pass rate beside the cost** of each round, and how many replies were flagged `OVER CAP`
  (ticket 07), which the ledger's result keeps when the session records it.
- **The doc ids failing replies cite most**, per file (ticket 06's attribution).
- **The maintainer agents' share** of all tokens (ticket 08's rows).
- **Baseline figures** passed in, for ticket 11's comparison.

A tool may not start a subprocess (ADR 0004), so git's facts are passed in as a file. Make the
commits file once, and again when the history has moved on, with one command:

    git log --format="commit %h %cs %s" --name-only -n 600 > .eval-local/commits.txt

A line `commit <sha> <date> <subject>` starts a commit and the lines after it are the files it
changed. A commit that changed `sqlglot_composer/version.txt` is a version raise, and its
version is the first `8.7`-like number of its subject; a commit's version is that of the
latest raise at or before it. A commit that changed `copilot/` or `tools/copilot_sources/` is
a Copilot file change; a merge whose subject names `<map> ticket NN` is that ticket's merge.
With no commits file the page still builds, with no versions and no marks.

The baseline file, `.eval-local/baseline.json`, is a list of
`{"label": "...", "low": 580000, "high": 720000}`: figures the ledger is compared with (8.7's
orchestration of a ticket cost about 580,000 to 720,000 tokens).

The page is built with `sqlglot_composer/html_page.py`, loads nothing from outside its file,
and escapes every text it shows.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import NamedTuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import eval_runs  # noqa: E402
import eval_sources  # noqa: E402

from sqlglot_composer import html_page  # noqa: E402

REPORT_NAME = "report.html"
COMMITS_NAME = "commits.txt"
BASELINE_NAME = "baseline.json"
VERSION_FILE = "sqlglot_composer/version.txt"
COPILOT_PATHS = ("copilot/", "tools/copilot_sources/")
OVER_CAP = "OVER CAP"
COMMITS_COMMAND = 'git log --format="commit %h %cs %s" --name-only -n 600'

CSS = """\
h2{font-size:15px;margin:28px 0 6px} h3{font-size:13px;margin:14px 0 4px}
td.num,th.num{text-align:right} .note{color:var(--muted);margin:4px 0}"""


class Commit(NamedTuple):
    """One commit of the commits file: its short sha, date, subject and changed files."""

    sha: str
    date: str
    subject: str
    files: tuple[str, ...]


class Baseline(NamedTuple):
    """A figure to compare the ledger with: what it measures and its range in tokens."""

    label: str
    low: int
    high: int


# --- What git said ----------------------------------------------------------------------------


def read_commits(text: str) -> list[Commit]:
    """The commits of a commits file, newest first as `git log` wrote them."""
    commits: list[Commit] = []
    heads: list[tuple[str, str, str]] = []
    files: list[list[str]] = []
    for line in text.splitlines():
        if line.startswith("commit "):
            parts = line.split(maxsplit=3) + ["", ""]
            heads.append((parts[1], parts[2], parts[3]))
            files.append([])
        elif line.strip() and files:
            files[-1].append(line.strip())
    for (sha, date, subject), changed in zip(heads, files, strict=True):
        commits.append(Commit(sha, date, subject, tuple(changed)))
    return commits


def raised_version(commit: Commit) -> str | None:
    """The version a commit raised the Toolbox to, or None if it didn't touch version.txt."""
    if VERSION_FILE not in commit.files:
        return None
    found = re.search(r"\d+\.\d+(?:\.\d+)?", commit.subject)
    return found.group(0) if found else "?"


def events_of(commit: Commit) -> list[str]:
    """What makes a commit eventful, in words: a version raise, a Copilot file change, a
    ticket's merge. Empty for any other commit."""
    events = []
    version = raised_version(commit)
    if version is not None:
        events.append(f"version raise: {version}")
    if any(name.startswith(COPILOT_PATHS) for name in commit.files):
        events.append("Copilot file change")
    ticket = re.search(r"\(([\w-]+ )?(ticket \d+)\)\s*$", commit.subject)
    if commit.subject.startswith("Merge") and ticket:
        events.append(f"ticket merge: {ticket.group(1) or ''}{ticket.group(2)}")
    return events


def position_of(commits: list[Commit], sha: str) -> int | None:
    """Where a sha is in the commits, matching by the start of the shorter of the two."""
    if not sha:
        return None
    for place, commit in enumerate(commits):
        if commit.sha.startswith(sha) or sha.startswith(commit.sha):
            return place
    return None


def version_at(commits: list[Commit], sha: str) -> str:
    """The Toolbox version at a commit: that of the latest raise at or before it, "-" when the
    commit or any raise is unknown."""
    place = position_of(commits, sha)
    if place is None:
        return "-"
    for commit in commits[place:]:
        version = raised_version(commit)
        if version is not None:
            return version
    return "-"


def read_baseline(path: Path) -> list[Baseline]:
    """The baseline figures in a JSON file; none when there is no file."""
    if not path.exists():
        return []
    given = json.loads(path.read_text(encoding="utf-8"))
    return [Baseline(str(one["label"]), int(one["low"]), int(one["high"])) for one in given]


# --- Numbers ----------------------------------------------------------------------------------


def tokens_of(rows: Iterable[eval_runs.Run]) -> float:
    """The tokens of some ledger rows, summed."""
    return sum(float(one.tokens) for one in rows)


def count(number: float) -> str:
    """A number of tokens or runs as digits with thousands commas."""
    return f"{round(number):,}"


def percent(part: float, whole: float) -> str:
    """A share as a whole percent; a dash when there is no whole."""
    return f"{round(100 * part / whole)}%" if whole else "-"


def outcome(run: eval_runs.Run) -> str | None:
    """"pass" or "fail" for a ledger row whose result starts with one; None for any other."""
    word = run.result.split()[:1]
    return word[0] if word and word[0] in ("pass", "fail") else None


# --- The page's parts -------------------------------------------------------------------------


def table(heads: list[str], rows: list[list[str]], numeric: set[int] | None = None) -> str:
    """A table of text cells, escaped; the columns whose numbers are `numeric` align right."""
    numeric = numeric or set()

    def cell(tag: str, place: int, text: str) -> str:
        css = ' class="num"' if place in numeric else ""
        return f"<{tag}{css}>{html.escape(text)}</{tag}>"

    head = "".join(cell("th", place, text) for place, text in enumerate(heads))
    lines = []
    for row in rows:
        cells = "".join(cell("td", place, text) for place, text in enumerate(row))
        lines.append(f"<tr>{cells}</tr>\n")
    return "<table>\n<tr>" + head + "</tr>\n" + "".join(lines) + "</table>"


def note(text: str) -> str:
    return f'<p class="note">{html.escape(text)}</p>'


def section(title: str, *parts: str) -> str:
    return f"<h2>{html.escape(title)}</h2>\n" + "\n".join(parts)


def earliest(group: tuple[tuple[str, ...], list[eval_runs.Run]]) -> str:
    """The earliest date of a group of rows, to order the groups by."""
    return min(one.date for one in group[1])


def grouped(rows: Iterable[eval_runs.Run], columns: tuple[str, ...],
            commits: list[Commit] | None = None
            ) -> dict[tuple[str, ...], list[eval_runs.Run]]:
    """The rows grouped by the values of `columns`, each a field of a row or "version" (its
    commit's Toolbox version), in the order of each group's earliest date."""
    groups: dict[tuple[str, ...], list[eval_runs.Run]] = defaultdict(list)
    for one in rows:
        values = [version_at(commits or [], one.commit) if name == "version"
                  else getattr(one, name) for name in columns]
        groups[tuple(values)].append(one)
    return dict(sorted(groups.items(), key=earliest))


def cost_section(runs: list[eval_runs.Run], commits: list[Commit]) -> str:
    """The tokens of each round, pipeline, model and commit, with its Toolbox version and the
    marks of its commit; then the totals by pipeline, model and version."""
    if not runs:
        return section("Cost per round", note("No runs in the ledger."))
    by_commit = {one.sha: events_of(one) for one in commits}
    rows = []
    for (name, pipeline, model, sha), group in grouped(
            runs, ("round", "pipeline", "model", "commit")).items():
        place = position_of(commits, sha)
        events = by_commit[commits[place].sha] if place is not None else []
        rows.append([min(one.date for one in group), name, pipeline, model,
                     version_at(commits, sha), sha or "-", ", ".join(events),
                     count(len(group)), count(tokens_of(group)),
                     count(tokens_of(group) / len(group))])
    heads = ["Date", "Round", "Pipeline", "Model", "Version", "Commit", "Events", "Runs",
             "Tokens", "Tokens a run"]
    parts = [table(heads, rows, {7, 8, 9})]
    total = tokens_of(runs)
    for title, column in (("pipeline", "pipeline"), ("model", "model"),
                          ("Toolbox version", "version")):
        totals = [[name, count(len(group)), count(tokens_of(group)),
                   percent(tokens_of(group), total)]
                  for (name,), group in grouped(runs, (column,), commits).items()]
        parts.append(f"<h3>Tokens by {html.escape(title)}</h3>")
        parts.append(table([title.capitalize(), "Runs", "Tokens", "Share"], totals, {1, 2, 3}))
    return section("Cost per round", *parts)


def eventful_section(runs: list[eval_runs.Run], commits: list[Commit]) -> str:
    """Each eventful commit, what made it so and the tokens recorded on it."""
    if not commits:
        return section("Eventful commits", note(
            "No commits file, so no commit is marked. Make one with: " + COMMITS_COMMAND
            + " > .eval-local/" + COMMITS_NAME))
    rows = []
    for commit in commits:
        events = events_of(commit)
        if events:
            here = [one for one in runs if position_of([commit], one.commit) == 0]
            rows.append([commit.sha, commit.date, ", ".join(events), count(len(here)),
                         count(tokens_of(here))])
    if not rows:
        return section("Eventful commits", note("No eventful commit in the commits file."))
    return section("Eventful commits", table(
        ["Commit", "Date", "Event", "Runs", "Tokens"], rows, {3, 4}))


def rates_of(name: str, pipeline: str, runs: list[eval_runs.Run],
             sources: list[eval_sources.SourceRow]) -> tuple[int, int]:
    """The passing and the total replies of a round of a pipeline: from the ledger's results
    where they say pass or fail, otherwise from the kept sources rows."""
    found = [outcome(one) for one in runs if outcome(one)]
    if not found:
        found = [one.result for one in sources
                 if (one.round, one.pipeline) == (name, pipeline)
                 and one.result in ("pass", "fail")]
    return found.count("pass"), len(found)


def rates_section(runs: list[eval_runs.Run], sources: list[eval_sources.SourceRow]) -> str:
    """The pass rate of each round of the testing pipelines, with its flags and its cost."""
    tested = [one for one in runs if one.pipeline != "maintainer"]
    rows = []
    for (name, pipeline), group in grouped(tested, ("round", "pipeline")).items():
        passed, asked = rates_of(name, pipeline, group, sources)
        over = sum(OVER_CAP in one.result for one in group)
        spent = tokens_of(group)
        rows.append([name, pipeline, f"{passed} of {asked}" if asked else "-",
                     percent(passed, asked), count(over), count(spent),
                     count(spent / passed) if passed else "-"])
    heads = ["Round", "Pipeline", "Passed", "Rate", "Over cap", "Tokens", "Tokens a pass"]
    body = table(heads, rows, {3, 4, 5, 6}) if rows else note("No rounds recorded.")
    return section("Pass rate beside cost", body)


def file_and_id(cited: str) -> tuple[str, str]:
    """A cited id's file and the id: `11:F4` is file 11, F4; `*:P3` an id two loaded files
    define; a usability item `<file> <section>` is that file and section."""
    if ":" in cited:
        file, _, name = cited.partition(":")
        return ("(two files)" if file == "*" else f"File {file}"), name
    if " " in cited:
        file, _, name = cited.partition(" ")
        return file, name
    return "(not in a loaded file)", cited


def failing_total(item: tuple[str, list[eval_sources.Cited]]) -> int:
    """The failing citations of a file's ids, negated, to put the file with most first."""
    return -sum(one.failing for one in item[1])


def by_failing(cited: eval_sources.Cited) -> tuple[int, str]:
    """An id's place among its file's: most failing replies first, then by id."""
    return -cited.failing, cited.id


def sources_section(sources: list[eval_sources.SourceRow]) -> str:
    """The ids failing replies cite, per file, most-cited-by-failures first, and the failures
    that cited nothing."""
    title = "Doc ids that failing replies cite"
    if not sources:
        return section(title, note("No sources recorded."))
    found = eval_sources.attribute(sources)
    per_file: dict[str, list[eval_sources.Cited]] = defaultdict(list)
    for one in found.ranked:
        if one.failing:
            per_file[file_and_id(one.id)[0]].append(one)
    parts = []
    for file, cited in sorted(per_file.items(), key=failing_total):
        cited.sort(key=by_failing)
        parts.append(f"<h3>{html.escape(file)}</h3>")
        parts.append(table(["Id", "Failing replies", "Passing replies"],
                           [[file_and_id(one.id)[1], f"{one.failing} failing "
                             f"({one.failing_rate}%)", f"{one.passing} passing "
                             f"({one.passing_rate}%)"] for one in cited], {1, 2}))
    if not parts:
        parts.append(note("No failing reply cited an id."))
    parts.append(note(f"Failures that cited nothing: {len(found.uncited_failures)}. "
                      f"Replies with no source line: {found.no_source['fail']} failing, "
                      f"{found.no_source['pass']} passing."))
    return section(title, *parts)


def maintainer_section(runs: list[eval_runs.Run]) -> str:
    """The maintainer agents' tokens and their share of all tokens, an agent and model a row."""
    title = "Maintainer agents' share"
    maintainers = [one for one in runs if one.pipeline == "maintainer"]
    if not maintainers:
        return section(title, note("No maintainer agent runs recorded."))
    spent, total = tokens_of(maintainers), tokens_of(runs)
    rows = []
    for (agent, model), group in grouped(maintainers, ("task", "model")).items():
        clean = sum(one.result.startswith("clean") for one in group)
        rows.append([agent, model, count(len(group)), count(tokens_of(group)),
                     percent(tokens_of(group), total), f"{clean} clean"])
    return section(title, note(f"Maintainer agents: {count(spent)} of {count(total)} tokens "
                               f"({percent(spent, total)})."),
                   table(["Agent", "Model", "Runs", "Tokens", "Share of all", "Result"],
                         rows, {2, 3, 4}))


def baseline_section(runs: list[eval_runs.Run], baselines: list[Baseline]) -> str:
    """The baseline figures passed in, beside what the ledger has spent so far."""
    rounds = {(one.round, one.pipeline) for one in runs if one.pipeline != "maintainer"}
    parts = [note(f"The ledger so far: {count(tokens_of(runs))} tokens in {len(runs)} runs "
                  f"of {len(rounds)} rounds.")]
    if baselines:
        parts.append(table(["Figure", "Range"], [
            [one.label, f"{count(one.low)} to {count(one.high)} tokens"] for one in baselines]))
    else:
        parts.append(note("No baseline figures passed in. Put them in .eval-local/"
                          + BASELINE_NAME + " as a list of label, low and high."))
    return section("Baseline", *parts)


def page_text(runs: list[eval_runs.Run], sources: list[eval_sources.SourceRow],
              commits: list[Commit], baselines: list[Baseline]) -> str:
    """The whole report page."""
    body = "\n".join([
        "<header><h1>The evaluation cost report</h1>",
        note("Built from the ledger, the kept sources and the commits file. It lives only on "
             "this computer.") + "</header>",
        "<main>",
        cost_section(runs, commits),
        eventful_section(runs, commits),
        rates_section(runs, sources),
        sources_section(sources),
        maintainer_section(runs),
        baseline_section(runs, baselines),
        "</main>",
        "<footer>Tokens are the totals each agent reported, as recorded.</footer>"])
    return html_page.page("The evaluation cost report", body, [CSS], [])


def main(argv: list[str] | None = None) -> int:
    """Write the report page to `<local>/report.html`."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--local", type=Path, default=eval_runs.LOCAL)
    parser.add_argument("--commits", type=Path, help=f"default: <local>/{COMMITS_NAME}")
    parser.add_argument("--baseline", type=Path, help=f"default: <local>/{BASELINE_NAME}")
    given = parser.parse_args(argv)
    commits_path = given.commits or given.local / COMMITS_NAME
    commits = (read_commits(commits_path.read_text(encoding="utf-8"))
               if commits_path.exists() else [])
    text = page_text(eval_runs.read_ledger(given.local), eval_sources.read_sources(given.local),
                     commits, read_baseline(given.baseline or given.local / BASELINE_NAME))
    path = eval_runs.make_local_path(REPORT_NAME, local=given.local)
    path.write_text(text, encoding="utf-8", newline="\n")
    print(f"Wrote {path}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
