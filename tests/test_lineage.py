"""export_lineage: the lineage of Statements, written as an HTML page and its Markdown twin.

As decided in "What does exploring a Statement's lineage look like?". The tests go through the
public names: Statements built on the Example database, `export_lineage`, and the two files it
writes, read as text. The Markdown's Mermaid chart is read back into boxes and arrows, so a
test can say "this column feeds that one" without depending on the chart's numbering.
"""

from __future__ import annotations

import json
import re
import runpy
import shutil
import subprocess
import textwrap

import pytest
from conftest import in_this_edition

import sqlglot_composer
from sqlglot_composer import (
    AS,
    FROM,
    GROUP_BY,
    HAVING,
    INSERT_OVERWRITE,
    JOIN,
    LEFT_JOIN,
    LIMIT,
    ORDER_BY,
    SELECT,
    WHERE,
    LoadRefused,
    Table,
    all_of,
    at_least,
    between,
    count_rows,
    create_table,
    derived,
    descending,
    equals,
    example_database,
    export_lineage,
    fill_null,
    is_null,
    last_n_days,
    not_equals,
    row_number,
    set_load_limits,
    statement,
    sum_of,
    to_hive,
    week_start,
)

job_runs = example_database.job_runs
jobs = example_database.jobs

daily_runs = Table("mart.daily_runs", date_partition="dt",
                   columns={"job_id": "bigint", "runs": "bigint", "dt": "string"})


def runs_per_team():
    return statement(
        SELECT(jobs.team, AS(count_rows(), "runs")),
        FROM(job_runs),
        JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
        WHERE(last_n_days(job_runs.dt, 2)),
        GROUP_BY(jobs.team),
    )


def fill_daily_runs(first="2026-09-24", last="2026-09-24"):
    return statement(
        INSERT_OVERWRITE(daily_runs),
        SELECT(job_runs.job_id, AS(count_rows(), "runs")),
        FROM(job_runs),
        WHERE(between(job_runs.dt, first, last)),
        GROUP_BY(job_runs.dt, job_runs.job_id),
    )


def runs_by_team():
    return statement(
        SELECT(jobs.team, AS(sum_of(daily_runs.runs), "runs")),
        FROM(daily_runs),
        JOIN(jobs, ON=equals(jobs.job_id, daily_runs.job_id)),
        WHERE(last_n_days(daily_runs.dt, 2)),
        GROUP_BY(jobs.team),
    )


def read(files) -> tuple[str, str]:
    """The Markdown and the HTML export_lineage wrote, as text.

    Each test calls export_lineage itself, since the Statements are named after the
    variables of the function that calls it.
    """
    html_file, markdown_file = files
    return markdown_file.read_text(encoding="utf-8"), html_file.read_text(encoding="utf-8")


def page_data(page: str) -> dict:
    """The boxes, arrows and groups the HTML page's script draws from.

    The page writes them as JSON on the one line after `const graph = `.
    """
    return json.loads(re.search(r"const graph = (\{.*\});\n", page).group(1))


def chart(markdown: str) -> dict:
    """The Mermaid chart as {"boxes": {label: group}, "arrows": {(from, to, label)}}.

    A box's label is its first line; a group's label is its title. An arrow's label is
    "value" for a solid arrow, "rows" for a dotted one, or the text written on it.
    """
    body = markdown.split("```mermaid\n", 1)[1].split("```", 1)[0]
    names, boxes, group = {}, {}, None
    for line in body.splitlines():
        if found := re.match(r'\s*subgraph (\w+)\["(.*)"\]$', line):
            names[found[1]], group = found[2], found[2]
        elif found := re.match(r'\s*(n\d+)(?:\["|\{\{")(.*?)(?:<br/>.*)?(?:"\]|"\}\})$', line):
            names[found[1]] = found[2]
            boxes[found[2]] = group
    arrows = set()
    for found in re.finditer(r"^\s*(\w+) (-->|-\.->)(?:\|(.*?)\|)? (\w+)$", body, re.MULTILINE):
        label = found[3] or ("value" if found[2] == "-->" else "rows")
        arrows.add((names[found[1]], names[found[4]], label))
    return {"boxes": boxes, "arrows": arrows}


def section(markdown: str, heading: str) -> str:
    """The text under one heading, down to the next heading of the same level or higher."""
    level = heading.split(" ")[0]
    start = markdown.index(f"\n{heading}\n") + len(heading) + 2
    ends = [m.start() for m in re.finditer(r"^#{1,%d} " % len(level), markdown[start:],
                                           re.MULTILINE)]
    return markdown[start:start + ends[0]] if ends else markdown[start:]


# --- The two files ------------------------------------------------------------------------------


def test_it_writes_the_html_and_its_markdown_twin_side_by_side(tmp_path) -> None:
    html_file, markdown_file = export_lineage(runs_per_team(), to=tmp_path / "team.html")
    assert html_file == tmp_path / "team.html"
    assert markdown_file == tmp_path / "team.md"
    assert html_file.read_text(encoding="utf-8").startswith("<!doctype html>")
    assert markdown_file.read_text(encoding="utf-8").startswith("# Lineage: ")


def test_to_creates_missing_folders(tmp_path) -> None:
    html_file, _ = export_lineage(runs_per_team(), to=str(tmp_path / "a" / "b" / "team.html"))
    assert html_file.exists()


def test_to_must_name_an_html_file(tmp_path) -> None:
    with pytest.raises(ValueError, match=r"to= must name an \.html file"):
        export_lineage(runs_per_team(), to=tmp_path / "team.md")


def test_both_footers_show_the_toolbox_version_and_the_scripts_commit(tmp_path) -> None:
    markdown, page = read(export_lineage(runs_per_team(), to=tmp_path / "lineage.html"))
    for text in (markdown, page):
        assert sqlglot_composer.VERSION in text
        assert re.search(r"Made by export_lineage on \d{4}-\d\d-\d\d \d\d:\d\d, from your "
                         r"scripts at commit \w+, with ", text)


# --- The default name and place ---------------------------------------------------------------


def run_script(folder, text: str) -> tuple:
    """Run a script saved in `folder` that calls export_lineage, and return what it returned."""
    script = folder / "weekly_report.py"
    script.write_text(textwrap.dedent(text), encoding="utf-8")
    return runpy.run_path(str(script))["files"]


SCRIPT = """
    from sqlglot_composer import (AS, FROM, JOIN, SELECT, WHERE, GROUP_BY, count_rows, equals,
                              example_database, export_lineage, last_n_days, statement)
    job_runs, jobs = example_database.job_runs, example_database.jobs
    runs_per_team = statement(
        SELECT(jobs.team, AS(count_rows(), "runs")),
        FROM(job_runs),
        JOIN(jobs, ON=equals(jobs.job_id, job_runs.job_id)),
        WHERE(last_n_days(job_runs.dt, 2)),
        GROUP_BY(jobs.team),
    )
    files = export_lineage(runs_per_team)
"""


def test_the_default_name_goes_in_a_lineage_folder_beside_the_calling_script(tmp_path) -> None:
    html_file, markdown_file = run_script(tmp_path, SCRIPT)
    assert html_file.parent == tmp_path / "lineage"
    assert re.fullmatch(r"\d{8}-\d{6}_nogit_lineage_weekly_report_runs_per_team\.html",
                        html_file.name)
    assert markdown_file == html_file.with_suffix(".md")
    assert markdown_file.exists()


def git(folder, *args) -> str:
    done = subprocess.run(["git", *args], cwd=folder, capture_output=True, text=True, check=True)
    return done.stdout.strip()


def git_repository(folder):
    git(folder, "init", "-q", "-b", "work")
    git(folder, "config", "user.email", "test@example.com")
    git(folder, "config", "user.name", "test")
    (folder / "notes.txt").write_text("notes\n", encoding="utf-8")
    git(folder, "add", "notes.txt")
    git(folder, "commit", "-q", "-m", "first")
    return git(folder, "rev-parse", "--short=7", "HEAD")


needs_git = pytest.mark.skipif(shutil.which("git") is None, reason="needs the git program")


@needs_git
def test_the_name_carries_the_commit_of_the_scripts_repository(tmp_path) -> None:
    commit = git_repository(tmp_path)
    html_file, _ = run_script(tmp_path, SCRIPT)
    assert f"_{commit}_lineage_weekly_report_" in html_file.name
    assert f"at commit {commit}," in html_file.read_text(encoding="utf-8")


@needs_git
def test_the_commit_is_read_from_packed_refs_too(tmp_path) -> None:
    commit = git_repository(tmp_path)
    git(tmp_path, "pack-refs", "--all")
    assert not (tmp_path / ".git" / "refs" / "heads" / "work").exists()
    html_file, _ = run_script(tmp_path, SCRIPT)
    assert f"_{commit}_lineage_" in html_file.name


@needs_git
def test_the_commit_is_read_in_a_worktree_and_on_a_detached_head(tmp_path) -> None:
    main = tmp_path / "main"
    main.mkdir()
    commit = git_repository(main)
    git(main, "worktree", "add", "-q", "--detach", str(tmp_path / "other"))
    html_file, _ = run_script(tmp_path / "other", SCRIPT)
    assert f"_{commit}_lineage_" in html_file.name
    git(main, "worktree", "add", "-q", "-b", "side", str(tmp_path / "side"))
    html_file, _ = run_script(tmp_path / "side", SCRIPT)
    assert f"_{commit}_lineage_" in html_file.name


def test_in_a_notebook_the_name_and_folder_come_from_the_notebook(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("JPY_SESSION_NAME", str(tmp_path / "Weekly report.ipynb"))
    cell = compile(textwrap.dedent(SCRIPT), "/tmp/ipykernel_4242/2718281828.py", "exec")
    scope = {}
    exec(cell, scope)
    html_file, _ = scope["files"]
    assert html_file.parent == tmp_path / "lineage"
    assert html_file.name.endswith("_nogit_lineage_Weekly_report_runs_per_team.html")


def test_several_statements_are_named_by_their_variables_in_the_order_passed(
        tmp_path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    scope = {"export_lineage": export_lineage, "fill": fill_daily_runs(),
             "weekly": runs_by_team(), "runs_per_team": runs_per_team}
    exec(compile("files = export_lineage(weekly, fill)", "<stdin>", "exec"), scope)
    html_file, _ = scope["files"]
    assert html_file.parent == tmp_path / "lineage"
    assert html_file.name.endswith("_nogit_lineage_notebook_weekly__fill.html")
    exec(compile("files = export_lineage(weekly, runs_per_team())", "<stdin>", "exec"), scope)
    assert scope["files"][0].name.endswith("_weekly__statement_2.html")


# --- What the drawing holds -------------------------------------------------------------------


def test_every_table_and_statement_is_its_own_group(tmp_path) -> None:
    team = runs_per_team()
    markdown, _ = read(export_lineage(team, to=tmp_path / "lineage.html"))
    boxes = chart(markdown)["boxes"]
    assert boxes["ops.job_runs.dt"] == "ops.job_runs"
    assert boxes["ops.jobs.team"] == "ops.jobs"
    assert boxes["team"] == "team"
    assert boxes["runs"] == "team"
    assert boxes["WHERE in team"] == "filters on team"
    assert boxes["JOIN ON in team"] == "filters on team"


def test_a_solid_arrow_carries_a_value_and_a_dotted_one_decides_the_rows(tmp_path) -> None:
    team = runs_per_team()
    markdown, _ = read(export_lineage(team, to=tmp_path / "lineage.html"))
    arrows = chart(markdown)["arrows"]
    assert ("ops.jobs.team", "team", "value") in arrows
    assert ("ops.job_runs.dt", "WHERE in team", "rows") in arrows
    assert ("ops.jobs.job_id", "JOIN ON in team", "rows") in arrows
    assert ("ops.job_runs.job_id", "JOIN ON in team", "rows") in arrows
    assert ("WHERE in team", "team", "filters") in arrows


def test_a_box_shows_the_call_it_was_written_with(tmp_path) -> None:
    weekly = statement(
        SELECT(AS(week_start(job_runs.dt), "week"), AS(count_rows(), "runs")),
        FROM(job_runs),
        WHERE(last_n_days(job_runs.dt, 2)),
        GROUP_BY("week"),
    )
    markdown, _ = read(export_lineage(weekly, to=tmp_path / "lineage.html"))
    assert '    n' in markdown
    assert re.search(r'\["week<br/><small>week_start\(job_runs\.dt\)</small>"\]', markdown)
    entry = section(markdown, "#### `week`")
    assert ("Calculated in **weekly** as `week_start(job_runs.dt)`, which is "
            "`CAST(NEXT_DAY(DATE_ADD(job_runs.dt, 7 * -1), 'MO') AS STRING)`") in entry
    assert "One value for each different" not in entry
    runs = section(markdown, "#### `runs`")
    assert "One value for each different `week_start(job_runs.dt)`." in runs


def test_arithmetic_between_calls_reads_as_written(tmp_path) -> None:
    average = statement(
        SELECT(job_runs.job_id,
               AS(sum_of(job_runs.duration_mins) / count_rows(), "average_minutes")),
        FROM(job_runs),
        WHERE(last_n_days(job_runs.dt, 2)),
        GROUP_BY(job_runs.job_id),
    )
    markdown, _ = read(export_lineage(average, to=tmp_path / "lineage.html"))
    hive = in_this_edition("SUM(job_runs.duration_mins) / COUNT(*)",
                           "SUM(job_runs.duration_mins) / NULLIF(COUNT(*), 0)")
    assert f"as `sum_of(job_runs.duration_mins) / count_rows()`, which is `{hive}`" in markdown


def test_a_condition_reads_as_written_where_the_editions_write_different_hive(tmp_path) -> None:
    slow = statement(
        SELECT(job_runs.job_id, AS(count_rows(), "runs")),
        FROM(job_runs),
        WHERE(at_least(job_runs.duration_mins * 0.5 / job_runs.avg_retry_secs, 2),
              last_n_days(job_runs.dt, 2)),
        GROUP_BY(job_runs.job_id),
    )
    markdown, _ = read(export_lineage(slow, to=tmp_path / "lineage.html"))
    hive = in_this_edition("(job_runs.duration_mins * 0.5) / job_runs.avg_retry_secs >= 2",
                           "(job_runs.duration_mins * 0.5D) / NULLIF(job_runs.avg_retry_secs, 0) >= 2")
    assert ("`at_least((job_runs.duration_mins * 0.5) / job_runs.avg_retry_secs, 2)`, "
            f"which is `{hive}`") in markdown


def test_the_report_traces_each_calculated_column_back_to_the_tables(tmp_path) -> None:
    team = runs_per_team()
    markdown, _ = read(export_lineage(team, to=tmp_path / "lineage.html"))
    runs = section(markdown, "#### `runs`")
    assert "```text\nteam.runs = count_rows()\n└─ (no columns: it counts rows)\n```" in runs
    assert ("- WHERE in team: `last_n_days(job_runs.dt, 2)`, which is `job_runs.dt BETWEEN "
            "'2026-09-23' AND '2026-09-24'` (reads ops.job_runs.dt)") in runs
    assert ("- JOIN ON in team: `equals(jobs.job_id, job_runs.job_id)`, which is "
            "`jobs.job_id = job_runs.job_id` (reads ops.job_runs.job_id, ops.jobs.job_id)"
            ) in runs
    assert "One value for each different `jobs.team`." in runs
    copied = section(markdown, "### Copied columns")
    assert "| `team` | ops.jobs.team |" in copied


def test_the_hive_is_the_one_to_hive_gives(tmp_path) -> None:
    team = runs_per_team()
    markdown, page = read(export_lineage(team, to=tmp_path / "lineage.html"))
    assert f"### Hive as submitted\n\n```sql\n{to_hive(team)}\n```" in markdown
    assert "<h3>Hive as submitted</h3>\n<pre>SELECT\n  jobs.team," in page


def latest_runs():
    numbered = derived("numbered", statement(
        SELECT(job_runs.job_id, job_runs.status,
               AS(row_number(PARTITION_BY=job_runs.job_id,
                             ORDER_BY=descending(job_runs.run_id)), "newest_first")),
        FROM(job_runs),
        WHERE(last_n_days(job_runs.dt, 2)),
    ))
    return statement(
        SELECT(numbered.job_id, numbered.status),
        FROM(numbered),
        WHERE(equals(numbered.newest_first, 1)),
    )


def test_a_derived_table_stays_on_screen_as_its_own_group(tmp_path) -> None:
    latest = latest_runs()
    markdown, _ = read(export_lineage(latest, to=tmp_path / "lineage.html"))
    got = chart(markdown)
    assert got["boxes"]["numbered.newest_first"] == "numbered"
    assert got["boxes"]["WHERE in numbered"] == "filters on numbered"
    assert ("ops.job_runs.run_id", "numbered.newest_first", "value") in got["arrows"]
    assert ("numbered.newest_first", "WHERE in latest", "rows") in got["arrows"]
    assert ("numbered.status", "status", "value") in got["arrows"]
    entry = section(markdown, "#### `numbered.newest_first`")
    assert ("numbered.newest_first = row_number(PARTITION_BY=job_runs.job_id, "
            "ORDER_BY=descending(job_runs.run_id))\n├─ ops.job_runs.job_id  (bigint)\n"
            "└─ ops.job_runs.run_id  (bigint)") in entry
    assert "| `status` | numbered.status ← ops.job_runs.status |" in markdown
    assert "WITH numbered AS (" in markdown


def test_having_and_limit_are_drawn_as_conditions(tmp_path) -> None:
    busy = statement(
        SELECT(job_runs.job_id, AS(count_rows(), "runs")),
        FROM(job_runs),
        WHERE(last_n_days(job_runs.dt, 2)),
        GROUP_BY(job_runs.job_id),
        HAVING(at_least(count_rows(), 2)),
        ORDER_BY(descending("runs")),
        LIMIT(3),
    )
    markdown, _ = read(export_lineage(busy, to=tmp_path / "lineage.html"))
    boxes = chart(markdown)["boxes"]
    assert boxes["HAVING in busy"] == "filters on busy"
    assert boxes["LIMIT in busy"] == "filters on busy"
    assert "- HAVING in busy: `at_least(count_rows(), 2)`, which is `COUNT(*) >= 2`" in markdown
    assert "- LIMIT in busy: `ORDER BY runs DESC LIMIT 3`" in markdown


def test_a_statement_named_like_a_derived_table_keeps_its_own_group(tmp_path) -> None:
    recent = derived("recent", statement(
        SELECT(job_runs.job_id, AS(count_rows(), "runs")),
        FROM(job_runs),
        WHERE(last_n_days(job_runs.dt, 2)),
        GROUP_BY(job_runs.job_id),
    ))
    top = statement(SELECT(recent.job_id, recent.runs), FROM(recent))
    recent = top  # the Statement is now held in a variable named like its Derived table
    markdown, page = read(export_lineage(recent, to=tmp_path / "lineage.html"))
    boxes = chart(markdown)["boxes"]
    assert boxes["runs"] == "recent"
    assert boxes["recent in recent.runs"] == "recent in recent"
    data = page_data(page)
    kinds = {group["name"]: group["kind"] for group in data["groups"]}
    assert kinds["recent"] == "output"
    assert kinds["recent in recent"] == "derived"


def test_several_statements_group_the_same_table_once(tmp_path) -> None:
    team, weekly = runs_per_team(), runs_by_team()
    markdown, _ = read(export_lineage(team, weekly, to=tmp_path / "lineage.html"))
    assert markdown.count('["ops.jobs"]') == 1


def test_a_column_nothing_uses_is_left_out(tmp_path) -> None:
    latest = latest_runs()
    markdown, _ = read(export_lineage(latest, to=tmp_path / "lineage.html"))
    assert "ops.job_runs.duration_mins" not in markdown


def test_box_lines_decides_what_every_view_shows(tmp_path, monkeypatch) -> None:
    from composer_core import lineage

    shown = lineage.box_lines

    def with_kind_line(box):
        return [*shown(box), f"kind: {box['kind']}"]

    monkeypatch.setattr(lineage, "box_lines", with_kind_line)
    team = runs_per_team()
    markdown, page = read(export_lineage(team, to=tmp_path / "lineage.html"))
    assert "<small>kind: table</small>" in markdown
    data = page_data(page)
    assert ["ops.jobs.team", "string", "kind: table"] in [b["lines"] for b in data["boxes"]]


def test_the_mermaid_labels_spell_out_what_mermaid_would_misread(tmp_path) -> None:
    odd = statement(
        SELECT(jobs.job_id),
        FROM(jobs),
        WHERE(equals(jobs.job_name, 'say "<hi>" #1')),
    )
    markdown, _ = read(export_lineage(odd, to=tmp_path / "lineage.html"))
    assert "#lt;hi#gt;" in markdown and "#35;1" in markdown
    assert '"<hi>"' not in section(markdown, "## Graph")


# --- Joined across Saved tables ---------------------------------------------------------------


def test_writers_come_first_whatever_order_they_are_passed_in(tmp_path) -> None:
    fill, weekly = fill_daily_runs(), runs_by_team()
    markdown, _ = read(export_lineage(weekly, fill, to=tmp_path / "lineage.html"))
    assert markdown.startswith("# Lineage: fill, weekly\n")
    assert markdown.index("\n## fill\n") < markdown.index("\n## weekly\n")
    assert "It writes the Saved table mart.daily_runs, one day at a time." in markdown
    assert "It reads the Saved table mart.daily_runs, written by fill above." in markdown


def test_the_drawing_continues_through_a_saved_table(tmp_path) -> None:
    fill, weekly = fill_daily_runs(), runs_by_team()
    markdown, _ = read(export_lineage(fill, weekly, to=tmp_path / "lineage.html"))
    got = chart(markdown)
    assert got["boxes"]["mart.daily_runs.runs"] == "mart.daily_runs"
    assert ("runs", "mart.daily_runs.runs", "value") in got["arrows"]
    assert ("job_id", "mart.daily_runs.job_id", "value") in got["arrows"]
    assert ("mart.daily_runs.runs", "runs", "value") in got["arrows"]
    assert ("WHERE in fill", "mart.daily_runs.dt", "day written") in got["arrows"]
    assert ("ops.job_runs.dt", "WHERE in fill", "rows") in got["arrows"]
    assert ("mart.daily_runs.dt", "WHERE in weekly", "rows") in got["arrows"]


def test_the_report_continues_through_a_saved_table(tmp_path) -> None:
    fill, weekly = fill_daily_runs(), runs_by_team()
    markdown, _ = read(export_lineage(fill, weekly, to=tmp_path / "lineage.html"))
    runs = section(section(markdown, "## weekly"), "#### `runs`")
    assert ("weekly.runs = sum_of(daily_runs.runs)\n└─ mart.daily_runs.runs  (bigint)\n"
            "   └─ fill.runs = count_rows()\n") in runs
    assert ("- JOIN ON in weekly: `equals(jobs.job_id, daily_runs.job_id)`, which is "
            "`jobs.job_id = daily_runs.job_id` (reads mart.daily_runs.job_id, ops.jobs.job_id)"
            ) in runs


def test_a_writes_date_bound_decides_the_day_written_not_the_rows_read_later(tmp_path) -> None:
    fill = statement(
        INSERT_OVERWRITE(daily_runs),
        SELECT(job_runs.job_id, AS(count_rows(), "runs")),
        FROM(job_runs),
        WHERE(equals(job_runs.dt, "2026-09-24"), not_equals(job_runs.status, "TEST")),
        GROUP_BY(job_runs.dt, job_runs.job_id),
    )
    weekly = runs_by_team()
    markdown, _ = read(export_lineage(fill, weekly, to=tmp_path / "lineage.html"))
    in_fill = section(section(markdown, "## fill"), "#### `runs`")
    assert '- WHERE in fill: `equals(job_runs.dt, "2026-09-24")`' in in_fill
    in_weekly = section(section(markdown, "## weekly"), "#### `runs`")
    assert '- WHERE in fill: `not_equals(job_runs.status, "TEST")`' in in_weekly
    assert "equals(job_runs.dt" not in in_weekly


def test_a_write_over_more_days_than_the_dates_cap_shows_its_first_days_hive(
        tmp_path) -> None:
    set_load_limits(dates=1)
    fill = fill_daily_runs("2026-09-23", "2026-09-24")
    markdown, _ = read(export_lineage(fill, to=tmp_path / "lineage.html"))
    hive = section(markdown, "### Hive as submitted")
    assert "This write covers 2 days" in hive
    assert "PARTITION(dt = '2026-09-23')" in hive


def test_a_one_day_write_over_the_dates_cap_is_refused_as_to_hive_refuses_it(
        tmp_path) -> None:
    set_load_limits(dates=1)
    alerts = statement(
        INSERT_OVERWRITE(daily_runs),
        SELECT(job_runs.job_id, AS(count_rows(), "runs")),
        FROM(job_runs),
        JOIN(example_database.run_alerts,
             ON=equals(example_database.run_alerts.run_id, job_runs.run_id), many_matches=True),
        WHERE(equals(job_runs.dt, "2026-09-24"),
              between(example_database.run_alerts.dt, "2026-09-23", "2026-09-24")),
        GROUP_BY(job_runs.job_id),
    )
    with pytest.raises(LoadRefused, match="reads 2 days of ops.run_alerts"):
        export_lineage(alerts, to=tmp_path / "lineage.html")


def test_a_write_over_several_days_shows_its_first_days_hive(tmp_path) -> None:
    fill = fill_daily_runs("2026-09-23", "2026-09-24")
    markdown, _ = read(export_lineage(fill, to=tmp_path / "lineage.html"))
    hive = section(markdown, "### Hive as submitted")
    assert ("This write covers 2 days, and a write fills one day at a time: send it with "
            "`for day in by_day(fill): run(day, send=...)`. This is the first day's Hive."
            ) in hive
    assert "PARTITION(dt = '2026-09-23')" in hive


def test_two_writers_into_one_saved_table_both_draw_into_it(tmp_path) -> None:
    yesterday = fill_daily_runs()
    before = fill_daily_runs("2026-09-23", "2026-09-23")
    weekly = runs_by_team()
    markdown, _ = read(export_lineage(weekly, yesterday, before, to=tmp_path / "lineage.html"))
    arrows = chart(markdown)["arrows"]
    assert ("WHERE in yesterday", "mart.daily_runs.dt", "day written") in arrows
    assert ("WHERE in before", "mart.daily_runs.dt", "day written") in arrows
    assert "written by yesterday and before above" in markdown


def test_a_saved_table_no_statement_writes_is_an_ordinary_table(tmp_path) -> None:
    weekly = runs_by_team()
    markdown, _ = read(export_lineage(weekly, to=tmp_path / "lineage.html"))
    got = chart(markdown)
    assert got["boxes"]["mart.daily_runs.runs"] == "mart.daily_runs"
    assert not [a for a in got["arrows"] if a[1] == "mart.daily_runs.runs"]
    assert "It reads the Saved table" not in markdown


alerts_per_job = Table("mart.alerts_per_job", date_partition="dt", key=["job_id", "dt"],
                       columns={"job_id": "bigint", "alerts": "bigint", "dt": "string"})


def html_entry(page: str, name: str, group: str) -> str:
    """One calculated column's entry in the HTML page's report."""
    start = page.index(f'<summary><code>{name}</code> <span class="muted">in {group}</span>')
    return page[start:page.index("</details>", start)]


@pytest.mark.parametrize("many_matches", [False, True], ids=["one match", "many matches"])
def test_a_left_joined_saved_tables_conditions_decide_only_its_own_columns(
        tmp_path, many_matches) -> None:
    run_alerts = example_database.run_alerts
    fill = fill_daily_runs()
    alerts = statement(
        INSERT_OVERWRITE(alerts_per_job),
        SELECT(job_runs.job_id, AS(count_rows(), "alerts")),
        FROM(run_alerts),
        JOIN(job_runs, ON=equals(job_runs.run_id, run_alerts.run_id)),
        WHERE(equals(run_alerts.dt, "2026-09-24"),
              between(job_runs.dt, "2026-09-23", "2026-09-24")),
        GROUP_BY(job_runs.job_id),
    )
    day = statement(
        SELECT(daily_runs.job_id, AS(sum_of(daily_runs.runs), "runs"),
               AS(fill_null(sum_of(alerts_per_job.alerts), 0), "alerts")),
        FROM(daily_runs),
        LEFT_JOIN(alerts_per_job, ON=all_of(equals(alerts_per_job.job_id, daily_runs.job_id),
                                            equals(alerts_per_job.dt, "2026-09-24")),
                  many_matches=many_matches),
        WHERE(equals(daily_runs.dt, "2026-09-24")),
        GROUP_BY(daily_runs.job_id),
    )
    markdown, page = read(export_lineage(fill, alerts, day, to=tmp_path / "lineage.html"))
    in_day = section(markdown, "## day")
    runs, alerts_entry = section(in_day, "#### `runs`"), section(in_day, "#### `alerts`")
    # A LEFT JOIN keeps every row of daily_runs, so what decided alerts_per_job's rows decides
    # only the columns read from it, unless each run can match several of its rows.
    assert ("in alerts:" in runs) is many_matches
    assert ("in alerts:" in html_entry(page, "runs", "day")) is many_matches
    # Nor does the LEFT JOIN's own ON= decide them: it only matches each row with its alerts.
    assert ("- LEFT JOIN ON in day:" in runs) is many_matches and "- WHERE in day:" in runs
    assert ("LEFT JOIN ON in day" in html_entry(page, "runs", "day")) is many_matches
    assert "- LEFT JOIN ON in day:" in alerts_entry
    # The alerts' own column still lists the write's conditions, its date bound aside.
    assert "- JOIN ON in alerts: `equals(job_runs.run_id, run_alerts.run_id)`" in alerts_entry
    assert '- WHERE in alerts: `between(job_runs.dt, "2026-09-23", "2026-09-24")`' in alerts_entry
    assert "equals(run_alerts.dt" not in alerts_entry
    assert "JOIN ON in alerts:" in html_entry(page, "alerts", "day")


job_events = example_database.job_events
job_owners = example_database.job_owners
job_day_facts = Table("mart.job_day_facts", date_partition="dt", key=["job_id", "dt"],
                      columns={"job_id": "bigint", "team": "string", "events": "bigint",
                               "dt": "string"})


def write_job_day_facts():
    """Each job's events on 2026-09-24, with the team that owned it that day: a LEFT_JOIN to
    that day's snapshot, as the intermediate Example project's example 2 does."""
    return statement(
        INSERT_OVERWRITE(job_day_facts),
        SELECT(job_events.job_id, job_owners.team, AS(count_rows(), "events")),
        FROM(job_events),
        LEFT_JOIN(job_owners, ON=all_of(equals(job_owners.job_id, job_events.job_id),
                                        equals(job_owners.dt, job_events.dt),
                                        between(job_owners.dt, "2026-09-24", "2026-09-24"))),
        WHERE(equals(job_events.dt, "2026-09-24")),
        GROUP_BY(job_events.dt, job_events.job_id, job_owners.team),
    )


def test_a_writers_left_join_decides_only_the_columns_read_from_its_table_downstream(
        tmp_path) -> None:
    facts = write_job_day_facts()
    per_team = statement(
        SELECT(job_day_facts.team, AS(sum_of(job_day_facts.events), "events"),
               AS(count_rows(where=is_null(job_day_facts.team)), "days_with_no_team")),
        FROM(job_day_facts),
        WHERE(equals(job_day_facts.dt, "2026-09-24")),
        GROUP_BY(job_day_facts.team),
    )
    markdown, page = read(export_lineage(facts, per_team, to=tmp_path / "lineage.html"))
    in_per_team = section(markdown, "## per_team")
    events = section(in_per_team, "#### `events`")
    no_team = section(in_per_team, "#### `days_with_no_team`")
    # events never reads job_owners, so the LEFT JOIN that looked each team up can't change
    # which rows it adds up, though it decides the team each row is grouped under.
    assert "LEFT JOIN ON in facts" not in events
    assert "LEFT JOIN ON in facts" not in html_entry(page, "events", "per_team")
    assert "- WHERE in facts: `equals(job_events.dt" not in events  # the day written
    assert "- WHERE in per_team:" in events
    # A column worked out from the team does depend on whether the LEFT JOIN matched.
    assert "- LEFT JOIN ON in facts:" in no_team
    assert "LEFT JOIN ON in facts" in html_entry(page, "days_with_no_team", "per_team")


def test_a_writes_bound_on_a_joined_tables_day_matched_to_the_day_written_stays_in_its_section(
        tmp_path) -> None:
    """How-to 23's team write reads each job's team from the snapshot of the day it writes:
    the bound on job_owners.dt follows the day written, so a later reader of many days doesn't
    list it, as it doesn't list the day written."""
    team_day = Table("mart.team_day", date_partition="dt", key=["team", "dt"],
                     columns={"team": "string", "events": "bigint", "dt": "string"})
    team_day_step = statement(
        INSERT_OVERWRITE(team_day),
        SELECT(job_owners.team, AS(sum_of(job_day_facts.events), "events")),
        FROM(job_day_facts),
        JOIN(job_owners, ON=all_of(equals(job_owners.job_id, job_day_facts.job_id),
                                   equals(job_owners.dt, job_day_facts.dt))),
        WHERE(equals(job_day_facts.dt, "2026-09-24"), equals(job_owners.dt, "2026-09-24")),
        GROUP_BY(job_day_facts.dt, job_owners.team),
    )
    weekly = statement(
        SELECT(team_day.team, AS(sum_of(team_day.events), "events")),
        FROM(team_day),
        WHERE(between(team_day.dt, "2026-09-21", "2026-09-27")),
        GROUP_BY(team_day.team),
    )
    markdown, page = read(export_lineage(weekly, team_day_step, to=tmp_path / "lineage.html"))
    in_weekly = section(section(markdown, "## weekly"), "#### `events`")
    assert "- WHERE in team_day_step:" not in in_weekly
    assert "WHERE in team_day_step" not in html_entry(page, "events", "weekly")
    assert "- JOIN ON in team_day_step:" in in_weekly and "- WHERE in weekly:" in in_weekly
    in_write = section(section(markdown, "## team_day_step"), "#### `events`")
    assert '- WHERE in team_day_step: `equals(job_owners.dt, "2026-09-24")`' in in_write


def test_a_left_join_decides_every_column_when_a_condition_reads_its_table(tmp_path) -> None:
    """An anti-join: WHERE keeps the rows the LEFT JOIN found no match for."""
    no_snapshot = statement(
        SELECT(job_events.job_id, AS(count_rows(), "events")),
        FROM(job_events),
        LEFT_JOIN(job_owners, ON=all_of(equals(job_owners.job_id, job_events.job_id),
                                        equals(job_owners.dt, job_events.dt),
                                        between(job_owners.dt, "2026-09-24", "2026-09-24"))),
        WHERE(equals(job_events.dt, "2026-09-24"), is_null(job_owners.team)),
        GROUP_BY(job_events.job_id),
    )
    markdown, _ = read(export_lineage(no_snapshot, to=tmp_path / "lineage.html"))
    events = section(section(markdown, "## no_snapshot"), "#### `events`")
    assert "- LEFT JOIN ON in no_snapshot:" in events
    assert "- WHERE in no_snapshot: `is_null(job_owners.team)`" in events


def test_a_loop_of_writes_is_refused_naming_the_statements_and_tables() -> None:
    other = Table("mart.other_runs", date_partition="dt",
                  columns={"job_id": "bigint", "runs": "bigint", "dt": "string"})
    one = statement(INSERT_OVERWRITE(other), SELECT(daily_runs.job_id, daily_runs.runs),
                    FROM(daily_runs), WHERE(equals(daily_runs.dt, "2026-09-24")))
    two = statement(INSERT_OVERWRITE(daily_runs), SELECT(other.job_id, other.runs),
                    FROM(other), WHERE(equals(other.dt, "2026-09-24")))
    with pytest.raises(ValueError) as refused:
        export_lineage(one, two)
    message = str(refused.value)
    assert "one writes mart.other_runs, which two reads" in message
    assert "two writes mart.daily_runs, which one reads" in message
    assert re.search(r"Opt-out: +none", message)


def test_the_loop_refusal_names_only_the_statements_in_the_loop() -> None:
    other = Table("mart.other_runs", date_partition="dt",
                  columns={"job_id": "bigint", "runs": "bigint", "dt": "string"})
    one = statement(INSERT_OVERWRITE(other), SELECT(daily_runs.job_id, daily_runs.runs),
                    FROM(daily_runs), WHERE(equals(daily_runs.dt, "2026-09-24")))
    two = statement(INSERT_OVERWRITE(daily_runs), SELECT(other.job_id, other.runs),
                    FROM(other), WHERE(equals(other.dt, "2026-09-24")))
    three = statement(SELECT(other.job_id), FROM(other), WHERE(equals(other.dt, "2026-09-24")))
    four = statement(SELECT(other.job_id), FROM(other), WHERE(equals(other.dt, "2026-09-24")))
    with pytest.raises(ValueError) as refused:
        export_lineage(three, one, two, four)
    message = str(refused.value)
    assert "one writes mart.other_runs, which two reads;" in message
    assert "two writes mart.daily_runs, which one reads." in message
    assert "three" not in message and "four" not in message


def test_a_statement_reading_the_saved_table_it_writes_is_a_loop() -> None:
    again = statement(INSERT_OVERWRITE(daily_runs), SELECT(daily_runs.job_id, daily_runs.runs),
                      FROM(daily_runs), WHERE(equals(daily_runs.dt, "2026-09-24")))
    with pytest.raises(ValueError, match="again writes mart.daily_runs, which again reads"):
        export_lineage(again)


# --- Misuse ------------------------------------------------------------------------------------


def test_no_statement_is_refused() -> None:
    with pytest.raises(TypeError, match="was given no Statement"):
        export_lineage()


@pytest.mark.parametrize("thing", ["SELECT 1", job_runs, create_table(daily_runs)],
                         ids=["a string", "a table", "create_table"])
def test_what_isnt_a_statement_reading_a_table_is_refused(thing) -> None:
    with pytest.raises(TypeError, match="isn't a Statement that reads a table"):
        export_lineage(thing)


def test_the_same_statement_twice_is_drawn_once(tmp_path) -> None:
    team = runs_per_team()
    markdown, _ = read(export_lineage(team, team, to=tmp_path / "lineage.html"))
    assert markdown.count("\n## team\n") == 1


# --- The HTML page ------------------------------------------------------------------------------


def test_the_page_needs_nothing_beyond_itself(tmp_path) -> None:
    _, page = read(export_lineage(runs_per_team(), to=tmp_path / "lineage.html"))
    assert "<script src" not in page
    assert "http://" not in page and "https://" not in page
    assert "<link" not in page


def test_without_scripts_the_page_shows_the_report_and_points_at_the_markdown(tmp_path) -> None:
    team = runs_per_team()
    html_file, markdown_file = export_lineage(team, to=tmp_path / "team.html")
    page = html_file.read_text(encoding="utf-8")
    noscript = page.split("<noscript>", 1)[1].split("</noscript>", 1)[0]
    assert markdown_file.name in noscript
    report = page.split('<section id="report">', 1)[1].split("</section>", 1)[0]
    assert "<h3>Calculated columns</h3>" in report
    assert "team.runs = count_rows()" in report


def test_the_page_draws_from_the_same_boxes_and_arrows(tmp_path) -> None:
    fill, weekly = fill_daily_runs(), runs_by_team()
    _, page = read(export_lineage(fill, weekly, to=tmp_path / "lineage.html"))
    data = page_data(page)
    names = {box["id"]: box["lines"][0] for box in data["boxes"]}
    arrows = {(names[a], names[b], kind) for a, b, kind in data["arrows"]}
    assert ("WHERE in fill", "mart.daily_runs.dt", "day") in arrows
    assert ("mart.daily_runs.runs", "runs", "value") in arrows
    kinds = {group["name"]: group["kind"] for group in data["groups"]}
    assert kinds == {"ops.job_runs": "table", "fill": "output", "mart.daily_runs": "table",
                     "ops.jobs": "table", "weekly": "output"}


def test_text_that_looks_like_the_pages_own_markers_stays_as_written(tmp_path) -> None:
    odd = statement(
        SELECT(jobs.job_id),
        FROM(jobs),
        WHERE(equals(jobs.job_name, "__DATA__ __REPORT__")),
    )
    _, page = read(export_lineage(odd, to=tmp_path / "__MD__.html"))
    assert page.count("const graph = ") == 1
    assert "jobs.job_name = &#x27;__DATA__ __REPORT__&#x27;" in page
    assert "<code>__MD__.md</code>" in page


def test_text_in_the_graph_data_cant_end_the_script(tmp_path) -> None:
    odd = statement(
        SELECT(jobs.job_id),
        FROM(jobs),
        WHERE(equals(jobs.job_name, "</script><b>")),
    )
    _, page = read(export_lineage(odd, to=tmp_path / "lineage.html"))
    assert page.count("</script>") == 1
    assert "&lt;/script&gt;&lt;b&gt;" in page


@pytest.mark.skipif(shutil.which("node") is None,
                    reason="Node isn't installed to read the page's script")
def test_the_pages_script_is_javascript_a_browser_can_read(tmp_path) -> None:
    """The page's drawing is about 760 lines of JavaScript inside a Python string, which no
    other test runs: Node reads it as a browser would, and stops on a syntax error."""
    _, page = read(export_lineage(runs_per_team(), to=tmp_path / "lineage.html"))
    script = page.split("<script>", 1)[1].rsplit("</script>", 1)[0]
    (tmp_path / "page.js").write_text(script, encoding="utf-8")
    checked = subprocess.run(["node", "--check", str(tmp_path / "page.js")],
                             capture_output=True, text=True)
    assert checked.returncode == 0, checked.stderr
