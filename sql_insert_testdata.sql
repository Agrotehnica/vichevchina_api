-- указываем кодировку
SET NAMES utf8mb4;

-- миксеры
INSERT INTO mixers (mixer_id, rfid_1, rfid_2) VALUES 
('0', NULL, NULL),
('M001', 'ABC_r', 'ABC_l'),
('M002', 'CDE_r', NULL),
('M003', NULL, NULL),
('M004', NULL, NULL),
('M005', NULL, NULL);

-- ингридиенты
INSERT INTO ingredients (ingredient_id, name) VALUES
('A3G7H1P9QZ', 'Dog Chow'),
('X9V2K4B7MN', 'Whiskas'),
('L8J6S0U1DQ', 'Purina One'),
('P4Q3W2E1ZR', 'Royal Canin'),
('T5Y7U8I9OP', 'Friskies'),
('C3V5B6N7MQ', 'Pedigree'),
('W2E4R6T8YQ', 'Sheba'),
('H7G5F3D1SA', 'Hill''s Science Diet'),
('M2N4B6V8CX', 'Acana'),
('S1D3F5G7HJ', 'Pro Plan');

-- бункеры (с датами для 1 и 13 бина)
INSERT INTO bins (bin_id, ingredient_id, amount, rfid, last_loaded_at) VALUES
('01', 'A3G7H1P9QZ', 200, 'ABC_l', '2024-06-01 08:00:00'),
('02', 'X9V2K4B7MN', 1000, 'CDE_r', NULL),
('03', NULL, 357, '0', NULL),
('04', 'P4Q3W2E1ZR', 829, '0', NULL),
('05', 'T5Y7U8I9OP', 12, '0', NULL),
('06', 'C3V5B6N7MQ', 747, '0', NULL),
('07', 'W2E4R6T8YQ', 405, '0', NULL),
('08', 'H7G5F3D1SA', 0, '0', NULL),
('09', 'M2N4B6V8CX', 951, '0', NULL),
('10', 'S1D3F5G7HJ', 110, '0', NULL),
('11', 'L8J6S0U1DQ', 780, '0', NULL),
('12', 'C3V5B6N7MQ', 67, '0', NULL),
('13', 'A3G7H1P9QZ', 300, '0', '2024-05-25 15:30:00');

-- пользователи
INSERT INTO users (username, password) VALUES
('петя', 'a7xP'),
('вася', 'K2lq');