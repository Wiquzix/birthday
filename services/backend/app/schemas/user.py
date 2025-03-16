"""
Схемы Pydantic для валидации данных, связанных с пользователями.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    """Базовая схема для данных пользователя."""
    first_name: str
    last_name: Optional[str] = None
    username: Optional[str] = None


class UserResponse(UserBase):
    """Схема для ответа с данными пользователя."""
    id: str
    last_active: datetime


class UserListResponse(BaseModel):
    """Схема для ответа со списком пользователей."""
    users: List[UserResponse]
    total: int = Field(..., description="Общее количество пользователей")


class UserStatsResponse(BaseModel):
    """Схема для ответа со статистикой пользователя."""
    user: UserResponse
    shares_count: int = Field(..., description="Количество созданных шар")
    last_share_date: Optional[datetime] = Field(None, description="Дата последней созданной шары") 