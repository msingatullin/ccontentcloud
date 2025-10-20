"""
Тесты для функциональности Telegram каналов
Архитектура: ОДИН БОТ - МНОГО КАНАЛОВ
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.telegram_channels import TelegramChannel
from app.services.telegram_channel_service import TelegramChannelService
from app.database.connection import Base


@pytest.fixture
def db_session():
    """Создает временную БД для тестов"""
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    yield session
    
    session.close()


@pytest.fixture
def mock_user_id():
    """Mock user ID для тестов"""
    return 123


@pytest.fixture
def telegram_service(db_session):
    """Создает экземпляр TelegramChannelService с mock БД"""
    with patch.dict('os.environ', {'TELEGRAM_BOT_TOKEN': 'test_token'}):
        service = TelegramChannelService(db_session)
        return service


class TestTelegramChannelService:
    """Тесты для TelegramChannelService"""
    
    def test_parse_channel_link_https(self, telegram_service):
        """Тест парсинга HTTPS ссылки"""
        result = telegram_service.parse_channel_link("https://t.me/mychannel")
        assert result == "@mychannel"
    
    def test_parse_channel_link_http(self, telegram_service):
        """Тест парсинга HTTP ссылки"""
        result = telegram_service.parse_channel_link("http://t.me/mychannel")
        assert result == "@mychannel"
    
    def test_parse_channel_link_short(self, telegram_service):
        """Тест парсинга короткой ссылки"""
        result = telegram_service.parse_channel_link("t.me/mychannel")
        assert result == "@mychannel"
    
    def test_parse_channel_link_username(self, telegram_service):
        """Тест парсинга username с @"""
        result = telegram_service.parse_channel_link("@mychannel")
        assert result == "@mychannel"
    
    def test_parse_channel_link_plain(self, telegram_service):
        """Тест парсинга просто названия канала"""
        result = telegram_service.parse_channel_link("mychannel")
        assert result == "@mychannel"
    
    def test_parse_channel_link_invalid(self, telegram_service):
        """Тест парсинга неверного формата"""
        result = telegram_service.parse_channel_link("invalid channel link!")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_get_bot_info(self, telegram_service):
        """Тест получения информации о боте"""
        mock_response = {
            'ok': True,
            'result': {
                'id': 123456789,
                'username': 'content4ubot',
                'first_name': 'Content4u'
            }
        }
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = AsyncMock()
            mock_get.return_value.json = AsyncMock(return_value=mock_response)
            
            bot_info = await telegram_service.get_bot_info()
            
            assert bot_info['username'] == 'content4ubot'
            assert bot_info['first_name'] == 'Content4u'
    
    @pytest.mark.asyncio
    async def test_verify_bot_in_channel_success(self, telegram_service):
        """Тест успешной верификации бота в канале"""
        mock_chat_response = {
            'ok': True,
            'result': {
                'id': -1001234567890,
                'title': 'Test Channel',
                'type': 'channel'
            }
        }
        
        mock_member_response = {
            'ok': True,
            'result': {
                'status': 'administrator',
                'can_post_messages': True
            }
        }
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = AsyncMock()
            mock_get.return_value.status_code = 200
            
            # Первый вызов - getChat
            # Второй вызов - getMe
            # Третий вызов - getChatMember
            mock_get.return_value.json = AsyncMock(
                side_effect=[
                    mock_chat_response,
                    {'ok': True, 'result': {'id': 123456789}},
                    mock_member_response
                ]
            )
            
            is_verified, chat_info = await telegram_service.verify_bot_in_channel("@testchannel")
            
            assert is_verified is True
            assert chat_info['title'] == 'Test Channel'
    
    @pytest.mark.asyncio
    async def test_verify_bot_not_admin(self, telegram_service):
        """Тест когда бот не администратор"""
        mock_chat_response = {
            'ok': True,
            'result': {
                'id': -1001234567890,
                'title': 'Test Channel',
                'type': 'channel'
            }
        }
        
        mock_member_response = {
            'ok': True,
            'result': {
                'status': 'member'  # Не админ!
            }
        }
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_get.return_value = AsyncMock()
            mock_get.return_value.status_code = 200
            mock_get.return_value.json = AsyncMock(
                side_effect=[
                    mock_chat_response,
                    {'ok': True, 'result': {'id': 123456789}},
                    mock_member_response
                ]
            )
            
            is_verified, chat_info = await telegram_service.verify_bot_in_channel("@testchannel")
            
            assert is_verified is False
            assert chat_info is not None
    
    @pytest.mark.asyncio
    async def test_add_channel_success(self, telegram_service, mock_user_id, db_session):
        """Тест успешного добавления канала"""
        with patch.object(telegram_service, 'verify_bot_in_channel') as mock_verify:
            mock_verify.return_value = (
                True,
                {
                    'id': -1001234567890,
                    'title': 'Test Channel',
                    'type': 'channel',
                    'members_count': 100
                }
            )
            
            success, message, channel = await telegram_service.add_channel(
                user_id=mock_user_id,
                channel_link="https://t.me/testchannel",
                channel_name="Мой тестовый канал"
            )
            
            assert success is True
            assert "успешно" in message.lower()
            assert channel is not None
            assert channel.channel_name == "Мой тестовый канал"
            assert channel.is_verified is True
            assert channel.is_default is True  # Первый канал
    
    @pytest.mark.asyncio
    async def test_add_channel_not_verified(self, telegram_service, mock_user_id, db_session):
        """Тест добавления канала без верификации"""
        with patch.object(telegram_service, 'verify_bot_in_channel') as mock_verify:
            mock_verify.return_value = (
                False,  # Не верифицирован
                {
                    'id': -1001234567890,
                    'title': 'Test Channel',
                    'type': 'channel'
                }
            )
            
            success, message, channel = await telegram_service.add_channel(
                user_id=mock_user_id,
                channel_link="@testchannel",
                channel_name="Канал без прав"
            )
            
            assert success is True
            assert channel.is_verified is False
            assert "не является администратором" in message
    
    @pytest.mark.asyncio
    async def test_add_duplicate_channel(self, telegram_service, mock_user_id, db_session):
        """Тест добавления дубликата канала"""
        # Добавляем первый канал
        with patch.object(telegram_service, 'verify_bot_in_channel') as mock_verify:
            mock_verify.return_value = (True, {'id': -1001234567890, 'title': 'Test'})
            
            await telegram_service.add_channel(
                user_id=mock_user_id,
                channel_link="@testchannel",
                channel_name="Канал 1"
            )
            
            # Пытаемся добавить снова
            success, message, channel = await telegram_service.add_channel(
                user_id=mock_user_id,
                channel_link="@testchannel",
                channel_name="Канал 2"
            )
            
            assert success is False
            assert "уже добавлен" in message
    
    def test_get_user_channels(self, telegram_service, mock_user_id, db_session):
        """Тест получения каналов пользователя"""
        # Создаем тестовые каналы
        channel1 = TelegramChannel(
            user_id=mock_user_id,
            channel_name="Канал 1",
            chat_id="@channel1",
            is_active=True,
            is_default=True
        )
        channel2 = TelegramChannel(
            user_id=mock_user_id,
            channel_name="Канал 2",
            chat_id="@channel2",
            is_active=True
        )
        channel3 = TelegramChannel(
            user_id=mock_user_id,
            channel_name="Канал 3",
            chat_id="@channel3",
            is_active=False  # Неактивный
        )
        
        db_session.add_all([channel1, channel2, channel3])
        db_session.commit()
        
        # Получаем только активные
        channels = telegram_service.get_user_channels(mock_user_id, active_only=True)
        assert len(channels) == 2
        assert channels[0].channel_name == "Канал 1"  # Дефолтный первым
        
        # Получаем все
        channels = telegram_service.get_user_channels(mock_user_id, active_only=False)
        assert len(channels) == 3
    
    def test_get_default_channel(self, telegram_service, mock_user_id, db_session):
        """Тест получения дефолтного канала"""
        channel1 = TelegramChannel(
            user_id=mock_user_id,
            channel_name="Канал 1",
            chat_id="@channel1",
            is_active=True,
            is_default=False
        )
        channel2 = TelegramChannel(
            user_id=mock_user_id,
            channel_name="Канал 2 (дефолтный)",
            chat_id="@channel2",
            is_active=True,
            is_default=True
        )
        
        db_session.add_all([channel1, channel2])
        db_session.commit()
        
        default = telegram_service.get_default_channel(mock_user_id)
        assert default is not None
        assert default.channel_name == "Канал 2 (дефолтный)"
    
    def test_set_default_channel(self, telegram_service, mock_user_id, db_session):
        """Тест установки дефолтного канала"""
        channel1 = TelegramChannel(
            user_id=mock_user_id,
            channel_name="Канал 1",
            chat_id="@channel1",
            is_active=True,
            is_default=True
        )
        channel2 = TelegramChannel(
            user_id=mock_user_id,
            channel_name="Канал 2",
            chat_id="@channel2",
            is_active=True,
            is_default=False
        )
        
        db_session.add_all([channel1, channel2])
        db_session.commit()
        
        # Меняем дефолтный
        success = telegram_service.set_default_channel(mock_user_id, channel2.id)
        assert success is True
        
        db_session.refresh(channel1)
        db_session.refresh(channel2)
        
        assert channel1.is_default is False
        assert channel2.is_default is True
    
    def test_deactivate_channel(self, telegram_service, mock_user_id, db_session):
        """Тест деактивации канала"""
        channel = TelegramChannel(
            user_id=mock_user_id,
            channel_name="Канал для удаления",
            chat_id="@channel",
            is_active=True
        )
        
        db_session.add(channel)
        db_session.commit()
        
        success = telegram_service.deactivate_channel(mock_user_id, channel.id)
        assert success is True
        
        db_session.refresh(channel)
        assert channel.is_active is False
    
    def test_update_channel_stats_success(self, telegram_service, db_session):
        """Тест обновления статистики канала после публикации"""
        channel = TelegramChannel(
            user_id=123,
            channel_name="Тестовый канал",
            chat_id="@test",
            posts_count=0
        )
        
        db_session.add(channel)
        db_session.commit()
        
        telegram_service.update_channel_stats(channel.id, post_success=True)
        
        db_session.refresh(channel)
        assert channel.posts_count == 1
        assert channel.last_post_at is not None
        assert channel.last_error is None
    
    def test_update_channel_stats_error(self, telegram_service, db_session):
        """Тест обновления статистики при ошибке"""
        channel = TelegramChannel(
            user_id=123,
            channel_name="Тестовый канал",
            chat_id="@test",
            posts_count=5
        )
        
        db_session.add(channel)
        db_session.commit()
        
        telegram_service.update_channel_stats(
            channel.id, 
            post_success=False, 
            error_message="Test error"
        )
        
        db_session.refresh(channel)
        assert channel.posts_count == 5  # Не увеличился
        assert channel.last_error == "Test error"


class TestTelegramChannelModel:
    """Тесты для модели TelegramChannel"""
    
    def test_to_dict(self, db_session):
        """Тест преобразования в словарь"""
        channel = TelegramChannel(
            user_id=123,
            channel_name="Тест",
            chat_id="@test",
            channel_username="@test",
            is_verified=True,
            posts_count=10
        )
        
        data = channel.to_dict()
        
        assert data['channel_name'] == "Тест"
        assert data['chat_id'] == "@test"
        assert data['is_verified'] is True
        assert data['posts_count'] == 10
    
    def test_repr(self, db_session):
        """Тест строкового представления"""
        channel = TelegramChannel(
            id=1,
            user_id=123,
            channel_name="Тест",
            chat_id="@test"
        )
        
        repr_str = repr(channel)
        assert "TelegramChannel" in repr_str
        assert "user_id=123" in repr_str


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

