"""
Схемы Pydantic для валидации данных, связанных с системными операциями.
"""
from pydantic import BaseModel, Field

class RedisStats(BaseModel):
    """Схема для статистики Redis."""
    used_memory: str
    used_memory_peak: str
    total_connections_received: int
    total_commands_processed: int
    instantaneous_ops_per_sec: int
    keyspace_hits: int
    keyspace_misses: int
    hit_rate: float


class RedisCounters(BaseModel):
    """Схема для счетчиков Redis."""
    api_requests: int
    share_created: int
    user_updated: int
    messages_sent: int = 0


class RedisMonitoringResponse(BaseModel):
    """Схема для ответа с мониторингом Redis."""
    status: str = Field("success", description="Статус операции")
    redis_stats: RedisStats
    counters: RedisCounters
