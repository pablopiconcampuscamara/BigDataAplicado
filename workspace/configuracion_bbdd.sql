-- Crear base de datos y usuario con los permisos adecuados
CREATE DATABASE IF NOT EXISTS ventas_db;
CREATE USER IF NOT EXISTS 'sqoopuser'@'%' IDENTIFIED BY 'sqooppassword';
GRANT ALL PRIVILEGES ON ventas_db.* TO 'sqoopuser'@'%';
FLUSH PRIVILEGES;

USE ventas_db;

-- 1. Crear tabla de clientes
CREATE TABLE IF NOT EXISTS clientes (
    cliente_id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    ciudad VARCHAR(50) NOT NULL,
    fecha_registro DATE NOT NULL
);

-- 2. Crear tabla de pedidos
CREATE TABLE IF NOT EXISTS pedidos (
    pedido_id INT AUTO_INCREMENT PRIMARY KEY,
    cliente_id INT NOT NULL,
    monto DECIMAL(10,2) NOT NULL,
    estado VARCHAR(20) NOT NULL,
    fecha_pedido DATETIME NOT NULL,
    FOREIGN KEY (cliente_id) REFERENCES clientes(cliente_id)
);

-- 3. Inserción masiva de 1000 clientes
DELIMITER //
DROP PROCEDURE IF EXISTS PoblarClientes//
CREATE PROCEDURE PoblarClientes()
BEGIN
    DECLARE i INT DEFAULT 1;
    WHILE i <= 1000 DO
        INSERT INTO clientes (nombre, email, ciudad, fecha_registro)
        VALUES (
            CONCAT('Cliente_', i),
            CONCAT('usuario_', i, '@ejemplo.com'),
            ELT(FLOOR(1 + RAND() * 5), 'Madrid', 'Barcelona', 'Valencia', 'Sevilla', 'Bilbao'),
            DATE_SUB(CURDATE(), INTERVAL FLOOR(RAND() * 365) DAY)
        );
        SET i = i + 1;
    END WHILE;
END//

CALL PoblarClientes()//
DROP PROCEDURE IF EXISTS PoblarClientes//
DELIMITER ;

-- 4. Inserción masiva de 1000 pedidos
DELIMITER //
DROP PROCEDURE IF EXISTS PoblarPedidos//
CREATE PROCEDURE PoblarPedidos()
BEGIN
    DECLARE j INT DEFAULT 1;
    WHILE j <= 1000 DO
        INSERT INTO pedidos (cliente_id, monto, estado, fecha_pedido)
        VALUES (
            FLOOR(1 + RAND() * 1000),
            ROUND(10 + (RAND() * 990), 2),
            ELT(FLOOR(1 + RAND() * 4), 'COMPLETADO', 'PENDIENTE', 'CANCELADO', 'PROCESANDO'),
            NOW() - INTERVAL FLOOR(RAND() * 100000) MINUTE
        );
        SET j = j + 1;
    END WHILE;
END//

CALL PoblarPedidos()//
DROP PROCEDURE IF EXISTS PoblarPedidos//
DELIMITER ;