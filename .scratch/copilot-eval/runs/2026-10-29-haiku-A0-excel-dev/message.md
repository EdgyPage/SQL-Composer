You are standing in for Microsoft Copilot in a web chat. Use no tools: answer from what is written here and what you already know.

Each task below is a separate request the user sends next. Answer each as you would in that chat: reply with its `## X..` heading, then your answer, with SQL in ```sql blocks and any Python in ```python blocks.

## X01

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x01.xlsx, as you read it:

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
    Headers: run_id | job_id | duration_mins | dt | duration_hours
    Row 2: 95 | 1 | 12 | 2026-09-23 | =[@duration_mins]/60
    Row 3: 96 | 2 | 18 | 2026-09-23 | =[@duration_mins]/60
    Row 4: 97 | 3 | 30 | 2026-09-23 | =[@duration_mins]/60
    Row 5: 98 | 2 | 15 | 2026-09-23 | =[@duration_mins]/60
    Row 6: 99 | 1 | 5 | 2026-09-23 | =[@duration_mins]/60
    Row 7: 101 | 1 | 10 | 2026-09-24 | =[@duration_mins]/60
    Row 8: 102 | 2 | 20 | 2026-09-24 | =[@duration_mins]/60
    Row 9: 103 | 3 | 30 | 2026-09-24 | =[@duration_mins]/60
    Row 10: 104 | 1 | 40 | 2026-09-24 | =[@duration_mins]/60
>>>

## X02

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x02.xlsx, as you read it:

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
    Headers: run_id | job_id | status | duration_mins | slow_job1 | flag
    Row 2: 95 | 1 | SUCCESS | 12 | =AND(job_runs[[#This Row],[duration_mins]]>10,job_runs[[#This Row],[job_id]]=1) | =IF(OR(job_runs[[#This Row],[duration_mins]]>25,job_runs[[#This Row],[job_id]]=3),"check","ok")
    Row 3: 96 | 2 | SUCCESS | 18 | =AND(job_runs[[#This Row],[duration_mins]]>10,job_runs[[#This Row],[job_id]]=1) | =IF(OR(job_runs[[#This Row],[duration_mins]]>25,job_runs[[#This Row],[job_id]]=3),"check","ok")
    Row 4: 97 | 3 | FAILED | 30 | =AND(job_runs[[#This Row],[duration_mins]]>10,job_runs[[#This Row],[job_id]]=1) | =IF(OR(job_runs[[#This Row],[duration_mins]]>25,job_runs[[#This Row],[job_id]]=3),"check","ok")
    Row 5: 98 | 2 |  | 15 | =AND(job_runs[[#This Row],[duration_mins]]>10,job_runs[[#This Row],[job_id]]=1) | =IF(OR(job_runs[[#This Row],[duration_mins]]>25,job_runs[[#This Row],[job_id]]=3),"check","ok")
    Row 6: 99 | 1 | TEST | 5 | =AND(job_runs[[#This Row],[duration_mins]]>10,job_runs[[#This Row],[job_id]]=1) | =IF(OR(job_runs[[#This Row],[duration_mins]]>25,job_runs[[#This Row],[job_id]]=3),"check","ok")
    Row 7: 101 | 1 | SUCCESS | 10 | =AND(job_runs[[#This Row],[duration_mins]]>10,job_runs[[#This Row],[job_id]]=1) | =IF(OR(job_runs[[#This Row],[duration_mins]]>25,job_runs[[#This Row],[job_id]]=3),"check","ok")
    Row 8: 102 | 2 | FAILED | 20 | =AND(job_runs[[#This Row],[duration_mins]]>10,job_runs[[#This Row],[job_id]]=1) | =IF(OR(job_runs[[#This Row],[duration_mins]]>25,job_runs[[#This Row],[job_id]]=3),"check","ok")
    Row 9: 103 | 3 | SUCCESS | 30 | =AND(job_runs[[#This Row],[duration_mins]]>10,job_runs[[#This Row],[job_id]]=1) | =IF(OR(job_runs[[#This Row],[duration_mins]]>25,job_runs[[#This Row],[job_id]]=3),"check","ok")
    Row 10: 104 | 1 | SUCCESS | 40 | =AND(job_runs[[#This Row],[duration_mins]]>10,job_runs[[#This Row],[job_id]]=1) | =IF(OR(job_runs[[#This Row],[duration_mins]]>25,job_runs[[#This Row],[job_id]]=3),"check","ok")
>>>

## X03

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x03.xlsx, as you read it:

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
  Excel Table "job_runs", A1:I10
    Headers: run_id | job_id | status | duration_mins | avg_retry_secs | dt | score | mins_per_retry | total_secs
    Row 2: 95 | 1 | SUCCESS | 12 | 2 | 2026-09-23 | =_xlfn.SWITCH(job_runs[[#This Row],[status]],"SUCCESS",1,"FAILED",-1,0) | =IFERROR(job_runs[[#This Row],[duration_mins]]/job_runs[[#This Row],[avg_retry_secs]],0) | =job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]]
    Row 3: 96 | 2 | SUCCESS | 18 | 0 | 2026-09-23 | =_xlfn.SWITCH(job_runs[[#This Row],[status]],"SUCCESS",1,"FAILED",-1,0) | =IFERROR(job_runs[[#This Row],[duration_mins]]/job_runs[[#This Row],[avg_retry_secs]],0) | =job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]]
    Row 4: 97 | 3 | FAILED | 30 | 8 | 2026-09-23 | =_xlfn.SWITCH(job_runs[[#This Row],[status]],"SUCCESS",1,"FAILED",-1,0) | =IFERROR(job_runs[[#This Row],[duration_mins]]/job_runs[[#This Row],[avg_retry_secs]],0) | =job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]]
    Row 5: 98 | 2 |  | 15 |  | 2026-09-23 | =_xlfn.SWITCH(job_runs[[#This Row],[status]],"SUCCESS",1,"FAILED",-1,0) | =IFERROR(job_runs[[#This Row],[duration_mins]]/job_runs[[#This Row],[avg_retry_secs]],0) | =job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]]
    Row 6: 99 | 1 | TEST | 5 | 0 | 2026-09-23 | =_xlfn.SWITCH(job_runs[[#This Row],[status]],"SUCCESS",1,"FAILED",-1,0) | =IFERROR(job_runs[[#This Row],[duration_mins]]/job_runs[[#This Row],[avg_retry_secs]],0) | =job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]]
    Row 7: 101 | 1 | SUCCESS | 10 | 1 | 2026-09-24 | =_xlfn.SWITCH(job_runs[[#This Row],[status]],"SUCCESS",1,"FAILED",-1,0) | =IFERROR(job_runs[[#This Row],[duration_mins]]/job_runs[[#This Row],[avg_retry_secs]],0) | =job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]]
    Row 8: 102 | 2 | FAILED | 20 | 6 | 2026-09-24 | =_xlfn.SWITCH(job_runs[[#This Row],[status]],"SUCCESS",1,"FAILED",-1,0) | =IFERROR(job_runs[[#This Row],[duration_mins]]/job_runs[[#This Row],[avg_retry_secs]],0) | =job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]]
    Row 9: 103 | 3 | SUCCESS | 30 | 0 | 2026-09-24 | =_xlfn.SWITCH(job_runs[[#This Row],[status]],"SUCCESS",1,"FAILED",-1,0) | =IFERROR(job_runs[[#This Row],[duration_mins]]/job_runs[[#This Row],[avg_retry_secs]],0) | =job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]]
    Row 10: 104 | 1 | SUCCESS | 40 | 3 | 2026-09-24 | =_xlfn.SWITCH(job_runs[[#This Row],[status]],"SUCCESS",1,"FAILED",-1,0) | =IFERROR(job_runs[[#This Row],[duration_mins]]/job_runs[[#This Row],[avg_retry_secs]],0) | =job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]]
>>>

## X04

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x04.xlsx, as you read it:

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
  Excel Table "jobs", A1:H5
    Headers: job_id | job_name | team | region | code | name_length | third | odd
    Row 2: 1 | nightly_load | data | LON | =UPPER(LEFT(jobs[[#This Row],[job_name]],3))&"-"&jobs[[#This Row],[region]] | =LEN(jobs[[#This Row],[job_name]]) | =ROUND(jobs[[#This Row],[job_id]]/3,2) | =MOD(jobs[[#This Row],[job_id]],2)
    Row 3: 2 | invoice_sync | finance | PAR | =UPPER(LEFT(jobs[[#This Row],[job_name]],3))&"-"&jobs[[#This Row],[region]] | =LEN(jobs[[#This Row],[job_name]]) | =ROUND(jobs[[#This Row],[job_id]]/3,2) | =MOD(jobs[[#This Row],[job_id]],2)
    Row 4: 3 | report_build | finance | NYC | =UPPER(LEFT(jobs[[#This Row],[job_name]],3))&"-"&jobs[[#This Row],[region]] | =LEN(jobs[[#This Row],[job_name]]) | =ROUND(jobs[[#This Row],[job_id]]/3,2) | =MOD(jobs[[#This Row],[job_id]],2)
    Row 5: 4 | cache_warm | web | LON | =UPPER(LEFT(jobs[[#This Row],[job_name]],3))&"-"&jobs[[#This Row],[region]] | =LEN(jobs[[#This Row],[job_name]]) | =ROUND(jobs[[#This Row],[job_id]]/3,2) | =MOD(jobs[[#This Row],[job_id]],2)
>>>

## X05

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x05.xlsx, as you read it:

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
  Excel Table "job_runs", A1:D10
    Headers: run_id | dt | month | days_since
    Row 2: 95 | 2026-09-23 | =MONTH(job_runs[[#This Row],[dt]]) | =DATEDIF(DATE(2026,9,1),job_runs[[#This Row],[dt]],"d")
    Row 3: 96 | 2026-09-23 | =MONTH(job_runs[[#This Row],[dt]]) | =DATEDIF(DATE(2026,9,1),job_runs[[#This Row],[dt]],"d")
    Row 4: 97 | 2026-09-23 | =MONTH(job_runs[[#This Row],[dt]]) | =DATEDIF(DATE(2026,9,1),job_runs[[#This Row],[dt]],"d")
    Row 5: 98 | 2026-09-23 | =MONTH(job_runs[[#This Row],[dt]]) | =DATEDIF(DATE(2026,9,1),job_runs[[#This Row],[dt]],"d")
    Row 6: 99 | 2026-09-23 | =MONTH(job_runs[[#This Row],[dt]]) | =DATEDIF(DATE(2026,9,1),job_runs[[#This Row],[dt]],"d")
    Row 7: 101 | 2026-09-24 | =MONTH(job_runs[[#This Row],[dt]]) | =DATEDIF(DATE(2026,9,1),job_runs[[#This Row],[dt]],"d")
    Row 8: 102 | 2026-09-24 | =MONTH(job_runs[[#This Row],[dt]]) | =DATEDIF(DATE(2026,9,1),job_runs[[#This Row],[dt]],"d")
    Row 9: 103 | 2026-09-24 | =MONTH(job_runs[[#This Row],[dt]]) | =DATEDIF(DATE(2026,9,1),job_runs[[#This Row],[dt]],"d")
    Row 10: 104 | 2026-09-24 | =MONTH(job_runs[[#This Row],[dt]]) | =DATEDIF(DATE(2026,9,1),job_runs[[#This Row],[dt]],"d")
Sheet "region_costs"
  Excel Table "region_costs", A1:E29
    Headers: job_id | cost_cents | region | dt | day
    Row 2: 1 | 120 | eu | 20260911 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 3: 2 | 180 | eu | 20260911 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 4: 3 | 300 | us | 20260911 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 5: 1 | 110 | eu | 20260912 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 6: 1 | 130 | eu | 20260913 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 7: 1 | 120 | eu | 20260914 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 8: 2 | 200 | eu | 20260914 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 9: 3 | 410 | us | 20260914 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 10: 1 | 100 | eu | 20260915 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 11: 2 | 170 | eu | 20260915 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 12: 1 | 250 | eu | 20260916 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 13: 2 | 190 | eu | 20260916 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 14: 1 | 120 | eu | 20260917 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 15: 2 | 160 | eu | 20260917 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 16: 1 | 140 | eu | 20260918 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 17: 2 | 220 | eu | 20260918 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 18: 3 | 120 | us | 20260918 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 19: 1 | 110 | eu | 20260919 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 20: 1 | 120 | eu | 20260920 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 21: 1 | 130 | eu | 20260921 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 22: 2 | 210 | eu | 20260921 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 23: 3 | 330 | us | 20260921 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 24: 1 | 100 | eu | 20260922 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 25: 2 | 180 | eu | 20260922 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 26: 1 | 120 | eu | 20260923 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 27: 2 | 180 | eu | 20260923 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 28: 1 | 100 | eu | 20260924 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
    Row 29: 2 |  | eu | 20260924 | =DATE(LEFT(region_costs[[#This Row],[dt]],4),MID(region_costs[[#This Row],[dt]],5,2),RIGHT(region_costs[[#This Row],[dt]],2))
>>>

## X06

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x06.xlsx, as you read it:

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
    Headers: run_id | job_id | duration_mins | job_name | runs_of_job
    Row 2: 95 | 1 | 12 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =COUNTIFS(job_runs[job_id],job_runs[[#This Row],[job_id]])
    Row 3: 96 | 2 | 18 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =COUNTIFS(job_runs[job_id],job_runs[[#This Row],[job_id]])
    Row 4: 97 | 3 | 30 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =COUNTIFS(job_runs[job_id],job_runs[[#This Row],[job_id]])
    Row 5: 98 | 2 | 15 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =COUNTIFS(job_runs[job_id],job_runs[[#This Row],[job_id]])
    Row 6: 99 | 1 | 5 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =COUNTIFS(job_runs[job_id],job_runs[[#This Row],[job_id]])
    Row 7: 101 | 1 | 10 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =COUNTIFS(job_runs[job_id],job_runs[[#This Row],[job_id]])
    Row 8: 102 | 2 | 20 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =COUNTIFS(job_runs[job_id],job_runs[[#This Row],[job_id]])
    Row 9: 103 | 3 | 30 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =COUNTIFS(job_runs[job_id],job_runs[[#This Row],[job_id]])
    Row 10: 104 | 1 | 40 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[job_name]) | =COUNTIFS(job_runs[job_id],job_runs[[#This Row],[job_id]])
Sheet "jobs"
  Excel Table "jobs", A1:D5
    Headers: job_id | job_name | team | region
    Row 2: 1 | nightly_load | data | LON
    Row 3: 2 | invoice_sync | finance | PAR
    Row 4: 3 | report_build | finance | NYC
    Row 5: 4 | cache_warm | web | LON
>>>

## X07

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x07.xlsx, as you read it:

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
    Headers: run_id | job_id | status | team | region
    Row 2: 95 | 1 | SUCCESS | =VLOOKUP([@job_id],jobs,3,FALSE) | =INDEX(jobs[region],MATCH([@job_id],jobs[job_id],0))
    Row 3: 96 | 2 | SUCCESS | =VLOOKUP([@job_id],jobs,3,FALSE) | =INDEX(jobs[region],MATCH([@job_id],jobs[job_id],0))
    Row 4: 97 | 3 | FAILED | =VLOOKUP([@job_id],jobs,3,FALSE) | =INDEX(jobs[region],MATCH([@job_id],jobs[job_id],0))
    Row 5: 98 | 2 |  | =VLOOKUP([@job_id],jobs,3,FALSE) | =INDEX(jobs[region],MATCH([@job_id],jobs[job_id],0))
    Row 6: 99 | 1 | TEST | =VLOOKUP([@job_id],jobs,3,FALSE) | =INDEX(jobs[region],MATCH([@job_id],jobs[job_id],0))
    Row 7: 101 | 1 | SUCCESS | =VLOOKUP([@job_id],jobs,3,FALSE) | =INDEX(jobs[region],MATCH([@job_id],jobs[job_id],0))
    Row 8: 102 | 2 | FAILED | =VLOOKUP([@job_id],jobs,3,FALSE) | =INDEX(jobs[region],MATCH([@job_id],jobs[job_id],0))
    Row 9: 103 | 3 | SUCCESS | =VLOOKUP([@job_id],jobs,3,FALSE) | =INDEX(jobs[region],MATCH([@job_id],jobs[job_id],0))
    Row 10: 104 | 1 | SUCCESS | =VLOOKUP([@job_id],jobs,3,FALSE) | =INDEX(jobs[region],MATCH([@job_id],jobs[job_id],0))
Sheet "jobs"
  Excel Table "jobs", A1:D5
    Headers: job_id | job_name | team | region
    Row 2: 1 | nightly_load | data | LON
    Row 3: 2 | invoice_sync | finance | PAR
    Row 4: 3 | report_build | finance | NYC
    Row 5: 4 | cache_warm | web | LON
>>>

## X08

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x08.xlsx, as you read it:

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
Sheet "by_job"
  Excel Table "by_job", A1:D4
    Headers: job_id | total_mins | avg_retry | longest
    Row 2: 1 | =SUMIFS(job_runs[duration_mins],job_runs[job_id],by_job[[#This Row],[job_id]]) | =AVERAGEIFS(job_runs[avg_retry_secs],job_runs[job_id],by_job[[#This Row],[job_id]]) | =_xlfn.MAXIFS(job_runs[duration_mins],job_runs[job_id],by_job[[#This Row],[job_id]])
    Row 3: 2 | =SUMIFS(job_runs[duration_mins],job_runs[job_id],by_job[[#This Row],[job_id]]) | =AVERAGEIFS(job_runs[avg_retry_secs],job_runs[job_id],by_job[[#This Row],[job_id]]) | =_xlfn.MAXIFS(job_runs[duration_mins],job_runs[job_id],by_job[[#This Row],[job_id]])
    Row 4: 3 | =SUMIFS(job_runs[duration_mins],job_runs[job_id],by_job[[#This Row],[job_id]]) | =AVERAGEIFS(job_runs[avg_retry_secs],job_runs[job_id],by_job[[#This Row],[job_id]]) | =_xlfn.MAXIFS(job_runs[duration_mins],job_runs[job_id],by_job[[#This Row],[job_id]])
>>>

## X09

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x09.xlsx, as you read it:

<<<
Sheet "Steps": the empty Formula workbook's steps, as it ships.
Sheet "Parameters"
  Excel Table "Parameters", A1:B2
    Headers: name | value
    Row 2: rate | 0.5
Sheet "Keys"
  Excel Table "Keys", A1:B2
    Headers: table | key_columns
    Row 2: job_runs | run_id
Sheet "job_runs"
  Excel Table "job_runs", A1:G10
    Headers: run_id | job_id | duration_mins | avg_retry_secs | team | team_mins | cost
    Row 2: 95 | 1 | 12 | 2 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team]) | =SUMIFS(job_runs[duration_mins],job_runs[team],job_runs[[#This Row],[team]]) | =(job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]])*_xlfn.XLOOKUP("rate",Parameters[name],Parameters[value])
    Row 3: 96 | 2 | 18 | 0 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team]) | =SUMIFS(job_runs[duration_mins],job_runs[team],job_runs[[#This Row],[team]]) | =(job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]])*_xlfn.XLOOKUP("rate",Parameters[name],Parameters[value])
    Row 4: 97 | 3 | 30 | 8 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team]) | =SUMIFS(job_runs[duration_mins],job_runs[team],job_runs[[#This Row],[team]]) | 100
    Row 5: 98 | 2 | 15 |  | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team]) | =SUMIFS(job_runs[duration_mins],job_runs[team],job_runs[[#This Row],[team]]) | =(job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]])*_xlfn.XLOOKUP("rate",Parameters[name],Parameters[value])
    Row 6: 99 | 1 | 5 | 0 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team]) | =SUMIFS(job_runs[duration_mins],job_runs[team],job_runs[[#This Row],[team]]) | =(job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]])*_xlfn.XLOOKUP("rate",Parameters[name],Parameters[value])
    Row 7: 101 | 1 | 10 | 1 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team]) | =SUMIFS(job_runs[duration_mins],job_runs[team],job_runs[[#This Row],[team]]) | =(job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]])*_xlfn.XLOOKUP("rate",Parameters[name],Parameters[value])
    Row 8: 102 | 2 | 20 | 6 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team]) | =SUMIFS(job_runs[duration_mins],job_runs[team],job_runs[[#This Row],[team]]) | =(job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]])*_xlfn.XLOOKUP("rate",Parameters[name],Parameters[value])
    Row 9: 103 | 3 | 30 | 0 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team]) | =SUMIFS(job_runs[duration_mins],job_runs[team],job_runs[[#This Row],[team]]) | =(job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]])*_xlfn.XLOOKUP("rate",Parameters[name],Parameters[value])
    Row 10: 104 | 1 | 40 | 3 | =_xlfn.XLOOKUP(job_runs[[#This Row],[job_id]],jobs[job_id],jobs[team]) | =SUMIFS(job_runs[duration_mins],job_runs[team],job_runs[[#This Row],[team]]) | =(job_runs[[#This Row],[duration_mins]]*60+job_runs[[#This Row],[avg_retry_secs]])*_xlfn.XLOOKUP("rate",Parameters[name],Parameters[value])
Sheet "jobs"
  Excel Table "jobs", A1:D5
    Headers: job_id | job_name | team | region
    Row 2: 1 | nightly_load | data | LON
    Row 3: 2 | invoice_sync | finance | PAR
    Row 4: 3 | report_build | finance | NYC
    Row 5: 4 | cache_warm | web | LON
>>>

## X10

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x10.xlsx, as you read it:

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
    Headers: run_id | job_id | duration_mins | dt | hours | sample
    Row 2: 95 | 1 | 12 | 2026-09-23 | =job_runs[[#This Row],[duration_mins]]/60 | =RAND()
    Row 3: 96 | 2 | 18 | 2026-09-23 | =job_runs[[#This Row],[duration_mins]]/60 | =RAND()
    Row 4: 97 | 3 | 30 | 2026-09-23 | =job_runs[[#This Row],[duration_mins]]/60 | =RAND()
    Row 5: 98 | 2 | 15 | 2026-09-23 | =job_runs[[#This Row],[duration_mins]]/60 | =RAND()
    Row 6: 99 | 1 | 5 | 2026-09-23 | =job_runs[[#This Row],[duration_mins]]/60 | =RAND()
    Row 7: 101 | 1 | 10 | 2026-09-24 | =job_runs[[#This Row],[duration_mins]]/60 | =RAND()
    Row 8: 102 | 2 | 20 | 2026-09-24 | =job_runs[[#This Row],[duration_mins]]/60 | =RAND()
    Row 9: 103 | 3 | 30 | 2026-09-24 | 9 | =RAND()
    Row 10: 104 | 1 | 40 | 2026-09-24 | =job_runs[[#This Row],[duration_mins]]/60 | =RAND()
>>>

## X11

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x11.xlsx, as you read it:

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
  Excel Table "job_runs", A1:D10
    Headers: run_id | duration_mins | pick | scaled
    Row 2: 95 | 12 | =INDIRECT("B"&ROW()) | =job_runs[[#This Row],[duration_mins]]*Summary!$C$2
    Row 3: 96 | 18 | =INDIRECT("B"&ROW()) | =job_runs[[#This Row],[duration_mins]]*Summary!$C$2
    Row 4: 97 | 30 | =INDIRECT("B"&ROW()) | =job_runs[[#This Row],[duration_mins]]*Summary!$C$2
    Row 5: 98 | 15 | =INDIRECT("B"&ROW()) | =job_runs[[#This Row],[duration_mins]]*Summary!$C$2
    Row 6: 99 | 5 | =INDIRECT("B"&ROW()) | =job_runs[[#This Row],[duration_mins]]*Summary!$C$2
    Row 7: 101 | 10 | =INDIRECT("B"&ROW()) | =job_runs[[#This Row],[duration_mins]]*Summary!$C$2
    Row 8: 102 | 20 | =INDIRECT("B"&ROW()) | =job_runs[[#This Row],[duration_mins]]*Summary!$C$2
    Row 9: 103 | 30 | =INDIRECT("B"&ROW()) | =job_runs[[#This Row],[duration_mins]]*Summary!$C$2
    Row 10: 104 | 40 | =INDIRECT("B"&ROW()) | =job_runs[[#This Row],[duration_mins]]*Summary!$C$2
Sheet "Summary"
  C2: 3
  A bar chart
>>>

## X12

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x12.xlsx, as you read it:

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
    Headers: run_id | duration_mins | running | loop | with_tax
    Row 2: 95 | 12 | =SUM(OFFSET(job_runs[[#Headers],[duration_mins]],1,0,ROW()-1,1)) | =job_runs[[#This Row],[loop]]+1 | =job_runs[[#This Row],[duration_mins]]*tax_rate
    Row 3: 96 | 18 | =SUM(OFFSET(job_runs[[#Headers],[duration_mins]],1,0,ROW()-1,1)) | =job_runs[[#This Row],[loop]]+1 | =job_runs[[#This Row],[duration_mins]]*tax_rate
    Row 4: 97 | 30 | =SUM(OFFSET(job_runs[[#Headers],[duration_mins]],1,0,ROW()-1,1)) | =job_runs[[#This Row],[loop]]+1 | =job_runs[[#This Row],[duration_mins]]*tax_rate
    Row 5: 98 | 15 | =SUM(OFFSET(job_runs[[#Headers],[duration_mins]],1,0,ROW()-1,1)) | =job_runs[[#This Row],[loop]]+1 | =job_runs[[#This Row],[duration_mins]]*tax_rate
    Row 6: 99 | 5 | =SUM(OFFSET(job_runs[[#Headers],[duration_mins]],1,0,ROW()-1,1)) | =job_runs[[#This Row],[loop]]+1 | =job_runs[[#This Row],[duration_mins]]*tax_rate
    Row 7: 101 | 10 | =SUM(OFFSET(job_runs[[#Headers],[duration_mins]],1,0,ROW()-1,1)) | =job_runs[[#This Row],[loop]]+1 | =job_runs[[#This Row],[duration_mins]]*tax_rate
    Row 8: 102 | 20 | =SUM(OFFSET(job_runs[[#Headers],[duration_mins]],1,0,ROW()-1,1)) | =job_runs[[#This Row],[loop]]+1 | =job_runs[[#This Row],[duration_mins]]*tax_rate
    Row 9: 103 | 30 | =SUM(OFFSET(job_runs[[#Headers],[duration_mins]],1,0,ROW()-1,1)) | =job_runs[[#This Row],[loop]]+1 | =job_runs[[#This Row],[duration_mins]]*tax_rate
    Row 10: 104 | 40 | =SUM(OFFSET(job_runs[[#Headers],[duration_mins]],1,0,ROW()-1,1)) | =job_runs[[#This Row],[loop]]+1 | =job_runs[[#This Row],[duration_mins]]*tax_rate
Sheet "Summary"
  B3: 0.2
Defined name tax_rate: Summary!$B$3
>>>

## X13

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x13.xlsx, as you read it:

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
  Excel Table "job_runs", A1:D10
    Headers: run_id | job_id | name | doubled
    Row 2: 95 | 1 | =VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE) | =DOUBLE(job_runs[[#This Row],[job_id]])
    Row 3: 96 | 2 | =VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE) | =DOUBLE(job_runs[[#This Row],[job_id]])
    Row 4: 97 | 3 | =VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE) | =DOUBLE(job_runs[[#This Row],[job_id]])
    Row 5: 98 | 2 | =VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE) | =DOUBLE(job_runs[[#This Row],[job_id]])
    Row 6: 99 | 1 | =VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE) | =DOUBLE(job_runs[[#This Row],[job_id]])
    Row 7: 101 | 1 | =VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE) | =DOUBLE(job_runs[[#This Row],[job_id]])
    Row 8: 102 | 2 | =VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE) | =DOUBLE(job_runs[[#This Row],[job_id]])
    Row 9: 103 | 3 | =VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE) | =DOUBLE(job_runs[[#This Row],[job_id]])
    Row 10: 104 | 1 | =VLOOKUP(job_runs[[#This Row],[job_id]],jobs,2,TRUE) | =DOUBLE(job_runs[[#This Row],[job_id]])
Sheet "jobs"
  Excel Table "jobs", A1:D5
    Headers: job_id | job_name | team | region
    Row 2: 1 | nightly_load | data | LON
    Row 3: 2 | invoice_sync | finance | PAR
    Row 4: 3 | report_build | finance | NYC
    Row 5: 4 | cache_warm | web | LON
Defined name DOUBLE: _xlfn.LAMBDA(x,x*2)
>>>

## X14

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x14.xlsx, as you read it:

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
    Headers: run_id | job_id | status | duration_mins | avg_retry_secs | dt | hours
    Row 2: 95 | 1 | SUCCESS | 12 | 2 | 2026-09-23 | =job_runs[[#This Row],[duration_mins]]/60
    Row 3: 96 | 2 | SUCCESS | 18 | 0 | 2026-09-23 | =job_runs[[#This Row],[duration_mins]]/60
    Row 4: 97 | 3 | FAILED | 30 | 8 | 2026-09-23 | =job_runs[[#This Row],[duration_mins]]/60
    Row 5: 98 | 2 |  | 15 |  | 2026-09-23 | =job_runs[[#This Row],[duration_mins]]/60
    Row 6: 99 | 1 | TEST | 5 | 0 | 2026-09-23 | =job_runs[[#This Row],[duration_mins]]/60
    Row 7: 101 | 1 | SUCCESS | 10 | 1 | 2026-09-24 | =job_runs[[#This Row],[duration_mins]]/60
    Row 8: 102 | 2 | FAILED | 20 | 6 | 2026-09-24 | =job_runs[[#This Row],[duration_mins]]/60
    Row 9: 103 | 3 | SUCCESS | 30 | 0 | 2026-09-24 | =job_runs[[#This Row],[duration_mins]]/60
    Row 10: 104 | 1 | SUCCESS | 40 | 3 | 2026-09-24 | =job_runs[[#This Row],[duration_mins]]/60
Sheet "by_job"
  Excel Table "by_job", A1:B4
    Headers: job_id | total_hours
    Row 2: 1 | =SUMIFS(job_runs[hours],job_runs[job_id],by_job[[#This Row],[job_id]])
    Row 3: 2 | =SUMIFS(job_runs[hours],job_runs[job_id],by_job[[#This Row],[job_id]])
    Row 4: 3 | =SUMIFS(job_runs[hours],job_runs[job_id],by_job[[#This Row],[job_id]])
Also in the workbook: a PivotTable on sheet "Pivot", from Table job_runs: rows job_id, values Sum of duration_mins
>>>

## X15

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x15.xlsx, as you read it:

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
Sheet "tblRuns"
  Excel Table "tblRuns", A1:D10
    Headers: Run ID | Job ID | Duration (mins) | Hours
    Row 2: 95 | 1 | 12 | =[@[Duration (mins)]]/60
    Row 3: 96 | 2 | 18 | =[@[Duration (mins)]]/60
    Row 4: 97 | 3 | 30 | =[@[Duration (mins)]]/60
    Row 5: 98 | 2 | 15 | =[@[Duration (mins)]]/60
    Row 6: 99 | 1 | 5 | =[@[Duration (mins)]]/60
    Row 7: 101 | 1 | 10 | =[@[Duration (mins)]]/60
    Row 8: 102 | 2 | 20 | =[@[Duration (mins)]]/60
    Row 9: 103 | 3 | 30 | =[@[Duration (mins)]]/60
    Row 10: 104 | 1 | 40 | =[@[Duration (mins)]]/60
>>>

## X16

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x16.xlsx, as you read it:

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
Sheet "long_runs"
  Excel Table "long_runs", A1:D6, loaded by Power Query "long_runs"
    Headers: run_id | job_id | minutes | hours
    Row 2: 96 | 2 | 18 | 0.3
    Row 3: 97 | 3 | 30 | 0.5
    Row 4: 102 | 2 | 20 | 0.3333333333333333
    Row 5: 103 | 3 | 30 | 0.5
    Row 6: 104 | 1 | 40 | 0.6666666666666666
Power Query "long_runs" (loads into Excel Table "long_runs"):
    let
        Source = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],
        Kept = Table.SelectColumns(Source, {"run_id", "job_id", "duration_mins"}),
        Long = Table.SelectRows(Kept, each [duration_mins] > 15),
        Hours = Table.AddColumn(Long, "hours", each [duration_mins] / 60, type number),
        Renamed = Table.RenameColumns(Hours, {{"duration_mins", "minutes"}})
    in
        Renamed
>>>

## X17

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x17.xlsx, as you read it:

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
Sheet "ok_by_job"
  Excel Table "ok_by_job", A1:C4, loaded by Power Query "ok_by_job"
    Headers: job_id | runs | total_mins
    Row 2: 1 | 3 | 62
    Row 3: 2 | 1 | 18
    Row 4: 3 | 1 | 30
Power Query "ok_runs" (connection only):
    let
        Source = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],
        Succeeded = Table.SelectRows(Source, each [status] = "SUCCESS")
    in
        Succeeded
Power Query "ok_by_job" (loads into Excel Table "ok_by_job"):
    let
        Source = ok_runs,
        Grouped = Table.Group(Source, {"job_id"}, {
            {"runs", each Table.RowCount(_), Int64.Type},
            {"total_mins", each List.Sum([duration_mins]), type number}})
    in
        Grouped
>>>

## X18

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x18.xlsx, as you read it:

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
Sheet "top_runs"
  Excel Table "top_runs", A1:C4, loaded by Power Query "top_runs"
    Headers: run_id | job_name | duration_mins
    Row 2: 104 | nightly_load | 40
    Row 3: 97 | report_build | 30
    Row 4: 103 | report_build | 30
Power Query "top_runs" (loads into Excel Table "top_runs"):
    let
        Source = Excel.CurrentWorkbook(){[Name="job_runs"]}[Content],
        Jobs = Excel.CurrentWorkbook(){[Name="jobs"]}[Content],
        Joined = Table.NestedJoin(Source, {"job_id"}, Jobs, {"job_id"}, "job", JoinKind.LeftOuter),
        Expanded = Table.ExpandTableColumn(Joined, "job", {"job_name"}),
        Sorted = Table.Sort(Expanded, {{"duration_mins", Order.Descending}}),
        Top = Table.FirstN(Sorted, 3),
        Kept = Table.SelectColumns(Top, {"run_id", "job_name", "duration_mins"})
    in
        Kept
>>>

## X19

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x19.xlsx, as you read it:

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
Sheet "all_runs"
  Excel Table "all_runs", A1:C19, loaded by Power Query "all_runs"
    Headers: run_id | job_id | dt
    Row 2: 95 | 1 | 2026-09-23
    Row 3: 95 | 1 | 2026-09-23
    Row 4: 96 | 2 | 2026-09-23
    Row 5: 96 | 2 | 2026-09-23
    Row 6: 97 | 3 | 2026-09-23
    Row 7: 97 | 3 | 2026-09-23
    Row 8: 98 | 2 | 2026-09-23
    Row 9: 98 | 2 | 2026-09-23
    Row 10: 99 | 1 | 2026-09-23
    Row 11: 100 | 3 | 2026-09-23
    Row 12: 101 | 1 | 2026-09-24
    Row 13: 101 | 1 | 2026-09-24
    Row 14: 102 | 2 | 2026-09-24
    Row 15: 102 | 2 | 2026-09-24
    Row 16: 103 | 3 | 2026-09-24
    Row 17: 103 | 3 | 2026-09-24
    Row 18: 104 | 1 | 2026-09-24
    Row 19: 104 | 1 | 2026-09-24
Power Query "all_runs" (loads into Excel Table "all_runs"):
    let
        Scheduled = Excel.CurrentWorkbook(){[Name="scheduler_runs"]}[Content],
        Warehouse = Sql.Database("dwh01", "ops"),
        Runs = Warehouse{[Schema = "ops", Item = "job_runs"]}[Data],
        RunsKept = Table.SelectColumns(Runs, {"run_id", "job_id", "dt"}),
        Combined = Table.Combine({Scheduled, RunsKept})
    in
        Combined
Power Query "holidays" (connection only):
    let
        Source = Csv.Document(Web.Contents("https://calendar.example.com/holidays.csv"))
    in
        Source
>>>

## X20

I attached an Excel workbook. Convert its calculations into Hive SQL.

The attached workbook, x20.xlsx, as you read it:

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
Sheet "alert_pivot"
  Excel Table "alert_pivot", A1:C3, loaded by Power Query "alert_pivot"
    Headers: run_id | high | low
    Row 2: 97 | 1 | 1
    Row 3: 101 | 1 | 2
Power Query "alert_pivot" (loads into Excel Table "alert_pivot"):
    let
        Source = Excel.CurrentWorkbook(){[Name="run_alerts"]}[Content],
        Two = Table.SelectRows(Source, each [run_id] = 97 or [run_id] = 101),
        Kept = Table.SelectColumns(Two, {"run_id", "severity"}),
        Counted = Table.AddColumn(Kept, "n", each 1),
        Pivoted = Table.Pivot(Counted, List.Distinct(Counted[severity]), "severity", "n", List.Sum)
    in
        Pivoted
>>>
