from sqlglot_composer import project, show_hive

table = project.load("mart_dev.failed_runs")
show_hive([table.create(), table.write()])
