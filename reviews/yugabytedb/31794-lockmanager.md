# Solving PostgreSQL Indexes, Partitioning, and LockManager Limitations

- Original: [published 2024-03-26](https://www.yugabyte.com/blog/postgresql-indexes-partitioning-lockmanager-limitations/)
- Review cutoff: 2026-03-06
- Status: `verified-no-change`
- Evidence: architecture documentation only; no contention reproduction

## What was reviewed

The article explains how large PostgreSQL partition hierarchies create many relation objects and locks, then contrasts that with YugabyteDB tablets and global indexes.

## Finding

The mechanism behind the comparison remains. YugabyteDB tables and global indexes are distributed as tablets rather than requiring each storage shard to be represented as a SQL partition, so sharding and semantic table partitioning remain separate choices.

## Evidence

- [PostgreSQL explicit locking](https://www.postgresql.org/docs/18/explicit-locking.html)
- [PostgreSQL partitioning caveats](https://www.postgresql.org/docs/18/ddl-partitioning.html)
- [YugabyteDB sharding](https://docs.yugabyte.com/stable/architecture/docdb-sharding/sharding/)
- [YSQL secondary indexes](https://docs.yugabyte.com/stable/explore/ysql-language-features/indexes-constraints/secondary-indexes-ysql/)

## Companion update

The design distinction remains valid in PostgreSQL 18 and YugabyteDB 2025.2. PostgreSQL partitioning creates relations that participate in relation locking, while YugabyteDB can split and distribute a logical table and its global indexes as tablets without exposing each shard as a SQL partition. The severity of lock contention depends on schema and workload; this review did not reproduce the production incident or benchmark a partition count.