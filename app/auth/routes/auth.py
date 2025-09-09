"""
API маршруты для аутентификации
"""

from flask import Blueprint, request, jsonify, g
from sqlalchemy.orm import Session
from marshmallow import Schema, fields, validate, ValidationError
import logging

from app.auth.services.auth_service import AuthService
from app.auth.utils.email import EmailService
from app.auth.middleware.jwt import JWTMiddleware, require_auth_response
from app.auth.models.user import User, UserRole

logger = logging.getLogger(__name__)

# Создание Blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Схемы валидации
class RegisterSchema(Schema):
    email = fields.Email(required=True, validate=validate.Length(max=255))
    password = fields.Str(required=True, validate=validate.Length(min=8, max=128))
    username = fields.Str(required=True, validate=validate.Length(min=3, max=100))
    first_name = fields.Str(validate=validate.Length(max=100))
    last_name = fields.Str(validate=validate.Length(max=100))
    company = fields.Str(validate=validate.Length(max=200))
    phone = fields.Str(validate=validate.Length(max=20))

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)

class ChangePasswordSchema(Schema):
    current_password = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate.Length(min=8, max=128))

class UpdateProfileSchema(Schema):
    first_name = fields.Str(validate=validate.Length(max=100))
    last_name = fields.Str(validate=validate.Length(max=100))
    phone = fields.Str(validate=validate.Length(max=20))
    company = fields.Str(validate=validate.Length(max=200))
    position = fields.Str(validate=validate.Length(max=100))
    timezone = fields.Str(validate=validate.Length(max=50))
    language = fields.Str(validate=validate.Length(max=10))
    notifications_enabled = fields.Bool()
    marketing_emails = fields.Bool()

class VerifyEmailSchema(Schema):
    token = fields.Str(required=True)

class PasswordResetRequestSchema(Schema):
    email = fields.Email(required=True)

class PasswordResetSchema(Schema):
    token = fields.Str(required=True)
    new_password = fields.Str(required=True, validate=validate.Length(min=8, max=128))

class RefreshTokenSchema(Schema):
    refresh_token = fields.Str(required=True)


def init_auth_routes(db_session: Session, secret_key: str):
    """Инициализация маршрутов аутентификации"""
    
    # Создание сервисов
    email_service = EmailService()
    auth_service = AuthService(db_session, secret_key, email_service)
    jwt_middleware = JWTMiddleware(auth_service)
    
    # Схемы валидации
    register_schema = RegisterSchema()
    login_schema = LoginSchema()
    change_password_schema = ChangePasswordSchema()
    update_profile_schema = UpdateProfileSchema()
    verify_email_schema = VerifyEmailSchema()
    password_reset_request_schema = PasswordResetRequestSchema()
    password_reset_schema = PasswordResetSchema()
    refresh_token_schema = RefreshTokenSchema()

    @auth_bp.route('/register', methods=['POST'])
    def register():
        """Регистрация нового пользователя"""
        try:
            # Валидация данных
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Данные не предоставлены'}), 400
            
            try:
                validated_data = register_schema.load(data)
            except ValidationError as err:
                return jsonify({'error': 'Ошибка валидации', 'details': err.messages}), 400
            
            # Регистрация пользователя
            success, message, user = auth_service.register_user(**validated_data)
            
            if success:
                return jsonify({
                    'message': message,
                    'user': user.to_dict()
                }), 201
            else:
                return jsonify({'error': message}), 400
                
        except Exception as e:
            logger.error(f"Error in register endpoint: {e}")
            return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

    @auth_bp.route('/login', methods=['POST'])
    def login():
        """Авторизация пользователя"""
        try:
            # Валидация данных
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Данные не предоставлены'}), 400
            
            try:
                validated_data = login_schema.load(data)
            except ValidationError as err:
                return jsonify({'error': 'Ошибка валидации', 'details': err.messages}), 400
            
            # Получение информации об устройстве
            device_info = {
                'user_agent': request.headers.get('User-Agent'),
                'ip': request.remote_addr
            }
            
            # Авторизация
            success, message, tokens = auth_service.login_user(
                validated_data['email'],
                validated_data['password'],
                device_info=device_info,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            
            if success:
                return jsonify({
                    'message': message,
                    **tokens
                }), 200
            else:
                return jsonify({'error': message}), 401
                
        except Exception as e:
            logger.error(f"Error in login endpoint: {e}")
            return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

    @auth_bp.route('/verify-email', methods=['POST'])
    def verify_email():
        """Верификация email"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Данные не предоставлены'}), 400
            
            try:
                validated_data = verify_email_schema.load(data)
            except ValidationError as err:
                return jsonify({'error': 'Ошибка валидации', 'details': err.messages}), 400
            
            success, message = auth_service.verify_email(validated_data['token'])
            
            if success:
                return jsonify({'message': message}), 200
            else:
                return jsonify({'error': message}), 400
                
        except Exception as e:
            logger.error(f"Error in verify_email endpoint: {e}")
            return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

    @auth_bp.route('/resend-verification', methods=['POST'])
    def resend_verification():
        """Повторная отправка email верификации"""
        try:
            data = request.get_json()
            if not data or 'email' not in data:
                return jsonify({'error': 'Email не предоставлен'}), 400
            
            success, message = auth_service.resend_verification_email(data['email'])
            
            if success:
                return jsonify({'message': message}), 200
            else:
                return jsonify({'error': message}), 400
                
        except Exception as e:
            logger.error(f"Error in resend_verification endpoint: {e}")
            return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

    @auth_bp.route('/forgot-password', methods=['POST'])
    def forgot_password():
        """Запрос сброса пароля"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Данные не предоставлены'}), 400
            
            try:
                validated_data = password_reset_request_schema.load(data)
            except ValidationError as err:
                return jsonify({'error': 'Ошибка валидации', 'details': err.messages}), 400
            
            success, message = auth_service.request_password_reset(validated_data['email'])
            
            return jsonify({'message': message}), 200
                
        except Exception as e:
            logger.error(f"Error in forgot_password endpoint: {e}")
            return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

    @auth_bp.route('/reset-password', methods=['POST'])
    def reset_password():
        """Сброс пароля"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Данные не предоставлены'}), 400
            
            try:
                validated_data = password_reset_schema.load(data)
            except ValidationError as err:
                return jsonify({'error': 'Ошибка валидации', 'details': err.messages}), 400
            
            success, message = auth_service.reset_password(
                validated_data['token'],
                validated_data['new_password']
            )
            
            if success:
                return jsonify({'message': message}), 200
            else:
                return jsonify({'error': message}), 400
                
        except Exception as e:
            logger.error(f"Error in reset_password endpoint: {e}")
            return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

    @auth_bp.route('/refresh', methods=['POST'])
    def refresh_token():
        """Обновление токена"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Данные не предоставлены'}), 400
            
            try:
                validated_data = refresh_token_schema.load(data)
            except ValidationError as err:
                return jsonify({'error': 'Ошибка валидации', 'details': err.messages}), 400
            
            success, message, tokens = auth_service.refresh_token(validated_data['refresh_token'])
            
            if success:
                return jsonify({
                    'message': message,
                    **tokens
                }), 200
            else:
                return jsonify({'error': message}), 401
                
        except Exception as e:
            logger.error(f"Error in refresh_token endpoint: {e}")
            return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

    @auth_bp.route('/logout', methods=['POST'])
    @jwt_middleware.require_auth
    def logout():
        """Выход пользователя"""
        try:
            token_jti = g.token_payload.get('jti')
            success, message = auth_service.logout_user(token_jti)
            
            if success:
                return jsonify({'message': message}), 200
            else:
                return jsonify({'error': message}), 500
                
        except Exception as e:
            logger.error(f"Error in logout endpoint: {e}")
            return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

    @auth_bp.route('/logout-all', methods=['POST'])
    @jwt_middleware.require_auth
    def logout_all():
        """Выход из всех сессий"""
        try:
            success, message = auth_service.logout_all_sessions(g.current_user_id)
            
            if success:
                return jsonify({'message': message}), 200
            else:
                return jsonify({'error': message}), 500
                
        except Exception as e:
            logger.error(f"Error in logout_all endpoint: {e}")
            return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

    @auth_bp.route('/me', methods=['GET'])
    @jwt_middleware.require_auth
    def get_current_user():
        """Получить информацию о текущем пользователе"""
        try:
            user = g.current_user
            usage_stats = user.get_usage_stats()
            
            return jsonify({
                'user': user.to_dict(),
                'usage_stats': usage_stats
            }), 200
                
        except Exception as e:
            logger.error(f"Error in get_current_user endpoint: {e}")
            return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

    @auth_bp.route('/profile', methods=['PUT'])
    @jwt_middleware.require_auth
    def update_profile():
        """Обновление профиля пользователя"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Данные не предоставлены'}), 400
            
            try:
                validated_data = update_profile_schema.load(data)
            except ValidationError as err:
                return jsonify({'error': 'Ошибка валидации', 'details': err.messages}), 400
            
            success, message, user = auth_service.update_user_profile(
                g.current_user_id,
                **validated_data
            )
            
            if success:
                return jsonify({
                    'message': message,
                    'user': user.to_dict()
                }), 200
            else:
                return jsonify({'error': message}), 400
                
        except Exception as e:
            logger.error(f"Error in update_profile endpoint: {e}")
            return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

    @auth_bp.route('/change-password', methods=['POST'])
    @jwt_middleware.require_auth
    def change_password():
        """Смена пароля"""
        try:
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Данные не предоставлены'}), 400
            
            try:
                validated_data = change_password_schema.load(data)
            except ValidationError as err:
                return jsonify({'error': 'Ошибка валидации', 'details': err.messages}), 400
            
            success, message = auth_service.change_password(
                g.current_user_id,
                validated_data['current_password'],
                validated_data['new_password']
            )
            
            if success:
                return jsonify({'message': message}), 200
            else:
                return jsonify({'error': message}), 400
                
        except Exception as e:
            logger.error(f"Error in change_password endpoint: {e}")
            return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

    @auth_bp.route('/sessions', methods=['GET'])
    @jwt_middleware.require_auth
    def get_user_sessions():
        """Получить активные сессии пользователя"""
        try:
            user = g.current_user
            sessions = [
                session.to_dict() for session in user.sessions 
                if session.is_active and not session.is_expired()
            ]
            
            return jsonify({'sessions': sessions}), 200
                
        except Exception as e:
            logger.error(f"Error in get_user_sessions endpoint: {e}")
            return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

    @auth_bp.route('/sessions/<int:session_id>', methods=['DELETE'])
    @jwt_middleware.require_auth
    def revoke_session(session_id):
        """Отозвать конкретную сессию"""
        try:
            session = next(
                (s for s in g.current_user.sessions if s.id == session_id), 
                None
            )
            
            if not session:
                return jsonify({'error': 'Сессия не найдена'}), 404
            
            session.is_active = False
            db_session.commit()
            
            return jsonify({'message': 'Сессия отозвана'}), 200
                
        except Exception as e:
            logger.error(f"Error in revoke_session endpoint: {e}")
            return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

    return auth_bp, jwt_middleware
