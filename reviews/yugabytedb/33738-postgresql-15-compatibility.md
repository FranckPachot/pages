---
title: "Review: PostgreSQL 15 Compatibility in YugabyteDB 2.25"
article_url: https://www.yugabyte.com/blog/postgresql-15-compatibility-in-yugabytedb/
archive_path: yugabyte/articles/33738.json
published: 2025-01-31
reviewed: 2026-09-16
status: verified-changed
original_version: "2.25.0.0-b0"
reviewed_version: "2025.2.6.0-b111 (PostgreSQL 15.12-YB-2025.2.6.0-b0)"
---

# PostgreSQL 15 Compatibility in YugabyteDB 2.25: Top 15 Features!

## Update note

> Update (2026-09-16): This article tested PostgreSQL 15 features in the
> YugabyteDB 2.25 preview series. That series is now end-of-life; current supported
> releases use calendar versioning, including 2025.2 LTS and 2026.1 STS. I retested
> core `gen_random_uuid()` without `pgcrypto` on YugabyteDB 2025.2.6.0, and it still
> works as described.

## Claim reviewed

The article ran examples on `PostgreSQL 15.2-YB-2.25.0.0-b0`. Its first example
showed that `gen_random_uuid()` can generate a UUID without installing the
`pgcrypto` extension.

## What changed

The SQL behavior checked here has not changed. The release and support context has:

- `2.25` was a preview series and is now listed under end-of-life releases.
- Stable releases now use `YYYY.N.MAINTENANCE.PATCH` calendar versioning.
- At review time, YugabyteDB documentation lists `2025.2` as LTS and `2026.1` as
  STS. Preview releases are not supported for production deployment.

This review verifies one representative feature from the article, not all 15
examples.

## Verification

**Question:** Does core `gen_random_uuid()` still work without `pgcrypto` in the
current 2025.2 LTS patch release?

**Hypothesis:** The PostgreSQL 15 behavior demonstrated in 2.25 remains available
in 2025.2.6.0.

**Environment:** Docker 29.6.2 on Windows/ARM64; single-node `yugabyted`; image
`yugabytedb/yugabyte:2025.2.6.0-b111` at digest
`sha256:98ad2aa1843f73b79f8f0e5bd9e3c90f0b9d7b63aed7a22eadd72abc2dc23d67`.

**Commands:**

```sql
select version();
select extname from pg_extension where extname = 'pgcrypto';

create temporary table review_uuid (
  id uuid default gen_random_uuid() primary key
);
insert into review_uuid default values;
select id is not null as generated_without_pgcrypto from review_uuid;
```

**Observed result:** `version()` returned
`PostgreSQL 15.12-YB-2025.2.6.0-b0`. No `pgcrypto` row was present. The insert
succeeded and `generated_without_pgcrypto` returned `true`.

## Sources

- [Published article](https://www.yugabyte.com/blog/postgresql-15-compatibility-in-yugabytedb/)
- [Archived article snapshot](../../yugabyte/articles/33738.json)
- [YugabyteDB 2.25 preview release notes](https://docs.yugabyte.com/stable/releases/ybdb-releases/end-of-life/v2.25/)
- [YugabyteDB 2025.2 LTS release notes](https://docs.yugabyte.com/stable/releases/ybdb-releases/v2025.2/)
- [YugabyteDB 2026.1 STS release notes](https://docs.yugabyte.com/stable/releases/ybdb-releases/v2026.1/)
- [Release versioning and feature availability](https://docs.yugabyte.com/stable/releases/versioning/)
