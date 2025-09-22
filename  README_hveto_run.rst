==============================
Scheduled runs and backfilling
==============================

At the LIGO Hanford and Livngston interferometer sites
hveto is scheduled to run 4 times per day:

- Every 8 hours covering from 00:00 UTC to 08:00, 16:00,
  and 00:00 UTC the next day.
- Once a day covering the previous 7 (UTC) days

There are other situations where multiple runs are needed
such as backfilling a time when problems prevented the
normally scheduled run.

`hveto_run` is a program used to create and [optionally]
submit condor jobs to hveto.

