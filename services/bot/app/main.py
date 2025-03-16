import logging
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from utils.config import BOT_TOKEN, EXTERNAL_URL, SKIP_UPDATES
from utils.kafka_utils import KafkaEventHandler
from aiogram.utils import executor

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
kafka_handler = None

@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    logger.info(f"Received /start command from user {message.from_user.id}")
    share_id = message.get_args()
    
    if not EXTERNAL_URL:
        await message.answer("Извините, приложение временно недоступно")
        return
    
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton(
        text="Открыть приложение",
        web_app=types.WebAppInfo(url=EXTERNAL_URL)
    ))
    
    await message.answer(
            "Привет! Нажмите на кнопку ниже, чтобы открыть приложение:",
            reply_markup=keyboard
        )

async def on_startup(dispatcher: Dispatcher):
    logger.info("==================================================")
    logger.info("\nЗапуск бота...")
    # Инициализация Kafka
    try:
        global kafka_handler
        kafka_handler = KafkaEventHandler(dispatcher)
        await kafka_handler.start()
        logger.info("Kafka успешно инициализирована")
    except Exception as e:
        logger.error(f"Ошибка в startup: {e}")
        raise

async def on_shutdown(dispatcher: Dispatcher):
    logger.info("Stopping Kafka handler...")
    if kafka_handler:
        await kafka_handler.stop()
    
    logger.info("\nБот остановлен")
    logger.info("==================================================\n")
    
    # Закрытие сессии бота
    await bot.session.close()

if __name__ == '__main__':
    logger.info(f"Skip updates: {SKIP_UPDATES}")    
    executor.start_polling(
        dp,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=SKIP_UPDATES,
        timeout=60,
        relax=1
    ) 