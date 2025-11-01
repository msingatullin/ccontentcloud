"""
Flask-RESTX namespace: Telegram API (Swagger exposure for existing Blueprint routes)

Мы не дублируем бизнес-логику – дергаем те же сервисы, что и блюпринт
`app/routes/telegram_channels.py`. Эндпоинты и поведение идентичны, но теперь
они доступны и в Swagger под /api/v1/telegram/*.
"""

from flask import request
from flask_restx import Namespace, Resource, fields
import logging
import asyncio

from app.database.connection import get_db_session
from app.services.telegram_channel_service import TelegramChannelService
from app.api.routes import jwt_required

logger = logging.getLogger(__name__)

telegram_ns = Namespace(
    'telegram',
    description='Управление Telegram каналами пользователя',
    path='/telegram'
)

# ===== Swagger models =====

bot_model = telegram_ns.model('TelegramBot', {
    'id': fields.String,
    'username': fields.String,
    'first_name': fields.String,
    'link': fields.String,
})

channel_model = telegram_ns.model('TelegramChannel', {
    'id': fields.Integer,
    'user_id': fields.Integer,
    'channel_link': fields.String,
    'channel_id': fields.String,
    'channel_name': fields.String,
    'is_default': fields.Boolean,
    'is_active': fields.Boolean,
    'is_verified': fields.Boolean,
})

add_channel_request = telegram_ns.model('AddTelegramChannelRequest', {
    'channel_link': fields.String(required=True, description='Ссылка на канал (название получается автоматически из Telegram API)')
})

list_response = telegram_ns.model('TelegramChannelsList', {
    'success': fields.Boolean,
    'channels': fields.List(fields.Nested(channel_model)),
    'count': fields.Integer
})

error_model = telegram_ns.model('ErrorResponseTelegram', {
    'success': fields.Boolean,
    'error': fields.String
})


@telegram_ns.route('/bot-info')
class TelegramBotInfo(Resource):
    @jwt_required
    @telegram_ns.doc('get_bot_info', security='BearerAuth')
    @telegram_ns.response(200, 'OK', bot_model)
    def get(self, current_user):
        try:
            db = get_db_session()
            service = TelegramChannelService(db)
            bot_info = asyncio.run(service.get_bot_info())
            return {
                'success': True,
                'bot': {
                    'id': bot_info.get('id'),
                    'username': bot_info.get('username'),
                    'first_name': bot_info.get('first_name'),
                    'link': f"https://t.me/{bot_info.get('username')}"
                }
            }, 200
        except Exception as e:
            logger.error(f"Ошибка получения информации о боте: {e}")
            return {'success': False, 'error': 'Не удалось получить информацию о боте'}, 500
        finally:
            if 'db' in locals() and db:
                db.close()


@telegram_ns.route('/channels')
class TelegramChannels(Resource):
    @jwt_required
    @telegram_ns.doc('list_channels', security='BearerAuth', params={
        'active_only': 'Возвращать только активные (true/false)'
    })
    @telegram_ns.response(200, 'OK', list_response)
    def get(self, current_user):
        try:
            user_id = current_user.get('user_id')
            active_only = request.args.get('active_only', 'true').lower() == 'true'
            db = get_db_session()
            service = TelegramChannelService(db)
            channels = service.get_user_channels(user_id, active_only=active_only)
            return {
                'success': True,
                'channels': [ch.to_dict() for ch in channels],
                'count': len(channels)
            }, 200
        except Exception as e:
            logger.error(f"Ошибка получения каналов: {e}")
            return {'success': False, 'error': 'Ошибка получения списка каналов'}, 500
        finally:
            if 'db' in locals() and db:
                db.close()

    @jwt_required
    @telegram_ns.doc('add_channel', security='BearerAuth')
    @telegram_ns.expect(add_channel_request, validate=True)
    def post(self, current_user):
        try:
            user_id = current_user.get('user_id')
            data = request.get_json() or {}
            channel_link = data.get('channel_link', '').strip()

            if not channel_link:
                return {'success': False, 'error': 'Укажите ссылку на канал'}, 400

            db = get_db_session()
            service = TelegramChannelService(db)
            
            # Используем упрощенный метод (автоматическое получение названия из Telegram API)
            success, message, channel = asyncio.run(
                service.upsert_and_activate_single_channel(user_id, channel_link)
            )
            if success:
                return {
                    'success': True,
                    'message': message,
                    'channel': channel.to_dict() if channel else None
                }, 201
            return {'success': False, 'error': message}, 400
        except Exception as e:
            logger.error(f"Критическая ошибка добавления канала: {e}")
            return {'success': False, 'error': 'Внутренняя ошибка сервера при добавлении канала'}, 500
        finally:
            if 'db' in locals() and db:
                db.close()


update_channel_request = telegram_ns.model('UpdateTelegramChannelRequest', {
    'channel_link': fields.String(description='Новая ссылка на канал (https://t.me/channel или @channel)', required=False),
    'channel_name': fields.String(description='Новое название канала', required=False),
    'is_active': fields.Boolean(description='Статус активации', required=False)
})


@telegram_ns.route('/channels/<int:channel_id>')
class TelegramChannelItem(Resource):
    @jwt_required
    @telegram_ns.doc('get_channel', security='BearerAuth')
    def get(self, current_user, channel_id: int):
        try:
            user_id = current_user.get('user_id')
            db = get_db_session()
            service = TelegramChannelService(db)
            channel = service.get_channel_by_id(user_id, channel_id)
            if not channel:
                return {'success': False, 'error': 'Канал не найден'}, 404
            return {'success': True, 'channel': channel.to_dict()}, 200
        except Exception as e:
            logger.error(f"Ошибка получения канала {channel_id}: {e}")
            return {'success': False, 'error': 'Ошибка получения информации о канале'}, 500
        finally:
            if 'db' in locals() and db:
                db.close()

    @jwt_required
    @telegram_ns.doc('update_channel', security='BearerAuth')
    @telegram_ns.expect(update_channel_request, validate=False)
    def put(self, current_user, channel_id: int):
        try:
            user_id = current_user.get('user_id')
            data = request.get_json() or {}
            
            channel_link = data.get('channel_link', '').strip() if data.get('channel_link') else None
            channel_name = data.get('channel_name', '').strip() if data.get('channel_name') else None
            is_active = data.get('is_active') if 'is_active' in data else None
            
            if not any([channel_link, channel_name, is_active is not None]):
                return {'success': False, 'error': 'Укажите хотя бы одно поле для обновления: channel_link, channel_name или is_active'}, 400
            
            db = get_db_session()
            service = TelegramChannelService(db)
            
            import asyncio
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
                return {
                    'success': True,
                    'message': message,
                    'channel': channel.to_dict() if channel else None
                }, 200
            return {'success': False, 'error': message}, 400
        except Exception as e:
            logger.error(f"Ошибка обновления канала {channel_id}: {e}")
            return {'success': False, 'error': 'Внутренняя ошибка сервера'}, 500
        finally:
            if 'db' in locals() and db:
                db.close()

    @jwt_required
    @telegram_ns.doc('delete_channel', security='BearerAuth')
    def delete(self, current_user, channel_id: int):
        try:
            user_id = current_user.get('user_id')
            db = get_db_session()
            service = TelegramChannelService(db)
            success = service.deactivate_channel(user_id, channel_id)
            if success:
                return {'success': True, 'message': 'Канал успешно удален'}, 200
            return {'success': False, 'error': 'Канал не найден'}, 404
        except Exception as e:
            logger.error(f"Ошибка удаления канала: {e}")
            return {'success': False, 'error': 'Ошибка удаления канала'}, 500
        finally:
            if 'db' in locals() and db:
                db.close()


@telegram_ns.route('/channels/<int:channel_id>/default')
class TelegramChannelDefault(Resource):
    @jwt_required
    @telegram_ns.doc('set_default_channel', security='BearerAuth')
    def put(self, current_user, channel_id: int):
        try:
            user_id = current_user.get('user_id')
            db = get_db_session()
            service = TelegramChannelService(db)
            success = service.set_default_channel(user_id, channel_id)
            if success:
                return {'success': True, 'message': 'Канал установлен по умолчанию'}, 200
            return {'success': False, 'error': 'Канал не найден или не активен'}, 404
        except Exception as e:
            logger.error(f"Ошибка установки дефолтного канала: {e}")
            return {'success': False, 'error': 'Ошибка установки канала по умолчанию'}, 500
        finally:
            if 'db' in locals() and db:
                db.close()


activate_telegram_request = telegram_ns.model('ActivateTelegramRequest', {
    'is_active': fields.Boolean(required=True, description='Статус активации (true/false)'),
    'channel_link': fields.String(description='Новая ссылка на канал (опционально - для автоматического обновления)', required=False),
    'channel_name': fields.String(description='Новое название канала (опционально - для автоматического обновления)', required=False)
})


@telegram_ns.route('/channels/<int:channel_id>/activate')
class TelegramChannelActivate(Resource):
    @jwt_required
    @telegram_ns.doc('toggle_telegram_activation', 
                     description='Активировать/деактивировать канал. Если указаны channel_link или channel_name - канал сначала обновится, затем активируется.',
                     security='BearerAuth')
    @telegram_ns.expect(activate_telegram_request, validate=False)
    def put(self, current_user, channel_id: int):
        try:
            user_id = current_user.get('user_id')
            data = request.get_json() or {}
            is_active = data.get('is_active')
            if is_active is None:
                return {'success': False, 'error': 'Укажите is_active (true/false)'}, 400
            
            # Опциональные поля для обновления канала
            channel_link = data.get('channel_link', '').strip() if data.get('channel_link') else None
            channel_name = data.get('channel_name', '').strip() if data.get('channel_name') else None
            
            db = get_db_session()
            service = TelegramChannelService(db)
            
            # Если указаны изменения канала - обновляем канал с активацией
            if channel_link or channel_name:
                import asyncio
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
                    return {
                        'success': True,
                        'message': message,
                        'is_active': is_active,
                        'channel': channel.to_dict() if channel else None
                    }, 200
                return {'success': False, 'error': message}, 400
            else:
                # Просто переключаем активацию без изменений
                success = service.toggle_activation(user_id, channel_id, bool(is_active))
                if success:
                    status_text = "активирован" if is_active else "деактивирован"
                    return {
                        'success': True,
                        'message': f'Канал успешно {status_text}',
                        'is_active': is_active
                    }, 200
                return {'success': False, 'error': 'Канал не найден'}, 404
        except Exception as e:
            logger.error(f"Ошибка переключения активации Telegram: {e}")
            return {'success': False, 'error': 'Внутренняя ошибка сервера'}, 500
        finally:
            if 'db' in locals() and db:
                db.close()


@telegram_ns.route('/channels/<int:channel_id>/verify')
class TelegramChannelVerify(Resource):
    @jwt_required
    @telegram_ns.doc('verify_channel', security='BearerAuth')
    def post(self, current_user, channel_id: int):
        try:
            user_id = current_user.get('user_id')
            db = get_db_session()
            service = TelegramChannelService(db)
            channel = service.get_channel_by_id(user_id, channel_id)
            if not channel:
                return {'success': False, 'error': 'Канал не найден'}, 404

            is_verified, chat_info = asyncio.run(
                service.verify_bot_in_channel(channel.chat_id)
            )

            if chat_info:
                channel.is_verified = is_verified
                channel.channel_title = chat_info.get('title')
                channel.channel_type = chat_info.get('type')
                channel.members_count = chat_info.get('members_count')
                if not is_verified:
                    channel.last_error = 'Бот не является администратором или без прав публикации'
                else:
                    channel.last_error = None
                db.commit()
                db.refresh(channel)
                return {
                    'success': True,
                    'channel': channel.to_dict(),
                    'message': '✅ Канал проверен и готов к публикациям' if is_verified else '⚠️ Добавьте бота в администраторы канала'
                }, 200

            channel.last_error = 'Не удалось получить информацию о канале'
            db.commit()
            return {'success': False, 'error': 'Не удалось подключиться к каналу. Проверьте бота'}, 400
        except Exception as e:
            logger.error(f"Ошибка проверки канала: {e}")
            return {'success': False, 'error': 'Ошибка проверки канала'}, 500
        finally:
            if 'db' in locals() and db:
                db.close()


# ===== УПРОЩЕННЫЕ ЭНДПОИНТЫ ДЛЯ ЕДИНСТВЕННОГО КАНАЛА =====

simple_activate_request = telegram_ns.model('SimpleActivateChannelRequest', {
    'channel_link': fields.String(required=True, description='Ссылка на канал (https://t.me/channel или @channel)')
})


@telegram_ns.route('/channel/activate')
class TelegramSingleChannelActivate(Resource):
    @jwt_required
    @telegram_ns.doc('activate_single_channel', 
                     description='''Упрощенный эндпоинт для единственного канала пользователя.
                     Клиент предоставляет только ссылку - все остальное делается автоматически:
                     - Находит существующий канал или создает новый
                     - Автоматически получает название из Telegram API
                     - Верифицирует канал
                     - Активирует его''',
                     security='BearerAuth')
    @telegram_ns.expect(simple_activate_request, validate=True)
    def put(self, current_user):
        try:
            user_id = current_user.get('user_id')
            data = request.get_json() or {}
            channel_link = data.get('channel_link', '').strip()
            
            if not channel_link:
                return {'success': False, 'error': 'Укажите ссылку на канал'}, 400
            
            db = get_db_session()
            service = TelegramChannelService(db)
            
            success, message, channel = asyncio.run(
                service.upsert_and_activate_single_channel(user_id, channel_link)
            )
            
            if success:
                return {
                    'success': True,
                    'message': message,
                    'channel': channel.to_dict() if channel else None
                }, 200
            return {'success': False, 'error': message}, 400
        except Exception as e:
            logger.error(f"Критическая ошибка активации канала: {e}")
            return {'success': False, 'error': 'Внутренняя ошибка сервера'}, 500
        finally:
            if 'db' in locals() and db:
                db.close()




