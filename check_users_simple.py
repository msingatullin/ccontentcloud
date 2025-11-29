#!/usr/bin/env python3
"""
Простой скрипт для проверки пользователей в Cloud SQL
"""

import os
import sys
import psycopg2
from psycopg2.extras import RealDictCursor

# Загружаем переменные окружения
from dotenv import load_dotenv
load_dotenv()

def check_users():
    """Проверяем пользователей в Cloud SQL"""
    
    # Параметры подключения к Cloud SQL
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'content_curator')
    DB_USER = os.getenv('DB_USER', 'content_curator_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    
    print(f"=== ПОДКЛЮЧЕНИЕ К CLOUD SQL ===")
    print(f"Host: {DB_HOST}")
    print(f"Database: {DB_NAME}")
    print(f"User: {DB_USER}")
    print()
    
    try:
        # Подключение к базе данных
        if DB_HOST.startswith('/cloudsql/'):
            # Cloud SQL Unix Socket
            conn = psycopg2.connect(
                host=DB_HOST,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
        else:
            # Обычное TCP подключение
            conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
        
        print("✅ Подключение к базе данных успешно!")
        
        # Создаем курсор
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Запрашиваем всех пользователей
        cursor.execute("""
            SELECT 
                id, 
                email, 
                username, 
                status, 
                is_active, 
                is_verified,
                created_at,
                updated_at
            FROM users 
            ORDER BY id
        """)
        
        users = cursor.fetchall()
        
        print(f"\n=== ПОЛЬЗОВАТЕЛИ В БАЗЕ ДАННЫХ ({len(users)} шт.) ===")
        
        for user in users:
            print(f"ID: {user['id']}")
            print(f"Email: {user['email']}")
            print(f"Username: {user['username']}")
            print(f"Status: {user['status']}")
            print(f"Is Active: {user['is_active']}")
            print(f"Is Verified: {user['is_verified']}")
            print(f"Created: {user['created_at']}")
            print(f"Updated: {user['updated_at']}")
            print("---")
        
        # Проверяем конкретного пользователя
        cursor.execute("""
            SELECT * FROM users 
            WHERE email = %s
        """, ('1@ya.ru',))
        
        user_1 = cursor.fetchone()
        
        if user_1:
            print(f"\n=== ПОЛЬЗОВАТЕЛЬ 1@ya.ru ===")
            print(f"ID: {user_1['id']}")
            print(f"Status: {user_1['status']}")
            print(f"Is Active: {user_1['is_active']}")
            print(f"Is Verified: {user_1['is_verified']}")
            
            # Проверяем, почему логин не работает
            if user_1['status'] == 'pending_verification':
                print("❌ ПРОБЛЕМА: Статус 'pending_verification' - требует подтверждения email")
            elif not user_1['is_active']:
                print("❌ ПРОБЛЕМА: Пользователь неактивен")
            elif not user_1['is_verified']:
                print("❌ ПРОБЛЕМА: Email не подтвержден")
            else:
                print("✅ Пользователь должен иметь возможность логиниться")
        else:
            print("\n❌ Пользователь 1@ya.ru не найден в базе данных")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        return False
    
    return True

if __name__ == "__main__":
    check_users()
