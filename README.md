DBStats Database Reporting Tool
===============================

The dbstats package collects database activity statistics over time, and displays
the data in a user friendly format.

- Only PostgreSQL is supported at the moment
- A worker process is run on the database server where it collects query logs
- A Django app stores those logs and displays the data

Licensed under the MIT license.

TODO
----
- Trim down the client process, just use iostat and vmstat to get memory and disk usage.
