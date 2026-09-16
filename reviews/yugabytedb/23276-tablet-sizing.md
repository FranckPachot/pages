# Distributed SQL Sharding: How Many Tablets and at What Size?

- Original: [published 2022-06-17](https://www.yugabyte.com/blog/distributed-sql-sharding-how-many-tablets-size/)
- Review cutoff: 2026-03-06
- Status: `verified-changed`
- Evidence: documentation and release history only; no tablet-splitting test

## What was reviewed

The article explains initial tablet counts, tablet size, manual pre-splitting, and the trade-off between parallelism and per-tablet overhead.

## What changed

The trade-off remains, but manual sizing is less central than it was in 2022. Automatic tablet splitting has been enabled by default for new universes since YugabyteDB 2.18, so current guidance should start with automatic splitting and introduce pre-splitting only for known initial scale or write-distribution needs.

## Evidence

- [Tablet splitting](https://docs.yugabyte.com/stable/architecture/docdb-sharding/tablet-splitting/)
- [Create tables with tablets](https://docs.yugabyte.com/stable/explore/going-beyond-sql/data-sharding/)

## Companion update

The tablet-size and overhead trade-offs in this 2022 article still exist, but the default operating model changed. Automatic tablet splitting has been enabled by default for new universes since YugabyteDB 2.18, including current 2025.2 deployments. Pre-split when the initial workload or key distribution requires immediate parallelism; otherwise let splitting and balancing adapt as data grows.