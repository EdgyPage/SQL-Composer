# Batch weekly

1 script, each read where it is: C:/Users/myfir/AppData/Local/Temp/usability-loop/runs/2026-11-06-H1-1/from_your_team/weekly.hql. Each table they write is a Saved table in the Dev Database, mart_dev; one they only create has its Table reference alone.

## Tables

- mart.team_fails: mart_dev.team_fails, tables/mart_dev__team_fails/, its checklist tables/mart_dev__team_fails/conversion/checklist.md
  - # CONVERSION: FROM(r, reads_all_partitions=True), a note on its checklist
  - # CONVERSION: FROM(o, reads_all_partitions=True), a note on its checklist
  - # CONVERSION: JOIN(w, many_matches=True), a note on its checklist
- mart.job_runs_counted: mart_dev.job_runs_counted, tables/mart_dev__job_runs_counted/, its checklist tables/mart_dev__job_runs_counted/conversion/checklist.md
  - # CONVERSION: FROM(r, reads_all_partitions=True), a note on its checklist
- mart.job_fails_counted: mart_dev.job_fails_counted, tables/mart_dev__job_fails_counted/, its checklist tables/mart_dev__job_fails_counted/conversion/checklist.md
  - # CONVERSION: FROM(r, reads_all_partitions=True), a note on its checklist

## Each statement, in the order they run

1. weekly.hql line 1, `SET hive.exec.dynamic.partition.mode=nonstrict`: the Session settings of the writes after it in its script
2. weekly.hql line 2, `CREATE TABLE IF NOT EXISTS mart.team_fails (team STRING, fails BIGINT) PARTIT...`: the columns, types and Partitions of mart_dev.team_fails's Table reference
3. weekly.hql line 4, `CREATE TABLE IF NOT EXISTS mart.job_runs_counted (job_id BIGINT, runs BIGINT)...`: the columns, types and Partitions of mart_dev.job_runs_counted's Table reference
4. weekly.hql line 6, `CREATE TABLE IF NOT EXISTS mart.job_fails_counted (job_id BIGINT, fails BIGIN...`: the columns, types and Partitions of mart_dev.job_fails_counted's Table reference
5. weekly.hql line 8, `CREATE TEMPORARY TABLE failed_runs AS SELECT r.job_id, r.dt FROM ops.job_runs...`: folded into mart.team_fails: a Derived table there, never created, written, compared or promoted
6. weekly.hql line 10, `WITH owned AS (SELECT o.job_id, o.team FROM ops.job_owners o) INSERT OVERWRIT...`: mart_dev.team_fails, written by its notebook
7. weekly.hql line 15, `FROM ops.job_runs r INSERT OVERWRITE TABLE mart.job_runs_counted PARTITION (d...`: mart_dev.job_runs_counted, written by its notebook (was one target of a FROM with several INSERTs)
8. weekly.hql line 15, `FROM ops.job_runs r INSERT OVERWRITE TABLE mart.job_runs_counted PARTITION (d...`: mart_dev.job_fails_counted, written by its notebook (was one target of a FROM with several INSERTs)
9. weekly.hql line 20, `DROP TABLE IF EXISTS failed_runs`: folded into mart.team_fails: a Derived table there, never created, written, compared or promoted
