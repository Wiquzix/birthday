import json
from redis.asyncio import Redis
from typing import Optional, Any
import logging
import asyncio
from utils.config import REDIS_URL
from datetime import date, datetime

logger = logging.getLogger(__name__)

# Создаем пользовательский JSON-энкодер для сериализации объектов типа date и datetime
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        return super().default(obj)

# Функция для создания подключения к Redis с повторными попытками
async def get_redis_connection():
    max_retries = 5
    retry_delay = 1  # начальная задержка в секундах
    
    for attempt in range(max_retries):
        try:
            # Создаем новое подключение к Redis
            connection = Redis.from_url(REDIS_URL, decode_responses=True, socket_timeout=5, socket_connect_timeout=5)
            # Проверяем подключение
            await connection.ping()
            logger.info("Успешное подключение к Redis")
            return connection
        except Exception as e:
            logger.error(f"Ошибка подключения к Redis (попытка {attempt+1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                # Увеличиваем задержку экспоненциально (backoff)
                wait_time = retry_delay * (2 ** attempt)
                logger.info(f"Повторная попытка через {wait_time} секунд...")
                await asyncio.sleep(wait_time)
            else:
                logger.error("Не удалось подключиться к Redis после нескольких попыток")
                raise

# Создаем подключение к Redis
redis = None

# Функция для получения или создания подключения к Redis
async def get_redis():
    global redis
    if redis is None:
        redis = await get_redis_connection()
    return redis

async def set_cache(key: str, value: Any, expire: int = 3600) -> None:
    """
    Сохраняет данные в кэш
    :param key: Ключ для сохранения
    :param value: Значение для сохранения (будет сериализовано в JSON)
    :param expire: Время жизни кэша в секундах (по умолчанию 1 час)
    """
    try:
        r = await get_redis()
        await r.set(key, json.dumps(value, cls=CustomJSONEncoder), ex=expire)
        logger.debug(f"Данные сохранены в кэш: {key}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении в кэш: {str(e)}")
        # Сбрасываем подключение, чтобы при следующем вызове создать новое
        global redis
        redis = None

async def get_cache(key: str) -> Optional[Any]:
    """
    Получает данные из кэша
    :param key: Ключ для получения данных
    :return: Данные из кэша или None, если данных нет
    """
    try:
        r = await get_redis()
        data = await r.get(key)
        if data:
            logger.debug(f"Данные получены из кэша: {key}")
            return json.loads(data)
        logger.debug(f"Данные не найдены в кэше: {key}")
        return None
    except Exception as e:
        logger.error(f"Ошибка при получении из кэша: {str(e)}")
        # Сбрасываем подключение, чтобы при следующем вызове создать новое
        global redis
        redis = None
        return None

async def delete_cache(key: str) -> None:
    """
    Удаляет данные из кэша
    :param key: Ключ для удаления
    """
    try:
        r = await get_redis()
        await r.delete(key)
        logger.debug(f"Данные удалены из кэша: {key}")
    except Exception as e:
        logger.error(f"Ошибка при удалении из кэша: {str(e)}")
        # Сбрасываем подключение, чтобы при следующем вызове создать новое
        global redis
        redis = None

async def clear_cache() -> None:
    """
    Очищает весь кэш
    """
    try:
        r = await get_redis()
        await r.flushdb()
        logger.debug("Кэш очищен")
    except Exception as e:
        logger.error(f"Ошибка при очистке кэша: {str(e)}")
        # Сбрасываем подключение, чтобы при следующем вызове создать новое
        global redis
        redis = None

def get_share_cache_key(share_id: str) -> str:
    """
    Генерирует ключ для кэширования данных о шаринге
    """
    return f"share:{share_id}"

def get_user_cache_key(user_id: str) -> str:
    """
    Генерирует ключ для кэширования данных пользователя
    """
    return f"user:{user_id}" 