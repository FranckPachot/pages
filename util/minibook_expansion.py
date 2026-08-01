"""Curated metadata and field manuals for the second minibook collection."""


def chapter(title: str, lead: str, *points: str) -> tuple[str, str, list[str]]:
    return title, lead, list(points)


def guide(title: str, body: str, code: str) -> dict[str, str]:
    return {"title": title, "body": body, "code": code}


EXTRA_BOOKS = [
    {
        "slug": "wal-redo-and-durability",
        "number": "12",
        "title": "WAL, Redo, and Durability",
        "subtitle": "From commit records to crash recovery",
        "description": "How PostgreSQL WAL and Oracle redo turn memory changes into durable, recoverable database state.",
        "accent": "#a23b32",
        "topics": "WAL · redo · checkpoints · recovery",
        "chapters": [
            chapter("The log goes first", "A database can acknowledge a commit before every changed data block reaches its final location only because the recovery log reaches durable storage first.", "WAL and redo describe changes needed to recover blocks.", "Commit durability depends on the log flush boundary.", "Data files may lag safely when recovery can replay the log."),
            chapter("Commit is a synchronization point", "A commit record joins transaction semantics to storage ordering. Group commit amortizes one flush across several sessions, while synchronous replication can extend the boundary to another failure domain.", "Log generation and log flush are different measurements.", "A wait event names the blocked phase, not automatically the root cause.", "Remote acknowledgement changes both durability and latency."),
            chapter("Checkpoints bound recovery", "A checkpoint establishes how far recovery may need to scan and creates pressure to write dirty buffers. Aggressive checkpoints shorten replay but increase write bursts and full-page logging.", "Checkpoint frequency trades recovery time for steady-state I/O.", "Dirty-page writes do not commit transactions.", "Observe checkpoint write time and buffer eviction together."),
            chapter("Protect pages from torn writes", "PostgreSQL full-page images and Oracle block recovery mechanisms ensure that a crash cannot leave a partially written page that logical redo cannot repair.", "Full-page images are normally logged after each checkpoint.", "Checksums detect corruption but do not supply missing bytes.", "Storage atomicity assumptions belong in correctness tests."),
            chapter("Recovery replays history", "Crash recovery repeats logged changes and treats transactions without a durable commit as aborted. Instance recovery, media recovery, and point-in-time recovery start from different material but share ordered redo.", "Replay must be idempotent at the recovery layer.", "Archived logs extend recovery beyond online log retention.", "Recovery objectives determine log retention and backup design."),
            chapter("Measure write amplification", "One logical row change can update heap blocks, indexes, transaction metadata, and replicas. Log volume is therefore a physical workload signal, not merely a backup concern.", "Measure WAL or redo per business operation.", "Wide updates and extra indexes increase log generation.", "Tune only after separating generation, flush, and transport costs."),
        ],
        "sources": ["What happens when a PostgreSQL backend crashes?", "Multi-AZ PostgreSQL COMMIT wait events: WALSync, SyncRep & XactSync", "Postgres, the fsync() issue, and ‘pgio’", "Full page logging in Postgres and Oracle", "18c: some optimization about redo size", "How many members for standby redo logs?", "Redo log block size on ODA X6 all flash"],
    },
    {
        "slug": "sql-plan-management",
        "number": "13",
        "title": "SQL Plan Management",
        "subtitle": "Baselines, evolution, and regression control",
        "description": "Use Oracle SQL Plan Management as a controlled acceptance process for execution plans, not a substitute for optimizer evidence.",
        "accent": "#4e5f8f",
        "topics": "Oracle · plan baselines · regression control",
        "chapters": [
            chapter("A baseline is an allow-list", "SQL Plan Management records accepted plan signatures for a SQL statement. The optimizer still costs alternatives, but only reproducible accepted plans are eligible when a baseline is active.", "A baseline is attached to normalized SQL identity.", "Accepted, enabled, and fixed are independent states.", "A stored plan must still be reproducible in the current schema."),
            chapter("Capture from evidence", "Plans can be loaded from the cursor cache, SQL tuning sets, or automatic capture. Capture should preserve the binds, environment, and performance evidence that made a plan worth keeping.", "Do not baseline an unexplained transient success.", "Keep origin and change-ticket metadata.", "Confirm that the captured plan handles representative selectivity."),
            chapter("Evolve rather than freeze", "New plans enter plan history without becoming accepted automatically. Evolution compares candidates and provides an explicit gate for improvement after statistics, index, or version changes.", "Fixed plans take precedence over non-fixed plans.", "Acceptance controls risk; it does not prove universal superiority.", "Retire obsolete plans after a measured observation window."),
            chapter("Diagnose reproduction failure", "A baseline can be enabled and accepted yet absent from the final plan because an index disappeared, a hint cannot be honored, or the statement no longer matches.", "Read the DBMS_XPLAN note and outline data.", "Check SQL handle, plan name, and origin.", "Treat failed reproduction as a dependency problem."),
            chapter("Separate directives and baselines", "SQL Plan Directives, cardinality feedback, profiles, patches, and baselines act at different layers. Directives improve estimates; baselines constrain plan choice; patches inject targeted hints.", "Choose the mechanism that matches the failure.", "Do not layer controls until causality is unknowable.", "Document precedence and removal criteria."),
            chapter("Operate a regression workflow", "A sound workflow detects a plan change, quantifies impact, installs a temporary guardrail, repairs the model or access path, and deliberately evolves the baseline.", "Record plan hash and baseline identity with runtime data.", "Test upgrades against a captured SQL workload.", "Keep a reversible path for every plan control."),
        ],
        "sources": ["Enabled, Accepted, Fixed SQL Plan Baselines", "Do you use SQL Plan Baselines?", "SQL Plan Directives strikes again", "SQL Plan Directive: disabling usage and column groups", "How to disable a SQL Plan Directive permanently", "How to import SQL Plan Directives", "Matching SQL Plan Directives and queries using it", "18c dbms_xplan note about failed SQL Plan Baseline", "Find the SQL Plan Baseline for a plan operation"],
    },
    {
        "slug": "oracle-multitenant-internals",
        "number": "14",
        "title": "Oracle Multitenant Internals",
        "subtitle": "CDB roots, PDB dictionaries, and object links",
        "description": "A physical and dictionary-level model of Oracle containers, common metadata, object links, DDL replay, and plug-in compatibility.",
        "accent": "#24706b",
        "topics": "Oracle · CDB · PDB · dictionary internals",
        "chapters": [
            chapter("One instance, many containers", "A CDB shares an instance and root dictionary while each PDB presents an application-facing database boundary with local data and metadata.", "CON_ID is part of multitenant identity.", "CDB$ROOT and PDB$SEED have special lifecycle roles.", "Services, not container names alone, route applications."),
            chapter("The dictionary is selectively shared", "Oracle consolidates some dictionary state in the root while preserving container-local rows elsewhere. CONTAINERS() views and internal metadata project the correct scope.", "CDB_ views are not simple UNION ALL wrappers.", "Common objects may have metadata-linked definitions.", "Always preserve container context in diagnostics."),
            chapter("Object links cross the boundary", "Metadata links and data links let a PDB resolve common objects whose definition or rows live in the root. Parsing and execution can therefore operate in different container contexts.", "Object links are an internal sharing mechanism.", "Fixed tables require specialized links.", "Execution context explains surprising recursive SQL."),
            chapter("Common DDL must be replayable", "A common-user or system-package change initiated from one container may need root execution and replay into PDB context. Oracle records enough state to keep common metadata coherent.", "Common and local users obey different naming and scope rules.", "Package compilation can cross container boundaries.", "DDL replay failures surface as compatibility violations."),
            chapter("Plug-in is a compatibility check", "Unplug and plug operations compare options, patches, character sets, common objects, and encryption keys. PDB_PLUG_IN_VIOLATIONS is the primary explanation surface.", "Warnings and errors have different open consequences.", "Run compatibility checks before moving files.", "Resolve root/PDB patch drift deliberately."),
            chapter("Isolation extends to operations", "File destinations, resource plans, save state, services, lockdown profiles, and standby behavior determine whether the logical tenant boundary survives routine operations.", "Place files through container-aware defaults.", "Resource plans limit noisy neighbors.", "Test startup, clone, switchover, and recovery per service."),
        ],
        "sources": ["12c Multitenant internals: PDB_PLUG_IN_VIOLATIONS", "12c Multitenant internals: PDB replay DDL for common users", "12c Multitenant Internals: compiling system package from PDB", "Multitenant internals: INT$ and INT$INT$ views", "12c Multitenant Internals: VPD for V$ views", "Multitenant internals: object links on fixed tables", "Multitenant internals: how object links are parsed/executed", "12c multitenant: Cursor sharing in CDB", "Multitenant dictionary: what is consolidated and what is not", "Multitenant dictionary: what is stored only in CDB$ROOT?"],
    },
    {
        "slug": "locks-blocking-and-deadlocks",
        "number": "15",
        "title": "Locks, Blocking, and Deadlocks",
        "subtitle": "Read wait graphs across database engines",
        "description": "Diagnose lock modes, blocker chains, deadlock cycles, and intentional coordination in Oracle, PostgreSQL, and distributed SQL.",
        "accent": "#87442f",
        "topics": "locks · blockers · deadlocks · diagnostics",
        "chapters": [
            chapter("A lock protects a fact", "Locks represent a transaction's claim over rows, keys, relations, or application-defined resources. The mode expresses which concurrent claims remain compatible.", "Waiting is not itself a defect.", "Object and row locks protect different invariants.", "MVCC reduces read/write blocking but does not remove write conflicts."),
            chapter("Read the compatibility matrix", "Shared, exclusive, intention, key-share, and update modes differ by engine. Translate the protected operation before comparing product names.", "Oracle TM modes describe table-level DML coordination.", "PostgreSQL relation and tuple modes have separate matrices.", "Distributed lock managers may expose key ranges and tablet identity."),
            chapter("Build the blocker graph", "A blocked session points to a holder, which may itself wait. The useful diagnostic is a graph from final blocker through all victims, with transaction age and SQL at every node.", "Capture the holder before killing it.", "Transaction start often matters more than query start.", "Idle-in-transaction sessions can retain consequential locks."),
            chapter("A deadlock is a cycle", "Deadlock detection chooses a victim because no participant can progress. The error trace is evidence of incompatible resource order, not random failure.", "Retry the complete transaction.", "Acquire equivalent resources in a stable order.", "Single statements can deadlock through multi-row execution order."),
            chapter("Lock intentionally", "SELECT FOR UPDATE, advisory locks, and SKIP LOCKED are coordination tools when a schema constraint cannot directly encode the invariant.", "Lock the row or key that represents the rule.", "Keep work after lock acquisition short.", "Advisory locks require every participant to honor the protocol."),
            chapter("Reduce the contention domain", "Indexes, partition keys, transaction boundaries, and batch order determine how much state must remain protected and for how long.", "An index can make conflict discovery precise.", "Large batches enlarge deadlock surfaces.", "Fix the access path before raising lock timeouts."),
        ],
        "sources": ["Single-statement deadlock in Oracle and ORA-00060", "Investigating Oracle lock issues with event 10704", "Oracle — Table lock modes", "Waiting for row lock. But which row is locked?", "Oracle locks: Identifying blocking sessions", "Pessimistic locking, Read Committed, and all Isolation Levels", "More details in pg_locks for YugabyteDB", "Advisory/Custom/Application Lock with YugabyteDB", "Isolation Levels - part XIII: Explicit Locking with SELECT (FOR UPDATE) intention", "Can writes be blocked by reads in YugabyteDB?"],
    },
    {
        "slug": "partitioning-and-sharding",
        "number": "16",
        "title": "Partitioning and Sharding",
        "subtitle": "Pruning, placement, and global constraints",
        "description": "Design range, list, and hash boundaries that improve lifecycle and locality without sacrificing SQL semantics.",
        "accent": "#6f5b22",
        "topics": "partitioning · pruning · sharding · placement",
        "chapters": [
            chapter("Partition for a boundary", "Partitioning is valuable when a boundary supports pruning, lifecycle operations, locality, or independent maintenance. Merely splitting a table does not reduce the work of an unprunable query.", "Choose a key present in important predicates.", "Keep partition count operationally bounded.", "Separate retention needs from distribution needs."),
            chapter("Pruning is optimizer proof", "Static pruning uses known values at planning time; runtime pruning uses parameters or join values during execution. Expressions and implicit casts can hide the boundary.", "Inspect partitions actually scanned.", "Bind variables can delay pruning decisions.", "Global and partition statistics both affect costing."),
            chapter("Range and hash solve different problems", "Range partitions preserve locality and permit detach-by-time operations. Hash distributes keys broadly but gives up adjacent-key locality.", "Monotonic keys can hotspot one range.", "Hash does not replace a queryable business key.", "Composite strategies can separate routing from local order."),
            chapter("Constraints may be global", "Uniqueness and foreign keys become harder when the constrained key omits the partition key. Engines use global indexes, distributed transactions, or restrictions to preserve semantics.", "Declare the real invariant before choosing local indexes.", "A partition-local unique key has narrower meaning.", "Test attach and detach validation costs."),
            chapter("Distributed tablets move", "A distributed shard is also a replication and balancing unit. Splitting and movement change physical placement while SQL identity should remain stable.", "Tablet count affects metadata and consensus overhead.", "Co-location reduces some RPCs but concentrates load.", "Observe skew in bytes, requests, and leaders."),
            chapter("Queries merge local answers", "Top-N, aggregation, and joins across partitions require a global merge unless predicates prove only one partition matters.", "Push limits only when semantics allow it.", "Preserve a total order across partition boundaries.", "Measure rows read from every child, not only final output."),
        ],
        "sources": ["Most Complete Auto-Sharding and Partitioning Strategies", "Advanced PostgreSQL Partitioning by Date with YugabyteDB Auto Sharding", "Partitions, Merge Append, Pagination, and Limit pushdown in YugabyteDB", "Partitioning vs. Sharding - What about SQL Features?", "Is co-partition or interleave necessary in Distributed SQL?", "Distributed PostgreSQL without sharding constraint for SQL joins", "Global Unique Constraint on a partitioned table in PostgreSQL and YugabyteDB", "Oracle global vs. partition level statistics CBO usage", "Oracle literal vs bind-variable in partition pruning and Top-N queries"],
    },
    {
        "slug": "optimizer-statistics",
        "number": "17",
        "title": "Optimizer Statistics",
        "subtitle": "Cardinality, correlation, and adaptive evidence",
        "description": "Understand what histograms, column groups, sampling, partition statistics, and feedback can tell an optimizer.",
        "accent": "#437047",
        "topics": "statistics · cardinality · histograms · feedback",
        "chapters": [
            chapter("Statistics compress reality", "An optimizer substitutes summaries for reading all data during planning. Row counts, distinct values, null fractions, density, and histograms preserve selected properties of a distribution.", "Every summary loses information.", "Sampling introduces bounded uncertainty.", "Statistics age matters only relative to changed distribution."),
            chapter("Histograms model skew", "Frequency and bucketed histograms improve equality and range estimates when values are not uniform, but bind handling and endpoint representation determine whether that knowledge is usable.", "Collect histograms on evidence, not every column.", "Popular and rare values may need different plans.", "String endpoints and collation can limit precision."),
            chapter("Columns are not independent", "Country and postal code, status and close date, or tenant and identifier often correlate. Extended statistics and Oracle column groups model facts that single-column summaries cannot.", "Dependencies improve combined selectivity.", "Multivariate NDV improves GROUP BY estimates.", "Expression statistics must match query expressions."),
            chapter("Partitions need two scales", "Local statistics describe one partition; global statistics describe the whole object. Incremental maintenance and synopses avoid rescanning all historical data after loading one partition.", "Skew between partitions defeats naive roll-up.", "Pruning does not eliminate the need to cost remaining partitions.", "Publish new statistics through a controlled workflow."),
            chapter("Runtime evidence can adapt", "Dynamic sampling, cardinality feedback, statistics collectors, and advisors fill gaps at parse or after execution. They have memory, persistence, and version-specific behavior.", "Feedback treats a symptom unless the missing fact is identified.", "Adaptive branches still consume planning and sometimes runtime work.", "Know when learned evidence is invalidated."),
            chapter("Gather without surprise", "Pending statistics, history, restore points, and representative tests make statistics changes reversible. A gather job is a production change because it can change every dependent plan.", "Capture plans before publishing new statistics.", "Use table-specific preferences for volatile objects.", "Validate representative binds and partition ages."),
        ],
        "sources": ["Optimizer Statistics Gathering – pending and history", "Oracle global vs. partition level statistics CBO usage", "How to gather Oracle optimizer statistics with minimal risks of regression", "Dynamic Sampling vs. Extended Statistics", "YugabyteDB cardinality estimation in the absence of ANALYZE statistics", "Extended Statistics and pg_hint_plan /*+ Rows() */", "12cR2 DML monitoring and Statistics Advisor", "Adaptive Plan: How much can STATISTICS COLLECTOR buffer?", "12c Dynamic Sampling and Standard Edition", "Out of Range statistics with PostgreSQL & YugabyteDB"],
    },
    {
        "slug": "replication-and-high-availability",
        "number": "18",
        "title": "Replication and High Availability",
        "subtitle": "Transport, apply, failover, and recovery objectives",
        "description": "Turn log transport and replicas into explicit durability, availability, consistency, RPO, and RTO guarantees.",
        "accent": "#2b6280",
        "topics": "replication · Data Guard · failover · RPO/RTO",
        "chapters": [
            chapter("Replication starts with a promise", "A replica may protect durability, serve reads, enable disaster recovery, or feed change data capture. Each purpose requires a different contract for acknowledgement and apply.", "Transported is not necessarily applied.", "Available is not necessarily current.", "State the failure domain each copy protects."),
            chapter("Synchronous changes commit", "Synchronous transport adds a remote acknowledgement to commit. The exact wait point may prove receipt in memory, durable log storage, or applied state.", "Quorum policy defines tolerated failures.", "Network tails appear in commit latency.", "Fallback modes can silently change protection."),
            chapter("Asynchronous creates an RPO", "Asynchronous replication decouples commits from network latency but permits acknowledged changes to be absent after source loss. Lag must be measured in the log coordinate system.", "Byte lag and time lag answer different questions.", "Archive gaps can stop apply long after transport recovers.", "RPO is a tested business limit, not a topology label."),
            chapter("Reads need a freshness contract", "A read replica can be transactionally consistent at its replay position while stale relative to the primary. Read routing must define monotonicity and read-your-writes behavior.", "Route consistency-sensitive reads to a sufficient position.", "Apply delay may be intentional for recovery.", "Long queries can conflict with replay cleanup."),
            chapter("Failover is a client workflow", "Promotion alone does not restore service. Fencing the old primary, changing routes, reconnecting pools, replaying transactions, and rebuilding protection determine real recovery time.", "Prevent dual writers before accepting traffic.", "Use request identity across ambiguous commits.", "Practice failback and replica re-creation."),
            chapter("Prove RPO and RTO", "A resilient design measures detection, decision, promotion, routing, client recovery, and backlog drain under realistic faults.", "Observe-only automation validates decisions safely.", "Test regional and storage failures separately.", "Include data validation in recovery completion."),
        ],
        "sources": ["Asynch replication for Disaster Recovery, Read Replicas, and Change Data Capture", "Cross-cluster async replication with YugabyteDB xCluster", "The cost and benefit of synchronous replication in PostgreSQL and YugabyteDB", "A Serverless Standby Database called Oracle Autonomous Data Guard", "Oracle 19c Data Guard sandbox created by DBCA -createDuplicateDB", "19c Observe-Only Data Guard FSFO: no split-brain risk in manual failover", "Where to check Data Guard gap?", "Data Guard gap history", "Archivelog deletion policy on Data Guard configuration", "12c NSSn process for Data Guard SYNC transport"],
    },
    {
        "slug": "database-observability",
        "number": "19",
        "title": "Database Observability",
        "subtitle": "Sessions, waits, plans, and workload time",
        "description": "Connect requests to active sessions, wait events, runtime plans, statement aggregates, and historical workload evidence.",
        "accent": "#72517d",
        "topics": "wait events · active sessions · runtime evidence",
        "chapters": [
            chapter("Observe time, not dashboard color", "Database response time divides into CPU execution and waits for resources or coordination. A useful signal preserves how many sessions experienced each state and for how long.", "Elapsed time includes work outside the database.", "Wait names identify a phase, not always a cause.", "Concurrency turns small per-call costs into saturation."),
            chapter("Active sessions are samples", "Active Session History samples sessions running on CPU or waiting in a database call. Aggregating samples approximates database time by SQL, event, module, object, or plan line.", "ASH is statistical, not a complete trace.", "Sample counts need the sampling interval for time estimates.", "Idle sessions are intentionally absent."),
            chapter("Current activity is a snapshot", "V$SESSION and pg_stat_activity show present session state. Repeated sampling can reconstruct a short history, but transaction age and prior statements require explicit capture.", "Record backend and application identity.", "Query start and transaction start answer different questions.", "Distributed systems require collection from all nodes."),
            chapter("Plans need runtime counters", "A plan explains operators; actual rows, loops, buffers, spills, and waits explain execution. Statement aggregates hide skew unless parameter and plan identity are retained.", "Find the first estimate divergence.", "Multiply per-loop rows by loops.", "Correlate plan changes with workload and schema changes."),
            chapter("Tag the business request", "SQL text alone cannot distinguish checkout from reconciliation or retries from first attempts. Module, action, application_name, trace identifiers, and query comments connect database work to its caller.", "Use bounded-cardinality tags.", "Propagate identity through connection pools.", "Keep secrets and user data out of SQL comments."),
            chapter("Investigate with a time window", "Start from an incident interval, quantify database demand, split CPU from waits, rank dimensions, and only then inspect representative statements and blockers.", "Compare against a workload-matched baseline.", "Preserve evidence before terminating sessions.", "Finish with a falsifiable cause and a monitored change."),
        ],
        "sources": ["Active Session History (ASH) in YugabyteDB", "Find hotspots with Yugabyte Active Session History", "Quick 📸 on 🐘 wait events from pg_stat_activity", "pg_stat_activity from all servers in YugabyteDB", "Quick 📊 on 🐘 active SQL from pg_stat_activity", "AWS Aurora IO:XactSync is not a PostgreSQL wait event", "Google Cloud SQL Insights: ASH, plans and statement tagging", "PostgreSQL: measuring query activity(WAL size generated, shared buffer reads, filesystem reads,…)", "Multi-AZ PostgreSQL COMMIT wait events: WALSync, SyncRep & XactSync"],
    },
]


EXTRA_TECHNICAL_GUIDES = {
    "wal-redo-and-durability": [
        guide("Measure WAL per transaction", "PostgreSQL reports generated WAL directly in EXPLAIN and exposes WAL positions for interval measurements. Compare equivalent business operations rather than raw bytes per second.", "SELECT pg_current_wal_lsn() AS before_lsn;\n-- execute one representative transaction\nSELECT pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), $1));"),
        guide("Separate write from flush", "pg_stat_wal separates records, full-page images, bytes, write calls, flush calls, and cumulative times when track_wal_io_timing is enabled. High generation and slow flush require different remedies.", "SELECT wal_records, wal_fpi, wal_bytes, wal_write, wal_sync,\n       wal_write_time, wal_sync_time\nFROM pg_stat_wal;"),
        guide("Inspect checkpoint pressure", "Frequent requested checkpoints, long write phases, or large backend buffer writes indicate that checkpoint pacing and buffer capacity need joint analysis.", "SELECT checkpoints_timed, checkpoints_req, checkpoint_write_time,\n       checkpoint_sync_time, buffers_checkpoint, buffers_backend\nFROM pg_stat_bgwriter;"),
        guide("Read Oracle redo generation", "Oracle cumulative statistics and log history distinguish generation rate, switches, and recovery retention. A log switch is an operational boundary, not a commit flush.", "SELECT name, value FROM v$sysstat\nWHERE name IN ('redo size','redo writes','redo write time');\nSELECT sequence#, first_time, next_time FROM v$log_history\nORDER BY sequence# DESC FETCH FIRST 20 ROWS ONLY;"),
    ],
    "sql-plan-management": [
        guide("List baseline state", "Inspect all independent state flags before assuming a plan is enforced. FIXED=YES changes precedence; REPRODUCED=NO means the stored outline cannot currently build the plan.", "SELECT sql_handle, plan_name, enabled, accepted, fixed, reproduced,\n       origin, last_executed\nFROM dba_sql_plan_baselines\nORDER BY last_modified DESC;"),
        guide("Capture a known cursor plan", "Loading from cursor cache creates a baseline from an observed plan. Pin down SQL_ID and PLAN_HASH_VALUE so capture does not bless an unintended child cursor.", "DECLARE n PLS_INTEGER; BEGIN\n  n := dbms_spm.load_plans_from_cursor_cache(\n    sql_id => :sql_id, plan_hash_value => :plan_hash_value, fixed => 'NO');\nEND;\n/"),
        guide("Display stored hints", "DBMS_XPLAN.DISPLAY_SQL_PLAN_BASELINE exposes the outline used to reproduce a baseline. Compare its note section with the actual cursor plan.", "SELECT * FROM TABLE(dbms_xplan.display_sql_plan_baseline(\n  sql_handle => :sql_handle, plan_name => :plan_name,\n  format => 'BASIC +NOTE +OUTLINE'));"),
        guide("Evolve candidates explicitly", "Evolution tests non-accepted plans and can accept verified candidates. Run it in a representative environment and retain the report as change evidence.", "SET LONG 100000\nSELECT dbms_spm.evolve_sql_plan_baseline(\n  sql_handle => :sql_handle, verify => 'YES', commit => 'NO')\nFROM dual;"),
    ],
    "oracle-multitenant-internals": [
        guide("Anchor every observation to a container", "SYS_CONTEXT and V$CONTAINERS establish where a session executes. Never compare dictionary rows from different containers without retaining CON_ID.", "SELECT sys_context('USERENV','CON_NAME') con_name,\n       sys_context('USERENV','CON_ID') con_id FROM dual;\nSELECT con_id, name, open_mode FROM v$containers ORDER BY con_id;"),
        guide("Inspect plug-in violations", "Violations persist by PDB, type, status, and message. ERROR entries can prevent normal open; resolved entries remain useful migration history.", "SELECT name, cause, type, status, message, action\nFROM pdb_plug_in_violations\nWHERE status <> 'RESOLVED'\nORDER BY time;"),
        guide("Query across containers deliberately", "CONTAINERS() executes a container-aware query and adds CON_ID. The common user needs suitable container data privileges; it is not an unrestricted cross-PDB shortcut.", "ALTER SESSION SET CONTAINER = CDB$ROOT;\nSELECT con_id, owner, object_name\nFROM containers(dba_objects)\nWHERE object_name = 'ORDERS';"),
        guide("Verify services and save state", "PDB open mode and application service placement must survive restart and role change. Save state records desired open mode but does not replace service configuration.", "ALTER PLUGGABLE DATABASE sales OPEN;\nALTER PLUGGABLE DATABASE sales SAVE STATE;\nSELECT con_id, name, open_mode, restricted FROM v$pdbs;"),
    ],
    "locks-blocking-and-deadlocks": [
        guide("Find PostgreSQL blocker chains", "pg_blocking_pids returns direct blockers. Join session metadata and transaction age before deciding which session is the cause or victim.", "SELECT pid, now()-xact_start AS xact_age, wait_event_type, wait_event,\n       pg_blocking_pids(pid) blockers, application_name, query\nFROM pg_stat_activity\nWHERE cardinality(pg_blocking_pids(pid)) > 0;"),
        guide("Map PostgreSQL lock objects", "pg_locks exposes granted and waiting claims. Relation, transactionid, virtualxid, tuple, advisory, and distributed extensions require different identity columns.", "SELECT pid, locktype, mode, granted, relation::regclass,\n       page, tuple, transactionid, virtualxid\nFROM pg_locks\nORDER BY granted, pid;"),
        guide("Find Oracle final blockers", "V$SESSION carries direct and final blocker identifiers. Add transaction age and current/previous SQL before following V$LOCK details.", "SELECT sid, serial#, event, blocking_session, final_blocking_session,\n       sql_id, prev_sql_id, module\nFROM v$session\nWHERE state='WAITING' AND blocking_session IS NOT NULL;"),
        guide("Design deadlock reproduction", "Use two sessions, explicit transaction boundaries, and opposite resource order. The deadlock victim receives an error, but the application must rollback before retrying the whole unit.", "-- Session A: UPDATE account SET ... WHERE id=1; then id=2;\n-- Session B: UPDATE account SET ... WHERE id=2; then id=1;\n-- Capture PostgreSQL log or Oracle deadlock trace before changing code."),
    ],
    "partitioning-and-sharding": [
        guide("Create lifecycle-oriented ranges", "A default partition catches unexpected values but can hide routing defects. Use half-open boundaries and automate creation before the boundary arrives.", "CREATE TABLE event (...) PARTITION BY RANGE (event_time);\nCREATE TABLE event_2026_08 PARTITION OF event\nFOR VALUES FROM ('2026-08-01') TO ('2026-09-01');"),
        guide("Verify pruning", "EXPLAIN must show which children are scanned and which are removed. Parameterized statements may prune at initialization or execution rather than planning.", "EXPLAIN (ANALYZE, BUFFERS, VERBOSE)\nSELECT * FROM event\nWHERE event_time >= $1 AND event_time < $2;\n-- Inspect Subplans Removed and loops for every partition."),
        guide("Preserve uniqueness semantics", "PostgreSQL requires a partitioned unique constraint to include all partition key columns because no global index arbitrates duplicate keys across children.", "ALTER TABLE reservation ADD CONSTRAINT reservation_uk\nUNIQUE (tenant_id, reservation_id);\n-- If reservation_id alone is globally unique, enforce it elsewhere or redesign."),
        guide("Expose distributed placement", "YugabyteDB hash keys distribute writes while following range columns retain order within a tablet keyspace. Explain distribution as part of schema review.", "CREATE TABLE reading (\n  device_id bigint, observed_at timestamptz, value numeric,\n  PRIMARY KEY ((device_id) HASH, observed_at DESC)\n) SPLIT INTO 24 TABLETS;"),
    ],
    "optimizer-statistics": [
        guide("Read PostgreSQL summaries", "pg_stats reveals the lossy model used for one column. Compare MCV frequency, histogram coverage, null fraction, and correlation with the predicate that was misestimated.", "SELECT attname, null_frac, n_distinct, most_common_vals,\n       most_common_freqs, histogram_bounds, correlation\nFROM pg_stats WHERE schemaname='public' AND tablename='orders';"),
        guide("Model correlation", "PostgreSQL extended statistics can record dependencies, multivariate distinct counts, and multicolumn most-common values. ANALYZE populates the object after creation.", "CREATE STATISTICS orders_tenant_status\n  (dependencies, ndistinct, mcv)\nON tenant_id, status FROM orders;\nANALYZE orders;"),
        guide("Publish Oracle statistics safely", "Pending statistics allow gathering and session-scoped testing before publication. Keep history retention sufficient to restore a known set.", "EXEC dbms_stats.set_table_prefs(USER,'ORDERS','PUBLISH','FALSE');\nEXEC dbms_stats.gather_table_stats(USER,'ORDERS');\nALTER SESSION SET optimizer_use_pending_statistics=TRUE;\n-- Test, then DBMS_STATS.PUBLISH_PENDING_STATS."),
        guide("Inspect estimate error", "Runtime row-source statistics turn a vague bad plan into a cardinality problem at a specific operation. Gather them selectively because instrumentation has cost.", "SELECT * FROM TABLE(dbms_xplan.display_cursor(\n  sql_id => :sql_id, cursor_child_no => :child_no,\n  format => 'ALLSTATS LAST +PREDICATE +PEEKED_BINDS'));"),
    ],
    "replication-and-high-availability": [
        guide("Measure PostgreSQL replay position", "Compare primary flush LSN with standby receive, replay, and replay timestamp. Timestamp delay can be NULL or misleading when a system is idle.", "-- Primary: SELECT pg_current_wal_flush_lsn();\n-- Standby:\nSELECT pg_last_wal_receive_lsn(), pg_last_wal_replay_lsn(),\n       now()-pg_last_xact_replay_timestamp() AS replay_delay;"),
        guide("Inspect synchronous policy", "synchronous_standby_names defines which standbys participate; pg_stat_replication shows state, sync role, and byte positions. Validate the policy during a standby outage.", "SHOW synchronous_commit;\nSHOW synchronous_standby_names;\nSELECT application_name, state, sync_state, sent_lsn, flush_lsn, replay_lsn\nFROM pg_stat_replication;"),
        guide("Read Data Guard transport and apply", "V$ARCHIVE_DEST_STATUS and V$DATAGUARD_STATS separate destination health, transport lag, and apply lag. Broker status adds role-transition readiness.", "SELECT dest_id, status, database_mode, recovery_mode, error\nFROM v$archive_dest_status WHERE status <> 'INACTIVE';\nSELECT name, value, unit FROM v$dataguard_stats;"),
        guide("Test ambiguous commit recovery", "A client can lose its connection after commit reaches the server but before acknowledgement returns. Retrying blindly duplicates effects; a stable request key makes outcome discovery safe.", "CREATE UNIQUE INDEX payment_request_uk ON payment(request_id);\nINSERT INTO payment(request_id, account_id, amount) VALUES ($1,$2,$3)\nON CONFLICT (request_id) DO NOTHING\nRETURNING payment_id;"),
    ],
    "database-observability": [
        guide("Sample PostgreSQL activity", "Current activity becomes useful history when sampled with timestamps, transaction age, wait classification, SQL identity, and application metadata.", "SELECT clock_timestamp(), pid, application_name, query_id, state,\n       wait_event_type, wait_event, xact_start, query_start\nFROM pg_stat_activity WHERE backend_type='client backend';"),
        guide("Rank statement resources", "pg_stat_statements aggregates normalized queries. Calls and variance context matter: a high total can be harmless throughput while one spill-heavy call breaks latency.", "SELECT queryid, calls, total_exec_time, mean_exec_time, rows,\n       shared_blks_read, temp_blks_written, wal_bytes\nFROM pg_stat_statements ORDER BY total_exec_time DESC LIMIT 20;"),
        guide("Aggregate Oracle ASH", "ASH samples active sessions. Converting samples to approximate active-session count requires dividing by samples per second and preserving plan line or wait class dimensions.", "SELECT sql_id, session_state, wait_class, event, COUNT(*) samples\nFROM v$active_session_history\nWHERE sample_time >= systimestamp - interval '15' minute\nGROUP BY sql_id, session_state, wait_class, event\nORDER BY samples DESC FETCH FIRST 20 ROWS ONLY;"),
        guide("Tag requests at connection boundaries", "Set low-cardinality application identity when a pooled connection is borrowed, then clear or replace it before reuse. This turns database evidence into an application workflow.", "-- PostgreSQL\nSET application_name = 'checkout/payment';\n-- Oracle\nBEGIN dbms_application_info.set_module('checkout','payment'); END;\n/"),
    ],
}
