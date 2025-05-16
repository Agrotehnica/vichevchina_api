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
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingredient not found"
        )

    for bin in result["bins"]:
        bin_amount = bin["amount"]
        if bin_amount >= amount:
            return {
                "status": "success",
                "additional_loading": False,
                "bin_id": bin["bin_id"],
                "amount": bin_amount
            }
        elif bin_amount > 0:
            return {
                "status": "insufficient",
                "additional_loading": True,
                "bin_id": bin["bin_id"],
                "amount": bin_amount
            }

    return {"status": "missing"}

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
    loading_into_mixer = 1  # True

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
                    delivered_amount,
                    loading_into_mixer
                ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                request_id,
                feed_mixer_id,
                bin_id,
                ingredient_id,
                amount,
                delivered_amount,
                loading_into_mixer
            ))
    finally:
        conn.close()

    return {
        "request_id": request_id,
        "additional_loading": additional_loading,
        "amount": delivered_amount,
        "start_loading": True
    }

# функция для получения всех ингредиентов (не обязательно)
def get_all_ingredients():
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM ingredients")
            data = cursor.fetchall()
            return data
    finally:
        conn.close()
