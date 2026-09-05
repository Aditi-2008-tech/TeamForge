CREATE DATABASE teamforge;
USE teamforge;
CREATE TABLE test_users { id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(100) NOT NULL };
INSERT INTO test_users(name) VALUES('Test Student');
SELECT * FROM test_users;