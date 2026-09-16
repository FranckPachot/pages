# Advanced PostgreSQL Partitioning by Date with YugabyteDB Auto Sharding

- Original: [published 2024-04-16](https://www.yugabyte.com/blog/postgresql-advanced-partitioning-by-date/)
- Review cutoff: 2026-03-06
- Status: `verified-no-change`
- Evidence: documentation only; no SQL execution

## What was reviewed

The article uses date partitioning for lifecycle and query semantics while allowing YugabyteDB to shard data automatically and distribute secondary indexes independently.

## Finding

That separation remains current. YSQL supports PostgreSQL-style table partitioning, while DocDB tablets handle physical distribution; non-colocated and non-copartitioned global indexes have sharding independent of the base table.

## Evidence

- [YSQL table partitioning](https://docs.yugabyte.com/stable/explore/ysql-language-features/advanced-features/partitions/)
- [YugabyteDB data sharding](https://docs.yugabyte.com/stable/explore/going-beyond-sql/data-sharding/)
- [YSQL secondary indexes](https://docs.yugabyte.com/stable/explore/ysql-language-features/indexes-constraints/secondary-indexes-ysql/)

## Companion update

The 2024 design remains valid in YugabyteDB 2025.2: use date partitions when they express retention, maintenance, or query boundaries, and let tablets provide physical distribution. Global secondary indexes are still distributed structures whose sharding is independent of the base table unless they are explicitly colocated or copartitioned. This avoids forcing every access path to share the table's partition key.