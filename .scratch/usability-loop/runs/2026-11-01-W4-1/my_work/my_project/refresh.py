from sqlglot_composer import project

print(project.refresh_reference_sheet(["ops.jobs", "ops.run_alerts"]))
print(project.check())
print(project.do_next())
