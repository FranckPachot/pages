# Distributed SQL: Sharding and Partitioning in YugabyteDB

- Original: [published 2021-11-19](https://www.yugabyte.com/blog/distributed-sql-essentials-sharding-and-partitioning-in-yugabytedb/)
- Review cutoff: 2026-03-06
- Status: `verified-no-change`
- Evidence: documentation only; no cluster test

## What was reviewed

The article distinguishes SQL table partitioning from DocDB sharding into tablets and from the SST files used by the storage engine.

## Finding

Those layers and terms remain current. User tables are still implicitly managed as tablets, with hash and range sharding supported by DocDB.

## Evidence

- [DocDB sharding](https://docs.yugabyte.com/stable/architecture/docdb-sharding/)
- [Hash and range sharding](https://docs.yugabyte.com/stable/architecture/docdb-sharding/sharding/)
- [LSM and SST storage](https://docs.yugabyte.com/stable/architecture/docdb/lsm-sst/)

## Companion update

The distinction made in this 2021 article remains accurate in YugabyteDB 2025.2: SQL partitioning is a schema-level choice, DocDB distributes data in tablets, and tablet storage uses LSM/SST structures. Tablet splitting has matured, but it refines automatic shard management rather than replacing this model.