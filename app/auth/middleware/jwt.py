"""
JWT Middleware для защиты маршрутов
"""

from functools import wraps
from typing import Optional, Callable, Any
from flask import request, jsonify, g, current_app
import logging

from app.auth.services.auth_service import AuthService
from app.auth.models.user import User, UserRole

logger = logging.getLogger(__name__)


class JWTMiddleware:
    """JWT Middleware для аутентификации"""
    
    def __init__(self, auth_service: AuthService):
        self.auth_service = auth_service

    def get_token_from_header(self) -> Optional[str]:
        """Извлечь токен из заголовка Authorization"""
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None
        
        try:
            scheme, token = auth_header.split(' ', 1)
            if scheme.lower() != 'bearer':
                return None
            return token
        except ValueError:
            return None

    def get_current_user(self) -> Optional[User]:
        """Получить текущего пользователя из токена"""
        token = self.get_token_from_header()
        if not token:
            return None
        
        is_valid, payload = self.auth_service.verify_token(token)
        if not is_valid or not payload:
            return None
        
        return self.auth_service.get_user_by_id(payload['user_id'])

    def require_auth(self, f: Callable) -> Callable:
        """Декоратор для требующих аутентификации маршрутов"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = self.get_token_from_header()
            
            if not token:
                return jsonify({
                    'error': 'Токен доступа не предоставлен',
                    'code': 'MISSING_TOKEN'
                }), 401
            
            is_valid, payload = self.auth_service.verify_token(token)
            
            if not is_valid or not payload:
                return jsonify({
                    'error': 'Неверный или истекший токен',
                    'code': 'INVALID_TOKEN'
                }), 401
            
            # Получение пользователя
            user = self.auth_service.get_user_by_id(payload['user_id'])
            if not user:
                return jsonify({
                    'error': 'Пользователь не найден',
                    'code': 'USER_NOT_FOUND'
                }), 401
            
            # Проверка статуса пользователя
            if not user.is_active:
                return jsonify({
                    'error': 'Аккаунт деактивирован',
                    'code': 'ACCOUNT_DEACTIVATED'
                }), 401
            
            if user.status.value == 'suspended':
                return jsonify({
                    'error': 'Аккаунт заблокирован',
                    'code': 'ACCOUNT_SUSPENDED'
                }), 401
            
            # Сохранение пользователя в контексте
            g.current_user = user
            g.current_user_id = user.id
            g.current_user_role = user.role
            g.token_payload = payload
            
            return f(*args, **kwargs)
        
        return decorated_function

    def require_verified_email(self, f: Callable) -> Callable:
        """Декоратор для требующих подтвержденный email"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_user'):
                return jsonify({
                    'error': 'Требуется аутентификация',
                    'code': 'AUTHENTICATION_REQUIRED'
                }), 401
            
            if not g.current_user.is_verified:
                return jsonify({
                    'error': 'Требуется подтверждение email',
                    'code': 'EMAIL_NOT_VERIFIED'
                }), 403
            
            return f(*args, **kwargs)
        
        return decorated_function

    def require_role(self, *allowed_roles: UserRole) -> Callable:
        """Декоратор для проверки роли пользователя"""
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not hasattr(g, 'current_user'):
                    return jsonify({
                        'error': 'Требуется аутентификация',
                        'code': 'AUTHENTICATION_REQUIRED'
                    }), 401
                
                if g.current_user.role not in allowed_roles:
                    return jsonify({
                        'error': 'Недостаточно прав доступа',
                        'code': 'INSUFFICIENT_PERMISSIONS'
                    }), 403
                
                return f(*args, **kwargs)
            
            return decorated_function
        return decorator

    def require_admin(self, f: Callable) -> Callable:
        """Декоратор для требующих админских прав"""
        return self.require_role(UserRole.ADMIN)(f)

    def require_moderator(self, f: Callable) -> Callable:
        """Декоратор для требующих прав модератора"""
        return self.require_role(UserRole.ADMIN, UserRole.MODERATOR)(f)

    def optional_auth(self, f: Callable) -> Callable:
        """Декоратор для опциональной аутентификации"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = self.get_token_from_header()
            
            if token:
                is_valid, payload = self.auth_service.verify_token(token)
                if is_valid and payload:
                    user = self.auth_service.get_user_by_id(payload['user_id'])
                    if user and user.is_active:
                        g.current_user = user
                        g.current_user_id = user.id
                        g.current_user_role = user.role
                        g.token_payload = payload
            
            return f(*args, **kwargs)
        
        return decorated_function

    def rate_limit_by_user(self, max_requests: int = 100, window_minutes: int = 60) -> Callable:
        """Декоратор для ограничения запросов по пользователю"""
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if not hasattr(g, 'current_user_id'):
                    return f(*args, **kwargs)
                
                # Здесь можно добавить логику rate limiting
                # Например, используя Redis для хранения счетчиков
                # Пока что просто пропускаем
                
                return f(*args, **kwargs)
            
            return decorated_function
        return decorator

    def log_user_activity(self, action: str) -> Callable:
        """Декоратор для логирования активности пользователя"""
        def decorator(f: Callable) -> Callable:
            @wraps(f)
            def decorated_function(*args, **kwargs):
                result = f(*args, **kwargs)
                
                if hasattr(g, 'current_user_id'):
                    logger.info(f"User {g.current_user_id} performed action: {action}")
                
                return result
            
            return decorated_function
        return decorator


def get_current_user() -> Optional[User]:
    """Получить текущего пользователя из контекста"""
    return getattr(g, 'current_user', None)


def get_current_user_id() -> Optional[int]:
    """Получить ID текущего пользователя"""
    return getattr(g, 'current_user_id', None)


def get_current_user_role() -> Optional[UserRole]:
    """Получить роль текущего пользователя"""
    return getattr(g, 'current_user_role', None)


def is_authenticated() -> bool:
    """Проверить, аутентифицирован ли пользователь"""
    return hasattr(g, 'current_user') and g.current_user is not None


def is_admin() -> bool:
    """Проверить, является ли пользователь администратором"""
    return (is_authenticated() and 
            get_current_user_role() == UserRole.ADMIN)


def is_moderator() -> bool:
    """Проверить, является ли пользователь модератором"""
    return (is_authenticated() and 
            get_current_user_role() in [UserRole.ADMIN, UserRole.MODERATOR])


def require_auth_response() -> tuple:
    """Стандартный ответ для неаутентифицированных пользователей"""
    return jsonify({
        'error': 'Требуется аутентификация',
        'code': 'AUTHENTICATION_REQUIRED'
    }), 401


def require_permission_response() -> tuple:
    """Стандартный ответ для недостаточных прав"""
    return jsonify({
        'error': 'Недостаточно прав доступа',
        'code': 'INSUFFICIENT_PERMISSIONS'
    }), 403


def require_verification_response() -> tuple:
    """Стандартный ответ для неподтвержденного email"""
    return jsonify({
        'error': 'Требуется подтверждение email',
        'code': 'EMAIL_NOT_VERIFIED'
    }), 403
