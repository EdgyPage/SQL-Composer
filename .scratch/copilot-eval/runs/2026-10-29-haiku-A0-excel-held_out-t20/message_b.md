You are standing in for Microsoft Copilot in a web chat. Use no tools: answer from what is written here and what you already know.

Each task below is a separate request the user sends next. Answer each as you would in that chat: reply with its `## X..` heading, then your answer, with SQL in ```sql blocks and any Python in ```python blocks.

## X39

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x39.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "job_runs"
  Excel Table "job_runs", A1:F10
    Headers: run_id | job_id | status | duration_mins | avg_retry_secs | dt
    Row 2: 95 | 1 | SUCCESS | 12 | 2 | 2026-09-23
    Row 3: 96 | 2 | SUCCESS | 18 | 0 | 2026-09-23
    Row 4: 97 | 3 | FAILED | 30 | 8 | 2026-09-23
    Row 5: 98 | 2 |  | 15 |  | 2026-09-23
    Row 6: 99 | 1 | TEST | 5 | 0 | 2026-09-23
    Row 7: 101 | 1 | SUCCESS | 10 | 1 | 2026-09-24
    Row 8: 102 | 2 | FAILED | 20 | 6 | 2026-09-24
    Row 9: 103 | 3 | SUCCESS | 30 | 0 | 2026-09-24
    Row 10: 104 | 1 | SUCCESS | 40 | 3 | 2026-09-24
Sheet "jobs"
  Excel Table "jobs", A1:D5
    Headers: job_id | job_name | team | region
    Row 2: 1 | nightly_load | data | LON
    Row 3: 2 | invoice_sync | finance | PAR
    Row 4: 3 | report_build | finance | NYC
    Row 5: 4 | cache_warm | web | LON
Sheet "ok_runs"
  Excel Table "ok_runs", A1:F6, loaded by Power Query "ok_runs"
    Headers: run_id | job_id | duration_mins | job_name | share | noise
    Row 2: 95 | 1 | 12 | =_xlfn.XLOOKUP(ok_runs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =ok_runs[[#This Row],[duration_mins]]/SUMIFS(ok_runs[duration_mins],ok_runs[job_id],ok_runs[[#This Row],[job_id]]) | =RAND()
    Row 3: 96 | 2 | 18 | =_xlfn.XLOOKUP(ok_runs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =ok_runs[[#This Row],[duration_mins]]/SUMIFS(ok_runs[duration_mins],ok_runs[job_id],ok_runs[[#This Row],[job_id]]) | =RAND()
    Row 4: 101 | 1 | 10 | =_xlfn.XLOOKUP(ok_runs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =ok_runs[[#This Row],[duration_mins]]/SUMIFS(ok_runs[duration_mins],ok_runs[job_id],ok_runs[[#This Row],[job_id]]) | =RAND()
    Row 5: 103 | 3 | 30 | =_xlfn.XLOOKUP(ok_runs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =ok_runs[[#This Row],[duration_mins]]/SUMIFS(ok_runs[duration_mins],ok_runs[job_id],ok_runs[[#This Row],[job_id]]) | =RAND()
    Row 6: 104 | 1 | 40 | =_xlfn.XLOOKUP(ok_runs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =ok_runs[[#This Row],[duration_mins]]/SUMIFS(ok_runs[duration_mins],ok_runs[job_id],ok_runs[[#This Row],[job_id]]) | =RAND()
Power Query "ok_runs" (loads into Excel Table "ok_runs"):
    let
        Source = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],
        Succeeded = Table.SelectRows(Source, each [status] = "SUCCESS"),
        Kept = Table.SelectColumns(Succeeded, {"run_id", "job_id", "duration_mins"})
    in
        Kept
>>>

## X40

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x40.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2: rate | 2
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "Runs"
  Excel Table "Runs", A1:E10
    Headers: Run | Job | Mins | Team | Cost
    Row 2: 95 | 1 | 12 | =_xlfn.XLOOKUP(Runs[[#This Row],[Job]],jobs[job_id],jobs[team]) | =Runs[[#This Row],[Mins]]*_xlfn.XLOOKUP("rate",Parameters[name],Parameters[value])
    Row 3: 96 | 2 | 18 | =_xlfn.XLOOKUP(Runs[[#This Row],[Job]],jobs[job_id],jobs[team]) | =Runs[[#This Row],[Mins]]*_xlfn.XLOOKUP("rate",Parameters[name],Parameters[value])
    Row 4: 97 | 3 | 30 | =_xlfn.XLOOKUP(Runs[[#This Row],[Job]],jobs[job_id],jobs[team]) | =Runs[[#This Row],[Mins]]*_xlfn.XLOOKUP("rate",Parameters[name],Parameters[value])
    Row 5: 98 | 2 | 15 | =_xlfn.XLOOKUP(Runs[[#This Row],[Job]],jobs[job_id],jobs[team]) | =Runs[[#This Row],[Mins]]*_xlfn.XLOOKUP("rate",Parameters[name],Parameters[value])
    Row 6: 99 | 1 | 5 | =_xlfn.XLOOKUP(Runs[[#This Row],[Job]],jobs[job_id],jobs[team]) | =Runs[[#This Row],[Mins]]*_xlfn.XLOOKUP("rate",Parameters[name],Parameters[value])
    Row 7: 101 | 1 | 10 | =_xlfn.XLOOKUP(Runs[[#This Row],[Job]],jobs[job_id],jobs[team]) | =Runs[[#This Row],[Mins]]*_xlfn.XLOOKUP("rate",Parameters[name],Parameters[value])
    Row 8: 102 | 2 | 20 | =_xlfn.XLOOKUP(Runs[[#This Row],[Job]],jobs[job_id],jobs[team]) | =Runs[[#This Row],[Mins]]*_xlfn.XLOOKUP("rate",Parameters[name],Parameters[value])
    Row 9: 103 | 3 | 30 | =_xlfn.XLOOKUP(Runs[[#This Row],[Job]],jobs[job_id],jobs[team]) | =Runs[[#This Row],[Mins]]*_xlfn.XLOOKUP("rate",Parameters[name],Parameters[value])
    Row 10: 104 | 1 | 40 | =_xlfn.XLOOKUP(Runs[[#This Row],[Job]],jobs[job_id],jobs[team]) | =Runs[[#This Row],[Mins]]*_xlfn.XLOOKUP("rate",Parameters[name],Parameters[value])
Sheet "jobs"
  Excel Table "jobs", A1:D5
    Headers: job_id | job_name | team | region
    Row 2: 1 | nightly_load | data | LON
    Row 3: 2 | invoice_sync | finance | PAR
    Row 4: 3 | report_build | finance | NYC
    Row 5: 4 | cache_warm | web | LON
Sheet "Teams"
  Excel Table "Teams", A1:B3
    Headers: Team | Total Cost
    Row 2: data | =SUMIFS(Runs[Cost],Runs[Team],Teams[[#This Row],[Team]])
    Row 3: finance | =SUMIFS(Runs[Cost],Runs[Team],Teams[[#This Row],[Team]])
Sheet "run_alerts"
  Excel Table "run_alerts", A1:E10
    Headers: alert_id | run_id | severity | dt | Run Mins
    Row 2: 1 | 97 | high | 2026-09-23 | =_xlfn.XLOOKUP(run_alerts[[#This Row],[run_id]],Runs[Run],Runs[Mins])
    Row 3: 2 | 97 | low | 2026-09-23 | =_xlfn.XLOOKUP(run_alerts[[#This Row],[run_id]],Runs[Run],Runs[Mins])
    Row 4: 3 | 101 | low | 2026-09-24 | =_xlfn.XLOOKUP(run_alerts[[#This Row],[run_id]],Runs[Run],Runs[Mins])
    Row 5: 4 | 101 | low | 2026-09-24 | =_xlfn.XLOOKUP(run_alerts[[#This Row],[run_id]],Runs[Run],Runs[Mins])
    Row 6: 5 | 101 | high | 2026-09-24 | =_xlfn.XLOOKUP(run_alerts[[#This Row],[run_id]],Runs[Run],Runs[Mins])
    Row 7: 6 | 102 | high | 2026-09-24 | =_xlfn.XLOOKUP(run_alerts[[#This Row],[run_id]],Runs[Run],Runs[Mins])
    Row 8: 7 | 103 | low | 2026-09-24 | =_xlfn.XLOOKUP(run_alerts[[#This Row],[run_id]],Runs[Run],Runs[Mins])
    Row 9: 8 | 103 | low | 2026-09-24 | =_xlfn.XLOOKUP(run_alerts[[#This Row],[run_id]],Runs[Run],Runs[Mins])
    Row 10: 9 | 104 | low | 2026-09-24 | =_xlfn.XLOOKUP(run_alerts[[#This Row],[run_id]],Runs[Run],Runs[Mins])
Also in the workbook: a PivotTable on sheet "Pivot", from Table Runs: rows Team, values Sum of Cost
>>>

## X46

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x46.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "jobs"
  Excel Table "jobs", A1:F5
    Headers: job_id | job_name | team | shortest | runs | busiest
    Row 2: 1 | nightly_load | data | =_xlfn.MINIFS(job_runs[duration_mins],job_runs[job_id],jobs[[#This Row],[job_id]]) | =COUNTIF(job_runs[job_id],jobs[[#This Row],[job_id]]) | =_xlfn.RANK.EQ(jobs[[#This Row],[runs]],jobs[runs])
    Row 3: 2 | invoice_sync | finance | =_xlfn.MINIFS(job_runs[duration_mins],job_runs[job_id],jobs[[#This Row],[job_id]]) | =COUNTIF(job_runs[job_id],jobs[[#This Row],[job_id]]) | =_xlfn.RANK.EQ(jobs[[#This Row],[runs]],jobs[runs])
    Row 4: 3 | report_build | finance | =_xlfn.MINIFS(job_runs[duration_mins],job_runs[job_id],jobs[[#This Row],[job_id]]) | =COUNTIF(job_runs[job_id],jobs[[#This Row],[job_id]]) | =_xlfn.RANK.EQ(jobs[[#This Row],[runs]],jobs[runs])
    Row 5: 4 | cache_warm | web | =_xlfn.MINIFS(job_runs[duration_mins],job_runs[job_id],jobs[[#This Row],[job_id]]) | =COUNTIF(job_runs[job_id],jobs[[#This Row],[job_id]]) | =_xlfn.RANK.EQ(jobs[[#This Row],[runs]],jobs[runs])
Sheet "job_runs"
  Excel Table "job_runs", A1:F10
    Headers: run_id | job_id | status | duration_mins | avg_retry_secs | dt
    Row 2: 95 | 1 | SUCCESS | 12 | 2 | 2026-09-23
    Row 3: 96 | 2 | SUCCESS | 18 | 0 | 2026-09-23
    Row 4: 97 | 3 | FAILED | 30 | 8 | 2026-09-23
    Row 5: 98 | 2 |  | 15 |  | 2026-09-23
    Row 6: 99 | 1 | TEST | 5 | 0 | 2026-09-23
    Row 7: 101 | 1 | SUCCESS | 10 | 1 | 2026-09-24
    Row 8: 102 | 2 | FAILED | 20 | 6 | 2026-09-24
    Row 9: 103 | 3 | SUCCESS | 30 | 0 | 2026-09-24
    Row 10: 104 | 1 | SUCCESS | 40 | 3 | 2026-09-24
>>>

## X47

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x47.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "region_budgets"
  Excel Table "region_budgets", A1:F5
    Headers: job_id | budget_cents | region | cheapest_first | region_total | region_avg
    Row 2: 1 | 150 | eu | =RANK.EQ([@budget_cents],region_budgets[budget_cents],1) | =SUMIF(region_budgets[region],[@region],region_budgets[budget_cents]) | =AVERAGEIF(region_budgets[region],[@region],region_budgets[budget_cents])
    Row 3: 2 | 200 | eu | =RANK.EQ([@budget_cents],region_budgets[budget_cents],1) | =SUMIF(region_budgets[region],[@region],region_budgets[budget_cents]) | =AVERAGEIF(region_budgets[region],[@region],region_budgets[budget_cents])
    Row 4: 3 | 350 | us | =RANK.EQ([@budget_cents],region_budgets[budget_cents],1) | =SUMIF(region_budgets[region],[@region],region_budgets[budget_cents]) | =AVERAGEIF(region_budgets[region],[@region],region_budgets[budget_cents])
    Row 5: 4 | 50 | eu | =RANK.EQ([@budget_cents],region_budgets[budget_cents],1) | =SUMIF(region_budgets[region],[@region],region_budgets[budget_cents]) | =AVERAGEIF(region_budgets[region],[@region],region_budgets[budget_cents])
>>>

## X48

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x48.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "job_runs"
  Excel Table "job_runs", A1:F10
    Headers: run_id | job_id | status | duration_mins | avg_retry_secs | dt
    Row 2: 95 | 1 | SUCCESS | 12 | 2 | 2026-09-23
    Row 3: 96 | 2 | SUCCESS | 18 | 0 | 2026-09-23
    Row 4: 97 | 3 | FAILED | 30 | 8 | 2026-09-23
    Row 5: 98 | 2 |  | 15 |  | 2026-09-23
    Row 6: 99 | 1 | TEST | 5 | 0 | 2026-09-23
    Row 7: 101 | 1 | SUCCESS | 10 | 1 | 2026-09-24
    Row 8: 102 | 2 | FAILED | 20 | 6 | 2026-09-24
    Row 9: 103 | 3 | SUCCESS | 30 | 0 | 2026-09-24
    Row 10: 104 | 1 | SUCCESS | 40 | 3 | 2026-09-24
Sheet "jobs"
  Excel Table "jobs", A1:D5
    Headers: job_id | job_name | team | region
    Row 2: 1 | nightly_load | data | LON
    Row 3: 2 | invoice_sync | finance | PAR
    Row 4: 3 | report_build | finance | NYC
    Row 5: 4 | cache_warm | web | LON
Sheet "run_alerts"
  Excel Table "run_alerts", A1:D10
    Headers: alert_id | run_id | severity | dt
    Row 2: 1 | 97 | high | 2026-09-23
    Row 3: 2 | 97 | low | 2026-09-23
    Row 4: 3 | 101 | low | 2026-09-24
    Row 5: 4 | 101 | low | 2026-09-24
    Row 6: 5 | 101 | high | 2026-09-24
    Row 7: 6 | 102 | high | 2026-09-24
    Row 8: 7 | 103 | low | 2026-09-24
    Row 9: 8 | 103 | low | 2026-09-24
    Row 10: 9 | 104 | low | 2026-09-24
Sheet "quiet_runs"
  Excel Table "quiet_runs", A1:C5, loaded by Power Query "quiet_runs"
    Headers: run_id | job_id | status
    Row 2: 95 | 1 | SUCCESS
    Row 3: 96 | 2 | SUCCESS
    Row 4: 98 | 2 | 
    Row 5: 99 | 1 | TEST
Sheet "slow_regions"
  Excel Table "slow_regions", A1:C2, loaded by Power Query "slow_regions"
    Headers: region | avg_mins | fastest
    Row 2: NYC | 30 | 30
Power Query "quiet_runs" (loads into Excel Table "quiet_runs"):
    let
        Runs = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],
        Alerts = Excel.CurrentWorkbook(){[Name="run_alerts"]}[Content],
        Quiet = Table.NestedJoin(Runs, {"run_id"}, Alerts, {"run_id"}, "a", JoinKind.LeftAnti),
        Kept = Table.SelectColumns(Quiet, {"run_id", "job_id", "status"})
    in
        Kept
Power Query "slow_regions" (loads into Excel Table "slow_regions"):
    let
        Runs = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],
        Jobs = Excel.CurrentWorkbook(){[Name="jobs"]}[Content],
        Joined = Table.NestedJoin(Runs, {"job_id"}, Jobs, {"job_id"}, "j", JoinKind.Inner),
        Expanded = Table.ExpandTableColumn(Joined, "j", {"region"}),
        Grouped = Table.Group(Expanded, {"region"}, {
            {"avg_mins", each List.Average([duration_mins]), type number},
            {"fastest", each List.Min([duration_mins]), type number}}),
        Slow = Table.SelectRows(Grouped, each [avg_mins] >= 20)
    in
        Slow
>>>

## X49

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x49.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "job_runs"
  Excel Table "job_runs", A1:F10
    Headers: run_id | job_id | status | duration_mins | avg_retry_secs | dt
    Row 2: 95 | 1 | SUCCESS | 12 | 2 | 2026-09-23
    Row 3: 96 | 2 | SUCCESS | 18 | 0 | 2026-09-23
    Row 4: 97 | 3 | FAILED | 30 | 8 | 2026-09-23
    Row 5: 98 | 2 |  | 15 |  | 2026-09-23
    Row 6: 99 | 1 | TEST | 5 | 0 | 2026-09-23
    Row 7: 101 | 1 | SUCCESS | 10 | 1 | 2026-09-24
    Row 8: 102 | 2 | FAILED | 20 | 6 | 2026-09-24
    Row 9: 103 | 3 | SUCCESS | 30 | 0 | 2026-09-24
    Row 10: 104 | 1 | SUCCESS | 40 | 3 | 2026-09-24
Sheet "jobs"
  Excel Table "jobs", A1:D5
    Headers: job_id | job_name | team | region
    Row 2: 1 | nightly_load | data | LON
    Row 3: 2 | invoice_sync | finance | PAR
    Row 4: 3 | report_build | finance | NYC
    Row 5: 4 | cache_warm | web | LON
Sheet "run_alerts"
  Excel Table "run_alerts", A1:D10
    Headers: alert_id | run_id | severity | dt
    Row 2: 1 | 97 | high | 2026-09-23
    Row 3: 2 | 97 | low | 2026-09-23
    Row 4: 3 | 101 | low | 2026-09-24
    Row 5: 4 | 101 | low | 2026-09-24
    Row 6: 5 | 101 | high | 2026-09-24
    Row 7: 6 | 102 | high | 2026-09-24
    Row 8: 7 | 103 | low | 2026-09-24
    Row 9: 8 | 103 | low | 2026-09-24
    Row 10: 9 | 104 | low | 2026-09-24
Sheet "scheduler_runs"
  Excel Table "scheduler_runs", A1:C10
    Headers: run_id | job_id | dt
    Row 2: 95 | 1 | 2026-09-23
    Row 3: 96 | 2 | 2026-09-23
    Row 4: 97 | 3 | 2026-09-23
    Row 5: 98 | 2 | 2026-09-23
    Row 6: 100 | 3 | 2026-09-23
    Row 7: 101 | 1 | 2026-09-24
    Row 8: 102 | 2 | 2026-09-24
    Row 9: 103 | 3 | 2026-09-24
    Row 10: 104 | 1 | 2026-09-24
Sheet "job_owners"
  Excel Table "job_owners", A1:D57
    Headers: job_id | team | owner | dt
    Row 2: 1 | data | ana | 2026-09-11
    Row 3: 2 | finance | ben | 2026-09-11
    Row 4: 3 | data | ana | 2026-09-11
    Row 5: 4 | web |  | 2026-09-11
    Row 6: 1 | data | ana | 2026-09-12
    Row 7: 2 | finance | ben | 2026-09-12
    Row 8: 3 | data | ana | 2026-09-12
    Row 9: 4 | web |  | 2026-09-12
    Row 10: 1 | data | ana | 2026-09-13
    Row 11: 2 | finance | ben | 2026-09-13
    Row 12: 3 | data | ana | 2026-09-13
    Row 13: 4 | web |  | 2026-09-13
    Row 14: 1 | data | ana | 2026-09-14
    Row 15: 2 | finance | ben | 2026-09-14
    Row 16: 3 | data | ana | 2026-09-14
    Row 17: 4 | web |  | 2026-09-14
    Row 18: 1 | data | ana | 2026-09-15
    Row 19: 2 | finance | ben | 2026-09-15
    Row 20: 3 | data | ana | 2026-09-15
    Row 21: 4 | web |  | 2026-09-15
    Row 22: 1 | data | ana | 2026-09-16
    Row 23: 2 | finance | ben | 2026-09-16
    Row 24: 3 | data | ana | 2026-09-16
    Row 25: 4 | web |  | 2026-09-16
    Row 26: 1 | data | ana | 2026-09-17
    Row 27: 2 | finance | ben | 2026-09-17
    Row 28: 3 | data | ana | 2026-09-17
    Row 29: 4 | web |  | 2026-09-17
    Row 30: 1 | data | ana | 2026-09-18
    Row 31: 2 | finance | ben | 2026-09-18
    Row 32: 3 | finance | chloe | 2026-09-18
    Row 33: 4 | web |  | 2026-09-18
    Row 34: 1 | data | ana | 2026-09-19
    Row 35: 2 | finance | ben | 2026-09-19
    Row 36: 3 | finance | chloe | 2026-09-19
    Row 37: 4 | web |  | 2026-09-19
    Row 38: 1 | data | ana | 2026-09-20
    Row 39: 2 | finance | ben | 2026-09-20
    Row 40: 3 | finance | chloe | 2026-09-20
    Row 41: 4 | web |  | 2026-09-20
    Row 42: 1 | data | ana | 2026-09-21
    Row 43: 2 | finance | ben | 2026-09-21
    Row 44: 3 | finance | chloe | 2026-09-21
    Row 45: 4 | web |  | 2026-09-21
    Row 46: 1 | data | ana | 2026-09-22
    Row 47: 2 | finance | ben | 2026-09-22
    Row 48: 3 | finance | chloe | 2026-09-22
    Row 49: 4 | web |  | 2026-09-22
    Row 50: 1 | data | ana | 2026-09-23
    Row 51: 2 | finance | ben | 2026-09-23
    Row 52: 3 | finance | chloe | 2026-09-23
    Row 53: 4 | web |  | 2026-09-23
    Row 54: 1 | data | ana | 2026-09-24
    Row 55: 2 | finance | ben | 2026-09-24
    Row 56: 3 | finance | chloe | 2026-09-24
    Row 57: 4 | web |  | 2026-09-24
Sheet "alert_status"
  Excel Table "alert_status", A1:C14, loaded by Power Query "alert_status"
    Headers: alert_id | severity | status
    Row 2:  |  | SUCCESS
    Row 3:  |  | SUCCESS
    Row 4: 1 | high | FAILED
    Row 5: 2 | low | FAILED
    Row 6:  |  | 
    Row 7:  |  | TEST
    Row 8: 3 | low | SUCCESS
    Row 9: 4 | low | SUCCESS
    Row 10: 5 | high | SUCCESS
    Row 11: 6 | high | FAILED
    Row 12: 7 | low | SUCCESS
    Row 13: 8 | low | SUCCESS
    Row 14: 9 | low | SUCCESS
Sheet "run_check"
  Excel Table "run_check", A1:C11, loaded by Power Query "run_check"
    Headers: run_id | status | scheduled_run
    Row 2: 99 | TEST | 
    Row 3: 95 | SUCCESS | 95
    Row 4: 96 | SUCCESS | 96
    Row 5: 97 | FAILED | 97
    Row 6: 98 |  | 98
    Row 7:  |  | 100
    Row 8: 101 | SUCCESS | 101
    Row 9: 102 | FAILED | 102
    Row 10: 103 | SUCCESS | 103
    Row 11: 104 | SUCCESS | 104
Sheet "teams"
  Excel Table "teams", A1:A4, loaded by Power Query "teams"
    Headers: team
    Row 2: data
    Row 3: finance
    Row 4: web
Power Query "alert_status" (loads into Excel Table "alert_status"):
    let
        Alerts = Excel.CurrentWorkbook(){[Name="run_alerts"]}[Content],
        Runs = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],
        Joined = Table.NestedJoin(Alerts, {"run_id"}, Runs, {"run_id"}, "r", JoinKind.RightOuter),
        Expanded = Table.ExpandTableColumn(Joined, "r", {"status"}),
        Kept = Table.SelectColumns(Expanded, {"alert_id", "severity", "status"})
    in
        Kept
Power Query "run_check" (loads into Excel Table "run_check"):
    let
        Runs = Table.SelectColumns(Excel.CurrentWorkbook(){[Name="job_runs"]}[Content], {"run_id", "status"}),
        Scheduled = Excel.CurrentWorkbook(){[Name="scheduler_runs"]}[Content],
        Joined = Table.NestedJoin(Runs, {"run_id"}, Scheduled, {"run_id"}, "s", JoinKind.FullOuter),
        Expanded = Table.ExpandTableColumn(Joined, "s", {"run_id"}, {"scheduled_run"})
    in
        Expanded
Power Query "teams" (loads into Excel Table "teams"):
    let
        FromJobs = Table.SelectColumns(Excel.CurrentWorkbook(){[Name="jobs"]}[Content], {"team"}),
        FromOwners = Table.SelectColumns(Excel.CurrentWorkbook(){[Name="job_owners"]}[Content], {"team"}),
        Unique = Table.Distinct(Table.Combine({FromJobs, FromOwners}))
    in
        Unique
>>>

## X50

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x50.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "job_owners"
  Excel Table "job_owners", A1:D57
    Headers: job_id | team | owner | dt
    Row 2: 1 | data | ana | 2026-09-11
    Row 3: 2 | finance | ben | 2026-09-11
    Row 4: 3 | data | ana | 2026-09-11
    Row 5: 4 | web |  | 2026-09-11
    Row 6: 1 | data | ana | 2026-09-12
    Row 7: 2 | finance | ben | 2026-09-12
    Row 8: 3 | data | ana | 2026-09-12
    Row 9: 4 | web |  | 2026-09-12
    Row 10: 1 | data | ana | 2026-09-13
    Row 11: 2 | finance | ben | 2026-09-13
    Row 12: 3 | data | ana | 2026-09-13
    Row 13: 4 | web |  | 2026-09-13
    Row 14: 1 | data | ana | 2026-09-14
    Row 15: 2 | finance | ben | 2026-09-14
    Row 16: 3 | data | ana | 2026-09-14
    Row 17: 4 | web |  | 2026-09-14
    Row 18: 1 | data | ana | 2026-09-15
    Row 19: 2 | finance | ben | 2026-09-15
    Row 20: 3 | data | ana | 2026-09-15
    Row 21: 4 | web |  | 2026-09-15
    Row 22: 1 | data | ana | 2026-09-16
    Row 23: 2 | finance | ben | 2026-09-16
    Row 24: 3 | data | ana | 2026-09-16
    Row 25: 4 | web |  | 2026-09-16
    Row 26: 1 | data | ana | 2026-09-17
    Row 27: 2 | finance | ben | 2026-09-17
    Row 28: 3 | data | ana | 2026-09-17
    Row 29: 4 | web |  | 2026-09-17
    Row 30: 1 | data | ana | 2026-09-18
    Row 31: 2 | finance | ben | 2026-09-18
    Row 32: 3 | finance | chloe | 2026-09-18
    Row 33: 4 | web |  | 2026-09-18
    Row 34: 1 | data | ana | 2026-09-19
    Row 35: 2 | finance | ben | 2026-09-19
    Row 36: 3 | finance | chloe | 2026-09-19
    Row 37: 4 | web |  | 2026-09-19
    Row 38: 1 | data | ana | 2026-09-20
    Row 39: 2 | finance | ben | 2026-09-20
    Row 40: 3 | finance | chloe | 2026-09-20
    Row 41: 4 | web |  | 2026-09-20
    Row 42: 1 | data | ana | 2026-09-21
    Row 43: 2 | finance | ben | 2026-09-21
    Row 44: 3 | finance | chloe | 2026-09-21
    Row 45: 4 | web |  | 2026-09-21
    Row 46: 1 | data | ana | 2026-09-22
    Row 47: 2 | finance | ben | 2026-09-22
    Row 48: 3 | finance | chloe | 2026-09-22
    Row 49: 4 | web |  | 2026-09-22
    Row 50: 1 | data | ana | 2026-09-23
    Row 51: 2 | finance | ben | 2026-09-23
    Row 52: 3 | finance | chloe | 2026-09-23
    Row 53: 4 | web |  | 2026-09-23
    Row 54: 1 | data | ana | 2026-09-24
    Row 55: 2 | finance | ben | 2026-09-24
    Row 56: 3 | finance | chloe | 2026-09-24
    Row 57: 4 | web |  | 2026-09-24
Sheet "jobs"
  Excel Table "jobs", A1:D5
    Headers: job_id | job_name | team | region
    Row 2: 1 | nightly_load | data | LON
    Row 3: 2 | invoice_sync | finance | PAR
    Row 4: 3 | report_build | finance | NYC
    Row 5: 4 | cache_warm | web | LON
Sheet "owners"
  Excel Table "owners", A1:D6, loaded by Power Query "owners"
    Headers: job_id | owner | job_name | newest_first
    Row 2: 1 | ana | =_xlfn.XLOOKUP(owners[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.RANK.EQ(owners[[#This Row],[job_id]],owners[job_id])
    Row 3: 2 | ben | =_xlfn.XLOOKUP(owners[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.RANK.EQ(owners[[#This Row],[job_id]],owners[job_id])
    Row 4: 3 | ana | =_xlfn.XLOOKUP(owners[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.RANK.EQ(owners[[#This Row],[job_id]],owners[job_id])
    Row 5: 3 | chloe | =_xlfn.XLOOKUP(owners[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.RANK.EQ(owners[[#This Row],[job_id]],owners[job_id])
    Row 6: 4 |  | =_xlfn.XLOOKUP(owners[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.RANK.EQ(owners[[#This Row],[job_id]],owners[job_id])
Power Query "owners" (loads into Excel Table "owners"):
    let
        Source = Excel.CurrentWorkbook(){[Name="job_owners"]}[Content],
        Kept = Table.SelectColumns(Source, {"job_id", "owner"}),
        Unique = Table.Distinct(Kept)
    in
        Unique
>>>

## X59

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x59.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "jobs"
  Excel Table "jobs", A1:E5
    Headers: job_id | job_name | long_runs | failed_mins | not_test
    Row 2: 1 | nightly_load | =COUNTIFS(job_runs[job_id],jobs[[#This Row],[job_id]],job_runs[duration_mins],">=20") | =SUMIFS(job_runs[duration_mins],job_runs[job_id],jobs[[#This Row],[job_id]],job_runs[status],"f*") | =COUNTIFS(job_runs[job_id],jobs[[#This Row],[job_id]],job_runs[status],"<>TEST")
    Row 3: 2 | invoice_sync | =COUNTIFS(job_runs[job_id],jobs[[#This Row],[job_id]],job_runs[duration_mins],">=20") | =SUMIFS(job_runs[duration_mins],job_runs[job_id],jobs[[#This Row],[job_id]],job_runs[status],"f*") | =COUNTIFS(job_runs[job_id],jobs[[#This Row],[job_id]],job_runs[status],"<>TEST")
    Row 4: 3 | report_build | =COUNTIFS(job_runs[job_id],jobs[[#This Row],[job_id]],job_runs[duration_mins],">=20") | =SUMIFS(job_runs[duration_mins],job_runs[job_id],jobs[[#This Row],[job_id]],job_runs[status],"f*") | =COUNTIFS(job_runs[job_id],jobs[[#This Row],[job_id]],job_runs[status],"<>TEST")
    Row 5: 4 | cache_warm | =COUNTIFS(job_runs[job_id],jobs[[#This Row],[job_id]],job_runs[duration_mins],">=20") | =SUMIFS(job_runs[duration_mins],job_runs[job_id],jobs[[#This Row],[job_id]],job_runs[status],"f*") | =COUNTIFS(job_runs[job_id],jobs[[#This Row],[job_id]],job_runs[status],"<>TEST")
Sheet "job_runs"
  Excel Table "job_runs", A1:F10
    Headers: run_id | job_id | status | duration_mins | avg_retry_secs | dt
    Row 2: 95 | 1 | SUCCESS | 12 | 2 | 2026-09-23
    Row 3: 96 | 2 | SUCCESS | 18 | 0 | 2026-09-23
    Row 4: 97 | 3 | FAILED | 30 | 8 | 2026-09-23
    Row 5: 98 | 2 |  | 15 |  | 2026-09-23
    Row 6: 99 | 1 | TEST | 5 | 0 | 2026-09-23
    Row 7: 101 | 1 | SUCCESS | 10 | 1 | 2026-09-24
    Row 8: 102 | 2 | FAILED | 20 | 6 | 2026-09-24
    Row 9: 103 | 3 | SUCCESS | 30 | 0 | 2026-09-24
    Row 10: 104 | 1 | SUCCESS | 40 | 3 | 2026-09-24
Sheet "run_alerts"
  Excel Table "run_alerts", A1:E10
    Headers: alert_id | run_id | severity | dt | alerts_so_far
    Row 2: 1 | 97 | high | 2026-09-23 | =COUNTIFS(run_alerts[run_id],"<="&run_alerts[[#This Row],[run_id]])
    Row 3: 2 | 97 | low | 2026-09-23 | =COUNTIFS(run_alerts[run_id],"<="&run_alerts[[#This Row],[run_id]])
    Row 4: 3 | 101 | low | 2026-09-24 | =COUNTIFS(run_alerts[run_id],"<="&run_alerts[[#This Row],[run_id]])
    Row 5: 4 | 101 | low | 2026-09-24 | =COUNTIFS(run_alerts[run_id],"<="&run_alerts[[#This Row],[run_id]])
    Row 6: 5 | 101 | high | 2026-09-24 | =COUNTIFS(run_alerts[run_id],"<="&run_alerts[[#This Row],[run_id]])
    Row 7: 6 | 102 | high | 2026-09-24 | =COUNTIFS(run_alerts[run_id],"<="&run_alerts[[#This Row],[run_id]])
    Row 8: 7 | 103 | low | 2026-09-24 | =COUNTIFS(run_alerts[run_id],"<="&run_alerts[[#This Row],[run_id]])
    Row 9: 8 | 103 | low | 2026-09-24 | =COUNTIFS(run_alerts[run_id],"<="&run_alerts[[#This Row],[run_id]])
    Row 10: 9 | 104 | low | 2026-09-24 | =COUNTIFS(run_alerts[run_id],"<="&run_alerts[[#This Row],[run_id]])
>>>

## X60

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x60.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "region_budgets"
  Excel Table "region_budgets", A1:F6
    Headers: job_id | budget_cents | region | share | above_avg | rank_in_region
    Row 2: 1 | 150 | eu | =[@budget_cents]/SUM(region_budgets[budget_cents]) | =[@budget_cents]>AVERAGE(region_budgets[budget_cents]) | =COUNTIFS(region_budgets[region],[@region],region_budgets[budget_cents],"<"&[@budget_cents])+1
    Row 3: 2 | 200 | eu | =[@budget_cents]/SUM(region_budgets[budget_cents]) | =[@budget_cents]>AVERAGE(region_budgets[budget_cents]) | =COUNTIFS(region_budgets[region],[@region],region_budgets[budget_cents],"<"&[@budget_cents])+1
    Row 4: 3 | 350 | us | =[@budget_cents]/SUM(region_budgets[budget_cents]) | =[@budget_cents]>AVERAGE(region_budgets[budget_cents]) | =COUNTIFS(region_budgets[region],[@region],region_budgets[budget_cents],"<"&[@budget_cents])+1
    Row 5: 4 | 50 | eu | =[@budget_cents]/SUM(region_budgets[budget_cents]) | =[@budget_cents]>AVERAGE(region_budgets[budget_cents]) | =COUNTIFS(region_budgets[region],[@region],region_budgets[budget_cents],"<"&[@budget_cents])+1
    Total Row: =SUBTOTAL(103,region_budgets[job_id]) | =SUBTOTAL(101,region_budgets[budget_cents]) | Total |  |  | 
>>>

## X61

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x61.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "region_costs"
  Excel Table "region_costs", A1:D29
    Headers: job_id | cost_cents | region | dt
    Row 2: 1 | 120 | eu | 20260911
    Row 3: 2 | 180 | eu | 20260911
    Row 4: 3 | 300 | us | 20260911
    Row 5: 1 | 110 | eu | 20260912
    Row 6: 1 | 130 | eu | 20260913
    Row 7: 1 | 120 | eu | 20260914
    Row 8: 2 | 200 | eu | 20260914
    Row 9: 3 | 410 | us | 20260914
    Row 10: 1 | 100 | eu | 20260915
    Row 11: 2 | 170 | eu | 20260915
    Row 12: 1 | 250 | eu | 20260916
    Row 13: 2 | 190 | eu | 20260916
    Row 14: 1 | 120 | eu | 20260917
    Row 15: 2 | 160 | eu | 20260917
    Row 16: 1 | 140 | eu | 20260918
    Row 17: 2 | 220 | eu | 20260918
    Row 18: 3 | 120 | us | 20260918
    Row 19: 1 | 110 | eu | 20260919
    Row 20: 1 | 120 | eu | 20260920
    Row 21: 1 | 130 | eu | 20260921
    Row 22: 2 | 210 | eu | 20260921
    Row 23: 3 | 330 | us | 20260921
    Row 24: 1 | 100 | eu | 20260922
    Row 25: 2 | 180 | eu | 20260922
    Row 26: 1 | 120 | eu | 20260923
    Row 27: 2 | 180 | eu | 20260923
    Row 28: 1 | 100 | eu | 20260924
    Row 29: 2 |  | eu | 20260924
Sheet "by_region"
  Excel Table "by_region", A1:D4
    Headers: region | total_cents | entries | priciest
    Row 2: eu | =SUMIFS(region_costs[cost_cents],region_costs[region],by_region[[#This Row],[region]]) | =COUNTIFS(region_costs[region],by_region[[#This Row],[region]]) | =_xlfn.MAXIFS(region_costs[cost_cents],region_costs[region],by_region[[#This Row],[region]])
    Row 3: us | =SUMIFS(region_costs[cost_cents],region_costs[region],by_region[[#This Row],[region]]) | =COUNTIFS(region_costs[region],by_region[[#This Row],[region]]) | =_xlfn.MAXIFS(region_costs[cost_cents],region_costs[region],by_region[[#This Row],[region]])
    Total Row: Total | =SUBTOTAL(109,by_region[total_cents]) | =SUBTOTAL(109,by_region[entries]) | =SUBTOTAL(104,by_region[priciest])
>>>

## X62

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x62.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "team_notes"
  Excel Table "team_notes", A1:J6
    Headers: team | note | written_on | week_of | month_end | month_of | months_in | three_before | who | short
    Row 2: web | cache_warm is paused until October | 2026-09-11 | =team_notes[[#This Row],[written_on]]-WEEKDAY(team_notes[[#This Row],[written_on]],2)+1 | =EOMONTH(team_notes[[#This Row],[written_on]],0) | =EOMONTH(team_notes[[#This Row],[written_on]],-1)+1 | =DATEDIF(DATE(2026,1,1),team_notes[[#This Row],[written_on]],"m") | =team_notes[[#This Row],[written_on]]-3 | =PROPER(team_notes[[#This Row],[team]]) | =_xlfn.TEXTJOIN(": ",TRUE,team_notes[[#This Row],[team]],LEFT(team_notes[[#This Row],[note]],5))
    Row 3: data | nightly_load runs long at the end of a month | 2026-09-15 | =team_notes[[#This Row],[written_on]]-WEEKDAY(team_notes[[#This Row],[written_on]],2)+1 | =EOMONTH(team_notes[[#This Row],[written_on]],0) | =EOMONTH(team_notes[[#This Row],[written_on]],-1)+1 | =DATEDIF(DATE(2026,1,1),team_notes[[#This Row],[written_on]],"m") | =team_notes[[#This Row],[written_on]]-3 | =PROPER(team_notes[[#This Row],[team]]) | =_xlfn.TEXTJOIN(": ",TRUE,team_notes[[#This Row],[team]],LEFT(team_notes[[#This Row],[note]],5))
    Row 4: data | ask ana before changing nightly_load | 2026-09-18 | =team_notes[[#This Row],[written_on]]-WEEKDAY(team_notes[[#This Row],[written_on]],2)+1 | =EOMONTH(team_notes[[#This Row],[written_on]],0) | =EOMONTH(team_notes[[#This Row],[written_on]],-1)+1 | =DATEDIF(DATE(2026,1,1),team_notes[[#This Row],[written_on]],"m") | =team_notes[[#This Row],[written_on]]-3 | =PROPER(team_notes[[#This Row],[team]]) | =_xlfn.TEXTJOIN(": ",TRUE,team_notes[[#This Row],[team]],LEFT(team_notes[[#This Row],[note]],5))
    Row 5: finance | report_build came over from data today | 2026-09-18 | =team_notes[[#This Row],[written_on]]-WEEKDAY(team_notes[[#This Row],[written_on]],2)+1 | =EOMONTH(team_notes[[#This Row],[written_on]],0) | =EOMONTH(team_notes[[#This Row],[written_on]],-1)+1 | =DATEDIF(DATE(2026,1,1),team_notes[[#This Row],[written_on]],"m") | =team_notes[[#This Row],[written_on]]-3 | =PROPER(team_notes[[#This Row],[team]]) | =_xlfn.TEXTJOIN(": ",TRUE,team_notes[[#This Row],[team]],LEFT(team_notes[[#This Row],[note]],5))
    Row 6: finance | invoice_sync's bill comes in a day late | 2026-09-21 | =team_notes[[#This Row],[written_on]]-WEEKDAY(team_notes[[#This Row],[written_on]],2)+1 | =EOMONTH(team_notes[[#This Row],[written_on]],0) | =EOMONTH(team_notes[[#This Row],[written_on]],-1)+1 | =DATEDIF(DATE(2026,1,1),team_notes[[#This Row],[written_on]],"m") | =team_notes[[#This Row],[written_on]]-3 | =PROPER(team_notes[[#This Row],[team]]) | =_xlfn.TEXTJOIN(": ",TRUE,team_notes[[#This Row],[team]],LEFT(team_notes[[#This Row],[note]],5))
>>>

## X63

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x63.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "job_runs"
  Excel Table "job_runs", A1:M10
    Headers: run_id | job_id | status | duration_mins | avg_retry_secs | no_retry | quarters | capped | variance | weighted | scheduled_job | label | succeeded
    Row 2: 95 | 1 | SUCCESS | 12 | 2 | =ISBLANK(job_runs[[#This Row],[avg_retry_secs]]) | =INT(job_runs[[#This Row],[duration_mins]]/4) | =MIN(job_runs[[#This Row],[duration_mins]],25) | =_xlfn.VAR.S(job_runs[duration_mins]) | =SUMPRODUCT(job_runs[duration_mins],job_runs[job_id]) | =_xlfn.XLOOKUP(job_runs[[#This Row],[run_id]],scheduler_runs[run_id],scheduler_runs[job_id],-1) | =CONCATENATE("run ",job_runs[[#This Row],[run_id]]) | =ISNUMBER(SEARCH("cess",job_runs[[#This Row],[status]]))
    Row 3: 96 | 2 | SUCCESS | 18 | 0 | =ISBLANK(job_runs[[#This Row],[avg_retry_secs]]) | =INT(job_runs[[#This Row],[duration_mins]]/4) | =MIN(job_runs[[#This Row],[duration_mins]],25) | =_xlfn.VAR.S(job_runs[duration_mins]) | =SUMPRODUCT(job_runs[duration_mins],job_runs[job_id]) | =_xlfn.XLOOKUP(job_runs[[#This Row],[run_id]],scheduler_runs[run_id],scheduler_runs[job_id],-1) | =CONCATENATE("run ",job_runs[[#This Row],[run_id]]) | =ISNUMBER(SEARCH("cess",job_runs[[#This Row],[status]]))
    Row 4: 97 | 3 | FAILED | 30 | 8 | =ISBLANK(job_runs[[#This Row],[avg_retry_secs]]) | =INT(job_runs[[#This Row],[duration_mins]]/4) | =MIN(job_runs[[#This Row],[duration_mins]],25) | =_xlfn.VAR.S(job_runs[duration_mins]) | =SUMPRODUCT(job_runs[duration_mins],job_runs[job_id]) | =_xlfn.XLOOKUP(job_runs[[#This Row],[run_id]],scheduler_runs[run_id],scheduler_runs[job_id],-1) | =CONCATENATE("run ",job_runs[[#This Row],[run_id]]) | =ISNUMBER(SEARCH("cess",job_runs[[#This Row],[status]]))
    Row 5: 98 | 2 |  | 15 |  | =ISBLANK(job_runs[[#This Row],[avg_retry_secs]]) | =INT(job_runs[[#This Row],[duration_mins]]/4) | =MIN(job_runs[[#This Row],[duration_mins]],25) | =_xlfn.VAR.S(job_runs[duration_mins]) | =SUMPRODUCT(job_runs[duration_mins],job_runs[job_id]) | =_xlfn.XLOOKUP(job_runs[[#This Row],[run_id]],scheduler_runs[run_id],scheduler_runs[job_id],-1) | =CONCATENATE("run ",job_runs[[#This Row],[run_id]]) | =ISNUMBER(SEARCH("cess",job_runs[[#This Row],[status]]))
    Row 6: 99 | 1 | TEST | 5 | 0 | =ISBLANK(job_runs[[#This Row],[avg_retry_secs]]) | =INT(job_runs[[#This Row],[duration_mins]]/4) | =MIN(job_runs[[#This Row],[duration_mins]],25) | =_xlfn.VAR.S(job_runs[duration_mins]) | =SUMPRODUCT(job_runs[duration_mins],job_runs[job_id]) | =_xlfn.XLOOKUP(job_runs[[#This Row],[run_id]],scheduler_runs[run_id],scheduler_runs[job_id],-1) | =CONCATENATE("run ",job_runs[[#This Row],[run_id]]) | =ISNUMBER(SEARCH("cess",job_runs[[#This Row],[status]]))
    Row 7: 101 | 1 | SUCCESS | 10 | 1 | =ISBLANK(job_runs[[#This Row],[avg_retry_secs]]) | =INT(job_runs[[#This Row],[duration_mins]]/4) | =MIN(job_runs[[#This Row],[duration_mins]],25) | =_xlfn.VAR.S(job_runs[duration_mins]) | =SUMPRODUCT(job_runs[duration_mins],job_runs[job_id]) | =_xlfn.XLOOKUP(job_runs[[#This Row],[run_id]],scheduler_runs[run_id],scheduler_runs[job_id],-1) | =CONCATENATE("run ",job_runs[[#This Row],[run_id]]) | =ISNUMBER(SEARCH("cess",job_runs[[#This Row],[status]]))
    Row 8: 102 | 2 | FAILED | 20 | 6 | =ISBLANK(job_runs[[#This Row],[avg_retry_secs]]) | =INT(job_runs[[#This Row],[duration_mins]]/4) | =MIN(job_runs[[#This Row],[duration_mins]],25) | =_xlfn.VAR.S(job_runs[duration_mins]) | =SUMPRODUCT(job_runs[duration_mins],job_runs[job_id]) | =_xlfn.XLOOKUP(job_runs[[#This Row],[run_id]],scheduler_runs[run_id],scheduler_runs[job_id],-1) | =CONCATENATE("run ",job_runs[[#This Row],[run_id]]) | =ISNUMBER(SEARCH("cess",job_runs[[#This Row],[status]]))
    Row 9: 103 | 3 | SUCCESS | 30 | 0 | =ISBLANK(job_runs[[#This Row],[avg_retry_secs]]) | =INT(job_runs[[#This Row],[duration_mins]]/4) | =MIN(job_runs[[#This Row],[duration_mins]],25) | =_xlfn.VAR.S(job_runs[duration_mins]) | =SUMPRODUCT(job_runs[duration_mins],job_runs[job_id]) | =_xlfn.XLOOKUP(job_runs[[#This Row],[run_id]],scheduler_runs[run_id],scheduler_runs[job_id],-1) | =CONCATENATE("run ",job_runs[[#This Row],[run_id]]) | =ISNUMBER(SEARCH("cess",job_runs[[#This Row],[status]]))
    Row 10: 104 | 1 | SUCCESS | 40 | 3 | =ISBLANK(job_runs[[#This Row],[avg_retry_secs]]) | =INT(job_runs[[#This Row],[duration_mins]]/4) | =MIN(job_runs[[#This Row],[duration_mins]],25) | =_xlfn.VAR.S(job_runs[duration_mins]) | =SUMPRODUCT(job_runs[duration_mins],job_runs[job_id]) | =_xlfn.XLOOKUP(job_runs[[#This Row],[run_id]],scheduler_runs[run_id],scheduler_runs[job_id],-1) | =CONCATENATE("run ",job_runs[[#This Row],[run_id]]) | =ISNUMBER(SEARCH("cess",job_runs[[#This Row],[status]]))
Sheet "scheduler_runs"
  Excel Table "scheduler_runs", A1:C10
    Headers: run_id | job_id | dt
    Row 2: 95 | 1 | 2026-09-23
    Row 3: 96 | 2 | 2026-09-23
    Row 4: 97 | 3 | 2026-09-23
    Row 5: 98 | 2 | 2026-09-23
    Row 6: 100 | 3 | 2026-09-23
    Row 7: 101 | 1 | 2026-09-24
    Row 8: 102 | 2 | 2026-09-24
    Row 9: 103 | 3 | 2026-09-24
    Row 10: 104 | 1 | 2026-09-24
>>>

## X64

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x64.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "jobs"
  Excel Table "jobs", A1:D5
    Headers: job_id | job_name | team | region
    Row 2: 1 | nightly_load | data | LON
    Row 3: 2 | invoice_sync | finance | PAR
    Row 4: 3 | report_build | finance | NYC
    Row 5: 4 | cache_warm | web | LON
Sheet "region_costs"
  Excel Table "region_costs", A1:D29
    Headers: job_id | cost_cents | region | dt
    Row 2: 1 | 120 | eu | 20260911
    Row 3: 2 | 180 | eu | 20260911
    Row 4: 3 | 300 | us | 20260911
    Row 5: 1 | 110 | eu | 20260912
    Row 6: 1 | 130 | eu | 20260913
    Row 7: 1 | 120 | eu | 20260914
    Row 8: 2 | 200 | eu | 20260914
    Row 9: 3 | 410 | us | 20260914
    Row 10: 1 | 100 | eu | 20260915
    Row 11: 2 | 170 | eu | 20260915
    Row 12: 1 | 250 | eu | 20260916
    Row 13: 2 | 190 | eu | 20260916
    Row 14: 1 | 120 | eu | 20260917
    Row 15: 2 | 160 | eu | 20260917
    Row 16: 1 | 140 | eu | 20260918
    Row 17: 2 | 220 | eu | 20260918
    Row 18: 3 | 120 | us | 20260918
    Row 19: 1 | 110 | eu | 20260919
    Row 20: 1 | 120 | eu | 20260920
    Row 21: 1 | 130 | eu | 20260921
    Row 22: 2 | 210 | eu | 20260921
    Row 23: 3 | 330 | us | 20260921
    Row 24: 1 | 100 | eu | 20260922
    Row 25: 2 | 180 | eu | 20260922
    Row 26: 1 | 120 | eu | 20260923
    Row 27: 2 | 180 | eu | 20260923
    Row 28: 1 | 100 | eu | 20260924
    Row 29: 2 |  | eu | 20260924
Sheet "picked_costs"
  Excel Table "picked_costs", A1:D19, loaded by Power Query "picked_costs"
    Headers: job_id | cost_cents | region | size
    Row 2: 1 | 120 | EU | small
    Row 3: 3 | 300 | US | big
    Row 4: 1 | 110 | EU | small
    Row 5: 1 | 130 | EU | small
    Row 6: 1 | 120 | EU | small
    Row 7: 3 | 410 | US | big
    Row 8: 1 | 100 | EU | small
    Row 9: 1 | 250 | EU | big
    Row 10: 1 | 120 | EU | small
    Row 11: 1 | 140 | EU | small
    Row 12: 3 | 120 | US | small
    Row 13: 1 | 110 | EU | small
    Row 14: 1 | 120 | EU | small
    Row 15: 1 | 130 | EU | small
    Row 16: 3 | 330 | US | big
    Row 17: 1 | 100 | EU | small
    Row 18: 1 | 120 | EU | small
    Row 19: 1 | 100 | EU | small
Sheet "costed_jobs"
  Excel Table "costed_jobs", A1:D3, loaded by Power Query "costed_jobs"
    Headers: job_id | job_name | team | region
    Row 2: 2 | invoice_sync | finance | PAR
    Row 3: 3 | report_build | finance | NYC
Sheet "costs_filled"
  Excel Table "costs_filled", A1:D29, loaded by Power Query "costs_filled"
    Headers: job_id | cost_cents | dt | day
    Row 2: 1 | 120 | 20260911 | 11
    Row 3: 2 | 180 | 20260911 | 11
    Row 4: 3 | 300 | 20260911 | 11
    Row 5: 1 | 110 | 20260912 | 12
    Row 6: 1 | 130 | 20260913 | 13
    Row 7: 1 | 120 | 20260914 | 14
    Row 8: 2 | 200 | 20260914 | 14
    Row 9: 3 | 410 | 20260914 | 14
    Row 10: 1 | 100 | 20260915 | 15
    Row 11: 2 | 170 | 20260915 | 15
    Row 12: 1 | 250 | 20260916 | 16
    Row 13: 2 | 190 | 20260916 | 16
    Row 14: 1 | 120 | 20260917 | 17
    Row 15: 2 | 160 | 20260917 | 17
    Row 16: 1 | 140 | 20260918 | 18
    Row 17: 2 | 220 | 20260918 | 18
    Row 18: 3 | 120 | 20260918 | 18
    Row 19: 1 | 110 | 20260919 | 19
    Row 20: 1 | 120 | 20260920 | 20
    Row 21: 1 | 130 | 20260921 | 21
    Row 22: 2 | 210 | 20260921 | 21
    Row 23: 3 | 330 | 20260921 | 21
    Row 24: 1 | 100 | 20260922 | 22
    Row 25: 2 | 180 | 20260922 | 22
    Row 26: 1 | 120 | 20260923 | 23
    Row 27: 2 | 180 | 20260923 | 23
    Row 28: 1 | 100 | 20260924 | 24
    Row 29: 2 | 0 | 20260924 | 24
Power Query "picked_costs" (loads into Excel Table "picked_costs"):
    let
        Source = Excel.CurrentWorkbook(){[Name="region_costs"]}[Content],
        Kept = Table.SelectRows(Source, each [cost_cents] <> null and List.Contains({1, 3},
            [job_id])),
        Upper = Table.TransformColumns(Kept, {{"region", Text.Upper}}),
        Sized = Table.AddColumn(Upper, "size", each if [cost_cents] >= 200 then "big" else "small"),
        Out = Table.SelectColumns(Sized, {"job_id", "cost_cents", "region", "size"})
    in
        Out
Power Query "costed_jobs" (loads into Excel Table "costed_jobs"):
    let
        Jobs = Excel.CurrentWorkbook(){[Name="jobs"]}[Content],
        Costs = Excel.CurrentWorkbook(){[Name="region_costs"]}[Content],
        Costed = Table.SelectRows(Jobs, each List.Contains(Costs[job_id], [job_id])
            and not Text.StartsWith([job_name], "n"))
    in
        Costed
Power Query "costs_filled" (loads into Excel Table "costs_filled"):
    let
        Source = Table.SelectColumns(Excel.CurrentWorkbook(){[Name="region_costs"]}[Content], {"job_id", "cost_cents", "dt"}),
        Filled = Table.ReplaceValue(Source, null, 0, Replacer.ReplaceValue, {"cost_cents"}),
        Day = Table.AddColumn(Filled, "day", each Text.End([dt], 2))
    in
        Day
>>>

## X65

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x65.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "jobs"
  Excel Table "jobs", A1:D5
    Headers: job_id | job_name | team | region
    Row 2: 1 | nightly_load | data | LON
    Row 3: 2 | invoice_sync | finance | PAR
    Row 4: 3 | report_build | finance | NYC
    Row 5: 4 | cache_warm | web | LON
Sheet "region_budgets"
  Excel Table "region_budgets", A1:C5
    Headers: job_id | budget_cents | region
    Row 2: 1 | 150 | eu
    Row 3: 2 | 200 | eu
    Row 4: 3 | 350 | us
    Row 5: 4 | 50 | eu
Sheet "job_owners"
  Excel Table "job_owners", A1:D57
    Headers: job_id | team | owner | dt
    Row 2: 1 | data | ana | 2026-09-11
    Row 3: 2 | finance | ben | 2026-09-11
    Row 4: 3 | data | ana | 2026-09-11
    Row 5: 4 | web |  | 2026-09-11
    Row 6: 1 | data | ana | 2026-09-12
    Row 7: 2 | finance | ben | 2026-09-12
    Row 8: 3 | data | ana | 2026-09-12
    Row 9: 4 | web |  | 2026-09-12
    Row 10: 1 | data | ana | 2026-09-13
    Row 11: 2 | finance | ben | 2026-09-13
    Row 12: 3 | data | ana | 2026-09-13
    Row 13: 4 | web |  | 2026-09-13
    Row 14: 1 | data | ana | 2026-09-14
    Row 15: 2 | finance | ben | 2026-09-14
    Row 16: 3 | data | ana | 2026-09-14
    Row 17: 4 | web |  | 2026-09-14
    Row 18: 1 | data | ana | 2026-09-15
    Row 19: 2 | finance | ben | 2026-09-15
    Row 20: 3 | data | ana | 2026-09-15
    Row 21: 4 | web |  | 2026-09-15
    Row 22: 1 | data | ana | 2026-09-16
    Row 23: 2 | finance | ben | 2026-09-16
    Row 24: 3 | data | ana | 2026-09-16
    Row 25: 4 | web |  | 2026-09-16
    Row 26: 1 | data | ana | 2026-09-17
    Row 27: 2 | finance | ben | 2026-09-17
    Row 28: 3 | data | ana | 2026-09-17
    Row 29: 4 | web |  | 2026-09-17
    Row 30: 1 | data | ana | 2026-09-18
    Row 31: 2 | finance | ben | 2026-09-18
    Row 32: 3 | finance | chloe | 2026-09-18
    Row 33: 4 | web |  | 2026-09-18
    Row 34: 1 | data | ana | 2026-09-19
    Row 35: 2 | finance | ben | 2026-09-19
    Row 36: 3 | finance | chloe | 2026-09-19
    Row 37: 4 | web |  | 2026-09-19
    Row 38: 1 | data | ana | 2026-09-20
    Row 39: 2 | finance | ben | 2026-09-20
    Row 40: 3 | finance | chloe | 2026-09-20
    Row 41: 4 | web |  | 2026-09-20
    Row 42: 1 | data | ana | 2026-09-21
    Row 43: 2 | finance | ben | 2026-09-21
    Row 44: 3 | finance | chloe | 2026-09-21
    Row 45: 4 | web |  | 2026-09-21
    Row 46: 1 | data | ana | 2026-09-22
    Row 47: 2 | finance | ben | 2026-09-22
    Row 48: 3 | finance | chloe | 2026-09-22
    Row 49: 4 | web |  | 2026-09-22
    Row 50: 1 | data | ana | 2026-09-23
    Row 51: 2 | finance | ben | 2026-09-23
    Row 52: 3 | finance | chloe | 2026-09-23
    Row 53: 4 | web |  | 2026-09-23
    Row 54: 1 | data | ana | 2026-09-24
    Row 55: 2 | finance | ben | 2026-09-24
    Row 56: 3 | finance | chloe | 2026-09-24
    Row 57: 4 | web |  | 2026-09-24
Sheet "scheduler_runs"
  Excel Table "scheduler_runs", A1:C10
    Headers: run_id | job_id | dt
    Row 2: 95 | 1 | 2026-09-23
    Row 3: 96 | 2 | 2026-09-23
    Row 4: 97 | 3 | 2026-09-23
    Row 5: 98 | 2 | 2026-09-23
    Row 6: 100 | 3 | 2026-09-23
    Row 7: 101 | 1 | 2026-09-24
    Row 8: 102 | 2 | 2026-09-24
    Row 9: 103 | 3 | 2026-09-24
    Row 10: 104 | 1 | 2026-09-24
Sheet "job_runs"
  Excel Table "job_runs", A1:F10
    Headers: run_id | job_id | status | duration_mins | avg_retry_secs | dt
    Row 2: 95 | 1 | SUCCESS | 12 | 2 | 2026-09-23
    Row 3: 96 | 2 | SUCCESS | 18 | 0 | 2026-09-23
    Row 4: 97 | 3 | FAILED | 30 | 8 | 2026-09-23
    Row 5: 98 | 2 |  | 15 |  | 2026-09-23
    Row 6: 99 | 1 | TEST | 5 | 0 | 2026-09-23
    Row 7: 101 | 1 | SUCCESS | 10 | 1 | 2026-09-24
    Row 8: 102 | 2 | FAILED | 20 | 6 | 2026-09-24
    Row 9: 103 | 3 | SUCCESS | 30 | 0 | 2026-09-24
    Row 10: 104 | 1 | SUCCESS | 40 | 3 | 2026-09-24
Sheet "team_regions"
  Excel Table "team_regions", A1:B10, loaded by Power Query "team_regions"
    Headers: team | region
    Row 2: data | LON
    Row 3: data | NYC
    Row 4: data | PAR
    Row 5: finance | LON
    Row 6: finance | NYC
    Row 7: finance | PAR
    Row 8: web | LON
    Row 9: web | NYC
    Row 10: web | PAR
Sheet "budget_places"
  Excel Table "budget_places", A1:D5, loaded by Power Query "budget_places"
    Headers: job_id | budget_cents | region | place
    Row 2: 3 | 350 | us | 1
    Row 3: 2 | 200 | eu | 2
    Row 4: 1 | 150 | eu | 3
    Row 5: 4 | 50 | eu | 4
Sheet "jobs_per_team"
  Excel Table "jobs_per_team", A1:B4, loaded by Power Query "jobs_per_team"
    Headers: team | jobs
    Row 2: data | 2
    Row 3: finance | 2
    Row 4: web | 1
Sheet "ran_as_scheduled"
  Excel Table "ran_as_scheduled", A1:B9, loaded by Power Query "ran_as_scheduled"
    Headers: run_id | dt
    Row 2: 95 | 2026-09-23
    Row 3: 96 | 2026-09-23
    Row 4: 97 | 2026-09-23
    Row 5: 98 | 2026-09-23
    Row 6: 101 | 2026-09-24
    Row 7: 102 | 2026-09-24
    Row 8: 103 | 2026-09-24
    Row 9: 104 | 2026-09-24
Sheet "run_measures"
  Excel Table "run_measures", A1:D10, loaded by Power Query "run_measures"
    Headers: run_id | job_id | measure | amount
    Row 2: 95 | 1 | duration_mins | 12
    Row 3: 96 | 2 | duration_mins | 18
    Row 4: 97 | 3 | duration_mins | 30
    Row 5: 98 | 2 | duration_mins | 15
    Row 6: 99 | 1 | duration_mins | 5
    Row 7: 101 | 1 | duration_mins | 10
    Row 8: 102 | 2 | duration_mins | 20
    Row 9: 103 | 3 | duration_mins | 30
    Row 10: 104 | 1 | duration_mins | 40
Power Query "team_regions" (loads into Excel Table "team_regions"):
    let
        Teams = Table.Distinct(Table.SelectColumns(Excel.CurrentWorkbook(){[Name="jobs"]}[Content], {"team"})),
        Regions = Table.Distinct(Table.SelectColumns(Excel.CurrentWorkbook(){[Name="jobs"]}[Content], {"region"})),
        Paired = Table.AddColumn(Teams, "r", each Regions),
        Expanded = Table.ExpandTableColumn(Paired, "r", {"region"}),
        Sorted = Table.Sort(Expanded, {{"team", Order.Ascending}})
    in
        Sorted
Power Query "budget_places" (loads into Excel Table "budget_places"):
    let
        Sorted = Table.Sort(Excel.CurrentWorkbook(){[Name="region_budgets"]}[Content], {{"budget_cents", Order.Descending}}),
        Placed = Table.AddIndexColumn(Sorted, "place", 1, 1)
    in
        Placed
Power Query "jobs_per_team" (loads into Excel Table "jobs_per_team"):
    let
        Source = Excel.CurrentWorkbook(){[Name="job_owners"]}[Content],
        Grouped = Table.Group(Source, {"team"}, {{"jobs", each List.Count(List.Distinct(
            [job_id])), Int64.Type}})
    in
        Grouped
Power Query "ran_as_scheduled" (loads into Excel Table "ran_as_scheduled"):
    let
        Scheduled = Table.SelectColumns(Excel.CurrentWorkbook(){[Name="scheduler_runs"]}[Content], {"run_id", "dt"}),
        Runs = Table.SelectColumns(Excel.CurrentWorkbook(){[Name="job_runs"]}[Content], {"run_id", "dt"}),
        Both = Table.NestedJoin(Scheduled, {"run_id", "dt"}, Runs, {"run_id", "dt"}, "r",
            JoinKind.Inner),
        Unique = Table.Distinct(Table.RemoveColumns(Both, {"r"}))
    in
        Unique
Power Query "run_measures" (loads into Excel Table "run_measures"):
    let
        Source = Table.SelectColumns(Excel.CurrentWorkbook(){[Name="job_runs"]}[Content], {"run_id", "job_id", "duration_mins",
            "avg_retry_secs"}),
        Long = Table.Unpivot(Source, {"duration_mins", "avg_retry_secs"}, "measure", "amount")
    in
        Long
>>>

## X66

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x66.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "job_runs"
  Excel Table "job_runs", A1:F10
    Headers: run_id | job_id | status | duration_mins | avg_retry_secs | dt
    Row 2: 95 | 1 | SUCCESS | 12 | 2 | 2026-09-23
    Row 3: 96 | 2 | SUCCESS | 18 | 0 | 2026-09-23
    Row 4: 97 | 3 | FAILED | 30 | 8 | 2026-09-23
    Row 5: 98 | 2 |  | 15 |  | 2026-09-23
    Row 6: 99 | 1 | TEST | 5 | 0 | 2026-09-23
    Row 7: 101 | 1 | SUCCESS | 10 | 1 | 2026-09-24
    Row 8: 102 | 2 | FAILED | 20 | 6 | 2026-09-24
    Row 9: 103 | 3 | SUCCESS | 30 | 0 | 2026-09-24
    Row 10: 104 | 1 | SUCCESS | 40 | 3 | 2026-09-24
Sheet "ok_runs"
  Excel Table "ok_runs", A1:F7, loaded by Power Query "ok_runs"
    Headers: run_id | job_id | duration_mins | dt | running | share
    Row 2: 95 | 1 | 12 | 2026-09-23 | =SUMIFS(ok_runs[duration_mins],ok_runs[job_id],ok_runs[[#This Row],[job_id]],ok_runs[dt],"<="&ok_runs[[#This Row],[dt]]) | =ok_runs[[#This Row],[duration_mins]]/SUM(ok_runs[duration_mins])
    Row 3: 96 | 2 | 18 | 2026-09-23 | =SUMIFS(ok_runs[duration_mins],ok_runs[job_id],ok_runs[[#This Row],[job_id]],ok_runs[dt],"<="&ok_runs[[#This Row],[dt]]) | =ok_runs[[#This Row],[duration_mins]]/SUM(ok_runs[duration_mins])
    Row 4: 101 | 1 | 10 | 2026-09-24 | =SUMIFS(ok_runs[duration_mins],ok_runs[job_id],ok_runs[[#This Row],[job_id]],ok_runs[dt],"<="&ok_runs[[#This Row],[dt]]) | =ok_runs[[#This Row],[duration_mins]]/SUM(ok_runs[duration_mins])
    Row 5: 103 | 3 | 30 | 2026-09-24 | =SUMIFS(ok_runs[duration_mins],ok_runs[job_id],ok_runs[[#This Row],[job_id]],ok_runs[dt],"<="&ok_runs[[#This Row],[dt]]) | =ok_runs[[#This Row],[duration_mins]]/SUM(ok_runs[duration_mins])
    Row 6: 104 | 1 | 40 | 2026-09-24 | =SUMIFS(ok_runs[duration_mins],ok_runs[job_id],ok_runs[[#This Row],[job_id]],ok_runs[dt],"<="&ok_runs[[#This Row],[dt]]) | =ok_runs[[#This Row],[duration_mins]]/SUM(ok_runs[duration_mins])
    Total Row: Total |  | =SUBTOTAL(109,ok_runs[duration_mins]) |  |  | 
Power Query "ok_runs" (loads into Excel Table "ok_runs"):
    let
        Source = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],
        Ok = Table.SelectRows(Source, each [status] <> null and Text.StartsWith([status], "SUCC")),
        Kept = Table.SelectColumns(Ok, {"run_id", "job_id", "duration_mins", "dt"})
    in
        Kept
>>>

## X69

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x69.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "region_costs"
  Excel Table "region_costs", A1:H29
    Headers: job_id | cost_cents | region | dt | job_name | budget | over_budget | running_cost
    Row 2: 1 | 120 | eu | 20260911 | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],region_budgets[job_id],region_budgets[budget_cents]) | =region_costs[[#This Row],[cost_cents]]>region_costs[[#This Row],[budget]] | =SUMIFS(region_costs[cost_cents],region_costs[job_id],region_costs[[#This Row],[job_id]],region_costs[dt],"<="&region_costs[[#This Row],[dt]])
    Row 3: 2 | 180 | eu | 20260911 | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],region_budgets[job_id],region_budgets[budget_cents]) | =region_costs[[#This Row],[cost_cents]]>region_costs[[#This Row],[budget]] | =SUMIFS(region_costs[cost_cents],region_costs[job_id],region_costs[[#This Row],[job_id]],region_costs[dt],"<="&region_costs[[#This Row],[dt]])
    Row 4: 3 | 300 | us | 20260911 | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],region_budgets[job_id],region_budgets[budget_cents]) | =region_costs[[#This Row],[cost_cents]]>region_costs[[#This Row],[budget]] | =SUMIFS(region_costs[cost_cents],region_costs[job_id],region_costs[[#This Row],[job_id]],region_costs[dt],"<="&region_costs[[#This Row],[dt]])
    Row 5: 1 | 110 | eu | 20260912 | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],region_budgets[job_id],region_budgets[budget_cents]) | =region_costs[[#This Row],[cost_cents]]>region_costs[[#This Row],[budget]] | =SUMIFS(region_costs[cost_cents],region_costs[job_id],region_costs[[#This Row],[job_id]],region_costs[dt],"<="&region_costs[[#This Row],[dt]])
    Row 6: 1 | 130 | eu | 20260913 | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],region_budgets[job_id],region_budgets[budget_cents]) | =region_costs[[#This Row],[cost_cents]]>region_costs[[#This Row],[budget]] | =SUMIFS(region_costs[cost_cents],region_costs[job_id],region_costs[[#This Row],[job_id]],region_costs[dt],"<="&region_costs[[#This Row],[dt]])
    Row 7: 1 | 120 | eu | 20260914 | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],region_budgets[job_id],region_budgets[budget_cents]) | =region_costs[[#This Row],[cost_cents]]>region_costs[[#This Row],[budget]] | =SUMIFS(region_costs[cost_cents],region_costs[job_id],region_costs[[#This Row],[job_id]],region_costs[dt],"<="&region_costs[[#This Row],[dt]])
    Row 8: 2 | 200 | eu | 20260914 | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],region_budgets[job_id],region_budgets[budget_cents]) | =region_costs[[#This Row],[cost_cents]]>region_costs[[#This Row],[budget]] | =SUMIFS(region_costs[cost_cents],region_costs[job_id],region_costs[[#This Row],[job_id]],region_costs[dt],"<="&region_costs[[#This Row],[dt]])
    Row 9: 3 | 410 | us | 20260914 | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],region_budgets[job_id],region_budgets[budget_cents]) | =region_costs[[#This Row],[cost_cents]]>region_costs[[#This Row],[budget]] | =SUMIFS(region_costs[cost_cents],region_costs[job_id],region_costs[[#This Row],[job_id]],region_costs[dt],"<="&region_costs[[#This Row],[dt]])
    Row 10: 1 | 100 | eu | 20260915 | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],region_budgets[job_id],region_budgets[budget_cents]) | =region_costs[[#This Row],[cost_cents]]>region_costs[[#This Row],[budget]] | =SUMIFS(region_costs[cost_cents],region_costs[job_id],region_costs[[#This Row],[job_id]],region_costs[dt],"<="&region_costs[[#This Row],[dt]])
    Row 11: 2 | 170 | eu | 20260915 | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],region_budgets[job_id],region_budgets[budget_cents]) | =region_costs[[#This Row],[cost_cents]]>region_costs[[#This Row],[budget]] | =SUMIFS(region_costs[cost_cents],region_costs[job_id],region_costs[[#This Row],[job_id]],region_costs[dt],"<="&region_costs[[#This Row],[dt]])
    Row 12: 1 | 250 | eu | 20260916 | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],region_budgets[job_id],region_budgets[budget_cents]) | =region_costs[[#This Row],[cost_cents]]>region_costs[[#This Row],[budget]] | =SUMIFS(region_costs[cost_cents],region_costs[job_id],region_costs[[#This Row],[job_id]],region_costs[dt],"<="&region_costs[[#This Row],[dt]])
    Row 13: 2 | 190 | eu | 20260916 | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],region_budgets[job_id],region_budgets[budget_cents]) | =region_costs[[#This Row],[cost_cents]]>region_costs[[#This Row],[budget]] | =SUMIFS(region_costs[cost_cents],region_costs[job_id],region_costs[[#This Row],[job_id]],region_costs[dt],"<="&region_costs[[#This Row],[dt]])
    Row 14: 1 | 120 | eu | 20260917 | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],region_budgets[job_id],region_budgets[budget_cents]) | =region_costs[[#This Row],[cost_cents]]>region_costs[[#This Row],[budget]] | =SUMIFS(region_costs[cost_cents],region_costs[job_id],region_costs[[#This Row],[job_id]],region_costs[dt],"<="&region_costs[[#This Row],[dt]])
    Row 15: 2 | 160 | eu | 20260917 | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],region_budgets[job_id],region_budgets[budget_cents]) | =region_costs[[#This Row],[cost_cents]]>region_costs[[#This Row],[budget]] | =SUMIFS(region_costs[cost_cents],region_costs[job_id],region_costs[[#This Row],[job_id]],region_costs[dt],"<="&region_costs[[#This Row],[dt]])
    Row 16: 1 | 140 | eu | 20260918 | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],region_budgets[job_id],region_budgets[budget_cents]) | =region_costs[[#This Row],[cost_cents]]>region_costs[[#This Row],[budget]] | =SUMIFS(region_costs[cost_cents],region_costs[job_id],region_costs[[#This Row],[job_id]],region_costs[dt],"<="&region_costs[[#This Row],[dt]])
    Row 17: 2 | 220 | eu | 20260918 | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],region_budgets[job_id],region_budgets[budget_cents]) | =region_costs[[#This Row],[cost_cents]]>region_costs[[#This Row],[budget]] | =SUMIFS(region_costs[cost_cents],region_costs[job_id],region_costs[[#This Row],[job_id]],region_costs[dt],"<="&region_costs[[#This Row],[dt]])
    Row 18: 3 | 120 | us | 20260918 | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],region_budgets[job_id],region_budgets[budget_cents]) | =region_costs[[#This Row],[cost_cents]]>region_costs[[#This Row],[budget]] | =SUMIFS(region_costs[cost_cents],region_costs[job_id],region_costs[[#This Row],[job_id]],region_costs[dt],"<="&region_costs[[#This Row],[dt]])
    Row 19: 1 | 110 | eu | 20260919 | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],region_budgets[job_id],region_budgets[budget_cents]) | =region_costs[[#This Row],[cost_cents]]>region_costs[[#This Row],[budget]] | =SUMIFS(region_costs[cost_cents],region_costs[job_id],region_costs[[#This Row],[job_id]],region_costs[dt],"<="&region_costs[[#This Row],[dt]])
    Row 20: 1 | 120 | eu | 20260920 | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],region_budgets[job_id],region_budgets[budget_cents]) | =region_costs[[#This Row],[cost_cents]]>region_costs[[#This Row],[budget]] | =SUMIFS(region_costs[cost_cents],region_costs[job_id],region_costs[[#This Row],[job_id]],region_costs[dt],"<="&region_costs[[#This Row],[dt]])
    Row 21: 1 | 130 | eu | 20260921 | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],region_budgets[job_id],region_budgets[budget_cents]) | =region_costs[[#This Row],[cost_cents]]>region_costs[[#This Row],[budget]] | =SUMIFS(region_costs[cost_cents],region_costs[job_id],region_costs[[#This Row],[job_id]],region_costs[dt],"<="&region_costs[[#This Row],[dt]])
    Row 22: 2 | 210 | eu | 20260921 | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],region_budgets[job_id],region_budgets[budget_cents]) | =region_costs[[#This Row],[cost_cents]]>region_costs[[#This Row],[budget]] | =SUMIFS(region_costs[cost_cents],region_costs[job_id],region_costs[[#This Row],[job_id]],region_costs[dt],"<="&region_costs[[#This Row],[dt]])
    Row 23: 3 | 330 | us | 20260921 | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],region_budgets[job_id],region_budgets[budget_cents]) | =region_costs[[#This Row],[cost_cents]]>region_costs[[#This Row],[budget]] | =SUMIFS(region_costs[cost_cents],region_costs[job_id],region_costs[[#This Row],[job_id]],region_costs[dt],"<="&region_costs[[#This Row],[dt]])
    Row 24: 1 | 100 | eu | 20260922 | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],region_budgets[job_id],region_budgets[budget_cents]) | =region_costs[[#This Row],[cost_cents]]>region_costs[[#This Row],[budget]] | =SUMIFS(region_costs[cost_cents],region_costs[job_id],region_costs[[#This Row],[job_id]],region_costs[dt],"<="&region_costs[[#This Row],[dt]])
    Row 25: 2 | 180 | eu | 20260922 | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],region_budgets[job_id],region_budgets[budget_cents]) | =region_costs[[#This Row],[cost_cents]]>region_costs[[#This Row],[budget]] | =SUMIFS(region_costs[cost_cents],region_costs[job_id],region_costs[[#This Row],[job_id]],region_costs[dt],"<="&region_costs[[#This Row],[dt]])
    Row 26: 1 | 120 | eu | 20260923 | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],region_budgets[job_id],region_budgets[budget_cents]) | =region_costs[[#This Row],[cost_cents]]>region_costs[[#This Row],[budget]] | =SUMIFS(region_costs[cost_cents],region_costs[job_id],region_costs[[#This Row],[job_id]],region_costs[dt],"<="&region_costs[[#This Row],[dt]])
    Row 27: 2 | 180 | eu | 20260923 | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],region_budgets[job_id],region_budgets[budget_cents]) | =region_costs[[#This Row],[cost_cents]]>region_costs[[#This Row],[budget]] | =SUMIFS(region_costs[cost_cents],region_costs[job_id],region_costs[[#This Row],[job_id]],region_costs[dt],"<="&region_costs[[#This Row],[dt]])
    Row 28: 1 | 100 | eu | 20260924 | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],region_budgets[job_id],region_budgets[budget_cents]) | =region_costs[[#This Row],[cost_cents]]>region_costs[[#This Row],[budget]] | =SUMIFS(region_costs[cost_cents],region_costs[job_id],region_costs[[#This Row],[job_id]],region_costs[dt],"<="&region_costs[[#This Row],[dt]])
    Row 29: 2 |  | eu | 20260924 | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =_xlfn.XLOOKUP(region_costs[[#This Row],[job_id]],region_budgets[job_id],region_budgets[budget_cents]) | =region_costs[[#This Row],[cost_cents]]>region_costs[[#This Row],[budget]] | =SUMIFS(region_costs[cost_cents],region_costs[job_id],region_costs[[#This Row],[job_id]],region_costs[dt],"<="&region_costs[[#This Row],[dt]])
Sheet "jobs"
  Excel Table "jobs", A1:D5
    Headers: job_id | job_name | team | region
    Row 2: 1 | nightly_load | data | LON
    Row 3: 2 | invoice_sync | finance | PAR
    Row 4: 3 | report_build | finance | NYC
    Row 5: 4 | cache_warm | web | LON
Sheet "region_budgets"
  Excel Table "region_budgets", A1:C5
    Headers: job_id | budget_cents | region
    Row 2: 1 | 150 | eu
    Row 3: 2 | 200 | eu
    Row 4: 3 | 350 | us
    Row 5: 4 | 50 | eu
Sheet "job_totals"
  Excel Table "job_totals", A1:C5
    Headers: job_id | total_cents | over_count
    Row 2: 1 | =SUMIFS(region_costs[cost_cents],region_costs[job_id],job_totals[[#This Row],[job_id]]) | =COUNTIFS(region_costs[job_id],job_totals[[#This Row],[job_id]],region_costs[over_budget],TRUE)
    Row 3: 2 | =SUMIFS(region_costs[cost_cents],region_costs[job_id],job_totals[[#This Row],[job_id]]) | =COUNTIFS(region_costs[job_id],job_totals[[#This Row],[job_id]],region_costs[over_budget],TRUE)
    Row 4: 3 | =SUMIFS(region_costs[cost_cents],region_costs[job_id],job_totals[[#This Row],[job_id]]) | =COUNTIFS(region_costs[job_id],job_totals[[#This Row],[job_id]],region_costs[over_budget],TRUE)
    Total Row: Total | =SUBTOTAL(109,job_totals[total_cents]) | =SUBTOTAL(109,job_totals[over_count])
Sheet "late_costs"
  Excel Table "late_costs", A1:C7, loaded by Power Query "late_costs"
    Headers: job_id | dt | running_cost
    Row 2: 1 | 20260922 | 100
    Row 3: 1 | 20260923 | 120
    Row 4: 1 | 20260924 | 100
    Row 5: 2 | 20260922 | 180
    Row 6: 2 | 20260923 | 180
    Row 7: 2 | 20260924 | 
Power Query "late_costs" (loads into Excel Table "late_costs"):
    let
        Source = Excel.CurrentWorkbook(){[Name="region_costs"]}[Content],
        Late = Table.SelectRows(Source, each [running_cost] > 1500),
        Kept = Table.SelectColumns(Late, {"job_id", "dt", "running_cost"})
    in
        Kept
>>>

## X70

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x70.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "jobs"
  Excel Table "jobs", A1:D5
    Headers: job_id | job_name | team | region
    Row 2: 1 | nightly_load | data | LON
    Row 3: 2 | invoice_sync | finance | PAR
    Row 4: 3 | report_build | finance | NYC
    Row 5: 4 | cache_warm | web | LON
Sheet "job_owners"
  Excel Table "job_owners", A1:D57
    Headers: job_id | team | owner | dt
    Row 2: 1 | data | ana | 2026-09-11
    Row 3: 2 | finance | ben | 2026-09-11
    Row 4: 3 | data | ana | 2026-09-11
    Row 5: 4 | web |  | 2026-09-11
    Row 6: 1 | data | ana | 2026-09-12
    Row 7: 2 | finance | ben | 2026-09-12
    Row 8: 3 | data | ana | 2026-09-12
    Row 9: 4 | web |  | 2026-09-12
    Row 10: 1 | data | ana | 2026-09-13
    Row 11: 2 | finance | ben | 2026-09-13
    Row 12: 3 | data | ana | 2026-09-13
    Row 13: 4 | web |  | 2026-09-13
    Row 14: 1 | data | ana | 2026-09-14
    Row 15: 2 | finance | ben | 2026-09-14
    Row 16: 3 | data | ana | 2026-09-14
    Row 17: 4 | web |  | 2026-09-14
    Row 18: 1 | data | ana | 2026-09-15
    Row 19: 2 | finance | ben | 2026-09-15
    Row 20: 3 | data | ana | 2026-09-15
    Row 21: 4 | web |  | 2026-09-15
    Row 22: 1 | data | ana | 2026-09-16
    Row 23: 2 | finance | ben | 2026-09-16
    Row 24: 3 | data | ana | 2026-09-16
    Row 25: 4 | web |  | 2026-09-16
    Row 26: 1 | data | ana | 2026-09-17
    Row 27: 2 | finance | ben | 2026-09-17
    Row 28: 3 | data | ana | 2026-09-17
    Row 29: 4 | web |  | 2026-09-17
    Row 30: 1 | data | ana | 2026-09-18
    Row 31: 2 | finance | ben | 2026-09-18
    Row 32: 3 | finance | chloe | 2026-09-18
    Row 33: 4 | web |  | 2026-09-18
    Row 34: 1 | data | ana | 2026-09-19
    Row 35: 2 | finance | ben | 2026-09-19
    Row 36: 3 | finance | chloe | 2026-09-19
    Row 37: 4 | web |  | 2026-09-19
    Row 38: 1 | data | ana | 2026-09-20
    Row 39: 2 | finance | ben | 2026-09-20
    Row 40: 3 | finance | chloe | 2026-09-20
    Row 41: 4 | web |  | 2026-09-20
    Row 42: 1 | data | ana | 2026-09-21
    Row 43: 2 | finance | ben | 2026-09-21
    Row 44: 3 | finance | chloe | 2026-09-21
    Row 45: 4 | web |  | 2026-09-21
    Row 46: 1 | data | ana | 2026-09-22
    Row 47: 2 | finance | ben | 2026-09-22
    Row 48: 3 | finance | chloe | 2026-09-22
    Row 49: 4 | web |  | 2026-09-22
    Row 50: 1 | data | ana | 2026-09-23
    Row 51: 2 | finance | ben | 2026-09-23
    Row 52: 3 | finance | chloe | 2026-09-23
    Row 53: 4 | web |  | 2026-09-23
    Row 54: 1 | data | ana | 2026-09-24
    Row 55: 2 | finance | ben | 2026-09-24
    Row 56: 3 | finance | chloe | 2026-09-24
    Row 57: 4 | web |  | 2026-09-24
Sheet "job_runs"
  Excel Table "job_runs", A1:F10
    Headers: run_id | job_id | status | duration_mins | avg_retry_secs | dt
    Row 2: 95 | 1 | SUCCESS | 12 | 2 | 2026-09-23
    Row 3: 96 | 2 | SUCCESS | 18 | 0 | 2026-09-23
    Row 4: 97 | 3 | FAILED | 30 | 8 | 2026-09-23
    Row 5: 98 | 2 |  | 15 |  | 2026-09-23
    Row 6: 99 | 1 | TEST | 5 | 0 | 2026-09-23
    Row 7: 101 | 1 | SUCCESS | 10 | 1 | 2026-09-24
    Row 8: 102 | 2 | FAILED | 20 | 6 | 2026-09-24
    Row 9: 103 | 3 | SUCCESS | 30 | 0 | 2026-09-24
    Row 10: 104 | 1 | SUCCESS | 40 | 3 | 2026-09-24
Sheet "owner_load"
  Excel Table "owner_load", A1:D5, loaded by Power Query "owner_load"
    Headers: owner | total_mins | runs | avg_mins
    Row 2: ana | 127 | 6 | =owner_load[[#This Row],[total_mins]]/owner_load[[#This Row],[runs]]
    Row 3: ben | 53 | 3 | =owner_load[[#This Row],[total_mins]]/owner_load[[#This Row],[runs]]
    Row 4: chloe | 60 | 2 | =owner_load[[#This Row],[total_mins]]/owner_load[[#This Row],[runs]]
    Total Row: Total |  | =SUBTOTAL(109,owner_load[runs]) | 
Sheet "busiest_owner"
  Excel Table "busiest_owner", A1:C2, loaded by Power Query "busiest_owner"
    Headers: owner | total_mins | runs
    Row 2: ana | 127 | 6
Power Query "staffed" (connection only):
    let
        Jobs = Table.SelectColumns(Excel.CurrentWorkbook(){[Name="jobs"]}[Content], {"job_id", "job_name"}),
        Owners = Table.Distinct(Table.SelectColumns(Excel.CurrentWorkbook(){[Name="job_owners"]}[Content], {"job_id", "owner"})),
        Joined = Table.NestedJoin(Jobs, {"job_id"}, Owners, {"job_id"}, "o", JoinKind.Inner),
        Expanded = Table.ExpandTableColumn(Joined, "o", {"owner"}),
        Named = Table.SelectRows(Expanded, each [owner] <> null)
    in
        Named
Power Query "owner_load" (loads into Excel Table "owner_load"):
    let
        Runs = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],
        Joined = Table.NestedJoin(staffed, {"job_id"}, Runs, {"job_id"}, "r", JoinKind.LeftOuter),
        Expanded = Table.ExpandTableColumn(Joined, "r", {"duration_mins"}),
        Grouped = Table.Group(Expanded, {"owner"}, {
            {"total_mins", each List.Sum([duration_mins]), type number},
            {"runs", each Table.RowCount(_), Int64.Type}})
    in
        Grouped
Power Query "busiest_owner" (loads into Excel Table "busiest_owner"):
    let
        Sorted = Table.Sort(owner_load, {{"runs", Order.Descending}}),
        Top = Table.FirstN(Sorted, 1)
    in
        Top
>>>
