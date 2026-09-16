# Aurora DSQL: How the Latest Distributed SQL Database Compares to YugabyteDB

- Original: [published 2025-01-02](https://www.yugabyte.com/blog/aurora-dsql-compared-to-yugabytedb/)
- Review cutoff: 2026-03-06
- Status: `verified-changed`
- Evidence: AWS and YugabyteDB documentation only; no comparative runtime test

## What was reviewed

The article compares the Aurora DSQL preview announced at re:Invent 2024 with YugabyteDB, including architecture, optimistic concurrency control, SQL compatibility, and missing preview features.

## What changed

Aurora DSQL became generally available on 2025-05-27, so the preview feature list is no longer current. AWS now documents foreign keys and sequences, including identity columns. It still documents a single fixed Repeatable Read isolation level, no temporary tables, application logic instead of triggers, and SQL functions rather than PL/pgSQL. Current AWS documentation also supports `SELECT ... FOR UPDATE` and `FOR KEY SHARE`, although concurrency remains optimistic and conflicts can surface at commit.

## Evidence

- [Aurora DSQL GA announcement](https://aws.amazon.com/about-aws/whats-new/2025/05/amazon-aurora-dsql-generally-available/)
- [Aurora DSQL supported SQL](https://docs.aws.amazon.com/aurora-dsql/latest/userguide/working-with-postgresql-compatibility-supported-sql-features.html)
- [Migrating PostgreSQL to Aurora DSQL](https://docs.aws.amazon.com/aurora-dsql/latest/userguide/working-with-postgresql-compatibility-migration-guide.html)
- [YugabyteDB YSQL features](https://docs.yugabyte.com/stable/explore/ysql-language-features/)

## Companion update

This comparison captured the Aurora DSQL preview; the service became GA on 2025-05-27. AWS now documents foreign keys, sequences and identity columns, and `SELECT ... FOR UPDATE`/`FOR KEY SHARE`, so those preview limitations must not be repeated. Temporary tables, triggers, and PL/pgSQL remain unsupported in current AWS guidance, and transaction isolation is fixed at Repeatable Read with optimistic conflict handling. This review compares current documentation and does not claim a new runtime benchmark.