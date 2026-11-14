SET hive.exec.dynamic.partition.mode=nonstrict;
CREATE TABLE IF NOT EXISTS mart.period_runs (team STRING, runs BIGINT)
PARTITIONED BY (dt STRING);
INSERT OVERWRITE TABLE mart.period_runs PARTITION (dt)
SELECT o.team AS team, COUNT(*) AS runs, r.dt
FROM ops.job_runs r JOIN ops.job_owners o ON r.job_id = o.job_id
WHERE r.dt BETWEEN date_sub('2026-09-24', 1) AND '2026-09-24'
GROUP BY o.team, r.dt;
