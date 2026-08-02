---
title: How to Build a Small Database Lab
description: A source-grounded method for reproducing database behavior with disposable containers, small fixtures, and observable experiments.
---

# How to Build a Small Database Lab

A useful database lab is not a miniature production system. It is the smallest environment that can disprove one explanation of a behavior. Keep the schema recognizable, exaggerate the relevant data distribution, expose the engine's evidence, and make the whole experiment disposable.

## The lab contract

Before running a command, write down:

- **Question:** the single behavior to understand.
- **Hypothesis:** one explanation that can be proven wrong.
- **Controlled variables:** image version, settings, schema, row count, data distribution, and topology.
- **Discriminating observation:** the plan counter, lock, row version, RPC, log position, or failover event that differs if the hypothesis is false.
- **Cleanup:** how to return to an empty machine.

Use these rules:

1. Pin an image digest or version when preserving evidence. `latest` is acceptable only for exploration when the resolved image ID and database version are recorded.
2. Start with product defaults. Add one setting only when that setting is the subject of the test.
3. Generate enough rows to reveal the behavior, but not so many that setup dominates the experiment.
4. Make skew intentional. Uniform random data hides many optimizer and contention problems.
5. Capture estimates and actual work separately. A plan without runtime counters tests the optimizer forecast; runtime counters test execution.
6. Use two named sessions for concurrency. Mark the exact point where each transaction must pause.
7. Do not call container timings benchmarks. They explain relative mechanics on one machine, not production capacity.
8. Preserve the commands, output, database version, image ID, and host architecture with the conclusion.

Record the environment before each experiment:

```text
Question:
Hypothesis:
Database version:
Container image and digest:
Host OS and architecture:
Schema and seed:
Changed settings:
Observation:
Result:
```

## Shared relational fixture

Use the same logical model in PostgreSQL, Oracle Database, and YugabyteDB. It supports selectivity, composite indexes, pagination, locking, MVCC, uniqueness, and foreign-key experiments.

```sql
CREATE TABLE lab_account (
  account_id BIGINT PRIMARY KEY,
  segment VARCHAR(12) NOT NULL,
  balance DECIMAL(19,2) NOT NULL,
  updated_at TIMESTAMP NOT NULL
);

CREATE TABLE lab_event (
  tenant_id BIGINT NOT NULL,
  event_id BIGINT NOT NULL,
  account_id BIGINT NOT NULL,
  category VARCHAR(12) NOT NULL,
  created_at TIMESTAMP NOT NULL,
  payload VARCHAR(200),
  PRIMARY KEY (tenant_id, event_id),
  FOREIGN KEY (account_id) REFERENCES lab_account(account_id)
);

CREATE INDEX lab_account_segment_ix
  ON lab_account (segment, account_id);

CREATE INDEX lab_event_page_ix
  ON lab_event (tenant_id, created_at DESC, event_id DESC);
```

The seed should create these deliberate properties:

- 10,000 accounts: 9,900 `COMMON` and 100 `RARE`.
- 100,000 events across ten tenants.
- Several events with identical timestamps, so pagination needs `event_id` as a tie-breaker.
- One account selected for concurrent updates.

## PostgreSQL

Replace `<PG_TAG>` with a version such as `18`, and keep that value in the lab record.

```shell
docker run --name pg-lab --rm -d -e POSTGRES_PASSWORD=labpass -p 5432:5432 postgres:<PG_TAG>
docker exec pg-lab pg_isready -U postgres
docker exec -it pg-lab psql -U postgres
```

Repeat `pg_isready` until it reports that the server accepts connections. Inside `psql`, create and seed the shared fixture:

```sql
CREATE TABLE lab_account (
  account_id bigint PRIMARY KEY,
  segment text NOT NULL,
  balance numeric(19,2) NOT NULL,
  updated_at timestamp NOT NULL
);

INSERT INTO lab_account
SELECT id,
       CASE WHEN id <= 9900 THEN 'COMMON' ELSE 'RARE' END,
       1000.00,
       timestamp '2026-01-01' + (id % 30) * interval '1 day'
FROM generate_series(1, 10000) AS id;

CREATE TABLE lab_event (
  tenant_id bigint NOT NULL,
  event_id bigint NOT NULL,
  account_id bigint NOT NULL REFERENCES lab_account,
  category text NOT NULL,
  created_at timestamp NOT NULL,
  payload text,
  PRIMARY KEY (tenant_id, event_id)
);

INSERT INTO lab_event
SELECT 1 + (id % 10), id, 1 + (id % 10000),
       CASE WHEN id % 100 = 0 THEN 'ERROR' ELSE 'INFO' END,
       timestamp '2026-01-01' + (id / 10) * interval '1 second',
       repeat('x', 40)
FROM generate_series(1, 100000) AS id;

CREATE INDEX lab_account_segment_ix ON lab_account (segment, account_id);
CREATE INDEX lab_event_page_ix
  ON lab_event (tenant_id, created_at DESC, event_id DESC);
ANALYZE;
```

Observe forecasts and physical work together:

```sql
EXPLAIN (ANALYZE, BUFFERS, WAL, SETTINGS, SUMMARY)
SELECT * FROM lab_account WHERE segment = 'RARE';

SELECT relname, indexrelname, idx_scan
FROM pg_stat_user_indexes
WHERE relname LIKE 'lab_%';
```

PostgreSQL does not provide a SQL command that makes a normal shared-buffer run equivalent to a cold operating-system cache. Prefer warm-cache comparisons, record cache state, or restart an isolated disposable container when cold-start behavior is the actual question.

Cleanup:

```shell
docker rm -f pg-lab
```

## Oracle Database Free

Oracle Container Registry may require authentication and acceptance of image terms. Replace `<ORACLE_TAG>` with an available pinned Database Free tag. The image is larger and takes longer to become ready than the other single-node labs.

```shell
docker login container-registry.oracle.com
docker run --name ora-lab -d -p 1521:1521 -e ORACLE_PWD=LabPassword23 container-registry.oracle.com/database/free:<ORACLE_TAG>
docker logs ora-lab
docker exec -it ora-lab sqlplus system/LabPassword23@FREEPDB1
```

Wait for the readiness message in the container log before connecting. Inside SQL*Plus:

```sql
CREATE TABLE lab_account (
  account_id NUMBER(19) PRIMARY KEY,
  segment VARCHAR2(12) NOT NULL,
  balance NUMBER(19,2) NOT NULL,
  updated_at TIMESTAMP NOT NULL
);

INSERT INTO lab_account
SELECT level,
       CASE WHEN level <= 9900 THEN 'COMMON' ELSE 'RARE' END,
       1000.00,
       TIMESTAMP '2026-01-01 00:00:00' + NUMTODSINTERVAL(MOD(level,30),'DAY')
FROM dual CONNECT BY level <= 10000;

CREATE TABLE lab_event (
  tenant_id NUMBER(19) NOT NULL,
  event_id NUMBER(19) NOT NULL,
  account_id NUMBER(19) NOT NULL REFERENCES lab_account(account_id),
  category VARCHAR2(12) NOT NULL,
  created_at TIMESTAMP NOT NULL,
  payload VARCHAR2(200),
  PRIMARY KEY (tenant_id, event_id)
);

INSERT INTO lab_event
SELECT 1 + MOD(level,10), level, 1 + MOD(level,10000),
       CASE WHEN MOD(level,100)=0 THEN 'ERROR' ELSE 'INFO' END,
       TIMESTAMP '2026-01-01 00:00:00' + NUMTODSINTERVAL(TRUNC(level/10),'SECOND'),
       RPAD('x',40,'x')
FROM dual CONNECT BY level <= 100000;

CREATE INDEX lab_account_segment_ix ON lab_account(segment, account_id);
CREATE INDEX lab_event_page_ix
  ON lab_event(tenant_id, created_at DESC, event_id DESC);
COMMIT;

BEGIN
  DBMS_STATS.GATHER_SCHEMA_STATS(USER, cascade => TRUE);
END;
/
```

Use runtime row-source statistics rather than `EXPLAIN PLAN` alone:

```sql
ALTER SESSION SET statistics_level = ALL;

SELECT /* lab_rare */ *
FROM lab_account
WHERE segment = 'RARE';

SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY_CURSOR(NULL, NULL, 'ALLSTATS LAST +BUFFERS'));
```

Cleanup:

```shell
docker rm -f ora-lab
```

## YugabyteDB

Use one node and replication factor one for SQL semantics, plans, indexes, and transaction experiments. Use at least three nodes only when the question involves quorum, leader movement, node failure, placement, or network distance. Replace `<YB_TAG>` with a pinned version.

```shell
docker run --name yb-lab --rm -d -p 5433:5433 -p 7000:7000 -p 15433:15433 yugabytedb/yugabyte:<YB_TAG> bin/yugabyted start --background=false
docker exec yb-lab ysqlsh -h yb-lab -c "select version()"
docker exec -it yb-lab ysqlsh -h yb-lab
```

The shared PostgreSQL fixture runs in YSQL with one physical change that makes distribution explicit:

```sql
CREATE TABLE lab_account (
  account_id bigint PRIMARY KEY,
  segment text NOT NULL,
  balance numeric(19,2) NOT NULL,
  updated_at timestamp NOT NULL
);

INSERT INTO lab_account
SELECT id,
       CASE WHEN id <= 9900 THEN 'COMMON' ELSE 'RARE' END,
       1000.00,
       timestamp '2026-01-01' + (id % 30) * interval '1 day'
FROM generate_series(1, 10000) AS id;

CREATE TABLE lab_event (
  tenant_id bigint NOT NULL,
  event_id bigint NOT NULL,
  account_id bigint NOT NULL REFERENCES lab_account,
  category text NOT NULL,
  created_at timestamp NOT NULL,
  payload text,
  PRIMARY KEY ((tenant_id) HASH, event_id)
);

INSERT INTO lab_event
SELECT 1 + (id % 10), id, 1 + (id % 10000),
       CASE WHEN id % 100 = 0 THEN 'ERROR' ELSE 'INFO' END,
       timestamp '2026-01-01' + (id / 10) * interval '1 second',
       repeat('x', 40)
FROM generate_series(1, 100000) AS id;

CREATE INDEX lab_account_segment_ix ON lab_account (segment, account_id);
CREATE INDEX lab_event_page_ix
  ON lab_event (tenant_id HASH, created_at DESC, event_id DESC);
ANALYZE;
```

Observe network and storage work in addition to PostgreSQL-style operators:

```sql
EXPLAIN (ANALYZE, DIST, COSTS OFF)
SELECT * FROM lab_account WHERE segment = 'RARE';
```

For a three-node lab, use a maintained Compose definition and record replication factor, placement, leaders, and injected latency. Do not infer failover or distributed latency from a one-node container. The publication sources below include compact CI images and multi-node Docker patterns.

Cleanup:

```shell
docker rm -f yb-lab
```

## MongoDB

Use a single-node replica set even for a small transaction lab: transactions and retry behavior require replica-set semantics. Replace `<MONGO_TAG>` with a pinned version.

```shell
docker run --name mongo-lab --rm -d -p 27017:27017 mongo:<MONGO_TAG> --replSet rs0 --bind_ip_all
docker exec mongo-lab mongosh --quiet --eval "rs.initiate({_id:'rs0',members:[{_id:0,host:'localhost:27017'}]})"
docker exec mongo-lab mongosh --quiet --eval "rs.status().myState"
docker exec -it mongo-lab mongosh "mongodb://localhost:27017/?replicaSet=rs0"
```

Wait until `myState` is `1`, then create an equivalent document fixture:

```javascript
use lab

db.account.drop()
db.event.drop()

db.account.insertMany(
  Array.from({length: 10000}, (_, offset) => {
    const id = offset + 1;
    return {
      _id: id,
      segment: id <= 9900 ? "COMMON" : "RARE",
      balance: NumberDecimal("1000.00"),
      updatedAt: new Date(Date.UTC(2026, 0, 1 + (id % 30)))
    };
  })
)

for (let first = 1; first <= 100000; first += 1000) {
  db.event.insertMany(
    Array.from({length: 1000}, (_, offset) => {
      const id = first + offset;
      return {
        _id: id,
        tenantId: 1 + (id % 10),
        accountId: 1 + (id % 10000),
        category: id % 100 === 0 ? "ERROR" : "INFO",
        createdAt: new Date(Date.UTC(2026, 0, 1, 0, 0, Math.floor(id / 10))),
        payload: "x".repeat(40)
      };
    })
  )
}

db.account.createIndex({segment: 1, _id: 1})
db.event.createIndex({tenantId: 1, createdAt: -1, _id: -1})
```

Observe examined keys and documents rather than elapsed time alone:

```javascript
db.account.find({segment: "RARE"}).explain("executionStats")
db.event.find({tenantId: 7})
  .sort({createdAt: -1, _id: -1})
  .limit(20)
  .explain("executionStats")
```

Use three members only for elections, majority acknowledgement, rollback, or failover. A three-member Compose lab must use stable container DNS names in `rs.initiate()`; clients must also be able to resolve the advertised names.

Cleanup:

```shell
docker rm -f mongo-lab
```

## Experiment cards

### Selectivity and cardinality

**Hypothesis:** the optimizer chooses different access paths for `COMMON` and `RARE` because their cardinalities differ.

Run both predicates before and after statistics collection. Compare estimated rows, actual rows, pages or documents examined, and the chosen access path. Do not compare only elapsed time.

### Composite index and stable pagination

Compare deep offset pagination with a keyset boundary:

```sql
SELECT * FROM lab_event
WHERE tenant_id = 7
ORDER BY created_at DESC, event_id DESC
OFFSET 5000 ROWS FETCH NEXT 20 ROWS ONLY;

SELECT * FROM lab_event
WHERE tenant_id = 7
  AND (created_at, event_id) < (:last_created_at, :last_event_id)
ORDER BY created_at DESC, event_id DESC
FETCH FIRST 20 ROWS ONLY;
```

Adapt `LIMIT`/`OFFSET` syntax to PostgreSQL and YugabyteDB. MongoDB uses the same principle with a compound `$or` boundary. Verify total ordering with the unique final key.

### Locking with two sessions

Open two clients and label them before starting.

```sql
-- Session A
BEGIN;
UPDATE lab_account SET balance = balance + 10 WHERE account_id = 42;
-- Pause without committing.

-- Session B
BEGIN;
UPDATE lab_account SET balance = balance - 5 WHERE account_id = 42;
-- Observe the wait or conflict here.

-- Session A
COMMIT;

-- Session B
COMMIT;
```

Observe direct blockers and transaction age with `pg_stat_activity` plus `pg_blocking_pids()` in PostgreSQL, `V$SESSION` and `V$LOCK` in Oracle, the distributed lock views in YugabyteDB, or `$currentOp` in MongoDB. Waiting is evidence of the invariant being coordinated, not automatically a defect.

### MVCC and uniqueness

Keep one transaction open on an old snapshot while another updates a row. Query the row from both sessions and inspect product-specific version evidence. For uniqueness, have two sessions insert the same key before either commits; record whether the second waits, fails immediately, or is restarted.

Do not persist PostgreSQL `ctid`, Oracle `rowid`, or WiredTiger record identifiers as application identity. They are diagnostic coordinates for the immediate experiment.

### Distribution, replication, and failure

A single container cannot answer a high-availability question. Before stopping a node, state:

- replication factor and acknowledgement policy;
- which member or tablet leader owns the write path;
- expected behavior for in-flight and ambiguous commits;
- the observation that proves recovery, including client reconnection;
- the data check that proves the acknowledged-write contract.

Inject one failure at a time. Container stop, process kill, network delay, network partition, disk-full, and clock skew test different mechanisms.

## Source trail

These publications demonstrate the small-lab method and the mechanics covered here. Use the local snapshot when an external page changes.

- [B-tree block split: what's the impact?](https://dev.to/franckpachot/b-tree-block-split-whats-the-impact-1i9c) ([snapshot](devto/articles/4212032.json))
- [Following ROWIDs Through an Oracle Unique Index Update](https://dev.to/franckpachot/following-rowids-through-an-oracle-unique-index-update-2lc) ([snapshot](devto/articles/4235447.json))
- [PostgreSQL resolves uniqueness through heap tuple visibility](https://dev.to/franckpachot/postgresql-resolves-uniqueness-through-heap-tuple-visibility-bkp) ([snapshot](devto/articles/4099802.json))
- [MongoDB High Availability: Replica Set in a Docker Lab](https://dev.to/mongodb/mongodb-high-availability-replicaset-in-a-docker-lab-4jlc) ([snapshot](devto/articles/2669399.json))
- [MongoDB Internals: How Collections and Indexes Are Stored in WiredTiger](https://dev.to/mongodb/mongodb-internals-how-collections-and-indexes-are-stored-in-wiredtiger-2ed) ([snapshot](devto/articles/2841989.json))
- [Strong consistency: MongoDB highly available durable writes](https://dev.to/mongodb/strong-consistency-mongodb-highly-available-durable-writes-2j2k) ([snapshot](devto/articles/2638775.json))
- [A smaller YugabyteDB image for CI/CD (example with Sakila)](https://dev.to/yugabyte/a-smaller-yugabytedb-image-for-cicd-1ig3) ([snapshot](devto/articles/1836259.json))
- [Isolation Levels part XIII: Explicit Locking with SELECT FOR UPDATE intention](https://dev.to/yugabyte/isolation-levels-part-xiii-explicit-locking-with-select-for-update-intention-4na3) ([snapshot](devto/articles/1716801.json))
- [ESR rule applied to YugabyteDB and PostgreSQL indexes](https://dev.to/yugabyte/esr-equality-sort-range-rule-for-yugabytedb-indexes-fi4) ([snapshot](devto/articles/2241892.json))
- [Indexing for NOT EQUAL across YugabyteDB, PostgreSQL, Oracle, SQL Server, and MongoDB](https://dev.to/aws-heroes/indexing-for-not-equal-in-yugabytedb-postgresql-oracle-database-and-mongodb-25mo) ([snapshot](devto/articles/2231411.json))
- [Pagination with an OFFSET is better without OFFSET](https://dev.to/franckpachot/pagination-with-an-offset-is-better-without-offset-5fah) ([snapshot](devto/articles/1691317.json))

## Finish the lab

A lab is complete when another person can run it from an empty machine, observe the same mechanism, falsify the stated hypothesis, and remove every created resource. Keep the failed attempts: they show which observations were not discriminating and prevent the same false lead from becoming folklore.