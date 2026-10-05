\set ON_ERROR_STOP on

DROP TABLE IF EXISTS events;

CREATE TABLE events (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    payload text NOT NULL,
    counter bigint NOT NULL DEFAULT 0,
    indexed_value bigint NOT NULL DEFAULT 0,
    key_a integer NOT NULL,
    key_b integer NOT NULL,
    key_c integer NOT NULL,
    key_d integer NOT NULL,
    key_e integer NOT NULL
) WITH (
    fillfactor = :fillfactor,
    autovacuum_enabled = on
);

CREATE INDEX events_indexed_value_idx ON events (indexed_value);
CREATE INDEX events_key_a_idx ON events (key_a);
CREATE INDEX events_key_b_idx ON events (key_b);
CREATE INDEX events_key_c_idx ON events (key_c);
CREATE INDEX events_key_d_idx ON events (key_d);
CREATE INDEX events_key_e_idx ON events (key_e);

INSERT INTO events (payload, indexed_value, key_a, key_b, key_c, key_d, key_e)
SELECT repeat(md5(id::text), 4),
       id,
       id % 1000,
       id % 2000,
       id % 3000,
       id % 4000,
       id % 5000
FROM generate_series(1, 100000) AS id;

VACUUM (ANALYZE) events;
