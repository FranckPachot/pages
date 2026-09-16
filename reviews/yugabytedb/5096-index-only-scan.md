# How a Distributed SQL Database Boosts Secondary Index Queries with Index Only Scan

- Original: [published 2021-10-14](https://www.yugabyte.com/blog/how-a-distributed-sql-database-boosts-secondary-index-queries-with-index-only-scan/)
- Review cutoff: 2026-03-06
- Status: `verified-no-change`
- Evidence: documentation only; no query-plan reproduction

## What was reviewed

The article explains why a covering secondary index can avoid the additional distributed table lookup of an ordinary index scan.

## Finding

The mechanism is unchanged. Current documentation still defines `INCLUDE` columns as covering columns stored in the index specifically to avoid a trip to the table.

## Evidence

- [YSQL secondary indexes](https://docs.yugabyte.com/stable/explore/ysql-language-features/indexes-constraints/secondary-indexes-ysql/)
- [YSQL covering indexes](https://docs.yugabyte.com/stable/explore/ysql-language-features/indexes-constraints/covering-index-ysql/)

## Companion update

The index-only-scan principle described here still applies to YugabyteDB 2025.2. YSQL continues to support covering indexes with `INCLUDE`, allowing selected columns to be read from the global secondary index without an additional table lookup. Planner and costing work since 2021 does not change that underlying access-path explanation.