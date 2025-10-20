"""
Сервис управления Twitter аккаунтами пользователей
Использует tweepy с OAuth 1.0a
"""

import os
import logging
from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from cryptography.fernet import Fernet

import tweepy
from tweepy.errors import TweepyException, Unauthorized, Forbidden

from app.models.twitter_accounts import TwitterAccount

logger = logging.getLogger(__name__)


class TwitterAccountService:
    """Сервис управления Twitter аккаунтами через OAuth"""
    
    def __init__(self, db: Session):
        self.db = db
        self.encryption_key = os.getenv('SOCIAL_TOKENS_ENCRYPTION_KEY')
        
        if not self.encryption_key:
            raise ValueError("SOCIAL_TOKENS_ENCRYPTION_KEY не установлен")
        
        self.fernet = Fernet(self.encryption_key.encode())
        
        # API ключи вашего Twitter приложения
        self.consumer_key = os.getenv('TWITTER_API_KEY')
        self.consumer_secret = os.getenv('TWITTER_API_SECRET')
        
        if not self.consumer_key or not self.consumer_secret:
            raise ValueError("TWITTER_API_KEY и TWITTER_API_SECRET должны быть установлены")
        
        self.api_clients = {}  # Кеш API клиентов {account_id: API}
        
        logger.info("TwitterAccountService инициализирован")
    
    def _encrypt(self, text: str) -> str:
        """Зашифровать текст"""
        return self.fernet.encrypt(text.encode()).decode()
    
    def _decrypt(self, encrypted_text: str) -> str:
        """Расшифровать текст"""
        return self.fernet.decrypt(encrypted_text.encode()).decode()
    
    def get_oauth_url(self, callback_url: str) -> Tuple[str, str, str]:
        """
        Получить URL для OAuth авторизации (шаг 1)
        
        Args:
            callback_url: URL для возврата после авторизации
            
        Returns:
            (auth_url, oauth_token, oauth_token_secret)
            oauth_token и oauth_token_secret нужно сохранить в сессии
        """
        try:
            auth = tweepy.OAuthHandler(
                self.consumer_key,
                self.consumer_secret,
                callback_url
            )
            
            # Получаем authorization URL
            auth_url = auth.get_authorization_url()
            oauth_token = auth.request_token['oauth_token']
            oauth_token_secret = auth.request_token['oauth_token_secret']
            
            logger.info(f"Сгенерирован OAuth URL для Twitter")
            
            return auth_url, oauth_token, oauth_token_secret
            
        except Exception as e:
            logger.error(f"Ошибка генерации OAuth URL: {e}")
            raise
    
    async def complete_oauth(self, user_id: int, oauth_token: str,
                            oauth_verifier: str, oauth_token_secret: str,
                            account_name: str) -> Tuple[bool, str, Optional[TwitterAccount]]:
        """
        Завершить OAuth и сохранить аккаунт (шаг 2)
        
        Args:
            user_id: ID пользователя
            oauth_token: Токен из callback
            oauth_verifier: Verifier из callback
            oauth_token_secret: Secret из сессии (сохранен на шаге 1)
            account_name: Название для UI
            
        Returns:
            (success, message, account)
        """
        try:
            # Создаем auth handler
            auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
            auth.request_token = {
                'oauth_token': oauth_token,
                'oauth_token_secret': oauth_token_secret
            }
            
            # Получаем access token
            auth.get_access_token(oauth_verifier)
            
            access_token = auth.access_token
            access_token_secret = auth.access_token_secret
            
            # Создаем API клиент для проверки
            api = tweepy.API(auth)
            
            # Получаем информацию о пользователе
            twitter_user = api.verify_credentials()
            
            logger.info(f"OAuth успешен для Twitter: @{twitter_user.screen_name}")
            
            # Проверяем что аккаунт не добавлен
            existing = self.db.query(TwitterAccount).filter(
                TwitterAccount.user_id == user_id,
                TwitterAccount.twitter_user_id == str(twitter_user.id)
            ).first()
            
            if existing:
                if existing.is_active:
                    return False, "Этот Twitter аккаунт уже добавлен", None
                else:
                    # Реактивируем
                    existing.is_active = True
                    existing.account_name = account_name
                    existing.encrypted_access_token = self._encrypt(access_token)
                    existing.encrypted_access_token_secret = self._encrypt(access_token_secret)
                    existing.updated_at = datetime.utcnow()
                    self.db.commit()
                    return True, "Twitter аккаунт реактивирован", existing
            
            # Шифруем токены
            encrypted_access_token = self._encrypt(access_token)
            encrypted_access_token_secret = self._encrypt(access_token_secret)
            
            # Создаем запись в БД
            account = TwitterAccount(
                user_id=user_id,
                encrypted_access_token=encrypted_access_token,
                encrypted_access_token_secret=encrypted_access_token_secret,
                twitter_user_id=str(twitter_user.id),
                twitter_username=twitter_user.screen_name,
                twitter_display_name=twitter_user.name,
                profile_image_url=twitter_user.profile_image_url_https,
                followers_count=twitter_user.followers_count,
                following_count=twitter_user.friends_count,
                tweet_count=twitter_user.statuses_count,
                account_name=account_name,
                is_verified=True,
                is_active=True
            )
            
            # Если это первый аккаунт - делаем дефолтным
            first_account = self.db.query(TwitterAccount).filter(
                TwitterAccount.user_id == user_id,
                TwitterAccount.is_active == True
            ).count() == 0
            
            if first_account:
                account.is_default = True
                logger.info(f"Первый Twitter аккаунт пользователя {user_id}, установлен как дефолтный")
            
            self.db.add(account)
            self.db.commit()
            self.db.refresh(account)
            
            logger.info(f"✅ Twitter аккаунт добавлен: user_id={user_id}, account_id={account.id}")
            
            return True, "✅ Twitter аккаунт успешно подключен!", account
            
        except Unauthorized as e:
            logger.error(f"Twitter OAuth unauthorized: {e}")
            return False, "❌ Ошибка авторизации Twitter. Попробуйте снова.", None
        
        except TweepyException as e:
            logger.error(f"Twitter API error: {e}")
            return False, f"❌ Ошибка Twitter API: {str(e)}", None
        
        except Exception as e:
            logger.error(f"Критическая ошибка OAuth: {e}", exc_info=True)
            return False, f"❌ Ошибка подключения: {str(e)}", None
    
    def get_user_accounts(self, user_id: int, active_only: bool = True) -> List[TwitterAccount]:
        """Получить Twitter аккаунты пользователя"""
        query = self.db.query(TwitterAccount).filter(
            TwitterAccount.user_id == user_id
        )
        
        if active_only:
            query = query.filter(TwitterAccount.is_active == True)
        
        accounts = query.order_by(
            TwitterAccount.is_default.desc(),
            TwitterAccount.created_at.desc()
        ).all()
        
        logger.info(f"Получено {len(accounts)} Twitter аккаунтов для user_id={user_id}")
        return accounts
    
    def get_account_by_id(self, user_id: int, account_id: int) -> Optional[TwitterAccount]:
        """Получить аккаунт по ID (с проверкой владельца)"""
        return self.db.query(TwitterAccount).filter(
            TwitterAccount.id == account_id,
            TwitterAccount.user_id == user_id
        ).first()
    
    def get_default_account(self, user_id: int) -> Optional[TwitterAccount]:
        """Получить дефолтный Twitter аккаунт"""
        account = self.db.query(TwitterAccount).filter(
            TwitterAccount.user_id == user_id,
            TwitterAccount.is_default == True,
            TwitterAccount.is_active == True
        ).first()
        
        if account:
            logger.info(f"Дефолтный Twitter для user_id={user_id}: @{account.twitter_username}")
        else:
            logger.warning(f"Дефолтный Twitter не найден для user_id={user_id}")
        
        return account
    
    def set_default_account(self, user_id: int, account_id: int) -> bool:
        """Установить аккаунт как дефолтный"""
        # Снимаем дефолт со всех
        self.db.query(TwitterAccount).filter(
            TwitterAccount.user_id == user_id
        ).update({'is_default': False})
        
        # Ставим новый
        account = self.db.query(TwitterAccount).filter(
            TwitterAccount.id == account_id,
            TwitterAccount.user_id == user_id,
            TwitterAccount.is_active == True
        ).first()
        
        if account:
            account.is_default = True
            account.updated_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"Twitter аккаунт {account_id} установлен как дефолтный для user_id={user_id}")
            return True
        
        return False
    
    def deactivate_account(self, user_id: int, account_id: int) -> bool:
        """Деактивировать аккаунт"""
        account = self.db.query(TwitterAccount).filter(
            TwitterAccount.id == account_id,
            TwitterAccount.user_id == user_id
        ).first()
        
        if account:
            account.is_active = False
            account.is_default = False
            account.updated_at = datetime.utcnow()
            self.db.commit()
            
            # Удаляем из кеша
            if account_id in self.api_clients:
                del self.api_clients[account_id]
            
            logger.info(f"Twitter аккаунт {account_id} деактивирован для user_id={user_id}")
            return True
        
        return False
    
    def _get_api_client(self, account: TwitterAccount) -> tweepy.API:
        """
        Получить или создать Twitter API клиент
        
        Кеширует клиенты для переиспользования
        """
        if account.id in self.api_clients:
            return self.api_clients[account.id]
        
        # Расшифровываем токены
        access_token = self._decrypt(account.encrypted_access_token)
        access_token_secret = self._decrypt(account.encrypted_access_token_secret)
        
        # Создаем auth
        auth = tweepy.OAuthHandler(self.consumer_key, self.consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        
        # Создаем API клиент
        api = tweepy.API(auth, wait_on_rate_limit=True)
        
        # Кешируем
        self.api_clients[account.id] = api
        
        return api
    
    async def publish_tweet(self, account_id: int, text: str, 
                           media_paths: List[str] = None) -> Tuple[bool, str]:
        """
        Опубликовать твит
        
        Args:
            account_id: ID аккаунта
            text: Текст твита (до 280 символов)
            media_paths: Пути к медиа файлам (до 4 файлов)
            
        Returns:
            (success, tweet_id_or_error)
        """
        try:
            account = self.db.query(TwitterAccount).get(account_id)
            
            if not account or not account.is_active:
                return False, "Аккаунт не найден или неактивен"
            
            if not account.is_verified:
                return False, "Аккаунт не верифицирован"
            
            # Проверка длины текста
            if len(text) > 280:
                logger.warning(f"Текст твита слишком длинный: {len(text)} символов")
                return False, "Текст твита не должен превышать 280 символов"
            
            # Получаем API клиент
            api = self._get_api_client(account)
            
            # Загружаем медиа если есть
            media_ids = []
            if media_paths:
                for path in media_paths[:4]:  # Максимум 4 файла
                    try:
                        media = api.media_upload(path)
                        media_ids.append(media.media_id)
                        logger.info(f"Медиа загружено: {media.media_id}")
                    except Exception as e:
                        logger.error(f"Ошибка загрузки медиа {path}: {e}")
            
            # Публикуем твит
            logger.info(f"Публикация твита для @{account.twitter_username}")
            
            tweet = api.update_status(
                status=text,
                media_ids=media_ids if media_ids else None
            )
            
            # Обновляем статистику
            account.tweets_count += 1
            account.last_tweet_at = datetime.utcnow()
            account.last_error = None
            account.updated_at = datetime.utcnow()
            self.db.commit()
            
            tweet_url = f"https://twitter.com/{account.twitter_username}/status/{tweet.id_str}"
            logger.info(f"✅ Твит опубликован: {tweet_url}")
            
            return True, tweet.id_str
            
        except Forbidden as e:
            error_msg = f"Доступ запрещен: {str(e)}"
            logger.error(error_msg)
            if account:
                account.last_error = error_msg
                self.db.commit()
            return False, error_msg
        
        except TweepyException as e:
            error_msg = f"Twitter API error: {str(e)}"
            logger.error(error_msg)
            if account:
                account.last_error = error_msg
                self.db.commit()
            return False, error_msg
        
        except Exception as e:
            error_msg = f"Ошибка публикации: {str(e)}"
            logger.error(error_msg, exc_info=True)
            if account:
                account.last_error = error_msg
                self.db.commit()
            return False, error_msg
    
    def update_account_stats(self, account_id: int, tweet_success: bool = True,
                           error_message: Optional[str] = None) -> None:
        """Обновить статистику аккаунта после публикации"""
        account = self.db.query(TwitterAccount).get(account_id)
        
        if account:
            if tweet_success:
                account.tweets_count += 1
                account.last_tweet_at = datetime.utcnow()
                account.last_error = None
            else:
                account.last_error = error_message
            
            account.updated_at = datetime.utcnow()
            self.db.commit()


