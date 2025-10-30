"""
Сервис управления Instagram аккаунтами пользователей
Использует instagrapi для работы через логин/пароль
"""

import os
import json
import logging
from typing import List, Optional, Tuple
from datetime import datetime, date
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet

from instagrapi import Client
from instagrapi.exceptions import (
    LoginRequired, 
    TwoFactorRequired, 
    ChallengeRequired,
    BadPassword,
    RecaptchaChallengeForm
)

from app.models.instagram_accounts import InstagramAccount

logger = logging.getLogger(__name__)


class InstagramAccountService:
    """Сервис управления Instagram аккаунтами"""
    
    def __init__(self, db: Session):
        self.db = db
        self.encryption_key = os.getenv('SOCIAL_TOKENS_ENCRYPTION_KEY')
        
        if not self.encryption_key:
            raise ValueError("SOCIAL_TOKENS_ENCRYPTION_KEY не установлен в переменных окружения")
        
        self.fernet = Fernet(self.encryption_key.encode())
        self.clients = {}  # Кеш Instagram клиентов {account_id: Client}
        
        logger.info("InstagramAccountService инициализирован")
    
    def _encrypt(self, text: str) -> str:
        """Зашифровать текст"""
        return self.fernet.encrypt(text.encode()).decode()
    
    def _decrypt(self, encrypted_text: str) -> str:
        """Расшифровать текст"""
        return self.fernet.decrypt(encrypted_text.encode()).decode()
    
    async def add_account(self, user_id: int, username: str, 
                         password: str, account_name: str) -> Tuple[bool, str, Optional[InstagramAccount]]:
        """
        Добавить Instagram аккаунт
        
        Проверяет:
        1. Логин/пароль корректны
        2. 2FA отключена
        3. Аккаунт не требует challenge (SMS/Email верификация)
        4. Аккаунт не забанен
        
        Args:
            user_id: ID пользователя
            username: Instagram username
            password: Instagram password
            account_name: Название для отображения в UI
            
        Returns:
            (success, message, account)
        """
        try:
            # Проверяем что аккаунт не добавлен
            existing = self.db.query(InstagramAccount).filter(
                InstagramAccount.user_id == user_id,
                InstagramAccount.instagram_username == username
            ).first()
            
            if existing:
                if existing.is_active:
                    return False, "Этот Instagram аккаунт уже добавлен", None
                else:
                    # Реактивируем
                    existing.is_active = True
                    existing.account_name = account_name
                    existing.updated_at = datetime.utcnow()
                    self.db.commit()
                    return True, "Instagram аккаунт реактивирован", existing
            
            # Пробуем залогиниться
            logger.info(f"Попытка входа в Instagram для username: {username}")
            cl = Client()
            cl.delay_range = [1, 3]  # Задержка между запросами
            
            try:
                cl.login(username, password)
            except TwoFactorRequired:
                logger.warning(f"2FA включена для {username}")
                return False, "❌ Двухфакторная аутентификация (2FA) включена.\n\nОтключите 2FA в настройках Instagram:\n1. Instagram → Настройки → Безопасность\n2. Двухфакторная аутентификация → Выключить", None
            
            except ChallengeRequired as e:
                logger.warning(f"Challenge required для {username}: {e}")
                return False, "❌ Instagram требует дополнительную верификацию.\n\nВойдите в свой аккаунт через приложение Instagram и подтвердите, что это вы.", None
            
            except BadPassword:
                logger.warning(f"Неверный пароль для {username}")
                return False, "❌ Неверный логин или пароль", None
            
            except LoginRequired as e:
                logger.error(f"Ошибка входа для {username}: {e}")
                return False, f"❌ Ошибка входа: {str(e)}", None
            
            # Получаем информацию о профиле
            user_info = cl.user_info_by_username(username)
            logger.info(f"Получена информация о профиле {username}: {user_info.username}")
            
            # Сохраняем сессию для повторного использования
            session_data = cl.get_settings()
            
            # Шифруем пароль
            encrypted_password = self._encrypt(password)
            
            # Создаем запись в БД
            # profile_pic_url из instagrapi может быть типом Url (pydantic),
            # приводим к строке, чтобы psycopg2 мог сохранить в TEXT
            safe_profile_pic_url = None
            try:
                safe_profile_pic_url = str(user_info.profile_pic_url) if getattr(user_info, "profile_pic_url", None) else None
            except Exception:
                safe_profile_pic_url = None

            account = InstagramAccount(
                user_id=user_id,
                instagram_username=username,
                encrypted_password=encrypted_password,
                account_name=account_name,
                instagram_user_id=str(user_info.pk),
                profile_pic_url=safe_profile_pic_url,
                followers_count=user_info.follower_count,
                following_count=user_info.following_count,
                biography=user_info.biography,
                session_data=json.dumps(session_data),
                is_verified=True,
                last_login=datetime.utcnow(),
                posts_reset_date=date.today(),
                is_active=True
            )
            
            # Если это первый аккаунт - делаем дефолтным
            first_account = self.db.query(InstagramAccount).filter(
                InstagramAccount.user_id == user_id,
                InstagramAccount.is_active == True
            ).count() == 0
            
            if first_account:
                account.is_default = True
                logger.info(f"Первый Instagram аккаунт пользователя {user_id}, установлен как дефолтный")
            
            self.db.add(account)
            self.db.commit()
            self.db.refresh(account)
            
            logger.info(f"✅ Instagram аккаунт добавлен: user_id={user_id}, account_id={account.id}")
            
            return True, "✅ Instagram аккаунт успешно подключен!", account
            
        except RecaptchaChallengeForm:
            logger.error("Instagram требует капчу")
            return False, "❌ Instagram требует верификацию капчи. Попробуйте войти через приложение Instagram сначала.", None
        
        except Exception as e:
            logger.error(f"Критическая ошибка при добавлении Instagram аккаунта: {e}", exc_info=True)
            return False, f"❌ Ошибка подключения: {str(e)}", None
    
    def get_user_accounts(self, user_id: int, active_only: bool = True) -> List[InstagramAccount]:
        """Получить Instagram аккаунты пользователя"""
        query = self.db.query(InstagramAccount).filter(
            InstagramAccount.user_id == user_id
        )
        
        if active_only:
            query = query.filter(InstagramAccount.is_active == True)
        
        accounts = query.order_by(
            InstagramAccount.is_default.desc(),
            InstagramAccount.created_at.desc()
        ).all()
        
        logger.info(f"Получено {len(accounts)} Instagram аккаунтов для user_id={user_id}")
        return accounts
    
    def get_account_by_id(self, user_id: int, account_id: int) -> Optional[InstagramAccount]:
        """Получить аккаунт по ID (с проверкой владельца)"""
        return self.db.query(InstagramAccount).filter(
            InstagramAccount.id == account_id,
            InstagramAccount.user_id == user_id
        ).first()
    
    def get_default_account(self, user_id: int) -> Optional[InstagramAccount]:
        """Получить дефолтный Instagram аккаунт"""
        account = self.db.query(InstagramAccount).filter(
            InstagramAccount.user_id == user_id,
            InstagramAccount.is_default == True,
            InstagramAccount.is_active == True
        ).first()
        
        if account:
            logger.info(f"Дефолтный Instagram для user_id={user_id}: {account.instagram_username}")
        else:
            logger.warning(f"Дефолтный Instagram не найден для user_id={user_id}")
        
        return account
    
    def set_default_account(self, user_id: int, account_id: int) -> bool:
        """Установить аккаунт как дефолтный"""
        # Снимаем дефолт со всех
        self.db.query(InstagramAccount).filter(
            InstagramAccount.user_id == user_id
        ).update({'is_default': False})
        
        # Ставим новый
        account = self.db.query(InstagramAccount).filter(
            InstagramAccount.id == account_id,
            InstagramAccount.user_id == user_id,
            InstagramAccount.is_active == True
        ).first()
        
        if account:
            account.is_default = True
            account.updated_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"Instagram аккаунт {account_id} установлен как дефолтный для user_id={user_id}")
            return True
        
        return False
    
    def deactivate_account(self, user_id: int, account_id: int) -> bool:
        """Деактивировать аккаунт"""
        account = self.db.query(InstagramAccount).filter(
            InstagramAccount.id == account_id,
            InstagramAccount.user_id == user_id
        ).first()
        
        if account:
            account.is_active = False
            account.is_default = False
            account.updated_at = datetime.utcnow()
            self.db.commit()
            
            # Удаляем из кеша если есть
            if account_id in self.clients:
                del self.clients[account_id]
            
            logger.info(f"Instagram аккаунт {account_id} деактивирован для user_id={user_id}")
            return True
        
        return False
    
    def _check_daily_limit(self, account: InstagramAccount) -> bool:
        """Проверка дневного лимита постов (защита от бана)"""
        today = date.today()
        
        if account.posts_reset_date != today:
            account.posts_today = 0
            account.posts_reset_date = today
            self.db.commit()
        
        return account.posts_today < account.daily_posts_limit
    
    def _get_client(self, account: InstagramAccount) -> Client:
        """
        Получить или создать Instagram клиент с сохраненной сессией
        
        Кеширует клиенты для переиспользования
        """
        if account.id in self.clients:
            return self.clients[account.id]
        
        cl = Client()
        cl.delay_range = [1, 3]
        
        # Загружаем сохраненную сессию если есть
        if account.session_data:
            try:
                cl.set_settings(json.loads(account.session_data))
                logger.info(f"Загружена сессия Instagram для {account.instagram_username}")
            except Exception as e:
                logger.warning(f"Ошибка загрузки сессии, делаем новый логин: {e}")
        
        # Логинимся
        try:
            password = self._decrypt(account.encrypted_password)
            cl.login(account.instagram_username, password)
            
            # Обновляем сессию
            account.session_data = json.dumps(cl.get_settings())
            account.last_login = datetime.utcnow()
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Ошибка логина Instagram для {account.instagram_username}: {e}")
            raise
        
        # Кешируем
        self.clients[account.id] = cl
        return cl
    
    async def publish_photo(self, account_id: int, photo_path: str, 
                           caption: str, hashtags: List[str] = None) -> Tuple[bool, str]:
        """
        Опубликовать фото в Instagram
        
        Args:
            account_id: ID аккаунта
            photo_path: Путь к фото
            caption: Подпись к посту
            hashtags: Список хештегов
            
        Returns:
            (success, media_id_or_error)
        """
        try:
            account = self.db.query(InstagramAccount).get(account_id)
            
            if not account or not account.is_active:
                return False, "Аккаунт не найден или неактивен"
            
            if not account.is_verified:
                return False, "Аккаунт не верифицирован"
            
            # Проверка дневного лимита
            if not self._check_daily_limit(account):
                logger.warning(f"Достигнут дневной лимит для аккаунта {account_id}")
                return False, f"Достигнут дневной лимит публикаций ({account.daily_posts_limit} постов/день)"
            
            # Получаем клиент
            cl = self._get_client(account)
            
            # Формируем caption с хештегами
            full_caption = caption
            if hashtags:
                hashtag_str = " ".join(f"#{tag.strip('#')}" for tag in hashtags)
                full_caption = f"{caption}\n\n{hashtag_str}"
            
            # Публикуем
            logger.info(f"Публикация фото в Instagram для {account.instagram_username}")
            media = cl.photo_upload(photo_path, full_caption)
            
            # Обновляем статистику
            account.posts_count += 1
            account.posts_today += 1
            account.last_post_at = datetime.utcnow()
            account.last_error = None
            account.updated_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"✅ Фото опубликовано в Instagram, media_id: {media.id}")
            
            return True, media.id
            
        except Exception as e:
            logger.error(f"Ошибка публикации в Instagram: {e}", exc_info=True)
            
            # Сохраняем ошибку
            if account:
                account.last_error = str(e)
                self.db.commit()
            
            return False, str(e)
    
    def update_account_stats(self, account_id: int, post_success: bool = True,
                           error_message: Optional[str] = None) -> None:
        """Обновить статистику аккаунта после публикации"""
        account = self.db.query(InstagramAccount).get(account_id)
        
        if account:
            if post_success:
                account.posts_count += 1
                account.posts_today += 1
                account.last_post_at = datetime.utcnow()
                account.last_error = None
            else:
                account.last_error = error_message
            
            account.updated_at = datetime.utcnow()
            self.db.commit()


