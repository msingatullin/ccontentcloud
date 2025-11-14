"""
Модели пользователей для системы аутентификации
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from app.database.connection import Base
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import string


class UserRole(str, Enum):
    """Роли пользователей"""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"


class UserStatus(str, Enum):
    """Статусы пользователей"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class User(Base):
    """Модель пользователя"""
    __tablename__ = 'users'

    # Основные поля
    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Персональная информация
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    company = Column(String(200), nullable=True)
    position = Column(String(100), nullable=True)
    
    # Статус и роли
    role = Column(SQLEnum(UserRole), default=UserRole.USER, nullable=False)
    status = Column(SQLEnum(UserStatus), default=UserStatus.PENDING_VERIFICATION, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Email верификация
    email_verification_token = Column(String(255), nullable=True)
    email_verification_expires = Column(DateTime, nullable=True)
    
    # Сброс пароля
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime, nullable=True)
    
    # Метаданные
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    login_count = Column(Integer, default=0, nullable=False)
    
    # Настройки пользователя
    timezone = Column(String(50), default='Europe/Moscow', nullable=False)
    language = Column(String(10), default='ru', nullable=False)
    notifications_enabled = Column(Boolean, default=True, nullable=False)
    marketing_emails = Column(Boolean, default=False, nullable=False)
    
    # Связи
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    usage_records = relationship("UsageRecord", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    content_pieces = relationship("ContentPieceDB", back_populates="user", cascade="all, delete-orphan")
    token_usage_records = relationship("TokenUsageDB", back_populates="user", cascade="all, delete-orphan")
    uploads = relationship("FileUploadDB", back_populates="user", cascade="all, delete-orphan")
    agent_subscriptions = relationship("AgentSubscription", back_populates="user", cascade="all, delete-orphan")
    telegram_channels = relationship("TelegramChannel", back_populates="user", cascade="all, delete-orphan")
    instagram_accounts = relationship("InstagramAccount", back_populates="user", cascade="all, delete-orphan")
    twitter_accounts = relationship("TwitterAccount", back_populates="user", cascade="all, delete-orphan")
    scheduled_posts = relationship("ScheduledPostDB", back_populates="user", cascade="all, delete-orphan")
    auto_posting_rules = relationship("AutoPostingRuleDB", back_populates="user", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.email_verification_token:
            self.generate_email_verification_token()

    def set_password(self, password: str) -> None:
        """Установить пароль с хешированием"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Проверить пароль"""
        return check_password_hash(self.password_hash, password)

    def generate_email_verification_token(self) -> str:
        """Сгенерировать токен для верификации email"""
        self.email_verification_token = self._generate_token()
        self.email_verification_expires = datetime.utcnow() + timedelta(hours=24)
        return self.email_verification_token

    def generate_password_reset_token(self) -> str:
        """Сгенерировать токен для сброса пароля"""
        self.password_reset_token = self._generate_token()
        self.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
        return self.password_reset_token

    def _generate_token(self, length: int = 32) -> str:
        """Сгенерировать случайный токен"""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def verify_email_token(self, token: str) -> bool:
        """Проверить токен верификации email"""
        if (self.email_verification_token == token and 
            self.email_verification_expires and 
            datetime.utcnow() < self.email_verification_expires):
            self.is_verified = True
            self.status = UserStatus.ACTIVE
            self.email_verification_token = None
            self.email_verification_expires = None
            return True
        return False

    def verify_password_reset_token(self, token: str) -> bool:
        """Проверить токен сброса пароля"""
        return (self.password_reset_token == token and 
                self.password_reset_expires and 
                datetime.utcnow() < self.password_reset_expires)

    def update_login_info(self) -> None:
        """Обновить информацию о последнем входе"""
        self.last_login = datetime.utcnow()
        self.login_count += 1

    def get_full_name(self) -> str:
        """Получить полное имя пользователя"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.username

    def _get_social_media_status(self) -> list:
        """Получить статус социальных сетей с детальной информацией"""
        from sqlalchemy.orm import object_session
        import logging
        
        logger = logging.getLogger(__name__)
        
        # Проверяем, есть ли активная сессия
        session = object_session(self)
        if not session:
            logger.debug(f"No active session for user {self.id}, returning empty social media")
            return []
        
        social_media = []
        
        try:
            # Telegram channels
            if self.telegram_channels:
                for channel in self.telegram_channels:
                    # Формируем ссылку на канал
                    channel_link = None
                    if channel.channel_username:
                        username = channel.channel_username.lstrip('@')
                        channel_link = f"https://t.me/{username}"
                    
                    social_media.append({
                        "name": "Telegram",
                        "isActive": channel.is_active,
                        "metadata": {
                            "channelLink": channel_link,
                            "accountId": channel.id,
                            "isDefault": channel.is_default,
                            "chatId": channel.chat_id,
                            "channelName": channel.channel_name,
                            "channelUsername": channel.channel_username
                        }
                    })
            
            # Instagram accounts
            if self.instagram_accounts:
                for account in self.instagram_accounts:
                    social_media.append({
                        "name": "Instagram",
                        "isActive": account.is_active,
                        "metadata": {
                            "username": account.instagram_username,
                            "accountId": account.id,
                            "isDefault": account.is_default,
                            "isActive": account.is_active
                        }
                    })
            
            # Twitter accounts
            if self.twitter_accounts:
                for account in self.twitter_accounts:
                    social_media.append({
                        "name": "Twitter",
                        "isActive": account.is_active,
                        "metadata": {
                            "username": account.twitter_username,
                            "accountId": account.id,
                            "isDefault": account.is_default,
                            "userId": account.twitter_user_id
                        }
                    })
        
        except Exception as e:
            logger.error(f"Error loading social media for user {self.id}: {e}", exc_info=True)
            return []
        
        return social_media if social_media else []

    def get_display_name(self) -> str:
        """Получить отображаемое имя"""
        return self.get_full_name() or self.username

    def is_admin(self) -> bool:
        """Проверить, является ли пользователь администратором"""
        return self.role == UserRole.ADMIN

    def is_moderator(self) -> bool:
        """Проверить, является ли пользователь модератором"""
        return self.role in [UserRole.ADMIN, UserRole.MODERATOR]

    def can_access_feature(self, feature: str) -> bool:
        """Проверить доступ к функции"""
        if not self.is_active or self.status != UserStatus.ACTIVE:
            return False
        
        # Админы имеют доступ ко всему
        if self.is_admin():
            return True
        
        # Проверка по подписке
        active_subscription = self.get_active_subscription()
        if not active_subscription:
            return False
        
        # Здесь можно добавить логику проверки функций по тарифу
        return True

    def get_active_subscription(self):
        """Получить активную подписку"""
        for subscription in self.subscriptions:
            if subscription.is_active():
                return subscription
        return None

    def get_usage_stats(self) -> dict:
        """Получить статистику использования"""
        active_subscription = self.get_active_subscription()
        if not active_subscription:
            return {}
        
        # Подсчет использования за текущий месяц
        current_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        posts_used = sum(
            record.posts_count for record in self.usage_records 
            if record.created_at >= current_month
        )
        
        api_calls_used = sum(
            record.api_calls_count for record in self.usage_records 
            if record.created_at >= current_month
        )
        
        return {
            'posts_used': posts_used,
            'api_calls_used': api_calls_used,
            'subscription_plan': active_subscription.plan_id,
            'subscription_status': active_subscription.status.value
        }

    def to_dict(self, include_sensitive: bool = False) -> dict:
        """Преобразовать в словарь"""
        data = {
            'id': self.id,
            'email': self.email,
            'username': self.username,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'company': self.company,
            'position': self.position,
            'role': self.role.value,
            'status': self.status.value,
            'is_verified': self.is_verified,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'login_count': self.login_count,
            'timezone': self.timezone,
            'language': self.language,
            'notifications_enabled': self.notifications_enabled,
            'marketing_emails': self.marketing_emails,
            'display_name': self.get_display_name(),
            'full_name': self.get_full_name(),
            'socialMedia': self._get_social_media_status()
        }
        
        if include_sensitive:
            data.update({
                'email_verification_token': self.email_verification_token,
                'password_reset_token': self.password_reset_token,
                'email_verification_expires': self.email_verification_expires.isoformat() if self.email_verification_expires else None,
                'password_reset_expires': self.password_reset_expires.isoformat() if self.password_reset_expires else None
            })
        
        return data

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>"


class UserSession(Base):
    """Модель сессии пользователя для JWT токенов"""
    __tablename__ = 'user_sessions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    token_jti = Column(String(255), unique=True, nullable=False, index=True)  # JWT ID
    refresh_token = Column(String(255), unique=True, nullable=True, index=True)
    device_info = Column(Text, nullable=True)  # JSON с информацией об устройстве
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_used = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Связи
    user = relationship("User", backref="sessions")

    def is_expired(self) -> bool:
        """Проверить, истекла ли сессия"""
        return datetime.utcnow() > self.expires_at

    def update_last_used(self) -> None:
        """Обновить время последнего использования"""
        self.last_used = datetime.utcnow()

    def to_dict(self) -> dict:
        """Преобразовать в словарь"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'token_jti': self.token_jti,
            'device_info': self.device_info,
            'ip_address': self.ip_address,
            'is_active': self.is_active,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_used': self.last_used.isoformat() if self.last_used else None
        }

    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, jti='{self.token_jti}')>"
