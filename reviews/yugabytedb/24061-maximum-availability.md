# Comparing the Maximum Availability of YugabyteDB and Oracle Database

- Original: [published 2022-08-25](https://www.yugabyte.com/blog/comparing-the-maximum-availability-of-yugabytedb-and-oracle-database/)
- Review cutoff: 2026-03-06
- Status: `verified-no-change`
- Evidence: architecture documentation only; no failure injection

## What was reviewed

The article contrasts shared-storage and instance-failover approaches with YugabyteDB's tablet-level Raft replication and quorum availability.

## Finding

The YugabyteDB mechanism remains current: each tablet has replicated peers, a leader, and quorum-based consensus. Exact recovery times and availability outcomes still depend on topology, failure detection, clients, and workload, so the architecture should not be read as a universal timing guarantee.

## Evidence

- [Raft replication](https://docs.yugabyte.com/stable/architecture/docdb-replication/raft/)
- [Fault tolerance](https://docs.yugabyte.com/stable/explore/fault-tolerance/)
- [Transaction availability](https://docs.yugabyte.com/stable/explore/fault-tolerance/transaction-availability/)

## Companion update

YugabyteDB 2025.2 still provides tablet-level Raft replication and quorum-based availability as described. This remains architecturally different from promoting a single standby database or failing over a shared-storage instance. Treat any recovery-time figure as topology- and client-dependent unless it is reproduced under the intended deployment conditions; this review did not run failure injection.