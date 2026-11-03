USE ventas_db;

SHOW TABLES;

SELECT * FROM clientes LIMIT 10;

SELECT COUNT(*) AS total_clientes FROM clientes;

SELECT * FROM pedidos LIMIT 10;

SELECT COUNT(*) AS total_pedidos FROM pedidos;

EXIT;

-- Uso en terminal: Get-Content .\workspace\inspeccion_datos.sql | docker exec -i mysql mysql -u sqoopuser -psqooppassword