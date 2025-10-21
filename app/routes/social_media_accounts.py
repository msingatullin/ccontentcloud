"""
Универсальные API routes для управления социальными сетями
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database.connection import get_db_session
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('social_media_accounts', __name__, url_prefix='/api/social-media')


@bp.route('/accounts', methods=['GET'])
@jwt_required()
def get_social_media_accounts():
    """
    Получить все социальные сети пользователя
    
    Returns:
        Collection of social media accounts with format:
        [
            {
                "name": "Telegram|Instagram|Twitter",
                "isActive": true/false,
                "metadata": {
                    "channelLink": "https://t.me/channel",
                    "accountId": 123,
                    "isDefault": true/false
                }
            }
        ]
    """
    try:
        user_id = get_jwt_identity()['user_id']
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
        
        db.close()
        
        return jsonify({
            'success': True,
            'data': social_media_accounts
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting social media accounts: {e}")
        return jsonify({
            'success': False,
            'error': 'Ошибка получения социальных сетей'
        }), 500


@bp.route('/accounts', methods=['PUT'])
@jwt_required()
def update_social_media_account():
    """
    Обновить настройки социальной сети
    
    Expected payload:
    {
        "name": "Telegram|Instagram|Twitter",
        "isActive": true/false,
        "metadata": {
            "channelLink": "https://t.me/channel",
            "key": "value"
        }
    }
    """
    try:
        user_id = get_jwt_identity()['user_id']
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Данные не предоставлены'}), 400
        
        social_media_name = data.get('name')
        is_active = data.get('isActive', True)
        metadata = data.get('metadata', {})
        
        if not social_media_name:
            return jsonify({'error': 'Название социальной сети не указано'}), 400
        
        db = get_db_session()
        
        # Обновление в зависимости от типа социальной сети
        if social_media_name.lower() == 'telegram':
            # Логика обновления Telegram каналов
            account_id = metadata.get('accountId')
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
                        
                        return jsonify({
                            'success': True,
                            'message': 'Telegram канал обновлен'
                        }), 200
                    else:
                        return jsonify({'error': 'Канал не найден'}), 404
                except ImportError:
                    return jsonify({'error': 'Telegram не поддерживается'}), 400
        
        elif social_media_name.lower() == 'instagram':
            # Логика обновления Instagram аккаунтов
            account_id = metadata.get('accountId')
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
                        
                        return jsonify({
                            'success': True,
                            'message': 'Instagram аккаунт обновлен'
                        }), 200
                    else:
                        return jsonify({'error': 'Аккаунт не найден'}), 404
                except ImportError:
                    return jsonify({'error': 'Instagram не поддерживается'}), 400
        
        elif social_media_name.lower() == 'twitter':
            # Логика обновления Twitter аккаунтов
            account_id = metadata.get('accountId')
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
                        
                        return jsonify({
                            'success': True,
                            'message': 'Twitter аккаунт обновлен'
                        }), 200
                    else:
                        return jsonify({'error': 'Аккаунт не найден'}), 404
                except ImportError:
                    return jsonify({'error': 'Twitter не поддерживается'}), 400
        
        else:
            return jsonify({'error': 'Неподдерживаемая социальная сеть'}), 400
        
        db.close()
        
        return jsonify({
            'success': True,
            'message': 'Настройки обновлены'
        }), 200
        
    except Exception as e:
        logger.error(f"Error updating social media account: {e}")
        return jsonify({
            'success': False,
            'error': 'Ошибка обновления настроек'
        }), 500
