from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from datetime import datetime, timedelta
from config import settings
from db_mysql import get_connection
from logger import logger  # импортируем логгер

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    logger.info(f"Токен создан для пользователя: {data.get('sub')}")
    return encoded_jwt

def authenticate_user(username: str, password: str) -> bool:
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            logger.info(f"Аутентификация пользователя {username}")
            sql = "SELECT * FROM users WHERE username=%s AND password=%s"
            cursor.execute(sql, (username, password))
            user = cursor.fetchone()
            found = user is not None
            if not found:
                logger.warning(f"Пользователь {username} не найден или неверный пароль")
            return found
    except Exception as e:
        logger.error(f"Ошибка при аутентификации пользователя: {e}", exc_info=True)
        raise
    finally:
        conn.close()

def get_current_user_from_token(token: str = Depends(oauth2_scheme)) -> str:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            logger.warning("В токене отсутствует sub (username)")
            raise credentials_exception
        logger.info(f"Пользователь извлечён из токена: {username}")
        return username
    except JWTError:
        logger.error("Ошибка при декодировании JWT токена", exc_info=True)
        raise credentials_exception
