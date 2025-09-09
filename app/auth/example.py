"""
Пример использования системы аутентификации
"""

import os
import sys
from datetime import datetime

# Добавляем путь к корню проекта
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.auth.models.user import User, UserRole, UserStatus
from app.auth.services.auth_service import AuthService
from app.auth.utils.email import EmailService

def setup_database():
    """Настройка базы данных"""
    # Создаем базу данных в памяти для примера
    engine = create_engine('sqlite:///:memory:', echo=True)
    
    # Создаем таблицы
    from app.auth.models.user import Base
    Base.metadata.create_all(engine)
    
    # Создаем сессию
    Session = sessionmaker(bind=engine)
    session = Session()
    
    return session

def test_user_registration():
    """Тест регистрации пользователя"""
    print("=== Тест регистрации пользователя ===")
    
    # Настройка
    session = setup_database()
    email_service = EmailService()
    auth_service = AuthService(session, "test-secret-key", email_service)
    
    # Регистрация пользователя
    success, message, user = auth_service.register_user(
        email="test@example.com",
        password="testpassword123",
        username="testuser",
        first_name="Тест",
        last_name="Пользователь",
        company="Test Company"
    )
    
    print(f"Регистрация: {success}")
    print(f"Сообщение: {message}")
    if user:
        print(f"Пользователь: {user.username} ({user.email})")
        print(f"Статус: {user.status.value}")
        print(f"Верифицирован: {user.is_verified}")
    
    return user

def test_user_login():
    """Тест авторизации пользователя"""
    print("\n=== Тест авторизации пользователя ===")
    
    # Настройка
    session = setup_database()
    email_service = EmailService()
    auth_service = AuthService(session, "test-secret-key", email_service)
    
    # Сначала регистрируем пользователя
    success, message, user = auth_service.register_user(
        email="test@example.com",
        password="testpassword123",
        username="testuser"
    )
    
    # Подтверждаем email (для теста)
    user.is_verified = True
    user.status = UserStatus.ACTIVE
    session.commit()
    
    # Авторизация
    success, message, tokens = auth_service.login_user(
        email="test@example.com",
        password="testpassword123"
    )
    
    print(f"Авторизация: {success}")
    print(f"Сообщение: {message}")
    if tokens:
        print(f"Access token: {tokens['access_token'][:50]}...")
        print(f"Refresh token: {tokens['refresh_token'][:50]}...")
        print(f"User: {tokens['user']['username']}")
    
    return tokens

def test_token_verification():
    """Тест верификации токена"""
    print("\n=== Тест верификации токена ===")
    
    # Настройка
    session = setup_database()
    email_service = EmailService()
    auth_service = AuthService(session, "test-secret-key", email_service)
    
    # Регистрация и авторизация
    success, message, user = auth_service.register_user(
        email="test@example.com",
        password="testpassword123",
        username="testuser"
    )
    
    user.is_verified = True
    user.status = UserStatus.ACTIVE
    session.commit()
    
    success, message, tokens = auth_service.login_user(
        email="test@example.com",
        password="testpassword123"
    )
    
    # Верификация токена
    is_valid, payload = auth_service.verify_token(tokens['access_token'])
    
    print(f"Токен валиден: {is_valid}")
    if payload:
        print(f"User ID: {payload['user_id']}")
        print(f"Email: {payload['email']}")
        print(f"Role: {payload['role']}")

def test_password_reset():
    """Тест сброса пароля"""
    print("\n=== Тест сброса пароля ===")
    
    # Настройка
    session = setup_database()
    email_service = EmailService()
    auth_service = AuthService(session, "test-secret-key", email_service)
    
    # Регистрация пользователя
    success, message, user = auth_service.register_user(
        email="test@example.com",
        password="testpassword123",
        username="testuser"
    )
    
    # Запрос сброса пароля
    success, message = auth_service.request_password_reset("test@example.com")
    print(f"Запрос сброса: {success}")
    print(f"Сообщение: {message}")
    
    # Получаем токен сброса
    reset_token = user.password_reset_token
    print(f"Токен сброса: {reset_token[:20]}...")
    
    # Сброс пароля
    success, message = auth_service.reset_password(reset_token, "newpassword123")
    print(f"Сброс пароля: {success}")
    print(f"Сообщение: {message}")
    
    # Проверяем новый пароль
    success, message, tokens = auth_service.login_user(
        email="test@example.com",
        password="newpassword123"
    )
    print(f"Авторизация с новым паролем: {success}")

def test_user_profile():
    """Тест обновления профиля"""
    print("\n=== Тест обновления профиля ===")
    
    # Настройка
    session = setup_database()
    email_service = EmailService()
    auth_service = AuthService(session, "test-secret-key", email_service)
    
    # Регистрация пользователя
    success, message, user = auth_service.register_user(
        email="test@example.com",
        password="testpassword123",
        username="testuser"
    )
    
    # Обновление профиля
    success, message, updated_user = auth_service.update_user_profile(
        user.id,
        first_name="Новое имя",
        last_name="Новая фамилия",
        company="Новая компания",
        phone="+7 (999) 123-45-67"
    )
    
    print(f"Обновление профиля: {success}")
    print(f"Сообщение: {message}")
    if updated_user:
        print(f"Полное имя: {updated_user.get_full_name()}")
        print(f"Компания: {updated_user.company}")
        print(f"Телефон: {updated_user.phone}")

def test_user_roles():
    """Тест ролей пользователей"""
    print("\n=== Тест ролей пользователей ===")
    
    # Настройка
    session = setup_database()
    email_service = EmailService()
    auth_service = AuthService(session, "test-secret-key", email_service)
    
    # Создание пользователей с разными ролями
    users_data = [
        ("user@example.com", "user123", "regularuser", UserRole.USER),
        ("admin@example.com", "admin123", "adminuser", UserRole.ADMIN),
        ("mod@example.com", "mod123", "moduser", UserRole.MODERATOR)
    ]
    
    for email, password, username, role in users_data:
        success, message, user = auth_service.register_user(
            email=email,
            password=password,
            username=username
        )
        if user:
            user.role = role
            user.is_verified = True
            user.status = UserStatus.ACTIVE
            session.commit()
            
            print(f"Пользователь: {user.username}")
            print(f"Роль: {user.role.value}")
            print(f"Админ: {user.is_admin()}")
            print(f"Модератор: {user.is_moderator()}")
            print("---")

def main():
    """Основная функция для запуска тестов"""
    print("Тестирование системы аутентификации")
    print("=" * 50)
    
    try:
        # Запуск тестов
        test_user_registration()
        test_user_login()
        test_token_verification()
        test_password_reset()
        test_user_profile()
        test_user_roles()
        
        print("\n" + "=" * 50)
        print("Все тесты завершены успешно!")
        
    except Exception as e:
        print(f"\nОшибка при выполнении тестов: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
