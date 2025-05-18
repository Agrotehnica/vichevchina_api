from fastapi import HTTPException, status
from typing import Dict, Any
from db_mysql import get_connection
import uuid

# Получить ингредиент и все его бункеры
def get_ingredient_bins_from_db(ingredient_id):
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM ingredients WHERE ingredient_id=%s", (ingredient_id,))
            ingredient = cursor.fetchone()
            if not ingredient:
                return None

            cursor.execute("SELECT * FROM bins WHERE ingredient_id=%s", (ingredient_id,))
            bins = cursor.fetchall()
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
            return {
                "status": "success",
                "additional_loading": False,
                "amount": bin["amount"],
                "bin_id": bin["bin_id"]
            }

    # 2. Считаем суммарное количество во всех бункерах
    total_amount = sum(bin["amount"] for bin in bins)
    # Смотрим, есть ли вообще хоть сколько-то в бункерах
    non_zero_bins = [bin for bin in bins if bin["amount"] > 0]

    # 3. Если в нескольких бункерах есть суммарно достаточно
    if len(non_zero_bins) > 1 and total_amount >= amount:
        # Возвращаем данные по самому "богатому" бункеру (или первому с остатком)
        richest_bin = max(non_zero_bins, key=lambda b: b["amount"])
        return {
            "status": "insufficient",
            "additional_loading": True,
            "amount": richest_bin["amount"],
            "bin_id": richest_bin["bin_id"]
        }

    # 4. Если в одном бункере мало и в других нет вообще, или всего не хватает
    if non_zero_bins:
        bin = non_zero_bins[0]
        return {
            "status": "insufficient",
            "additional_loading": False,
            "amount": bin["amount"],
            "bin_id": bin["bin_id"]
        }

    # 5. Вообще нигде нет такого ингредиента
    return {
        "status": "missing",
        "additional_loading": False,
        "amount": 0,
        "bin_id": None
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

    # Проверка ингредиента и бункера
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

    # Проверка миксера
    if not mixer_exists(feed_mixer_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feed mixer not found"
        )

    bin_amount = bin_found["amount"]
    additional_loading = bin_amount < amount

    request_id = str(uuid.uuid4())
    delivered_amount = min(bin_amount, amount)
    loading_into_mixer_run = 1  # True

    # Формируем статус (добавлено!)
    if bin_amount >= amount:
        status_val = "success"
    elif bin_amount > 0:
        status_val = "insufficient"
    else:
        status_val = "missing"

    # Сохраняем новый запрос в таблицу requests
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
    finally:
        conn.close()

    return {
        "request_id": request_id,
        "status": status_val,
        "additional_loading": additional_loading,
        "amount": delivered_amount,
        "start_loading": True
    }

# функция для получения всех ингредиентов (не используется)
def get_all_ingredients():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM ingredients")
            data = cursor.fetchall()
            return data
    finally:
        conn.close()
