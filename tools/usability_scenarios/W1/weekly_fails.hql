SET hive.exec.dynamic.partition.mode=nonstrict;
CREATE TABLE IF NOT EXISTS mart.team_fails (team STRING, fails BIGINT)
PARTITIONED BY (dt STRING);
WITH f AS (SELECT r.job_id, r.dt FROM ops.job_runs r WHERE r.status = 'FAILED')
INSERT OVERWRITE TABLE mart.team_fails PARTITION (dt)
SELECT o.team AS team, COUNT(*) AS fails, f.dt
FROM f JOIN ops.job_owners o ON f.job_id = o.job_id
GROUP BY o.team, f.dt;
