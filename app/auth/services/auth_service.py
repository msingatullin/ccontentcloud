"""
Сервис аутентификации пользователей
"""

import secrets
import string
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import logging

from app.auth.models.user import User, UserSession, UserRole, UserStatus
from app.auth.utils.email import EmailService
from app.billing.models.subscription import Subscription, SubscriptionStatus

logger = logging.getLogger(__name__)


class AuthService:
    """Сервис аутентификации"""
    
    def __init__(self, db_session: Session, secret_key: str, email_service: EmailService):
        self.db = db_session
        self.secret_key = secret_key
        self.email_service = email_service
        self.jwt_algorithm = 'HS256'
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 30

    def register_user(
        self, 
        email: str, 
        password: str, 
        username: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        company: Optional[str] = None,
        phone: Optional[str] = None
    ) -> Tuple[bool, str, Optional[User]]:
        """
        Регистрация нового пользователя
        
        Returns:
            Tuple[bool, str, Optional[User]]: (success, message, user)
        """
        try:
            # Проверка существования пользователя
            existing_user = self.db.query(User).filter(
                (User.email == email) | (User.username == username)
            ).first()
            
            if existing_user:
                if existing_user.email == email:
                    return False, "Пользователь с таким email уже существует", None
                else:
                    return False, "Пользователь с таким именем уже существует", None

            # Создание нового пользователя
            user = User(
                email=email,
                username=username,
                first_name=first_name,
                last_name=last_name,
                company=company,
                phone=phone,
                role=UserRole.USER,
                status=UserStatus.PENDING_VERIFICATION
            )
            
            user.set_password(password)
            user.generate_email_verification_token()
            
            self.db.add(user)
            self.db.commit()
            
            # Отправка email для верификации
            try:
                self.email_service.send_verification_email(user)
                logger.info(f"Verification email sent to {email}")
            except Exception as e:
                logger.error(f"Failed to send verification email to {email}: {e}")
                # Не прерываем регистрацию из-за ошибки email
            
            logger.info(f"User registered successfully: {email}")
            return True, "Пользователь успешно зарегистрирован. Проверьте email для подтверждения.", user
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error during registration: {e}")
            return False, "Ошибка при регистрации пользователя", None
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during registration: {e}")
            return False, "Внутренняя ошибка сервера", None

    def login_user(
        self, 
        email: str, 
        password: str,
        device_info: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Авторизация пользователя
        
        Returns:
            Tuple[bool, str, Optional[Dict]]: (success, message, tokens)
        """
        try:
            # Поиск пользователя
            user = self.db.query(User).filter(User.email == email).first()
            
            if not user:
                return False, "Неверный email или пароль", None
            
            # Проверка пароля
            if not user.check_password(password):
                return False, "Неверный email или пароль", None
            
            # Проверка статуса пользователя
            if not user.is_active:
                return False, "Аккаунт деактивирован", None
            
            if user.status == UserStatus.SUSPENDED:
                return False, "Аккаунт заблокирован", None
            
            # ВРЕМЕННО ОТКЛЮЧЕНО ДЛЯ ТЕСТИРОВАНИЯ
            # if user.status == UserStatus.PENDING_VERIFICATION:
            #     return False, "Подтвердите email для входа в систему", None
            
            # Обновление информации о входе
            user.update_login_info()
            
            # Создание JWT токенов
            tokens = self._create_tokens(user, device_info, ip_address, user_agent)
            
            self.db.commit()
            
            logger.info(f"User logged in successfully: {email}")
            return True, "Успешная авторизация", tokens
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during login: {e}")
            return False, "Внутренняя ошибка сервера", None

    def verify_email(self, token: str) -> Tuple[bool, str]:
        """Верификация email"""
        try:
            user = self.db.query(User).filter(
                User.email_verification_token == token
            ).first()
            
            if not user:
                return False, "Неверный токен верификации"
            
            if user.verify_email_token(token):
                self.db.commit()
                logger.info(f"Email verified successfully: {user.email}")
                return True, "Email успешно подтвержден"
            else:
                return False, "Токен верификации истек или неверен"
                
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during email verification: {e}")
            return False, "Внутренняя ошибка сервера"

    def resend_verification_email(self, email: str) -> Tuple[bool, str]:
        """Повторная отправка email верификации"""
        try:
            user = self.db.query(User).filter(User.email == email).first()
            
            if not user:
                return False, "Пользователь не найден"
            
            if user.is_verified:
                return False, "Email уже подтвержден"
            
            # Генерация нового токена
            user.generate_email_verification_token()
            self.db.commit()
            
            # Отправка email
            self.email_service.send_verification_email(user)
            
            logger.info(f"Verification email resent to {email}")
            return True, "Письмо с подтверждением отправлено повторно"
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error resending verification email: {e}")
            return False, "Внутренняя ошибка сервера"

    def request_password_reset(self, email: str) -> Tuple[bool, str]:
        """Запрос сброса пароля"""
        try:
            user = self.db.query(User).filter(User.email == email).first()
            
            if not user:
                # Не раскрываем информацию о существовании пользователя
                return True, "Если пользователь существует, письмо с инструкциями отправлено"
            
            # Генерация токена сброса
            user.generate_password_reset_token()
            self.db.commit()
            
            # Отправка email
            self.email_service.send_password_reset_email(user)
            
            logger.info(f"Password reset email sent to {email}")
            return True, "Если пользователь существует, письмо с инструкциями отправлено"
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error requesting password reset: {e}")
            return False, "Внутренняя ошибка сервера"

    def reset_password(self, token: str, new_password: str) -> Tuple[bool, str]:
        """Сброс пароля"""
        try:
            user = self.db.query(User).filter(
                User.password_reset_token == token
            ).first()
            
            if not user:
                return False, "Неверный токен сброса пароля"
            
            if not user.verify_password_reset_token(token):
                return False, "Токен сброса пароля истек или неверен"
            
            # Установка нового пароля
            user.set_password(new_password)
            user.password_reset_token = None
            user.password_reset_expires = None
            
            # Деактивация всех сессий
            self._deactivate_user_sessions(user.id)
            
            self.db.commit()
            
            logger.info(f"Password reset successfully for {user.email}")
            return True, "Пароль успешно изменен"
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error resetting password: {e}")
            return False, "Внутренняя ошибка сервера"

    def change_password(
        self, 
        user_id: int, 
        current_password: str, 
        new_password: str
    ) -> Tuple[bool, str]:
        """Смена пароля"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            
            if not user:
                return False, "Пользователь не найден"
            
            if not user.check_password(current_password):
                return False, "Неверный текущий пароль"
            
            user.set_password(new_password)
            
            # Деактивация всех сессий кроме текущей
            self._deactivate_user_sessions(user.id)
            
            self.db.commit()
            
            logger.info(f"Password changed successfully for user {user_id}")
            return True, "Пароль успешно изменен"
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error changing password: {e}")
            return False, "Внутренняя ошибка сервера"

    def refresh_token(self, refresh_token: str) -> Tuple[bool, str, Optional[Dict]]:
        """Обновление токена"""
        try:
            session = self.db.query(UserSession).filter(
                UserSession.refresh_token == refresh_token,
                UserSession.is_active == True
            ).first()
            
            if not session or session.is_expired():
                return False, "Неверный или истекший refresh token", None
            
            user = session.user
            if not user.is_active or user.status != UserStatus.ACTIVE:
                return False, "Пользователь неактивен", None
            
            # Создание новых токенов
            tokens = self._create_tokens(user, session.device_info, session.ip_address, session.user_agent)
            
            # Обновление сессии
            session.update_last_used()
            self.db.commit()
            
            return True, "Токен обновлен", tokens
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error refreshing token: {e}")
            return False, "Внутренняя ошибка сервера", None

    def logout_user(self, token_jti: str) -> Tuple[bool, str]:
        """Выход пользователя"""
        try:
            session = self.db.query(UserSession).filter(
                UserSession.token_jti == token_jti
            ).first()
            
            if session:
                session.is_active = False
                self.db.commit()
            
            return True, "Успешный выход"
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error during logout: {e}")
            return False, "Внутренняя ошибка сервера"

    def logout_all_sessions(self, user_id: int) -> Tuple[bool, str]:
        """Выход из всех сессий"""
        try:
            self._deactivate_user_sessions(user_id)
            self.db.commit()
            
            return True, "Выход из всех сессий выполнен"
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error logging out all sessions: {e}")
            return False, "Внутренняя ошибка сервера"

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Получить пользователя по email"""
        return self.db.query(User).filter(User.email == email).first()

    def update_user_profile(
        self, 
        user_id: int, 
        **kwargs
    ) -> Tuple[bool, str, Optional[User]]:
        """Обновление профиля пользователя"""
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            
            if not user:
                return False, "Пользователь не найден", None
            
            # Обновление разрешенных полей
            allowed_fields = [
                'first_name', 'last_name', 'phone', 'company', 
                'position', 'timezone', 'language', 'notifications_enabled', 
                'marketing_emails'
            ]
            
            for field, value in kwargs.items():
                if field in allowed_fields and hasattr(user, field):
                    setattr(user, field, value)
            
            self.db.commit()
            
            return True, "Профиль обновлен", user
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error updating user profile: {e}")
            return False, "Внутренняя ошибка сервера", None

    def _create_tokens(
        self, 
        user: User, 
        device_info: Optional[Dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Создание JWT токенов"""
        now = datetime.utcnow()
        jti = self._generate_jti()
        
        logger.info(f"AuthService._create_tokens called for user {user.email}")
        logger.info(f"AuthService SECRET_KEY for token creation: {self.secret_key[:10]}...")
        
        # Access token
        access_token_payload = {
            'user_id': user.id,
            'email': user.email,
            'role': user.role.value,
            'jti': jti,
            'type': 'access',
            'iat': now,
            'exp': now + timedelta(minutes=self.access_token_expire_minutes)
        }
        
        logger.info(f"Access token payload: {access_token_payload}")
        access_token = jwt.encode(access_token_payload, self.secret_key, algorithm=self.jwt_algorithm)
        logger.info(f"Access token created: {access_token[:20]}...")
        
        # Refresh token
        refresh_token = self._generate_refresh_token()
        refresh_expires = now + timedelta(days=self.refresh_token_expire_days)
        
        # Создание сессии
        session = UserSession(
            user_id=user.id,
            token_jti=jti,
            refresh_token=refresh_token,
            device_info=str(device_info) if device_info else None,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=refresh_expires
        )
        
        self.db.add(session)
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'bearer',
            'expires_in': self.access_token_expire_minutes * 60,
            'user': user.to_dict()
        }

    def _generate_jti(self) -> str:
        """Генерация JWT ID"""
        return secrets.token_urlsafe(32)

    def _generate_refresh_token(self) -> str:
        """Генерация refresh token"""
        return secrets.token_urlsafe(64)

    def _deactivate_user_sessions(self, user_id: int) -> None:
        """Деактивация всех сессий пользователя"""
        self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True
        ).update({'is_active': False})

    def verify_token(self, token: str) -> Tuple[bool, Optional[Dict]]:
        """Верификация JWT токена"""
        try:
            logger.info(f"AuthService.verify_token called with token: {token[:20]}...")
            logger.info(f"AuthService SECRET_KEY: {self.secret_key[:10]}...")
            
            payload = jwt.decode(token, self.secret_key, algorithms=[self.jwt_algorithm])
            logger.info(f"JWT payload decoded successfully: {payload}")
            
            # Проверка типа токена
            if payload.get('type') != 'access':
                logger.warning(f"Invalid token type: {payload.get('type')}")
                return False, None
            
            # Проверка существования сессии
            jti = payload.get('jti')
            logger.info(f"Looking for session with JTI: {jti}")
            
            # ВРЕМЕННАЯ ДИАГНОСТИКА: проверим все сессии
            all_sessions = self.db.query(UserSession).all()
            logger.info(f"Total sessions in DB: {len(all_sessions)}")
            for sess in all_sessions:
                logger.info(f"Session: JTI={sess.token_jti}, is_active={sess.is_active}, user_id={sess.user_id}")
            
            session = self.db.query(UserSession).filter(
                UserSession.token_jti == jti,
                UserSession.is_active == True
            ).first()
            
            if not session:
                logger.warning(f"Session not found for JTI: {jti}")
                return False, None
            
            if session.is_expired():
                logger.warning(f"Session expired for JTI: {jti}")
                return False, None
            
            # Проверка пользователя
            user = session.user
            logger.info(f"User found: id={user.id}, email={user.email}, is_active={user.is_active}, status={user.status}")
            
            if not user.is_active or user.status != UserStatus.ACTIVE:
                logger.warning(f"User not active: is_active={user.is_active}, status={user.status}")
                return False, None
            
            # Обновление времени последнего использования
            session.update_last_used()
            self.db.commit()
            
            result = {
                'user_id': user.id,
                'email': user.email,
                'role': user.role.value,
                'jti': payload.get('jti')
            }
            logger.info(f"Token verification successful: {result}")
            return True, result
            
        except jwt.ExpiredSignatureError as e:
            logger.warning(f"JWT token expired: {e}")
            return False, None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return False, None
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False, None
