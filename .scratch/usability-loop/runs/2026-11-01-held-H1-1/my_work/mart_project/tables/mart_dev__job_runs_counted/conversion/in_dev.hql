SET hive.exec.dynamic.partition.mode=nonstrict;
INSERT OVERWRITE TABLE mart_dev.job_runs_counted PARTITION(dt) SELECT r.job_id, COUNT(*) AS runs, r.dt FROM ops.job_runs AS r GROUP BY r.job_id, r.dt