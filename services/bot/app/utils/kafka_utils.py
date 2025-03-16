import json
import logging
import asyncio
from typing import Dict, Any, Optional
from aiogram import types, Dispatcher
from aiokafka import AIOKafkaConsumer
from utils.config import KAFKA_BOOTSTRAP_SERVERS
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class KafkaEventHandler:
    """Обработчик событий Kafka для бота"""
    def __init__(self, dp: Dispatcher):
        self.dp = dp
        self.consumers = {}
        self.tasks = []
        logger.info("KafkaEventHandler initialized")
        
    async def start(self):
        """Запускает обработчики событий Kafka"""
        try:
            # Создаем и запускаем consumer для каждого типа событий
            for topic in ['share_created', 'user_updated', 'send_message']:
                consumer = await self._create_consumer(topic)
                if consumer:
                    task = asyncio.create_task(self._handle_events(consumer))
                    self.tasks.append(task)
                    logger.info(f"Started consumer task for topic {topic}")
        except Exception as e:
            logger.error(f"Error starting Kafka event handlers: {e}")
            raise
    
    async def stop(self):
        """Останавливает все Kafka consumers"""
        try:
            # Отменяем все задачи
            for task in self.tasks:
                task.cancel()
            
            # Ждем завершения всех задач
            if self.tasks:
                await asyncio.gather(*self.tasks, return_exceptions=True)
            
            # Останавливаем все consumers
            for consumer in self.consumers.values():
                await consumer.stop()
            
            logger.info("All Kafka consumers stopped")
        except Exception as e:
            logger.error(f"Error stopping Kafka consumers: {e}")
    
    async def _create_consumer(self, topic: str) -> Optional[AIOKafkaConsumer]:
        """Создает и запускает consumer для указанного топика"""
        try:
            group_id = f"bot_{topic.replace('-', '_')}_handler"
            consumer = AIOKafkaConsumer(
                topic,
                bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                group_id=group_id,
                auto_offset_reset='earliest'
            )
            await consumer.start()
            self.consumers[topic] = consumer
            logger.info(f"Consumer created and started for topic {topic}")
            return consumer
        except Exception as e:
            logger.error(f"Error creating consumer for topic {topic}: {e}")
            return None
    
    async def _handle_events(self, consumer: AIOKafkaConsumer):
        """Обрабатывает события из Kafka"""
        try:
            async for msg in consumer:
                try:
                    topic = msg.topic
                    value = json.loads(msg.value.decode())

                    if topic == 'share_created':
                        await self._handle_share_created(value)
                    elif topic == 'user_updated':
                        await self._handle_user_updated(value)
                    elif topic == 'send_message':
                        await self._handle_send_message(value)

                except json.JSONDecodeError as e:
                    logger.error(f"Error decoding message: {e}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")

        except asyncio.CancelledError:
            logger.info("Consumer task was cancelled")
        except Exception as e:
            logger.error(f"Error in event handler: {e}")
    
    async def _handle_share_created(self, data: dict):
        """Обрабатывает событие создания шары"""
        try:
            logger.info(f"Processing share_created event: {data}")
            
            # Получаем данные из события
            share_id = data.get('share_id')
            user_id = data.get('user_id')
            share_data = data.get('data', {})
            
            if not share_id or not user_id:
                logger.error(f"Missing required fields in share_created event: {data}")
                return
                
            # Формируем сообщение для пользователя
            message_text = (
                f"🔄 Ваша шара с ID {share_id} успешно создана!\n\n"
                f"Данные шары:\n"
            )
            
            # Добавляем информацию о дне рождения, если она есть
            if 'birthday' in share_data:
                message_text += f"📅 День рождения: {share_data['birthday']}\n"
                
            # Добавляем информацию о времени создания
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message_text += f"\nВремя создания: {current_time}"
            
            # Отправляем сообщение пользователю
            await self.dp.bot.send_message(
                chat_id=user_id,
                text=message_text,
                parse_mode="HTML"
            )
            
            logger.info(f"Share creation notification sent to user {user_id}")
            
        except Exception as e:
            logger.error(f"Error handling share_created event: {e}")
    
    async def _handle_user_updated(self, data: dict):
        """Обрабатывает событие обновления пользователя"""
        try:
            logger.info(f"Processing user_updated event: {data}")
            user_id = data.get('user_id')
            user_data = data.get('data', {})
            if user_id:
                action = user_data.get('action')
                if action == 'created':
                    message_text = "👋 Добро пожаловать! Ваш профиль успешно создан."
                else:
                    message_text = "✅ Ваш профиль успешно обновлен."
                await self.dp.bot.send_message(chat_id=user_id, text=message_text)
        except Exception as e:
            logger.error(f"Error handling user_updated event: {e}")
            
    async def _handle_send_message(self, data: dict):
        """Обрабатывает событие отправки сообщения"""
        try:
            logger.info(f"Processing send_message event")
            message_data = data.get('message_data', {})
            
            if not message_data:
                logger.error("No message_data in event")
                return
                
            chat_id = message_data.get('chat_id')
            text = message_data.get('text')
            
            if not chat_id or not text:
                logger.error(f"Missing required fields in message_data: {message_data}")
                return
                
            # Получаем дополнительные параметры
            parse_mode = message_data.get('parse_mode', 'HTML')
            disable_web_page_preview = message_data.get('disable_web_page_preview', False)
            disable_notification = message_data.get('disable_notification', False)
            reply_to_message_id = message_data.get('reply_to_message_id')
            
            # Проверяем наличие клавиатуры
            reply_markup = None
            if 'reply_markup' in message_data:
                markup_data = message_data['reply_markup']
                if 'inline_keyboard' in markup_data:
                    keyboard = types.InlineKeyboardMarkup()
                    
                    for row in markup_data['inline_keyboard']:
                        buttons = []
                        for button_data in row:
                            button = None
                            
                            # Создаем кнопку в зависимости от типа
                            if 'url' in button_data and button_data['url']:
                                button = types.InlineKeyboardButton(
                                    text=button_data['text'],
                                    url=button_data['url']
                                )
                            elif 'callback_data' in button_data and button_data['callback_data']:
                                button = types.InlineKeyboardButton(
                                    text=button_data['text'],
                                    callback_data=button_data['callback_data']
                                )
                            elif 'web_app' in button_data and button_data['web_app']:
                                button = types.InlineKeyboardButton(
                                    text=button_data['text'],
                                    web_app=types.WebAppInfo(url=button_data['web_app']['url'])
                                )
                                
                            if button:
                                buttons.append(button)
                                
                        if buttons:
                            keyboard.row(*buttons)
                            
                    reply_markup = keyboard
            
            # Отправляем сообщение
            await self.dp.bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview,
                disable_notification=disable_notification,
                reply_to_message_id=reply_to_message_id,
                reply_markup=reply_markup
            )
            
            logger.info(f"Message sent to chat_id {chat_id}")
            
        except Exception as e:
            logger.error(f"Error handling send_message event: {e}") 