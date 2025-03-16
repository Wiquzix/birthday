"""
Схемы Pydantic для валидации данных, связанных с сообщениями.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List


class MessageData(BaseModel):
    """Схема для данных сообщения."""
    chat_id: int = Field(..., description="ID чата пользователя в Telegram")
    text: str = Field(..., description="Текст сообщения")
    parse_mode: Optional[str] = Field("HTML", description="Режим форматирования текста")
    disable_web_page_preview: Optional[bool] = Field(False, description="Отключить предпросмотр ссылок")
    disable_notification: Optional[bool] = Field(False, description="Отключить уведомление")
    reply_to_message_id: Optional[int] = Field(None, description="ID сообщения, на которое отвечаем")


class InlineKeyboardButton(BaseModel):
    """Схема для кнопки инлайн-клавиатуры."""
    text: str = Field(..., description="Текст кнопки")
    url: Optional[str] = Field(None, description="URL для кнопки")
    callback_data: Optional[str] = Field(None, description="Данные для callback")
    web_app: Optional[Dict[str, str]] = Field(None, description="Данные для веб-приложения")


class InlineKeyboardMarkup(BaseModel):
    """Схема для инлайн-клавиатуры."""
    inline_keyboard: List[List[InlineKeyboardButton]] = Field(..., description="Кнопки клавиатуры")


class MessageWithKeyboardData(MessageData):
    """Схема для сообщения с клавиатурой."""
    reply_markup: InlineKeyboardMarkup = Field(..., description="Клавиатура для сообщения") 