\set id random(1, 100000)
UPDATE events SET indexed_value = indexed_value + 1 WHERE id = :id;
