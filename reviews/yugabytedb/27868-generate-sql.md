# Generate SQL Script in PostgreSQL

- Original: [published 2023-05-22](https://www.yugabyte.com/blog/generate-sql-script-postgresql/)
- Review cutoff: 2026-03-06
- Status: `verified-no-change`
- Evidence: documentation only; no SQL execution

## What was reviewed

The article uses PostgreSQL catalog queries and `format()` to generate SQL statements, emphasizing correct identifier and literal quoting.

## Finding

The method remains current. PostgreSQL still documents `%I` for SQL identifiers and `%L` for SQL literals, which is safer than manual concatenation when generating commands.

## Evidence

- [PostgreSQL `format()`](https://www.postgresql.org/docs/18/functions-string.html#FUNCTIONS-STRING-FORMAT)
- [PostgreSQL system catalogs](https://www.postgresql.org/docs/18/catalogs.html)

## Companion update

The catalog-query and `format()` approach remains valid in PostgreSQL 18 and current YSQL. Use `%I` for identifiers and `%L` for literals so generated SQL is quoted according to SQL rules rather than assembled with ad hoc string replacement. Review generated commands before execution, especially when catalog filters span multiple schemas.