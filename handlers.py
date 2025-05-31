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
                logger.warning(f"Запрашиваемый ингредиент {ingredient_id} не найден в базе данных")
                raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": 404.6,
                    "message": "Ingredient id not found"}           
                            )    
                return None

            cursor.execute("SELECT * FROM bins WHERE ingredient_id=%s", (ingredient_id,))
            bins = cursor.fetchall()
            if not bins:
                logger.info(f"Бункеров с ингредиентом {ingredient_id} не найдено")
                raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "code": 404.7,
                    "message": "Ingredient bins not found"}           
                                    )

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

# Проверка общего количества
def check_amount(total_amount, ingredient_id, amount):

    # Проверка если ингредиента на складе меньше или равно 0 кг возвращаем ошибку 404.2  missing Ингредиента нет на складе
    if total_amount <= 0:
        logger.warning(f"Количество {ingredient_id} во всех бункерах меньше или равно 0")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": 400.2,
                "message": "missing"}
        )
    
    # Если общего количества недостаточно на всём складе, возвращаем ошибку с доступным количеством
    if total_amount < amount:
        logger.warning(f"Недостаточно ингредиента на складе: {total_amount} доступно, {amount} запрошено")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": 400,
                "message": "insufficient",
                "available": total_amount
            }
        )
    return True

# POST /ingredient/
def handle_ingredient_request(data: Dict[str, Any]):
    required_fields = ["ingredient_id", "amount"]
    
    if not all(field in data for field in required_fields):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ошибка запроса к БД"
        )

    ingredient_id = data["ingredient_id"]
    amount = int(data["amount"])

    result = get_ingredient_bins_from_db(ingredient_id)
    bins = result["bins"]
    total_amount = sum(bin["amount"] for bin in bins)

    logger.info(f"Запрошен ингредиент: {ingredient_id}, количество: {amount}")

    # Проверка количества ингридиента на складе 
    check_amount (total_amount, ingredient_id, amount)

    # Найдём бункер с максимальным количеством ингредиента
    richest_bin = max(bins, key=lambda b: b["amount"])
    will_be_issued = min(richest_bin["amount"], amount)
    status = "success" if will_be_issued == amount else "insufficient" # !!!!!!!!!!!!!!!!!!!!!
    logger.info(f"Отгрузка из самого полного бункера {richest_bin['bin_id']}: {will_be_issued} из {amount}, всего в бункере: {richest_bin['amount']}")
    return {
        "status": status,
        "additional_loading": will_be_issued < amount,
        "amount": will_be_issued,
        "bin_id": richest_bin["bin_id"],
        "available": total_amount
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

    # 
    result = get_ingredient_bins_from_db(ingredient_id)
    bins = result["bins"]

    # Получаем общее количество на складе
    total_amount = sum(bin["amount"] for bin in bins)

    # Проверка доступного количества ингридиента на складе 
    check_amount (total_amount, ingredient_id, amount)

    # Проверка соответствия бункер <-> ингридиент
    bin_found = next((bin for bin in bins if bin["bin_id"] == bin_id), None)
    if not bin_found:
        logger.warning(f"Бункер {bin_id} отсутствует в списке бункеров с запрошенным ингридиентом")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": 404.1,
                "message": "Bin not found"}            
        )

    # 2. Проверка соответствия rfid ↔ mixer_id
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT rfid FROM bins WHERE bin_id=%s", (bin_id,))
            row = cursor.fetchone()
            rfid = row["rfid"] if row else None
            if not rfid or rfid == '0':
                logger.warning(f"у бункера {bin_id} не обнаружена  rfid")
                raise HTTPException(
                    status_code=400,
                    detail={
                        "code": 400.6,
                        "message":"no rfid detected at bunker"}
                    )

            cursor.execute("SELECT rfid_1, rfid_2 FROM mixers WHERE mixer_id = %s", (feed_mixer_id,))
            mixer_row = cursor.fetchone()
            if not mixer_row:
                logger.warning(f"Миксер {feed_mixer_id} не найден")
                raise HTTPException(
                    status_code=404, 
                    detail={
                        "code": 400.2,
                        "message": "mixer not found"}
                )

            rfid_1, rfid_2 = mixer_row["rfid_1"], mixer_row["rfid_2"]
            if not rfid_1 and not rfid_2:
                logger.warning(f"Миксеру {feed_mixer_id} не заданы метки rfid")
                raise HTTPException(
                    status_code=400, 
                    detail={
                        "code": 400.3,
                        "message": "rfid tags missing"}
                )
        

            cursor.execute("SELECT bin_id FROM bins WHERE rfid IN (%s, %s)", (rfid_1, rfid_2))
            linked_bins = cursor.fetchall()
            linked_bin_ids = [b["bin_id"] for b in linked_bins]

            if not linked_bin_ids:
                logger.warning(f"Миксер с метками rfid {rfid_1} или {rfid_2} не обнаружен ни у одного из бункеров")
                raise HTTPException(
                    status_code=404,
                    detail={
                        "code": 404.5,
                        "message": f"Mixer with {rfid_1} or {rfid_2} was not found at any of the bunkers"}
                )

            if len(linked_bin_ids) > 1:
                logger.warning(f"Метки миксера обнаружены у нескольких бункеров: {linked_bin_ids}")
                raise HTTPException(
                    status_code=400,
                    detail={
                    "code": 400.5,
                    "message": f"rfid assigned to multiple bins"}
                    )

            if linked_bin_ids[0] != bin_id:
                logger.warning(f"Миксер с метками rfid обнаружен у bin_id {linked_bin_ids[0]} вместо ожидаемого {bin_id}")
                raise HTTPException(
                    status_code=400,
                    detail={
                        "code": 400.4,
                        "message": f"Mixer with rfid tags detected at bin_id {linked_bin_ids[0]} instead of expected {bin_id}"}
                )
    finally:
        conn.close()

    # 3. Расчёт объёма загрузки
    bin_amount = bin_found["amount"]
    delivered_amount = min(bin_amount, amount)
    missing_amount = max(0, amount - delivered_amount)
    additional_loading = delivered_amount < amount
    loading_into_mixer_run = 1  # True

#    if delivered_amount == 0:
#       logger.warning(f"Бункер {bin_id} не содержит достаточного количества ингредиента для загрузки")
#       raise HTTPException(
#           status_code=status.HTTP_400_BAD_REQUEST,
#           detail="missing"
#       )

    status_val = "success" if delivered_amount == amount else "insufficient"

    logger.info(f"Старт загрузки: ингредиент {ingredient_id}, миксер {feed_mixer_id}, бункер {bin_id}, запрощшено количество {amount}")

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
