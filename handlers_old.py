from fastapi import HTTPException, status
from typing import Dict, Any
from db_mysql import get_connection
import uuid
from logger import logger  # импортируем логгер

def get_ingredient_bins_from_db(ingredient_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            logger.info(f"Ищем ингредиент {ingredient_id}")
            cursor.execute("SELECT * FROM ingredients WHERE ingredient_id=%s", (ingredient_id,))
            ingredient = cursor.fetchone()
            if not ingredient:
                logger.warning(f"Ингредиент {ingredient_id} не найден!")
                return None

            cursor.execute("SELECT * FROM bins WHERE ingredient_id=%s", (ingredient_id,))
            bins = cursor.fetchall()
            logger.info(f"Найдено {len(bins)} бункеров для ингредиента {ingredient_id}")
            return {
                "ingredient": ingredient,
                "bins": bins
            }
    except Exception as e:
        logger.error(f"Ошибка при получении данных из БД: {e}", exc_info=True)
        raise
    finally:
        conn.close()

def mixer_exists(feed_mixer_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT 1 FROM mixers WHERE mixer_id=%s", (feed_mixer_id,))
            exists = cursor.fetchone() is not None
            if not exists:
                logger.warning(f"Миксер {feed_mixer_id} не найден в базе!")
            return exists
    except Exception as e:
        logger.error(f"Ошибка при проверке миксера: {e}", exc_info=True)
        raise
    finally:
        conn.close()

def handle_ingredient_request(data: Dict[str, Any]):
    required_fields = ["ingredient_id", "amount"]
    if not all(field in data for field in required_fields):
        logger.warning("handle_ingredient_request: Не все обязательные поля присутствуют в запросе")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required fields"
        )

    ingredient_id = data["ingredient_id"]
    amount = int(data["amount"])

    logger.info(f"Запрошен ингредиент: {ingredient_id}, количество: {amount}")

    result = get_ingredient_bins_from_db(ingredient_id)
    if not result or not result["bins"]:
        logger.warning(f"Ингредиент {ingredient_id} не найден или отсутствуют бункеры!")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingredient not found"
        )

    bins = result["bins"]

    for bin in bins:
        if bin["amount"] >= amount:
            logger.info(f"Найден подходящий бункер: {bin['bin_id']}")
            return {
                "status": "success",
                "additional_loading": False,
                "amount": bin["amount"],
                "bin_id": bin["bin_id"]
            }

    total_amount = sum(bin["amount"] for bin in bins)
    non_zero_bins = [bin for bin in bins if bin["amount"] > 0]

    if len(non_zero_bins) > 1 and total_amount >= amount:
        richest_bin = max(non_zero_bins, key=lambda b: b["amount"])
        logger.info(f"Достаточно ингредиента в нескольких бункерах, выдаём богатый: {richest_bin['bin_id']}")
        return {
            "status": "insufficient",
            "additional_loading": True,
            "amount": richest_bin["amount"],
            "bin_id": richest_bin["bin_id"]
        }

    if non_zero_bins:
        bin = non_zero_bins[0]
        logger.info(f"Ингредиент есть только в одном бункере: {bin['bin_id']}")
        return {
            "status": "insufficient",
            "additional_loading": False,
            "amount": bin["amount"],
            "bin_id": bin["bin_id"]
        }

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
        logger.warning("handle_confirm_start_loading: Не все обязательные поля присутствуют в запросе")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required fields"
        )

    ingredient_id = data["ingredient_id"]
    feed_mixer_id = data["feed_mixer_id"]
    bin_id = data["bin_id"]
    amount = int(data["amount"])

    logger.info(f"Старт загрузки: ингредиент {ingredient_id}, миксер {feed_mixer_id}, бункер {bin_id}, количество {amount}")

    result = get_ingredient_bins_from_db(ingredient_id)
    if not result:
        logger.warning(f"Ингредиент {ingredient_id} не найден!")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingredient not found"
        )
    bin_found = next((bin for bin in result["bins"] if bin["bin_id"] == bin_id), None)
    if not bin_found:
        logger.warning(f"Бункер {bin_id} не найден!")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bin not found"
        )

    if not mixer_exists(feed_mixer_id):
        logger.warning(f"Миксер {feed_mixer_id} не найден!")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feed mixer not found"
        )

    bin_amount = bin_found["amount"]
    additional_loading = bin_amount < amount

    request_id = str(uuid.uuid4())
    delivered_amount = min(bin_amount, amount)
    loading_into_mixer_run = 1  # True

    if bin_amount >= amount:
        status_val = "success"
    elif bin_amount > 0:
        status_val = "insufficient"
    else:
        status_val = "missing"

    logger.info(f"Запись нового запроса: request_id={request_id}, status={status_val}, requested_amount={amount}")

    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                INSERT INTO requests (
                    request_id,
                    mixer_id,
                    bin_id,
                    ingredient_id,
                    requested_amount,
                    loading_into_mixer_run
                ) VALUES ( %s, %s, %s, %s, %s, %s)
            """, (
                request_id,
                feed_mixer_id,
                bin_id,
                ingredient_id,
                amount,
                loading_into_mixer_run
            ))
    except Exception as e:
        logger.error(f"Ошибка при записи запроса в БД: {e}", exc_info=True)
        raise
    finally:
        conn.close()

    return {
        "request_id": request_id,
        "status": status_val,
        "additional_loading": additional_loading,
        "amount": delivered_amount,
        "start_loading": True
    }

def get_all_ingredients():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM ingredients")
            data = cursor.fetchall()
            logger.info(f"Получено {len(data)} ингредиентов")
            return data
    except Exception as e:
        logger.error(f"Ошибка при получении всех ингредиентов: {e}", exc_info=True)
        raise
    finally:
        conn.close()
