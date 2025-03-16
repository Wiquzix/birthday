import json
from redis.asyncio import Redis
from typing import Optional, Any
import logging
from utils.config import REDIS_URL

logger = logging.getLogger(__name__)

# Создаем подключение к Redis
redis = Redis.from_url(REDIS_URL, decode_responses=True)

async def set_cache(key: str, value: Any, expire: int = 3600) -> None:
    """
    Сохраняет данные в кэш
    :param key: Ключ для сохранения
    :param value: Значение для сохранения (будет сериализовано в JSON)
    :param expire: Время жизни кэша в секундах (по умолчанию 1 час)
    """
    try:
        await redis.set(key, json.dumps(value), ex=expire)
        logger.debug(f"Данные сохранены в кэш: {key}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении в кэш: {str(e)}")

async def get_cache(key: str) -> Optional[Any]:
    """
    Получает данные из кэша
    :param key: Ключ для получения данных
    :return: Данные из кэша или None, если данных нет
    """
    try:
        data = await redis.get(key)
        if data:
            logger.debug(f"Данные получены из кэша: {key}")
            return json.loads(data)
        logger.debug(f"Данные не найдены в кэше: {key}")
        return None
    except Exception as e:
        logger.error(f"Ошибка при получении из кэша: {str(e)}")
        return None

async def delete_cache(key: str) -> None:
    """
    Удаляет данные из кэша
    :param key: Ключ для удаления
    """
    try:
        await redis.delete(key)
        logger.debug(f"Данные удалены из кэша: {key}")
    except Exception as e:
        logger.error(f"Ошибка при удалении из кэша: {str(e)}")

async def clear_cache() -> None:
    """
    Очищает весь кэш
    """
    try:
        await redis.flushdb()
        logger.debug("Кэш очищен")
    except Exception as e:
        logger.error(f"Ошибка при очистке кэша: {str(e)}")

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