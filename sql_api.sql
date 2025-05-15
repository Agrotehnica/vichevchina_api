-- Таблица для ингредиентов
CREATE TABLE ingredients (
    ingredient_id VARCHAR(255) PRIMARY KEY NOT NULL,
    name VARCHAR(255) NOT NULL
);

-- Таблица для корзин (бункеров)
CREATE TABLE bins (
    bin_id VARCHAR(255) PRIMARY KEY NOT NULL,
    ingredient_id VARCHAR(255) NOT NULL,
    amount INT NOT NULL,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(ingredient_id)
);

-- Таблица миксеров (только ID)
CREATE TABLE mixers (
    mixer_id VARCHAR(255) PRIMARY KEY NOT NULL
);

CREATE TABLE requests (
    request_id VARCHAR(255) PRIMARY KEY NOT NULL,
    mixer_id VARCHAR(255) NOT NULL,
    bin_id VARCHAR(255) NOT NULL,
    ingredient_id VARCHAR(255) NOT NULL,
    requested_amount INT NOT NULL,
    delivered_amount INT NOT NULL,
    FOREIGN KEY (mixer_id) REFERENCES mixers(mixer_id),
    FOREIGN KEY (bin_id) REFERENCES bins(bin_id),
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(ingredient_id)
);

