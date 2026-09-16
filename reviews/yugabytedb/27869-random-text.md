# Generate Random Text Strings in PostgreSQL

- Original: [published 2023-05-15](https://www.yugabyte.com/blog/generate-random-text-strings-in-postgresql/)
- Review cutoff: 2026-03-06
- Status: `verified-no-change`
- Evidence: documentation only; no SQL execution

## What was reviewed

The article demonstrates SQL expressions for generating random text from random values, hashes, and selected character sets.

## Finding

The PostgreSQL functions underlying the examples remain available, and the technique is not tied to a YugabyteDB release. As originally cautioned, convenience expressions based on `random()` or MD5 are test-data techniques, not cryptographically secure token generation.

## Evidence

- [PostgreSQL string functions](https://www.postgresql.org/docs/18/functions-string.html)
- [PostgreSQL mathematical functions and random numbers](https://www.postgresql.org/docs/18/functions-math.html)

## Companion update

The SQL techniques in this 2023 article remain valid in current PostgreSQL and YSQL. Functions such as `random()`, `md5()`, `substr()`, and `string_agg()` still support the demonstrated test-data patterns. Do not use these convenience expressions where cryptographic unpredictability is a security requirement; this review checked documented semantics rather than rerunning every expression.