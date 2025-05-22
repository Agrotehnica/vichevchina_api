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

    total_amount = sum(bin["amount"] for bin in bins)

    # Если ингредиента вообще нет на складе
    if total_amount == 0:
        logger.warning(f"Ингредиент {ingredient_id} отсутствует во всех бункерах")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="missing"
        )

    # Если общего количества недостаточно на всём складе, возвращаем ошибку
    if total_amount < amount:
        logger.warning(f"Недостаточно ингредиента на складе: {total_amount} доступно, {amount} запрошено")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="insufficient"
        )

    # Найдём бункер с максимальным количеством ингредиента
    richest_bin = max(bins, key=lambda b: b["amount"])
    выдаётся = min(richest_bin["amount"], amount)
    статус = "success" if выдаётся == amount else "insufficient"
    logger.info(f"Отгрузка из самого полного бункера {richest_bin['bin_id']}: {выдаётся} из {amount}, всего в бункере: {richest_bin['amount']}")
    return {
        "status": статус,
        "additional_loading": выдаётся < amount,
        "amount": выдаётся,
        "bin_id": richest_bin["bin_id"]
    }

# POST /confirm_start_loading/
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

    bins = result["bins"]

    # 1.5 Проверяем общее количество на складе
    total_amount = sum(bin["amount"] for bin in bins)
    if total_amount == 0:
        logger.warning(f"Ингредиент {ingredient_id} отсутствует во всех бункерах")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="missing"
        )

    if total_amount < amount:
        logger.warning(f"Недостаточно ингредиента на складе: {total_amount} доступно, {amount} запрошено")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="insufficient"
        )

    bin_found = next((bin for bin in bins if bin["bin_id"] == bin_id), None)
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
    delivered_amount = min(bin_amount, amount)
    missing_amount = max(0, amount - delivered_amount)
    additional_loading = delivered_amount < amount
    loading_into_mixer_run = 1  # True

    if delivered_amount == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="missing"
        )

    # Формируем статус
    status_val = "success" if delivered_amount == amount else "insufficient"

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
        "missing_amount": missing_amount,
        "start_loading": True
    }
