CREATE EXTERNAL TABLE IF NOT EXISTS mart.job_day_costs (
  job_id BIGINT,
  cost_cents BIGINT,
  PRIMARY KEY (job_id, dt) DISABLE NOVALIDATE
)
PARTITIONED BY (dt STRING)
STORED AS ORC
LOCATION '/data/your_team/mart.db/job_day_costs';
CREATE EXTERNAL TABLE IF NOT EXISTS mart.job_day_facts (
  job_id BIGINT,
  team STRING,
  events BIGINT,
  runs BIGINT,
  minutes BIGINT,
  PRIMARY KEY (job_id, dt) DISABLE NOVALIDATE
)
PARTITIONED BY (dt STRING)
STORED AS ORC
LOCATION '/data/your_team/mart.db/job_day_facts';
CREATE EXTERNAL TABLE IF NOT EXISTS mart.team_days (
  team STRING,
  events BIGINT,
  runs BIGINT,
  minutes BIGINT,
  cost_cents BIGINT,
  PRIMARY KEY (team, dt) DISABLE NOVALIDATE
)
PARTITIONED BY (dt STRING)
STORED AS ORC
LOCATION '/data/your_team/mart.db/team_days';
