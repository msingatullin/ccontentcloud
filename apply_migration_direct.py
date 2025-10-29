#!/usr/bin/env python3
"""
Прямое подключение к PostgreSQL для применения миграции
Использует psycopg2 для подключения к Cloud SQL
"""

import os
import sys
from pathlib import Path

try:
    import psycopg2
except ImportError:
    print("❌ psycopg2 не установлен. Устанавливаю...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    import psycopg2

# Цвета
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'

def print_color(text, color):
    print(f"{color}{text}{NC}")

def main():
    print_color("=" * 60, GREEN)
    print_color("  Применение миграции token_usage к PostgreSQL", GREEN)
    print_color("=" * 60, GREEN)
    print()
    
    # Параметры подключения
    db_params = {
        'host': '34.55.156.101',  # External IP Cloud SQL
        'port': 5432,
        'database': 'content_curator',
        'user': 'content_curator_user',
        'password': 'XbsOELWNmeTGLkj9JCH8G8VG',
        'connect_timeout': 10
    }
    
    print_color(f"📋 Подключение к: {db_params['host']}:{db_params['port']}/{db_params['database']}", YELLOW)
    print_color(f"   Пользователь: {db_params['user']}", YELLOW)
    print()
    
    # Читаем миграцию
    migration_file = Path(__file__).parent / "migrations" / "create_token_usage_table_postgres.sql"
    if not migration_file.exists():
        print_color(f"❌ Файл миграции не найден: {migration_file}", RED)
        sys.exit(1)
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        migration_sql = f.read()
    
    print_color(f"📄 Файл миграции загружен: {len(migration_sql)} символов", YELLOW)
    print()
    
    try:
        # Подключаемся
        print_color("🔌 Подключение к PostgreSQL...", YELLOW)
        conn = psycopg2.connect(**db_params)
        conn.autocommit = True
        cursor = conn.cursor()
        
        print_color("✅ Подключено успешно!", GREEN)
        print()
        
        # Проверяем существует ли таблица
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'token_usage'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            print_color("⚠️  Таблица token_usage уже существует!", YELLOW)
            print_color("   Проверяю структуру...", YELLOW)
            
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'token_usage'
                ORDER BY ordinal_position;
            """)
            columns = cursor.fetchall()
            print_color(f"   Колонок в таблице: {len(columns)}", GREEN)
            print()
            
            # Применяем только индексы и комментарии
            print_color("📊 Применяю индексы и комментарии...", YELLOW)
        else:
            print_color("✅ Таблица не существует, применяю полную миграцию...", GREEN)
        
        # Применяем миграцию
        cursor.execute(migration_sql)
        
        print_color("✅ Миграция применена успешно!", GREEN)
        print()
        
        # Проверяем результат
        cursor.execute("SELECT COUNT(*) FROM token_usage;")
        count = cursor.fetchone()[0]
        print_color(f"✅ Таблица token_usage: {count} записей", GREEN)
        
        cursor.execute("""
            SELECT indexname FROM pg_indexes 
            WHERE tablename = 'token_usage';
        """)
        indexes = cursor.fetchall()
        print_color(f"✅ Создано индексов: {len(indexes)}", GREEN)
        
        cursor.close()
        conn.close()
        
        print()
        print_color("=" * 60, GREEN)
        print_color("🎉 МИГРАЦИЯ УСПЕШНО ПРИМЕНЕНА!", GREEN)
        print_color("=" * 60, GREEN)
        print()
        print_color("Endpoints /api/v1/billing/usage/tokens/* теперь работают!", GREEN)
        
    except psycopg2.Error as e:
        print_color(f"❌ Ошибка PostgreSQL: {e}", RED)
        sys.exit(1)
    except Exception as e:
        print_color(f"❌ Ошибка: {e}", RED)
        sys.exit(1)

if __name__ == "__main__":
    main()



