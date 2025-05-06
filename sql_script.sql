-- Criação do banco de dados
CREATE DATABASE IF NOT EXISTS escola;
USE escola;

-- Criação da tabela aluno
CREATE TABLE IF NOT EXISTS aluno (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(100) NOT NULL,
    idade INT NOT NULL
);

-- Inserção de registros iniciais
INSERT INTO aluno (nome, idade) VALUES 
('Maria', 22),
('João', 20),
('Ana', 23),
('Carlos', 21),
('Beatriz', 24);