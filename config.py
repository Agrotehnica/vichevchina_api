from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Feed Mill Control System API"
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200

    # --- Добавлено для MySQL ---
    MYSQL_HOST: str = "localhost"
    MYSQL_USER: str = "myuser"
    MYSQL_PASSWORD: str = "mypassword"
    MYSQL_DB: str = "feedmill_db"

    class Config:
        case_sensitive = True

settings = Settings()
