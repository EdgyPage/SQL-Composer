"""The Example database's tables that aren't partitioned by a day, described and queried
like Hive.

ops.region_budgets is partitioned by region alone, and ops.team_notes isn't partitioned and has
no Key. With ops.jobs, which isn't partitioned either, and the six tables partitioned by a day,
the Example database holds the three kinds of table a warehouse holds. Each query's answer is
checked against the same numbers worked out in pandas.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from conftest import example_rows
from sqlglot_composer import (
    AS,
    FROM,
    GROUP_BY,
    JOIN,
    SELECT,
    LoadRefused,
    Table,
    check_key,
    check_table_reference,
    count_rows,
    equals,
    example_database,
    run_query,
    statement,
    write_table_reference,
)
from sqlglot_composer.refusals import RepeatedRowsWarning

budgets = example_database.region_budgets
notes = example_database.team_notes
jobs = example_database.jobs


def described(name: str) -> list[tuple[str | None, ...]]:
    """DESCRIBE's rows, a missing cell read as None: pandas 3 shows missing text as NaN."""
    frame = example_database.query(f"DESCRIBE {name}")
    return [tuple(None if pd.isna(cell) else cell for cell in row)
            for row in frame.itertuples(index=False, name=None)]


# --- The three kinds --------------------------------------------------------------------------


def test_the_example_database_holds_all_three_kinds_of_table() -> None:
    kinds = {name: tuple(table._partitioned_by)
             for name, (table, _) in example_database._TABLES.items()}
    assert sorted(name for name, partitions in kinds.items() if not partitions) == [
        "jobs", "team_notes"]
    assert kinds["region_budgets"] == ("region",)
    assert sorted(name for name, partitions in kinds.items() if partitions[-1:] == ("dt",)) == [
        "job_events", "job_owners", "job_runs", "region_costs", "run_alerts", "scheduler_runs"]


def test_every_table_but_team_notes_has_a_key() -> None:
    assert [name for name, (table, _) in example_database._TABLES.items()
            if table._key is None] == ["team_notes"]


# --- DESCRIBE and SHOW PARTITIONS -------------------------------------------------------------


def test_region_budgets_is_described_like_hive() -> None:
    assert described("ops.region_budgets") == [
        ("job_id", "bigint", ""),
        ("budget_cents", "bigint", "the most a day of the job should cost there"),
        ("region", "string", ""),
        ("", None, None),
        ("# Partition Information", None, None),
        ("# col_name", "data_type", "comment"),
        ("region", "string", ""),
    ]


def test_team_notes_is_described_with_no_partitions() -> None:
    assert described("ops.team_notes") == [
        ("team", "string", ""),
        ("note", "string", ""),
        ("written_on", "string", "the day the note was written, as yyyy-MM-dd"),
    ]


def test_region_budgets_lists_each_region() -> None:
    partitions = example_database.query("SHOW PARTITIONS ops.region_budgets")
    assert list(partitions.partition) == ["region=eu", "region=us"]


def test_show_partitions_of_team_notes_is_hives_error() -> None:
    with pytest.raises(ValueError, match="ops.team_notes is not a partitioned table"):
        example_database.query("SHOW PARTITIONS ops.team_notes")


# --- Table references -------------------------------------------------------------------------


def test_write_table_reference_on_region_budgets_lists_region_alone(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    text = write_table_reference("ops.region_budgets",
                                 query=example_database.query).read_text(encoding="utf-8")
    assert '    partitioned_by=["region"],\n' in text
    assert '"budget_cents": "the most a day of the job should cost there",' in text


def test_write_table_reference_on_team_notes_has_no_partitions(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    text = write_table_reference("ops.team_notes",
                                 query=example_database.query).read_text(encoding="utf-8")
    assert "partitioned_by" not in text
    assert "    key=None,  # TODO" in text


@pytest.mark.parametrize("t", [budgets, notes])
def test_check_table_reference_finds_each_one_matches(t: Table) -> None:
    assert str(check_table_reference(t, query=example_database.query)) == (
        f"{t._name} matches its Table reference.")


def test_check_key_holds_on_one_region() -> None:
    verdict = check_key(budgets, query=example_database.query,
                        where=equals(budgets.region, "eu"))
    assert str(verdict) == (
        "ops.region_budgets: the key (job_id, region) holds "
        "where region_budgets.region = 'eu'.")


def test_check_key_on_team_notes_says_it_has_no_key() -> None:
    with pytest.raises(ValueError, match="declares no key"):
        check_key(notes, query=example_database.query)


# --- The Load limit, and the Warning a table with no Key brings ---------------------------


def test_a_read_of_region_budgets_names_its_regions() -> None:
    with pytest.raises(LoadRefused, match="filters none of its partition columns: region"):
        statement(SELECT(budgets.job_id), FROM(budgets))


def test_a_read_of_team_notes_is_never_limited() -> None:
    found = run_query(statement(SELECT(notes.team, AS(count_rows(), "notes")), FROM(notes),
                                GROUP_BY(notes.team)), example_database.query)
    expected = example_rows("team_notes").groupby("team").size()
    assert found.set_index("team").notes.to_dict() == expected.to_dict()


def test_a_join_onto_team_notes_is_warned_and_counts_each_job_once_per_note() -> None:
    """The Warning catches a wrong number: a team's jobs, counted after joining its notes,
    come out once per note."""
    with pytest.warns(RepeatedRowsWarning, match="team_notes declares no Key"):
        s = statement(SELECT(jobs.team, AS(count_rows(), "jobs")), FROM(jobs),
                      JOIN(notes, ON=equals(notes.team, jobs.team)), GROUP_BY(jobs.team))
    found = run_query(s, example_database.query).set_index("team").jobs.to_dict()
    jobs_per_team = example_rows("jobs").groupby("team").size()
    notes_per_team = example_rows("team_notes").groupby("team").size()
    assert found == (jobs_per_team * notes_per_team).to_dict()
    assert found != jobs_per_team.to_dict()


# --- The rows ---------------------------------------------------------------------------------


def test_each_job_has_one_budget_in_the_region_it_is_billed_in() -> None:
    rows = example_rows("region_budgets")
    assert not rows.duplicated(subset=["job_id", "region"]).any()
    assert sorted(rows.job_id) == sorted(example_rows("jobs").job_id)
    billed = example_rows("region_costs")[["job_id", "region"]].drop_duplicates()
    assert set(map(tuple, billed.values)) <= set(map(tuple, rows[["job_id", "region"]].values))


def test_every_note_is_by_a_team_that_owns_a_job() -> None:
    assert set(example_rows("team_notes").team) <= set(example_rows("jobs").team)
