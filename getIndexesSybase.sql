SELECT c2.relname,
	i.indisprimary,
	i.indisunique,
	i.indisclustered,
	i.indisvalid,
	pg_catalog.pg_get_indexdef(i.indexrelid, 0, true) as indexSql,
	pg_catalog.pg_get_constraintdef(con.oid, true) as indexConstraint,
	contype,
	condeferrable,
	condeferred,
	c2.reltablespace
FROM pg_catalog.pg_class c,
	pg_catalog.pg_class c2,
	pg_catalog.pg_index i
LEFT JOIN pg_catalog.pg_constraint con ON
	(conrelid = i.indrelid
		AND conindid = i.indexrelid
		AND contype IN ('p','u','x'))
WHERE c.relname ~ '^(MY_TABLE_NAME)$'
	AND c.oid = i.indrelid
	AND i.indexrelid = c2.oid
ORDER BY i.indisprimary DESC, i.indisunique DESC, c2.relname
