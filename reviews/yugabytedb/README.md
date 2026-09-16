# YugabyteDB publication reviews

This first batch covers the 26 articles published on the Yugabyte blog between
2021-07-23 and 2025-01-31. Articles about YugabyteDB published on other platforms
can be added after this source batch.

## Progress

| Status | Count |
| --- | ---: |
| Verified changed | 9 |
| Verified no change | 17 |
| Total reviewed | 26 |

## Update priority

### High - current readers can be misled

1. [Aurora DSQL](33701-aurora-dsql.md): the article describes the preview. Aurora
	DSQL is now GA and supports foreign keys, sequences, identity columns, and
	locking syntax that the preview comparison listed as absent or limited.
2. [Arctype client](4425-arctype.md): the named client is no longer available from
	the documented site, so readers cannot follow the tutorial as written.
3. [Tablet sizing](23276-tablet-sizing.md): automatic tablet splitting is now the
	default for new universes. Current advice should begin there and reserve manual
	pre-splitting for known initial-scale or distribution requirements.

### Medium - newer features address the problem better

1. [Improving PostgreSQL](29245-improve-postgresql.md): YSQL Connection Manager has
	matured, and true Read Committed is enabled by default for new 2025.2
	`yugabyted` and Aeon universes.
2. [Two data centers](27432-two-data-centers.md): transactional xCluster automatic
	mode is GA and automates supported YSQL DDL replication.
3. [Multi-cloud replication](5530-multi-cloud.md): the same xCluster improvement
	reduces operational work, although asynchronous replication guarantees are
	unchanged.
4. [AWS ClockBound](33645-clockbound.md): the integration demonstrated during the
	2.23.1 period reached GA in YugabyteDB 2025.2.2.
5. [PostgreSQL 15 compatibility](33738-postgresql-15-compatibility.md): the 2.25
	preview line is end-of-life; supported releases now use calendar versioning.
	The representative `gen_random_uuid()` behavior was retested successfully on
	2025.2.6.0.

### Low - historical output only

1. [Check PostgreSQL version](28212-check-version.md): the commands are still
	correct; only the PostgreSQL 15.1 and YugabyteDB 2.17.3.0 example output is old.

No reviewed article was prioritized for a verified bug fix. The material changes
found were product availability, defaults, release maturity, and expanded feature
sets. The other 17 articles do not need a corrective update based on this review.

## Reviews

Each companion note links to the published article and records its evidence. The
snapshot column is the immutable historical source used for comparison.

| Published | Companion review | Snapshot | Status |
| --- | --- | --- | --- |
| 2021-07-23 | [Arctype client](4425-arctype.md) | [4425](../../yugabyte/articles/4425.json) | `verified-changed` |
| 2021-09-03 | [Oracle Kubernetes Engine](4719-oke.md) | [4719](../../yugabyte/articles/4719.json) | `verified-no-change` |
| 2021-10-14 | [Index-only scan](5096-index-only-scan.md) | [5096](../../yugabyte/articles/5096.json) | `verified-no-change` |
| 2021-11-19 | [Sharding and partitioning](5301-sharding-partitioning.md) | [5301](../../yugabyte/articles/5301.json) | `verified-no-change` |
| 2021-12-22 | [Multi-cloud replication](5530-multi-cloud.md) | [5530](../../yugabyte/articles/5530.json) | `verified-changed` |
| 2022-01-19 | [Oracle feature migration](5678-oracle-features.md) | [5678](../../yugabyte/articles/5678.json) | `verified-no-change` |
| 2022-03-10 | [Two-layer architecture](6106-two-layer-architecture.md) | [6106](../../yugabyte/articles/6106.json) | `verified-no-change` |
| 2022-06-17 | [Tablet sizing](23276-tablet-sizing.md) | [23276](../../yugabyte/articles/23276.json) | `verified-changed` |
| 2022-08-25 | [Maximum availability](24061-maximum-availability.md) | [24061](../../yugabyte/articles/24061.json) | `verified-no-change` |
| 2023-04-20 | [Two data centers](27432-two-data-centers.md) | [27432](../../yugabyte/articles/27432.json) | `verified-changed` |
| 2023-05-15 | [Random text](27869-random-text.md) | [27869](../../yugabyte/articles/27869.json) | `verified-no-change` |
| 2023-05-22 | [Generate SQL](27868-generate-sql.md) | [27868](../../yugabyte/articles/27868.json) | `verified-no-change` |
| 2023-06-13 | [Check PostgreSQL version](28212-check-version.md) | [28212](../../yugabyte/articles/28212.json) | `verified-changed` |
| 2023-06-26 | [Conditional WHERE clause](28372-conditional-where.md) | [28372](../../yugabyte/articles/28372.json) | `verified-no-change` |
| 2023-07-10 | [Resource pressure](28484-resource-pressure.md) | [28484](../../yugabyte/articles/28484.json) | `verified-no-change` |
| 2023-07-24 | [Oracle connection errors](28671-oracle-connections.md) | [28671](../../yugabyte/articles/28671.json) | `verified-no-change` |
| 2023-09-06 | [Improving PostgreSQL](29245-improve-postgresql.md) | [29245](../../yugabyte/articles/29245.json) | `verified-changed` |
| 2024-03-26 | [LockManager limitations](31794-lockmanager.md) | [31794](../../yugabyte/articles/31794.json) | `verified-no-change` |
| 2024-04-16 | [Date partitioning](32125-date-partitioning.md) | [32125](../../yugabyte/articles/32125.json) | `verified-no-change` |
| 2024-04-25 | [PgBench custom scripts](32193-pgbench-scripts.md) | [32193](../../yugabyte/articles/32193.json) | `verified-no-change` |
| 2024-06-17 | [Index column order](32452-index-column-order.md) | [32452](../../yugabyte/articles/32452.json) | `verified-no-change` |
| 2024-06-27 | [YugabyteDB resiliency](32486-resiliency.md) | [32486](../../yugabyte/articles/32486.json) | `verified-no-change` |
| 2024-11-25 | [In-place index updates](33594-in-place-index.md) | [33594](../../yugabyte/articles/33594.json) | `verified-no-change` |
| 2024-12-03 | [AWS ClockBound](33645-clockbound.md) | [33645](../../yugabyte/articles/33645.json) | `verified-changed` |
| 2025-01-02 | [Aurora DSQL](33701-aurora-dsql.md) | [33701](../../yugabyte/articles/33701.json) | `verified-changed` |
| 2025-01-31 | [PostgreSQL 15 compatibility](33738-postgresql-15-compatibility.md) | [33738](../../yugabyte/articles/33738.json) | `verified-changed` |
