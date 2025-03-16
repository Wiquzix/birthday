from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import json
import logging
from typing import Any, Dict, List
import os
from datetime import datetime
from utils.redis_advanced import increment_counter

logger = logging.getLogger(__name__)

# Явно указываем адрес Kafka
KAFKA_BOOTSTRAP_SERVERS = 'kafka:9092'

# Определяем топики
SHARE_CREATED_TOPIC = 'share_created'
USER_UPDATED_TOPIC = 'user_updated'
SEND_MESSAGE_TOPIC = 'send_message'

class KafkaClient:
    """Клиент для работы с Kafka"""
    def __init__(self):
        self.producer = None
        self.consumers: Dict[str, AIOKafkaConsumer] = {}
        
    async def start(self):
        """Инициализация Kafka producer"""
        if not self.producer:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
            await self.producer.start()
            logger.info("Kafka producer started")
    
    async def stop(self):
        """Остановка Kafka producer и consumers"""
        if self.producer:
            await self.producer.stop()
            self.producer = None
            logger.info("Kafka producer stopped")
        
        for consumer in self.consumers.values():
            await consumer.stop()
        self.consumers.clear()
        logger.info("Kafka consumers stopped")
    
    async def send_message(self, topic: str, value: Any, key: str = None):
        """Отправка сообщения в Kafka"""
        try:
            if not self.producer:
                await self.start()
            
            key_bytes = key.encode() if key else None
            await self.producer.send_and_wait(topic, value, key=key_bytes)
        except Exception as e:
            logger.error(f"Error sending message to Kafka: {str(e)}")
            raise
    
    async def get_consumer(self, topic: str, group_id: str) -> AIOKafkaConsumer:
        """Получение или создание consumer для топика"""
        consumer_key = f"{topic}_{group_id}"
        if consumer_key not in self.consumers:
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=group_id,
                value_deserializer=lambda v: json.loads(v.decode('utf-8'))
            )
            await consumer.start()
            self.consumers[consumer_key] = consumer
            logger.info(f"Created consumer for topic {topic} with group {group_id}")
        return self.consumers[consumer_key]

# Создаем глобальный экземпляр клиента
kafka_client = KafkaClient()

async def send_share_created_event(share_id: str, user_id: str, data: Dict):
    """Отправка события о создании share"""
    event = {
        'share_id': share_id,
        'user_id': user_id,
        'data': data,
        'event_type': 'share_created'
    }
    await kafka_client.send_message(SHARE_CREATED_TOPIC, event, key=share_id)
    
    # Увеличиваем счетчик созданных шар
    await increment_counter("share_created")

async def send_user_updated_event(user_id: str, data: Dict):
    """Отправка события об обновлении пользователя"""
    event = {
        'user_id': user_id,
        'data': data,
        'event_type': 'user_updated'
    }
    await kafka_client.send_message(USER_UPDATED_TOPIC, event, key=user_id)
    
    # Увеличиваем счетчик обновлений пользователей
    await increment_counter("user_updated")

async def send_telegram_message_event(message_data: Dict):
    """Отправка события для отправки сообщения через Telegram Bot API"""
    try:
        event = {
            'message_data': message_data,
            'event_type': 'send_message',
            'timestamp': datetime.now().isoformat()
        }
        logger.info(f"Sending message event to user {message_data.get('chat_id')}")
        await kafka_client.send_message(SEND_MESSAGE_TOPIC, event)
        
        # Увеличиваем счетчик отправленных сообщений
        await increment_counter("messages_sent")
        
        return True
    except Exception as e:
        logger.error(f"Error sending message event: {str(e)}")
        logger.error(f"Event data: {event}")
        return False 