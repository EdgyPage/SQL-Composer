SET hive.exec.dynamic.partition.mode=nonstrict;
CREATE TABLE IF NOT EXISTS mart.run_log (run_id BIGINT, job_id BIGINT)
PARTITIONED BY (dt STRING);
INSERT INTO TABLE mart.run_log PARTITION (dt)
SELECT r.run_id, r.job_id, r.dt FROM ops.job_runs r
WHERE r.dt BETWEEN date_sub('2026-09-24', 1) AND '2026-09-24'
  AND r.run_id NOT IN (SELECT l.run_id FROM mart.run_log l);
