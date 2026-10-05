# Do Not Read Uber's Migration Story as "PostgreSQL Is Bad"

Long ago, at university, I learned about data structures from drawings on a whiteboard. One of them represented records stored in fixed-size blocks. An index did not contain the complete row. It provided a way to find the block, for example from an offset in a file, and then the record within it.

The teacher then left some empty space in each block. Why waste space? Because data is alive. A row may be updated and become larger. If the block is already packed, the database needs an overflow area, another location, or some reorganization. The course was not yet about MVCC, but the physical principle was already there: active data needs room to move.

Free space is not necessarily wasted space. A business needs available cash, not only assets. A parking lot needs lanes between the cars. A home in which every cubic centimeter is occupied may store many things, but it is no longer practical to live in. Only an archive that will never change can be packed without considering future movement.

I encountered the same idea later when working with Db2 and Oracle. Both store rows in fixed-size pages or blocks and expose a parameter named `PCTFREE`. It is the percentage left available for future changes. Oracle defaults to `PCTFREE=10`, reserving 10% of a heap block for updates to existing rows. Db2 also provides `PCTFREE`, although its default for a table page is 0, so reserving space is an explicit physical-design decision there.

Then I learned how B-trees work, and found the same principle in another structure. A B-tree leaf page cannot stay overfilled. When an entry must be inserted into a full page, the page is split and its entries are distributed. The exact occupancy after a split depends on the database implementation, insertion pattern, and index options; it is not always 50%. But the important point is that even without deleting anything, a living B-tree naturally contains partially filled pages. That free space is what allows future entries to arrive without splitting every block again.

This is also why the size immediately after a rebuild can be misleading. We can pack a table or index and celebrate the space saved, but if its normal life requires updates and inserts, page splits and new row versions will generate logs and restore the working space. It is like a severe diet before returning to the same habits: the impressive result may last only a few days before the object returns to its natural shape.

This old whiteboard lesson is how I read discussions about PostgreSQL `fillfactor`. Leaving space in a block is not a defect to eliminate. For active data, it can be the resource that avoids overflow, page splits, row movement, and additional index maintenance. The question is not how tightly we can pack the database today, but how much working space its future changes need.

PostgreSQL makes a surprising default choice here: heap tables use `fillfactor=100`. This does not guarantee that every byte of every page is occupied, because rows rarely fit page boundaries exactly. It means that inserts reserve no percentage of the page for future updates. By contrast, PostgreSQL B-tree indexes default to `fillfactor=90`, precisely because completely packed leaf pages would soon require page splits under inserts or updates.

Table and index `fillfactor` were introduced in PostgreSQL 8.2, one major release before HOT in PostgreSQL 8.3. The 8.2 release notes already described the purpose as leaving free space in pages for performance as the database grows, particularly to preserve clustering. HOT later made page-local free space even more valuable by allowing some updates to avoid new index entries.

Why, then, is the heap default still 100? I have not found a design note proving one original rationale, so I prefer the physical explanation to speculation about PostgreSQL philosophy. The database cannot know at `CREATE TABLE` time whether a table will be append-only, read-mostly, or frequently updated. Reserving 10% or 20% everywhere would make every newly loaded table larger and make scans and caches cover more pages, including for tables that never benefit from the reserve. The current documentation therefore calls complete packing the best choice for rows that are never updated, and recommends a lower value for heavily updated tables.

This does not mean that HOT is absent at `fillfactor=100`. Updates and pruning create reusable space over time, and inserts naturally advance to new pages, so later updates can still find page-local room. But on a freshly packed page there may be nothing to reclaim. For an update-heavy table, leaving the default unchanged can make the first updates pay for new tuple locations and index entries before reusable space develops. PostgreSQL avoids imposing a universal space cost, but that transfers the responsibility to us: choose a lower `fillfactor` selectively where measured update behavior justifies it.

In 2016, Uber Engineering published [Why Uber Engineering Switched from Postgres to MySQL](https://www.uber.com/blog/postgres-to-mysql-migration/). The article is still frequently referenced as evidence that PostgreSQL has an inefficient architecture for writes.

It is an interesting description of Uber's experience. It should not be read as a general verdict on PostgreSQL.

Uber explained a real migration, from PostgreSQL 9.2, for a specific workload and operational context. Their decision may have been the right one. However, the article's write-amplification explanation omits an important PostgreSQL optimization: Heap-Only Tuple updates, or HOT updates. It also does not discuss `fillfactor`, which reserves room in heap pages to make HOT updates more likely.

This omission matters because readers may conclude that every PostgreSQL update must modify every index. That is not always true.

## What Uber's example gets right

The article creates this table:

```sql
CREATE TABLE users (
    id SERIAL,
    first TEXT,
    last TEXT,
    birth_year INTEGER,
    PRIMARY KEY (id)
);

CREATE INDEX ix_users_first_last ON users (first, last);
CREATE INDEX ix_users_birth_year ON users (birth_year);
```

It then changes al-Khwarizmi's estimated birth year from 780 to 770:

```sql
UPDATE users
SET birth_year = 770
WHERE first = 'Muhammad';
```

PostgreSQL creates a new heap tuple version for the update. Because indexes contain tuple identifiers pointing to heap locations, a normal update creates new entries in all indexes. Uber counts a heap write and three index writes.

For this exact schema and update, that explanation is correct: `birth_year` is indexed. A HOT update cannot be used when a regular index references a changed column. No `fillfactor` can change this eligibility rule.

This distinction is important. The problem is not the example, but the general conclusion readers may take from it.

## What the article leaves out: HOT

PostgreSQL can avoid adding new entries to any index when both conditions are true:

1. The update does not change a column referenced by a regular index.
2. The new tuple version fits on the same heap page as the old version.

The existing index entry then points to the root of an on-page tuple chain. PostgreSQL follows that chain to the visible version. The row still has a new version for MVCC, but the indexes are not amplified by the update.

This is a Heap-Only Tuple update. It has existed since PostgreSQL 8.3, years before the Uber article and the PostgreSQL 9.2 version discussed there.

Consider a common variation of the same table:

```sql
ALTER TABLE users ADD COLUMN login_count bigint DEFAULT 0;

UPDATE users
SET login_count = login_count + 1
WHERE id = 4;
```

`login_count` is not indexed. This update is eligible for HOT. Whether it becomes HOT now depends on free space in the heap page.

## FILLFACTOR reserves update space

The default table `fillfactor` is 100. During inserts, PostgreSQL tries to fill heap pages completely. Some incidental free space may remain, and space from old versions may later be pruned and reused, but a freshly loaded page has little room for a new tuple version.

A lower `fillfactor` deliberately leaves room:

```sql
ALTER TABLE users SET (fillfactor = 90);
```

This changes the target for future inserts. Existing pages are not rearranged by this metadata change; the table must be rewritten or naturally replaced over time for the new page layout to apply.

`fillfactor=90` is not universally better. It trades denser storage and fewer pages for more opportunities to keep updates on-page and out of the indexes. The right value depends on row width, the fraction of rows updated, update frequency, indexed columns, pruning, vacuum, and read patterns.

This is why a demonstration with eight small rows is misleading. A table declared with `fillfactor=100` does not magically fill its first 8 KB page with eight rows. To observe the effect, the test must populate enough rows to form many pages and apply a representative update workload.

## Measure the workload with pgbench

The files accompanying this draft run the same workload with `fillfactor` values 100, 95, 90, 80, and 70. The table has a primary key and six secondary indexes, making unnecessary index maintenance visible.

Run this only on a disposable PostgreSQL instance. The script drops its `events` table and resets cluster-wide WAL statistics.

Run the HOT-eligible workload first:

```shell
./run.sh unindexed
```

Each transaction increments an unindexed counter for one randomly selected row:

```sql
\set id random(1, 100000)
UPDATE events SET counter = counter + 1 WHERE id = :id;
```

The script reports:

- `pgbench` throughput and latency
- `n_tup_upd` and `n_tup_hot_upd`
- the HOT update percentage
- WAL bytes generated
- heap and index sizes

Then run the boundary case:

```shell
./run.sh indexed
```

This increments a column that has an index:

```sql
\set id random(1, 100000)
UPDATE events SET indexed_value = indexed_value + 1 WHERE id = :id;
```

The HOT ratio should remain zero for every fillfactor. Reserving heap space cannot make an indexed-column change HOT.

Do not select the winner from TPS alone, and do not trust one short run in a fixed order. Repeat the sweep, reverse or randomize the order, and use a dataset larger than memory when storage behavior matters. A lower fillfactor may improve update throughput and reduce WAL while increasing heap size, cache footprint, and sequential scan work. The useful result is the smallest storage overhead that delivers a stable HOT ratio and acceptable latency for the real update mix.

## What should we conclude from Uber's article?

Uber did not claim to run a universal database benchmark. They described why their architecture, workload, PostgreSQL version, and operational history led them to build Schemaless on MySQL. The article even states that its analysis was primarily based on their experience with PostgreSQL 9.2.

The MySQL/InnoDB design they preferred has different tradeoffs. Secondary indexes point to the primary key rather than directly to a heap tuple location. This avoids one kind of index maintenance, but a secondary-index lookup normally needs another lookup through the primary key. PostgreSQL makes a different tradeoff and uses HOT to optimize many updates that do not change indexed values.

The practical lesson is not "PostgreSQL is bad" or "MySQL is bad." It is to model the actual workload:

- Which columns change?
- Which of them are indexed?
- How frequently is each row updated?
- How wide are the rows?
- What HOT ratio is observed?
- How much WAL and relation growth does the workload produce?
- What read amplification is introduced by reserving more free space?

Before accepting a broad architectural claim, measure the mechanism that applies to your schema. For PostgreSQL update-heavy tables, start with `n_tup_hot_upd`, `n_tup_upd`, WAL volume, and page density. Then choose `fillfactor` from evidence rather than from a default or a migration story.

## References

- [Why Uber Engineering Switched from Postgres to MySQL](https://www.uber.com/blog/postgres-to-mysql-migration/), Uber Engineering, 2016
- [PostgreSQL documentation: Heap-Only Tuple updates](https://www.postgresql.org/docs/current/storage-hot.html)
- [PostgreSQL documentation: CREATE TABLE storage parameters](https://www.postgresql.org/docs/current/sql-createtable.html#SQL-CREATETABLE-STORAGE-PARAMETERS)
- [PostgreSQL documentation: CREATE INDEX storage parameters](https://www.postgresql.org/docs/current/sql-createindex.html#SQL-CREATEINDEX-STORAGE-PARAMETERS)
- [PostgreSQL 8.2 release notes: introduction of FILLFACTOR](https://www.postgresql.org/docs/8.2/release-8-2.html)
- [PostgreSQL 8.3 release notes: introduction of HOT](https://www.postgresql.org/docs/8.3/release-8-3.html)
- [IBM Db2 11.5 documentation: CREATE TABLE and PCTFREE](https://www.ibm.com/docs/en/db2/11.5.x?topic=statements-create-table)
- [Oracle Database documentation: PCTFREE physical attribute](https://docs.oracle.com/en/database/oracle/oracle-database/19/sqlrf/physical_attributes_clause.html)
- [No HOT updates on JSONB (write amplification) performance impact](https://dev.to/mongodb/no-hot-updates-on-jsonb-13k7)
- [PostgreSQL 19 REPACK: Choosing the Right FILLFACTOR](https://dev.to/franckpachot/postgresql-19-repack-choosing-the-right-fillfactor-3848)
