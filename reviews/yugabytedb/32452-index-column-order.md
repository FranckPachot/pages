# Improving Your SQL Indexing: How to Effectively Order Columns

- Original: [published 2024-06-17](https://www.yugabyte.com/blog/improving-sql-indexing-how-to-order-columns/)
- Review cutoff: 2026-03-06
- Status: `verified-no-change`
- Evidence: documentation only; no query-plan reproduction

## What was reviewed

Using YugabyteDB 2.21, the article orders index columns according to equality, range, ordering, filtering, and covering requirements, with distributed sharding considered separately.

## Finding

The methodology remains valid. Current YSQL still distinguishes sharding, clustering, and covering columns and supports partial and covering indexes; optimizer improvements do not remove the need to design an index around predicates and required ordering.

## Evidence

- [Design secondary indexes](https://docs.yugabyte.com/stable/develop/data-modeling/secondary-indexes-ysql/)
- [YSQL secondary indexes](https://docs.yugabyte.com/stable/explore/ysql-language-features/indexes-constraints/secondary-indexes-ysql/)
- [YSQL covering indexes](https://docs.yugabyte.com/stable/explore/ysql-language-features/indexes-constraints/covering-index-ysql/)

## Companion update

The index-ordering principles demonstrated on YugabyteDB 2.21 remain applicable to 2025.2. Equality, range, required ordering, residual filtering, and covering needs still determine useful column placement, while YSQL separately identifies index sharding and clustering columns. Confirm the result with `EXPLAIN (ANALYZE, DIST)` on representative data; this review did not rerun the plans.