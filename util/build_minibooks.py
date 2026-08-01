#!/usr/bin/env python3
"""Build the static minibook collection from curated chapter and source data."""

from __future__ import annotations

import html
import json
from pathlib import Path

from google_analytics import add_google_tag
from minibook_expansion import EXTRA_BOOKS, EXTRA_TECHNICAL_GUIDES
from minibook_details import TECHNICAL_GUIDES

SITE_URL = "https://franckpachot.github.io/pages/"

BOOKS = [
    {
        "slug": "indexes-and-access-paths",
        "number": "02",
        "title": "Indexes and Access Paths",
        "subtitle": "From data structure to execution plan",
        "description": "How B-trees, covering indexes, scan methods, and optimizer costs turn a predicate into physical work.",
        "accent": "#9f3f31",
        "topics": "B-trees · access paths · execution plans",
        "chapters": [
            ("The index is a physical promise", "An index promises ordered access to a subset of table facts. It is not inherently faster than a table scan: its value depends on how much data can be rejected before visiting the table and how those visits are distributed across storage.", ["A B-tree branch narrows the search; leaf entries identify rows or row locations.", "Selectivity determines how soon an index stops being cheaper than scanning.", "The table remains the source of truth unless the index covers every required fact."]),
            ("Read the tree from root to leaf", "Height, fan-out, key width, and block density determine the work needed to reach a leaf. A wide covering index can save table visits while increasing branch size, cache pressure, and write cost. Index design is therefore a workload trade, not a checklist item.", ["Prefix columns define which predicates can navigate the tree.", "Included or trailing columns can cover output without improving navigation.", "Block splits preserve order; they are normal maintenance, not automatic evidence of damage."]),
            ("One predicate, several access paths", "A sequential scan, index scan, index-only scan, and bitmap scan answer the same logical request with different physical work. The optimizer compares estimated pages, tuples, CPU operations, ordering benefits, and parallelism rather than following a rule such as ‘an index exists, therefore use it.’", ["Sequential scans amortize I/O when much of the table is needed.", "Index scans excel when few row locations are visited predictably.", "Bitmap scans collect many locations before visiting table pages, trading latency for locality."]),
            ("Covering is product-specific", "Oracle can often return indexed columns directly because row visibility is resolved through undo and block metadata. PostgreSQL index-only scans also consult the visibility map: an index containing every projected column may still visit the heap when pages are not known to be all-visible.", ["Coverage is a query property, not an index label.", "Visibility and recent updates influence PostgreSQL heap fetches.", "Measure logical reads and heap fetches, not only the plan node name."]),
            ("Ordering is work you may avoid", "A B-tree already stores keys in order. Matching equality prefixes and an ordered suffix can eliminate sorting, accelerate min/max queries, and stop early for top-N retrieval. Direction, null ordering, and mixed ascending/descending requirements decide whether the stored order is reusable.", ["Filtering and ordering should be designed together.", "A reverse scan can satisfy a fully reversed order.", "Pagination needs a deterministic tie-breaker in the index and query."]),
            ("Design from evidence", "Start with the query shape and expected cardinality, then verify estimates against actual rows and buffers. An index that rescues one statement can slow every write and duplicate another index. Keep the smallest set that supports real invariants and access paths.", ["Use EXPLAIN with runtime statistics where production safety permits.", "Compare estimates, actual rows, buffers, and elapsed time.", "Re-test after data distribution and workload shape change."]),
        ],
        "sources": ["B-tree block split: what's the impact?", "B+tree height after full delete: PostgreSQL fast root", "Covering indexes in Oracle, and branch size", "Postgres vs. Oracle access paths I", "Postgres vs. Oracle access paths II", "Postgres vs. Oracle access paths VI", "Postgres vs. Oracle access paths VII"],
    },
    {
        "slug": "postgresql-query-planning",
        "number": "03",
        "title": "PostgreSQL Query Planning",
        "subtitle": "Estimates, costs, joins, and plan stability",
        "description": "A practical model for understanding why PostgreSQL chooses a plan and how to investigate when that choice is wrong.",
        "accent": "#26617a",
        "topics": "PostgreSQL · cardinality · join planning",
        "chapters": [
            ("A plan is a forecast", "The planner cannot execute every alternative. It predicts cardinalities and costs from statistics, parameters, and algebraic transformations, then chooses the cheapest forecast. Most surprising plans begin with a wrong estimate rather than a broken scan or join implementation.", ["Cost is an internal comparison unit, not elapsed milliseconds.", "Rows flowing between nodes matter more than the final row count.", "The first large estimate error is usually more useful than the top node."]),
            ("Statistics describe distributions", "Per-column statistics summarize null fractions, distinct values, common values, and histograms. They cannot automatically describe every correlation between columns or expressions. Extended statistics and expression indexes communicate facts that independent column summaries miss.", ["Increase statistics targets selectively, not globally by reflex.", "Analyze after representative data changes.", "Compare estimated and actual rows at every plan boundary."]),
            ("Parameters change what can be known", "A literal can reveal selectivity during planning; a parameter may not. Prepared statements can move from custom plans to a generic plan whose compromise is cheaper across executions but poor for skewed values. The right diagnosis distinguishes planning-time ignorance from stale statistics.", ["Inspect custom and generic plan behavior separately.", "Parameter skew can justify query variants or controlled replanning.", "Do not disable prepared statements before measuring their trade-off."]),
            ("Join order multiplies uncertainty", "For several relations, the planner must choose both join algorithms and order. Underestimating an early input can make a nested loop look cheap; overestimating can hide a useful parameterized index path. Hash and merge joins have different memory, ordering, and startup profiles.", ["Nested loops are excellent when the inner lookup stays small.", "Hash joins favor larger equality joins when memory is adequate.", "Merge joins exploit compatible ordering and range-like progression."]),
            ("Cost parameters are a model", "Settings such as random_page_cost and effective_cache_size describe the environment; they are not knobs for forcing one query. Calibrate them to broad storage and cache behavior, then fix local modeling problems with statistics, indexes, or query structure.", ["Planner enable flags are diagnostic tools, not permanent hints.", "A forced alternative reveals whether a better executable plan exists.", "Global parameter changes require workload-wide evidence."]),
            ("A repeatable investigation", "Capture the SQL, parameters, schema, statistics age, plan, runtime rows, buffers, and relevant settings. Find the earliest estimate divergence, formulate one cause, and change one input to the model. This produces knowledge that survives the next query instead of a brittle forced plan.", ["Preserve the original plan before experimenting.", "Test realistic parameter values and cache states.", "Treat plan stability as controlled adaptability, not immobility."]),
        ],
        "sources": ["PostgreSQL query planner parameters and prepared statements", "Postgres vs. Oracle access paths III", "Postgres vs. Oracle access paths IV", "Postgres vs. Oracle access paths V", "Adaptive plan: how much can statistics collector buffer", "When automatic reoptimization plan is less efficient"],
    },
    {
        "slug": "distributed-sql-for-postgresql",
        "number": "04",
        "title": "Distributed SQL",
        "subtitle": "For PostgreSQL developers",
        "description": "How familiar SQL, indexes, joins, and transactions change when storage and consensus span nodes and regions.",
        "accent": "#6b4f16",
        "topics": "sharding · consensus · distributed PostgreSQL",
        "chapters": [
            ("Distribution adds distance", "A monolithic PostgreSQL execution can access shared memory and local storage. Distributed SQL preserves a relational interface while rows, indexes, and transaction participants live on different nodes. Every physical operation must therefore be evaluated in network round trips as well as CPU and storage.", ["Logical SQL portability does not imply identical physical cost.", "One local nested loop can become thousands of remote requests.", "Batching and pushdown are central execution techniques."]),
            ("Tablets make placement explicit", "Distributed tables are divided into ranges or hash partitions, often called tablets. Hash distribution spreads write load; range distribution preserves locality and ordered access. The primary key usually participates in this physical decision even when SQL syntax looks ordinary.", ["Hash for broad distribution and point access.", "Range for locality, scans, and time-oriented retention.", "Avoid monotonically growing hotspots unless splitting and placement absorb them."]),
            ("Indexes are distributed tables", "A global secondary index has its own key order and distribution. Updating one base row may synchronously update remote index entries through a transaction. That preserves SQL semantics but makes every additional index a distributed write path.", ["Align index keys with filtering, ordering, and distribution needs.", "Covering can avoid a remote base-table lookup.", "Measure write amplification and tablet hotspots."]),
            ("Joins need request locality", "A distributed optimizer tries to send predicates and joins toward the data, batch outer keys, and reduce returned rows. Co-location can help tightly coupled small tables, but requiring every relationship to share a shard key gives up much of relational flexibility.", ["Filter before crossing the network.", "Batch nested-loop keys when the inner side is indexed.", "Use denormalization only when measured communication cost justifies it."]),
            ("Transactions cross consensus groups", "Atomic commits across tablets coordinate multiple replicated groups. Serializable histories, conflict detection, clock uncertainty, and retries become visible operational concerns. This is not weaker ACID; it is ACID paying the latency required by failure tolerance and distance.", ["Keep distributed transactions focused and retryable.", "Expect contention errors as part of the API.", "Do not put irreversible external effects inside an uncommitted retry loop."]),
            ("Regions are a business decision", "Leader placement, read replicas, follower reads, and transaction geography trade freshness, latency, and resilience. A global topology should follow where writes originate and which failures the application must survive, not a generic multi-region diagram.", ["Put leaders near dominant write paths.", "State the staleness contract for local reads.", "Test failover latency and client behavior, not only server recovery."]),
        ],
        "sources": ["Foreign Keys on Distributed SQL: don't worry, it scales", "Is co-partition or interleave necessary in Distributed SQL?", "Most Complete Auto-Sharding and Partitioning Strategies", "Distributed PostgreSQL without sharding constraint for SQL joins", "Monolithic vs. Distributed SQL", "Multi-Region Distributed SQL Transaction Latency", "Global Secondary Indexes in Distributed SQL", "How to Optimize Indexing for Distributed One-to-Many Join With Pagination"],
    },
    {
        "slug": "foreign-keys-and-concurrency",
        "number": "05",
        "title": "Foreign Keys and Concurrency",
        "subtitle": "Integrity, indexes, locks, and online change",
        "description": "Why referential integrity is also a concurrency protocol, and how Oracle, PostgreSQL, and distributed SQL enforce it.",
        "accent": "#3d6b4d",
        "topics": "foreign keys · locking · migrations",
        "chapters": [
            ("A foreign key protects a relationship", "The constraint says every non-null child key references a parent key. This simple statement must remain true while parents and children are inserted, updated, and deleted concurrently. The engine therefore needs a coordination protocol, not only a validation query.", ["Parent deletion conflicts with concurrent child insertion.", "Key updates have the same integrity problem as deletes.", "Immediate and deferred checking change when violations surface."]),
            ("Locks represent intention", "When a child references a parent, the engine protects the parent key against disappearance. When a parent is removed, it must establish that no visible or in-flight child can preserve the relationship. Product lock modes differ because their row-version and lock architectures differ.", ["Waiting is often proof that integrity is being preserved.", "Inspect the blocked and blocking statements before blaming the constraint.", "Consistent lock order reduces deadlocks across related tables."]),
            ("Why Oracle often needs the child index", "Without an index beginning with foreign-key columns, Oracle may need broader child-table locking when a referenced parent key is deleted or changed. An index gives the engine a precise key range to inspect and coordinate instead of protecting an entire heap search space.", ["Index foreign keys when parent deletes or key updates occur concurrently.", "The index may also support parent-to-child navigation.", "Low-selectivity foreign keys still need a concurrency assessment."]),
            ("PostgreSQL makes a different trade", "PostgreSQL has shared row lock modes that let it protect referenced parent tuples without reproducing every Oracle table-lock pattern. An unindexed foreign key still makes parent deletes validate children by scanning, but the concurrency consequences are not identical.", ["Do not migrate Oracle indexing rules without retesting.", "Performance and locking are separate reasons for a child index.", "Observe pg_locks and the actual conflicting transactions."]),
            ("Distributed foreign keys still scale", "A distributed SQL database may read and lock keys on remote tablets, so constraint checks have network cost. Removing foreign keys trades visible database work for application races and repair work. Good distribution, batching, and indexes preserve integrity without abandoning scale.", ["Model relationships first, then optimize their physical path.", "Account for the index as a distributed write participant.", "Keep application and constraint datatypes identical."]),
            ("Add constraints online", "Large existing tables should separate enforcement of new writes from validation of old rows when the product supports it. Create a not-valid or equivalent constraint, validate existing data in a controlled phase, and monitor the locks each phase requests.", ["Clean orphan rows before final validation.", "Index supporting columns before the blocking phase when appropriate.", "Treat migration rollback and retry as part of the design."]),
        ],
        "sources": ["Script to suggest FK indexes", "Investigating Oracle lock issues with event 10704", "Create constraints in your datawarehouse - why and how", "Unindexed Foreign Keys in Oracle and PostgreSQL", "Do you need foreign keys and surrogate keys because you broke your relationships ?", "Speeding Up Foreign Key Constraints During Migrations", "Foreign Key validation in YugabyteDB when created in NOT VALID", "Best Practice: use the same datatypes for comparisons, like joins and foreign keys"],
    },
    {
        "slug": "sql-statement-lifecycle",
        "number": "06",
        "title": "The Life of a SQL Statement",
        "subtitle": "Parse, plan, execute, observe, repeat",
        "description": "Follow SQL from text and binds through parsing, optimization, execution, caching, invalidation, and runtime evidence.",
        "accent": "#76517d",
        "topics": "parsing · optimization · execution",
        "chapters": [
            ("Text becomes a database object", "Before execution, SQL text is parsed, names are resolved, privileges checked, datatypes inferred, and dependencies recorded. Small textual differences can create different cache identities even when humans read the statements as equivalent.", ["Use bind variables for values, not identifiers or syntax.", "Qualified names and search paths influence dependency resolution.", "Parsing is both semantic work and shared-cache coordination."]),
            ("The optimizer builds alternatives", "The parsed tree is transformed into equivalent relational forms. The optimizer estimates rows and costs for scans, joins, aggregation, sorting, and data movement, then selects an executable plan. Its output depends on statistics, parameters, schema, and available physical structures.", ["Optimization is constrained search, not exhaustive proof.", "Cardinality errors propagate into later choices.", "A plan is valid for a context, not universally optimal."]),
            ("Binds delay knowledge", "Bind variables improve sharing and security but hide values until execution. Oracle bind peeking and adaptive cursor sharing, and PostgreSQL custom versus generic plans, are different responses to the same tension: one cached plan may not fit every value distribution.", ["Capture the parameter values behind a slow execution.", "Separate parse-time estimates from runtime adaptation.", "Skewed workloads may need deliberate statement variants."]),
            ("Execution turns operators into work", "Plan nodes request rows from their children, allocate memory, read buffers, acquire locks, produce temporary data, and return batches to the client. Fetch size and client behavior can make a fast server plan appear slow or leave much of a plan unexecuted.", ["Distinguish startup time from total time.", "Observe buffers, rows, waits, spills, and network fetches.", "A LIMIT can stop lower nodes before their estimated total work."]),
            ("Caching avoids repeated planning", "A reusable cursor or prepared plan saves parse and optimization work. It also carries dependencies and assumptions that can become stale. DDL, statistics changes, configuration, and memory pressure can invalidate or age cached objects.", ["A soft parse is cheaper but not free.", "Hard-parse storms are both CPU and concurrency problems.", "Do not flush a whole cache to diagnose one statement."]),
            ("Stability needs controlled change", "Plan baselines and related mechanisms constrain which plans may be selected; they do not repair bad estimates or missing access paths. Use them as operational guardrails while preserving the evidence needed for a root-cause fix.", ["Record plan identity with execution statistics over time.", "Test candidate plans with representative binds.", "Allow a path for verified improvements to replace old baselines."]),
            ("Observe the complete path", "A useful trace connects application request, SQL identity, parse activity, chosen plan, waits, row counts, commit, and client fetch. Looking at only the final duration collapses distinct problems into one number.", ["Tag sessions and requests with meaningful module metadata.", "Correlate database time with application and network time.", "Keep a minimal reproducible execution with schema and binds."]),
        ],
        "sources": ["Flush one SQL statement to hard parse it again", "Oracle 12cr2 rolling invalidate window exceeded", "Multitenant internals: how object links are parsed/executed", "Enabled, accepted, fixed SQL plan baselines", "Do you use SQL plan baselines?", "Variations on 1M insert (6): CPU Flame Graph"],
    },
    {
        "slug": "database-time-and-ordering",
        "number": "07",
        "title": "Database Time and Ordering",
        "subtitle": "Clocks, commits, snapshots, and sort order",
        "description": "A precise vocabulary for the different kinds of time and order that applications ask databases to provide.",
        "accent": "#9a4f13",
        "topics": "time · ordering · consistency",
        "chapters": [
            ("There is no single database time", "Wall-clock time, transaction time, commit order, log position, and snapshot visibility answer different questions. Treating one as a substitute for another creates bugs that appear only under concurrency, failover, or clock adjustment.", ["A timestamp is a value, not proof of causality.", "Commit sequence can disagree with transaction start time.", "State which order a business requirement actually needs."]),
            ("Logical clocks order database events", "Oracle SCNs, PostgreSQL transaction identifiers and log sequence positions, and distributed hybrid clocks help engines coordinate visibility and recovery. They are implementation coordinates with specific scope and lifecycle, not universal application timestamps.", ["Use commit or log positions for replication progress.", "Account for identifier wraparound and epochs.", "Do not expose engine counters as permanent business identity."]),
            ("A snapshot defines visible history", "MVCC evaluates row versions against a snapshot. Read Committed may acquire a new snapshot for each statement, while repeatable-read modes hold a stable transaction view. Both can be correct while returning different answers after another transaction commits.", ["Name the snapshot boundary in consistency tests.", "Current does not mean globally latest in a replicated system.", "Long snapshots retain old versions and operational debt."]),
            ("Serializable is about outcomes", "Serializable execution guarantees a result equivalent to some serial order; it does not necessarily run one transaction at a time or preserve wall-clock order. Engines enforce this through locking, conflict detection, or aborts with different anomaly boundaries.", ["Build retries around the whole transaction.", "Keep external effects outside retryable database work.", "Test invariants, not only individual statements."]),
            ("SQL ordering must be requested", "Rows have no guaranteed presentation order without ORDER BY. An index can provide a useful physical order, but ties remain nondeterministic unless the query names a unique final key. Parallel and distributed execution make accidental order especially fragile.", ["Add a stable tie-breaker to user-visible lists.", "Match index prefixes to filter and order clauses.", "Never infer commit order from unordered query output."]),
            ("Distributed clocks add uncertainty", "Across regions, message delay and clock skew prevent a process from instantly knowing a universal present. Systems pay with coordination latency, expose bounded-staleness reads, or weaken which order is promised. The application must choose consciously.", ["Define maximum acceptable staleness per read path.", "Place coordination near the transactions that require it.", "Observe clock health and replication lag independently."]),
        ],
        "sources": ["SCN synchronization in distributed transactions", "Oracle serializable is not serializable", "Isolation Levels - Part I: Introduction", "Isolation Levels - Part XIII: Explicit Locking with SELECT (FOR UPDATE)", "WHERE $1::timestamptz IS NULL OR \"timestamp\" > $1", "Postgres vs. Oracle access paths IV"],
    },
    {
        "slug": "scalable-pagination",
        "number": "08",
        "title": "Scalable Pagination",
        "subtitle": "Stable pages without counting from zero",
        "description": "Design deterministic, index-backed pagination that remains fast and understandable across joins, partitions, and distributed SQL.",
        "accent": "#24706b",
        "topics": "keyset pagination · indexes · distributed queries",
        "chapters": [
            ("OFFSET counts discarded work", "OFFSET does not teleport to row N. The executor still identifies and orders earlier rows before discarding them. Later pages therefore consume increasing work, and concurrent changes can shift rows between requests.", ["Use OFFSET for small, bounded, low-change result sets.", "Measure deep pages, not only page one.", "A total count is a separate query and product decision."]),
            ("A cursor describes a position", "Keyset pagination carries the last ordered values into the next predicate. For ORDER BY created_at, id, the cursor means rows after a specific pair, not rows after an unstable ordinal position.", ["Include every ordering expression in the cursor.", "Finish with a unique tie-breaker.", "Encode cursors opaquely but keep their semantics explicit in code."]),
            ("Row-value predicates express lexicographic order", "Where supported, a tuple comparison such as (created_at, id) < ($1, $2) mirrors the composite index order. Expanded OR predicates can express the same logic but are easier to get wrong around direction and nulls.", ["Match comparison direction to ORDER BY direction.", "Define null placement or avoid nullable cursor columns.", "Use LIMIT page_size + 1 to signal another page."]),
            ("The index is the pagination engine", "An effective index begins with stable equality filters and continues with ordered cursor columns. It lets the executor seek to the boundary and stop after a small number of entries rather than sorting or scanning the full eligible set.", ["Avoid functions that hide indexable ordering expressions.", "Cover projected columns when it meaningfully avoids lookups.", "Verify actual rows read, not merely rows returned."]),
            ("Joins need bounded inner work", "Pagination over one-to-many relationships can duplicate parent rows or fetch unbounded child data. First identify the bounded set of parent keys, then join or aggregate children with indexes and batching that preserve the page boundary.", ["Define whether the page unit is a parent or joined row.", "Push LIMIT only through operations where semantics remain valid.", "Batch indexed child lookups in distributed execution."]),
            ("Partitions need a global order", "Each partition can return its local top rows, but a merge must choose the global next row. LIMIT pushdown reduces work only when partition ranges and ordering allow the executor to prove which candidates matter.", ["Align time partitions with time-oriented cursor keys.", "Expect a merge step across active partitions.", "Retain the partition key in cursors when it narrows routing."]),
        ],
        "sources": ["Pagination with an OFFSET is better without OFFSET", "Result Cache and 12c ‘fetch first n rows’", "Batched Nested Loop for Join With Large Pagination", "How to Optimize Indexing for Distributed One-to-Many Join With Pagination", "Partitions, Merge Append, Pagination, and Limit pushdown in YugabyteDB", "Equality with Multiple Values, Preserving Sort for Pagination", "Oracle Multi-Value Index and ORDER BY Pagination queries"],
    },
    {
        "slug": "postgresql-mvcc-backstage",
        "number": "09",
        "title": "PostgreSQL MVCC Backstage",
        "subtitle": "Tuple versions, visibility, vacuum, and recovery",
        "description": "Look behind PostgreSQL snapshots to understand heap tuples, index behavior, vacuum, uniqueness, and crash recovery.",
        "accent": "#345995",
        "topics": "PostgreSQL · MVCC · vacuum",
        "chapters": [
            ("Updates create tuple versions", "PostgreSQL normally updates by writing a new heap tuple version and marking the old version with transaction metadata. Readers choose the visible version for their snapshot, allowing reads and writes to overlap without returning uncommitted state.", ["xmin records the creating transaction.", "xmax participates in deletion, update, and lock state.", "Visibility also depends on commit status and the reader snapshot."]),
            ("The index points into the heap", "A regular index entry identifies a heap tuple location. Because visibility information lives primarily with heap tuples and transaction state, an index match may still require a heap visit before the row can be returned.", ["An index entry is not by itself proof of a visible row.", "Updates can leave obsolete index entries until cleanup.", "CTID is a physical locator, not durable row identity."]),
            ("The visibility map enables index-only scans", "The visibility map records pages whose tuples are all visible to all transactions. An index-only scan can trust that summary and avoid a heap check for those pages. Recent writes clear the useful state until vacuum establishes it again.", ["Coverage and all-visible state are both required.", "Heap fetches reveal how much the optimization actually helped.", "Write-heavy tables naturally have fewer all-visible pages."]),
            ("HOT keeps some updates out of indexes", "A heap-only tuple update is possible when indexed columns do not change and the page has room for the new version. PostgreSQL links versions on the same heap page, avoiding new entries in every index and reducing write amplification.", ["Fillfactor can reserve room for update-heavy tables.", "An extra index can disqualify HOT when its column changes.", "Use table statistics to observe HOT effectiveness."]),
            ("Vacuum makes reuse safe", "Vacuum determines which dead versions are no longer visible to any relevant snapshot, marks space reusable, maintains visibility information, and freezes old transaction identifiers. It works with concurrent traffic rather than compacting every table into a new file.", ["Long transactions delay cleanup eligibility.", "Autovacuum thresholds must match table size and churn.", "Anti-wraparound vacuum protects correctness, not optional tidiness."]),
            ("Uniqueness consults visibility", "A unique index may encounter an entry belonging to an in-progress, deleted, or superseded tuple. PostgreSQL coordinates with that transaction and examines heap visibility before deciding whether a new key truly conflicts.", ["Unique checking is a concurrency protocol.", "Waiting on an uncommitted key is expected behavior.", "ON CONFLICT builds on these visibility semantics."]),
            ("WAL recovers physical consistency", "Write-ahead logging records changes before corresponding data pages are considered durable. Full-page images protect recovery from torn pages after checkpoints, while crash recovery replays WAL and treats transactions without commit records as aborted.", ["A backend crash and an operating-system crash have different blast radii.", "fsync and storage guarantees are correctness settings.", "Replication reuses the ordered WAL stream for change delivery."]),
        ],
        "sources": ["PostgreSQL resolves uniqueness through heap tuple visibility", "Postgres vs. Oracle access paths II", "Postgres vs. Oracle access paths X", "What happens when a PostgreSQL backend crashes?", "Full page logging in Postgres and Oracle", "Postgres, the fsync() issue, and ‘pgio’ (the SLOB method for PostgreSQL)"],
    },
    {
        "slug": "schema-design-for-concurrency",
        "number": "10",
        "title": "Schema Design for Concurrency",
        "subtitle": "Make invariants executable",
        "description": "Move correctness from timing assumptions into keys, constraints, indexes, queues, and retryable transactions.",
        "accent": "#8a3948",
        "topics": "schema design · invariants · contention",
        "chapters": [
            ("Start with the invariant", "Concurrency bugs survive when a rule exists only in application control flow. State the invariant independently: one active reservation per seat, no negative balance, every child has a parent. Then choose the database mechanism that can evaluate it atomically.", ["Unique and exclusion constraints arbitrate competing writes.", "Foreign keys protect relationships across transactions.", "Checks protect row-local facts, not arbitrary cross-row totals."]),
            ("Read then write is not atomic", "Two transactions can both observe absence or an old value before either writes. Repeating the check in application code does not close the race. Conditional DML, constraints, locks, or serializable conflict detection must connect the decision to the write.", ["Prefer INSERT with conflict handling over check-then-insert.", "Use UPDATE ... WHERE state = expected for compare-and-set.", "Check affected row counts before reporting success."]),
            ("Keys can create hotspots", "A globally increasing key concentrates inserts on the newest index pages; a single counter row serializes every increment. These may be acceptable until concurrency crosses a threshold, but schema choices should make the contention domain intentional.", ["Do not sacrifice stable identity merely to randomize writes.", "Partition counters and queues by a meaningful business domain.", "Measure latch, lock, and tablet contention before redesigning keys."]),
            ("Queues need claim semantics", "Multiple workers must claim distinct work without blocking behind the oldest busy item. SELECT FOR UPDATE SKIP LOCKED and atomic state transitions can implement scalable claiming, provided leases, failures, and duplicate processing are part of the model.", ["Assume a worker can die after claiming work.", "Make processing idempotent or record effects transactionally.", "Order only where the business requires it."]),
            ("Indexes define conflict precision", "An index is not only a read accelerator. It lets the engine find conflicting keys and lock a narrow part of a relation. Missing or poorly ordered indexes can turn a local invariant check into broad scans, longer locks, and larger deadlock surfaces.", ["Index the keys used to find and arbitrate work.", "Keep transactions short after a lock is acquired.", "Acquire multiple logical resources in a consistent order."]),
            ("Serializable still requires retries", "Serializable isolation detects executions that cannot safely coexist and aborts one participant. The schema should minimize false contention through precise predicates and indexes, while the application treats a serialization failure as a request to replay the transaction.", ["Retry from a clean transaction boundary.", "Use bounded backoff and preserve request identity.", "Test the invariant under concurrent load, not only the happy path."]),
        ],
        "sources": ["Oracle write consistency, bug, and scalable multi-thread de-queuing", "Oracle partitioned sequences - a future new feature in 12c", "Dirty Writes, INSERT ... ON CONFLICT DO UPDATE, Read Committed Isolation Level", "Isolation Levels - part XII: To go further", "Indexing for a Scalable Serialization Isolation Level", "Do you need foreign keys and surrogate keys because you broke your relationships ?"],
    },
    {
        "slug": "oracle-to-postgresql",
        "number": "11",
        "title": "Oracle to PostgreSQL",
        "subtitle": "Translate behavior, not syntax",
        "description": "A migration field guide to the architectural differences behind plans, MVCC, indexes, datatypes, transactions, and operations.",
        "accent": "#b13b2e",
        "topics": "Oracle · PostgreSQL · migration",
        "chapters": [
            ("Compatibility is behavioral", "A converter can rewrite syntax while preserving the wrong assumptions about empty strings, implicit casts, isolation, locking, or object names. Inventory the application behaviors that matter before translating code, then test those behaviors on both systems.", ["Classify differences as syntax, semantics, performance, or operations.", "Create paired tests for critical queries and transactions.", "Do not use one product as an imperfect emulator of the other."]),
            ("Plans use different vocabularies", "Oracle and PostgreSQL expose similar physical ideas through different nodes, cost models, and instrumentation. A FULL scan resembles a sequential scan; index range access resembles an index scan, but visibility checks, bitmap mechanics, and row-location designs change the real work.", ["Compare rows, buffers, and time rather than cost numbers across products.", "Translate the purpose of a hint before seeking an equivalent.", "Refresh statistics and verify estimates after loading migrated data."]),
            ("MVCC moves the maintenance burden", "Oracle reconstructs older images largely from undo while PostgreSQL stores tuple versions in the heap and later vacuums them. This changes index access, update amplification, space reuse, long-running transaction impact, and the operational signals used to detect trouble.", ["Size and tune autovacuum as a core workload service.", "Review update-heavy tables for HOT opportunities.", "Replace undo-retention assumptions with snapshot and bloat monitoring."]),
            ("Row identity is not portable", "Oracle ROWID and PostgreSQL CTID both identify physical locations, but updates and table maintenance can change them. Neither should replace a declared business or surrogate key. PostgreSQL updates often create a new CTID as a normal consequence of MVCC.", ["Add explicit primary keys before replication or synchronization.", "Remove persisted ROWID dependencies from application contracts.", "Use physical identifiers only for controlled, immediate diagnostics."]),
            ("Index features solve different gaps", "PostgreSQL partial indexes, expression indexes, included columns, and visibility-map-dependent index-only scans do not map one-to-one to Oracle function-based, bitmap, or covering strategies. Rebuild the index set from migrated query shapes and write costs.", ["Preserve constraints before preserving incidental indexes.", "Retest null and uniqueness behavior.", "Consolidate overlapping indexes after representative workload capture."]),
            ("Transactions need semantic tests", "Oracle Read Committed consistency, Oracle's Serializable implementation, and PostgreSQL isolation levels differ in snapshot boundaries and conflict handling. Lock modes and foreign-key behavior also differ, so successful single-session tests prove little.", ["Run two-session anomaly and blocking tests.", "Implement retries for deadlocks and serialization failures.", "Verify autonomous and external side effects during transaction rewrites."]),
            ("Datatypes carry application policy", "Oracle treats an empty string as null; PostgreSQL distinguishes them. Numeric precision, timestamp zones, character padding, generated values, and implicit conversions can all change results or index use after a syntactically successful migration.", ["Profile actual values, not only declared source types.", "Make casts and timezone policy explicit at boundaries.", "Compare ordering, null handling, and round trips with production samples."]),
            ("Operations complete the migration", "AWR, ASH, SQL Plan Management, SQL*Plus, Data Guard, and RMAN responsibilities must be mapped to PostgreSQL statistics, logs, extensions, psql, replication, backup, and recovery practices. Feature names matter less than preserving the operating capability.", ["Define performance baselines before cutover.", "Practice restore and failover under the target topology.", "Train incident response on PostgreSQL wait and lock evidence."]),
        ],
        "sources": ["Postgres vs. Oracle access paths I", "Postgres vs. Oracle access paths II", "Postgres vs. Oracle access paths VI", "Server process name in Postgres and Oracle", "Full page logging in Postgres and Oracle", "B-tree block split: what's the impact?", "Following ROWIDs Through an Oracle Unique Index Update"],
    },
]

BOOKS.extend(EXTRA_BOOKS)
TECHNICAL_GUIDES.update(EXTRA_TECHNICAL_GUIDES)


def normalize(value: str) -> str:
    return " ".join(value.casefold().replace("–", "-").replace("—", "-").split())


def resolve_sources(manifest: list[dict], requested: list[str]) -> list[dict]:
    resolved = []
    for query in requested:
        needle = normalize(query)
        exact = [entry for entry in manifest if normalize(entry.get("title", "")) == needle]
        prefix = [entry for entry in manifest if normalize(entry.get("title", "")).startswith(needle + " ")]
        candidates = exact or prefix or [entry for entry in manifest if needle in normalize(entry.get("title", "")) or normalize(entry.get("title", "")) in needle]
        if not candidates:
            raise ValueError(f"No manifest article matches source title: {query}")
        entry = min(candidates, key=lambda item: abs(len(normalize(item["title"])) - len(needle)))
        resolved.append(entry)
    return resolved


def page_head(title: str, description: str, canonical: str, page_type: str = "TechArticle") -> str:
    schema = {
        "@context": "https://schema.org",
        "@type": page_type,
        "name" if page_type == "CollectionPage" else "headline": title,
        "description": description,
        "author": {"@type": "Person", "name": "Franck Pachot", "url": SITE_URL},
        "url": canonical,
    }
    return f'''<meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="description" content="{html.escape(description, quote=True)}">
  <meta name="author" content="Franck Pachot">
  <meta name="robots" content="index, follow, max-image-preview:large">
  <link rel="canonical" href="{canonical}">
  <link rel="icon" type="image/png" href="../../favicon.png">
  <meta property="og:type" content="article">
  <meta property="og:title" content="{html.escape(title, quote=True)}">
  <meta property="og:description" content="{html.escape(description, quote=True)}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:image" content="{SITE_URL}franck-pachot-linkedin.jpg">
  <title>{html.escape(title)} | Franck Pachot</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&amp;family=IBM+Plex+Sans:wght@400;500;600&amp;family=Newsreader:opsz,wght@6..72,500;600;700&amp;display=swap" rel="stylesheet">
  <link rel="stylesheet" href="../book.css">
  <script type="application/ld+json">{json.dumps(schema, ensure_ascii=False, separators=(",", ":"))}</script>'''


def render_book(book: dict, sources: list[dict], technical_guide: list[dict]) -> str:
    canonical = f"{SITE_URL}minibook/{book['slug']}/"
    chapter_count = len(book["chapters"]) + 1
    toc = "\n".join(f'        <li><a href="#chapter-{position}">{html.escape(chapter[0])}</a></li>' for position, chapter in enumerate(book["chapters"], 1))
    toc += f'\n        <li><a href="#field-manual">Field manual</a></li>'
    chapters = []
    for position, (title, lead, points) in enumerate(book["chapters"], 1):
        point_markup = "".join(f"<li>{html.escape(point)}</li>" for point in points)
        chapters.append(f'''      <section class="chapter" id="chapter-{position}">
        <p class="chapter__number">{position:02d}</p>
        <h2>{html.escape(title)}</h2>
        <p class="chapter__intro">{html.escape(lead)}</p>
        <ul class="principles">{point_markup}</ul>
      </section>''')
        technical_markup = "\n".join(
                f'''        <article class="technical-section">
                    <span>{position:02d}</span>
                    <div><h3>{html.escape(section['title'])}</h3><p>{html.escape(section['body'])}</p><pre><code>{html.escape(section['code'])}</code></pre></div>
                </article>'''
                for position, section in enumerate(technical_guide, 1)
        )
    source_markup = "\n".join(
        f'''        <a href="{html.escape(source['canonical_url'], quote=True)}"><strong>{html.escape(source['title'])}</strong><span>{html.escape(source.get('source', 'Article'))} · {html.escape(source.get('published_at', '')[:10])}</span></a>'''
        for source in sources
    )
    return f'''<!doctype html>
<html lang="en" style="--accent:{book['accent']}">
<head>
  {page_head(book['title'] + ': ' + book['subtitle'], book['description'], canonical)}
</head>
<body>
  <header class="book-bar">
    <a class="book-bar__author" href="../../"><img src="../../franck-pachot-linkedin.jpg" alt="" width="42" height="42"><span><strong>Franck Pachot</strong><small>Database Developer Advocate</small></span></a>
    <span class="book-bar__label">Minibook {book['number']} · Database field guides</span>
    <a class="book-bar__back" href="../">All minibooks</a>
  </header>
  <div class="reading-progress" aria-hidden="true"><span id="reading-progress"></span></div>
  <div class="book-layout">
    <aside class="contents" aria-label="Table of contents"><p class="contents__title">Contents</p><ol>
{toc}
        <li><a href="#sources">Sources</a></li>
      </ol><div class="contents__status"><span></span> Living minibook</div></aside>
    <main class="book">
      <header class="hero">
        <p class="eyebrow">Database field guide · {book['number']}</p>
        <h1>{html.escape(book['title'])}</h1>
        <p class="hero__subtitle">{html.escape(book['subtitle'])}</p>
        <p class="hero__lede">{html.escape(book['description'])}</p>
        <div class="hero__meta"><span>Franck Pachot</span><span>{chapter_count} chapters</span><span>{html.escape(book['topics'])}</span></div>
      </header>
    <section class="premise"><p>Build the mental model before choosing the mechanism.</p><span>This minibook was AI-generated from Franck Pachot's archived blog posts. Links to the original articles are included for source context and verification.</span></section>
{chr(10).join(chapters)}
            <section class="chapter field-manual" id="field-manual">
                <p class="chapter__number">{chapter_count:02d}</p><h2>Field manual</h2>
                <p class="chapter__intro">Concrete mechanics, diagnostic evidence, and executable patterns to carry into a real system.</p>
{technical_markup}
            </section>
      <section class="chapter resources" id="sources">
                <p class="chapter__number">{chapter_count + 1:02d}</p><h2>Source articles</h2>
                <p class="chapter__intro">Optional deep dives with the complete experiments and product-version context behind this guide.</p>
        <div class="source-grid">{source_markup}</div>
      </section>
      <footer class="book-footer"><div><strong>Franck Pachot</strong><span>🇨🇭 Database Developer Advocate</span></div><p>Product behavior changes across versions. Verify every physical claim on the system you operate.</p><a href="../">Continue through the minibook collection →</a></footer>
    </main>
  </div>
  <script src="../book.js"></script>
</body>
</html>
'''


def render_index() -> str:
        canonical = f"{SITE_URL}minibook/"
        cards = []
        isolation = {
                "slug": "sql-isolation",
                "number": "01",
                "title": "SQL Isolation Levels",
                "subtitle": "From anomalies to serializable execution",
                "description": "A practical mental model for snapshots, conflicts, explicit locking, and retries across Oracle, PostgreSQL, and distributed SQL.",
                "accent": "#a13d2d",
                "topics": "isolation · MVCC · serializability",
                "chapters": [None] * 9,
        }
        for book in [isolation, *BOOKS]:
                cards.append(f'''      <a class="collection-card" href="{book['slug']}/" style="--card-accent:{book['accent']}">
                <span class="collection-card__number">{book['number']}</span>
                <div><p>{html.escape(book['topics'])}</p><h2>{html.escape(book['title'])}</h2><strong>{html.escape(book['subtitle'])}</strong><span>{html.escape(book['description'])}</span></div>
                <small>{len(book['chapters']) + 1} chapters →</small>
            </a>''')
        volume_count = len(BOOKS) + 1
        description = f"{volume_count} AI-generated database field guides based on Franck Pachot's archived blog posts, covering SQL internals, performance, concurrency, recovery, high availability, and migration."
        return f'''<!doctype html>
<html lang="en">
<head>
    {page_head("Database Minibooks", description, canonical, "CollectionPage").replace('../../favicon.png', '../favicon.png').replace('../book.css', 'collection.css')}
</head>
<body>
    <header class="collection-nav"><a href="../"><img src="../franck-pachot-linkedin.jpg" alt="" width="42" height="42"><span><strong>Franck Pachot</strong><small>Database Developer Advocate</small></span></a><a href="../">Article archive</a></header>
    <main>
        <header class="collection-hero"><p>Database field guides · {volume_count} volumes</p><h1>Minibooks for<br>the systems<br>behind SQL.</h1><div><span>From physical storage to distributed transactions, each guide builds a compact mental model from tested database behavior.</span><strong>Read independently.<br>Connect the models.</strong></div></header>
        <section class="collection-intro"><p>AI-generated from the blog archive.</p><span>These minibooks were generated with AI from Franck Pachot's archived blog posts. Links to the original articles are retained for source context and verification.</span></section>
        <section class="collection-grid" aria-label="Minibook collection">
{chr(10).join(cards)}
        </section>
    </main>
    <footer class="collection-footer"><strong>Franck Pachot</strong><span>Database internals, performance, and distributed SQL.</span><a href="../">Search 1,200+ source articles →</a></footer>
</body>
</html>
'''


def build(root: Path) -> None:
    manifest = json.loads((root / "archive-manifest.json").read_text(encoding="utf-8"))["articles"]
    output_root = root / "minibook"
    for book in BOOKS:
        output = output_root / book["slug"]
        output.mkdir(parents=True, exist_ok=True)
        sources = resolve_sources(manifest, book["sources"])
        technical_guide = TECHNICAL_GUIDES.get(book["slug"], [])
        if len(technical_guide) < 4:
            raise ValueError(f"Technical guide requires at least four sections: {book['slug']}")
        (output / "index.html").write_text(add_google_tag(render_book(book, sources, technical_guide)), encoding="utf-8")
    (output_root / "index.html").write_text(add_google_tag(render_index()), encoding="utf-8")
    print(f"Built the collection index and {len(BOOKS)} minibooks")


if __name__ == "__main__":
    build(Path(__file__).resolve().parent.parent)
