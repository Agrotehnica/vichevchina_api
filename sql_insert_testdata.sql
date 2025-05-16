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

-- бункеры 
INSERT INTO bins (bin_id, ingredient_id, amount) VALUES
('01', 'A3G7H1P9QZ', 523),
('02', 'X9V2K4B7MN', 1000),
('03', 'L8J6S0U1DQ', 357),
('04', 'P4Q3W2E1ZR', 829),
('05', 'T5Y7U8I9OP', 12),
('06', 'C3V5B6N7MQ', 747),
('07', 'W2E4R6T8YQ', 405),
('08', 'H7G5F3D1SA', 0),
('09', 'M2N4B6V8CX', 951),
('10', 'S1D3F5G7HJ', 110),
('11', 'L8J6S0U1DQ', 780),
('12', 'C3V5B6N7MQ', 67),
('13', 'A3G7H1P9QZ', 633);

-- миксеры
INSERT INTO mixers (mixer_id) VALUES
('00000000000001'),
('00000000000002'),
('00000000000003'),
('00000000000004'),
('00000000000005');

-- пользователи
INSERT INTO users (username, password) VALUES
('петя', 'a7xP'),
('вася', 'K2lq');
