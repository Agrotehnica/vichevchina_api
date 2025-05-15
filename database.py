from typing import Dict, Optional
from pydantic import BaseModel

# Модель ингредиента
class Ingredient(BaseModel):
    guid: str
    name: str
    total_amount: int
    bins: Dict[str, int]  # {bin_id: amount}

# Модель кормосмесителя
class FeedMixer(BaseModel):
    feed_mixer_id: str
    current_bin_id: Optional[str] = None
    current_ingredient_guid: Optional[str] = None
    current_request_id: Optional[str] = None  # добавлено

# Имитация базы данных
db = {
    "ingredients": {
        "44440ec5-4178-4e33-bd2e-74db77931d44": Ingredient(
            guid="44440ec5-4178-4e33-bd2e-74db77931d44",
            name="Corn",
            total_amount=5000,
            bins={
                "23a9d070-7f40-4c52-b82a-c0e4ca83d35f": 2301,
                "another-bin-id": 2699
            }
        )
    },
    "feed_mixers": {
        "12442309": FeedMixer(feed_mixer_id="12442309")
    },
    "requests": {}  # ключи — request_id
}

def get_db():
    return db
