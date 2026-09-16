# YugabyteDB Resiliency vs. PostgreSQL High Availability Solutions

- Original: [published 2024-06-27](https://www.yugabyte.com/blog/yugabytedb-resiliency-vs-postgresql-ha-solutions/)
- Review cutoff: 2026-03-06
- Status: `verified-no-change`
- Evidence: architecture documentation only; no failure injection

## What was reviewed

The article contrasts leader election for individual Raft-replicated tablets with primary-instance promotion in common PostgreSQL high-availability designs.

## Finding

The architectural distinction remains valid. YugabyteDB still replicates tablets with Raft and can continue when a quorum remains, but observed recovery and application interruption depend on failure detection, leader placement, connection behavior, and workload.

## Evidence

- [Raft replication](https://docs.yugabyte.com/stable/architecture/docdb-replication/raft/)
- [YugabyteDB node failures](https://docs.yugabyte.com/stable/explore/fault-tolerance/)
- [YugabyteDB smart drivers](https://docs.yugabyte.com/stable/develop/drivers-orms/smart-drivers/)

## Companion update

The tablet-level Raft resilience described in 2024 remains central to YugabyteDB 2025.2. A failed node does not require promoting one replacement database instance when tablet quorums remain, but clients can still observe retries or connection interruption during failure detection and leader movement. The article's measured recovery time belongs to its test conditions; this documentation review did not reproduce that timing.