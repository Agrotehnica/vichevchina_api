from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from auth import create_access_token, get_current_user_from_token, authenticate_user
from handlers import handle_ingredient_request, handle_confirm_start_loading
from config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="API for feed mill control system",
    version="1.0.0"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модели запросов
class IngredientRequest(BaseModel):
    ingredient_id: str
    amount: int

class ConfirmStartLoadingRequest(BaseModel):
    ingredient_id: str
    feed_mixer_id: str
    bin_id: str
    amount: int

# Новая модель для логина
class LoginRequest(BaseModel):
    username: str
    password: str

# Эндпоинт авторизации через JSON
@app.post("/login")
async def login(login_data: LoginRequest):
    if authenticate_user(login_data.username, login_data.password):
        access_token = create_access_token(data={"sub": login_data.username})
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(status_code=400, detail="Incorrect username or password")

# Защищённые эндпоинты
@app.post("/ingredient/", summary="Request ingredient loading")
async def request_ingredient_loading(
    request: IngredientRequest,
    current_user: str = Depends(get_current_user_from_token)
):
    return handle_ingredient_request(request.dict())

@app.post("/confirm_start_loading/", summary="Confirm readiness for loading")
async def confirm_start_loading(
    request: ConfirmStartLoadingRequest,
    current_user: str = Depends(get_current_user_from_token)
):
    return handle_confirm_start_loading(request.dict())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
