from sqlglot_composer import project
from references import ops
print(project.check())
print(ops.jobs.job_id)
print(ops.run_alerts.alert_id)
print(project.do_next())
