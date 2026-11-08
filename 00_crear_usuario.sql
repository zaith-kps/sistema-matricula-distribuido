-- Ejecutar UNA sola vez en MySQL Workbench conectado como root.
-- Crea el usuario que usara el proyecto (no se usa root desde Python).
CREATE USER IF NOT EXISTS 'matricula'@'localhost' IDENTIFIED BY 'matricula123';
GRANT ALL PRIVILEGES ON universidad_dist.* TO 'matricula'@'localhost';
FLUSH PRIVILEGES;