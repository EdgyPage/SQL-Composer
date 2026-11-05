"""The seed's limits: a converted table that reads itself copies its original's rows once, and
only the Partitions its SEED names. Toolbox 8.4, ticket 09.

A limit is by partition column, any of its partition columns, a date or not: a value, that
value or later; a range, {"from": ..., "to": ...}; a list, those values alone. A value may be
a Run value's function.
"""

from __future__ import annotations

import datetime
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest
from conftest import forget_the_projects_modules

from sqlglot_composer import Table, example_database, project, seed_copy, to_hive

LOG = Table("mart_dev.team_log", columns={"run_id": "bigint", "dt": "string",
                                          "team": "string", "batch_no": "int"},
            partitioned_by=["dt", "team", "batch_no"], location="/data/team/mart_dev.db/log")
COPY = "INSERT OVERWRITE TABLE mart_dev.team_log PARTITION (dt, team, batch_no) SELECT * FROM "


def latest_day() -> datetime.date:
    return datetime.date(2026, 9, 24)


@pytest.mark.parametrize(("limits", "where"), [
    (None, ""),
    ({}, ""),
    ({"dt": "2026-09-24"}, " WHERE dt >= '2026-09-24'"),
    ({"dt": {"from": "2026-09-01", "to": "2026-09-24"}},
     " WHERE dt >= '2026-09-01' AND dt <= '2026-09-24'"),
    ({"dt": {"to": "2026-09-24"}}, " WHERE dt <= '2026-09-24'"),
    ({"team": ["US", "CA"]}, " WHERE team IN ('US', 'CA')"),
    ({"batch_no": 400}, " WHERE batch_no >= 400"),
    ({"batch_no": [7, 9]}, " WHERE batch_no IN (7, 9)"),
    ({"dt": latest_day, "team": "web"}, " WHERE dt >= '2026-09-24' AND team >= 'web'"),
    ({"dt": datetime.date(2026, 9, 1)}, " WHERE dt >= '2026-09-01'"),
], ids=["none", "empty", "a value", "a range", "a top end", "a list", "a number",
        "a list of numbers", "a Run value", "a date"])
def test_a_seed_copies_the_partitions_its_limits_name(limits: dict[str, object] | None,
                                                      where: str) -> None:
    assert to_hive(seed_copy(LOG, "mart.team_log", limits)) == COPY + "mart.team_log" + where


@pytest.mark.parametrize(("limits", "said"), [
    ({"run_id": 5}, "run_id isn't a partition column of mart_dev.team_log"),
    ({"batch_no": "many"}, "batch_no's limit 'many' doesn't fit its type, int"),
    ({"dt": {"since": "2026-09-01"}}, "dt's limit {'since': '2026-09-01'} isn't a range"),
    ({"dt": True}, "dt's limit True doesn't fit its type, string"),
])
def test_a_limit_that_doesnt_fit_is_refused(limits: dict[str, object], said: str) -> None:
    with pytest.raises(ValueError, match=said):
        seed_copy(LOG, "mart.team_log", limits)


def test_a_table_with_no_partitions_copies_everything() -> None:
    flat = Table("mart_dev.grows", columns={"job_id": "bigint"}, location="/data/grows")
    assert to_hive(seed_copy(flat, "mart.grows")) == (
        "INSERT OVERWRITE TABLE mart_dev.grows SELECT * FROM mart.grows")
    with pytest.raises(ValueError, match="which has none"):
        seed_copy(flat, "mart.grows", {"dt": "2026-09-24"})


# --- Answered in the decisions cell -----------------------------------------------------------

# Two tables that read themselves, one partitioned by a day and a team, one by a day alone, and
# one that doesn't read itself.
SCRIPT = """CREATE TABLE IF NOT EXISTS ops_reports.log (run_id BIGINT, job_id BIGINT)
PARTITIONED BY (dt STRING, team STRING);
CREATE TABLE IF NOT EXISTS ops_reports.days (run_id BIGINT) PARTITIONED BY (dt STRING);
CREATE TABLE IF NOT EXISTS ops_reports.flat (job_id BIGINT);
INSERT INTO TABLE ops_reports.log PARTITION (dt, team)
SELECT r.run_id, r.job_id, r.dt, 'web' AS team FROM ops.job_runs r WHERE r.dt = '2026-09-24'
  AND r.run_id NOT IN (SELECT l.run_id FROM ops_reports.log l);
INSERT INTO TABLE ops_reports.days PARTITION (dt)
SELECT r.run_id, r.dt FROM ops.job_runs r WHERE r.dt = '2026-09-24'
  AND r.run_id NOT IN (SELECT d.run_id FROM ops_reports.days d);
INSERT OVERWRITE TABLE ops_reports.flat SELECT j.job_id FROM ops.jobs j;
"""
LOG_DEV, DAYS_DEV, FLAT_DEV = ("mart_dev.log_ops_reports", "mart_dev.days_ops_reports",
                               "mart_dev.flat_ops_reports")


@pytest.fixture
def converted(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Path]:
    """The script converted in a started Project, its DEV filled in."""
    monkeypatch.setattr(sys, "path", [str(tmp_path), *sys.path])
    monkeypatch.chdir(tmp_path)
    project.start()
    databases = tmp_path / "admin" / "databases.py"
    databases.write_text(databases.read_text(encoding="utf-8")
                         .replace('"<DEV_DATABASE>"', '"mart_dev"'), encoding="utf-8")
    (tmp_path / "script.hql").write_text(SCRIPT, encoding="utf-8")
    project.convert("script", files=["script.hql"], query=example_database.query,
                    database="ops")
    yield tmp_path
    forget_the_projects_modules()


def _reference(root: Path, table: str) -> str:
    return (root / "references" / f"{table.replace('.', '__')}.py").read_text(encoding="utf-8")


def test_a_table_that_reads_itself_has_seed_limits_to_answer(converted: Path) -> None:
    assert "SEED = {}" in _reference(converted, LOG_DEV)
    assert "SEED" not in _reference(converted, FLAT_DEV)
    assert to_hive(project.load(LOG_DEV).seed()) == (
        "INSERT OVERWRITE TABLE mart_dev.log_ops_reports PARTITION (dt, team) "
        "SELECT * FROM ops_reports.log")


def test_a_tables_own_seed_answer_limits_its_seed(converted: Path) -> None:
    said = repr(project.write_decisions(
        {LOG_DEV: {"seed": {"dt": {"from": "2026-09-24"}, "team": ["web"]}}}))
    assert f"Wrote 1 answer into references/{LOG_DEV.replace('.', '__')}.py." in said
    assert 'SEED = {"dt": {"from": "2026-09-24"}, "team": ["web"]}' in (
        _reference(converted, LOG_DEV))
    assert to_hive(project.load(LOG_DEV).seed()).endswith(
        "SELECT * FROM ops_reports.log WHERE dt >= '2026-09-24' AND team IN ('web')")


def test_all_tables_seed_limits_each_table_with_that_partition_column(converted: Path) -> None:
    project.write_decisions({"all_tables": {"seed": {"team": ["web"], "dt": "2026-09-01"}}},
                            tables=[LOG_DEV, DAYS_DEV, FLAT_DEV])
    assert 'SEED = {"team": ["web"], "dt": "2026-09-01"}' in _reference(converted, LOG_DEV)
    # days has no team: only its dt is limited. flat doesn't read itself: it has no seed.
    assert 'SEED = {"dt": "2026-09-01"}' in _reference(converted, DAYS_DEV)
    assert "SEED" not in _reference(converted, FLAT_DEV)


def test_a_seed_answer_that_matches_nothing_is_refused(converted: Path) -> None:
    with pytest.raises(ValueError) as refused:
        project.write_decisions({LOG_DEV: {"seed": {"run_id": 5}},
                                 FLAT_DEV: {"seed": {"dt": "2026-09-24"}}})
    said = str(refused.value)
    assert f"{LOG_DEV}: seed: run_id is no partition column of {LOG_DEV}" in said
    assert f"{FLAT_DEV}: seed: {FLAT_DEV}'s Table reference has no SEED to limit" in said
    assert "SEED = {}" in _reference(converted, LOG_DEV)


def test_a_run_value_limits_a_seed(converted: Path) -> None:
    (converted / "building_blocks" / "run_values.py").write_text(
        "import datetime\n\n\ndef seed_start() -> datetime.date:\n"
        "    return datetime.date(2026, 9, 20)\n", encoding="utf-8")
    from building_blocks.run_values import seed_start
    project.write_decisions({LOG_DEV: {"seed": {"dt": {"from": seed_start}}}})
    reference = _reference(converted, LOG_DEV)
    assert "from building_blocks.run_values import seed_start  # a Run value" in reference
    assert 'SEED = {"dt": {"from": seed_start}}' in reference
    assert to_hive(project.load(LOG_DEV).seed()).endswith("WHERE dt >= '2026-09-20'")
    sys.modules.pop("building_blocks.run_values", None)


def test_an_empty_list_or_a_number_that_isnt_one_is_refused() -> None:
    with pytest.raises(ValueError, match="team's limit is an empty list"):
        seed_copy(LOG, "mart.team_log", {"team": []})
    with pytest.raises(ValueError, match="doesn't fit its type, int"):
        seed_copy(LOG, "mart.team_log", {"batch_no": float("nan")})


def test_all_tables_seed_naming_no_tables_column_is_refused(converted: Path) -> None:
    with pytest.raises(ValueError, match="all_tables: seed: region is no partition column of "
                                         "any table with a seed"):
        project.write_decisions({"all_tables": {"seed": {"region": ["US"]}}},
                                tables=[LOG_DEV, DAYS_DEV])


def test_all_tables_seed_says_which_tables_it_was_written_into(converted: Path) -> None:
    said = repr(project.write_decisions(
        {"all_tables": {"seed": {"dt": "2026-09-01"}},
         DAYS_DEV: {"seed": {"dt": "2026-09-20"}}}, tables=[LOG_DEV, DAYS_DEV, FLAT_DEV]))
    assert (f"all_tables: seed: written into {LOG_DEV}, each for the partition columns it "
            f"has; a table that doesn't read itself has no seed. {DAYS_DEV} keeps its own."
            in said)
