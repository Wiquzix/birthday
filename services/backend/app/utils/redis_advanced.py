import json
import time
from redis.asyncio import Redis
from typing import Optional, Any, List, Dict, Union, Set
import logging
from utils.config import REDIS_URL

logger = logging.getLogger(__name__)

# Создаем подключение к Redis
redis = Redis.from_url(REDIS_URL, decode_responses=True)

# Префиксы для разных типов данных
CACHE_PREFIX = "cache:"
LOCK_PREFIX = "lock:"
RATE_LIMIT_PREFIX = "rate_limit:"
COUNTER_PREFIX = "counter:"
SESSION_PREFIX = "session:"

# Время жизни по умолчанию для разных типов данных (в секундах)
DEFAULT_CACHE_TTL = 3600  # 1 час
DEFAULT_LOCK_TTL = 30     # 30 секунд
DEFAULT_RATE_LIMIT_TTL = 60  # 1 минута
DEFAULT_SESSION_TTL = 86400  # 24 часа

async def get_redis_info() -> Dict[str, Any]:
    """
    Получает информацию о состоянии Redis сервера
    :return: Словарь с информацией о Redis
    """
    try:
        info = await redis.info()
        return info
    except Exception as e:
        logger.error(f"Ошибка при получении информации о Redis: {str(e)}")
        return {}

async def get_redis_stats() -> Dict[str, Any]:
    """
    Получает статистику использования Redis
    :return: Словарь со статистикой
    """
    try:
        info = await redis.info()
        stats = {
            "used_memory": info.get("used_memory_human", "N/A"),
            "used_memory_peak": info.get("used_memory_peak_human", "N/A"),
            "total_connections_received": info.get("total_connections_received", 0),
            "total_commands_processed": info.get("total_commands_processed", 0),
            "instantaneous_ops_per_sec": info.get("instantaneous_ops_per_sec", 0),
            "keyspace_hits": info.get("keyspace_hits", 0),
            "keyspace_misses": info.get("keyspace_misses", 0),
            "hit_rate": 0
        }
        
        # Вычисляем процент попаданий в кэш
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)
        total = hits + misses
        if total > 0:
            stats["hit_rate"] = round((hits / total) * 100, 2)
            
        return stats
    except Exception as e:
        logger.error(f"Ошибка при получении статистики Redis: {str(e)}")
        return {}

async def acquire_lock(lock_name: str, owner: str, ttl: int = DEFAULT_LOCK_TTL) -> bool:
    """
    Получает блокировку с указанным именем
    :param lock_name: Имя блокировки
    :param owner: Идентификатор владельца блокировки
    :param ttl: Время жизни блокировки в секундах
    :return: True, если блокировка получена, иначе False
    """
    lock_key = f"{LOCK_PREFIX}{lock_name}"
    try:
        # Пытаемся установить блокировку, только если она еще не существует
        result = await redis.set(lock_key, owner, nx=True, ex=ttl)
        return result is not None
    except Exception as e:
        logger.error(f"Ошибка при получении блокировки {lock_name}: {str(e)}")
        return False

async def release_lock(lock_name: str, owner: str) -> bool:
    """
    Освобождает блокировку, если текущий владелец совпадает
    :param lock_name: Имя блокировки
    :param owner: Идентификатор владельца блокировки
    :return: True, если блокировка освобождена, иначе False
    """
    lock_key = f"{LOCK_PREFIX}{lock_name}"
    try:
        # Проверяем, что блокировка принадлежит указанному владельцу
        current_owner = await redis.get(lock_key)
        if current_owner != owner:
            return False
        
        # Удаляем блокировку
        await redis.delete(lock_key)
        return True
    except Exception as e:
        logger.error(f"Ошибка при освобождении блокировки {lock_name}: {str(e)}")
        return False

async def rate_limit_check(key: str, limit: int, period: int = DEFAULT_RATE_LIMIT_TTL) -> bool:
    """
    Проверяет, не превышен ли лимит запросов
    :param key: Ключ для ограничения (например, IP-адрес или user_id)
    :param limit: Максимальное количество запросов за период
    :param period: Период в секундах
    :return: True, если лимит не превышен, иначе False
    """
    rate_key = f"{RATE_LIMIT_PREFIX}{key}"
    try:
        # Получаем текущее количество запросов
        count = await redis.get(rate_key)
        
        # Если ключа нет, создаем его
        if count is None:
            await redis.set(rate_key, 1, ex=period)
            return True
        
        # Если лимит не превышен, увеличиваем счетчик
        count = int(count)
        if count < limit:
            await redis.incr(rate_key)
            return True
        
        # Лимит превышен
        return False
    except Exception as e:
        logger.error(f"Ошибка при проверке ограничения скорости для {key}: {str(e)}")
        # В случае ошибки разрешаем запрос
        return True

async def increment_counter(key: str, amount: int = 1) -> int:
    """
    Увеличивает счетчик на указанное значение
    :param key: Ключ счетчика
    :param amount: Значение для увеличения
    :return: Новое значение счетчика
    """
    counter_key = f"{COUNTER_PREFIX}{key}"
    try:
        # Увеличиваем счетчик и возвращаем новое значение
        return await redis.incrby(counter_key, amount)
    except Exception as e:
        logger.error(f"Ошибка при увеличении счетчика {key}: {str(e)}")
        return 0

async def get_counter(key: str) -> int:
    """
    Получает текущее значение счетчика
    :param key: Ключ счетчика
    :return: Текущее значение счетчика
    """
    counter_key = f"{COUNTER_PREFIX}{key}"
    try:
        value = await redis.get(counter_key)
        return int(value) if value else 0
    except Exception as e:
        logger.error(f"Ошибка при получении счетчика {key}: {str(e)}")
        return 0

async def set_session_data(session_id: str, data: Dict[str, Any], ttl: int = DEFAULT_SESSION_TTL) -> bool:
    """
    Сохраняет данные сессии
    :param session_id: Идентификатор сессии
    :param data: Данные для сохранения
    :param ttl: Время жизни сессии в секундах
    :return: True, если данные сохранены успешно
    """
    session_key = f"{SESSION_PREFIX}{session_id}"
    try:
        await redis.set(session_key, json.dumps(data), ex=ttl)
        return True
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных сессии {session_id}: {str(e)}")
        return False

async def get_session_data(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Получает данные сессии
    :param session_id: Идентификатор сессии
    :return: Данные сессии или None, если сессия не найдена
    """
    session_key = f"{SESSION_PREFIX}{session_id}"
    try:
        data = await redis.get(session_key)
        return json.loads(data) if data else None
    except Exception as e:
        logger.error(f"Ошибка при получении данных сессии {session_id}: {str(e)}")
        return None

async def update_session_data(session_id: str, data: Dict[str, Any], ttl: int = DEFAULT_SESSION_TTL) -> bool:
    """
    Обновляет данные сессии
    :param session_id: Идентификатор сессии
    :param data: Новые данные для обновления
    :param ttl: Время жизни сессии в секундах
    :return: True, если данные обновлены успешно
    """
    session_key = f"{SESSION_PREFIX}{session_id}"
    try:
        # Получаем текущие данные
        current_data = await get_session_data(session_id)
        if current_data is None:
            current_data = {}
        
        # Обновляем данные
        current_data.update(data)
        
        # Сохраняем обновленные данные
        await redis.set(session_key, json.dumps(current_data), ex=ttl)
        return True
    except Exception as e:
        logger.error(f"Ошибка при обновлении данных сессии {session_id}: {str(e)}")
        return False

async def delete_session(session_id: str) -> bool:
    """
    Удаляет сессию
    :param session_id: Идентификатор сессии
    :return: True, если сессия удалена успешно
    """
    session_key = f"{SESSION_PREFIX}{session_id}"
    try:
        await redis.delete(session_key)
        return True
    except Exception as e:
        logger.error(f"Ошибка при удалении сессии {session_id}: {str(e)}")
        return False 