-- 1. Таблица ингредиентов
CREATE TABLE ingredients (
    ingredient_id VARCHAR(255) PRIMARY KEY NOT NULL,
    name VARCHAR(255) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Таблица миксеров
CREATE TABLE mixers (
    mixer_id VARCHAR(255) PRIMARY KEY NOT NULL,
    rfid_1 VARCHAR(255) DEFAULT NULL,
    rfid_2 VARCHAR(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Таблица бункеров
CREATE TABLE bins (
    bin_id VARCHAR(255) PRIMARY KEY NOT NULL,
    ingredient_id VARCHAR(255) DEFAULT NULL,
    amount INT DEFAULT NULL,
    rfid VARCHAR(255) DEFAULT NULL,
    last_loaded_at TIMESTAMP NULL DEFAULT NULL,
    bin_status INT NOT NULL DEFAULT 0,
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(ingredient_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Таблица запросов (request_id — автоинкремент!)
CREATE TABLE requests (
    request_id INT PRIMARY KEY AUTO_INCREMENT NOT NULL,
    mixer_id VARCHAR(255),
    bin_id VARCHAR(255) NOT NULL,
    ingredient_id VARCHAR(255) NOT NULL,
    requested_amount INT NOT NULL,
    delivered_amount INT DEFAULT NULL,
    loading_into_mixer_run INT NOT NULL DEFAULT 0,
    otgruzka_start_at TIMESTAMP NULL DEFAULT NULL,
    otgruzka_end_at TIMESTAMP NULL DEFAULT NULL,
    FOREIGN KEY (mixer_id) REFERENCES mixers(mixer_id),
    FOREIGN KEY (bin_id) REFERENCES bins(bin_id),
    FOREIGN KEY (ingredient_id) REFERENCES ingredients(ingredient_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Таблица пользователей
CREATE TABLE users (
    username VARCHAR(100) PRIMARY KEY NOT NULL,
    password VARCHAR(100) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
