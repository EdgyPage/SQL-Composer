"""The conversion chart: other people's Hive of each common shape, converted and checked both
ways on the Intermediate Example project (Toolbox 7.2, ticket 10).

Each query is converted with project.convert, as a user converts one, into a Saved table in the
Project's Dev Database, mart, then checked: its Hive is the original's,
once both are written out the same way, on every sqlglot the Toolbox takes; and its rows are the
original's on a Partition that has rows, through the Example database. A query a Conversion
can't take is refused, saying what to do.
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path

import pytest

from sqlglot_composer import compare_with_original, example_database, project

INTERMEDIATE = Path(__file__).parents[1] / "example_projects" / "intermediate"

# name: (the Hive as someone else wrote it, the Partition its rows are compared on)
CHART = {
    "filtered_events": ("""\
SELECT e.job_id, e.event_type, e.minutes, e.dt
FROM ops.job_events e
WHERE e.dt = '2026-09-24'
  AND e.event_type IN ('start', 'finish', 'retry', 'fail')
  AND e.minutes >= 5
ORDER BY e.job_id, e.minutes DESC
""", "2026-09-24"),
    "team_counts": ("""\
WITH owned AS (
  SELECT e.job_id, e.event_type, o.team, e.dt
  FROM ops.job_events e
  LEFT JOIN ops.job_owners o ON o.job_id = e.job_id AND o.dt = e.dt
  WHERE e.dt BETWEEN '2026-09-22' AND '2026-09-24'
)
SELECT owned.team,
       CASE owned.team WHEN 'data' THEN 'Data platform' WHEN 'web' THEN 'Web' ELSE 'Other' """
"""END AS team_name,
       COUNT(*) AS events,
       COUNT(DISTINCT owned.job_id) AS jobs,
       SUM(CASE WHEN owned.event_type = 'fail' THEN 1 ELSE 0 END) AS fails,
       owned.dt
FROM owned
GROUP BY owned.team, owned.dt
HAVING COUNT(*) > 1
""", "2026-09-24"),
    "latest_event": ("""\
SELECT * FROM (
  SELECT e.job_id, e.event_type, e.dt,
         ROW_NUMBER() OVER (PARTITION BY e.job_id ORDER BY e.minutes DESC, e.event_type) AS rn
  FROM ops.job_events e
  WHERE e.dt = '2026-09-24'
) ranked
WHERE ranked.rn = 1
""", "2026-09-24"),
    "costs_by_region": ("""\
SET hive.exec.parallel=true;
INSERT INTO TABLE ops_reports.region_totals PARTITION (dt)
SELECT c.region,
       SUM(c.cost_cents) AS cost_cents,
       COALESCE(MAX(c.cost_cents), 0) AS biggest,
       c.dt
FROM ops.region_costs c
WHERE c.dt BETWEEN '20260918' AND '20260921'
GROUP BY c.region, c.dt
""", "20260921"),
    "both_regions": ("""\
SELECT c.job_id, c.cost_cents, c.dt FROM ops.region_costs c WHERE c.dt = '20260921' AND """
"""c.region = 'eu'
UNION ALL
SELECT c.job_id, c.cost_cents, c.dt FROM ops.region_costs c WHERE c.dt = '20260921' AND """
"""c.region = 'us'
""", "20260921"),
}


# The Saved table each query becomes in mart: the batch's name, but where its INSERT names the
# table it writes, <table>_<its database>.
MADE = {"costs_by_region": "region_totals_ops_reports"}


def made(name: str) -> str:
    """The short name of the Saved table a chart query becomes in mart."""
    return MADE.get(name, name)


@pytest.fixture
def intermediate(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A copy of the Intermediate Example project, worked in at its top."""
    shutil.copytree(INTERMEDIATE, tmp_path, dirs_exist_ok=True)
    monkeypatch.chdir(tmp_path)
    monkeypatch.syspath_prepend(str(tmp_path))
    for name in [name for name in sys.modules
                 if name.split(".")[0] in ("references", "warehouse")]:
        monkeypatch.delitem(sys.modules, name)
    return tmp_path


@pytest.mark.parametrize("name", list(CHART))
def test_each_query_of_the_chart_converts_to_the_same_hive(intermediate: Path,
                                                           name: str) -> None:
    """Its tables have Table references in the Project, so it needs no query."""
    project.convert(name, CHART[name][0])
    conversion = intermediate / "tables" / f"mart__{made(name)}" / "conversion"
    scan = (conversion / "scan.md").read_text(encoding="utf-8")
    assert ("Its Hive and the original's: The Statement's Hive and the original are the same "
            "query, once both are written out the same way.") in scan, scan


@pytest.mark.parametrize("name", list(CHART))
def test_each_query_of_the_chart_converts_to_the_same_rows(intermediate: Path,
                                                           name: str) -> None:
    hive, day = CHART[name]
    project.convert(name, hive, query=example_database.query)
    verdict = compare_with_original(project.load(f"mart.{made(name)}").preview(), hive,
                                    query=example_database.query, partition={"dt": day})
    assert verdict.ok, verdict
    rows = re.search(r": (\d+) rows? each\.", repr(verdict))
    assert rows and int(rows.group(1)) > 0, verdict  # a Partition with rows proves something


def test_the_window_and_the_query_in_brackets_convert_as_you_would_write_them(
        intermediate: Path) -> None:
    project.convert("latest_event", CHART["latest_event"][0])
    logic = (intermediate / "tables" / "mart__latest_event" / "mart__latest_event.ipynb"
             ).read_text(encoding="utf-8")
    assert 'ranked = derived(\\"ranked\\", statement(' in logic
    assert "row_number(over=window(PARTITION_BY=[e.job_id], ORDER_BY=[descending(e.minutes)" \
           in logic
    assert "SELECT(*all_columns(ranked))" in logic


@pytest.mark.parametrize(("hive", "said"), [
    pytest.param("FROM ops.job_events e\nINSERT OVERWRITE TABLE a.x SELECT e.job_id\n"
                 "INSERT OVERWRITE TABLE a.y SELECT e.dt",
                 "it is one FROM with 2 INSERTs, into a.x, a.y",
                 id="two_inserts_from_one_from"),
    pytest.param("DROP TABLE ops.job_events", "it is a DROP, not a query", id="not_a_query"),
])
def test_what_a_conversion_cant_take_is_refused_saying_what_to_do(
        intermediate: Path, hive: str, said: str) -> None:
    with pytest.raises(ValueError) as refused:
        project.scan_hive(hive)
    message = str(refused.value)
    assert f"a Conversion can't take this Hive: {said}" in message
    assert "unchecked_hive(...)" in message
