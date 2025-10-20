"""
API routes для управления Twitter аккаунтами
Includes OAuth 1.0a flow
"""

from flask import Blueprint, request, jsonify, redirect, session
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.twitter_account_service import TwitterAccountService
from app.database.connection import get_db_session
import asyncio
import logging
import os

logger = logging.getLogger(__name__)

bp = Blueprint('twitter_accounts', __name__, url_prefix='/api/twitter')


@bp.route('/oauth/url', methods=['GET'])
@jwt_required()
def get_oauth_url():
    """
    Получить URL для OAuth авторизации (шаг 1)
    
    Query params:
        callback_url: URL для возврата (опционально)
    
    Returns:
        JSON с URL для редиректа и токенами для сессии
    """
    try:
        user_id = get_jwt_identity()
        
        # Callback URL
        callback_url = request.args.get('callback_url')
        if not callback_url:
            # Default callback
            base_url = os.getenv('API_BASE_URL', 'http://localhost:5000')
            callback_url = f"{base_url}/api/twitter/oauth/callback"
        
        db = next(get_db_session())
        service = TwitterAccountService(db)
        
        # Получаем OAuth URL
        auth_url, oauth_token, oauth_token_secret = service.get_oauth_url(callback_url)
        
        logger.info(f"OAuth URL сгенерирован для user_id={user_id}")
        
        return jsonify({
            'success': True,
            'auth_url': auth_url,
            'oauth_token': oauth_token,
            'oauth_token_secret': oauth_token_secret,
            'message': 'Сохраните oauth_token_secret и передайте в callback'
        }), 200
        
    except Exception as e:
        logger.error(f"Ошибка генерации OAuth URL: {e}")
        return jsonify({
            'success': False,
            'error': f'Ошибка OAuth: {str(e)}'
        }), 500


@bp.route('/oauth/callback', methods=['GET', 'POST'])
@jwt_required()
def oauth_callback():
    """
    OAuth callback (шаг 2)
    
    Query params (от Twitter):
        oauth_token: токен
        oauth_verifier: verifier
    
    Body (от фронтенда):
        {
            "oauth_token_secret": "сохраненный secret",
            "account_name": "Мой Twitter"
        }
    
    Returns:
        JSON с результатом
    """
    try:
        user_id = get_jwt_identity()
        
        # Получаем параметры от Twitter
        oauth_token = request.args.get('oauth_token')
        oauth_verifier = request.args.get('oauth_verifier')
        
        if not oauth_token or not oauth_verifier:
            return jsonify({
                'success': False,
                'error': 'Отсутствуют параметры OAuth от Twitter'
            }), 400
        
        # Получаем данные от фронтенда
        data = request.get_json() or {}
        oauth_token_secret = data.get('oauth_token_secret')
        account_name = data.get('account_name', 'Мой Twitter аккаунт')
        
        if not oauth_token_secret:
            return jsonify({
                'success': False,
                'error': 'oauth_token_secret обязателен'
            }), 400
        
        db = next(get_db_session())
        service = TwitterAccountService(db)
        
        # Завершаем OAuth
        success, message, account = asyncio.run(
            service.complete_oauth(
                user_id=user_id,
                oauth_token=oauth_token,
                oauth_verifier=oauth_verifier,
                oauth_token_secret=oauth_token_secret,
                account_name=account_name
            )
        )
        
        if success:
            logger.info(f"✅ Twitter OAuth успешен для user_id={user_id}")
            return jsonify({
                'success': True,
                'message': message,
                'account': account.to_dict() if account else None
            }), 201
        else:
            logger.warning(f"❌ Twitter OAuth не удался: {message}")
            return jsonify({
                'success': False,
                'error': message
            }), 400
            
    except Exception as e:
        logger.error(f"Критическая ошибка OAuth callback: {e}")
        return jsonify({
            'success': False,
            'error': 'Внутренняя ошибка сервера'
        }), 500


@bp.route('/accounts', methods=['GET'])
@jwt_required()
def get_accounts():
    """
    Получить все Twitter аккаунты текущего пользователя
    
    Query params:
        active_only: bool (default=true)
    
    Returns:
        JSON со списком аккаунтов
    """
    try:
        user_id = get_jwt_identity()
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        db = next(get_db_session())
        service = TwitterAccountService(db)
        
        accounts = service.get_user_accounts(user_id, active_only=active_only)
        
        return jsonify({
            'success': True,
            'accounts': [acc.to_dict() for acc in accounts],
            'count': len(accounts)
        }), 200
        
    except Exception as e:
        logger.error(f"Ошибка получения Twitter аккаунтов: {e}")
        return jsonify({
            'success': False,
            'error': 'Ошибка получения списка аккаунтов'
        }), 500


@bp.route('/accounts/<int:account_id>', methods=['GET'])
@jwt_required()
def get_account(account_id):
    """Получить информацию о конкретном аккаунте"""
    try:
        user_id = get_jwt_identity()
        
        db = next(get_db_session())
        service = TwitterAccountService(db)
        
        account = service.get_account_by_id(user_id, account_id)
        
        if not account:
            return jsonify({
                'success': False,
                'error': 'Аккаунт не найден'
            }), 404
        
        return jsonify({
            'success': True,
            'account': account.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f"Ошибка получения аккаунта: {e}")
        return jsonify({
            'success': False,
            'error': 'Ошибка получения информации'
        }), 500


@bp.route('/accounts/<int:account_id>/default', methods=['PUT'])
@jwt_required()
def set_default_account(account_id):
    """Установить аккаунт как дефолтный"""
    try:
        user_id = get_jwt_identity()
        
        db = next(get_db_session())
        service = TwitterAccountService(db)
        
        success = service.set_default_account(user_id, account_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Аккаунт установлен по умолчанию'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Аккаунт не найден'
            }), 404
            
    except Exception as e:
        logger.error(f"Ошибка установки дефолтного аккаунта: {e}")
        return jsonify({
            'success': False,
            'error': 'Ошибка установки'
        }), 500


@bp.route('/accounts/<int:account_id>', methods=['DELETE'])
@jwt_required()
def delete_account(account_id):
    """Удалить (деактивировать) аккаунт"""
    try:
        user_id = get_jwt_identity()
        
        db = next(get_db_session())
        service = TwitterAccountService(db)
        
        success = service.deactivate_account(user_id, account_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Аккаунт успешно удален'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'Аккаунт не найден'
            }), 404
            
    except Exception as e:
        logger.error(f"Ошибка удаления аккаунта: {e}")
        return jsonify({
            'success': False,
            'error': 'Ошибка удаления'
        }), 500


@bp.route('/info', methods=['GET'])
@jwt_required()
def get_info():
    """
    Получить информацию и инструкцию для подключения Twitter
    
    Returns:
        JSON с инструкцией
    """
    return jsonify({
        'success': True,
        'info': {
            'title': 'Подключение Twitter',
            'method': 'OAuth 1.0a',
            'instructions': [
                'Нажмите кнопку "Подключить Twitter"',
                'Вы будете перенаправлены на Twitter.com',
                'Авторизуйтесь в Twitter (если еще не вошли)',
                'Разрешите доступ приложению Content4u',
                'Вас вернет обратно - аккаунт подключен!'
            ],
            'security': [
                'Используется официальный Twitter OAuth',
                'Вы можете отозвать доступ в любой момент',
                'Токены хранятся в зашифрованном виде'
            ],
            'permissions': [
                'Публикация твитов от вашего имени',
                'Загрузка медиа файлов',
                'Чтение информации профиля'
            ]
        }
    }), 200


