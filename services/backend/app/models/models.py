from tortoise import fields, models
from datetime import datetime, timedelta

class User(models.Model):
    """Модель пользователя"""
    id = fields.CharField(pk=True, max_length=50)   
    first_name = fields.CharField(max_length=100)
    last_name = fields.CharField(max_length=100, null=True)
    username = fields.CharField(max_length=100, null=True)
    last_active = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "users"

class Share(models.Model):
    """Модель для хранения расшаренных данных"""
    id = fields.CharField(pk=True, max_length=50)  
    user = fields.ForeignKeyField('models.User', related_name='shares')
    birthday = fields.DateField()
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "shares"
    
    @classmethod
    async def cleanup_expired(cls):
        """Удаляет записи старше 24 часов"""
        expiration_date = datetime.now() - timedelta(hours=24)
        await cls.filter(created_at__lt=expiration_date).delete() 