"""
Схемы Pydantic для валидации данных, связанных с шарингом информации.
"""
from pydantic import BaseModel, Field
from typing import Dict, Optional, Any
from datetime import date, datetime


class UserInfo(BaseModel):
    """Схема для информации о пользователе Telegram."""
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None


class ShareDataRequest(BaseModel):
    """Схема для входящих данных при создании шары."""
    shareId: str = Field(..., description="Уникальный идентификатор шары")
    data: Dict[str, Any] = Field(..., description="Данные для шаринга")
    chatId: int = Field(..., description="ID чата пользователя в Telegram")
    userInfo: UserInfo = Field(..., description="Информация о пользователе")


class ShareResponse(BaseModel):
    """Схема для ответа при успешном создании шары."""
    status: str = Field("success", description="Статус операции")
    message: str = Field(..., description="Сообщение о результате операции")
    shareId: str = Field(..., description="Идентификатор созданной шары")


class UserData(BaseModel):
    """Схема для данных пользователя в ответе."""
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None


class ShareData(BaseModel):
    """Схема для данных шары в ответе."""
    id: str
    birthday: date
    created_at: datetime


class SharedDataResponse(BaseModel):
    """Схема для ответа при получении данных шары."""
    share: ShareData
    user: UserData 