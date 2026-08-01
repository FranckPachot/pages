"""Standalone technical reference material for the generated minibooks."""

TECHNICAL_GUIDES = {
    "indexes-and-access-paths": [
        {
            "title": "Read an access path by counting visits",
            "body": "An index lookup has two distinct costs: walking branch blocks to a leaf, then visiting heap or table blocks for matching entries. A three-level B-tree does not mean three I/O operations per row because upper blocks are usually cached. The variable cost is commonly the table visit pattern. PostgreSQL exposes it as heap fetches and buffer hits; Oracle exposes consistent gets and physical reads. A poor clustering factor turns adjacent index entries into scattered table visits.",
            "code": "EXPLAIN (ANALYZE, BUFFERS, WAL)\nSELECT customer_id, created_at\nFROM orders\nWHERE customer_id = 42\nORDER BY created_at DESC\nLIMIT 20;",
        },
        {
            "title": "Build one index for filtering and stopping",
            "body": "Equality columns normally lead, followed by range and ordering columns. The key below lets the executor seek to one customer, scan in requested order, and stop after twenty entries. INCLUDE columns are payload: they can make the query covering but cannot navigate the tree. On PostgreSQL, an index-only plan still needs all-visible heap pages; inspect Heap Fetches rather than trusting the node name alone.",
            "code": "CREATE INDEX orders_customer_recent_ix\nON orders (customer_id, created_at DESC, order_id DESC)\nINCLUDE (status, total);",
        },
        {
            "title": "Know when a bitmap wins",
            "body": "A PostgreSQL bitmap index scan gathers tuple identifiers from one or more indexes, combines them with bitmap AND/OR, sorts visits by heap block, then reads each needed block. It is useful between a selective point lookup and a broad sequential scan. A lossy bitmap stores page-level rather than tuple-level membership when work_mem is tight, so the Bitmap Heap Scan must recheck predicates.",
            "code": "SET LOCAL work_mem = '64MB';\nEXPLAIN (ANALYZE, BUFFERS)\nSELECT * FROM event\nWHERE tenant_id = 7\n  AND severity IN ('ERROR', 'FATAL');",
        },
        {
            "title": "Measure maintenance, not folklore",
            "body": "Every extra index adds WAL or redo, cache churn, uniqueness checks where applicable, and page split work. PostgreSQL's pg_stat_user_indexes reveals read usage but cannot prove an index is redundant; constraints, rare reporting jobs, and standby workloads matter. Compare definitions and left prefixes before removal, then observe a complete business cycle.",
            "code": "SELECT relname, indexrelname, idx_scan,\n       pg_size_pretty(pg_relation_size(indexrelid)) AS size\nFROM pg_stat_user_indexes\nORDER BY idx_scan, pg_relation_size(indexrelid) DESC;",
        },
    ],
    "postgresql-query-planning": [
        {
            "title": "Find the first estimation error",
            "body": "EXPLAIN estimates are available without execution; ANALYZE executes the statement. For each node compare estimated rows with actual rows per loop, not only total output. If a nested loop runs 10,000 times, actual rows=2 means 20,000 rows overall. The first large divergence from the leaves upward is usually the cause; later errors are often multiplication effects.",
            "code": "BEGIN;\nEXPLAIN (ANALYZE, BUFFERS, WAL, SETTINGS, SUMMARY)\nSELECT ...;\nROLLBACK; -- required when diagnosing modifying statements",
        },
        {
            "title": "Inspect what statistics can represent",
            "body": "pg_stats exposes most-common values, frequencies, histogram bounds, null fraction, correlation, and estimated distinct counts. A negative n_distinct is a multiplier of table cardinality. Single-column statistics assume independence, so correlated predicates such as country and postal_code can be badly underestimated. Dependency and multivariate-NDISTINCT statistics give the planner the missing relationship.",
            "code": "CREATE STATISTICS customer_geo_stats\n  (dependencies, ndistinct, mcv)\nON country, postal_code FROM customer;\nANALYZE customer;\n\nSELECT attname, n_distinct, most_common_vals, correlation\nFROM pg_stats WHERE tablename = 'customer';",
        },
        {
            "title": "Separate generic from custom plans",
            "body": "A prepared statement initially receives custom plans using its parameter values. PostgreSQL may later choose a generic plan when its estimated average cost plus planning savings beats continued custom planning. Skew makes that compromise visible: one value needs an index while another needs a scan. plan_cache_mode is a diagnostic control, not a default tuning recommendation.",
            "code": "SET LOCAL plan_cache_mode = force_custom_plan;\nEXPLAIN (ANALYZE, BUFFERS) EXECUTE by_status('RARE');\n\nSET LOCAL plan_cache_mode = force_generic_plan;\nEXPLAIN (ANALYZE, BUFFERS) EXECUTE by_status('RARE');",
        },
        {
            "title": "Interpret join memory correctly",
            "body": "Hash joins build a hash table from one input and probe it with the other. If the build side exceeds work_mem multiplied by hash_mem_multiplier, batches spill to temporary files. A sort may consume work_mem independently at several plan nodes and parallel workers. Raising work_mem globally can multiply memory consumption dramatically; use node evidence and scoped settings.",
            "code": "EXPLAIN (ANALYZE, BUFFERS) SELECT ...;\n-- Look for: Batches > 1, temp read/written,\n-- Sort Method: external merge, and Disk usage.\nSET LOCAL work_mem = '128MB';",
        },
    ],
    "distributed-sql-for-postgresql": [
        {
            "title": "Choose hash or range distribution deliberately",
            "body": "Hash sharding transforms the distribution key into a token and spreads adjacent keys across tablets. It balances point writes but destroys key locality. Range sharding keeps adjacent values together, enabling ordered scans and targeted retention, but a growing edge can become hot. In YugabyteDB, HASH and ASC/DESC in a primary key express this physical choice.",
            "code": "CREATE TABLE account_event (\n  tenant_id bigint,\n  event_time timestamptz,\n  event_id uuid,\n  payload jsonb,\n  PRIMARY KEY ((tenant_id) HASH, event_time DESC, event_id)\n);",
        },
        {
            "title": "Count RPCs, not just SQL operators",
            "body": "A nested loop that performs one remote lookup per outer row has latency proportional to request count. Distributed executors batch outer keys into array or IN probes and push predicates to tablet servers. EXPLAIN ANALYZE should be read for storage requests, rows scanned, and network execution time in addition to familiar PostgreSQL nodes. Returning ten rows after reading a million remote rows is still an expensive plan.",
            "code": "EXPLAIN (ANALYZE, DIST, COSTS OFF)\nSELECT o.id, i.sku\nFROM orders o JOIN order_item i ON i.order_id = o.id\nWHERE o.customer_id = 42\nORDER BY o.created_at DESC LIMIT 20;",
        },
        {
            "title": "Model transaction latency as consensus work",
            "body": "A write is durable after the relevant tablet leader replicates it to a quorum. A transaction touching multiple tablets also records transaction status and coordinates commit. Geographic latency therefore follows the slowest required quorum and transaction participants, not the number of SQL statements alone. Keep a transaction within one placement when practical, but preserve the business invariant before optimizing locality.",
            "code": "BEGIN;\nUPDATE account SET balance = balance - 100 WHERE id = 1;\nUPDATE account SET balance = balance + 100 WHERE id = 2;\nCOMMIT;\n-- Retry the complete unit on serialization or restart errors.",
        },
        {
            "title": "Treat a secondary index as another table",
            "body": "A global secondary index has its own tablets and Raft groups. Each base-table write may create a distributed index write in the same transaction. Covering columns can remove a second network hop from index to base row, but increase replication volume. Evaluate read RPC savings against write amplification and tablet count rather than copying a monolithic index set.",
            "code": "CREATE INDEX order_customer_recent_ix\nON orders (customer_id HASH, created_at DESC, id)\nINCLUDE (status, total);",
        },
    ],
    "foreign-keys-and-concurrency": [
        {
            "title": "See the race a foreign key closes",
            "body": "Without coordination, one transaction can verify that parent 42 exists while another deletes it, after which the first inserts an orphan. A foreign key protects the referenced key during child insertion and checks child references during parent deletion. The exact lock is product-specific, but the invariant requires one operation to wait, fail, or observe the other's committed result.",
            "code": "CREATE TABLE child (\n  child_id bigint PRIMARY KEY,\n  parent_id bigint NOT NULL\n    REFERENCES parent(parent_id)\n    ON DELETE RESTRICT\n);",
        },
        {
            "title": "Index the child for parent-side operations",
            "body": "An index beginning with the foreign-key columns lets the engine establish quickly whether children exist and supports application navigation from parent to children. Oracle can take broader locks for parent deletes when that path is absent. PostgreSQL uses different row lock modes, but still scans the child table for each parent-side check without a useful index. Composite foreign keys require the same leading column set and compatible datatypes.",
            "code": "CREATE INDEX child_parent_fk_ix ON child(parent_id);\n\nEXPLAIN (ANALYZE, BUFFERS)\nSELECT 1 FROM child WHERE parent_id = 42 LIMIT 1;",
        },
        {
            "title": "Add integrity without one long outage",
            "body": "PostgreSQL NOT VALID skips the historical scan while enforcing the foreign key for new or changed rows. VALIDATE CONSTRAINT later scans old data with a lock compatible with normal reads and writes, though conflicting DDL still waits. Create the supporting child index concurrently outside a transaction, clean orphans, add the constraint, then validate under monitoring.",
            "code": "CREATE INDEX CONCURRENTLY child_parent_fk_ix ON child(parent_id);\nALTER TABLE child ADD CONSTRAINT child_parent_fk\n  FOREIGN KEY (parent_id) REFERENCES parent(parent_id) NOT VALID;\nALTER TABLE child VALIDATE CONSTRAINT child_parent_fk;",
        },
        {
            "title": "Diagnose the blocker as a transaction graph",
            "body": "A waiting statement is only the visible edge. Capture both sessions, their transaction age, SQL, lock mode, and application identity. In PostgreSQL pg_blocking_pids returns direct blockers; pg_locks explains the protected object. In Oracle join V$SESSION blocking identifiers with V$LOCK or use ASH. The durable fix is usually shorter transactions, consistent object order, or a precise index.",
            "code": "SELECT pid, application_name, xact_start, wait_event, query,\n       pg_blocking_pids(pid) AS blockers\nFROM pg_stat_activity\nWHERE cardinality(pg_blocking_pids(pid)) > 0;",
        },
    ],
    "sql-statement-lifecycle": [
        {
            "title": "Separate parse, bind, execute, and fetch",
            "body": "Parsing validates syntax and resolves names; binding supplies typed values; execution opens the plan and produces rows; fetching transfers result batches. Database time can be small while application latency is large if a client fetches fifteen rows per network round trip. Conversely, a cursor may execute but never run expensive lower nodes when the client stops early. Trace the phases independently.",
            "code": "-- PostgreSQL server-side preparation\nPREPARE recent_orders(bigint) AS\nSELECT * FROM orders WHERE customer_id = $1\nORDER BY created_at DESC LIMIT 20;\nEXECUTE recent_orders(42);",
        },
        {
            "title": "Understand cursor identity",
            "body": "Oracle groups cursor children under SQL_ID but may create children for optimizer environment, bind metadata, authorization, or adaptive cursor sharing. PostgreSQL prepared statements live in a session, while pg_stat_statements groups normalized query shapes globally. SQL text identity, plan identity, and business operation identity are different dimensions; keep all three in telemetry.",
            "code": "SELECT sql_id, child_number, plan_hash_value, executions,\n       parse_calls, invalidations, is_bind_sensitive, is_bind_aware\nFROM v$sql\nWHERE sql_id = :sql_id\nORDER BY child_number;",
        },
        {
            "title": "Read execution as an iterator pipeline",
            "body": "Most row-source plans use a demand-driven iterator model: a parent asks a child for the next row. Startup cost describes work before the first row; total cost assumes all rows are consumed. Blocking operators such as sort or hash aggregation may consume their input before returning anything, while an index scan under LIMIT can stop immediately. This explains why first-row latency and total throughput favor different plans.",
            "code": "EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)\nSELECT * FROM event\nWHERE tenant_id = 7\nORDER BY event_time DESC\nLIMIT 1;",
        },
        {
            "title": "Treat invalidation as dependency maintenance",
            "body": "DDL, statistics refresh, privilege changes, search path, and optimizer settings can make a cached plan unusable or inappropriate. Replanning is correct behavior, but synchronized invalidation of a hot statement can produce a parse storm. Roll out DDL with lock timeouts, observe parse rates and library/cache contention, and avoid clearing an entire cache to change one statement.",
            "code": "SELECT queryid, calls, plans, total_plan_time, total_exec_time\nFROM pg_stat_statements\nWHERE calls > 0\nORDER BY total_plan_time DESC\nLIMIT 20;",
        },
    ],
    "database-time-and-ordering": [
        {
            "title": "Keep four clocks separate",
            "body": "Transaction start time orders beginnings; wall-clock timestamps represent a node's clock; commit order defines visibility publication; WAL LSN or Oracle SCN places changes in an engine history. None is a universal substitute for another. PostgreSQL now() is fixed at transaction start, statement_timestamp() at statement start, and clock_timestamp() reads the clock on each call.",
            "code": "SELECT now() AS transaction_time,\n       statement_timestamp() AS statement_time,\n       clock_timestamp() AS wall_clock,\n       pg_current_wal_lsn() AS wal_position;",
        },
        {
            "title": "Use engine positions for replication progress",
            "body": "A timestamp comparison cannot prove that a replica has applied a write because clocks may differ and commits can share or reorder timestamps. Compare replay positions in the same log coordinate system. PostgreSQL exposes current, received, and replay LSNs; Oracle exposes SCNs and redo sequence/apply positions. Convert byte lag to time only as an operational approximation.",
            "code": "SELECT pg_current_wal_lsn() AS primary_lsn;\n-- On a standby:\nSELECT pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn(),\n       now() - pg_last_xact_replay_timestamp() AS replay_delay;",
        },
        {
            "title": "Make result ordering total",
            "body": "ORDER BY created_at alone is not deterministic when timestamps tie. The executor may emit ties in heap order, index order, worker arrival order, or shard merge order. Add an immutable unique key as the final ordering term and mirror it in the index. The same tuple becomes a pagination cursor and a reproducible test boundary.",
            "code": "SELECT id, created_at, payload\nFROM event\nWHERE tenant_id = 7\nORDER BY created_at DESC, id DESC\nLIMIT 50;",
        },
        {
            "title": "Serializable order is not wall-clock order",
            "body": "Serializable guarantees equivalence to some serial execution, but the chosen order can differ from transaction start order unless the system also promises strict serializability. PostgreSQL SSI tracks read/write dependencies and aborts a transaction when a dangerous structure could complete a cycle. Applications must replay the whole transaction from a fresh snapshot on SQLSTATE 40001.",
            "code": "BEGIN ISOLATION LEVEL SERIALIZABLE;\n-- read the complete invariant, then perform writes\nCOMMIT;\n-- On 40001: rollback, back off, and rerun the transaction.",
        },
    ],
    "scalable-pagination": [
        {
            "title": "Seek from the last tuple",
            "body": "For descending order, the next page predicate must be lexicographically less than the final tuple of the current page. PostgreSQL row-value comparison implements this directly. The index uses equality on tenant_id, then seeks into created_at and id. LIMIT 51 returns fifty visible rows plus one look-ahead row without a separate count.",
            "code": "SELECT id, created_at, summary\nFROM event\nWHERE tenant_id = $1\n  AND (created_at, id) < ($2, $3)\nORDER BY created_at DESC, id DESC\nLIMIT 51;",
        },
        {
            "title": "Design the matching index",
            "body": "The B-tree key must follow predicate and order semantics. An equality prefix can be followed by the ordered cursor tuple. INCLUDE carries small payload columns without changing order. PostgreSQL can scan a B-tree backward, but mixed directions must match the index definition or require a sort. Null cursor values need explicit policy because row comparison with null is unknown.",
            "code": "CREATE INDEX event_page_ix\nON event (tenant_id, created_at DESC, id DESC)\nINCLUDE (summary);",
        },
        {
            "title": "Page parent entities before joining children",
            "body": "A one-to-many join changes the unit from orders to order items. Applying LIMIT after the join can return only part of the desired parent set, while applying it carelessly before filters changes semantics. Select the bounded parent keys in a materialized CTE, then join their children. This also bounds distributed inner lookups.",
            "code": "WITH page AS MATERIALIZED (\n  SELECT id, created_at FROM orders\n  WHERE customer_id = $1\n    AND (created_at, id) < ($2, $3)\n  ORDER BY created_at DESC, id DESC LIMIT 20\n)\nSELECT p.id, p.created_at, i.sku, i.quantity\nFROM page p LEFT JOIN order_item i ON i.order_id = p.id\nORDER BY p.created_at DESC, p.id DESC, i.line_no;",
        },
        {
            "title": "Define consistency between page requests",
            "body": "Keyset pagination prevents duplicates caused by ordinal shifts before the cursor, but it is not a transaction snapshot across HTTP requests. Rows inserted behind the cursor may be omitted and updates to ordering columns can move rows. For a stable export, hold a database snapshot or materialize identifiers. For an activity feed, document live semantics and keep cursor columns immutable where possible.",
            "code": "-- PostgreSQL stable export pattern\nBEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;\nSELECT pg_export_snapshot();\n-- Worker transactions import the snapshot before their first query.",
        },
    ],
    "postgresql-mvcc-backstage": [
        {
            "title": "Read tuple metadata cautiously",
            "body": "xmin identifies the inserting transaction and xmax is overloaded for deletion, update, and row-lock state. They are 32-bit transaction identifiers interpreted with an epoch and commit-status data; they are not permanent business values. ctid identifies a block and item offset, and normally changes on update. Exposing them is useful for a controlled experiment, not an application contract.",
            "code": "SELECT ctid, xmin, xmax, id, status\nFROM orders\nWHERE id = 42;\n\nUPDATE orders SET status = 'paid' WHERE id = 42;\nSELECT ctid, xmin, xmax, id, status FROM orders WHERE id = 42;",
        },
        {
            "title": "Measure HOT rather than assuming it",
            "body": "A HOT update requires that no indexed column changes and that the heap page has room for the new tuple. The old index entry leads to the root of an on-page tuple chain. Lower fillfactor reserves update space but increases table size and scan work. Compare n_tup_hot_upd with n_tup_upd after a representative interval.",
            "code": "SELECT relname, n_tup_upd, n_tup_hot_upd, n_dead_tup\nFROM pg_stat_user_tables\nWHERE relname = 'orders';\n\nALTER TABLE orders SET (fillfactor = 80);\n-- A rewrite is needed for existing pages to adopt the space layout.",
        },
        {
            "title": "Understand the two visibility-map bits",
            "body": "Each heap page has all-visible and all-frozen state. All-visible allows index-only scans to skip heap visibility checks; all-frozen means tuples no longer need future freezing. Any modification clears all-visible for the page. Vacuum can set it only after proving every tuple is globally visible, which is why write-heavy tables still show Heap Fetches in an Index Only Scan.",
            "code": "CREATE EXTENSION IF NOT EXISTS pg_visibility;\nSELECT * FROM pg_visibility_map_summary('orders');\n\nEXPLAIN (ANALYZE, BUFFERS)\nSELECT id FROM orders WHERE customer_id = 42;",
        },
        {
            "title": "Tune autovacuum from change volume",
            "body": "Vacuum trigger thresholds combine a fixed threshold and a fraction of estimated table rows. A 20 percent scale factor is too slow for many large, high-churn tables. Per-table settings let vacuum start after a bounded number of dead tuples. Also monitor transaction age: anti-wraparound vacuum is a correctness deadline and can ignore normal cost delays.",
            "code": "ALTER TABLE orders SET (\n  autovacuum_vacuum_threshold = 5000,\n  autovacuum_vacuum_scale_factor = 0.01,\n  autovacuum_analyze_scale_factor = 0.005\n);\n\nSELECT relname, n_dead_tup, last_autovacuum,\n       age(relfrozenxid) AS xid_age\nFROM pg_stat_user_tables JOIN pg_class USING (relname);",
        },
    ],
    "schema-design-for-concurrency": [
        {
            "title": "Encode one active row as a unique fact",
            "body": "If only one active reservation may exist per seat, a partial unique index makes competing inserts arbitrate on one key. The application no longer relies on a prior absence check. One transaction succeeds; the other waits and then receives a unique violation or follows ON CONFLICT behavior. This works at Read Committed because the index is the coordination point.",
            "code": "CREATE UNIQUE INDEX one_active_reservation_per_seat\nON reservation (show_id, seat_id)\nWHERE cancelled_at IS NULL;",
        },
        {
            "title": "Use compare-and-set for state transitions",
            "body": "An UPDATE predicate can combine validation and mutation atomically. A zero row count means another transaction changed the expected state or the business condition is false. This avoids a lost update without holding an application-side value between SELECT and UPDATE. RETURNING gives the committed candidate state to the caller in the same round trip.",
            "code": "UPDATE account\nSET balance = balance - $1, version = version + 1\nWHERE account_id = $2\n  AND version = $3\n  AND balance >= $1\nRETURNING balance, version;",
        },
        {
            "title": "Claim queue rows without convoying",
            "body": "FOR UPDATE SKIP LOCKED lets workers ignore rows already claimed by concurrent transactions. Keep selection and state transition in one statement so the lock cannot escape between calls. SKIP LOCKED does not provide fairness and a failed worker still requires lease expiry or transaction rollback. Processing outside the transaction requires an idempotency key.",
            "code": "WITH claim AS (\n  SELECT job_id FROM job\n  WHERE state = 'ready' AND run_after <= now()\n  ORDER BY priority DESC, job_id\n  FOR UPDATE SKIP LOCKED LIMIT 10\n)\nUPDATE job j SET state = 'running', worker_id = $1, started_at = now()\nFROM claim WHERE j.job_id = claim.job_id\nRETURNING j.*;",
        },
        {
            "title": "Retry a transaction, not a statement fragment",
            "body": "Deadlock victims and serialization failures roll back the transaction's logical decision. Retrying only the final UPDATE reuses observations from a failed snapshot and is incorrect. Begin again, repeat every read and check, preserve a request id for deduplication, and bound retries with jittered backoff. PostgreSQL reports serialization failure as 40001 and deadlock detected as 40P01.",
            "code": "retry transaction on SQLSTATE in ('40001', '40P01'):\n  BEGIN\n  read invariant state\n  perform conditional writes\n  COMMIT\n-- External messages use an outbox row committed with the data.",
        },
    ],
    "oracle-to-postgresql": [
        {
            "title": "Test null and empty-string behavior first",
            "body": "Oracle folds a zero-length character string to NULL; PostgreSQL stores it as a distinct value. This changes NOT NULL checks, unique constraints, concatenation, count(column), and application round trips. Do not hide the difference in scattered compatibility functions. Choose a target policy, clean source values, and test every boundary that treats blank as missing.",
            "code": "-- PostgreSQL returns two different predicates\nSELECT '' IS NULL AS empty_is_null,\n       NULL IS NULL AS null_is_null,\n       length('') AS empty_length;\n\n-- Normalize explicitly only where the business model requires it:\nNULLIF(btrim(input_value), '')",
        },
        {
            "title": "Translate plans through physical work",
            "body": "Oracle cost and PostgreSQL cost are unrelated units. Map FULL TABLE SCAN to Seq Scan conceptually, but compare actual rows, buffers, temp spills, and elapsed time. PostgreSQL Bitmap Heap Scan has no direct Oracle bitmap-index requirement, and Index Only Scan depends on the visibility map. Replace hints by understanding which estimate or physical structure made the desired path unavailable.",
            "code": "EXPLAIN (ANALYZE, BUFFERS, WAL, SETTINGS) SELECT ...;\n\n-- Oracle counterpart for runtime row-source statistics:\nSELECT * FROM TABLE(dbms_xplan.display_cursor(\n  sql_id => :sql_id, format => 'ALLSTATS LAST +PEEKED_BINDS'));",
        },
        {
            "title": "Replace undo assumptions with vacuum operations",
            "body": "Oracle retains before-images in undo and can raise snapshot-too-old when required undo is overwritten. PostgreSQL leaves old tuple versions in heap pages until no snapshot can see them, then vacuum marks space reusable. Long PostgreSQL transactions delay cleanup across every table they might see. Migration capacity plans must include autovacuum throughput, WAL volume, fillfactor, and index bloat.",
            "code": "SELECT pid, now() - xact_start AS age, backend_xmin, query\nFROM pg_stat_activity\nWHERE xact_start IS NOT NULL\nORDER BY xact_start;\n\nSELECT relname, n_dead_tup, last_autovacuum\nFROM pg_stat_user_tables ORDER BY n_dead_tup DESC;",
        },
        {
            "title": "Map generated values and numeric types explicitly",
            "body": "Oracle NUMBER without precision can hold a wider range than many automatic mappings. PostgreSQL numeric is exact but slower and larger than integer types; choose bigint only after proving the range. Oracle sequences are independent objects, while PostgreSQL identity columns own sequence behavior more clearly. Neither guarantees gap-free committed numbering.",
            "code": "CREATE TABLE invoice (\n  invoice_id bigint GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,\n  amount numeric(19,4) NOT NULL,\n  issued_at timestamptz NOT NULL\n);",
        },
        {
            "title": "Build a capability-based operations map",
            "body": "Map responsibilities rather than product names: statement aggregation, session sampling, plan capture, backup, point-in-time recovery, physical replication, failover control, and patching. pg_stat_statements is not AWR, streaming replication is not Data Guard Broker, and a filesystem copy is not a tested backup. Define retention, overhead, recovery objectives, and ownership for each target capability.",
            "code": "CREATE EXTENSION pg_stat_statements;\nSELECT queryid, calls, total_exec_time, rows,\n       shared_blks_hit, shared_blks_read, temp_blks_written\nFROM pg_stat_statements\nORDER BY total_exec_time DESC LIMIT 20;",
        },
    ],
}