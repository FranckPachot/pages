# How to Enhance Database Performance Testing Using Custom SQL Scripts in PgBench

- Original: [published 2024-04-25](https://www.yugabyte.com/blog/pgbench-custom-sql-scripts/)
- Review cutoff: 2026-03-06
- Status: `verified-no-change`
- Evidence: PostgreSQL documentation only; no benchmark rerun

## What was reviewed

The article recommends custom pgbench scripts for workloads that differ from the built-in TPC-B-like transaction and explains how round trips and contention shape results.

## Finding

The recommendation remains current. PostgreSQL 18 still describes the default as only loosely based on TPC-B, supports custom scripts with `-f`, and warns that short or poorly scaled tests can produce meaningless numbers.

## Evidence

- [PostgreSQL 18 pgbench](https://www.postgresql.org/docs/18/pgbench.html)

## Companion update

The methodology remains current with PostgreSQL 18 clients and YugabyteDB 2025.2. pgbench still defaults to a TPC-B-like script and accepts application-specific transaction scripts with `-f`; those scripts should model the intended concurrency, data distribution, round trips, and retry policy. This review confirms the tool semantics from documentation and does not reproduce the article's performance numbers.