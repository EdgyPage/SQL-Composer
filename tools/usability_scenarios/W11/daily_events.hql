SET hive.exec.dynamic.partition.mode=nonstrict;
CREATE TABLE IF NOT EXISTS mart.daily_events (job_id BIGINT, events BIGINT)
PARTITIONED BY (dt STRING);
INSERT INTO TABLE mart.daily_events PARTITION (dt)
SELECT e.job_id, COUNT(*) AS events, e.dt
FROM ops.job_events e
WHERE e.dt = date_sub(current_date, 1)
GROUP BY e.job_id, e.dt;
