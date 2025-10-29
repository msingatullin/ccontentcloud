#!/usr/bin/env python3
"""
Скрипт для применения миграции token_usage к PostgreSQL на Cloud SQL
Использует переменную окружения DATABASE_URL или параметры подключения из .env
"""

import os
import sys
import subprocess
from pathlib import Path

# Цвета для вывода
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'

def print_color(text, color):
    print(f"{color}{text}{NC}")

def main():
    print_color("╔════════════════════════════════════════════════════════════╗", GREEN)
    print_color("║   Применение миграции token_usage к PostgreSQL            ║", GREEN)
    print_color("╚════════════════════════════════════════════════════════════╝", GREEN)
    print()

    # Путь к миграции
    migration_file = Path(__file__).parent / "migrations" / "create_token_usage_table_postgres.sql"
    
    if not migration_file.exists():
        print_color(f"❌ Файл миграции не найден: {migration_file}", RED)
        sys.exit(1)
    
    # Читаем SQL из файла
    with open(migration_file, 'r', encoding='utf-8') as f:
        migration_sql = f.read()
    
    print_color(f"📄 Файл миграции: {migration_file.name}", YELLOW)
    print()
    
    # Конфигурация Cloud SQL
    project_id = "content-curator-1755119514"
    instance_name = "content-curator-db"
    database_name = "content_curator"
    
    print_color("📋 Конфигурация:", YELLOW)
    print(f"  Project: {project_id}")
    print(f"  Instance: {instance_name}")
    print(f"  Database: {database_name}")
    print()
    
    # Применяем миграцию через gcloud sql execute с разбивкой на команды
    print_color("🔄 Применение миграции через gcloud...", YELLOW)
    print()
    
    # Разбиваем SQL на отдельные команды (по CREATE TABLE, CREATE INDEX, COMMENT)
    sql_commands = []
    current_cmd = []
    
    for line in migration_sql.split('\n'):
        line_stripped = line.strip()
        
        # Пропускаем комментарии и пустые строки
        if not line_stripped or line_stripped.startswith('--'):
            continue
        
        current_cmd.append(line)
        
        # Если строка заканчивается на ; - это конец команды
        if line_stripped.endswith(';'):
            sql_commands.append('\n'.join(current_cmd))
            current_cmd = []
    
    print_color(f"📊 Найдено SQL команд: {len(sql_commands)}", YELLOW)
    print()
    
    success_count = 0
    error_count = 0
    
    for i, sql_cmd in enumerate(sql_commands, 1):
        # Получаем первую строку для отображения
        first_line = sql_cmd.strip().split('\n')[0][:60]
        print(f"[{i}/{len(sql_commands)}] {first_line}...")
        
        try:
            # Экранируем SQL для передачи в gcloud
            sql_escaped = sql_cmd.replace("'", "\\'")
            
            # Выполняем через gcloud sql execute
            result = subprocess.run([
                "gcloud", "sql", "execute-sql", instance_name,
                f"--project={project_id}",
                f"--database={database_name}",
                f"--sql={sql_cmd}"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print_color("  ✅ Успешно", GREEN)
                success_count += 1
            else:
                # Игнорируем ошибки "already exists" 
                if "already exists" in result.stderr.lower() or "duplicate" in result.stderr.lower():
                    print_color("  ⚠️  Уже существует (пропуск)", YELLOW)
                    success_count += 1
                else:
                    print_color(f"  ❌ Ошибка: {result.stderr[:100]}", RED)
                    error_count += 1
        
        except subprocess.TimeoutExpired:
            print_color("  ❌ Таймаут выполнения", RED)
            error_count += 1
        except Exception as e:
            print_color(f"  ❌ Ошибка: {str(e)[:100]}", RED)
            error_count += 1
    
    print()
    print_color("=" * 60, GREEN)
    print_color(f"✅ Успешно выполнено: {success_count}", GREEN)
    if error_count > 0:
        print_color(f"❌ Ошибок: {error_count}", RED)
    print_color("=" * 60, GREEN)
    print()
    
    if error_count == 0:
        print_color("🎉 Миграция успешно применена!", GREEN)
        print()
        print_color("Проверка таблицы:", YELLOW)
        print(f"gcloud sql connect {instance_name} --project={project_id} --database={database_name}")
        print("\\d token_usage")
    else:
        print_color("⚠️  Миграция применена с ошибками. Проверьте логи выше.", YELLOW)
        sys.exit(1)

if __name__ == "__main__":
    main()



