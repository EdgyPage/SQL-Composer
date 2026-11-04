SET hive.exec.dynamic.partition.mode=nonstrict;
CREATE TABLE IF NOT EXISTS mart.daily_fails (team STRING, fails BIGINT)
PARTITIONED BY (dt STRING);
INSERT OVERWRITE TABLE mart.daily_fails PARTITION (dt)
SELECT o.team AS team, COUNT(*) AS fails, r.dt
FROM ops.job_runs r JOIN ops.job_owners o ON r.job_id = o.job_id
WHERE r.status = 'FAILED' AND r.dt = <PARM="RUN_DAY"/> AND o.team <> '<PARM="SKIP_TEAM"/>'
GROUP BY o.team, r.dt;
