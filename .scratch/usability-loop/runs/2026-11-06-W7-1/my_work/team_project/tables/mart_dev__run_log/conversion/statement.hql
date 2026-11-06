INSERT INTO TABLE mart.run_log PARTITION (dt)
SELECT r.run_id, r.job_id, r.dt FROM ops.job_runs r
WHERE r.dt BETWEEN date_sub(<PARM="PERIOD_END"/>, 1) AND <PARM="PERIOD_END"/>
  AND r.run_id NOT IN (SELECT l.run_id FROM mart.run_log l);
