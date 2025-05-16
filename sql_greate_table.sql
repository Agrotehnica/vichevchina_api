-- Таблица для ингредиентов
CREATE TABLE ingredients (
    guid VARCHAR(255) PRIMARY KEY NOT NULL,
    name VARCHAR(255) NOT NULL,
    UNIQUE (name)
);

-- Таблица для бункеров
CREATE TABLE bins (
    bin_id VARCHAR(255) PRIMARY KEY NOT NULL,
    guid VARCHAR(255) NOT NULL,
    amount INT NOT NULL,
    FOREIGN KEY (guid) REFERENCES ingredients(guid)
);

-- Таблица миксеров (только ID)
CREATE TABLE mixers (
    mixer_id VARCHAR(255) PRIMARY KEY NOT NULL
);

CREATE TABLE requests (
    request_id VARCHAR(255) PRIMARY KEY NOT NULL,
    mixer_id VARCHAR(255) NOT NULL,
    bin_id VARCHAR(255) NOT NULL,
    guid VARCHAR(255) NOT NULL,
    requested_amount INT NOT NULL,
    delivered_amount INT NOT NULL,
    loading_into_mixer INT NOT NULL DEFAULT 0,
    FOREIGN KEY (mixer_id) REFERENCES mixers(mixer_id),
    FOREIGN KEY (bin_id) REFERENCES bins(bin_id),
    FOREIGN KEY (guid) REFERENCES ingredients(guid)
);

-- Таблица пользователь/пароль
CREATE TABLE users (
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    PRIMARY KEY (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

