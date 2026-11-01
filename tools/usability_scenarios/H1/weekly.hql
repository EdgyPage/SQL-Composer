SET hive.exec.dynamic.partition.mode=nonstrict;
CREATE TABLE IF NOT EXISTS mart.team_fails (team STRING, fails BIGINT)
PARTITIONED BY (dt STRING);
CREATE TABLE IF NOT EXISTS mart.job_runs_counted (job_id BIGINT, runs BIGINT)
PARTITIONED BY (dt STRING);
CREATE TABLE IF NOT EXISTS mart.job_fails_counted (job_id BIGINT, fails BIGINT)
PARTITIONED BY (dt STRING);
CREATE TEMPORARY TABLE failed_runs AS
SELECT r.job_id, r.dt FROM ops.job_runs r WHERE r.status = 'FAILED';
WITH owned AS (SELECT o.job_id, o.team FROM ops.job_owners o)
INSERT OVERWRITE TABLE mart.team_fails PARTITION (dt)
SELECT w.team AS team, COUNT(*) AS fails, f.dt
FROM failed_runs f JOIN owned w ON f.job_id = w.job_id
GROUP BY w.team, f.dt;
FROM ops.job_runs r
INSERT OVERWRITE TABLE mart.job_runs_counted PARTITION (dt)
SELECT r.job_id, COUNT(*) AS runs, r.dt GROUP BY r.job_id, r.dt
INSERT OVERWRITE TABLE mart.job_fails_counted PARTITION (dt)
SELECT r.job_id, COUNT(*) AS fails, r.dt WHERE r.status = 'FAILED' GROUP BY r.job_id, r.dt;
DROP TABLE IF EXISTS failed_runs;
