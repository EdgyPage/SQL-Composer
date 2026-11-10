# Batch team_fails

1 script, each read where it is: admin/workflows/convert/weekly_fails.hql. Each table they write is a Saved table in the Dev Database, mart_dev; one they only create has its Table reference alone.

## Tables

- mart.team_fails: mart_dev.team_fails, tables/mart_dev__team_fails/, its checklist tables/mart_dev__team_fails/conversion/checklist.md
  - # CONVERSION: FROM(r, reads_all_partitions=True), a note on its checklist
  - # CONVERSION: JOIN(o, many_matches=True), a note on its checklist
  - # CONVERSION: JOIN(o, reads_all_partitions=True), a note on its checklist

## Each statement, in the order they run

1. weekly_fails.hql line 1, `SET hive.exec.dynamic.partition.mode=nonstrict`: the Session settings of the writes after it in its script
2. weekly_fails.hql line 2, `CREATE TABLE IF NOT EXISTS mart.team_fails (team STRING, fails BIGINT) PARTIT...`: the columns, types and Partitions of mart_dev.team_fails's Table reference
3. weekly_fails.hql line 4, `WITH f AS (SELECT r.job_id, r.dt FROM ops.job_runs r WHERE r.status = 'FAILED...`: mart_dev.team_fails, written by its notebook
