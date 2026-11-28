SET hive.exec.dynamic.partition.mode=nonstrict;
CREATE TABLE IF NOT EXISTS mart.daily_events (job_id BIGINT, events BIGINT)
PARTITIONED BY (dt STRING);
INSERT INTO TABLE mart.daily_events PARTITION (dt)
SELECT e.job_id, COUNT(*) AS events, e.dt
FROM ops.job_events e
WHERE e.dt = date_sub('2026-09-21', 1)
GROUP BY e.job_id, e.dt;
SET hive.exec.dynamic.partition.mode=nonstrict;
CREATE TABLE IF NOT EXISTS mart.daily_events (job_id BIGINT, events BIGINT)
PARTITIONED BY (dt STRING);
INSERT INTO TABLE mart.daily_events PARTITION (dt)
SELECT e.job_id, COUNT(*) AS events, e.dt
FROM ops.job_events e
WHERE e.dt = date_sub('2026-09-22', 1)
GROUP BY e.job_id, e.dt;
SET hive.exec.dynamic.partition.mode=nonstrict;
CREATE TABLE IF NOT EXISTS mart.daily_events (job_id BIGINT, events BIGINT)
PARTITIONED BY (dt STRING);
INSERT INTO TABLE mart.daily_events PARTITION (dt)
SELECT e.job_id, COUNT(*) AS events, e.dt
FROM ops.job_events e
WHERE e.dt = date_sub('2026-09-23', 1)
GROUP BY e.job_id, e.dt;
SET hive.exec.dynamic.partition.mode=nonstrict;
CREATE TABLE IF NOT EXISTS mart.daily_events (job_id BIGINT, events BIGINT)
PARTITIONED BY (dt STRING);
INSERT INTO TABLE mart.daily_events PARTITION (dt)
SELECT e.job_id, COUNT(*) AS events, e.dt
FROM ops.job_events e
WHERE e.dt = date_sub('2026-09-24', 1)
GROUP BY e.job_id, e.dt;
SET hive.exec.dynamic.partition.mode=nonstrict;
CREATE TABLE IF NOT EXISTS mart.daily_events (job_id BIGINT, events BIGINT)
PARTITIONED BY (dt STRING);
INSERT INTO TABLE mart.daily_events PARTITION (dt)
SELECT e.job_id, COUNT(*) AS events, e.dt
FROM ops.job_events e
WHERE e.dt = date_sub('2026-09-25', 1)
GROUP BY e.job_id, e.dt;
