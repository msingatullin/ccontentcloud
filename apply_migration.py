#!/usr/bin/env python3
"""
Скрипт для применения миграции agent_subscriptions
"""

import sys
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Добавляем путь к приложению
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database.connection import get_db_session, engine
from sqlalchemy import text

def apply_migration():
    """Применяет миграцию для создания таблицы agent_subscriptions"""
    
    print("=" * 60)
    print("ПРИМЕНЕНИЕ МИГРАЦИИ: agent_subscriptions")
    print("=" * 60)
    
    # Читаем SQL миграцию
    migration_file = 'migrations/add_agent_subscriptions_table.sql'
    
    if not os.path.exists(migration_file):
        print(f"❌ Файл миграции не найден: {migration_file}")
        return False
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print(f"\n📄 Читаем миграцию из: {migration_file}")
    print(f"📏 Размер: {len(sql_content)} символов")
    
    # Разбиваем на отдельные команды
    # Убираем комментарии и пустые строки
    commands = []
    current_command = []
    
    for line in sql_content.split('\n'):
        # Пропускаем комментарии
        if line.strip().startswith('--'):
            continue
        
        # Добавляем строку к текущей команде
        current_command.append(line)
        
        # Если строка заканчивается на ;, это конец команды
        if line.strip().endswith(';'):
            command = '\n'.join(current_command).strip()
            if command:
                commands.append(command)
            current_command = []
    
    print(f"📋 Найдено команд SQL: {len(commands)}")
    
    # Применяем миграцию
    try:
        db_session = get_db_session()
        
        print("\n🔄 Применяем миграцию...")
        
        for i, command in enumerate(commands, 1):
            try:
                # Показываем первые 100 символов команды
                preview = command[:100].replace('\n', ' ')
                print(f"  [{i}/{len(commands)}] {preview}...")
                
                # Выполняем команду
                db_session.execute(text(command))
                db_session.commit()
                
                print(f"  ✅ Выполнено")
                
            except Exception as e:
                error_msg = str(e)
                
                # Если таблица уже существует - это нормально
                if 'already exists' in error_msg.lower():
                    print(f"  ⚠️  Уже существует (пропускаем)")
                    db_session.rollback()
                    continue
                else:
                    print(f"  ❌ Ошибка: {error_msg}")
                    db_session.rollback()
                    raise
        
        print("\n✅ МИГРАЦИЯ УСПЕШНО ПРИМЕНЕНА!")
        print("=" * 60)
        
        # Проверяем что таблица создана
        result = db_session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'agent_subscriptions'
        """))
        
        if result.fetchone():
            print("✅ Таблица agent_subscriptions создана")
            
            # Проверяем структуру
            result = db_session.execute(text("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'agent_subscriptions'
                ORDER BY ordinal_position
            """))
            
            columns = result.fetchall()
            print(f"\n📊 Структура таблицы ({len(columns)} колонок):")
            for col in columns:
                print(f"  - {col[0]}: {col[1]}")
        else:
            print("⚠️  Таблица не найдена после миграции")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ОШИБКА ПРИ ПРИМЕНЕНИИ МИГРАЦИИ:")
        print(f"   {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = apply_migration()
    sys.exit(0 if success else 1)

