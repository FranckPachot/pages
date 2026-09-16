# Better Than PostgreSQL! In-Place Index Updates with YugabyteDB

- Original: [published 2024-11-25](https://www.yugabyte.com/blog/yugabytedb-in-place-index/)
- Review cutoff: 2026-03-06
- Status: `verified-no-change`
- Evidence: documentation and release history only; no performance reproduction

## What was reviewed

The article compares YugabyteDB 2.23.0 and 2.23.1, where in-place updates of non-key index values avoid deleting and reinserting an index entry. The archived article also identifies 2024.2.1 as the stable release and states that `yb_enable_inplace_index_update` is enabled by default.

## Finding

The mechanism and maturity statement remain current in 2025.2. Updating an indexed key can move the entry and is not the same case as updating an included, non-key value in place.

## Evidence

- [YSQL secondary indexes](https://docs.yugabyte.com/stable/explore/ysql-language-features/indexes-constraints/secondary-indexes-ysql/)
- [YugabyteDB 2024.2 releases](https://docs.yugabyte.com/stable/releases/ybdb-releases/v2024.2/)
- [YugabyteDB 2025.2 releases](https://docs.yugabyte.com/stable/releases/ybdb-releases/v2025.2/)

## Companion update

The version history stated in the article remains accurate: in-place index updates appeared in the 2.23.1 preview line and in the 2024.2.1 stable line, and the optimization remains enabled by default in current releases. It applies when the update can preserve the index key position, such as changing an included value; changing key columns can still require moving the entry. The original measurements were not rerun for this review.