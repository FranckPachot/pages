# PostgreSQL HOT and fillfactor pgbench lab

This lab compares `fillfactor` values for two point-update workloads:

- `unindexed`: updates an unindexed column and can use HOT when the heap page has room.
- `indexed`: updates an indexed column and cannot use HOT at any fillfactor.

The script drops `events` and calls `pg_stat_reset_shared('wal')`. Use a disposable PostgreSQL instance and connect as a superuser.

## Run

The client needs `psql`, `pgbench`, and Bash:

```shell
export PGHOST=localhost
export PGPORT=5432
export PGUSER=postgres
export PGPASSWORD=labpass
export PGDATABASE=postgres

DURATION=60 CLIENTS=16 JOBS=8 ./run.sh unindexed
DURATION=60 CLIENTS=16 JOBS=8 ./run.sh indexed
```

For a quick disposable container where the scripts are mounted at `/bench`:

```shell
docker run --name pg-hot-lab --rm -d \
  -e POSTGRES_PASSWORD=labpass \
  -v "$PWD:/bench" \
  postgres:18

docker exec pg-hot-lab pg_isready -U postgres
docker exec -e PGUSER=postgres -e DURATION=60 \
  -e CLIENTS=16 -e JOBS=8 \
  pg-hot-lab bash /bench/run.sh unindexed

docker exec -e PGUSER=postgres -e DURATION=60 \
  -e CLIENTS=16 -e JOBS=8 \
  pg-hot-lab bash /bench/run.sh indexed

docker rm -f pg-hot-lab
```

## Interpret

Compare all of these, not TPS alone:

- HOT percentage: `n_tup_hot_upd / n_tup_upd`
- WAL generated during the run
- heap and index sizes
- average latency and TPS from `pgbench`

Repeat each point multiple times and change the test order to expose cache, checkpoint, and thermal bias. Increase the row count in `setup.sql` beyond available memory if the question includes physical storage behavior. Replace the synthetic update mix with captured application proportions before choosing a production fillfactor.