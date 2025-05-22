-- указываем кодировку
SET NAMES utf8mb4;

-- миксеры
INSERT INTO mixers (mixer_id, rfid_1, rfid_2) VALUES 
('0', NULL, NULL),
('M001', 'rfid_001', 'rfid_002'),
('M002', 'rfid_003', NULL),
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

INSERT INTO bins (bin_id, ingredient_id, amount, mixer_id) VALUES
('01', 'A3G7H1P9QZ', 200, 'M003'),
('02', 'X9V2K4B7MN', 1000, 'M002'),
('03', 'L8J6S0U1DQ', 357, '0'),
('04', 'P4Q3W2E1ZR', 829, '0'),
('05', 'T5Y7U8I9OP', 12, '0'),
('06', 'C3V5B6N7MQ', 747, '0'),
('07', 'W2E4R6T8YQ', 405, '0'),
('08', 'H7G5F3D1SA', 0, '0'),
('09', 'M2N4B6V8CX', 951, '0'),
('10', 'S1D3F5G7HJ', 110, '0'),
('11', 'L8J6S0U1DQ', 780, '0'),
('12', 'C3V5B6N7MQ', 67, '0'),
('13', 'A3G7H1P9QZ', 300, '0');


-- пользователи
INSERT INTO users (username, password) VALUES
('петя', 'a7xP'),
('вася', 'K2lq');
