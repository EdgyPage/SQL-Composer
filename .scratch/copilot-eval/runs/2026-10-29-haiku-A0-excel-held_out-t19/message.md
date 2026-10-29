You are standing in for Microsoft Copilot in a web chat. Use no tools: answer from what is written here and what you already know.

Each task below is a separate request the user sends next. Answer each as you would in that chat: reply with its `## X..` heading, then your answer, with SQL in ```sql blocks and any Python in ```python blocks.

## X21

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x21.xlsx, as you read it:

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
  Excel Table "region_budgets", A1:E5
    Headers: job_id | budget_cents | region | budget_dollars | with_margin
    Row 2: 1 | 150 | eu | =region_budgets[[#This Row],[budget_cents]]/100 | =region_budgets[[#This Row],[budget_cents]]*1.1
    Row 3: 2 | 200 | eu | =region_budgets[[#This Row],[budget_cents]]/100 | =region_budgets[[#This Row],[budget_cents]]*1.1
    Row 4: 3 | 350 | us | =region_budgets[[#This Row],[budget_cents]]/100 | =region_budgets[[#This Row],[budget_cents]]*1.1
    Row 5: 4 | 50 | eu | =region_budgets[[#This Row],[budget_cents]]/100 | =region_budgets[[#This Row],[budget_cents]]*1.1
>>>

## X22

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x22.xlsx, as you read it:

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
    Headers: job_id | job_name | team | is_finance | ratio
    Row 2: 1 | nightly_load | data | =IF([@team]="finance","yes","no") | =IFERROR([@job_id]/([@job_id]-2),0)
    Row 3: 2 | invoice_sync | finance | =IF([@team]="finance","yes","no") | =IFERROR([@job_id]/([@job_id]-2),0)
    Row 4: 3 | report_build | finance | =IF([@team]="finance","yes","no") | =IFERROR([@job_id]/([@job_id]-2),0)
    Row 5: 4 | cache_warm | web | =IF([@team]="finance","yes","no") | =IFERROR([@job_id]/([@job_id]-2),0)
>>>

## X23

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x23.xlsx, as you read it:

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
  Excel Table "job_runs", A1:E10
    Headers: run_id | status | avg_retry_secs | label | risky
    Row 2: 95 | SUCCESS | 2 | =_xlfn.SWITCH(job_runs[[#This Row],[status]],"SUCCESS","ok","FAILED","bad","other") | =OR(job_runs[[#This Row],[status]]="FAILED",job_runs[[#This Row],[avg_retry_secs]]>5)
    Row 3: 96 | SUCCESS | 0 | =_xlfn.SWITCH(job_runs[[#This Row],[status]],"SUCCESS","ok","FAILED","bad","other") | =OR(job_runs[[#This Row],[status]]="FAILED",job_runs[[#This Row],[avg_retry_secs]]>5)
    Row 4: 97 | FAILED | 8 | =_xlfn.SWITCH(job_runs[[#This Row],[status]],"SUCCESS","ok","FAILED","bad","other") | =OR(job_runs[[#This Row],[status]]="FAILED",job_runs[[#This Row],[avg_retry_secs]]>5)
    Row 5: 98 |  |  | =_xlfn.SWITCH(job_runs[[#This Row],[status]],"SUCCESS","ok","FAILED","bad","other") | =OR(job_runs[[#This Row],[status]]="FAILED",job_runs[[#This Row],[avg_retry_secs]]>5)
    Row 6: 99 | TEST | 0 | =_xlfn.SWITCH(job_runs[[#This Row],[status]],"SUCCESS","ok","FAILED","bad","other") | =OR(job_runs[[#This Row],[status]]="FAILED",job_runs[[#This Row],[avg_retry_secs]]>5)
    Row 7: 101 | SUCCESS | 1 | =_xlfn.SWITCH(job_runs[[#This Row],[status]],"SUCCESS","ok","FAILED","bad","other") | =OR(job_runs[[#This Row],[status]]="FAILED",job_runs[[#This Row],[avg_retry_secs]]>5)
    Row 8: 102 | FAILED | 6 | =_xlfn.SWITCH(job_runs[[#This Row],[status]],"SUCCESS","ok","FAILED","bad","other") | =OR(job_runs[[#This Row],[status]]="FAILED",job_runs[[#This Row],[avg_retry_secs]]>5)
    Row 9: 103 | SUCCESS | 0 | =_xlfn.SWITCH(job_runs[[#This Row],[status]],"SUCCESS","ok","FAILED","bad","other") | =OR(job_runs[[#This Row],[status]]="FAILED",job_runs[[#This Row],[avg_retry_secs]]>5)
    Row 10: 104 | SUCCESS | 3 | =_xlfn.SWITCH(job_runs[[#This Row],[status]],"SUCCESS","ok","FAILED","bad","other") | =OR(job_runs[[#This Row],[status]]="FAILED",job_runs[[#This Row],[avg_retry_secs]]>5)
>>>

## X24

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x24.xlsx, as you read it:

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
  Excel Table "team_notes", A1:G6
    Headers: team | note | written_on | first_word | shout | month | tens_of_chars
    Row 2: web | cache_warm is paused until October | 2026-09-11 | =LEFT(team_notes[[#This Row],[note]],FIND(" ",team_notes[[#This Row],[note]])-1) | =UPPER(team_notes[[#This Row],[team]]) | =MONTH(team_notes[[#This Row],[written_on]]) | =ROUND(LEN(team_notes[[#This Row],[note]])/10,1)
    Row 3: data | nightly_load runs long at the end of a month | 2026-09-15 | =LEFT(team_notes[[#This Row],[note]],FIND(" ",team_notes[[#This Row],[note]])-1) | =UPPER(team_notes[[#This Row],[team]]) | =MONTH(team_notes[[#This Row],[written_on]]) | =ROUND(LEN(team_notes[[#This Row],[note]])/10,1)
    Row 4: data | ask ana before changing nightly_load | 2026-09-18 | =LEFT(team_notes[[#This Row],[note]],FIND(" ",team_notes[[#This Row],[note]])-1) | =UPPER(team_notes[[#This Row],[team]]) | =MONTH(team_notes[[#This Row],[written_on]]) | =ROUND(LEN(team_notes[[#This Row],[note]])/10,1)
    Row 5: finance | report_build came over from data today | 2026-09-18 | =LEFT(team_notes[[#This Row],[note]],FIND(" ",team_notes[[#This Row],[note]])-1) | =UPPER(team_notes[[#This Row],[team]]) | =MONTH(team_notes[[#This Row],[written_on]]) | =ROUND(LEN(team_notes[[#This Row],[note]])/10,1)
    Row 6: finance | invoice_sync's bill comes in a day late | 2026-09-21 | =LEFT(team_notes[[#This Row],[note]],FIND(" ",team_notes[[#This Row],[note]])-1) | =UPPER(team_notes[[#This Row],[team]]) | =MONTH(team_notes[[#This Row],[written_on]]) | =ROUND(LEN(team_notes[[#This Row],[note]])/10,1)
>>>

## X25

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x25.xlsx, as you read it:

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
Sheet "Costs"
  Excel Table "Costs", A1:E29
    Headers: Job | Cost (cents) | Region | Day Key | Day
    Row 2: 1 | 120 | eu | 20260911 | =DATE(LEFT(Costs[[#This Row],[Day Key]],4),MID(Costs[[#This Row],[Day Key]],5,2),RIGHT(Costs[[#This Row],[Day Key]],2))
    Row 3: 2 | 180 | eu | 20260911 | =DATE(LEFT(Costs[[#This Row],[Day Key]],4),MID(Costs[[#This Row],[Day Key]],5,2),RIGHT(Costs[[#This Row],[Day Key]],2))
    Row 4: 3 | 300 | us | 20260911 | =DATE(LEFT(Costs[[#This Row],[Day Key]],4),MID(Costs[[#This Row],[Day Key]],5,2),RIGHT(Costs[[#This Row],[Day Key]],2))
    Row 5: 1 | 110 | eu | 20260912 | =DATE(LEFT(Costs[[#This Row],[Day Key]],4),MID(Costs[[#This Row],[Day Key]],5,2),RIGHT(Costs[[#This Row],[Day Key]],2))
    Row 6: 1 | 130 | eu | 20260913 | =DATE(LEFT(Costs[[#This Row],[Day Key]],4),MID(Costs[[#This Row],[Day Key]],5,2),RIGHT(Costs[[#This Row],[Day Key]],2))
    Row 7: 1 | 120 | eu | 20260914 | =DATE(LEFT(Costs[[#This Row],[Day Key]],4),MID(Costs[[#This Row],[Day Key]],5,2),RIGHT(Costs[[#This Row],[Day Key]],2))
    Row 8: 2 | 200 | eu | 20260914 | =DATE(LEFT(Costs[[#This Row],[Day Key]],4),MID(Costs[[#This Row],[Day Key]],5,2),RIGHT(Costs[[#This Row],[Day Key]],2))
    Row 9: 3 | 410 | us | 20260914 | =DATE(LEFT(Costs[[#This Row],[Day Key]],4),MID(Costs[[#This Row],[Day Key]],5,2),RIGHT(Costs[[#This Row],[Day Key]],2))
    Row 10: 1 | 100 | eu | 20260915 | =DATE(LEFT(Costs[[#This Row],[Day Key]],4),MID(Costs[[#This Row],[Day Key]],5,2),RIGHT(Costs[[#This Row],[Day Key]],2))
    Row 11: 2 | 170 | eu | 20260915 | =DATE(LEFT(Costs[[#This Row],[Day Key]],4),MID(Costs[[#This Row],[Day Key]],5,2),RIGHT(Costs[[#This Row],[Day Key]],2))
    Row 12: 1 | 250 | eu | 20260916 | =DATE(LEFT(Costs[[#This Row],[Day Key]],4),MID(Costs[[#This Row],[Day Key]],5,2),RIGHT(Costs[[#This Row],[Day Key]],2))
    Row 13: 2 | 190 | eu | 20260916 | =DATE(LEFT(Costs[[#This Row],[Day Key]],4),MID(Costs[[#This Row],[Day Key]],5,2),RIGHT(Costs[[#This Row],[Day Key]],2))
    Row 14: 1 | 120 | eu | 20260917 | =DATE(LEFT(Costs[[#This Row],[Day Key]],4),MID(Costs[[#This Row],[Day Key]],5,2),RIGHT(Costs[[#This Row],[Day Key]],2))
    Row 15: 2 | 160 | eu | 20260917 | =DATE(LEFT(Costs[[#This Row],[Day Key]],4),MID(Costs[[#This Row],[Day Key]],5,2),RIGHT(Costs[[#This Row],[Day Key]],2))
    Row 16: 1 | 140 | eu | 20260918 | =DATE(LEFT(Costs[[#This Row],[Day Key]],4),MID(Costs[[#This Row],[Day Key]],5,2),RIGHT(Costs[[#This Row],[Day Key]],2))
    Row 17: 2 | 220 | eu | 20260918 | =DATE(LEFT(Costs[[#This Row],[Day Key]],4),MID(Costs[[#This Row],[Day Key]],5,2),RIGHT(Costs[[#This Row],[Day Key]],2))
    Row 18: 3 | 120 | us | 20260918 | =DATE(LEFT(Costs[[#This Row],[Day Key]],4),MID(Costs[[#This Row],[Day Key]],5,2),RIGHT(Costs[[#This Row],[Day Key]],2))
    Row 19: 1 | 110 | eu | 20260919 | =DATE(LEFT(Costs[[#This Row],[Day Key]],4),MID(Costs[[#This Row],[Day Key]],5,2),RIGHT(Costs[[#This Row],[Day Key]],2))
    Row 20: 1 | 120 | eu | 20260920 | =DATE(LEFT(Costs[[#This Row],[Day Key]],4),MID(Costs[[#This Row],[Day Key]],5,2),RIGHT(Costs[[#This Row],[Day Key]],2))
    Row 21: 1 | 130 | eu | 20260921 | =DATE(LEFT(Costs[[#This Row],[Day Key]],4),MID(Costs[[#This Row],[Day Key]],5,2),RIGHT(Costs[[#This Row],[Day Key]],2))
    Row 22: 2 | 210 | eu | 20260921 | =DATE(LEFT(Costs[[#This Row],[Day Key]],4),MID(Costs[[#This Row],[Day Key]],5,2),RIGHT(Costs[[#This Row],[Day Key]],2))
    Row 23: 3 | 330 | us | 20260921 | =DATE(LEFT(Costs[[#This Row],[Day Key]],4),MID(Costs[[#This Row],[Day Key]],5,2),RIGHT(Costs[[#This Row],[Day Key]],2))
    Row 24: 1 | 100 | eu | 20260922 | =DATE(LEFT(Costs[[#This Row],[Day Key]],4),MID(Costs[[#This Row],[Day Key]],5,2),RIGHT(Costs[[#This Row],[Day Key]],2))
    Row 25: 2 | 180 | eu | 20260922 | =DATE(LEFT(Costs[[#This Row],[Day Key]],4),MID(Costs[[#This Row],[Day Key]],5,2),RIGHT(Costs[[#This Row],[Day Key]],2))
    Row 26: 1 | 120 | eu | 20260923 | =DATE(LEFT(Costs[[#This Row],[Day Key]],4),MID(Costs[[#This Row],[Day Key]],5,2),RIGHT(Costs[[#This Row],[Day Key]],2))
    Row 27: 2 | 180 | eu | 20260923 | =DATE(LEFT(Costs[[#This Row],[Day Key]],4),MID(Costs[[#This Row],[Day Key]],5,2),RIGHT(Costs[[#This Row],[Day Key]],2))
    Row 28: 1 | 100 | eu | 20260924 | =DATE(LEFT(Costs[[#This Row],[Day Key]],4),MID(Costs[[#This Row],[Day Key]],5,2),RIGHT(Costs[[#This Row],[Day Key]],2))
    Row 29: 2 |  | eu | 20260924 | =DATE(LEFT(Costs[[#This Row],[Day Key]],4),MID(Costs[[#This Row],[Day Key]],5,2),RIGHT(Costs[[#This Row],[Day Key]],2))
Sheet "Budgets"
  Excel Table "Budgets", A1:D5
    Headers: Job | Budget | Region | Dollars
    Row 2: 1 | 150 | eu | =Budgets[[#This Row],[Budget]]/100
    Row 3: 2 | 200 | eu | =Budgets[[#This Row],[Budget]]/100
    Row 4: 3 | 350 | us | =Budgets[[#This Row],[Budget]]/100
    Row 5: 4 | 50 | eu | =Budgets[[#This Row],[Budget]]/100
>>>

## X26

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x26.xlsx, as you read it:

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
Sheet "run_alerts"
  Excel Table "run_alerts", A1:F10
    Headers: alert_id | run_id | severity | job_id | status | avg_mins
    Row 2: 1 | 97 | high | =_xlfn.XLOOKUP(run_alerts[[#This Row],[run_id]],job_runs[run_id],job_runs[job_id]) | =VLOOKUP(run_alerts[[#This Row],[run_id]],job_runs,3,FALSE) | =AVERAGEIFS(job_runs[duration_mins],job_runs[job_id],run_alerts[[#This Row],[job_id]])
    Row 3: 2 | 97 | low | =_xlfn.XLOOKUP(run_alerts[[#This Row],[run_id]],job_runs[run_id],job_runs[job_id]) | =VLOOKUP(run_alerts[[#This Row],[run_id]],job_runs,3,FALSE) | =AVERAGEIFS(job_runs[duration_mins],job_runs[job_id],run_alerts[[#This Row],[job_id]])
    Row 4: 3 | 101 | low | =_xlfn.XLOOKUP(run_alerts[[#This Row],[run_id]],job_runs[run_id],job_runs[job_id]) | =VLOOKUP(run_alerts[[#This Row],[run_id]],job_runs,3,FALSE) | =AVERAGEIFS(job_runs[duration_mins],job_runs[job_id],run_alerts[[#This Row],[job_id]])
    Row 5: 4 | 101 | low | =_xlfn.XLOOKUP(run_alerts[[#This Row],[run_id]],job_runs[run_id],job_runs[job_id]) | =VLOOKUP(run_alerts[[#This Row],[run_id]],job_runs,3,FALSE) | =AVERAGEIFS(job_runs[duration_mins],job_runs[job_id],run_alerts[[#This Row],[job_id]])
    Row 6: 5 | 101 | high | =_xlfn.XLOOKUP(run_alerts[[#This Row],[run_id]],job_runs[run_id],job_runs[job_id]) | =VLOOKUP(run_alerts[[#This Row],[run_id]],job_runs,3,FALSE) | =AVERAGEIFS(job_runs[duration_mins],job_runs[job_id],run_alerts[[#This Row],[job_id]])
    Row 7: 6 | 102 | high | =_xlfn.XLOOKUP(run_alerts[[#This Row],[run_id]],job_runs[run_id],job_runs[job_id]) | =VLOOKUP(run_alerts[[#This Row],[run_id]],job_runs,3,FALSE) | =AVERAGEIFS(job_runs[duration_mins],job_runs[job_id],run_alerts[[#This Row],[job_id]])
    Row 8: 7 | 103 | low | =_xlfn.XLOOKUP(run_alerts[[#This Row],[run_id]],job_runs[run_id],job_runs[job_id]) | =VLOOKUP(run_alerts[[#This Row],[run_id]],job_runs,3,FALSE) | =AVERAGEIFS(job_runs[duration_mins],job_runs[job_id],run_alerts[[#This Row],[job_id]])
    Row 9: 8 | 103 | low | =_xlfn.XLOOKUP(run_alerts[[#This Row],[run_id]],job_runs[run_id],job_runs[job_id]) | =VLOOKUP(run_alerts[[#This Row],[run_id]],job_runs,3,FALSE) | =AVERAGEIFS(job_runs[duration_mins],job_runs[job_id],run_alerts[[#This Row],[job_id]])
    Row 10: 9 | 104 | low | =_xlfn.XLOOKUP(run_alerts[[#This Row],[run_id]],job_runs[run_id],job_runs[job_id]) | =VLOOKUP(run_alerts[[#This Row],[run_id]],job_runs,3,FALSE) | =AVERAGEIFS(job_runs[duration_mins],job_runs[job_id],run_alerts[[#This Row],[job_id]])
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

## X27

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x27.xlsx, as you read it:

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
Sheet "by_team"
  Excel Table "by_team", A1:D4
    Headers: team | jobs_in_team | last_job_id | last_job_name
    Row 2: data | =COUNTIFS(jobs[team],by_team[[#This Row],[team]]) | =_xlfn.MAXIFS(jobs[job_id],jobs[team],by_team[[#This Row],[team]]) | =INDEX(jobs[job_name],MATCH(by_team[[#This Row],[last_job_id]],jobs[job_id],0))
    Row 3: finance | =COUNTIFS(jobs[team],by_team[[#This Row],[team]]) | =_xlfn.MAXIFS(jobs[job_id],jobs[team],by_team[[#This Row],[team]]) | =INDEX(jobs[job_name],MATCH(by_team[[#This Row],[last_job_id]],jobs[job_id],0))
    Row 4: web | =COUNTIFS(jobs[team],by_team[[#This Row],[team]]) | =_xlfn.MAXIFS(jobs[job_id],jobs[team],by_team[[#This Row],[team]]) | =INDEX(jobs[job_name],MATCH(by_team[[#This Row],[last_job_id]],jobs[job_id],0))
>>>

## X28

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x28.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2: jobs | job_id
Sheet "jobs"
  Excel Table "jobs", A1:C5
    Headers: job_id | job_name | ok_mins
    Row 2: 1 | nightly_load | =SUMIFS(job_runs[duration_mins],job_runs[job_id],jobs[[#This Row],[job_id]],job_runs[status],"SUCCESS")
    Row 3: 2 | invoice_sync | =SUMIFS(job_runs[duration_mins],job_runs[job_id],jobs[[#This Row],[job_id]],job_runs[status],"SUCCESS")
    Row 4: 3 | report_build | 99
    Row 5: 4 | cache_warm | =SUMIFS(job_runs[duration_mins],job_runs[job_id],jobs[[#This Row],[job_id]],job_runs[status],"SUCCESS")
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

## X29

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x29.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2: cents_per_dollar | 100
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2:  | 
Sheet "region_budgets"
  Excel Table "region_budgets", A1:E5
    Headers: job_id | budget_cents | region | in_dollars | pointer
    Row 2: 1 | 150 | eu | =region_budgets[[#This Row],[budget_cents]]/_xlfn.XLOOKUP("cents_per_dollar",Parameters[name],Parameters[value]) | =INDIRECT("A"&ROW())
    Row 3: 2 | 200 | eu | =region_budgets[[#This Row],[budget_cents]]/_xlfn.XLOOKUP("cents_per_dollar",Parameters[name],Parameters[value]) | =INDIRECT("A"&ROW())
    Row 4: 3 | 350 | us | 5 | =INDIRECT("A"&ROW())
    Row 5: 4 | 50 | eu | =region_budgets[[#This Row],[budget_cents]]/_xlfn.XLOOKUP("cents_per_dollar",Parameters[name],Parameters[value]) | =INDIRECT("A"&ROW())
>>>

## X30

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x30.xlsx, as you read it:

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
Sheet "scheduler_runs"
  Excel Table "scheduler_runs", A1:F10
    Headers: run_id | job_id | dt | day | prev_run | jitter
    Row 2: 95 | 1 | 2026-09-23 | =RIGHT(scheduler_runs[[#This Row],[dt]],2) | =OFFSET(scheduler_runs[[#This Row],[run_id]],-1,0) | =RANDBETWEEN(1,5)
    Row 3: 96 | 2 | 2026-09-23 | =RIGHT(scheduler_runs[[#This Row],[dt]],2) | =OFFSET(scheduler_runs[[#This Row],[run_id]],-1,0) | =RANDBETWEEN(1,5)
    Row 4: 97 | 3 | 2026-09-23 | =RIGHT(scheduler_runs[[#This Row],[dt]],2) | =OFFSET(scheduler_runs[[#This Row],[run_id]],-1,0) | =RANDBETWEEN(1,5)
    Row 5: 98 | 2 | 2026-09-23 | =RIGHT(scheduler_runs[[#This Row],[dt]],2) | =OFFSET(scheduler_runs[[#This Row],[run_id]],-1,0) | =RANDBETWEEN(1,5)
    Row 6: 100 | 3 | 2026-09-23 | =RIGHT(scheduler_runs[[#This Row],[dt]],2) | =OFFSET(scheduler_runs[[#This Row],[run_id]],-1,0) | =RANDBETWEEN(1,5)
    Row 7: 101 | 1 | 2026-09-24 | =RIGHT(scheduler_runs[[#This Row],[dt]],2) | =OFFSET(scheduler_runs[[#This Row],[run_id]],-1,0) | =RANDBETWEEN(1,5)
    Row 8: 102 | 2 | 2026-09-24 | =RIGHT(scheduler_runs[[#This Row],[dt]],2) | =OFFSET(scheduler_runs[[#This Row],[run_id]],-1,0) | =RANDBETWEEN(1,5)
    Row 9: 103 | 3 | 2026-09-24 | =RIGHT(scheduler_runs[[#This Row],[dt]],2) | =OFFSET(scheduler_runs[[#This Row],[run_id]],-1,0) | =RANDBETWEEN(1,5)
    Row 10: 104 | 1 | 2026-09-24 | =RIGHT(scheduler_runs[[#This Row],[dt]],2) | =OFFSET(scheduler_runs[[#This Row],[run_id]],-1,0) | =RANDBETWEEN(1,5)
Sheet "Summary"
  A bar chart
Also in the workbook: a PivotTable on sheet "Pivot", from Table scheduler_runs: rows job_id, values Count of run_id
>>>

## X31

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x31.xlsx, as you read it:

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
    Headers: job_id | team | bump | tag | scaled | boosted
    Row 2: 1 | data | =jobs[[#This Row],[bump]]*2 | =TAG(jobs[[#This Row],[team]]) | =jobs[[#This Row],[job_id]]*Summary!$D$4 | =jobs[[#This Row],[job_id]]*boost
    Row 3: 2 | finance | =jobs[[#This Row],[bump]]*2 | =TAG(jobs[[#This Row],[team]]) | =jobs[[#This Row],[job_id]]*Summary!$D$4 | =jobs[[#This Row],[job_id]]*boost
    Row 4: 3 | finance | =jobs[[#This Row],[bump]]*2 | =TAG(jobs[[#This Row],[team]]) | =jobs[[#This Row],[job_id]]*Summary!$D$4 | =jobs[[#This Row],[job_id]]*boost
    Row 5: 4 | web | =jobs[[#This Row],[bump]]*2 | =TAG(jobs[[#This Row],[team]]) | =jobs[[#This Row],[job_id]]*Summary!$D$4 | =jobs[[#This Row],[job_id]]*boost
Sheet "Summary"
  B2: 10
  D4: 7
Defined name boost: Summary!$B$2
Defined name TAG: _xlfn.LAMBDA(t,UPPER(t)&"!")
>>>

## X32

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x32.xlsx, as you read it:

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
  Excel Table "job_runs", A1:G10
    Headers: run_id | job_id | status | duration_mins | avg_retry_secs | dt | job_name
    Row 2: 95 | 1 | SUCCESS | 12 | 2 | 2026-09-23 | =VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE)
    Row 3: 96 | 2 | SUCCESS | 18 | 0 | 2026-09-23 | =VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE)
    Row 4: 97 | 3 | FAILED | 30 | 8 | 2026-09-23 | =VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE)
    Row 5: 98 | 2 |  | 15 |  | 2026-09-23 | =VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE)
    Row 6: 99 | 1 | TEST | 5 | 0 | 2026-09-23 | =VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE)
    Row 7: 101 | 1 | SUCCESS | 10 | 1 | 2026-09-24 | =VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE)
    Row 8: 102 | 2 | FAILED | 20 | 6 | 2026-09-24 | =VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE)
    Row 9: 103 | 3 | SUCCESS | 30 | 0 | 2026-09-24 | =VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE)
    Row 10: 104 | 1 | SUCCESS | 40 | 3 | 2026-09-24 | =VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE)
Sheet "jobs"
  Excel Table "jobs", A1:D5
    Headers: job_id | job_name | team | region
    Row 2: 1 | nightly_load | data | LON
    Row 3: 2 | invoice_sync | finance | PAR
    Row 4: 3 | report_build | finance | NYC
    Row 5: 4 | cache_warm | web | LON
Sheet "by_name"
  Excel Table "by_name", A1:B4
    Headers: job_name | runs
    Row 2: invoice_sync | =COUNTIFS(job_runs[job_name],by_name[[#This Row],[job_name]])
    Row 3: nightly_load | =COUNTIFS(job_runs[job_name],by_name[[#This Row],[job_name]])
    Row 4: report_build | =COUNTIFS(job_runs[job_name],by_name[[#This Row],[job_name]])
>>>

## X33

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x33.xlsx, as you read it:

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
Sheet "slow_runs"
  Excel Table "slow_runs", A1:C5, loaded by Power Query "slow_runs"
    Headers: run_id | duration_mins | over_by
    Row 2: 97 | 30 | 10
    Row 3: 102 | 20 | 0
    Row 4: 103 | 30 | 10
    Row 5: 104 | 40 | 20
Power Query "slow_runs" (loads into Excel Table "slow_runs"):
    let
        Warehouse = Sql.Database("dwh01", "ops"),
        Source = Warehouse{[Schema = "ops", Item = "job_runs"]}[Data],
        Slow = Table.SelectRows(Source, each [duration_mins] >= 20 and [status] <> "TEST"),
        Added = Table.AddColumn(Slow, "over_by", each [duration_mins] - 20, type number),
        Kept = Table.SelectColumns(Added, {"run_id", "duration_mins", "over_by"})
    in
        Kept
>>>

## X34

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x34.xlsx, as you read it:

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
Sheet "team_totals"
  Excel Table "team_totals", A1:C3, loaded by Power Query "team_totals"
    Headers: team | total_mins | longest
    Row 2: data | 67 | 40
    Row 3: finance | 113 | 30
Power Query "runs_with_team" (connection only):
    let
        Source = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],
        Jobs = Excel.CurrentWorkbook(){[Name="jobs"]}[Content],
        Joined = Table.NestedJoin(Source, {"job_id"}, Jobs, {"job_id"}, "j", JoinKind.LeftOuter),
        Expanded = Table.ExpandTableColumn(Joined, "j", {"team"})
    in
        Expanded
Power Query "team_totals" (loads into Excel Table "team_totals"):
    let
        Source = runs_with_team,
        Grouped = Table.Group(Source, {"team"}, {
            {"total_mins", each List.Sum([duration_mins]), type number},
            {"longest", each List.Max([duration_mins]), type number}})
    in
        Grouped
>>>

## X35

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x35.xlsx, as you read it:

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
Sheet "recent"
  Excel Table "recent", A1:B5, loaded by Power Query "recent"
    Headers: run_id | dt
    Row 2: 104 | 2026-09-24
    Row 3: 104 | 2026-09-24
    Row 4: 103 | 2026-09-24
    Row 5: 103 | 2026-09-24
Power Query "recent" (loads into Excel Table "recent"):
    let
        Runs = Table.SelectColumns(Excel.CurrentWorkbook(){[Name="job_runs"]}[Content], {"run_id", "dt"}),
        Scheduled = Table.SelectColumns(Excel.CurrentWorkbook(){[Name="scheduler_runs"]}[Content], {"run_id", "dt"}),
        Both = Table.Combine({Runs, Scheduled}),
        Sorted = Table.Sort(Both, {{"run_id", Order.Descending}}),
        Top = Table.FirstN(Sorted, 4)
    in
        Top
Power Query "rates" (connection only):
    let
        Source = Json.Document(Web.Contents("https://rates.example.com/today.json"))
    in
        Source
>>>

## X36

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x36.xlsx, as you read it:

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
Sheet "severity_by_day"
  Excel Table "severity_by_day", A1:C3, loaded by Power Query "severity_by_day"
    Headers: dt | high | low
    Row 2: 2026-09-23 | 1 | 1
    Row 3: 2026-09-24 | 2 | 5
Sheet "job_runs"
  Excel Table "job_runs", A1:C10
    Headers: run_id | status | alerts
    Row 2: 95 | SUCCESS | =COUNTIFS(run_alerts[run_id],job_runs[[#This Row],[run_id]])
    Row 3: 96 | SUCCESS | =COUNTIFS(run_alerts[run_id],job_runs[[#This Row],[run_id]])
    Row 4: 97 | FAILED | =COUNTIFS(run_alerts[run_id],job_runs[[#This Row],[run_id]])
    Row 5: 98 |  | =COUNTIFS(run_alerts[run_id],job_runs[[#This Row],[run_id]])
    Row 6: 99 | TEST | =COUNTIFS(run_alerts[run_id],job_runs[[#This Row],[run_id]])
    Row 7: 101 | SUCCESS | =COUNTIFS(run_alerts[run_id],job_runs[[#This Row],[run_id]])
    Row 8: 102 | FAILED | =COUNTIFS(run_alerts[run_id],job_runs[[#This Row],[run_id]])
    Row 9: 103 | SUCCESS | =COUNTIFS(run_alerts[run_id],job_runs[[#This Row],[run_id]])
    Row 10: 104 | SUCCESS | =COUNTIFS(run_alerts[run_id],job_runs[[#This Row],[run_id]])
Power Query "severity_by_day" (loads into Excel Table "severity_by_day"):
    let
        Source = Excel.CurrentWorkbook(){[Name="run_alerts"]}[Content],
        Kept = Table.SelectColumns(Source, {"dt", "severity"}),
        Counted = Table.AddColumn(Kept, "n", each 1),
        Pivoted = Table.Pivot(Counted, List.Distinct(Counted[severity]), "severity", "n", List.Sum)
    in
        Pivoted
>>>

## X37

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x37.xlsx, as you read it:

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
Sheet "Owners"
  Excel Table "Owners", A1:E57
    Headers: Job No | Team Name | Owner | Day | Is Ana
    Row 2: 1 | data | ana | 2026-09-11 | =IF([@Owner]="ana",1,0)
    Row 3: 2 | finance | ben | 2026-09-11 | =IF([@Owner]="ana",1,0)
    Row 4: 3 | data | ana | 2026-09-11 | =IF([@Owner]="ana",1,0)
    Row 5: 4 | web |  | 2026-09-11 | =IF([@Owner]="ana",1,0)
    Row 6: 1 | data | ana | 2026-09-12 | =IF([@Owner]="ana",1,0)
    Row 7: 2 | finance | ben | 2026-09-12 | =IF([@Owner]="ana",1,0)
    Row 8: 3 | data | ana | 2026-09-12 | =IF([@Owner]="ana",1,0)
    Row 9: 4 | web |  | 2026-09-12 | =IF([@Owner]="ana",1,0)
    Row 10: 1 | data | ana | 2026-09-13 | =IF([@Owner]="ana",1,0)
    Row 11: 2 | finance | ben | 2026-09-13 | =IF([@Owner]="ana",1,0)
    Row 12: 3 | data | ana | 2026-09-13 | =IF([@Owner]="ana",1,0)
    Row 13: 4 | web |  | 2026-09-13 | =IF([@Owner]="ana",1,0)
    Row 14: 1 | data | ana | 2026-09-14 | =IF([@Owner]="ana",1,0)
    Row 15: 2 | finance | ben | 2026-09-14 | =IF([@Owner]="ana",1,0)
    Row 16: 3 | data | ana | 2026-09-14 | =IF([@Owner]="ana",1,0)
    Row 17: 4 | web |  | 2026-09-14 | =IF([@Owner]="ana",1,0)
    Row 18: 1 | data | ana | 2026-09-15 | =IF([@Owner]="ana",1,0)
    Row 19: 2 | finance | ben | 2026-09-15 | =IF([@Owner]="ana",1,0)
    Row 20: 3 | data | ana | 2026-09-15 | =IF([@Owner]="ana",1,0)
    Row 21: 4 | web |  | 2026-09-15 | =IF([@Owner]="ana",1,0)
    Row 22: 1 | data | ana | 2026-09-16 | =IF([@Owner]="ana",1,0)
    Row 23: 2 | finance | ben | 2026-09-16 | =IF([@Owner]="ana",1,0)
    Row 24: 3 | data | ana | 2026-09-16 | =IF([@Owner]="ana",1,0)
    Row 25: 4 | web |  | 2026-09-16 | =IF([@Owner]="ana",1,0)
    Row 26: 1 | data | ana | 2026-09-17 | =IF([@Owner]="ana",1,0)
    Row 27: 2 | finance | ben | 2026-09-17 | =IF([@Owner]="ana",1,0)
    Row 28: 3 | data | ana | 2026-09-17 | =IF([@Owner]="ana",1,0)
    Row 29: 4 | web |  | 2026-09-17 | =IF([@Owner]="ana",1,0)
    Row 30: 1 | data | ana | 2026-09-18 | =IF([@Owner]="ana",1,0)
    Row 31: 2 | finance | ben | 2026-09-18 | =IF([@Owner]="ana",1,0)
    Row 32: 3 | finance | chloe | 2026-09-18 | =IF([@Owner]="ana",1,0)
    Row 33: 4 | web |  | 2026-09-18 | =IF([@Owner]="ana",1,0)
    Row 34: 1 | data | ana | 2026-09-19 | =IF([@Owner]="ana",1,0)
    Row 35: 2 | finance | ben | 2026-09-19 | =IF([@Owner]="ana",1,0)
    Row 36: 3 | finance | chloe | 2026-09-19 | =IF([@Owner]="ana",1,0)
    Row 37: 4 | web |  | 2026-09-19 | =IF([@Owner]="ana",1,0)
    Row 38: 1 | data | ana | 2026-09-20 | =IF([@Owner]="ana",1,0)
    Row 39: 2 | finance | ben | 2026-09-20 | =IF([@Owner]="ana",1,0)
    Row 40: 3 | finance | chloe | 2026-09-20 | =IF([@Owner]="ana",1,0)
    Row 41: 4 | web |  | 2026-09-20 | =IF([@Owner]="ana",1,0)
    Row 42: 1 | data | ana | 2026-09-21 | =IF([@Owner]="ana",1,0)
    Row 43: 2 | finance | ben | 2026-09-21 | =IF([@Owner]="ana",1,0)
    Row 44: 3 | finance | chloe | 2026-09-21 | =IF([@Owner]="ana",1,0)
    Row 45: 4 | web |  | 2026-09-21 | =IF([@Owner]="ana",1,0)
    Row 46: 1 | data | ana | 2026-09-22 | =IF([@Owner]="ana",1,0)
    Row 47: 2 | finance | ben | 2026-09-22 | =IF([@Owner]="ana",1,0)
    Row 48: 3 | finance | chloe | 2026-09-22 | =IF([@Owner]="ana",1,0)
    Row 49: 4 | web |  | 2026-09-22 | =IF([@Owner]="ana",1,0)
    Row 50: 1 | data | ana | 2026-09-23 | =IF([@Owner]="ana",1,0)
    Row 51: 2 | finance | ben | 2026-09-23 | =IF([@Owner]="ana",1,0)
    Row 52: 3 | finance | chloe | 2026-09-23 | =IF([@Owner]="ana",1,0)
    Row 53: 4 | web |  | 2026-09-23 | =IF([@Owner]="ana",1,0)
    Row 54: 1 | data | ana | 2026-09-24 | =IF([@Owner]="ana",1,0)
    Row 55: 2 | finance | ben | 2026-09-24 | =IF([@Owner]="ana",1,0)
    Row 56: 3 | finance | chloe | 2026-09-24 | =IF([@Owner]="ana",1,0)
    Row 57: 4 | web |  | 2026-09-24 | =IF([@Owner]="ana",1,0)
>>>

## X38

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x38.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2:  | 
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2: job_runs | run_id
Sheet "job_runs"
  Excel Table "job_runs", A1:H10
    Headers: run_id | job_id | status | duration_mins | avg_retry_secs | region | region_mins | retry_cost
    Row 2: 95 | 1 | SUCCESS | 12 | 2 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[region]) | =SUMIFS(job_runs[duration_mins],job_runs[region],job_runs[[#This Row],[region]]) | =(job_runs[[#This Row],[avg_retry_secs]]+job_runs[[#This Row],[duration_mins]])*2
    Row 3: 96 | 2 | SUCCESS | 18 | 0 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[region]) | =SUMIFS(job_runs[duration_mins],job_runs[region],job_runs[[#This Row],[region]]) | =(job_runs[[#This Row],[avg_retry_secs]]+job_runs[[#This Row],[duration_mins]])*2
    Row 4: 97 | 3 | FAILED | 30 | 8 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[region]) | =SUMIFS(job_runs[duration_mins],job_runs[region],job_runs[[#This Row],[region]]) | =(job_runs[[#This Row],[avg_retry_secs]]+job_runs[[#This Row],[duration_mins]])*2
    Row 5: 98 | 2 |  | 15 |  | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[region]) | =SUMIFS(job_runs[duration_mins],job_runs[region],job_runs[[#This Row],[region]]) | =(job_runs[[#This Row],[avg_retry_secs]]+job_runs[[#This Row],[duration_mins]])*2
    Row 6: 99 | 1 | TEST | 5 | 0 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[region]) | =SUMIFS(job_runs[duration_mins],job_runs[region],job_runs[[#This Row],[region]]) | =(job_runs[[#This Row],[avg_retry_secs]]+job_runs[[#This Row],[duration_mins]])*2
    Row 7: 101 | 1 | SUCCESS | 10 | 1 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[region]) | =SUMIFS(job_runs[duration_mins],job_runs[region],job_runs[[#This Row],[region]]) | =(job_runs[[#This Row],[avg_retry_secs]]+job_runs[[#This Row],[duration_mins]])*2
    Row 8: 102 | 2 | FAILED | 20 | 6 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[region]) | =SUMIFS(job_runs[duration_mins],job_runs[region],job_runs[[#This Row],[region]]) | 1
    Row 9: 103 | 3 | SUCCESS | 30 | 0 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[region]) | =SUMIFS(job_runs[duration_mins],job_runs[region],job_runs[[#This Row],[region]]) | =(job_runs[[#This Row],[avg_retry_secs]]+job_runs[[#This Row],[duration_mins]])*2
    Row 10: 104 | 1 | SUCCESS | 40 | 3 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[region]) | =SUMIFS(job_runs[duration_mins],job_runs[region],job_runs[[#This Row],[region]]) | =(job_runs[[#This Row],[avg_retry_secs]]+job_runs[[#This Row],[duration_mins]])*2
Sheet "jobs"
  Excel Table "jobs", A1:D5
    Headers: job_id | job_name | team | region
    Row 2: 1 | nightly_load | data | LON
    Row 3: 2 | invoice_sync | finance | PAR
    Row 4: 3 | report_build | finance | NYC
    Row 5: 4 | cache_warm | web | LON
>>>

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
