-- Таблица для ингредиентов
CREATE TABLE ingredients (
    ingredient_id VARCHAR(255) PRIMARY KEY NOT NULL,
    name VARCHAR(255) NOT NULL,
    UNIQUE (name)
);

-- Таблица для бункеров
CREATE TABLE bins (
    bin_id VARCHAR(255) PRIMARY KEY NOT NULL,
    ingredient_id VARCHAR(255) NOT NULL,
    amount INT NOT NULL ,
    mixer_id VARCHAR(255) NOT NULL DEFAULT 0,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(ingredient_id),
    FOREIGN KEY (mixer_id) REFERENCES mixers(mixer_id) 
);

-- Таблица миксеров (только ID)
CREATE TABLE mixers (
    mixer_id VARCHAR(255) PRIMARY KEY NOT NULL
);

CREATE TABLE requests (
    request_id VARCHAR(255) PRIMARY KEY NOT NULL,
    mixer_id VARCHAR(255),
    bin_id VARCHAR(255) NOT NULL,
    ingredient_id VARCHAR(255) NOT NULL,
    requested_amount INT NOT NULL,
    delivered_amount INT,
    loading_into_mixer_run INT NOT NULL DEFAULT 0,
    FOREIGN KEY (mixer_id) REFERENCES mixers(mixer_id),
    FOREIGN KEY (bin_id) REFERENCES bins(bin_id),
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(ingredient_id)
);

-- Таблица пользователь/пароль
CREATE TABLE users (
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    PRIMARY KEY (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
