from fastapi import HTTPException, status
from typing import Dict, Any
from db_mysql import get_connection
from logger import logger  # импортируем логгер

# Получить ингредиент и все его бункеры
def get_ingredient_bins_from_db(ingredient_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            logger.info(f"Ищем ингредиент {ingredient_id}")
            cursor.execute("SELECT * FROM ingredients WHERE ingredient_id=%s", (ingredient_id,))
            ingredient = cursor.fetchone()
            if not ingredient:
                return None

            cursor.execute("SELECT * FROM bins WHERE ingredient_id=%s", (ingredient_id,))
            bins = cursor.fetchall()
            logger.info(f"Найдено {len(bins)} бункеров с ингредиентом {ingredient_id}")
            return {
                "ingredient": ingredient,
                "bins": bins
            }
    finally:
        conn.close()

# Проверить наличие миксера
def mixer_exists(feed_mixer_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM mixers WHERE mixer_id=%s", (feed_mixer_id,))
            return cursor.fetchone() is not None
    finally:
        conn.close()

# POST /ingredient/
def handle_ingredient_request(data: Dict[str, Any]):
    required_fields = ["ingredient_id", "amount"]
    if not all(field in data for field in required_fields):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required fields"
        )

    ingredient_id = data["ingredient_id"]
    amount = int(data["amount"])

    logger.info(f"Запрошен ингредиент: {ingredient_id}, количество: {amount}")

    result = get_ingredient_bins_from_db(ingredient_id)
    if not result or not result["bins"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingredient not found"
        )

    bins = result["bins"]

    # 1. Проверяем, хватает ли в ОДНОМ бункере
    for bin in bins:
        if bin["amount"] >= amount:
            logger.info(f"Найден подходящий бункер: {bin['bin_id']}")
            return {
                "status": "success",
                "additional_loading": False,
                "amount": bin["amount"],
                "bin_id": bin["bin_id"]
            }

    # 2. Считаем суммарное количество во всех бункерах
    total_amount = sum(bin["amount"] for bin in bins)
    non_zero_bins = [bin for bin in bins if bin["amount"] > 0]

    # 3. Если в нескольких бункерах есть суммарно достаточно
    if len(non_zero_bins) > 1 and total_amount >= amount:
        richest_bin = max(non_zero_bins, key=lambda b: b["amount"])
        logger.info(f"Достаточно ингредиента в нескольких бункерах, выдаём богатый: {richest_bin['bin_id']}")
        return {
            "status": "insufficient",
            "additional_loading": True,
            "amount": richest_bin["amount"],
            "bin_id": richest_bin["bin_id"]
        }

    # 4. Если в одном бункере мало и в других нет вообще, или всего не хватает
    if non_zero_bins:
        bin = non_zero_bins[0]
        logger.info(f"Ингредиент есть только в одном бункере: {bin['bin_id']}")
        return {
            "status": "insufficient",
            "additional_loading": False,
            "amount": bin["amount"],
            "bin_id": bin["bin_id"]
        }

    # 5. Вообще нигде нет такого ингредиента
    logger.info(f"Ингредиент {ingredient_id} отсутствует во всех бункерах")
    return {
        "status": "missing",
        "additional_loading": False,
        "amount": 0,
        "bin_id": None
    }


def handle_confirm_start_loading(data: Dict[str, Any]):
    required_fields = ["ingredient_id", "feed_mixer_id", "bin_id", "amount"]
    if not all(field in data for field in required_fields):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required fields"
        )

    ingredient_id = data["ingredient_id"]
    feed_mixer_id = data["feed_mixer_id"]
    bin_id = data["bin_id"]
    amount = int(data["amount"])

    logger.info(f"Старт загрузки: ингредиент {ingredient_id}, миксер {feed_mixer_id}, бункер {bin_id}, количество {amount}")

    # 1. Проверяем существование ингредиента и наличие бункера
    result = get_ingredient_bins_from_db(ingredient_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingredient not found"
        )
    bin_found = next((bin for bin in result["bins"] if bin["bin_id"] == bin_id), None)
    if not bin_found:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bin not found"
        )

    # 2. Проверяем наличие миксера
    if not mixer_exists(feed_mixer_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feed mixer not found"
        )

    bin_amount = bin_found["amount"]
    additional_loading = bin_amount < amount
    delivered_amount = min(bin_amount, amount)
    loading_into_mixer_run = 1  # True

    # Формируем статус
    if bin_amount >= amount:
        status_val = "success"
    elif bin_amount > 0:
        status_val = "insufficient"
    else:
        status_val = "missing"

    # 3. Проверяем соответствие bin_id и mixer_id в bins
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT bin_id FROM bins WHERE mixer_id = %s", (feed_mixer_id,))
            row = cursor.fetchone()
            if row:
                mixer_bin_id = row["bin_id"]
                if mixer_bin_id != bin_id:
                    logger.warning(f"mixer_id '{feed_mixer_id}' обнаружен у bin_id '{mixer_bin_id}' вместо ожидаемого bin_id '{bin_id}'")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"mixer_id '{feed_mixer_id}' is found with bin_id '{mixer_bin_id}' instead of the requested bin_id '{bin_id}'."
                    )
            else:
                logger.warning(f"mixer_id '{feed_mixer_id}' не обнаржен ни у одного из бункеров")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"mixer_id '{feed_mixer_id}' is not assigned to any bin."
                )
    finally:
        conn.close()

    # 4. Сохраняем новый запрос в таблицу requests (ID автоинкремент)
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO requests (
                    mixer_id,
                    bin_id,
                    ingredient_id,
                    requested_amount,
                    loading_into_mixer_run
                ) VALUES ( %s, %s, %s, %s, %s)
            """, (
                feed_mixer_id,
                bin_id,
                ingredient_id,
                amount,
                loading_into_mixer_run
            ))
            request_id = cursor.lastrowid  # новый номер!
            logger.info(f"Запись нового запроса: request_id={request_id}, status={status_val}, requested_amount={amount}")
    finally:
        conn.close()

    return {
        "request_id": request_id,
        "status": status_val,
        "additional_loading": additional_loading,
        "amount": delivered_amount,
        "start_loading": True
    }
