\set id random(1, 100000)
UPDATE events SET counter = counter + 1 WHERE id = :id;
