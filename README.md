kormoceh_api/
│
├── app.py                # Основной файл сервера
├── config.py             # Конфигурационные параметры
├── database.py           # Работа с данными (имитация базы данных)
├── handlers.py           # Обработчики запросов
└── requirements.txt      # Зависимости


Установить зависимости:
pip install -r requirements.txt

Запустить сервер:
python app.py

Сервер доступен по адресу 127.0.0.1:8000

# запрос токена POST /login/
http -f POST http://127.0.0.1:8000/login username=admin password=password

Ответ:
{
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc0NzIzNTA3M30.8hU25wq6yAfOjL3zaSn-zybqRPS_JTpTLdhe9ErrSnU",
    "token_type": "bearer"
}



# Запрос на загрузку ингредиента POST /ingredient/ (одной строкой)
http POST http://127.0.0.1:8000/ingredient/ Authorization:"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc0OTg4MTQ1Mn0.SC8-XtROEmFtrSxtp2iZ_x-4pb1O_zGBrgVtaHzmKDo" guid="44440ec5-4178-4e33-bd2e-74db77931d44" amount:=1000

Ответ:
{
    "additional_loading": false,
    "amount": 2301,
    "bin": "101",
    "bin_id": "23a9d070-7f40-4c52-b82a-c0e4ca83d35f",
    "status": "success"
}

#Подтверждение готовности к загрузке POST /confirm_start_loading/
http POST http://127.0.0.1:8000/confirm_start_loading/ Authorization:"Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImV4cCI6MTc0OTg4MTQ1Mn0.SC8-XtROEmFtrSxtp2iZ_x-4pb1O_zGBrgVtaHzmKDo" guid="44440ec5-4178-4e33-bd2e-74db77931d44" feed_mixer_id="12442309" bin_id="23a9d070-7f40-4c52-b82a-c0e4ca83d35f" amount:=1000

Ответ:
{
    "additional_loading": false,
    "amount": 1000,
    "request_id": "de6f6bd8-e9e0-4600-8c0b-07ff4ad8589e",
    "start_loading": true
}



При неуспешной авторизации (токен истек) при запросах возворащается:
{
    "detail": "Could not validate credentials"
}