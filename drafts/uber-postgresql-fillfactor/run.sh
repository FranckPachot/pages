#!/usr/bin/env bash
set -euo pipefail

workload="${1:-unindexed}"
case "$workload" in
  unindexed|indexed) ;;
  *) echo "usage: $0 [unindexed|indexed]" >&2; exit 2 ;;
esac

duration="${DURATION:-15}"
clients="${CLIENTS:-8}"
jobs="${JOBS:-4}"
database="${PGDATABASE:-postgres}"
script_dir="$(cd "$(dirname "$0")" && pwd)"

echo "PostgreSQL version:"
psql -X -d "$database" -Atc "select version();"
echo "workload=$workload duration=${duration}s clients=$clients jobs=$jobs"

for fillfactor in 100 95 90 80 70; do
  echo
  echo "=== fillfactor=$fillfactor workload=$workload ==="

  psql -X -d "$database" \
    -v fillfactor="$fillfactor" \
    -f "$script_dir/setup.sql" >/dev/null

  psql -X -d "$database" -v ON_ERROR_STOP=1 <<'SQL' >/dev/null
CHECKPOINT;
SELECT pg_stat_reset_single_table_counters('events'::regclass);
SELECT pg_stat_reset_shared('wal');
SQL

  pgbench -n -M prepared \
    -c "$clients" -j "$jobs" -T "$duration" \
    -f "$script_dir/workload-${workload}.sql" \
    "$database"

  psql -X -d "$database" -P pager=off -c "
    SELECT $fillfactor AS fillfactor,
           s.n_tup_upd,
           s.n_tup_hot_upd,
           round(100.0 * s.n_tup_hot_upd / nullif(s.n_tup_upd, 0), 1) AS hot_pct,
           pg_size_pretty(w.wal_bytes) AS wal,
           pg_size_pretty(pg_table_size(s.relid)) AS heap,
           pg_size_pretty(pg_indexes_size(s.relid)) AS indexes
    FROM pg_stat_user_tables AS s
    CROSS JOIN pg_stat_wal AS w
    WHERE s.relname = 'events';"
done