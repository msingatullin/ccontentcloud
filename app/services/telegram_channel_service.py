"""
Сервис управления Telegram каналами пользователей
Архитектура: ОДИН БОТ - МНОГО КАНАЛОВ
"""

import os
import re
import httpx
from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from app.models.telegram_channels import TelegramChannel
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class TelegramChannelService:
    """Сервис управления Telegram каналами пользователей"""
    
    def __init__(self, db: Session):
        self.db = db
        self.bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        
        if not self.bot_token:
            raise ValueError("TELEGRAM_BOT_TOKEN не установлен в переменных окружения")
        
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        logger.info("TelegramChannelService инициализирован")
    
    def parse_channel_link(self, link: str) -> Optional[str]:
        """
        Извлекает username канала из различных форматов ссылок
        
        Поддерживаемые форматы:
        - https://t.me/mychannel -> @mychannel
        - t.me/mychannel -> @mychannel
        - @mychannel -> @mychannel
        - mychannel -> @mychannel
        
        Args:
            link: Ссылка или username канала
            
        Returns:
            Username с @ или None если формат неверный
        """
        if not link:
            return None
        
        link = link.strip().replace(' ', '')
        
        # Если уже с @
        if link.startswith('@'):
            return link
        
        # Парсим различные форматы ссылок
        patterns = [
            r'https?://t\.me/([a-zA-Z0-9_]+)',
            r'https?://telegram\.me/([a-zA-Z0-9_]+)',
            r't\.me/([a-zA-Z0-9_]+)',
            r'telegram\.me/([a-zA-Z0-9_]+)',
            r'^([a-zA-Z0-9_]+)$'
        ]
        
        for pattern in patterns:
            match = re.match(pattern, link)
            if match:
                username = match.group(1)
                return f'@{username}'
        
        logger.warning(f"Не удалось распарсить ссылку на канал: {link}")
        return None
    
    async def get_bot_info(self) -> dict:
        """
        Получает информацию о боте через Telegram API
        
        Returns:
            Словарь с информацией о боте
        """
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{self.base_url}/getMe")
                result = response.json()
                
                if result.get('ok'):
                    bot_info = result['result']
                    logger.info(f"Получена информация о боте: @{bot_info.get('username')}")
                    return bot_info
                else:
                    raise Exception(f"Ошибка Telegram API: {result.get('description')}")
                    
        except Exception as e:
            logger.error(f"Ошибка получения информации о боте: {e}")
            raise
    
    async def verify_bot_in_channel(self, chat_id: str) -> Tuple[bool, Optional[dict]]:
        """
        Проверяет что бот добавлен в канал как администратор
        и получает информацию о канале
        
        Args:
            chat_id: ID канала или @username
            
        Returns:
            Tuple (is_verified, chat_info)
            - is_verified: True если бот - админ с правами на постинг
            - chat_info: Информация о канале или None
        """
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                # Получаем информацию о канале
                response = await client.get(
                    f"{self.base_url}/getChat",
                    params={'chat_id': chat_id}
                )
                
                if response.status_code != 200:
                    logger.error(f"Ошибка HTTP {response.status_code} при получении канала")
                    return False, None
                
                result = response.json()
                
                if not result.get('ok'):
                    error_desc = result.get('description', 'Неизвестная ошибка')
                    logger.error(f"Канал не найден: {error_desc}")
                    return False, None
                
                chat_info = result['result']
                logger.info(f"Найден канал: {chat_info.get('title')} (type: {chat_info.get('type')})")
                
                # Получаем информацию о боте
                bot_info = await self.get_bot_info()
                bot_id = bot_info['id']
                
                # Проверяем что бот - администратор
                admin_response = await client.get(
                    f"{self.base_url}/getChatMember",
                    params={
                        'chat_id': chat_id,
                        'user_id': bot_id
                    }
                )
                
                if admin_response.status_code == 200:
                    admin_result = admin_response.json()
                    
                    if admin_result.get('ok'):
                        member_info = admin_result['result']
                        member_status = member_info['status']
                        
                        logger.info(f"Статус бота в канале: {member_status}")
                        
                        # Проверяем статус
                        if member_status not in ['administrator', 'creator']:
                            logger.warning(f"Бот не администратор. Статус: {member_status}")
                            return False, chat_info
                        
                        # Для каналов проверяем права на постинг
                        if chat_info.get('type') == 'channel':
                            can_post = member_info.get('can_post_messages', False)
                            if not can_post:
                                logger.warning("Бот не может постить в канал (нет прав)")
                                return False, chat_info
                        
                        logger.info(f"✅ Бот подтвержден как администратор канала")
                        return True, chat_info
                    else:
                        logger.error(f"Ошибка проверки статуса бота: {admin_result.get('description')}")
                
                return False, chat_info
                
        except Exception as e:
            logger.error(f"Критическая ошибка проверки канала: {e}")
            return False, None
    
    async def add_channel(self, user_id: int, channel_link: str, 
                         channel_name: str) -> Tuple[bool, str, Optional[TelegramChannel]]:
        """
        Добавляет Telegram канал пользователю
        
        Args:
            user_id: ID пользователя
            channel_link: Ссылка на канал или @username
            channel_name: Название канала для отображения
            
        Returns:
            Tuple (success, message, channel)
        """
        # Парсим ссылку
        chat_id = self.parse_channel_link(channel_link)
        
        if not chat_id:
            return False, "Неверный формат ссылки на канал. Используйте: https://t.me/channel или @channel", None
        
        # Проверяем что канал не добавлен
        existing = self.db.query(TelegramChannel).filter(
            TelegramChannel.user_id == user_id,
            TelegramChannel.chat_id == chat_id
        ).first()
        
        if existing:
            if existing.is_active:
                return False, "Этот канал уже добавлен в вашем аккаунте", None
            else:
                # Реактивируем
                existing.is_active = True
                existing.channel_name = channel_name
                existing.updated_at = datetime.utcnow()
                self.db.commit()
                return True, "Канал успешно реактивирован", existing
        
        # Проверяем что бот есть в канале
        is_verified, chat_info = await self.verify_bot_in_channel(chat_id)
        
        if not chat_info:
            return False, f"Канал не найден. Убедитесь что:\n1. Вы добавили бота @content4ubot в канал\n2. Ссылка на канал указана верно", None
        
        # Используем числовой ID если получили
        final_chat_id = str(chat_info.get('id', chat_id))
        
        # Создаем запись в БД
        channel = TelegramChannel(
            user_id=user_id,
            channel_name=channel_name,
            channel_username=chat_id if chat_id.startswith('@') else None,
            chat_id=final_chat_id,
            is_verified=is_verified,
            channel_title=chat_info.get('title'),
            channel_type=chat_info.get('type'),
            members_count=chat_info.get('members_count'),
            is_active=True
        )
        
        # Если это первый канал пользователя - делаем дефолтным
        first_channel = self.db.query(TelegramChannel).filter(
            TelegramChannel.user_id == user_id,
            TelegramChannel.is_active == True
        ).count() == 0
        
        if first_channel:
            channel.is_default = True
            logger.info(f"Первый канал пользователя {user_id}, установлен как дефолтный")
        
        self.db.add(channel)
        self.db.commit()
        self.db.refresh(channel)
        
        logger.info(f"✅ Канал добавлен: user_id={user_id}, channel_id={channel.id}, verified={is_verified}")
        
        if not is_verified:
            return True, "⚠️ Канал добавлен, но бот не является администратором или не имеет прав на публикацию. Добавьте бота @content4ubot в администраторы канала с правами 'Публикация сообщений'", channel
        
        return True, "✅ Канал успешно подключен и готов к публикациям!", channel
    
    def get_user_channels(self, user_id: int, active_only: bool = True) -> List[TelegramChannel]:
        """
        Получить все каналы пользователя
        
        Args:
            user_id: ID пользователя
            active_only: Возвращать только активные каналы
            
        Returns:
            Список каналов
        """
        query = self.db.query(TelegramChannel).filter(
            TelegramChannel.user_id == user_id
        )
        
        if active_only:
            query = query.filter(TelegramChannel.is_active == True)
        
        channels = query.order_by(
            TelegramChannel.is_default.desc(),
            TelegramChannel.created_at.desc()
        ).all()
        
        logger.info(f"Получено {len(channels)} каналов для user_id={user_id}")
        return channels
    
    def get_channel_by_id(self, user_id: int, channel_id: int) -> Optional[TelegramChannel]:
        """Получить канал по ID (с проверкой владельца)"""
        return self.db.query(TelegramChannel).filter(
            TelegramChannel.id == channel_id,
            TelegramChannel.user_id == user_id
        ).first()
    
    def get_default_channel(self, user_id: int) -> Optional[TelegramChannel]:
        """
        Получить канал по умолчанию для пользователя
        
        Args:
            user_id: ID пользователя
            
        Returns:
            Канал по умолчанию или None
        """
        channel = self.db.query(TelegramChannel).filter(
            TelegramChannel.user_id == user_id,
            TelegramChannel.is_default == True,
            TelegramChannel.is_active == True
        ).first()
        
        if channel:
            logger.info(f"Дефолтный канал для user_id={user_id}: {channel.channel_name}")
        else:
            logger.warning(f"Дефолтный канал не найден для user_id={user_id}")
        
        return channel
    
    def set_default_channel(self, user_id: int, channel_id: int) -> bool:
        """
        Установить канал как дефолтный
        
        Args:
            user_id: ID пользователя
            channel_id: ID канала
            
        Returns:
            True если успешно
        """
        # Снимаем дефолт со всех каналов пользователя
        self.db.query(TelegramChannel).filter(
            TelegramChannel.user_id == user_id
        ).update({'is_default': False})
        
        # Ставим новый дефолт
        channel = self.db.query(TelegramChannel).filter(
            TelegramChannel.id == channel_id,
            TelegramChannel.user_id == user_id,
            TelegramChannel.is_active == True
        ).first()
        
        if channel:
            channel.is_default = True
            channel.updated_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"Канал {channel_id} установлен как дефолтный для user_id={user_id}")
            return True
        
        logger.warning(f"Канал {channel_id} не найден для user_id={user_id}")
        return False
    
    def deactivate_channel(self, user_id: int, channel_id: int) -> bool:
        """
        Деактивировать (удалить) канал
        
        Args:
            user_id: ID пользователя
            channel_id: ID канала
            
        Returns:
            True если успешно
        """
        channel = self.db.query(TelegramChannel).filter(
            TelegramChannel.id == channel_id,
            TelegramChannel.user_id == user_id
        ).first()
        
        if channel:
            channel.is_active = False
            channel.is_default = False
            channel.updated_at = datetime.utcnow()
            self.db.commit()
            logger.info(f"Канал {channel_id} деактивирован для user_id={user_id}")
            return True
        
        logger.warning(f"Канал {channel_id} не найден для user_id={user_id}")
        return False
    
    async def update_channel(self, user_id: int, channel_id: int, 
                           channel_link: Optional[str] = None,
                           channel_name: Optional[str] = None,
                           is_active: Optional[bool] = None) -> Tuple[bool, str, Optional[TelegramChannel]]:
        """
        Обновить информацию о канале
        
        Args:
            user_id: ID пользователя
            channel_id: ID канала
            channel_link: Новая ссылка на канал (опционально)
            channel_name: Новое название канала (опционально)
            is_active: Новый статус активации (опционально)
            
        Returns:
            Tuple (success, message, channel)
        """
        channel = self.db.query(TelegramChannel).filter(
            TelegramChannel.id == channel_id,
            TelegramChannel.user_id == user_id
        ).first()
        
        if not channel:
            return False, "Канал не найден", None
        
        updated_fields = []
        needs_verification = False
        
        # Обновляем ссылку на канал, если указана
        if channel_link:
            new_chat_id = self.parse_channel_link(channel_link.strip())
            if not new_chat_id:
                return False, "Неверный формат ссылки на канал. Используйте: https://t.me/channel или @channel", None
            
            # Если ссылка изменилась - нужно переверифицировать
            if channel.chat_id != new_chat_id and channel.chat_id != channel_link.strip():
                needs_verification = True
                channel.chat_id = new_chat_id
                channel.channel_username = new_chat_id if new_chat_id.startswith('@') else None
                updated_fields.append("ссылка на канал")
                
                # Верифицируем новый канал
                is_verified, chat_info = await self.verify_bot_in_channel(new_chat_id)
                channel.is_verified = is_verified
                
                if chat_info:
                    channel.channel_title = chat_info.get('title')
                    channel.channel_type = chat_info.get('type')
                    channel.members_count = chat_info.get('members_count')
                    
                    if not is_verified:
                        channel.last_error = 'Бот не является администратором или без прав публикации'
                    else:
                        channel.last_error = None
                else:
                    channel.last_error = 'Не удалось получить информацию о канале'
                    logger.warning(f"Не удалось получить информацию о новом канале {new_chat_id}")
        
        # Обновляем название канала, если указано
        if channel_name:
            channel_name = channel_name.strip()
            if len(channel_name) < 3:
                return False, "Название канала должно быть не короче 3 символов", None
            if channel.channel_name != channel_name:
                channel.channel_name = channel_name
                updated_fields.append("название канала")
        
        # Обновляем статус активации, если указан
        if is_active is not None:
            if channel.is_active != is_active:
                channel.is_active = is_active
                updated_fields.append("статус активации")
                # Если деактивируем - снимаем дефолт
                if not is_active:
                    channel.is_default = False
        
        if not updated_fields:
            return True, "Изменений не обнаружено", channel
        
        channel.updated_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(channel)
        
        fields_text = ", ".join(updated_fields)
        logger.info(f"✅ Канал {channel_id} обновлен: {fields_text} для user_id={user_id}")
        
        if needs_verification and not channel.is_verified:
            message = f"Канал обновлен. ⚠️ Добавьте бота @content4ubot в администраторы нового канала с правами 'Публикация сообщений'"
        else:
            message = f"✅ Канал успешно обновлен: {fields_text}"
        
        return True, message, channel
    
    def toggle_activation(self, user_id: int, channel_id: int, is_active: bool) -> bool:
        """
        Переключить статус активации канала
        
        Args:
            user_id: ID пользователя
            channel_id: ID канала
            is_active: Новый статус активации (True/False)
            
        Returns:
            True если успешно, False если канал не найден
        """
        channel = self.db.query(TelegramChannel).filter(
            TelegramChannel.id == channel_id,
            TelegramChannel.user_id == user_id
        ).first()
        
        if channel:
            channel.is_active = is_active
            # Если деактивируем - снимаем дефолт
            if not is_active:
                channel.is_default = False
            channel.updated_at = datetime.utcnow()
            self.db.commit()
            
            status = "активирован" if is_active else "деактивирован"
            logger.info(f"Telegram канал {channel_id} {status} для user_id={user_id}")
            return True
        
        logger.warning(f"Канал {channel_id} не найден для user_id={user_id}")
        return False
    
    async def upsert_and_activate_single_channel(self, user_id: int, 
                                                channel_link: str) -> Tuple[bool, str, Optional[TelegramChannel]]:
        """
        Упрощенный метод для единственного канала пользователя.
        Находит существующий канал или создает новый, обновляет ссылку, 
        автоматически получает название из Telegram API, верифицирует и активирует.
        
        Args:
            user_id: ID пользователя
            channel_link: Ссылка на канал (единственное что нужно от клиента)
            
        Returns:
            Tuple (success, message, channel)
        """
        # Парсим ссылку
        chat_id = self.parse_channel_link(channel_link.strip())
        if not chat_id:
            return False, "Неверный формат ссылки на канал. Используйте: https://t.me/channel или @channel", None
        
        # Ищем существующий канал пользователя (должен быть только один)
        existing_channel = self.db.query(TelegramChannel).filter(
            TelegramChannel.user_id == user_id
        ).first()
        
        # Верифицируем канал и получаем информацию
        is_verified, chat_info = await self.verify_bot_in_channel(chat_id)
        
        if not chat_info:
            return False, f"Канал не найден. Убедитесь что:\n1. Вы добавили бота @content4ubot в канал\n2. Ссылка на канал указана верно", None
        
        # Получаем название из API или генерируем дефолтное
        auto_channel_name = chat_info.get('title') or f"Telegram Channel ({chat_id})"
        final_chat_id = str(chat_info.get('id', chat_id))
        
        if existing_channel:
            # Обновляем существующий канал
            existing_channel.chat_id = final_chat_id
            existing_channel.channel_username = chat_id if chat_id.startswith('@') else None
            existing_channel.channel_name = auto_channel_name
            existing_channel.channel_title = chat_info.get('title')
            existing_channel.channel_type = chat_info.get('type')
            existing_channel.members_count = chat_info.get('members_count')
            existing_channel.is_verified = is_verified
            existing_channel.is_active = True
            existing_channel.is_default = True
            
            if not is_verified:
                existing_channel.last_error = 'Бот не является администратором или без прав публикации'
            else:
                existing_channel.last_error = None
            
            existing_channel.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(existing_channel)
            
            logger.info(f"✅ Канал обновлен и активирован: user_id={user_id}, channel_id={existing_channel.id}")
            
            if not is_verified:
                return True, f"⚠️ Канал '{auto_channel_name}' обновлен, но бот не является администратором. Добавьте бота @content4ubot в администраторы канала с правами 'Публикация сообщений'", existing_channel
            
            return True, f"✅ Канал '{auto_channel_name}' успешно обновлен и активирован!", existing_channel
        else:
            # Создаем новый канал
            new_channel = TelegramChannel(
                user_id=user_id,
                channel_name=auto_channel_name,
                channel_username=chat_id if chat_id.startswith('@') else None,
                chat_id=final_chat_id,
                is_verified=is_verified,
                channel_title=chat_info.get('title'),
                channel_type=chat_info.get('type'),
                members_count=chat_info.get('members_count'),
                is_active=True,
                is_default=True
            )
            
            if not is_verified:
                new_channel.last_error = 'Бот не является администратором или без прав публикации'
            
            self.db.add(new_channel)
            self.db.commit()
            self.db.refresh(new_channel)
            
            logger.info(f"✅ Новый канал создан и активирован: user_id={user_id}, channel_id={new_channel.id}")
            
            if not is_verified:
                return True, f"⚠️ Канал '{auto_channel_name}' добавлен, но бот не является администратором. Добавьте бота @content4ubot в администраторы канала с правами 'Публикация сообщений'", new_channel
            
            return True, f"✅ Канал '{auto_channel_name}' успешно подключен и активирован!", new_channel
    
    def update_channel_stats(self, channel_id: int, post_success: bool = True, 
                           error_message: Optional[str] = None) -> None:
        """
        Обновить статистику канала после публикации
        
        Args:
            channel_id: ID канала
            post_success: Успешна ли публикация
            error_message: Сообщение об ошибке если неуспешна
        """
        channel = self.db.query(TelegramChannel).filter(
            TelegramChannel.id == channel_id
        ).first()
        
        if channel:
            if post_success:
                channel.posts_count += 1
                channel.last_post_at = datetime.utcnow()
                channel.last_error = None
                logger.info(f"Статистика канала {channel_id} обновлена: posts_count={channel.posts_count}")
            else:
                channel.last_error = error_message
                logger.warning(f"Ошибка публикации в канал {channel_id}: {error_message}")
            
            channel.updated_at = datetime.utcnow()
            self.db.commit()


