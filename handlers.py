from fastapi import HTTPException, status
from typing import Dict, Any
from database import get_db, Ingredient, FeedMixer
import uuid

db = get_db()

# POST /ingredient/
def handle_ingredient_request(data: Dict[str, Any]):
    required_fields = ["guid", "amount"]
    if not all(field in data for field in required_fields):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required fields"
        )
    
    guid = data["guid"]
    amount = int(data["amount"])
    
    if guid not in db["ingredients"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingredient not found"
        )
    
    ingredient = db["ingredients"][guid]
    
    for bin_id, bin_amount in ingredient.bins.items():
        if bin_amount >= amount:
            return {
                "status": "success",
                "additional_loading": False,
                "bin": "101",  # Условный номер
                "bin_id": bin_id,
                "amount": bin_amount
            }
        elif bin_amount > 0:
            return {
                "status": "insufficient",
                "additional_loading": True,
                "bin": "101",
                "bin_id": bin_id,
                "amount": bin_amount
            }

    return {"status": "missing"}

# POST /confirm_start_loading/
def handle_confirm_start_loading(data: Dict[str, Any]):
    required_fields = ["guid", "feed_mixer_id", "bin_id", "amount"]
    if not all(field in data for field in required_fields):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing required fields"
        )
    
    guid = data["guid"]
    feed_mixer_id = data["feed_mixer_id"]
    bin_id = data["bin_id"]
    amount = int(data["amount"])
    
    if guid not in db["ingredients"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ingredient not found"
        )
    
    if feed_mixer_id not in db["feed_mixers"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Feed mixer not found"
        )
    
    ingredient = db["ingredients"][guid]
    
    if bin_id not in ingredient.bins:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bin not found"
        )
    
    bin_amount = ingredient.bins[bin_id]
    additional_loading = bin_amount < amount

    # Генерация и сохранение request_id
    request_id = str(uuid.uuid4())
    db["requests"][request_id] = {
        "request_id": request_id,
        "feed_mixer_id": feed_mixer_id,
        "current_bin_id": bin_id,
        "current_ingredient_guid": guid
    }

    # Обновляем состояние миксера
    mixer = db["feed_mixers"][feed_mixer_id]
    mixer.current_bin_id = bin_id
    mixer.current_ingredient_guid = guid
    mixer.current_request_id = request_id

    return {
        "additional_loading": additional_loading,
        "request_id": request_id,
        "start_loading": True,
        "amount": min(bin_amount, amount)
    }
