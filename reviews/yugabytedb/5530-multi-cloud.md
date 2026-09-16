# Multi-Cloud Distributed SQL: Avoiding Region Failure with YugabyteDB

- Original: [published 2021-12-22](https://www.yugabyte.com/blog/avoiding-region-failure-with-multi-cloud-distributed-sql/)
- Review cutoff: 2026-03-06
- Status: `verified-changed`
- Evidence: documentation and release notes only; no failover test

## What was reviewed

The article contrasts synchronous consensus replication with asynchronous cross-cluster replication for regional resilience.

## What changed

The architectural trade-off is unchanged, but xCluster operations have advanced. YugabyteDB 2025.2.1 documents automatic transactional xCluster mode as generally available, including automated YSQL DDL replication.

## Evidence

- [Synchronous replication](https://docs.yugabyte.com/stable/architecture/docdb-replication/replication/)
- [xCluster replication](https://docs.yugabyte.com/stable/architecture/docdb-replication/async-replication/)
- [YugabyteDB 2025.2 release notes](https://docs.yugabyte.com/stable/releases/ybdb-releases/v2025.2/)

## Companion update

The consistency and latency trade-offs described in 2021 remain: synchronous Raft replication and asynchronous xCluster replication solve different failure-domain problems. Since publication, transactional xCluster automatic mode reached GA in YugabyteDB 2025.2.1 and can automate YSQL DDL replication. That reduces operating work but does not turn asynchronous replication into zero-data-loss synchronous consensus.