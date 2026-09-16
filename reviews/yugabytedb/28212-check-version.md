# How to Check Your PostgreSQL Version

- Original: [published 2023-06-13](https://www.yugabyte.com/blog/check-postgresql-version/)
- Review cutoff: 2026-03-06
- Status: `verified-changed`
- Evidence: documentation only; no runtime test

## What was reviewed

The examples distinguish client utility versions from the connected server version and show PostgreSQL 15.1 with YugabyteDB 2.17.3.0.

## What changed

The commands and distinction remain correct, but those example versions are historical. PostgreSQL 18 is the current major release at the review cutoff, while YugabyteDB 2025.2 uses its own product version and a PostgreSQL-derived YSQL compatibility baseline.

## Evidence

- [PostgreSQL preset version parameters](https://www.postgresql.org/docs/18/runtime-config-preset.html)
- [PostgreSQL 18 documentation](https://www.postgresql.org/docs/18/)
- [YugabyteDB 2025.2 releases](https://docs.yugabyte.com/stable/releases/ybdb-releases/v2025.2/)

## Companion update

The commands in this article still answer different questions: `psql --version` reports the client, while `version()`, `SHOW server_version`, and `SHOW server_version_num` inspect the connected server. The PostgreSQL 15.1 and YugabyteDB 2.17.3.0 outputs are snapshots from 2023; PostgreSQL 18 and YugabyteDB 2025.2 are current at this review cutoff. Compare behavior against the server actually connected, not the local `psql` binary alone.