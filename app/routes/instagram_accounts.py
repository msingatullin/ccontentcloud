"""
API routes для управления Instagram аккаунтами
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.instagram_account_service import InstagramAccountService
from app.database.connection import get_db
import asyncio
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('instagram_accounts', __name__, url_prefix='/api/instagram')


@bp.route('/accounts', methods=['GET'])
@jwt_required()
def get_accounts():
    """
    Получить все Instagram аккаунты текущего пользователя
    
    Query params:
        active_only: bool (default=true)
    
    Returns:
        JSON со списком аккаунтов
    """
    try:
        user_id = get_jwt_identity()
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        
        db = next(get_db())
        service = InstagramAccountService(db)
        
        accounts = service.get_user_accounts(user_id, active_only=active_only)
        
        return jsonify({
            'success': True,
            'accounts': [acc.to_dict() for acc in accounts],
            'count': len(accounts)
        }), 200
        
    except Exception as e:
        logger.error(f"Ошибка получения Instagram аккаунтов: {e}")
        return jsonify({
            'success': False,
            'error': 'Ошибка получения списка аккаунтов'
        }), 500


@bp.route('/accounts', methods=['POST'])
@jwt_required()
def add_account():
    """
    Добавить новый Instagram аккаунт
    
    Body:
        {
            "username": "instagram_username",
            "password": "instagram_password",
            "account_name": "Мой Instagram аккаунт"
        }
    
    Returns:
        JSON с результатом и данными аккаунта
    """
    try:
        user_id = get_jwt_identity()
        data = request.get_json()
        
        # Валидация
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        account_name = data.get('account_name', '').strip()
        
        if not username:
            return jsonify({
                'success': False,
                'error': 'Укажите Instagram username'
            }), 400
        
        if not password:
            return jsonify({
                'success': False,
                'error': 'Укажите пароль от Instagram'
            }), 400
        
        if not account_name:
            return jsonify({
                'success': False,
                'error': 'Укажите название аккаунта'
            }), 400
        
        if len(account_name) < 3:
            return jsonify({
                'success': False,
                'error': 'Название должно быть не короче 3 символов'
            }), 400
        
        db = next(get_db())
        service = InstagramAccountService(db)
        
        # Добавляем аккаунт (async операция)
        success, message, account = asyncio.run(
            service.add_account(user_id, username, password, account_name)
        )
        
        if success:
            logger.info(f"✅ Instagram аккаунт добавлен: user_id={user_id}, account_id={account.id if account else None}")
            return jsonify({
                'success': True,
                'message': message,
                'account': account.to_dict() if account else None
            }), 201
        else:
            logger.warning(f"❌ Не удалось добавить Instagram: {message}")
            return jsonify({
                'success': False,
                'error': message
            }), 400
            
    except Exception as e:
        logger.error(f"Критическая ошибка добавления Instagram: {e}")
        return jsonify({
            'success': False,
            'error': 'Внутренняя ошибка сервера'
        }), 500


@bp.route('/accounts/<int:account_id>', methods=['GET'])
@jwt_required()
def get_account(account_id):
    """Получить информацию о конкретном аккаунте"""
    try:
        user_id = get_jwt_identity()
        
        db = next(get_db())
        service = InstagramAccountService(db)
        
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
        
        db = next(get_db())
        service = InstagramAccountService(db)
        
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
        
        db = next(get_db())
        service = InstagramAccountService(db)
        
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
    Получить информацию и инструкцию для подключения Instagram
    
    Returns:
        JSON с инструкцией
    """
    return jsonify({
        'success': True,
        'info': {
            'title': 'Подключение Instagram',
            'requirements': [
                'Отключите двухфакторную аутентификацию (2FA)',
                'Используйте логин и пароль от Instagram',
                'Аккаунт должен быть старше 3 месяцев для стабильной работы'
            ],
            'instructions': [
                'Откройте Instagram → Настройки → Безопасность',
                'Отключите "Двухфакторную аутентификацию"',
                'Если используете вход через Google/Facebook - создайте пароль',
                'Введите ваш Instagram username и пароль в форме',
                'Нажмите "Подключить"'
            ],
            'security': [
                'Пароль хранится в зашифрованном виде',
                'Используется официальная библиотека Instagram API',
                'Соблюдаем лимиты Instagram (защита от блокировки)'
            ],
            'limits': {
                'daily_posts': 10,
                'description': 'Максимум 10 постов в день для защиты от блокировки'
            }
        }
    }), 200


