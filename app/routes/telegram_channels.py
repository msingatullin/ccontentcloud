"""
API routes для управления Telegram каналами
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.telegram_channel_service import TelegramChannelService
from app.database.connection import get_db_session
import asyncio
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('telegram_channels', __name__, url_prefix='/api/telegram')


@bp.route('/bot-info', methods=['GET'])
@jwt_required()
def get_bot_info():
    """
    Получить информацию о боте для отображения в UI
    
    Returns:
        JSON с информацией о боте
    """
    try:
        db = next(get_db_session())
        service = TelegramChannelService(db)
        
        # Вызываем async функцию
        bot_info = asyncio.run(service.get_bot_info())
        
        return jsonify({
            'success': True,
            'bot': {
                'id': bot_info.get('id'),
                'username': bot_info.get('username'),
                'first_name': bot_info.get('first_name'),
                'link': f"https://t.me/{bot_info.get('username')}"
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Ошибка получения информации о боте: {e}")
        return jsonify({
            'success': False,
            'error': 'Не удалось получить информацию о боте. Проверьте TELEGRAM_BOT_TOKEN'
        }), 500


@bp.route('/channels', methods=['GET'])
@jwt_required()
def get_channels():
    """
    Получить все каналы текущего пользователя
    
    Query params:
        active_only: bool (default=true) - возвращать только активные
    
    Returns:
        JSON со списком каналов
    """
    try:
        user_id = get_jwt_identity()
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        db = next(get_db_session())
        service = TelegramChannelService(db)
        
        channels = service.get_user_channels(user_id, active_only=active_only)
        
        return jsonify({
            'success': True,
            'channels': [ch.to_dict() for ch in channels],
            'count': len(channels)
        }), 200
        
    except Exception as e:
        logger.error(f"Ошибка получения каналов: {e}")
        return jsonify({
            'success': False,
            'error': 'Ошибка получения списка каналов'
        }), 500


@bp.route('/channels', methods=['POST'])
@jwt_required()
def add_channel():
    """
    Добавить новый Telegram канал
    
    Body:
        {
            "channel_link": "https://t.me/mychannel",
            "channel_name": "Мой канал о финансах"
        }
    
    Returns:
        JSON с результатом и данными канала
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Валидация входных данных
        channel_link = data.get('channel_link', '').strip()
        channel_name = data.get('channel_name', '').strip()
        
        if not channel_link:
            return jsonify({
                'success': False,
                'error': 'Укажите ссылку на канал'
            }), 400
        
        if not channel_name:
            return jsonify({
                'success': False,
                'error': 'Укажите название канала'
            }), 400
        
        if len(channel_name) < 3:
            return jsonify({
                'success': False,
                'error': 'Название канала должно быть не короче 3 символов'
            }), 400
        
        db = next(get_db_session())
        service = TelegramChannelService(db)
        
        # Добавляем канал (async операция)
        success, message, channel = asyncio.run(
            service.add_channel(user_id, channel_link, channel_name)
        )
        
        if success:
            logger.info(f"✅ Канал добавлен: user_id={user_id}, channel_id={channel.id if channel else None}")
            return jsonify({
                'success': True,
                'message': message,
                'channel': channel.to_dict() if channel else None
            }), 201
        else:
            logger.warning(f"❌ Не удалось добавить канал: {message}")
            return jsonify({
                'success': False,
                'error': message
            }), 400
            
    except Exception as e:
        logger.error(f"Критическая ошибка добавления канала: {e}")
        return jsonify({
            'success': False,
            'error': 'Внутренняя ошибка сервера при добавлении канала'
        }), 500


@bp.route('/channels/<int:channel_id>', methods=['GET'])
@jwt_required()
def get_channel(channel_id):
    """
    Получить информацию о конкретном канале
    
    Args:
        channel_id: ID канала
    
    Returns:
        JSON с данными канала
    """
    try:
        user_id = get_jwt_identity()
        
        db = next(get_db_session())
        service = TelegramChannelService(db)
        
        channel = service.get_channel_by_id(user_id, channel_id)
        
        if not channel:
            return jsonify({
                'success': False,
                'error': 'Канал не найден'
            }), 404
        
        return jsonify({
            'success': True,
            'channel': channel.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Ошибка получения канала {channel_id}: {e}")
        return jsonify({
            'success': False,
            'error': 'Ошибка получения информации о канале'
        }), 500


@bp.route('/channels/<int:channel_id>', methods=['PUT'])
@jwt_required()
def update_channel(channel_id):
    """
    Обновить информацию о канале
    
    Body (все поля опциональны):
        {
            "channel_link": "https://t.me/newchannel",  // Новая ссылка на канал
            "channel_name": "Новое название",           // Новое название канала
            "is_active": true                           // Статус активации
        }
    
    Returns:
        JSON с результатом и обновленными данными канала
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        # Получаем опциональные поля
        channel_link = data.get('channel_link', '').strip() if data.get('channel_link') else None
        channel_name = data.get('channel_name', '').strip() if data.get('channel_name') else None
        is_active = data.get('is_active') if 'is_active' in data else None
        
        # Проверяем что хотя бы одно поле указано
        if not any([channel_link, channel_name, is_active is not None]):
            return jsonify({
                'success': False,
                'error': 'Укажите хотя бы одно поле для обновления: channel_link, channel_name или is_active'
            }), 400
        
        db = next(get_db_session())
        service = TelegramChannelService(db)
        
        # Обновляем канал (async операция)
        success, message, channel = asyncio.run(
            service.update_channel(
                user_id=user_id,
                channel_id=channel_id,
                channel_link=channel_link,
                channel_name=channel_name,
                is_active=is_active
            )
        )
        
        if success:
            logger.info(f"✅ Канал {channel_id} обновлен для user_id={user_id}")
            return jsonify({
                'success': True,
                'message': message,
                'channel': channel.to_dict() if channel else None
            }), 200
        else:
            logger.warning(f"❌ Не удалось обновить канал {channel_id}: {message}")
            return jsonify({
                'success': False,
                'error': message
            }), 400
            
    except Exception as e:
        logger.error(f"Критическая ошибка обновления канала: {e}")
        return jsonify({
            'success': False,
            'error': 'Внутренняя ошибка сервера'
        }), 500


@bp.route('/channels/<int:channel_id>/default', methods=['PUT'])
@jwt_required()
def set_default_channel(channel_id):
    """
    Установить канал как дефолтный для публикаций
    
    Args:
        channel_id: ID канала
    
    Returns:
        JSON с результатом
    """
    try:
        user_id = get_jwt_identity()
        
        db = next(get_db_session())
        service = TelegramChannelService(db)
        
        success = service.set_default_channel(user_id, channel_id)
        
        if success:
            logger.info(f"✅ Канал {channel_id} установлен как дефолтный для user_id={user_id}")
            return jsonify({
                'success': True,
                'message': 'Канал установлен по умолчанию'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Канал не найден или не активен'
            }), 404
            
    except Exception as e:
        logger.error(f"Ошибка установки дефолтного канала: {e}")
        return jsonify({
            'success': False,
            'error': 'Ошибка установки канала по умолчанию'
        }), 500


@bp.route('/channels/<int:channel_id>', methods=['DELETE'])
@jwt_required()
def delete_channel(channel_id):
    """
    Удалить (деактивировать) канал
    
    Args:
        channel_id: ID канала
    
    Returns:
        JSON с результатом
    """
    try:
        user_id = get_jwt_identity()
        
        db = next(get_db_session())
        service = TelegramChannelService(db)
        
        success = service.deactivate_channel(user_id, channel_id)
        
        if success:
            logger.info(f"✅ Канал {channel_id} удален для user_id={user_id}")
            return jsonify({
                'success': True,
                'message': 'Канал успешно удален'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Канал не найден'
            }), 404
            
    except Exception as e:
        logger.error(f"Ошибка удаления канала: {e}")
        return jsonify({
            'success': False,
            'error': 'Ошибка удаления канала'
        }), 500


@bp.route('/channels/<int:channel_id>/activate', methods=['PUT'])
@jwt_required()
def toggle_activation(channel_id):
    """
    Переключить статус активации канала
    
    Поддерживает автоматическое обновление канала перед активацией.
    Если указаны channel_link или channel_name - канал сначала обновится, затем активируется.
    
    Body:
        {
            "is_active": true/false,
            "channel_link": "https://t.me/newchannel",  // опционально - обновить ссылку
            "channel_name": "Новое название"            // опционально - обновить название
        }
    
    Returns:
        JSON с результатом
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json() or {}
        
        is_active = data.get('is_active')
        if is_active is None:
            return jsonify({
                'success': False,
                'error': 'Укажите is_active (true/false)'
            }), 400
        
        # Опциональные поля для обновления канала
        channel_link = data.get('channel_link', '').strip() if data.get('channel_link') else None
        channel_name = data.get('channel_name', '').strip() if data.get('channel_name') else None
        
        db = next(get_db_session())
        service = TelegramChannelService(db)
        
        # Если указаны изменения канала - обновляем канал с активацией
        if channel_link or channel_name:
            logger.info(f"Обновление канала {channel_id} с последующей активацией для user_id={user_id}")
            success, message, channel = asyncio.run(
                service.update_channel(
                    user_id=user_id,
                    channel_id=channel_id,
                    channel_link=channel_link,
                    channel_name=channel_name,
                    is_active=bool(is_active)  # активируем одновременно с обновлением
                )
            )
            
            if success:
                status_text = "активирован" if is_active else "деактивирован"
                logger.info(f"✅ Канал {channel_id} обновлен и {status_text} для user_id={user_id}")
                return jsonify({
                    'success': True,
                    'message': message,
                    'is_active': is_active,
                    'channel': channel.to_dict() if channel else None
                }), 200
            else:
                logger.warning(f"❌ Не удалось обновить канал {channel_id}: {message}")
                return jsonify({
                    'success': False,
                    'error': message
                }), 400
        else:
            # Просто переключаем активацию без изменений
            success = service.toggle_activation(user_id, channel_id, bool(is_active))
            
            if success:
                status_text = "активирован" if is_active else "деактивирован"
                logger.info(f"✅ Канал {channel_id} {status_text} для user_id={user_id}")
                return jsonify({
                    'success': True,
                    'message': f'Канал успешно {status_text}',
                    'is_active': is_active
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': 'Канал не найден'
                }), 404
            
    except Exception as e:
        logger.error(f"Ошибка переключения активации: {e}")
        return jsonify({
            'success': False,
            'error': 'Внутренняя ошибка сервера'
        }), 500


@bp.route('/channels/<int:channel_id>/verify', methods=['POST'])
@jwt_required()
def verify_channel(channel_id):
    """
    Повторно проверить статус канала (права бота)
    
    Args:
        channel_id: ID канала
    
    Returns:
        JSON с обновленной информацией о канале
    """
    try:
        user_id = get_jwt_identity()
        
        db = next(get_db_session())
        service = TelegramChannelService(db)
        
        # Получаем канал
        channel = service.get_channel_by_id(user_id, channel_id)
        
        if not channel:
            return jsonify({
                'success': False,
                'error': 'Канал не найден'
            }), 404
        
        # Проверяем статус
        is_verified, chat_info = asyncio.run(
            service.verify_bot_in_channel(channel.chat_id)
        )
        
        # Обновляем информацию
        if chat_info:
            channel.is_verified = is_verified
            channel.channel_title = chat_info.get('title')
            channel.channel_type = chat_info.get('type')
            channel.members_count = chat_info.get('members_count')
            
            if not is_verified:
                channel.last_error = "Бот не является администратором или не имеет прав на публикацию"
            else:
                channel.last_error = None
            
            db.commit()
            db.refresh(channel)
            
            return jsonify({
                'success': True,
                'channel': channel.to_dict(),
                'message': '✅ Канал проверен и готов к публикациям' if is_verified else '⚠️ Добавьте бота в администраторы канала'
            }), 200
        else:
            channel.last_error = "Не удалось получить информацию о канале"
            db.commit()
            
            return jsonify({
                'success': False,
                'error': 'Не удалось подключиться к каналу. Проверьте что бот добавлен в канал'
            }), 400
            
    except Exception as e:
        logger.error(f"Ошибка проверки канала: {e}")
        return jsonify({
            'success': False,
            'error': 'Ошибка проверки канала'
        }), 500


