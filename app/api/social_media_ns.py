"""
Flask-RESTX namespace для управления социальными сетями (Swagger документация)
"""

from flask import request
from flask_restx import Namespace, Resource, fields
from functools import wraps
from app.database.connection import get_db_session
import logging

# Импортируем кастомный jwt_required декоратор из routes.py
from app.api.routes import jwt_required

logger = logging.getLogger(__name__)

# Создаем namespace
social_media_ns = Namespace(
    'social-media',
    description='Управление социальными сетями пользователя (Telegram, Instagram, Twitter)',
    path='/social-media'
)

# Модели для Swagger документации
metadata_model = social_media_ns.model('SocialMediaMetadata', {
    'channelLink': fields.String(description='Ссылка на канал (для Telegram)'),
    'channelId': fields.String(description='ID канала (для Telegram)'),
    'channelName': fields.String(description='Название канала (для Telegram)'),
    'username': fields.String(description='Username (для Instagram/Twitter)'),
    'userId': fields.String(description='ID пользователя в социальной сети'),
    'accountId': fields.Integer(description='ID аккаунта в нашей системе'),
    'isDefault': fields.Boolean(description='Является ли аккаунт по умолчанию'),
    'isActive': fields.Boolean(description='Активен ли аккаунт')
})

social_media_account_model = social_media_ns.model('SocialMediaAccount', {
    'name': fields.String(required=True, description='Название социальной сети', enum=['Telegram', 'Instagram', 'Twitter']),
    'isActive': fields.Boolean(required=True, description='Активна ли социальная сеть'),
    'metadata': fields.Nested(metadata_model, description='Метаданные аккаунта')
})

social_media_list_response_model = social_media_ns.model('SocialMediaListResponse', {
    'success': fields.Boolean(required=True, description='Статус запроса'),
    'data': fields.List(fields.Nested(social_media_account_model), description='Список социальных сетей')
})

update_request_model = social_media_ns.model('UpdateSocialMediaRequest', {
    'name': fields.String(required=True, description='Название социальной сети', enum=['Telegram', 'Instagram', 'Twitter']),
    'isActive': fields.Boolean(description='Активность социальной сети'),
    'metadata': fields.Nested(metadata_model, required=True, description='Данные для обновления')
})

update_response_model = social_media_ns.model('UpdateSocialMediaResponse', {
    'success': fields.Boolean(required=True, description='Статус запроса'),
    'message': fields.String(required=True, description='Сообщение о результате')
})

error_model = social_media_ns.model('ErrorResponse', {
    'success': fields.Boolean(description='Статус запроса'),
    'error': fields.String(description='Текст ошибки')
})


@social_media_ns.route('/accounts')
class SocialMediaAccounts(Resource):
    
    @jwt_required
    @social_media_ns.doc('get_social_media_accounts',
        security='BearerAuth',
        description='Получить все подключенные социальные сети пользователя с их настройками',
        responses={
            200: ('Success', social_media_list_response_model),
            401: ('Unauthorized', error_model),
            500: ('Internal Server Error', error_model)
        }
    )
    def get(self, current_user):
        """Получить все социальные сети пользователя"""
        try:
            user_id = current_user.get('user_id')
            db = get_db_session()
            
            social_media_accounts = []
            
            # Telegram channels
            try:
                from app.models.telegram_channels import TelegramChannel
                telegram_channels = db.query(TelegramChannel).filter(
                    TelegramChannel.user_id == user_id
                ).all()
                
                for channel in telegram_channels:
                    social_media_accounts.append({
                        "name": "Telegram",
                        "isActive": True,
                        "metadata": {
                            "channelLink": channel.channel_link,
                            "accountId": channel.id,
                            "isDefault": channel.is_default,
                            "channelId": channel.channel_id,
                            "channelName": channel.channel_name
                        }
                    })
            except ImportError:
                logger.warning("TelegramChannel model not found")
            
            # Instagram accounts
            try:
                from app.models.instagram_accounts import InstagramAccount
                instagram_accounts = db.query(InstagramAccount).filter(
                    InstagramAccount.user_id == user_id
                ).all()
                
                for account in instagram_accounts:
                    social_media_accounts.append({
                        "name": "Instagram",
                        "isActive": True,
                        "metadata": {
                            "username": account.username,
                            "accountId": account.id,
                            "isDefault": account.is_default,
                            "isActive": account.is_active
                        }
                    })
            except ImportError:
                logger.warning("InstagramAccount model not found")
            
            # Twitter accounts
            try:
                from app.models.twitter_accounts import TwitterAccount
                twitter_accounts = db.query(TwitterAccount).filter(
                    TwitterAccount.user_id == user_id
                ).all()
                
                for account in twitter_accounts:
                    social_media_accounts.append({
                        "name": "Twitter",
                        "isActive": True,
                        "metadata": {
                            "username": account.username,
                            "accountId": account.id,
                            "isDefault": account.is_default,
                            "userId": account.twitter_user_id
                        }
                    })
            except ImportError:
                logger.warning("TwitterAccount model not found")
            
            return {
                'success': True,
                'data': social_media_accounts
            }, 200
            
        except Exception as e:
            logger.error(f"Error getting social media accounts: {e}", exc_info=True)
            return {
                'success': False,
                'error': 'Ошибка получения социальных сетей',
                'details': str(e)
            }, 500
        finally:
            if db:
                db.close()
    
    @jwt_required
    @social_media_ns.doc('update_social_media_account',
        security='BearerAuth',
        description='Обновить настройки конкретной социальной сети',
        responses={
            200: ('Success', update_response_model),
            400: ('Bad Request', error_model),
            401: ('Unauthorized', error_model),
            404: ('Not Found', error_model),
            500: ('Internal Server Error', error_model)
        }
    )
    @social_media_ns.expect(update_request_model)
    def put(self, current_user):
        """Обновить настройки социальной сети"""
        try:
            user_id = current_user.get('user_id')
            data = request.get_json()
            
            if not data:
                return {'error': 'Данные не предоставлены'}, 400
            
            social_media_name = data.get('name')
            is_active = data.get('isActive', True)
            metadata = data.get('metadata', {})
            
            if not social_media_name:
                return {'error': 'Название социальной сети не указано'}, 400
            
            db = get_db_session()
            
            # Обновление в зависимости от типа социальной сети
            if social_media_name.lower() == 'telegram':
                account_id = metadata.get('accountId')
                if not account_id:
                    return {'error': 'accountId обязателен для обновления'}, 400
                if account_id:
                    try:
                        from app.models.telegram_channels import TelegramChannel
                        channel = db.query(TelegramChannel).filter(
                            TelegramChannel.id == account_id,
                            TelegramChannel.user_id == user_id
                        ).first()
                        
                        if channel:
                            channel.is_default = metadata.get('isDefault', channel.is_default)
                            db.commit()
                            
                            return {
                                'success': True,
                                'message': 'Telegram канал обновлен'
                            }, 200
                        else:
                            return {'error': 'Канал не найден'}, 404
                    except ImportError:
                        return {'error': 'Telegram не поддерживается'}, 400
            
            elif social_media_name.lower() == 'instagram':
                account_id = metadata.get('accountId')
                if not account_id:
                    return {'error': 'accountId обязателен для обновления'}, 400
                if account_id:
                    try:
                        from app.models.instagram_accounts import InstagramAccount
                        account = db.query(InstagramAccount).filter(
                            InstagramAccount.id == account_id,
                            InstagramAccount.user_id == user_id
                        ).first()
                        
                        if account:
                            account.is_default = metadata.get('isDefault', account.is_default)
                            account.is_active = is_active
                            db.commit()
                            
                            return {
                                'success': True,
                                'message': 'Instagram аккаунт обновлен'
                            }, 200
                        else:
                            return {'error': 'Аккаунт не найден'}, 404
                    except ImportError:
                        return {'error': 'Instagram не поддерживается'}, 400
            
            elif social_media_name.lower() == 'twitter':
                account_id = metadata.get('accountId')
                if not account_id:
                    return {'error': 'accountId обязателен для обновления'}, 400
                if account_id:
                    try:
                        from app.models.twitter_accounts import TwitterAccount
                        account = db.query(TwitterAccount).filter(
                            TwitterAccount.id == account_id,
                            TwitterAccount.user_id == user_id
                        ).first()
                        
                        if account:
                            account.is_default = metadata.get('isDefault', account.is_default)
                            account.is_active = is_active
                            db.commit()
                            
                            return {
                                'success': True,
                                'message': 'Twitter аккаунт обновлен'
                            }, 200
                        else:
                            return {'error': 'Аккаунт не найден'}, 404
                    except ImportError:
                        return {'error': 'Twitter не поддерживается'}, 400
            
            else:
                return {'error': 'Неподдерживаемая социальная сеть'}, 400
            
        except Exception as e:
            logger.error(f"Error updating social media account: {e}")
            return {
                'success': False,
                'error': 'Ошибка обновления настроек'
            }, 500


