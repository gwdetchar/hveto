This directory contains tempplates for Condor cron jobs to run hveto 
on a daily basis as used by the Detchar account.

These templates are used to create the actual ssubmit files in 
${HOME}/etc/ligo-monitors/condor

- hveto-daily.sub - runs 3 times per day over 8, 16, and 24 hrs since 00:00 UTC
- hveto-weekly.su - runs once per day and covers the previous 7 days from
  00:00 to 00:00 UTc