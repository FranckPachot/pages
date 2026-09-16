# Connecting to YugabyteDB with Arctype, a Collaborative SQL Client

- Original: [published 2021-07-23](https://www.yugabyte.com/blog/connecting-to-yugabytedb-with-arctype-a-collaborative-sql-client/)
- Review cutoff: 2026-03-06
- Status: `verified-changed`
- Evidence: documentation and current product-site behavior; no runtime test

## What was reviewed

The article used the downloadable Arctype client to demonstrate that a PostgreSQL-compatible client can connect to YSQL.

## What changed

The PostgreSQL protocol point remains valid, but the named client is no longer a current prerequisite readers can obtain as described. The Arctype website now redirects to ClickHouse, so this is a historical Arctype tutorial rather than a current setup path.

## Evidence

- [YugabyteDB PostgreSQL compatibility](https://docs.yugabyte.com/stable/reference/configuration/postgresql-compatibility/)
- [Arctype URL](https://arctype.com/)

## Companion update

This 2021 tutorial used Arctype as one example of a PostgreSQL-compatible client. YugabyteDB 2025.2 still exposes the PostgreSQL protocol, but Arctype is no longer available from the product site described here: arctype.com now redirects to ClickHouse. Use a currently maintained PostgreSQL client and the same YSQL connection parameters instead.