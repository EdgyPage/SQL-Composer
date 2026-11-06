# Batch run_log

1 script, kept as given in scripts/: run_log.hql. Each table they write is a Saved table in the Dev Database, mart_dev; one they only create has its Table reference alone.

## Tables

- mart.run_log: mart_dev.run_log, tables/mart_dev__run_log/, its checklist tables/mart_dev__run_log/conversion/checklist.md

## Each statement, in the order they run

1. run_log.hql line 1, `SET hive.exec.dynamic.partition.mode=nonstrict`: the Session settings of the writes after it in its script
2. run_log.hql line 2, `CREATE TABLE IF NOT EXISTS mart.run_log (run_id BIGINT, job_id BIGINT) PARTIT...`: the columns, types and Partitions of mart_dev.run_log's Table reference
3. run_log.hql line 4, `INSERT INTO TABLE mart.run_log PARTITION (dt) SELECT r.run_id, r.job_id, r.dt...`: mart_dev.run_log, written by its notebook
