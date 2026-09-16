# Is My PostgreSQL Database Experiencing CPU, RAM, or I/O Pressure?

- Original: [published 2023-07-10](https://www.yugabyte.com/blog/identify-cpu-ram-io-pressure-postgresql/)
- Review cutoff: 2026-03-06
- Status: `verified-no-change`
- Evidence: documentation only; no production diagnostic capture

## What was reviewed

The article correlates database activity and waits with operating-system CPU, memory, and I/O observations rather than diagnosing pressure from one metric alone.

## Finding

That diagnostic method remains valid. PostgreSQL and YugabyteDB expose richer observability now, but wait events, query activity, and host metrics still need to be interpreted together and over the same time interval.

## Evidence

- [PostgreSQL cumulative statistics](https://www.postgresql.org/docs/18/monitoring-stats.html)
- [YugabyteDB metrics](https://docs.yugabyte.com/stable/launch-and-manage/monitor-and-alert/metrics/)
- [YugabyteDB Active Session History](https://docs.yugabyte.com/stable/launch-and-manage/monitor-and-alert/active-session-history-monitor/)

## Companion update

The diagnostic principle remains current: correlate SQL activity and wait events with host CPU, memory, and storage metrics over the same period. YugabyteDB 2025.2 adds product-specific metrics and Active Session History views, but no single high utilization value proves the database is resource-bound. This review validates the method from documentation and does not diagnose a particular system.