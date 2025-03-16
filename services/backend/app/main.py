from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import aiohttp
import logging
import ssl
import certifi
from tortoise.contrib.fastapi import register_tortoise
from utils.config import DATABASE_URL, TELEGRAM_API_URL, APP_NAME, BOT_NAME
from models.models import User, Share
from fastapi.responses import JSONResponse
from utils.redis_utils import (
    get_cache, set_cache, 
    get_share_cache_key, get_user_cache_key
)
from utils.redis_advanced import (
    get_redis_info, get_redis_stats,
    rate_limit_check, increment_counter, get_counter
)
from utils.kafka_utils import (
    kafka_client, send_share_created_event,
    send_user_updated_event, send_telegram_message_event
)
from schemas.share import (
    ShareDataRequest, ShareResponse, SharedDataResponse,
    ShareData, UserData
)
from schemas.user import (
    UserResponse, UserListResponse, UserStatsResponse
)
from schemas.system import (
    RedisMonitoringResponse
)
from schemas.message import (
    MessageData
)

# Настройка логирования
logging.basicConfig(
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация FastAPI
app = FastAPI()

# Создаем SSL контекст с проверкой сертификатов
ssl_context = ssl.create_default_context(cafile=certifi.where())

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600
)

# Добавляем middleware для логирования запросов
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Middleware для логирования запросов и ограничения скорости"""
    logger.info(f"Входящий запрос: {request.method} {request.url}")
    logger.info(f"Заголовки запроса: {request.headers}")
    
    # Увеличиваем счетчик API запросов
    await increment_counter("api_requests")
    
    # Проверяем ограничение скорости по IP
    client_ip = request.client.host
    if not await rate_limit_check(f"ip:{client_ip}", limit=100, period=60):
        logger.warning(f"Превышен лимит запросов для IP: {client_ip}")
        return JSONResponse(
            status_code=429,
            content={"detail": "Too many requests"}
        )
    
    response = await call_next(request)
    logger.info(f"Статус ответа: {response.status_code}")
    return response

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске приложения"""
    await kafka_client.start()
    logger.info("Kafka client started")

@app.on_event("shutdown")
async def shutdown_event():
    """Очистка ресурсов при остановке приложения"""
    await kafka_client.stop()
    logger.info("Kafka client stopped")

@app.post("/api/share", response_model=ShareResponse)
async def share_data(share_data: ShareDataRequest):
    """Обработка запроса на сохранение данных для шаринга"""
    try:
        logger.info(f"Получен запрос на сохранение данных: {share_data}")
        
        # Создаем или обновляем пользователя
        user = await User.get_or_none(id=str(share_data.chatId))
        if user is None:
            user = await User.create(
                id=str(share_data.chatId),
                first_name=share_data.userInfo.first_name,
                last_name=share_data.userInfo.last_name,
                username=share_data.userInfo.username
            )
            # Отправляем событие о создании пользователя
            await send_user_updated_event(user.id, {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'username': user.username,
                'action': 'created'
            })
        else:
            user.first_name = share_data.userInfo.first_name
            user.last_name = share_data.userInfo.last_name
            user.username = share_data.userInfo.username
            await user.save()
            # Отправляем событие об обновлении пользователя
            await send_user_updated_event(user.id, {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'username': user.username,
                'action': 'updated'
            })

        # Создаем запись о шаринге
        share = await Share.create(
            id=share_data.shareId,
            user=user,
            birthday=share_data.data['birthday']
        )
        
        # Отправляем событие о создании share
        await send_share_created_event(
            share.id,
            user.id,
            {'birthday': share.birthday.isoformat()}
        )
        
        # Очищаем устаревшие записи и кэш
        await Share.cleanup_expired()
        
        # Кэшируем данные пользователя
        user_cache_key = get_user_cache_key(str(share_data.chatId))
        await set_cache(user_cache_key, {
            'id': user.id,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'username': user.username,
            'last_active': user.last_active.isoformat()
        })
        
        # Кэшируем данные шаринга
        share_cache_key = get_share_cache_key(share.id)
        await set_cache(share_cache_key, {
            'share': {
                'id': share.id,
                'birthday': share.birthday.isoformat(),
                'created_at': share.created_at.isoformat()
            },
            'user': {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'username': user.username
            }
        })
        
        # Создаем ссылку для шаринга
        share_link = f"https://t.me/{BOT_NAME}/{APP_NAME}?startapp=share_{share.id}" 
        logger.info(f"Создана ссылка для шаринга: {share_link}")
        
        # Отправляем сообщение в чат через Kafka
        message_text = (
            "✅ Данные успешно сохранены!\n\n"
            "Нажмите на ссылку ниже, чтобы открыть мини-приложение с вашими данными:\n"
            "⚠️ Ссылка действительна 24 часа\n\n"
            f"{share_link}"
        )
        
        # Создаем данные сообщения
        message_data = MessageData(
            chat_id=share_data.chatId,
            text=message_text,
            parse_mode="HTML"
        )
        
        # Отправляем событие в Kafka
        success = await send_telegram_message_event(message_data.dict())
        if not success:
            logger.warning(f"Не удалось отправить сообщение пользователю {share_data.chatId}")
        
        return ShareResponse(
            status="success", 
            message="Данные успешно сохранены",
            shareId=share_data.shareId
        )
    except Exception as e:
        logger.error(f"Ошибка при обработке данных: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/share/{share_id}", response_model=SharedDataResponse)
async def get_shared_data(share_id: str):
    """Получение данных шары"""
    logger.info(f"Запрос на получение данных share_id: {share_id}")
    
    # Пробуем получить данные из кэша
    cache_key = get_share_cache_key(share_id)
    cached_data = await get_cache(cache_key)
    if cached_data:
        logger.info(f"Данные получены из кэша для share_id: {share_id}")
        return cached_data
    
    # Если данных нет в кэше, получаем из базы
    share = await Share.get_or_none(id=share_id).prefetch_related('user')
    if not share:
        logger.warning(f"Данные не найдены для share_id: {share_id}")
        raise HTTPException(status_code=404, detail="Данные не найдены")
    
    logger.info(f"Найдены данные для share_id {share_id}: {share.birthday}, пользователь: {share.user.first_name}")
    
    # Формируем ответ
    response_data = SharedDataResponse(
        share=ShareData(
            id=share.id,
            birthday=share.birthday,
            created_at=share.created_at
        ),
        user=UserData(
            first_name=share.user.first_name,
            last_name=share.user.last_name,
            username=share.user.username
        )
    )
    
    # Сохраняем в кэш
    await set_cache(cache_key, response_data.model_dump(), 3600)
    
    return response_data

@app.get("/api/user/{user_id}", response_model=UserResponse)
async def get_user_data(user_id: str):
    """Получение данных пользователя"""
    logger.info(f"Запрос на получение данных пользователя: {user_id}")
    
    # Пробуем получить данные из кэша
    cache_key = get_user_cache_key(user_id)
    cached_data = await get_cache(cache_key)
    if cached_data:
        logger.info(f"Данные получены из кэша для пользователя: {user_id}")
        return cached_data
    
    # Если данных нет в кэше, получаем из базы
    user = await User.get_or_none(id=user_id)
    if not user:
        logger.warning(f"Пользователь не найден: {user_id}")
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    # Формируем ответ
    response_data = UserResponse(
        id=user.id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        last_active=user.last_active
    )
    
    # Кэшируем данные
    await set_cache(cache_key, response_data.model_dump())
    
    return response_data

@app.get("/api/monitoring/redis", response_model=RedisMonitoringResponse)
async def get_redis_monitoring():
    """Получение информации о состоянии Redis"""
    try:
        # Получаем статистику Redis
        stats = await get_redis_stats()
        
        # Получаем счетчики запросов
        api_requests = await get_counter("api_requests")
        share_created = await get_counter("share_created")
        user_updated = await get_counter("user_updated")
        messages_sent = await get_counter("messages_sent")
        
        return RedisMonitoringResponse(
            status="success",
            redis_stats=stats,
            counters={
                "api_requests": api_requests,
                "share_created": share_created,
                "user_updated": user_updated,
                "messages_sent": messages_sent
            }
        )
    except Exception as e:
        logger.error(f"Ошибка при получении мониторинга Redis: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users", response_model=UserListResponse)
async def get_users():
    """Получение списка всех пользователей"""
    try:
        # Получаем всех пользователей
        users = await User.all()
        total = len(users)
        
        # Формируем ответ
        user_list = [
            UserResponse(
                id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                username=user.username,
                last_active=user.last_active
            ) for user in users
        ]
        
        return UserListResponse(
            users=user_list,
            total=total
        )
    except Exception as e:
        logger.error(f"Ошибка при получении списка пользователей: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/{user_id}/stats", response_model=UserStatsResponse)
async def get_user_stats(user_id: str):
    """Получение статистики пользователя"""
    try:
        # Получаем пользователя
        user = await User.get_or_none(id=user_id).prefetch_related('shares')
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        # Получаем количество шар
        shares_count = len(user.shares)
        
        # Получаем дату последней шары
        last_share_date = None
        if shares_count > 0:
            # Сортируем шары по дате создания (от новых к старым)
            sorted_shares = sorted(user.shares, key=lambda x: x.created_at, reverse=True)
            last_share_date = sorted_shares[0].created_at
        
        # Формируем ответ
        return UserStatsResponse(
            user=UserResponse(
                id=user.id,
                first_name=user.first_name,
                last_name=user.last_name,
                username=user.username,
                last_active=user.last_active
            ),
            shares_count=shares_count,
            last_share_date=last_share_date
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ошибка при получении статистики пользователя {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Регистрируем TortoiseORM
register_tortoise(
    app,
    db_url=DATABASE_URL,
    modules={"models": ["models.models"]},
    generate_schemas=True,
    add_exception_handlers=True,
)

if __name__ == "__main__":
    logger.info("Запуск сервера FastAPI")
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )