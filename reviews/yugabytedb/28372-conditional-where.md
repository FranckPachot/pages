# How to Create a Conditional WHERE Clause in PostgreSQL

- Original: [published 2023-06-26](https://www.yugabyte.com/blog/conditional-where-clause-postgresql/)
- Review cutoff: 2026-03-06
- Status: `verified-no-change`
- Evidence: documentation only; no SQL execution

## What was reviewed

The article shows how Boolean expressions, `CASE`, and parameter-aware predicates can express conditional filtering without constructing a different SQL string for every case.

## Finding

The SQL semantics are unchanged. `CASE` remains a general expression usable in `WHERE`, although direct Boolean predicates are usually clearer when they express the same condition.

## Evidence

- [PostgreSQL conditional expressions](https://www.postgresql.org/docs/18/functions-conditional.html)
- [PostgreSQL comparison predicates](https://www.postgresql.org/docs/18/functions-comparison.html)

## Companion update

The conditional-predicate patterns in this article remain valid in current PostgreSQL and YSQL. `CASE` can still appear wherever an expression is valid, including `WHERE`, while ordinary `AND`/`OR` Boolean predicates are often easier for readers and the optimizer. Parameter-sensitive plans should still be checked with `EXPLAIN` for the real data distribution.