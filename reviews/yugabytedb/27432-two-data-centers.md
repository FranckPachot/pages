# Achieving High Availability and Disaster Recovery with Two Data Centers

- Original: [published 2023-04-20](https://www.yugabyte.com/blog/high-availability-disaster-recovery-two-data-centers/)
- Review cutoff: 2026-03-06
- Status: `verified-changed`
- Evidence: documentation and release notes only; no failover test

## What was reviewed

The YugabyteDB 2.17 article combines a local quorum-bearing topology with a second-site xCluster replica to address high availability and disaster recovery across two sites.

## What changed

The quorum constraint behind the topology is unchanged. The xCluster workflow has matured: transactional automatic mode reached GA in YugabyteDB 2025.2.1 and automates supported YSQL DDL replication, while planned switchover and unplanned failover remain distinct procedures.

## Evidence

- [xCluster deployments](https://docs.yugabyte.com/stable/deploy/multi-dc/async-replication/)
- [Automatic transactional xCluster setup](https://docs.yugabyte.com/stable/deploy/multi-dc/async-replication/async-transactional-setup-automatic/)
- [YugabyteDB 2025.2 release notes](https://docs.yugabyte.com/stable/releases/ybdb-releases/v2025.2/)

## Companion update

The two-site constraint explained with YugabyteDB 2.17 still applies: synchronous consensus needs a quorum and cannot be made symmetric across only two failure domains. For disaster recovery, xCluster is substantially easier to operate now; automatic transactional mode reached GA in YugabyteDB 2025.2.1 and replicates supported YSQL DDL. Planned switchover and unplanned failover still require separate procedures and should be tested against the required RPO and RTO.