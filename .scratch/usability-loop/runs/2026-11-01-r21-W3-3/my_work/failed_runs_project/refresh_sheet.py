from sqlglot_composer import project
print(project.refresh_reference_sheet(["ops.job_runs", "mart_dev.failed_runs"]))
