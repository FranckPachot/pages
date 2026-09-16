# How Does YugabyteDB's Two-Layer Architecture Work?

- Original: [published 2022-03-10](https://www.yugabyte.com/blog/distributed-sql-yugabytedb-two-layer-architecture/)
- Review cutoff: 2026-03-06
- Status: `verified-no-change`
- Evidence: documentation only; no runtime test

## What was reviewed

The article describes the PostgreSQL-compatible YSQL query layer above the distributed DocDB storage, transaction, sharding, and replication layers.

## Finding

This remains the documented architecture. The query and storage layers have gained features, but their ownership and interaction have not been replaced.

## Evidence

- [Query layer](https://docs.yugabyte.com/stable/architecture/query-layer/)
- [DocDB](https://docs.yugabyte.com/stable/architecture/docdb/)
- [Distributed transactions](https://docs.yugabyte.com/stable/architecture/transactions/distributed-txns/)

## Companion update

The two-layer model described in 2022 remains the basis of YugabyteDB 2025.2. YSQL supplies PostgreSQL-compatible parsing, planning, and execution, while DocDB owns distributed storage, sharding, replication, and transaction coordination. Later optimizer and compatibility work extends these layers without changing the central explanation.